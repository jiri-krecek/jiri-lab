from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=0)
display.set_backlight(1.0)

BLACK = display.create_pen(0, 0, 0)
RED   = display.create_pen(255, 20, 0)
AMBER = display.create_pen(255, 165, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE  = display.create_pen(0, 200, 255)

display.set_pen(BLACK)
display.clear()

display.set_pen(RED)
display.text("Temp:", 10, 10, 240, 3)
display.text("75 F", 110, 10, 240, 3)

display.set_pen(AMBER)
display.text("RH:", 10, 41, 240, 3)
display.text("65%",110, 41, 240, 3)

display.set_pen(GREEN)
display.text("Press: 1026 hPa", 10, 72, 240, 3)
display.text("1026 hPa", 110, 72, 240, 3)

display.set_pen(BLUE)
display.text("UV:", 10, 103, 240, 3)
display.text("2", 110, 103, 240, 3)

display.update()