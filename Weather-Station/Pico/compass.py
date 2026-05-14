# ─────────────────────────────────────────────────────────
# Author    : Jiri Krecek
# Company   : Archer Dynamics LLC (goarcherdynamics.com)
# License   : MIT - free to use, modify, and distribute
#             with attribution
# AI Notice : This code was co-developed with assistance of
#             Claude AI (Anthropic). Logic, design, code
#             modifications and testing done by the author.
# ─────────────────────────────────────────────────────────

# compass.py
# Wind vane voltage lookup for SparkFun SEN-15901
# Base table calibrated to true North — 10K pull-up, 3.3V supply
# OFFSET_STEPS: steps to rotate labels CW to match trailer orientation
# 0 = trailer faces true North
# 1 = trailer faces NE
# 2 = trailer faces E
# 3 = trailer faces SE
# 4 = trailer faces S 
# -1 = trailer faces NW
# -2 = trailer faces W
# -3 = trailer faces SW
# -4 = trailer faces S (same as +4 above)

OFFSET_STEPS = 1

DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

VOLTAGE_TABLE = [
    (2.93, 3.10, 0),  # N
    (2.78, 2.92, 1),  # NE
    (2.45, 2.58, 2),  # E
    (1.40, 1.55, 3),  # SE
    (0.24, 0.33, 4),  # S
    (0.55, 0.63, 5),  # SW
    (0.86, 0.96, 6),  # W
    (1.97, 2.07, 7),  # NW
]

def voltage_to_direction(voltage):
    for low, high, index in VOLTAGE_TABLE:
        if low <= voltage <= high:
            corrected = (index + OFFSET_STEPS) % 8
            return DIRECTIONS[corrected]
    return None

def get_wind_direction(readings):
    valid = [r for r in readings if r is not None]
    if not valid:
        return None
    counts = {}
    for r in valid:
        counts[r] = counts.get(r, 0) + 1
    return max(counts, key=counts.get)