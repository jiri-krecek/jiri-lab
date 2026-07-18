# ─────────────────────────────────────────────────────────
# Font test — scrolls full A-Z, 0-9, punctuation across the
# Pico Unicorn to visually inspect every character tuple.
# No WiFi/NTP needed — pure display test.
# ─────────────────────────────────────────────────────────

import time
from picounicorn import PicoUnicorn

u = PicoUnicorn()
WIDTH = u.get_width()
HEIGHT = u.get_height()

CHARS = {
    'A': (5, [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001]),
    'B': (5, [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110]),
    'C': (5, [0b01111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b01111]),
    'D': (5, [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110]),
    'E': (5, [0b11111, 0b10000, 0b10000, 0b11100, 0b10000, 0b10000, 0b11111]),
    'F': (5, [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000]),
    'G': (5, [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111]),
    'H': (5, [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001]),
    'I': (5, [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111]),
    'J': (5, [0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100]),
    'K': (5, [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001]),
    'L': (5, [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111]),
    'M': (5, [0b10001, 0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001]),
    'N': (5, [0b10001, 0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001]),
    'O': (5, [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110]),
    'P': (5, [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000]),
    'Q': (5, [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101]),
    'R': (5, [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001]),
    'S': (5, [0b01110, 0b10001, 0b10000, 0b01110, 0b00001, 0b10001, 0b01110]),
    'T': (5, [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100]),
    'U': (5, [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110]),
    'V': (5, [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100]),
    'W': (5, [0b10001, 0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b01010]),
    'X': (5, [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001]),
    'Y': (5, [0b10001, 0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100]),
    'Z': (5, [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111]),
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

# Bright, single color so you're judging shape only, not color rendering
LETTER_COLOR = (0, 80, 100)
DIGIT_COLOR = (80, 60, 0)
PUNCT_COLOR = (60, 0, 60)

TEXT = '    ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 :,*    '

def render_buffer(text):
    buf_width = len(text) * 6
    buf = [[(0, 0, 0)] * buf_width for _ in range(7)]
    for ci, char in enumerate(text):
        if char not in CHARS:
            continue
        if char.isalpha():
            color = LETTER_COLOR
        elif char.isdigit():
            color = DIGIT_COLOR
        else:
            color = PUNCT_COLOR
        width, rows = CHARS[char]
        x_start = ci * 6
        for y, row in enumerate(rows):
            for x in range(width):
                if row & (1 << (width - 1 - x)):
                    buf[y][x_start + x] = color
    return buf, buf_width

def clear():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            u.set_pixel(x, y, 0, 0, 0)

buf, buf_width = render_buffer(TEXT)
scroll_pos = 0
last_scroll = time.ticks_ms()

# Slower than the main clock scroll (80ms vs 40ms) so each letter
# is easier to read and inspect as it passes
SCROLL_DELAY_MS = 80

while True:
    if time.ticks_diff(time.ticks_ms(), last_scroll) > SCROLL_DELAY_MS:
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