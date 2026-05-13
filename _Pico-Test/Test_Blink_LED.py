import machine
import time

led = machine.Pin("LED", machine.Pin.OUT)
reps = 10

for i in range(reps):
    led.on()
    time.sleep(0.01)
    led.off()
    time.sleep(0.99)