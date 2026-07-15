#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# weather_ingest.py
# Pulls journal.csv from the weather node over SSH, parses PICO_RAW
# lines, and inserts them into PostgreSQL on syscheck.
#
# Runs ON SYSCHECK. Pull model: syscheck reaches out to weather.
# The weather node knows nothing about this script.
#
# IDEMPOTENT BY CONSTRUCTION:
# weather.station_readings has ts as its PRIMARY KEY, so a duplicate
# reading is impossible at the database level. This script reads the
# WHOLE journal every run and lets ON CONFLICT DO NOTHING discard
# whatever is already stored. No high-water mark, no state file,
# nothing to get out of sync. Re-running is always safe.

import subprocess
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values

# --- Config ---

from config import WEATHER_HOST, DB_DSN

JOURNAL_PATH = "/mnt/data/weather/journal.csv"
SSH_TIMEOUT = 30                   # seconds before we give up on the pull
DRY_RUN = True                     # True = parse and report, never write


# --- Pull ---

def fetch_journal():
    """Cat journal.csv on the weather node over SSH. Returns the text,
    or None if the node is unreachable. Never raises - a down weather
    node is an expected condition, not a crash."""
    cmd = [
        "ssh",
        "-o", "BatchMode=yes",              # never prompt for a password
        "-o", f"ConnectTimeout={SSH_TIMEOUT}",
        WEATHER_HOST,
        f"cat {JOURNAL_PATH}",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SSH_TIMEOUT,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"SSH failed (exit {e.returncode}): {e.stderr.strip()}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"SSH timed out after {SSH_TIMEOUT}s", file=sys.stderr)
        return None


# --- Parse ---

def to_float_or_none(s):
    """Empty field means the sensor failed that cycle. Return None so it
    lands in the DB as NULL, not as a fake 0."""
    s = s.strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_journal_line(line):
    """Returns a row tuple for a PICO_RAW line, or None for anything else.
    journal.csv holds many event types (APRS_OK, PICO_RAIN, RAIN_STATE_LOAD
    ...). Only PICO_RAW carries sensor readings. Everything else is the
    operational record and is deliberately ignored here.

    PICO_RAW format, 10 fields:
      ts, PICO_RAW, temp_f, humidity, slp, uv, wind_speed, wind_gust, wind_dir, rain
    """
    parts = line.strip().split(",")

    if len(parts) != 10:
        return None
    if parts[1] != "PICO_RAW":
        return None

    try:
        ts = datetime.fromisoformat(parts[0])
    except ValueError:
        return None

    temp_f     = to_float_or_none(parts[2])
    humidity   = to_float_or_none(parts[3])
    pressure   = to_float_or_none(parts[4])
    # parts[5] is uv - hardcoded 0.0 placeholder on the Pico, discarded here
    wind_speed = to_float_or_none(parts[6])
    wind_gust  = to_float_or_none(parts[7])
    wind_dir   = parts[8].strip() or None
    rain_in    = to_float_or_none(parts[9])

    return (ts, temp_f, humidity, pressure, wind_dir, wind_speed, wind_gust, rain_in)


def parse_journal(text):
    rows = []
    for line in text.splitlines():
        row = parse_journal_line(line)
        if row is not None:
            rows.append(row)
    return rows


# --- Insert ---

INSERT_SQL = """
    INSERT INTO weather.station_readings
        (ts, temp_f, humidity_pct, pressure_hpa, wind_dir,
         wind_speed_mph, wind_gust_mph, rain_in)
    VALUES %s
    ON CONFLICT (ts) DO NOTHING
"""


def insert_rows(rows):
    """Insert all rows in one batch. Returns the number actually inserted
    (rows already present are silently discarded by ON CONFLICT)."""
    with psycopg2.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            execute_values(cur, INSERT_SQL, rows, page_size=500)
            return cur.rowcount


# --- Main ---

def main():
    text = fetch_journal()
    if text is None:
        sys.exit(1)

    rows = parse_journal(text)
    if not rows:
        print("No PICO_RAW rows found in journal - nothing to do.")
        return

    print(f"Parsed {len(rows)} readings "
          f"({rows[0][0].isoformat()} to {rows[-1][0].isoformat()})")

    if DRY_RUN:
        print("DRY RUN - no database writes")
        return

    try:
        inserted = insert_rows(rows)
    except psycopg2.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Inserted {inserted} new, skipped {len(rows) - inserted} already present")


if __name__ == "__main__":
    main()