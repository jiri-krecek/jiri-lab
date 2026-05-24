# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# Weather Display - Decker Pico
# Reads BME280 directly via I2C Stemma pigtail on GP0/GP1
# BME280 default address is 0x76 - temp, barometer, humidity
# LTR559 default address is 0x23 - light, proximity
# LSM6DS3 default address is 0x6A - gyro, accelerometer
#
# Wiring from sensor to Pico 2W: 
# BLACK - GND ground
# RED - VIN 3V positive
# BLUE - SDA data
# YELLOW - SCL clock
# Displays temp, humidity, pressure on PIM543 display

from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
from machine import I2C, Pin
import bme280
import time

# --- Metrics Calibration Against Primary Station ---
PRESSURE_OFFSET = -1.2  # hPa, calibrated against KORD

# --- I2C and sensor setup ---
i2c = I2C(0, sda=Pin(0), scl=Pin(1))
sensor = bme280.BME280(i2c=i2c)

# --- Display setup ---
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=0)
display.set_backlight(1.0)

BLACK = display.create_pen(0, 0, 0)
RED   = display.create_pen(255, 20, 0)
AMBER = display.create_pen(255, 165, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE  = display.create_pen(0, 200, 255)

def update_display(temp_f, humidity, pressure):
    display.set_pen(BLACK)
    display.clear()

    display.set_pen(RED)
    display.text("Temp:", 10, 10, 240, 3)
    display.text(f"{temp_f:.1f} F", 105, 10, 240, 3)

    display.set_pen(AMBER)
    display.text("RH:", 10, 41, 240, 3)
    display.text(f"{humidity:.1f}%", 105, 41, 240, 3)

    display.set_pen(GREEN)
    display.text("Press:", 10, 72, 240, 3)
    display.text(f"{pressure:.1f}", 105, 72, 240, 3)

    display.set_pen(BLUE)
    display.text("Light:", 10, 103, 240, 3)
    display.text("N/A", 105, 103, 240, 3)

    display.update()

# --- Boot screen ---
display.set_pen(BLACK)
display.clear()
display.set_pen(AMBER)
display.text("Starting...", 10, 57, 240, 3)
display.update()
time.sleep(1)

# --- Main loop ---
while True:
    try:
        temp_c, pressure_pa, humidity = sensor.read_compensated_data()
        temp_f = (temp_c * 9 / 5) + 32
        pressure_hpa = pressure_pa / 100
        pressure_slp = (pressure_hpa * (1 - (0.0065 * 210) / (temp_c + 0.0065 * 210 + 273.15)) ** -5.257) + PRESSURE_OFFSET
        update_display(temp_f, humidity, pressure_slp)
        print(f"T:{temp_f:.1f}F  RH:{humidity:.1f}%  P:{pressure_slp:.1f}hPa")
    except Exception as e:
        print(f"Sensor error: {e}")
    time.sleep(2)