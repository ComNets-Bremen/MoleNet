# Minimalistic test for new MoleNet boards
# Jens Dede <jd@comnets.uni-bremen.de>

import machine
import network
import os
import time
import binascii

import BME280

# LoRa
from SX1262 import Transceiver
from machine import SPI, Pin
import machine
import utime


GPIO_LED_1 = 2
GPIO_LED_2 = 38

BME_I2C_SCL = 8
BME_I2C_SDA = 9
BME_I2C_FREQ = 10000

LED_TIME = 0.5 #s

node_id = binascii.hexlify(machine.unique_id()).decode()

spi = machine.SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
cs = Pin(48, Pin.OUT, value=1)
rst = Pin(15, Pin.OUT, value=1)
busy = Pin(16, Pin.IN) # Was 45 but fails as it is a strapping pin
dio1 = Pin(46, Pin.IN)

sx1262 = Transceiver(spi, cs, rst, busy, dio1)
sx1262.set_freq(868.3)

led1 = machine.Pin(GPIO_LED_1, machine.Pin.OUT)
led2 = machine.Pin(GPIO_LED_2, machine.Pin.OUT)

i2c = machine.SoftI2C(
        scl=machine.Pin(BME_I2C_SCL),
        sda=machine.Pin(BME_I2C_SDA),
        freq=BME_I2C_FREQ,
        )

try:
    bme = BME280.BME280(i2c=i2c)
except:
    bme = None

wlan = network.WLAN()

while True:
    print(f"*** Testing board with ID {node_id} ***")
    print("## Step 1: Test LED")
    led1.on()
    time.sleep(LED_TIME)
    led2.on()
    time.sleep(LED_TIME)
    led1.off()
    time.sleep(LED_TIME)
    led2.off()
    time.sleep(LED_TIME)
    print("## Step 1: Done")
    print("## Step 2: Test BME280")
    if bme is None:
        print("No BME280")
    else:
        try:
            print(f"Temperature: {bme.temperature}")
            print(f"Humidity   : {bme.humidity}")
            print(f"Pressure   : {bme.pressure}")
        except:
            print("BME error. Device disconnected?")
    print("## Step 2: Done")

    print("## Step 3: Test WiFi")
    wlan.active(True)
    nws = wlan.scan()
    wifis = ", ".join([n[0].decode() for n in nws])
    print(f"WiFis: {wifis}")
    wlan.active(False)
    print("## Step 3: Done")

    break



print("Testing LoRa")

sx1262.send("25 byte test Transmission")
msg = sx1262.receive()
print(sx1262.get_meta())
