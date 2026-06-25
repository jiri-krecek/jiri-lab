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

def build_aprs_packet(temp_f, humidity, pressure, wind_dir, wind_sustained, wind_gust, rain_1h, rain_24h, rain_midnight):
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%d%H%Mz")

    lat = format_lat(LAT)
    lon = format_lon(LON)

    dir_map = {"N":0,"NE":45,"E":90,"SE":135,"S":180,"SW":225,"W":270,"NW":315}
    wind_deg = dir_map.get(wind_dir, 0)

    hum_display = min(int(humidity), 99)
    packet = (
        f"{STATION_ID}>APRS,TCPIP*:@{timestamp}{lat}/{lon}"
        f"_{wind_deg:03d}/{int(wind_sustained):03d}g{int(wind_gust):03d}"
        f"t{int(temp_f):03d}r{int(rain_1h*100):03d}"
        f"p{int(rain_24h*100):03d}P{int(rain_midnight*100):03d}"
        f"h{hum_display:02d}b{int(pressure*10):05d}"
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

# --- Main loop ---

def parse_line(line):
    parts = line.strip().split(",")
    if len(parts) != 8:
        return None
    try:
        temp_f = float(parts[0])
        humidity = float(parts[1])
        pressure = float(parts[2])
        wind_sustained = float(parts[4])
        wind_gust = float(parts[5])
        wind_dir = parts[6]
        rainfall = float(parts[7])
        return temp_f, humidity, pressure, wind_sustained, wind_gust, wind_dir, rainfall
    except:
        return None

def main():
    rain_1h_bucket = []
    rain_24h_bucket = []
    rain_midnight = 0.0
    last_submit = 0
    # Track the LOCAL calendar date so rain_midnight resets at local
    # midnight (00:00 CDT/CST), per CWOP spec - not at UTC midnight.
    last_midnight = local_date()

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

            if rainfall > 0:
                rain_1h_bucket.append((now, rainfall))
                rain_24h_bucket.append((now, rainfall))
                rain_midnight += rainfall

            rain_1h_bucket = [(t, r) for t, r in rain_1h_bucket if now - t <= 3600]
            rain_24h_bucket = [(t, r) for t, r in rain_24h_bucket if now - t <= 86400]

            rain_1h = sum(r for _, r in rain_1h_bucket)
            rain_24h = sum(r for _, r in rain_24h_bucket)

            if now - last_submit >= 300:
                packet = build_aprs_packet(
                    temp_f, humidity, pressure,
                    wind_dir, wind_sustained, wind_gust,
                    rain_1h, rain_24h, rain_midnight
                )
                submit_aprs(packet)
                write_journal("APRS_SUB", packet)
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