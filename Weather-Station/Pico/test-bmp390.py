# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=0, scl=Pin(1), sda=Pin(0))

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")
print("")
bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)

# Calibration constants
ELEVATION_M = 210.0
PRESSURE_OFFSET_HPA = 1.3

try:
    while True:
        station_pressure = bmp.pressure
        temp = bmp.temperature
        slp = (station_pressure / (1.0 - ELEVATION_M / 44330.77) ** (1 / 0.1902632)) - PRESSURE_OFFSET_HPA
        temp_f = (temp * 9/5) + 32
        print(f"Station: {station_pressure:.2f} hPa  |  SLP: {slp:.2f} hPa  |  Temp: {temp_f:.2f} F")
        print(f"Station: {station_pressure:.2f} hPa  |  SLP: {slp:.2f} hPa  |  Temp: {temp:.2f} C")
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopped.")