# ─────────────────────────────────────────────────────────
# pico_diagnostics.py
# Comprehensive Pico W hardware and network diagnostic test
# Run on a bare Pico W with no sensors attached
#
# Requires config.py on saved the Pico itself with:
#   WIFI_SSID     = "your_ssid"
#   WIFI_PASSWORD = "your_password"
#
# SECTIONS:
#   SYSTEM    - unique ID, CPU clock, firmware, reset cause,
#               chip temp, RAM + usage, flash storage + usage
#   TIME      - RTC read, NTP clock sync and verification
#   NETWORK   - WiFi info, local ping, HTTP/HTTPS GET,
#               internal and external DNS resolution
#   HARDWARE  - I2C, SPI, UART, PWM, ADC (GP26)
#   RESILIENCE - exception handling
#
# All tests report PASS or FAIL independently
# MicroPython v1.28.0+ on Raspberry Pi Pico W
# ─────────────────────────────────────────────────────────

import network
import time
import machine
import os
import gc
import sys
import socket
import ubinascii
import ntptime
import urequests
from config import WIFI_SSID, WIFI_PASSWORD

# ── CONNECT ───────────────────────────────────────────────
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(f"Connecting to {WIFI_SSID}...")
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 15
start = time.time()
while not wlan.isconnected():
    elapsed = time.time() - start
    if elapsed > timeout:
        print("FAILED - connection timed out")
        raise SystemExit
    print(f"  waiting... {elapsed}s")
    time.sleep(1)

print(f"  Connected in {time.time() - start}s")

# ── SYSTEM ────────────────────────────────────────────────
print("\n── SYSTEM ──────────────────────────────────────────")

uid = ubinascii.hexlify(machine.unique_id()).decode()
print(f"  Unique ID  : {uid}")

freq_mhz = machine.freq() // 1_000_000
print(f"  CPU freq   : {freq_mhz} MHz")

print(f"  MicroPython: {sys.version}")
print(f"  MP impl    : {sys.implementation[0]} v{sys.implementation[1][0]}.{sys.implementation[1][1]}.{sys.implementation[1][2]}")

reset_causes = {
    1: "Power on",
    2: "External reset",
    3: "Software reset",
    4: "Watchdog",
    5: "Deep sleep",
}
reset = machine.reset_cause()
reset_str = reset_causes.get(reset, f"Unknown ({reset})")
print(f"  Reset cause: {reset_str}")

sensor_temp = machine.ADC(4)
conversion = 3.3 / 65535
reading = sensor_temp.read_u16() * conversion
temp_c = 27 - (reading - 0.706) / 0.001721
print(f"  Chip temp  : {temp_c:.1f} C")

gc.collect()
ram_free = gc.mem_free()
ram_used = gc.mem_alloc()
ram_total = ram_free + ram_used
ram_pct = (ram_used / ram_total) * 100
print(f"  RAM free   : {ram_free} bytes")
print(f"  RAM used   : {ram_used} bytes ({ram_pct:.1f}%)")

fs = os.statvfs('/')
block_size = fs[0]
total_blocks = fs[2]
free_blocks = fs[3]
storage_total = block_size * total_blocks
storage_free = block_size * free_blocks
storage_used = storage_total - storage_free
storage_pct = (storage_used / storage_total) * 100
print(f"  Flash total: {storage_total} bytes")
print(f"  Flash free : {storage_free} bytes ({storage_pct:.1f}% used)")

# ── TIME ─────────────────────────────────────────────────
print("\n── TIME ────────────────────────────────────────────")

rtc = machine.RTC()
sys_time = rtc.datetime()
print(f"  System RTC : {sys_time[0]}-{sys_time[1]:02d}-{sys_time[2]:02d} {sys_time[4]:02d}:{sys_time[5]:02d}:{sys_time[6]:02d} UTC")

print("  Syncing NTP...")
try:
    ntptime.settime()
    sys_time = rtc.datetime()
    print(f"  NTP synced : {sys_time[0]}-{sys_time[1]:02d}-{sys_time[2]:02d} {sys_time[4]:02d}:{sys_time[5]:02d}:{sys_time[6]:02d} UTC")
except Exception as e:
    print(f"  NTP FAILED : {e}")

# ── NETWORK ──────────────────────────────────────────────
print("\n── NETWORK ─────────────────────────────────────────")

status = wlan.ifconfig()
mac = wlan.config('mac')
mac_str = ':'.join(f'{b:02x}' for b in mac)
rssi = wlan.status('rssi')
print(f"  IP address : {status[0]}")
print(f"  Gateway    : {status[2]}")
print(f"  DNS        : {status[3]}")
print(f"  MAC        : {mac_str}")
print(f"  Signal     : {rssi} dBm")

print("  DNS resolve: pihole (10.0.0.101)...")
try:
    resolved = socket.getaddrinfo("pihole", 53)
    print(f"  DNS result : {resolved[0][4][0]} PASS")
except Exception as e:
    print(f"  DNS FAILED : {e}")

print("  Ping pihole: 10.0.0.101:53...")
try:
    s = socket.socket()
    s.settimeout(3)
    s.connect(("10.0.0.101", 53))
    s.close()
    print("  Ping result: PASS")
except Exception as e:
    print(f"  Ping FAILED: {e}")

print("  Testing HTTP GET...")
try:
    r = urequests.get("http://httpbin.org/get")
    print(f"  HTTP status: {r.status_code}")
    r.close()
    print("  GET test   : PASS")
except Exception as e:
    print(f"  GET FAILED : {e}")

print("  Testing HTTPS GET...")
try:
    r = urequests.get("https://httpbin.org/get")
    print(f"  HTTPS status: {r.status_code}")
    r.close()
    print("  HTTPS test  : PASS")
except Exception as e:
    print(f"  HTTPS FAILED: {e}")

print("  DNS external: google.com...")
try:
    resolved = socket.getaddrinfo("google.com", 80)
    print(f"  DNS result  : {resolved[0][4][0]} PASS")
except Exception as e:
    print(f"  DNS FAILED  : {e}")

# ── HARDWARE BUSES ───────────────────────────────────────
print("\n── HARDWARE BUSES ──────────────────────────────────")

try:
    i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1))
    devices = i2c.scan()
    print(f"  I2C bus    : PASS ({len(devices)} devices found)")
except Exception as e:
    print(f"  I2C FAILED : {e}")

try:
    spi = machine.SPI(0, baudrate=1000000)
    print("  SPI bus    : PASS")
except Exception as e:
    print(f"  SPI FAILED : {e}")

try:
    uart = machine.UART(0, baudrate=9600)
    print("  UART       : PASS")
except Exception as e:
    print(f"  UART FAILED: {e}")

try:
    pwm = machine.PWM(machine.Pin(15))
    pwm.freq(1000)
    pwm.duty_u16(32768)
    pwm.deinit()
    print("  PWM        : PASS")
except Exception as e:
    print(f"  PWM FAILED : {e}")

try:
    adc = machine.ADC(machine.Pin(26))
    reading = adc.read_u16()
    print(f"  ADC GP26   : PASS (raw {reading})")
except Exception as e:
    print(f"  ADC FAILED : {e}")

# ── SYSTEM RESILIENCE ────────────────────────────────────
print("\n── SYSTEM RESILIENCE ───────────────────────────────")

try:
    result = 1 / 0
except ZeroDivisionError:
    print("  Exception  : PASS")

# ── DONE ─────────────────────────────────────────────────
print("\n── COMPLETE ────────────────────────────────────────")
print("  Disconnecting...")
wlan.disconnect()
wlan.active(False)
print("  Done.")