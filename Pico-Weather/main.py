# Weather Station - Pico 2W
# Sensors: BMP390 (pressure, altitude), HDC3022 (temperature, humidity)
# BMP390 contains temp sensor, but HDC3022 temp sensor used instead due to higher accuracy
#
# BMP390 driver: micropython_bmpxxx library
# Author: Brad Carlile (bradcar)
# GitHub: https://github.com/bradcar/MicroPython_BMPxxx
#
# HDC3022: raw I2C driver

import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

# I2C bus - shared by both sensors
i2c = I2C(0, sda=Pin(0), scl=Pin(1))

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")
print("")

# --- BMP390 setup ---
bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)

sea_level_pressure = bmp.sea_level_pressure
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

bmp.sea_level_pressure = 1017.0
print(f"Adjusted sea level pressure = {bmp.sea_level_pressure:.2f} hPa")

bmp.altitude = 210.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")

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

# --- Main loop ---
while True:
    # BMP390 readings
    print(f"Station Pressure = {bmp.pressure:.2f} hPa")
    print(f"Sea Level Pressure = {bmp.sea_level_pressure:.2f} hPa")
    meters = bmp.altitude
    feet = meters * 3.28084
    feet_only = int(feet)
    inches = int((feet - feet_only) * 12)
    print(f"Altitude = {meters:.2f} m / {feet_only} feet {inches} inches")

    # HDC3022 readings
    temp_c, temp_f, humidity = read_hdc3022()
    print(f"Temp = {temp_c:.2f} C / {temp_f:.2f} F")
    print(f"Humidity = {humidity:.2f} %")
    print("---")

    time.sleep(10)