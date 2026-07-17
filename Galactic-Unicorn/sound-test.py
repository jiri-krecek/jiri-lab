from galactic import GalacticUnicorn
import time

gu = GalacticUnicorn()
channel = gu.synth_channel(0)

channel.play_tone(220, 0.5)
gu.play_synth()
time.sleep(2)
gu.stop_playing()