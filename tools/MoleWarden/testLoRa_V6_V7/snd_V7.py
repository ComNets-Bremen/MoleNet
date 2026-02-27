from machine import SoftSPI, Pin
from SX1262 import Transceiver
import utime

spi = SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
cs = Pin(48, Pin.OUT, value=1)
rst = Pin(15, Pin.OUT, value=1)
busy = Pin(16, Pin.IN)
dio1 = Pin(46, Pin.IN)

sx1262 = Transceiver(spi, cs, rst, busy, dio1)

sx1262.settings(
    power=17,
    sf=7,
    bw=125,
    cr=4/5,
    syn_word=0x12,
    inv_iq=False,
    crc=True,
    exp_header=True
)


# Send loop

while True:
    message = "Hello from SX1262 (V7)!"
    success = sx1262.send(message, freq=868.3)
    if success:
        print("Message sent:", message)
    else:
        print("Sending failed")
    utime.sleep(5)  



# Receive loop

# while True:
#     payload, snr, rssi = sx1262.receive(868.3, timeout=5)
#     print(payload, snr, rssi)

