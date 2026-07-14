# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# cwop.py
# CWOP/APRS weather submission script
# Runs on Pi Zero 2W, reads Pico 2W via USB serial
# Submits to cwop.aprs.net every 5 minutes
# Does require config.py to be present with your WIFI credentials
#
# MISSING-DATA HANDLING (added 2026-07-10):
# The Pico (main.py) now degrades gracefully - if an I2C sensor fails
# for a cycle, that field arrives as an empty string in the serial line
# instead of the whole line being dropped. This script mirrors that:
#   - parse_line() converts empty numeric fields to None (never crashes
#     on float("")).
#   - build_aprs_packet() emits the APRS spec's "..." missing-data marker,
#     correctly sized per field, for any None value, instead of faking a 0.
# Wind direction/speed/gust come from GPIO/ADC (not I2C), so they remain
# present even during an I2C bus lockup - which matters because per the
# CWOP/APRS spec those, plus temperature, are the required leading fields.

import json
import os
import serial # type: ignore
import serial.tools.list_ports # type: ignore
import socket
import time
from datetime import datetime, timezone
from config import STATION_ID, LAT, LON, PASSCODE, DRY_RUN

# --- Journal file path ---

JOURNAL_FILE = "/mnt/data/weather/journal.csv"

# --- Silence sentinel ---
# Pico emits one line every 120s (main.py: 24 samples x 5s).
# 360s = 3 full cycles. Phase-independent guarantee: at least two
# FULL missed broadcasts in any alignment before we act. Trips
# ~6-8 min after a real freeze. On trip: log + reopen serial port.

SILENCE_TIMEOUT = 360

# --- Rain State file path ---

RAIN_STATE_FILE = "/mnt/data/weather/rainstate.json"

# --- Local midnight helper ---

# CWOP/MADIS spec (wxqa.com FAQ): the "P" field is rain since LOCAL
# midnight, not UTC midnight. The weather node is set to
# America/Chicago, so datetime.now().astimezone() returns local time
# with the correct CDT/CST DST offset automatically, and .date() gives
# today's LOCAL calendar date. NOTE: the APRS packet timestamp (the
# zXXXXXX field in build_aprs_packet) stays Zulu/UTC on purpose - only
# the rain-since-midnight rollover uses this local date.

def local_date():
    return datetime.now().astimezone().date()

# --- APRS packet formatting ---

def format_lat(lat):
    deg = int(lat)
    minutes = (lat - deg) * 60
    return f"{deg:02d}{minutes:05.2f}N"

def format_lon(lon):
    lon = abs(lon)
    deg = int(lon)
    minutes = (lon - deg) * 60
    return f"{deg:03d}{minutes:05.2f}W"

# --- Missing-data field formatters ---
# APRS spec (aprs.org/aprs12/weather-new.txt, wxqa.com FAQ): a missing
# value is sent as "..." sized to that field's fixed width, NOT as zeros.
# Sending t000 would falsely report 0F; t... honestly reports "no data".
# Each helper takes a value-or-None and returns the correctly sized string.

def fmt_temp(temp_f):
    # t field: 3 chars (supports negatives via the width, e.g. t-05)
    if temp_f is None:
        return "t..."
    return f"t{int(temp_f):03d}"

def fmt_pressure(pressure):
    # b field: 5 digits, tenths of millibars (e.g. 1012.8 hPa -> b10128)
    if pressure is None:
        return "b....."
    return f"b{int(pressure * 10):05d}"

def fmt_humidity(humidity):
    # h field: 2 digits, percent (00 = 100%)
    if humidity is None:
        return "h.."
    return f"h{min(int(humidity), 99):02d}"

def fmt_rain_1h(rain_1h):
    # r field: 3 digits, hundredths of an inch, last hour
    if rain_1h is None:
        return "r..."
    return f"r{int(rain_1h * 100):03d}"

def fmt_rain_24h(rain_24h):
    # p field: 3 digits, hundredths of an inch, last 24 hours
    if rain_24h is None:
        return "p..."
    return f"p{int(rain_24h * 100):03d}"

def fmt_rain_midnight(rain_midnight):
    # P field: 3 digits, hundredths of an inch, since local midnight
    if rain_midnight is None:
        return "P..."
    return f"P{int(rain_midnight * 100):03d}"

def fmt_wind_dir(wind_dir):
    # _ field: 3 digits, degrees from true north (REQUIRED field)
    dir_map = {"N": 0, "NE": 45, "E": 90, "SE": 135,
               "S": 180, "SW": 225, "W": 270, "NW": 315}
    if wind_dir is None or wind_dir not in dir_map:
        return "..."
    return f"{dir_map[wind_dir]:03d}"

def fmt_wind_speed(wind_sustained):
    # / field: 3 digits, sustained wind mph (REQUIRED field)
    if wind_sustained is None:
        return "..."
    return f"{int(wind_sustained):03d}"

def fmt_wind_gust(wind_gust):
    # g field: 3 digits, peak gust mph (REQUIRED field)
    if wind_gust is None:
        return "g..."
    return f"g{int(wind_gust):03d}"


def build_aprs_packet(temp_f, humidity, pressure, wind_dir, wind_sustained,
                      wind_gust, rain_1h, rain_24h, rain_midnight):
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%d%H%Mz")

    lat = format_lat(LAT)
    lon = format_lon(LON)

    # Required leading fields first (wind dir / speed / gust / temp), then
    # the optional fields. Any None becomes the spec's "..." marker.
    packet = (
        f"{STATION_ID}>APRS,TCPIP*:@{timestamp}{lat}/{lon}"
        f"_{fmt_wind_dir(wind_dir)}/{fmt_wind_speed(wind_sustained)}"
        f"{fmt_wind_gust(wind_gust)}"
        f"{fmt_temp(temp_f)}"
        f"{fmt_rain_1h(rain_1h)}{fmt_rain_24h(rain_24h)}{fmt_rain_midnight(rain_midnight)}"
        f"{fmt_humidity(humidity)}{fmt_pressure(pressure)}"
    )
    return packet

# --- Serial port detection ---

def find_pico():
    while True:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'ACM' in port.device:
                print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Pico found on {port.device}")
                return port.device
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Pico not found, retrying in 10s...")
        time.sleep(10)

# --- Serial (re)connect helper ---
# Shared by startup, the SerialException path, and the silence
# sentinel so all three reconnect identically instead of three
# copies drifting apart.
# Paired with the silence sentinel below: if the Pico stops sending
# its 2-min lines and goes quiet past SILENCE_TIMEOUT (360s = 3 cycles),
# the sentinel closes and reopens the port via this helper.

def open_serial():
    port = find_pico()
    ser = serial.Serial(port, 115200, timeout=5)
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Reading Pico serial stream...")
    return ser

# --- APRS submission ---

def submit_aprs(packet):
    if DRY_RUN:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] DRY RUN - WOULD SUBMIT: {packet}")
        return True
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        s.connect(("cwop.aprs.net", 14580))

        greeting = s.recv(1024).decode("utf-8", errors="replace").strip()
        write_journal("APRS_GTNG", greeting)

        login = f"user {STATION_ID} pass {PASSCODE} vers PiWeather 1.0\r\n"
        s.sendall(login.encode())
        time.sleep(2)

        login_ack = s.recv(1024).decode("utf-8", errors="replace").strip()
        write_journal("APRS_ACK", login_ack)

        s.sendall((packet + "\r\n").encode())
        time.sleep(2)
        s.close()

        utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"[{utc_now}] Submitted: {packet}")
        return True

    except Exception as e:
        utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"[{utc_now}] APRS submit failed: {e}")
        write_journal("APRS_ERR", f"APRS submit failed: {e}")
        return False

# --- Journal Logging ---

def write_journal(event_type, data_str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp},{event_type},{data_str}\n"
    try:
        with open(JOURNAL_FILE, "a") as f:
            f.write(line)
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Journal write failed: {e}")

# --- Line parsing ---
#
# Pico serial line format (main.py), 8 comma-separated fields:
#   temp_f, humidity, slp, uv, wind_sustained, wind_gust, wind_dir, rainfall
# Any I2C-sourced field (temp, humidity, slp) may arrive as an EMPTY
# STRING when that sensor failed for the cycle. We convert empties to
# None rather than crashing on float(""). Wind + rain come from GPIO and
# should always be numeric, but we treat them defensively the same way.

def _to_float_or_none(s):
    s = s.strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None

def parse_line(line):
    parts = line.strip().split(",")
    if len(parts) != 8:
        return None
    # wind_dir is a string token (N/NE/E/...); everything else is numeric.
    temp_f = _to_float_or_none(parts[0])
    humidity = _to_float_or_none(parts[1])
    pressure = _to_float_or_none(parts[2])
    # parts[3] is uv, unused
    wind_sustained = _to_float_or_none(parts[4])
    wind_gust = _to_float_or_none(parts[5])
    wind_dir = parts[6].strip() if parts[6].strip() != "" else None
    rainfall = _to_float_or_none(parts[7])
    return temp_f, humidity, pressure, wind_sustained, wind_gust, wind_dir, rainfall

# --- Load Rain State ---

def load_rain_state():
    # Clean defaults - used whenever anything goes wrong below.
    # A corrupt state file must NEVER crash the service on boot;
    # falling back to empty is always safer than that.
    default_1h = []
    default_24h = []
    default_midnight = 0.0
    default_last_midnight = local_date()

    try:
        with open(RAIN_STATE_FILE, "r") as f:
            state = json.load(f)

        rain_1h_bucket = state["rain_1h_bucket"]
        rain_24h_bucket = state["rain_24h_bucket"]
        rain_midnight = state["rain_midnight"]
        last_midnight = datetime.fromisoformat(state["last_midnight"]).date()

        # Prune both buckets against current time immediately on load.
        # If the box was down 3 hours, the 1h bucket should reload
        # already-empty - same prune logic the main loop already uses.
        now = time.time()
        rain_1h_bucket = [(t, r) for t, r in rain_1h_bucket if now - t <= 3600]
        rain_24h_bucket = [(t, r) for t, r in rain_24h_bucket if now - t <= 86400]

        # Midnight check: if the persisted date is older than today,
        # the restart crossed local midnight - zero the midnight bucket.
        # Worst case if we get this wrong is a gap in data (acceptable),
        # never a double-count (unacceptable).
        today_local = local_date()
        if today_local > last_midnight:
            rain_midnight = 0.0
            last_midnight = today_local

        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Rain state loaded from {RAIN_STATE_FILE}")
        write_journal("RAIN_STATE_LOAD", f"loaded ok: rain_midnight={rain_midnight:.4f}, last_midnight={last_midnight}")
        return rain_1h_bucket, rain_24h_bucket, rain_midnight, last_midnight

    except FileNotFoundError:
        # Expected on first-ever run, or right after this feature
        # is first deployed - not an error, just "nothing to load yet".
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] No rain state file found, starting fresh")
        write_journal("RAIN_STATE_LOAD", "no state file found, starting fresh")
        return default_1h, default_24h, default_midnight, default_last_midnight

    except Exception as e:
        # Anything else - corrupted JSON, missing key, bad date string,
        # power-yank mid-write on a previous version without the atomic
        # rename fix, etc. Same fallback. A bad file is not worth crashing
        # over; losing today's rain total once is fine, crashing forever
        # on every boot is not.
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Rain state load failed, starting fresh: {e}")
        write_journal("RAIN_STATE_LOAD", f"load failed, starting fresh: {e}")
        return default_1h, default_24h, default_midnight, default_last_midnight
    
# --- Save Rain State ---

def save_rain_state(rain_1h_bucket, rain_24h_bucket, rain_midnight, last_midnight):
    state = {
        "rain_1h_bucket": rain_1h_bucket,
        "rain_24h_bucket": rain_24h_bucket,
        "rain_midnight": rain_midnight,
        "last_midnight": last_midnight.isoformat(),
    }
    tmp_file = RAIN_STATE_FILE + ".tmp"
    try:
        with open(tmp_file, "w") as f:
            json.dump(state, f)
        # Atomic on POSIX: rename either fully completes or doesn't
        # happen at all. Never leaves a half-written/truncated JSON
        # in place of the real file, even if power is cut mid-write.
        os.rename(tmp_file, RAIN_STATE_FILE)
    except Exception as e:
        # Don't crash the main loop over a save failure - just log it
        # and try again next cycle in ~2 min.
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Rain state save failed: {e}")
        write_journal("RAIN_STATE_SAVE_ERR", f"save failed: {e}")


# --- Main loop ---

def main():
    rain_1h_bucket, rain_24h_bucket, rain_midnight, last_midnight = load_rain_state()
    last_submit = 0

    try:
        ser = open_serial()
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Serial open failed: {e}")
        return

    # Silence sentinel: time of last successfully parsed line.
    # Initialized to now so a slow first line doesn't false-trip.
    last_valid_line = time.time()

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()

            # --- Silence sentinel check (runs every iteration) ---
            # readline() returns "" every 5s when the Pico is quiet,
            # so this is evaluated frequently even with no data.
            # After SILENCE_TIMEOUT (360s = 3 missed 2-min cycles) of no
            # valid line, log a "Pico silent" entry to the journal and
            # reopen the serial port.
            if time.time() - last_valid_line >= SILENCE_TIMEOUT:
                silent_for = int(time.time() - last_valid_line)
                print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Pico silent {silent_for}s - reopening serial")
                write_journal("PICO_SILENT", f"no valid line for {silent_for}s; reopening serial")
                try:
                    ser.close()
                except Exception:
                    pass
                time.sleep(5)
                ser = open_serial()
                # Reset so we don't re-trip every iteration while
                # waiting for the Pico to come back so it doesn't spam our log with fake timeout entries.
                # If it's still frozen, this will trip again in another SILENCE_TIMEOUT.
                last_valid_line = time.time()
                continue

            if not line or "," not in line:
                continue

            parsed = parse_line(line)
            if parsed is None:
                continue

            # Valid data arrived - reset the silence clock to zero again, to prevent fake positive Pico dropouts.
            last_valid_line = time.time()

            write_journal("PICO_RAW", line.strip())

            temp_f, humidity, pressure, wind_sustained, wind_gust, wind_dir, rainfall = parsed

            now = time.time()

            # Rain-since-midnight rollover, checked against LOCAL date.
            today_local = local_date()
            if today_local > last_midnight:
                rain_midnight = 0.0
                last_midnight = today_local

            # rainfall may be None if the (GPIO) field somehow came blank;
            # treat None as "no tips this cycle" for accumulation purposes.
            if rainfall is not None and rainfall > 0:
                rain_1h_bucket.append((now, rainfall))
                rain_24h_bucket.append((now, rainfall))
                rain_midnight += rainfall

            rain_1h_bucket = [(t, r) for t, r in rain_1h_bucket if now - t <= 3600]
            rain_24h_bucket = [(t, r) for t, r in rain_24h_bucket if now - t <= 86400]

            rain_1h = sum(r for _, r in rain_1h_bucket)
            rain_24h = sum(r for _, r in rain_24h_bucket)

            save_rain_state(rain_1h_bucket, rain_24h_bucket, rain_midnight, last_midnight)

            if now - last_submit >= 300:
                packet = build_aprs_packet(
                    temp_f, humidity, pressure,
                    wind_dir, wind_sustained, wind_gust,
                    rain_1h, rain_24h, rain_midnight
                )
                success = submit_aprs(packet)
                if success:
                    write_journal("APRS_OK", packet)
                else:
                    write_journal("APRS_FAIL", packet)
                write_journal("PICO_RAIN", f"rain_1h={rain_1h:.4f},rain_24h={rain_24h:.4f},rain_midnight={rain_midnight:.4f}")
                last_submit = now

        except serial.SerialException:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Serial lost, reconnecting...")
            try:
                ser.close()
            except Exception:
                pass
            time.sleep(5)
            ser = open_serial()
            last_valid_line = time.time()

        except Exception as e:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()