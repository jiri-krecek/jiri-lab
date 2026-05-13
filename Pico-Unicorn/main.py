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
    'MON': (1, 7, 12),
    'TUE': (1, 5, 10),
    'WED': (1, 7, 11),
    'THU': (1, 5, 10),
    'FRI': (1, 5, 10),
    'SAT': (1, 6, 11),
    'SUN': (1, 6, 11),
}

DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

# this applies only to US, not other countries and does not apply to Arizona where time 
# does not change in some parts of the state.
# this is based on the premise that DST in the US begins 2nd Sun of Mar and ends 1st Sun of Nov

def is_dst(year, month, day, weekday):
    # weekday: 0=Monday, 6=Sunday in MicroPython
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
    if month == 3:
        # second Sunday of March
        second_sunday = 14 - (weekday + 6) % 7
        return day >= second_sunday
    if month == 11:
        # first Sunday of November
        first_sunday = 7 - (weekday + 6) % 7
        return day < first_sunday

def local_hour(utc_hour, year, month, day, weekday):
    offset = -5 if is_dst(year, month, day, weekday) else -6
    hour_24 = (utc_hour + offset) % 24
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
    return hour_12, hour_24 >= 12

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

def draw_ampm(is_pm):
    if not is_pm:
        u.set_pixel(0, 6, 50, 50, 0)   # AM - yellow
    else:
        u.set_pixel(0, 6, 0, 0, 50)    # PM - blue

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

def local_time(now):
    offset = -5 if is_dst(now[0], now[1], now[2], now[6]) else -6
    t = time.mktime(now)
    t += offset * 3600
    return time.localtime(t)        

def clear():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            u.set_pixel(x, y, 0, 0, 0)

# positions: H1=0, H2=4, gap, M1=9, M2=13
# H1 at 0, H2 at 4, M1 at 9, M2 at 13
# that's 3+1+3+2+3+1+3 = 16 exactly

mode = 0  # 0=24h, 1=12h, 2=date, 3=dow
last_display = 0
last_sync = time.time()

while True:
    # check buttons
    if u.is_pressed(PicoUnicorn.BUTTON_A):
        mode = 0
        last_display = 0
    elif u.is_pressed(PicoUnicorn.BUTTON_B):
        mode = 1
        last_display = 0
    elif u.is_pressed(PicoUnicorn.BUTTON_X):
        mode = 2
        last_display = 0
    elif u.is_pressed(PicoUnicorn.BUTTON_Y):
        mode = 3
        last_display = 0

    # resync NTP every hour
    if time.time() - last_sync > 3600:
        try:
            ntptime.settime()
            last_sync = time.time()
        except:
            pass

    # only redraw every 30 seconds
    if time.time() - last_display < 30:
        time.sleep(0.1)
        continue

    last_display = time.time()
    now_utc = time.localtime()
    now = local_time(now_utc)

    clear()

    if mode == 0:
        # 24h clock
        hour_24 = (now_utc[3] + (-5 if is_dst(now[0], now[1], now[2], now[6]) else -6)) % 24
        minute = now[4]
        h1 = '{:02d}'.format(hour_24)[0]
        h2 = '{:02d}'.format(hour_24)[1]
        m1 = '{:02d}'.format(minute)[0]
        m2 = '{:02d}'.format(minute)[1]
        u.set_pixel(0, 0, 0, 50, 0)
        draw_char(h1, 0, 50, 50, 50)
        draw_char(h2, 4, 50, 50, 50)
        draw_char(m1, 9, 50, 50, 50)
        draw_char(m2, 13, 50, 50, 50)

    elif mode == 1:
        # 12h clock
        hour_12, is_pm = local_hour(now_utc[3], now[0], now[1], now[2], now[6])
        minute = now[4]
        h1 = '{:02d}'.format(hour_12)[0]
        h2 = '{:02d}'.format(hour_12)[1]
        m1 = '{:02d}'.format(minute)[0]
        m2 = '{:02d}'.format(minute)[1]
        draw_ampm(is_pm)
        draw_char(h1, 0, 50, 50, 50)
        draw_char(h2, 4, 50, 50, 50)
        draw_char(m1, 9, 50, 50, 50)
        draw_char(m2, 13, 50, 50, 50)

    elif mode == 2:
        # date MM DD
        month = now[1]
        day = now[2]
        mo1 = '{:02d}'.format(month)[0]
        mo2 = '{:02d}'.format(month)[1]
        d1 = '{:02d}'.format(day)[0]
        d2 = '{:02d}'.format(day)[1]
        u.set_pixel(15, 0, 0, 50, 0)
        draw_char(mo1, 0, 50, 50, 50)
        draw_char(mo2, 4, 50, 50, 50)
        draw_char(d1, 9, 50, 50, 50)
        draw_char(d2, 13, 50, 50, 50)

    elif mode == 3:
        # day of week
        dow = DAYS[now[6]]
        offsets = OFFSETS[dow]
        u.set_pixel(15, 6, 0, 50, 0)
        draw_letter(dow[0], offsets[0], 50, 50, 50)
        draw_letter(dow[1], offsets[1], 50, 50, 50)
        draw_letter(dow[2], offsets[2], 50, 50, 50)

    time.sleep(0.1)