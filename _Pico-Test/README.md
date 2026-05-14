# pico_diagnostics.py

A somewhat comprehensive hardware and network diagnostic tool for Raspberry Pi Pico and Pico W.
Designed to verify a freshly flashed Pico before deploying it in a project. I have been burned
too many times when using the wrong firmware, so this comes in handy.

## Compatible Hardware

- Raspberry Pi Pico (RP2040) — 1st gen, no WiFi
- Raspberry Pi Pico W (RP2040) — 1st gen, with WiFi
- Raspberry Pi Pico 2 (RP2350) — 2nd gen, no WiFi
- Raspberry Pi Pico 2W (RP2350) — 2nd gen, with WiFi
- I do not have any other model family, so cannot test

The script auto-detects WiFi capability and skips network tests on non-W models.

## What It Tests (see sample below)

**SYSTEM** — Identifies the board (chip generation), unique hardware ID, CPU frequency,
MicroPython firmware version, last reset cause, internal chip temperature, RAM usage,
and flash storage usage.

**TIME** — Reads the onboard RTC and syncs with an NTP server to verify accurate UTC time.
Skipped on non-W models.

**NETWORK** — Reports IP address, gateway, DNS, MAC address, and signal strength. Tests
local DNS resolution and reachability (configurable, defaults to PiHole), HTTP and HTTPS
GET requests to verify the full network stack, and external DNS resolution via google.com.
Skipped on non-W models.

**HARDWARE BUSES** — Initializes and tests I2C (GP0/GP1), SPI, UART, PWM (GP15),
and ADC (GP26). No external hardware required — buses are tested in isolation.

**RESILIENCE** — Verifies that Python exception handling works correctly.

All tests report PASS or FAIL independently so partial failures are easy to spot.

## Requirements

- MicroPython v1.28.0 or later
- For WiFi tests: Pico W with `config.py` saved on the Pico containing:

```python
WIFI_SSID     = "your_ssid"
WIFI_PASSWORD = "your_password"
```
NOTE: this script will fail, if your Pico does not have this config file saved inside

## How to Use

1. Flash MicroPython firmware onto your Pico (download from micropython.org)
2. Connect the Pico to your computer via USB 
3. Copy `pico_diagnostics.py` to the Pico root or run it from your dev console
4. For Pico W: also copy `config.py` with your WiFi credentials
5. Open a serial connection (Thonny, VSCode with MicroPico, or any serial terminal)
6. Run the script — results print to the console

## Local Network Tests

The NETWORK section includes a ping and DNS test against a local host. By default this
points to a PiHole DNS server with hostname `pihole`. If you don't run
PiHole, update these values in the script or add them to `config.py`:

```python
LOCAL_DNS_HOST = "your_local_host"
LOCAL_DNS_IP   = "your_local_ip"
LOCAL_DNS_PORT = 53
```

## Sample Output

```
Connecting to "YourNetwork"...
waiting... 0s
waiting... 1s
waiting... 2s
waiting... 3s
waiting... 4s
waiting... 5s
Connected in 5s
── SYSTEM ──────────────────────────────────────────
Board      : Raspberry Pi Pico W with RP2040
WiFi       : Yes
Unique ID  : xxxxxxxxxxxxxxxxxxx
CPU freq   : 150 MHz
MicroPython: 3.4.0; MicroPython v1.28.0 on 2026-04-06
MP impl    : micropython v1.28.0
Reset cause: Power on
Chip temp  : 19.6 C
RAM free   : 445648 bytes
RAM used   : 11248 bytes (2.5%)
Flash total: 2621440 bytes
Flash free : 2613248 bytes (0.3% used)
── TIME ────────────────────────────────────────────
System RTC : 2026-05-12 17:19:48 UTC
Syncing NTP...
NTP synced : 2026-05-12 17:19:48 UTC
── NETWORK ─────────────────────────────────────────
IP address : xx.xx.xx.xxx
Gateway    : xx.xx.xx.xxx
DNS        : xx.xx.xx.xxx
MAC        : xx:xx:xx:xx:xx:xx
Signal     : -56 dBm
DNS resolve: hostname (xx.xx.xx.xxx)... xx.xx.xx.xxx PASS
Ping result: PASS
HTTP status: 200 — GET test: PASS
HTTPS status: 200 — HTTPS test: PASS
DNS result  : xx.xx.xx.xxx PASS
── HARDWARE BUSES ──────────────────────────────────
I2C bus    : PASS (0 devices found)
SPI bus    : PASS
UART       : PASS
PWM        : PASS
ADC GP26   : PASS (raw 2192)
── SYSTEM RESILIENCE ───────────────────────────────
Exception  : PASS
── COMPLETE ────────────────────────────────────────
Disconnecting...
Done.
```
