# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

from machine import Pin, ADC
import time

vane_adc = ADC(Pin(26))

while True:
    raw = vane_adc.read_u16()
    voltage = raw * 3.3 / 65535
    print(f"{voltage:.2f}V")
    time.sleep(1)