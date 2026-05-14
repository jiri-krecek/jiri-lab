# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

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