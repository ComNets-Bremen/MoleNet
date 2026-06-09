from config_OTAA import *
from machine import SPI, Pin
from LoRaWAN import LoRaWAN
import machine
import utime
import EU868
from SX1276 import Transceiver

spi = machine.SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
lora_cs = Pin(48, Pin.OUT, value=1)
lora_rst = Pin(15, Pin.OUT, value=1)
lora_dio0 = Pin(46, Pin.IN)

sx1276 = Transceiver(spi, lora_cs, lora_rst, lora_dio0)
lw = LoRaWAN(sx1276, EU868.FREQS)
# lw.reset()

if not lw.joined: # don't check, when you want to re-register a device as another device! NO,NO,NO: Call lw.reset() instead! 
    lw.join_otaa(AppKey, joinEUI, devEUI, sf=12)
lw.send("Hello World")