# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# Anemometer debug - scan all candidate pins for pulses

from machine import Pin
import time

# Test GP4 - our intended ANE pin
ane = Pin(4, Pin.IN, Pin.PULL_UP)

count = 0

def pulse(pin):
    global count
    count += 1

ane.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=pulse)

while True:
    print(f"GP4 state: {ane.value()}  pulses: {count}")
    time.sleep(1)