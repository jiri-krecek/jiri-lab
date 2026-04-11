# Weather Station - Pico 2W - UART Sender
# This code is only made to prove that sensor data from one pico
# can be sent to another pico via UART
# Weather Pico = PIco 2W + BMP390 + HDC3022 sensors
# Decker Pico = Pico 2W + Pimoroni Decker + Pimoroni Pico Display
# 
# Pinout:
# Weather Pico GP4 TX >> Decker Pico GP5 RX
# Weather Pico GP5 RX << Decker Pico GP4 TX
#
# Sensors: BMP390 (pressure, altitude), HDC3022 (temperature, humidity)
# Sends data to Decker Pico via UART1 on GP4 (TX) / GP5 (RX)

import time
from machine import Pin, I2C, UART # type: ignore
from micropython_bmpxxx import bmpxxx

# I2C bus - shared by both sensors
i2c = I2C(0, sda=Pin(0), scl=Pin(1))

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")

# --- BMP390 setup ---
bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)
bmp.sea_level_pressure = 1017.0
bmp.altitude = 210.0
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

# --- UART setup ---
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# --- Main loop ---
while True:
    pressure = bmp.sea_level_pressure
    temp_c, temp_f, humidity = read_hdc3022()

    # format as simple CSV string
    msg = f"{temp_f:.1f},{humidity:.1f},{pressure:.0f}\n"
    uart.write(msg)
    print(f"Sent: {msg.strip()}")

    time.sleep(10)