import picokeypad
import time

keypad = picokeypad.PicoKeypad()
keypad.set_brightness(0.05)

colors = [
    (255,0,0), (255,165,0), (255,255,0), (0,255,0),
    (0,255,255), (0,0,255), (128,0,255), (255,0,128),
    (255,0,0), (255,165,0), (255,255,0), (0,255,0),
    (0,255,255), (0,0,255), (128,0,255), (255,0,128),
]

for i in range(16):
    keypad.illuminate(i, *colors[i])
keypad.update()

while True:
    pressed = keypad.get_button_states()
    if pressed:
        print(f"Button pressed: {pressed}")
    time.sleep(0.1)