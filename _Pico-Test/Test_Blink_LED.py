# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

import machine
import time

led = machine.Pin("LED", machine.Pin.OUT)
reps = 10

for i in range(reps):
    led.on()
    time.sleep(0.01)
    led.off()
    time.sleep(0.99)