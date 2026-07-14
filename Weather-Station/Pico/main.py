# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# Weather Station - Pico 2W
# Sensors: BMP390 (pressure), HDC3022 (temp, humidity), Wind Vane, Anemometer, Rain Gauge
# Barometric Pressure:
# Pressure validated against known source: Chicago O'Hare (KORD) current METAR:
# https://aviationweather.gov/api/data/metar?ids=KORD&format=raw
# You may need to replace the airport code for a known manned airport nearby with comparable elevation
#
# RESILIENCE DESIGN (added 2026-07-10):
# Four layers of protection so a transient I2C failure never leaves the Pico
# dead at the REPL (the recurring failure mode that plagued this station):
#   1. Sensor init wrapped in a retry loop - a boot-time I2C hiccup retries
#      instead of throwing an unhandled exception and crashing to REPL.
#   2. Every sensor read wrapped in try/except - one flaky sensor degrades
#      gracefully; the others still report.
#   3. wdt.feed() called unconditionally at the top of the loop - a transient
#      read failure never accidentally starves the watchdog.
#   4. Consecutive-failure counter - if reads fail for MAX_FAIL_CYCLES report
#      cycles in a row (genuinely wedged bus), we STOP feeding the watchdog
#      on purpose and let it perform a clean hardware reset.

import time
from machine import Pin, I2C, ADC, WDT # type: ignore
from micropython_bmpxxx import bmpxxx
from compass import voltage_to_direction, get_wind_direction

# I2C bus - shared by all sensors
i2c = I2C(0, sda=Pin(0), scl=Pin(1))

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")

# --- Hardware watchdog ---
# RP2040/RP2350 hardware cap is ~8.3s max - cannot be paused/disabled once started, only fed.
# Fed once per main loop iteration (every 5s via SAMPLE_INTERVAL) so a hung I2C
# read (bus lockup - the known failure mode of some sensors) causes a hard reset within 8s
# instead of the Pico going silent. See RESILIENCE DESIGN note above: the watchdog is
# deliberately allowed to fire only when reads are persistently wedged, never on a single blip.
wdt = WDT(timeout=8000)

# --- Sensor config / addresses ---
BMP390_ADDR = 0x77
HDC3022_ADDR = 0x44
ELEVATION_M = 210.0
# PRESSURE_OFFSET_HPA: this BMP390 unit reads high vs KORD by 1.3 hPa.
# Validated 2026-04-28 against KORD METAR SLP in stable weather.
# To recalibrate: run testbmp390.py, compare SLP output to current KORD METAR SLP,
# set offset = sensor SLP - KORD SLP.
PRESSURE_OFFSET_HPA = 1.3

# --- Resilience tuning ---
INIT_ATTEMPTS = 5       # boot-time init retries per sensor
INIT_RETRY_DELAY = 2    # seconds between init retries
# Report cycles (every SAMPLE_COUNT * SAMPLE_INTERVAL = ~2 min) of total sensor
# failure before we let the watchdog hard-reset. 3 cycles = ~6 min wedged.
MAX_FAIL_CYCLES = 3


def init_bmp390():
    """Attempt to initialize the BMP390. Returns the sensor object or None.
    Never raises - a persistent failure returns None so the station can still
    come up and report the other sensors while retrying pressure in the loop."""
    for attempt in range(INIT_ATTEMPTS):
        try:
            sensor = bmpxxx.BMP390(i2c=i2c, address=BMP390_ADDR)
            print("BMP390 initialized")
            return sensor
        except Exception as e:
            print(f"BMP390 init attempt {attempt + 1}/{INIT_ATTEMPTS} failed: {e}")
            time.sleep(INIT_RETRY_DELAY)
    print("BMP390 failed all init attempts - will keep retrying in main loop")
    return None


# --- BMP390 setup (with retry) ---
bmp = init_bmp390()
time.sleep(1)


# --- HDC3022 read ---
def read_hdc3022():
    """Returns (temp_c, temp_f, humidity) or None on failure."""
    try:
        i2c.writeto(HDC3022_ADDR, bytes([0x24, 0x00]))
        time.sleep_ms(50)
        data = i2c.readfrom(HDC3022_ADDR, 6)
        temp_raw = (data[0] << 8) | data[1]
        temp_c = -45 + 175 * (temp_raw / 65535)
        temp_f = temp_c * 9 / 5 + 32
        hum_raw = (data[3] << 8) | data[4]
        humidity = 100 * (hum_raw / 65535)
        return temp_c, temp_f, humidity
    except Exception as e:
        print(f"HDC3022 read failed: {e}")
        return None


# --- BMP390 pressure read ---
def read_pressure(sensor):
    """Returns station pressure (hPa) or None on failure."""
    try:
        return sensor.pressure
    except Exception as e:
        print(f"BMP390 read failed: {e}")
        return None


# --- Wind Vane setup (GP26, ADC) ---
vane_adc = ADC(Pin(26))

def read_vane_voltage():
    raw = vane_adc.read_u16()
    return raw * 3.3 / 65535

# --- Anemometer setup (GP4, pulse counter) ---
ANE_PIN = Pin(4, Pin.IN, Pin.PULL_UP)
pulse_count = 0

def count_pulse(pin):
    global pulse_count
    pulse_count += 1

ANE_PIN.irq(trigger=Pin.IRQ_RISING, handler=count_pulse)

def read_wind_speed():
    global pulse_count
    count = pulse_count
    pulse_count = 0
    return (count / 5) * 1.492

# --- Rain Gauge setup (GP3, pulse counter) ---
RAIN_PIN = Pin(3, Pin.IN, Pin.PULL_UP)
rain_count = 0
last_rain_time = 0

def rain_pulse(pin):
    global rain_count, last_rain_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_rain_time) > 1990:
        rain_count += 1
        last_rain_time = now

RAIN_PIN.irq(trigger=Pin.IRQ_FALLING, handler=rain_pulse)

def read_rain():
    global rain_count
    count = rain_count
    rain_count = 0
    # SparkFun SEN-15901: each tip = 0.011 inches of rain
    return count * 0.011

# --- Sampling config ---
SAMPLE_INTERVAL = 5     # seconds between samples
SAMPLE_COUNT = 24       # samples per report (24 x 5s = 120s = 2 minutes)

vane_readings = []
speed_readings = []
sample_count = 0
fail_cycles = 0         # consecutive report cycles with total sensor failure

while True:
    # Layer 3: feed the watchdog unconditionally while the loop is alive.
    # The ONLY exception is the deliberate wedged-bus path below, where we
    # stop feeding so the watchdog can force a clean reset.
    wdt.feed()

    # Wind is sampled every 5s so gusts are caught between full reports.
    voltage = read_vane_voltage()
    direction = voltage_to_direction(voltage)
    mph = read_wind_speed()

    vane_readings.append(direction)
    speed_readings.append(mph)

    if len(vane_readings) > SAMPLE_COUNT:
        vane_readings.pop(0)
    if len(speed_readings) > SAMPLE_COUNT:
        speed_readings.pop(0)

    sample_count += 1

    if sample_count >= SAMPLE_COUNT:
        # Layer 1 (recovery): if pressure sensor is dead, try to bring it back.
        if bmp is None:
            bmp = init_bmp390()

        # Layer 2: read each I2C sensor independently; failures return None.
        station_pressure = read_pressure(bmp) if bmp is not None else None
        hdc = read_hdc3022()

        # These never touch the I2C bus, so they don't participate in the
        # I2C-failure logic - they read fine even if the bus is wedged.
        uv = 0.0
        rainfall = read_rain()
        wind_dir = get_wind_direction(vane_readings)

        valid_speeds = [s for s in speed_readings if s is not None]
        wind_sustained = sum(valid_speeds) / len(valid_speeds) if valid_speeds else 0.0
        wind_gust = max(valid_speeds) if valid_speeds else 0.0

        # Layer 4: track consecutive TOTAL I2C failures. If BOTH I2C sensors
        # fail together, the bus is likely wedged. Count it. If only one fails,
        # that's partial degradation - report what we have and reset the counter.
        both_i2c_failed = (station_pressure is None) and (hdc is None)
        if both_i2c_failed:
            fail_cycles += 1
            print(f"Both I2C sensors failed - cycle {fail_cycles}/{MAX_FAIL_CYCLES}")
        else:
            fail_cycles = 0

        if fail_cycles >= MAX_FAIL_CYCLES:
            # Deliberately stop feeding the watchdog and let it hard-reset.
            # init retry (Layer 1) will run again cleanly on the fresh boot.
            print("I2C bus persistently wedged - allowing watchdog reset...")
            while True:
                time.sleep(1)   # no wdt.feed() here -> reset within ~8s

        # Build the report from whatever we successfully read.
        # Missing values are emitted as blanks so downstream parsing can
        # decide how to handle them, rather than reporting bogus zeros.
        if hdc is not None:
            temp_c, temp_f, humidity = hdc
            temp_str = f"{temp_f:.1f}"
            hum_str = f"{humidity:.1f}"
        else:
            temp_str = ""
            hum_str = ""

        if station_pressure is not None:
            slp = (station_pressure / (1.0 - ELEVATION_M / 44330.77) ** (1 / 0.1902632)) - PRESSURE_OFFSET_HPA
            slp_str = f"{slp:.2f}"
        else:
            slp_str = ""

        msg = f"{temp_str},{hum_str},{slp_str},{uv:.2f},{wind_sustained:.1f},{wind_gust:.1f},{wind_dir},{rainfall:.3f}"
        print(msg)

        sample_count = 0

    time.sleep(SAMPLE_INTERVAL)