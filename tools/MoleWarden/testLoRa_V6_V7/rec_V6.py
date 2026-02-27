from SX1276 import Transceiver
from machine import SoftSPI, Pin
import utime

spi = SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
cs = Pin(48, Pin.OUT, value=1)
rst = Pin(45, Pin.OUT, value=1)
dio0 = Pin(46, Pin.IN)

sx1276 = Transceiver(spi, cs, rst, dio0)

sx1276.settings(
    power=17,
    sf=7,
    bw=125,
    cr=4/5,
    syn_word=0x12,
    inv_iq=False,
    crc=True,
    exp_header=True
)

#sending
#
# while True:
#     print("Sending...")
#     sx1276.send("Hello from SX1276", 868.3)
#     utime.sleep(2)


# #receiving

while True:
    msg, snr, rssi = sx1276.receive(freq=868.3, timeout=10)
    if msg:
        print("Received message:", msg.decode())
        print("SNR:", snr, "RSSI:", rssi)
    else:
        print("No message received")
    utime.sleep(1)