# Unicorn Clock

A 24-hour NTP-synced clock for the Pimoroni Pico Unicorn Pack, 
running on a Raspberry Pi Pico 2W. Displays time in HHMM format 
with a double gap separating hours and minutes.

## Hardware
- Raspberry Pi Pico 2W
- Pimoroni Pico Unicorn Pack (16x7 RGB LED matrix)

## Firmware Required
Pimoroni MicroPython for RP2350:
rpi_pico2_w-v1.26.1-micropython.uf2
https://github.com/pimoroni/pimoroni-pico-rp2350/releases

Do NOT use standard MicroPython — the picounicorn library 
will not be available on that firmware - use the link above 
nd find the latest release available for Pico 2W, or wahtever 
model you are running - the name will be similar to mine above.
NOTE: Pico 2st gen has a completely seprate Git repo than Pico 2!
RP2350 is Pico2 repo!


## Setup
1. Flash the Pimoroni firmware above
2. Create config.py on the Pico with your WiFi credentials:
   WIFI_SSID = "your_network"
   WIFI_PASSWORD = "your_password"
3. Upload main.py and config.py to the Pico
4. config.py is gitignored — never commit credentials

## Notes
- Time synced via NTP on boot
- DST handled automatically for US timezones (except Arizona)
- Timezone hardcoded for US Central — adjust offset in local_hour() for other zones
