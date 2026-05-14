# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# kord_scraper.py
# Fetches hourly KORD METAR and logs SLP and wind data for calibration comparison
# Runs on Pi Zero 2W via cron, once per hour
# Author: Jiri Krecek (Archer Dynamics)

import requests
import re
from datetime import datetime, timezone

METAR_URL = "https://aviationweather.gov/api/data/metar?ids=KORD&format=raw"
KORD_LOG = "/mnt/data/weather/kord_slp.csv"

def fetch_metar():
    try:
        response = requests.get(METAR_URL, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"METAR fetch failed: {e}")
        return None

def parse_metar(metar):
    # SLP — format SLP### where ### is hPa x10 minus 1000 or 900
    slp_match = re.search(r'SLP(\d{3})', metar)
    if not slp_match:
        return None
    slp_raw = int(slp_match.group(1))
    # NOAA convention: if raw < 500, prefix with 10, else prefix with 9
    slp_hpa = (1000 + slp_raw / 10) if slp_raw < 500 else (900 + slp_raw / 10)

    # Wind — format DDDSSGGgKT or DDDSSKT
    wind_match = re.search(r'(\d{3})(\d{2,3})(?:G(\d{2,3}))?KT', metar)
    if not wind_match:
        return None
    wind_dir = int(wind_match.group(1))
    wind_kt = int(wind_match.group(2))
    gust_kt = int(wind_match.group(3)) if wind_match.group(3) else wind_kt

    return slp_hpa, wind_dir, wind_kt, gust_kt

def log_kord(slp_hpa, wind_dir, wind_kt, gust_kt):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp},{slp_hpa:.1f},{wind_dir},{wind_kt},{gust_kt}\n"
    try:
        with open(KORD_LOG, "a") as f:
            f.write(line)
        print(f"Logged: {line.strip()}")
    except Exception as e:
        print(f"Log write failed: {e}")

def main():
    metar = fetch_metar()
    if metar is None:
        return
    parsed = parse_metar(metar)
    if parsed is None:
        print("METAR parse failed")
        return
    slp_hpa, wind_dir, wind_kt, gust_kt = parsed
    log_kord(slp_hpa, wind_dir, wind_kt, gust_kt)

if __name__ == "__main__":
    main()