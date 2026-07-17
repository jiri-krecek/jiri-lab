from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN
import time

graphics = PicoGraphics(display=DISPLAY_GALACTIC_UNICORN)
gu = GalacticUnicorn()
gu.set_brightness(0.3)

red = graphics.create_pen(255, 0, 0)
yellow = graphics.create_pen(255, 255, 0)
green = graphics.create_pen(0, 255, 0)
teal = graphics.create_pen(0, 128, 128)
black = graphics.create_pen(0, 0, 0)

while True:
    graphics.set_pen(black)
    graphics.clear()

    if gu.is_pressed(GalacticUnicorn.SWITCH_A):
        graphics.set_pen(red)
        graphics.clear()
        print("A pressed")
    elif gu.is_pressed(GalacticUnicorn.SWITCH_B):
        graphics.set_pen(yellow)
        graphics.clear()
        print("B pressed")
    elif gu.is_pressed(GalacticUnicorn.SWITCH_C):
        graphics.set_pen(green)
        graphics.clear()
        print("C pressed")
    elif gu.is_pressed(GalacticUnicorn.SWITCH_D):
        graphics.set_pen(teal)
        graphics.clear()
        print("D pressed")

    gu.update(graphics)
    time.sleep(0.05)