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

ntptime.settime()

u = PicoUnicorn()
WIDTH = u.get_width()
HEIGHT = u.get_height()

LETTERS = {
    'M': (5, [0b10001, 0b11011, 0b10101, 0b10001, 0b10001]),
    'O': (4, [0b0110, 0b1001, 0b1001, 0b1001, 0b0110]),
    'N': (4, [0b1001, 0b1101, 0b1011, 0b1001, 0b1001]),
    'T': (3, [0b111, 0b010, 0b010, 0b010, 0b010]),
    'U': (4, [0b1001, 0b1001, 0b1001, 0b1001, 0b0110]),
    'E': (3, [0b111, 0b100, 0b110, 0b100, 0b111]),
    'W': (5, [0b10001, 0b10001, 0b10101, 0b10101, 0b01010]),
    'D': (4, [0b1110, 0b1001, 0b1001, 0b1001, 0b1110]),
    'H': (4, [0b1001, 0b1001, 0b1111, 0b1001, 0b1001]),
    'R': (4, [0b1110, 0b1001, 0b1110, 0b1010, 0b1001]),
    'I': (3, [0b111, 0b010, 0b010, 0b010, 0b111]),
    'F': (3, [0b111, 0b100, 0b110, 0b100, 0b100]),
    'A': (4, [0b0110, 0b1001, 0b1111, 0b1001, 0b1001]),
    'S': (4, [0b0111, 0b1000, 0b0110, 0b0001, 0b1110]),
}

OFFSETS = {
    'MON': (1, 7, 12),    # 1, 1+5+1=7, 7+4+1=12
    'TUE': (1, 5, 10),    # 1, 1+3+1=5, 5+4+1=10
    'WED': (1, 7, 11),    # 1, 1+5+1=7, 7+3+1=11
    'THU': (1, 5, 10),    # 1, 1+3+1=5, 5+4+1=10
    'FRI': (1, 5, 10),    # 1, 1+3+1=5, 5+4+1=10
    'SAT': (1, 6, 11),    # 1, 1+4+1=6, 6+4+1=11
    'SUN': (1, 6, 11),    # 1, 1+4+1=6, 6+4+1=11
}

DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

def draw_letter(char, x_offset, r, g, b):
    if char not in LETTERS:
        return
    width, rows = LETTERS[char]
    for y, row in enumerate(rows):
        for x in range(width):
            if row & (1 << (width - 1 - x)):
                px = x_offset + x
                py = y + 1
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    u.set_pixel(px, py, r, g, b)

def clear():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            u.set_pixel(x, y, 0, 0, 0)

def is_dst(year, month, day, weekday):
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
    if month == 3:
        second_sunday = 14 - (weekday + 6) % 7
        return day >= second_sunday
    if month == 11:
        first_sunday = 7 - (weekday + 6) % 7
        return day < first_sunday

def local_time(now):
    offset = -5 if is_dst(now[0], now[1], now[2], now[6]) else -6
    t = time.mktime(now)
    t += offset * 3600
    return time.localtime(t)

last_sync = time.time()

while True:
    if time.time() - last_sync > 3600:
        try:
            ntptime.settime()
            last_sync = time.time()
        except:
            pass

    now = local_time(time.localtime())
    dow = DAYS[now[6]]
    offsets = OFFSETS[dow]
    clear()
    u.set_pixel(15, 6, 0, 50, 0)
    draw_letter(dow[0], offsets[0], 50, 50, 50)
    draw_letter(dow[1], offsets[1], 50, 50, 50)
    draw_letter(dow[2], offsets[2], 50, 50, 50)