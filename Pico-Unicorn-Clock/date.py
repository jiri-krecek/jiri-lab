# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

import network
import ntptime
import time
from picounicorn import PicoUnicorn
from config import WIFI_SSID, WIFI_PASSWORD

# Connect WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 15
start = time.time()
while not wlan.isconnected():
    if time.time() - start > timeout:
        break
    time.sleep(0.5)

# Sync time
ntptime.settime()

u = PicoUnicorn()
WIDTH = u.get_width()
HEIGHT = u.get_height()

DIGITS = {
    '0': [0b111, 0b101, 0b101, 0b101, 0b111],
    '1': [0b010, 0b110, 0b010, 0b010, 0b111],
    '2': [0b111, 0b001, 0b111, 0b100, 0b111],
    '3': [0b111, 0b001, 0b111, 0b001, 0b111],
    '4': [0b101, 0b101, 0b111, 0b001, 0b001],
    '5': [0b111, 0b100, 0b111, 0b001, 0b111],
    '6': [0b111, 0b100, 0b111, 0b101, 0b111],
    '7': [0b111, 0b001, 0b001, 0b001, 0b001],
    '8': [0b111, 0b101, 0b111, 0b101, 0b111],
    '9': [0b111, 0b101, 0b111, 0b001, 0b111],
}

def draw_char(char, x_offset, r, g, b):
    if char not in DIGITS:
        return
    rows = DIGITS[char]
    for y, row in enumerate(rows):
        for x in range(3):
            if row & (0b100 >> x):
                px = x_offset + x
                py = y + 1
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    u.set_pixel(px, py, r, g, b)

def clear():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            u.set_pixel(x, y, 0, 0, 0)

last_sync = time.time()

while True:
    if time.time() - last_sync > 3600:
        try:
            ntptime.settime()
            last_sync = time.time()
        except:
            pass

    now = time.localtime()
    month = now[1]
    day = now[2]

    m1 = '{:02d}'.format(month)[0]
    m2 = '{:02d}'.format(month)[1]
    d1 = '{:02d}'.format(day)[0]
    d2 = '{:02d}'.format(day)[1]

    clear()
    u.set_pixel(15, 0, 0, 50, 0)
    draw_char(m1, 0, 50, 50, 50)
    draw_char(m2, 4, 50, 50, 50)
    draw_char(d1, 9, 50, 50, 50)
    draw_char(d2, 13, 50, 50, 50)

    time.sleep(30)
