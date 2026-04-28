# BMP390 sensor driver: micropython_bmpxxx library
# Author: Brad Carlile (bradcar)
# GitHub: https://github.com/bradcar/MicroPython_BMPxxx
# License: Open source - see LICENSE.md in repo


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


# Jiri Krecek (Archer Dynamics)
# Update the device address if your device is not found. 
# Some BMP390 sensors have 0x76 and some have 0x77 address.
bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)

sea_level_pressure = bmp.sea_level_pressure
print(f"initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

sea_level_pressure = bmp.sea_level_pressure
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

# Jiri Krecek (Archer Dynamics)
# Use METAR information published on the hour and be aware that in active weather the metrics change rapidly
# Do these adjustments in steady weather when metrics do not change, not in active storms when METARs become obsolete fast
# This is done only once during initial setup and allows the driver to recalculate your precise sea level pressure
# Never use this value directly. It takes your elevation, your station pressure and adjusts the driver
# to match what a good known reading from the nearest airport is, given your elevation and actual station pressure
# calculates the actual normalized SLP (sea level pressure) for your location
bmp.sea_level_pressure = 1001.0
print(f"Adjusted sea level pressure = {bmp.sea_level_pressure:.2f} hPa")


# For the SLP calculation to be accurate you must set known altitude in meters and the sea level pressure will recalculate
bmp.altitude = 210.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")


# Update by: Jiri Krecek (Archer Dynamics)
# Sensor calibration offset: this BMP390 unit reads high vs KORD/KDPA barometric reference by ~0.5 hPa.
# Determined by comparing refined SLP output against current METAR from Chicago O'Hare (KORD) and DuPage (KDPA) airports.
# Offset = sensor refined SLP - current KORD SLP (1003.03 - 1002.50 = 0.53, rounded to 0.5 hPa)
PRESSURE_OFFSET_HPA = 0.5

try:
    while True:
        print(f"Pressure = {bmp.pressure - PRESSURE_OFFSET_HPA:.2f} hPa")
        temp = bmp.temperature
        print(f"temp = {temp:.2f} C")
      
        meters = bmp.altitude
        print(f"Altitude = {meters:.2f} meters")
        feet = meters * 3.28084
        feet_only = int(feet)
        inches = int((feet - feet_only) * 12)
        print(f"Altitude = {feet_only} feet {inches} inches")

        time.sleep(5)

except KeyboardInterrupt:
    print("Stopped.")