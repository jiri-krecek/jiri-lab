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

CHARS = {
    'M': (5, [0b10001, 0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001]),
    'O': (5, [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110]),
    'N': (5, [0b10001, 0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001]),
    'D': (5, [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110]),
    'A': (5, [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001]),
    'Y': (5, [0b10001, 0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100]),
    'W': (5, [0b10001, 0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b01010]),
    'E': (5, [0b11111, 0b10000, 0b10000, 0b11100, 0b10000, 0b10000, 0b11111]),
    'S': (5, [0b01110, 0b10001, 0b10000, 0b01110, 0b00001, 0b10001, 0b01110]),
    'P': (5, [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000]),
    'T': (5, [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100]),
    'H': (5, [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001]),
    'R': (5, [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001]),
    '0': (5, [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110]),
    '1': (5, [0b00100, 0b01100, 0b10100, 0b00100, 0b00100, 0b00100, 0b11111]),
    '2': (5, [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111]),
    '3': (5, [0b01110, 0b10001, 0b00001, 0b00110, 0b00001, 0b10001, 0b01110]),
    '4': (5, [0b00100, 0b01000, 0b10000, 0b10010, 0b11111, 0b00010, 0b00010]),
    '5': (5, [0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b10001, 0b01110]),
    '6': (5, [0b01110, 0b10001, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110]),
    '7': (5, [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000]),
    '8': (5, [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110]),
    '9': (5, [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b10001, 0b01110]),
    ':': (5, [0b00000, 0b00000, 0b00100, 0b00000, 0b00100, 0b00000, 0b00000]),
    ' ': (5, [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000]),
    ',': (5, [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01000, 0b01000]),
    '*': (5, [0b00000, 0b10101, 0b01110, 0b11111, 0b01110, 0b10101, 0b00000]),
}

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

DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

def ordinal(n):         # when adding ordinals to dates (1st, 2nd, 3rd, 4th, 5th, etc... we must account for the exceptions: 11th, 12th, 13th...
    if 11 <= n <= 13:
        return 'TH'
    if n % 10 == 1:
        return 'ST'
    if n % 10 == 2:
        return 'ND'
    if n % 10 == 3:
        return 'RD'
    return 'TH'

def build_scroll_string(now):
    hour = now[3]
    minute = now[4]
    month = now[1]
    day = now[2]
    suffix = ordinal(day)
    dow = DAYS[now[6]]
    mon = MONTHS[month - 1]
    year = now[0]
    ampm = 'AM' if hour < 12 else 'PM'
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    return '    ******* {:02d}:{:02d} {} {} {} {}{}, {}   '.format(     # need to add extra leading spaces in the string to make the text fly into the screen from right and if you do update this you must change render_buffer!   
        hour_12, minute, ampm, dow, mon, day, suffix, year)

CHAKRA = [
    (100, 0, 0),     # red
    (75, 35, 0),     # orange
    (50, 50, 0),     # yellow
    (0, 50, 0),      # green
    (0, 50, 50),     # teal
    (0, 0, 75),      # blue
    (50, 0, 50),     # magenta
]

def render_buffer(text):
    buf_width = len(text) * 6
    buf = [[(0, 0, 0)] * buf_width for _ in range(7)]
    for ci, char in enumerate(text):
        if char not in CHARS:
            continue
        width, rows = CHARS[char]
        x_start = ci * 6
        if ci >=4 and ci < 11:          # if you change the leading characters, you must chcange the offset - this expects 4 blank spaces to allow the * flyin from right
            color = CHAKRA[ci-4]        # this has to be offset by 4 - that is how many leading blank spaces we added at the beginning of the display string before * flies in
        else:
            color = (50, 50, 50)
        for y, row in enumerate(rows):
            for x in range(width):
                if row & (1 << (width - 1 - x)):
                    buf[y][x_start + x] = color
    return buf, buf_width

def clear():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            u.set_pixel(x, y, 0, 0, 0)

last_sync = time.time()
scroll_pos = 0
last_scroll = time.ticks_ms()
now = local_time(time.localtime())
text = build_scroll_string(now)
buf, buf_width = render_buffer(text)

while True:
    if time.time() - last_sync > 3600:
        try:
            ntptime.settime()
            last_sync = time.time()
        except:
            pass

    # rebuild string every minute
    now = local_time(time.localtime())
    new_text = build_scroll_string(now)
    if new_text != text:
        text = new_text
        buf, buf_width = render_buffer(text)

    # scroll one pixel at a time
    if time.ticks_diff(time.ticks_ms(), last_scroll) > 40:      # adjust this delay by 10 ms up to slow down scroll speed, or down by 10 ms to speed up scroll speed
        clear()
        for y in range(7):
            for x in range(WIDTH):
                src = scroll_pos + x
                if src < buf_width and buf[y][src] != (0, 0, 0):
                    r, g, b = buf[y][src]
                    u.set_pixel(x, y, r, g, b)
        scroll_pos += 1
        if scroll_pos >= buf_width:
            scroll_pos = 0
        last_scroll = time.ticks_ms()

    time.sleep(0.01)