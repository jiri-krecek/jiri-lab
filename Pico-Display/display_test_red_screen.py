import picographics
import time

display = picographics.PicoGraphics(display=picographics.DISPLAY_PICO_DISPLAY_2)

# Red
display.set_pen(display.create_pen(255, 0, 0))
display.clear()
display.update()

time.sleep(5)

# Black
display.set_pen(display.create_pen(0, 0, 0))
display.clear()
display.update()