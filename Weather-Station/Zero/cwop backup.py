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

import serial # type: ignore
import serial.tools.list_ports # type: ignore
import socket
import time
from datetime import datetime, timezone
from config import STATION_ID, LAT, LON, PASSCODE, DRY_RUN

# --- Journal file path ---

JOURNAL_FILE = "/mnt/data/weather/journal.csv"

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

    # Convert wind direction string to degrees
    dir_map = {"N":0,"NE":45,"E":90,"SE":135,"S":180,"SW":225,"W":270,"NW":315}
    wind_deg = dir_map.get(wind_dir, 0)

    # APRS weather format
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
        # Pico will appear in Linux as /dev/ttyACM0, but if disconnected and reconnected while Linux remains booted,
        # the reconnected Pico will appear as /dev/ttyACM1. So, do NOT hardcode it's device name
        # If Linux reboots, Pico's device name reverts back to ttyACM0
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'ACM' in port.device:
                print(f"Pico found on {port.device}")
                return port.device
        print("Pico not found, retrying in 10s...")
        time.sleep(10)

# --- APRS submission ---

def submit_aprs(packet):
    if DRY_RUN:
        print(f"DRY RUN - WOULD SUBMIT: {packet}")
        return True
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        s.connect(("cwop.aprs.net", 14580))
        s.recv(1024)  # read server greeting
        # Login
        login = f"user {STATION_ID} pass {PASSCODE} vers PiWeather 1.0\r\n"
        s.sendall(login.encode())
        time.sleep(2) # Findu instructions ask for a 2-second pause after login and before login acknowledgement
        s.recv(1024)  # read login acknowledgement
        # Send packet
        s.sendall((packet + "\r\n").encode())
        time.sleep(2) # Findu instructions ask for a 2-second pause after sending and before disconencting
        s.close()
        print(f"Submitted: {packet}")
        return True
    except Exception as e:
        print(f"APRS submit failed: {e}")
        write_journal("ERROR", f"APRS submit failed: {e}")
        return False

# --- Journal Logging ---

def write_journal(event_type, data_str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp},{event_type},{data_str}\n"
    try:
        with open(JOURNAL_FILE, "a") as f:
            f.write(line)
    except Exception as e:
        print(f"Journal write failed: {e}")

# --- Main loop ---

def parse_line(line):
    parts = line.strip().split(",")
    if len(parts) != 8:
        return None
    try:
        temp_f = float(parts[0])
        humidity = float(parts[1])
        pressure = float(parts[2])
        # parts[3] is uv index LTR 390 sensor -- not yet installed, skipping for now
        wind_sustained = float(parts[4])
        wind_gust = float(parts[5])
        wind_dir = parts[6]
        rainfall = float(parts[7])
        return temp_f, humidity, pressure, wind_sustained, wind_gust, wind_dir, rainfall
    except:
        return None

def main():
    rain_1h_bucket = []    # (timestamp, inches) tuples
    rain_24h_bucket = []
    rain_midnight = 0.0
    last_submit = 0
    last_midnight = datetime.now(timezone.utc).date()

    port = find_pico()

    try:
        ser = serial.Serial(port, 115200, timeout=5)
    except Exception as e:
        print(f"Serial open failed: {e}")
        return

    print("Reading Pico serial stream...")

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()

            # Reject lines that are blank or malformed 
            if not line or "," not in line:
                continue

            # Reject lines that don't match expected field structure
            parsed = parse_line(line)
            if parsed is None:
                continue
            
            write_journal("RAW", line.strip())      # Write 2-minute raw Pico data into CSV Journal for Grafana weather dashboard

            temp_f, humidity, pressure, wind_sustained, wind_gust, wind_dir, rainfall = parsed

            now = time.time()
            now_utc = datetime.now(timezone.utc)

            # Reset midnight rain counter at midnight UTC
            if now_utc.date() > last_midnight:
                rain_midnight = 0.0
                last_midnight = now_utc.date()

            # Accumulate rain
            if rainfall > 0:
                rain_1h_bucket.append((now, rainfall))
                rain_24h_bucket.append((now, rainfall))
                rain_midnight += rainfall

            # Prune old rain buckets
            rain_1h_bucket = [(t, r) for t, r in rain_1h_bucket if now - t <= 3600]
            rain_24h_bucket = [(t, r) for t, r in rain_24h_bucket if now - t <= 86400]

            # Sum remaining buckets for totals
            rain_1h = sum(r for _, r in rain_1h_bucket)
            rain_24h = sum(r for _, r in rain_24h_bucket)

            # Submit every 5 minutes
            if now - last_submit >= 300:
                packet = build_aprs_packet(
                    temp_f, humidity, pressure,
                    wind_dir, wind_sustained, wind_gust,
                    rain_1h, rain_24h, rain_midnight
                )
                submit_aprs(packet)
                write_journal("SUBMITTED", packet)
                last_submit = now

        except serial.SerialException:
            print("Serial lost, reconnecting...")
            ser.close()
            time.sleep(5)
            port = find_pico()
            ser = serial.Serial(port, 115200, timeout=5)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()