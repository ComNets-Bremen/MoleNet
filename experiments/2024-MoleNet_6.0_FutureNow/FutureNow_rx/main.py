from config import *
from machine import Pin, SPI, SoftSPI, I2C
from sx127x import SX127x
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
from time import sleep

device_spi = SoftSPI(
    baudrate = 200000, 
    polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB,
    sck = Pin(device_config['sck'], Pin.OUT, Pin.PULL_DOWN),
    mosi = Pin(device_config['mosi'], Pin.OUT, Pin.PULL_UP),
    miso = Pin(device_config['miso'], Pin.IN, Pin.PULL_UP))

Pin(device_config['reset'], Pin.OUT, value=1)
lora = SX127x(device_spi, pins=device_config, parameters=lora_parameters)

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16

i2c = I2C(1, scl=Pin(8), sda=Pin(9), freq=10000)     #initializing the I2C method for ESP32

lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns)

while True:
    if lora.received_packet():
        lcd.clear()
        lcd.putstr("Receiving...")
        sleep(1)
        lcd.clear()
        lora.blink_led()
        payload = lora.read_payload().decode("utf-8")
        print(payload)
        tmp, hum = payload.split(",")
        print(tmp+"        "+hum)
        lcd.putstr(tmp+""+hum)
        
