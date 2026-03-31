import pycom
import time

pycom.heartbeat(False)

class printing(object):
    def __init__(self):
        print("TEST MIT KLASSE")

def longGreenBlink():
    pycom.rgbled(0x00FF00)  # Green
    time.sleep(5)
