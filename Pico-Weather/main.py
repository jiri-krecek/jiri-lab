# BMP390 sensor driver: micropython_bmpxxx library
# Author: Brad Carlile (bradcar)
# GitHub: https://github.com/bradcar/MicroPython_BMPxxx
# License: Open source - see LICENSE.md in repo

import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

#i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
#changed from defa
i2c = I2C(0, sda=Pin(0), scl=Pin(1))

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")
print("")

#changed to address   
bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)

sea_level_pressure = bmp.sea_level_pressure
print(f"initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

sea_level_pressure = bmp.sea_level_pressure
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

# reset driver to contain the accurate sea level pressure (SLP) from my nearest airport this hour
bmp.sea_level_pressure = 1017.0
print(f"Adjusted sea level pressure = {bmp.sea_level_pressure:.2f} hPa")

# Alternatively set known altitude in meters and the sea level pressure will be calculated
# changed from 111 to 208 meters, which is the altitude of my location
bmp.altitude = 210.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")

while True:
    print(f"Station Pressure = {bmp.pressure:.2f} hPa")
    print(f"Sea Level Pressure = {bmp.sea_level_pressure:.2f} hPa")
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
    print(f"temp = {temp * 9/5 + 32:.2f} F")  
    meters = bmp.altitude
    print(f"Altitude = {meters:.2f} meters")
    feet = meters * 3.28084
    feet_only = int(feet)
    inches = int((feet - feet_only) * 12)
    print(f"Altitude = {feet_only} feet {inches} inches")
    

    time.sleep(10)
 