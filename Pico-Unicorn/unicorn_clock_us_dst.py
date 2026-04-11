import network
import ntptime
import time
from picounicorn import PicoUnicorn
from config import WIFI_SSID, WIFI_PASSWORD

# Connect WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

while not wlan.isconnected():
    pass

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
    return (utc_hour + offset) % 24

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

# positions: H1=0, H2=4, gap, M1=9, M2=13
# H1 at 0, H2 at 4, M1 at 9, M2 at 13
# that's 3+1+3+2+3+1+3 = 16 exactly

last_sync = time.time()

while True:
    # Resync NTP every hour
    if time.time() - last_sync > 3600:
        try:
            ntptime.settime()
            last_sync = time.time()
        except:
            pass  # if sync fails, keep running with last known time
    
    now = time.localtime()
    hour = local_hour(now[3], now[0], now[1], now[2], now[6])
    minute = now[4]
    
    h1 = '{:02d}'.format(hour)[0]
    h2 = '{:02d}'.format(hour)[1]
    m1 = '{:02d}'.format(minute)[0]
    m2 = '{:02d}'.format(minute)[1]

    # color and brightness controlled by 3rd, 4th and 5th value
    # in this case R=10, G=50, B=50 for low brightness solution
    # if you want full brightness, set to 50, 255, 255 or whatever color
    clear()
    draw_char(h1, 0, 10, 50, 50)
    draw_char(h2, 4, 10, 50, 50)
    draw_char(m1, 9, 10, 50, 50)
    draw_char(m2, 13, 10, 50, 50)

    time.sleep(30)