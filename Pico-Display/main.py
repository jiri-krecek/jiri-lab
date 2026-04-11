# Weather Display - Decker Pico
# Receives sensor data from Weather Pico via UART1 on GP4 (RX) / GP5 (TX)
# Displays temp, humidity, pressure on PIM543 display

from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
from machine import UART, Pin
import time

# --- UART setup ---
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

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
    display.text(f"{temp_f} F", 105, 10, 240, 3)

    display.set_pen(AMBER)
    display.text("RH:", 10, 41, 240, 3)
    display.text(f"{humidity}%", 105, 41, 240, 3)

    display.set_pen(GREEN)
    display.text("Press:", 10, 72, 240, 3)
    display.text(f"{pressure}", 105, 72, 240, 3)

    display.set_pen(BLUE)
    display.text("UV:", 10, 103, 240, 3)
    display.text("N/A", 105, 103, 240, 3)

    display.update()

# show waiting screen on boot
display.set_pen(BLACK)
display.clear()
display.set_pen(AMBER)
display.text("Waiting for", 10, 41, 240, 3)
display.text("sensor data", 10, 72, 240, 3)
display.update()

# --- Main loop ---
while True:
    if uart.any():
        line = uart.readline()
        if line:
            try:
                line = line.decode().strip()
                parts = line.split(",")
                if len(parts) == 3:
                    temp_f = parts[0]
                    humidity = parts[1]
                    pressure = parts[2]
                    update_display(temp_f, humidity, pressure)
                    print(f"Received: {line}")
            except Exception as e:
                print(f"Parse error: {e}")
    time.sleep(1)