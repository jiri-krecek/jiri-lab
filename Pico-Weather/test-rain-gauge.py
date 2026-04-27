from machine import Pin
import time

count = 0
last_time = 0

def rain_pulse(pin):
    global count, last_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_time) > 1990:
        count += 1
        last_time = now

rain = Pin(3, Pin.IN, Pin.PULL_UP)
rain.irq(trigger=Pin.IRQ_FALLING, handler=rain_pulse)

print("Watching GP3 for pulses...")

while True:
    print(f"Pulses: {count}")
    time.sleep(2)