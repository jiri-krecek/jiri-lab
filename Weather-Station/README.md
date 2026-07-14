# Weather Station GW7261

Alright, this is my two-board personal weather station reporting to CWOP/APRS every 5 minutes from my location in Lombard, IL.

Live data:
- [FindU](https://www.findu.com/cgi-bin/wx.cgi?call=GW7261)
- [APRS.fi](https://aprs.fi/#!call=a%2FGW7261&timerange=3600&tail=3600)
- [Gladstone Family](https://weather.gladstonefamily.net/site/search?site=G7261&Get+information=Get+information)

This is not a step-by-step build manual by any means. If it did I'd have to write hundreds of pages. 
It is a description of what the station is, how it is put together, why the design decisions were made, and what broke along the way -- and broke it did! Dozens of times to say the least! 
If you are building something similar, the failure modes section is probably the most valuable part -- most of this design exists because something went wrong first. Lots of it!
Was this painful?
Oh yes!
Would I do this again?
Oh yes!

---

## What it consists of

Two boards, split by job.

| Role | Hardware | Runs |
| --- | --- | --- |
| Sensor node | Raspberry Pi Pico 2W (RP2350) | MicroPython, `main.py` |
| Submission + data node | Raspberry Pi Zero 2W | Debian Trixie, `cwop.py` as a systemd service |

Sensors:

| Sensor | Interface | Measures |
| --- | --- | --- |
| BMP390 | I2C, addr `0x77` | Barometric pressure |
| HDC3022 | I2C, addr `0x44` | Temperature, relative humidity |
| SparkFun SEN-15901 | GPIO / ADC | Wind speed, wind direction, rainfall |

A UV sensor (LTR390) was part of the original plan and was abandoned. The site is shaded, so a UV reading here would be measuring the tree, not the sky. The `uv` field still exists in the serial line as a hardcoded `0.0` placeholder rather than removing it and renumbering the downstream parser.

Housing: the BMP390 and HDC3022 live in a properly-shop-built wooden Stevenson screen. This replaced a commercial plastic LaCrosse screen, and that swap alone was worth more accuracy than any code change in this repo (see failure modes below).
If you are thinking of buying that plastic stevenson screen off Amazon. Jsut DON'T.... just don't.

---

## How it is wired

Broad strokes only.

The Pico is mounted on a board with the sensors wired back to it. and it it way simpler than it seems: 
VIN (or VCC) is your 3V power
GND is your ground
SCL is your clock and 
SDA is your actual data

So, each sensor needs only 4 wires - 2 for power, one as a clock to trigger the sensor to take a reading and one is the actual data wire over which the sensors sends the values back to Pico
Both I2C sensors share one bus and because they have different addresses, there is no collision:

WARNING: when deciding which sensors to build your projects from (if using I2C) be sure to verify what addresses your sensors need, so there is no overlap. Otherwise your project won't work due to data collisions.

```
BMP390   GP0 > SDA, GP1 > SCL, 3V3 > VIN, GND > GND
HDC3022  GP0 > SDA, GP1 > SCL, 3V3 > VIN, GND > GND
```

The SparkFun kit is not I2C, and that separation matters -- see the resilience section:

```
Wind vane      GP26 (ADC)   voltage divider, resistance varies by direction
Anemometer     GP4  (IRQ)   rising-edge pulse counter, reed switch
Rain gauge     GP3  (IRQ)   falling-edge pulse counter, tipping bucket
```

The Pico connects to the Pi Zero by a single micro USB cable, which carries both power and data. The Zero is on wired Ethernet via an Ethernet + USB HAT and boots from a 128GB USB stick, not an SD card.

### Why USB serial and not the Pico's WiFi

The Pico 2W has WiFi. It is not used.

The station's original recurring failure was the Pico going silent during storms. Adding a WiFi stack to the sensor node means adding an association state machine, a DHCP lease, and a reconnect path to the exact board that was already wedging during the exact weather being measured. USB gives power and data over one cable with no radio involved, and the Zero already has reliable wired Ethernet. Two other Pi Zeros on this network were decommissioned specifically for unreliable WiFi, which did not encourage betting the station on more of it.

The split of responsibility follows from this: the Pico only reads sensors and prints a line. It knows nothing about networks, CWOP, or files. The Zero owns everything that touches the outside world.

---

## Pico: `main.py`

The Pico's entire job is to print one comma-separated line of sensor data to USB serial every 2 minutes, and to never, ever stop doing that.

Cadence:

```
SAMPLE_INTERVAL = 5     # read wind every 5s
SAMPLE_COUNT    = 24    # 24 x 5s = 120s per reported line
```

Wind is sampled every 5 seconds even though a line is only emitted every 2 minutes. That is deliberate: sustained wind is the mean of the 24 samples and gust is the max, so gusts between reports are still caught. Sampling wind only at report time would miss them entirely.

Output line format, 8 fields:

```
temp_f, humidity, slp, uv, wind_sustained, wind_gust, wind_dir, rainfall
95.4,55.9,1019.11,0.00,6.3,9.5,SW,0.000
```

Conversions worth knowing:

- Rain: each tipping-bucket tip is 0.011 inches (SEN-15901 spec). The IRQ handler debounces at 1990ms to reject reed-switch bounce.
- Wind: `(pulses / 5) * 1.492` mph. 1.492 mph per pulse per second is the SEN-15901 anemometer constant, divided by the 5-second sample window.
- Direction: the vane is a resistor network read as a voltage on the ADC. `compass.py` maps voltage to a compass point and picks the dominant direction across the sample window.

Missing values are emitted as empty fields, not zeros. A failed temperature sensor sends `,,` and not `,0.0,`, because 0°F is a real temperature and a lie is worse than a gap.

### Other files on the Pico

| File | Purpose |
| --- | --- |
| `main.py` | The loop. Auto-runs on boot. |
| `compass.py` | Vane voltage to compass direction, dominant-direction logic |
| `micropython_bmpxxx/` | Third-party BMP390 driver library - see credits for Brad Carlile |
| `main-pico-backup.py` | Known-good rollback copy |

The BMP390 needs the `micropython_bmpxxx` library copied onto the Pico's filesystem. It is not built into MicroPython. The HDC3022 needs no library at all -- it is driven with raw I2C register reads in `main.py`, which is about 10 lines and avoids a dependency:

```python
i2c.writeto(HDC3022_ADDR, bytes([0x24, 0x00]))   # trigger measurement
time.sleep_ms(50)
data = i2c.readfrom(HDC3022_ADDR, 6)             # 6 bytes: temp, crc, hum, crc
temp_c = -45 + 175 * (temp_raw / 65535)
humidity = 100 * (hum_raw / 65535)
```

Development is done in VSCodium with `mpremote` over USB.

---

## Zero: `cwop.py`

The Zero reads the Pico's serial lines, keeps rain history, formats APRS packets, submits to CWOP, and journals everything.

| File | Purpose |
| --- | --- |
| `cwop.py` | The service. Serial read, rain accounting, APRS submit, journaling. |
| `config.py` | `STATION_ID`, `LAT`, `LON`, `PASSCODE`, `DRY_RUN`. Not in git. |
| `journal.csv` | Append-only log. Source of truth. Rotated monthly. |
| `rainstate.json` | Persisted rain totals. Written by the service, never by hand. |
| `kord-calibration.py` | Pressure calibration helper against KORD METAR |
| `kord_slp.csv` | Calibration capture data |

`DRY_RUN` in `config.py` prints packets instead of submitting them. Use it when testing packet formatting so you are not sending garbage to the real CWOP network.

### Journal events

Everything is logged to `journal.csv` with a UTC timestamp and an event type:

| Event | Meaning |
| --- | --- |
| `PICO_RAW` | A raw serial line, exactly as received |
| `PICO_RAIN` | Rain totals at submit time |
| `PICO_SILENT` | Silence sentinel tripped, serial reopened |
| `APRS_GTNG` | CWOP server greeting received |
| `APRS_ACK` | CWOP login acknowledged |
| `APRS_OK` | Packet genuinely submitted |
| `APRS_FAIL` | Submit failed, packet did not land |
| `APRS_ERR` | The reason a submit failed |
| `RAIN_STATE_LOAD` | Rain state restored at startup |
| `RAIN_STATE_SAVE_ERR` | Rain state write failed |

A successful submit is four lines: `APRS_GTNG`, `APRS_ACK`, `APRS_OK`, `PICO_RAIN`. A failed one is three: `APRS_ERR`, `APRS_FAIL`, `PICO_RAIN`, with no greeting or ack because the connection never got that far.

### Missing-data handling

The APRS spec sends missing values as `...` sized to the field width, not as zeros. `t000` claims it is 0°F. `t...` honestly says there is no reading. Each field has a formatter that takes a value-or-`None`:

```python
def fmt_temp(temp_f):
    if temp_f is None:
        return "t..."
    return f"t{int(temp_f):03d}"
```

Wind direction, speed, gust, and temperature are the APRS required leading fields. Wind comes from GPIO rather than I2C, so it survives an I2C bus lockup -- which is a large part of why the two sensor groups are kept on separate interfaces.

### Running as a systemd service

`/etc/systemd/system/cwop.service` runs `cwop.py` as a persistent unit, enabled at boot:

```
[Unit]
Description=CWOP Weather Station Submission
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /mnt/data/weather/cwop.py
WorkingDirectory=/mnt/data/weather
Restart=always
User=jiri

[Install]
WantedBy=multi-user.target
```

Deploy is stop-free: overwrite `cwop.py` while the service runs (the running process holds the old code in memory and is unaffected), then `sudo systemctl restart cwop`. Back up first. Watch it come up with `tail -n 20 -f journal.csv`.

---

## Pressure calibration

Two separate corrections, often confused.

### Elevation to sea level

Barometric pressure at 689 feet is meaningfully lower than at sea level, and CWOP wants sea-level pressure. The barometric formula converts station pressure to SLP:

```python
ELEVATION_M = 210.0
slp = (station_pressure / (1.0 - ELEVATION_M / 44330.77) ** (1 / 0.1902632)) - PRESSURE_OFFSET_HPA
```

Get the elevation right. This is the difference between a plausible reading and an absurd one.

### Sensor offset against a known-good reference

Individual BMP390 units have a unit-to-unit offset. This one reads 1.3 hPa high:

```python
PRESSURE_OFFSET_HPA = 1.3
```

Calibrated against Chicago O'Hare (KORD) METAR sea-level pressure in stable weather:

```
https://aviationweather.gov/api/data/metar?ids=KORD&format=raw
```

Procedure: pick a calm, stable day. Read the sensor's computed SLP and the reference station's reported SLP at the same moment. `offset = sensor_SLP - reference_SLP`. Validated 2026-04-28.

Choose a reference that is a manned airport at comparable elevation, reasonably nearby. Do not calibrate during a passing front, and do not calibrate against an automated station of unknown quality.

### Result

Compared against KORD at 16:00 CDT on 2026-07-14:

| Metric | KORD | GW7261 |
| --- | --- | --- |
| Pressure (hPa) | 1018.9 | 1019.1 |
| Temp (F) | 96.1 | 97.3 |
| RH (%) | 39 | 50.3 |

Pressure and temperature are within expected error. Humidity is not, and that is honest rather than broken: the HDC3022 has roughly a ±5% accuracy margin, and this station sits in a river valley still dissipating moisture a week after nearby flooding while KORD sits on well-drained flat ground. Humidity is the weakest link in this build.

---

## Failure modes and fixes

Everything in this section is here because it actually happened.

### The plastic radiation shield was lying by 17°F

The original commercial LaCrosse plastic Stevenson screen read 112°F on a day cooler than one where the wooden screen read 95°F. Thin plastic absorbs solar radiation and re-radiates it onto the sensor, so you measure the temperature of a hot plastic box, not of air. Wood has thermal mass and insulates; with proper louvers you get real convective exchange.

No code fixes this. If your temperatures are absurd in direct sun, the problem is your enclosure.

### Storm freezes: I2C bus lockup

The recurring failure: the Pico goes silent mid-storm. It stays USB-enumerated so `cwop.py` sits waiting for a line that never comes. Confirmed mechanism is a loop stall, most likely an I2C bus lockup triggered by storm electrical noise with the HDC3022 sitting near 100% RH.

Four layers now protect against this:

1. Sensor init is wrapped in a retry loop. A boot-time I2C hiccup retries instead of throwing an unhandled exception and dropping the board to the REPL, dead until someone notices.
2. Every sensor read is wrapped in try/except and returns `None` on failure. One flaky sensor degrades to blank fields; the others keep reporting.
3. A hardware watchdog (`WDT(timeout=8000)`, the RP2350's ~8.3s cap) is fed unconditionally at the top of the loop, before any sensor work. A transient read failure must never accidentally starve the watchdog.
4. A consecutive-failure counter. If *both* I2C sensors fail together for `MAX_FAIL_CYCLES` report cycles (~6 minutes), the bus is genuinely wedged, so the code deliberately *stops* feeding the watchdog and lets it hard-reset the board. Layer 1 then runs a clean init on the fresh boot.

```python
if fail_cycles >= MAX_FAIL_CYCLES:
    print("I2C bus persistently wedged - allowing watchdog reset...")
    while True:
        time.sleep(1)   # no wdt.feed() here -> reset within ~8s
```

The distinction between layer 2 and layer 4 is the important one. A single sensor failing is degradation, and you report what you have. Both failing together is a bus problem, and no amount of retrying at the application level fixes a wedged bus. Only a reset does.

### Silence sentinel on the Zero

The Pico's watchdog cannot help if the Pico is fine and the *serial link* is the problem. So `cwop.py` tracks the time of the last successfully parsed line:

```python
SILENCE_TIMEOUT = 360   # 3 full 2-minute Pico cycles
```

360 seconds guarantees at least two full missed broadcasts in any phase alignment before acting, so it cannot false-trip on timing jitter. On trip: journal it, close the port, reopen it.

### Sensor stuck after physical handling

Moving the sensor board into the new screen without unplugging it left the BMP390 reporting a frozen 863.93 hPa against an expected ~1020. The chip still answered on the I2C bus and still reported its correct chip ID, so nothing looked broken -- but the measurement registers were serving stale garbage. TBH, if I were in the middle of 863 hPa barometric pressure, my eardrums would explode, blood boil and eyeballs popped out. 863 hPa is a pressure I'd probebaly expect inside an EF5 2-mile tornado wedge, not on a clear summer day with no wind. So, yes, there was some data issue indeed. 

The tell was that the value never moved. Real atmospheric pressure never holds bit-identical for four hours.

A reboot fixed it completely - it was just stuck at a weird state -- how or why? I will never know. BUt a quick reboot thankfully addressed it and the sensor started reporting baro pressure within 1/2 hPa margin of error off my KORD reference airport.
Diagnosis order that mattered:

1. Is it plausible? 863.93 hPa is a several-thousand-foot elevation reading, not a 689-foot one. Unless you are in the middle of an EF5 tornado and your eyballs pop out, eardrums burst and blod boils. 
2. Is it *moving*? Frozen to two decimals across hours is a stuck state, not weather.
3. Does the device still answer? `i2c.scan()` and a chip ID read confirmed the chip was alive, ruling out a broken connection or ESD damage.
4. Does a clean init clear it? Yes. Damaged silicon does not un-damage itself on a power cycle, so this was a stuck state machine, most likely from a momentary power or bus interruption during handling.

### Rain totals died on every reboot

`rain_1h`, `rain_24h`, and `rain_midnight` were local variables. Any restart -- deploy, crash, watchdog reset, power blip -- wiped them, meaning the 24-hour total was only correct after 24 hours of continuous uptime.

Now persisted to `rainstate.json`, written on every valid line (~2 min) and reloaded at startup. The algorithm is trivial. The failure handling is not, and that is the whole job:

Atomic write. Write to a temp file, then `os.rename()` over the real one. Rename is atomic on POSIX, so the file on disk is always either the complete old version or the complete new one, never a truncated half-write from a power cut mid-`json.dump()`.

```python
with open(tmp_file, "w") as f:
    json.dump(state, f)
os.rename(tmp_file, RAIN_STATE_FILE)
```

Fail safe on load. Missing file, corrupt JSON, missing key, bad date string -- every path falls back to clean empty defaults. A corrupt state file that crashes the service on every boot is strictly worse than having no persistence at all. This is non-negotiable and it is the reason for the broad `except Exception`.

Prune on reload. Buckets store absolute Unix timestamps, so they are pruned against `time.time()` at load. Down for 3 hours means the 1-hour bucket reloads already empty, automatically, using the same prune logic the main loop runs.

Midnight check on reload. If the persisted `last_midnight` date is older than today's local date, the restart crossed midnight and `rain_midnight` resets. Worst case is a gap, which is acceptable. Double-counting is not.

Rain-since-midnight is *local* midnight per the CWOP/MADIS spec, while the APRS packet timestamp stays UTC. Two different clocks in one packet, on purpose.

Deploy timing: the persistence deploy itself causes one unavoidable zero-out, since there is no state file yet to reload from. Deploy on a dry day when `rain_24h` reads `0.0000` and it costs nothing.

### The journal was logging failures as successes

`submit_aprs()` returned `True`/`False` and `main()` threw the value away, then wrote an `APRS_SUB` line unconditionally. A submit that timed out logged `APRS_ERR` immediately followed by `APRS_SUB`, which reads as "this failed and also submitted."

```python
success = submit_aprs(packet)
if success:
    write_journal("APRS_OK", packet)
else:
    write_journal("APRS_FAIL", packet)
```

Now `APRS_OK` means the packet reached CWOP and `APRS_FAIL` means it did not. Note that `last_submit = now` is set either way, deliberately: a network outage should retry on the normal 5-minute cadence rather than hammering CWOP on every new line.

Occasional CWOP submit timeouts are normal and self-recovering. APRS assumes individual reports can drop. This fix was about honest logging, not about a broken submission path.

---

## Data pipeline

```
Pico 2W  --USB serial-->  Pi Zero 2W  --TCP-->  cwop.aprs.net:14580
                              |
                              +--> journal.csv (source of truth)
                              |
                              +--> SCP push --> syscheck node
                                                   |
                                                   +--> PostgreSQL (weather.station_readings)
                                                          |
                                                          +--> Grafana
```

`journal.csv` on the Zero is the source of truth. Everything downstream is derived and can be rebuilt from it.

---

## Design principles

Split by failure domain. The Pico only reads sensors. The Zero only handles networks and state. Neither needs to know how the other fails.

Never fake data. Missing readings are blank fields and `...` markers, never zeros. A gap in the record is honest. A zero is a lie that looks like data.

Let it reset. The watchdog reset path is not a failure of the design, it is the design. Recovering in 8 seconds beats staying wedged until a human notices.

Fail safe, not fail clever. A corrupt state file loads as empty. A failed save logs and retries next cycle. Nothing in the recovery path is allowed to be the thing that takes the station down.

Validate against a reference. A number that looks plausible is not the same as a number that is right. KORD is 20 miles away and staffed.

---

## Credits

BMP390 driver: [MicroPython_BMPxxx](https://github.com/bradcar/MicroPython_BMPxxx)
by Brad Carlile (bradcar). A single driver covering the BMP585, BMP581, BMP390,
BMP280, and BME280 over I2C, tested on the Pico 2. It credits earlier work by
Jose D. Montoya and Scott in its own README.

Only the BMP390 needs a library here. The HDC3022 is driven with raw I2C register
reads in `main.py`, which is about ten lines and avoids a dependency.

---

## License

MIT. Free to use, modify, and distribute with attribution.

Co-developed with assistance from Claude AI (Anthropic). Logic, design, code modifications, and testing by the author.

Jiri Krecek, Archer Dynamics LLC -- [goarcherdynamics.com](https://goarcherdynamics.com)
