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
# RP2040 hardware cap is ~8.3s max - cannot be paused/disabled once started, only fed.
# Fed once per main loop iteration (every 5s via SAMPLE_INTERVAL) so a hung I2C
# read (bus lockup - the known failure mode of some sensors) causes a hard reset within 8s
# instead of the Pico going silent for the rest of the storm, if the hygro sensor caused I2C to lock up.
wdt = WDT(timeout=8000)

# --- BMP390 setup ---
# Jiri Krecek (Archer Dynamics)
# SLP is calculated live each reading using the hypsometric formula.
# No hardcoded sea_level_pressure or altitude setter - those freeze the value.
# PRESSURE_OFFSET_HPA: this BMP390 unit reads high vs KORD by 1.3 hPa.
# Validated 2026-04-28 against KORD METAR SLP in stable weather.
# To recalibrate: run testbmp390.py, compare SLP output to current KORD METAR SLP,
# set offset = sensor SLP - KORD SLP.
bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)
ELEVATION_M = 210.0
PRESSURE_OFFSET_HPA = 1.3
time.sleep(1)

# --- HDC3022 setup ---
HDC3022_ADDR = 0x44

def read_hdc3022():
    i2c.writeto(HDC3022_ADDR, bytes([0x24, 0x00]))
    time.sleep_ms(50)
    data = i2c.readfrom(HDC3022_ADDR, 6)
    temp_raw = (data[0] << 8) | data[1]
    temp_c = -45 + 175 * (temp_raw / 65535)
    temp_f = temp_c * 9/5 + 32
    hum_raw = (data[3] << 8) | data[4]
    humidity = 100 * (hum_raw / 65535)
    return temp_c, temp_f, humidity

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

while True:
    wdt.feed()

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
        station_pressure = bmp.pressure
        slp = (station_pressure / (1.0 - ELEVATION_M / 44330.77) ** (1 / 0.1902632)) - PRESSURE_OFFSET_HPA
        temp_c, temp_f, humidity = read_hdc3022()
        uv = 0.0
        rainfall = read_rain()

        wind_dir = get_wind_direction(vane_readings)

        valid_speeds = [s for s in speed_readings if s is not None]
        wind_sustained = sum(valid_speeds) / len(valid_speeds) if valid_speeds else 0.0
        wind_gust = max(valid_speeds) if valid_speeds else 0.0

        msg = f"{temp_f:.1f},{humidity:.1f},{slp:.2f},{uv:.2f},{wind_sustained:.1f},{wind_gust:.1f},{wind_dir},{rainfall:.3f}"
        print(msg)

        sample_count = 0

    time.sleep(SAMPLE_INTERVAL)