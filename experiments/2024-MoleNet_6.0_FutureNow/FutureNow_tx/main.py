from config import *
from machine import Pin, SPI, SoftSPI
from sx127x import SX127x
import dht

device_spi = SoftSPI(
    baudrate = 200000, 
    polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB,
    sck = Pin(device_config['sck'], Pin.OUT, Pin.PULL_DOWN),
    mosi = Pin(device_config['mosi'], Pin.OUT, Pin.PULL_UP),
    miso = Pin(device_config['miso'], Pin.IN, Pin.PULL_UP))

Pin(device_config['reset'], Pin.OUT, value=1)
lora = SX127x(device_spi, pins=device_config, parameters=lora_parameters)

d = dht.DHT11(Pin(16))

try:
    d.measure()
except OSError:
    print("No DHT-11 connected")

payload = 'Temperature: {}, Humidity: {}'.format(d.temperature(),d.humidity())
print("Sending packet: \n{}\n".format(payload))
lora.println(payload)
