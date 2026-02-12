# Test script for MoleNet boards
# Jens Dede <jd@comnets.uni-bremen.de>
# Faruk Kollar <fkollar@uni-bremen.de>

import machine
import network
import os
import time
import binascii

import BME280
from machine import UART, Pin
# LoRa
from SX1262 import Transceiver
from SX1276 import Transceiver
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

print("Testing Sd Card")
sd = machine.SDCard(slot=2, sck=12, miso=13, mosi=11, cs=10, freq=200_000)
utime.sleep(1)
os.mount(sd, '/sd') # mount

with open("/sd/test.text","w") as f:
    f.write("This is a test")

with open("/sd/test.text","r") as f:
    for row in f:
        print(row)
        
print(os.listdir('/sd/'))    # list directory contents

os.umount('/sd')    # eject
print("Success")

print("Testing Sdi-12 Interface")

class SDI12:
    def __init__(self):
        print("Init SDI12")
        
        #define pins, start with TX activated
        self.RX = Pin(18)
        self.TX = Pin(17)
        self.SDI_Marking = Pin(37, Pin.OUT, value=1)
        self.RX_Enable = Pin(36, Pin.OUT, value=0)
        self.TX_Enable = Pin(35, Pin.OUT, value=0)

        #define UART
        self.sdi12 = UART(1, baudrate=1200, bits=7, parity=0, stop=1, tx=self.TX, rx=self.RX)
        utime.sleep_ms(500)
        self.sdi12.read() # Discard the boot message from sensor
        self.command()
        utime.sleep(1)
        self.command("1D0!") # Data collect command for sensor address 1
        
    def write(self, msg):
        print("writing")
        #enter write mode
        self.RX_Enable.value(0)
        self.TX_Enable.value(0)
        #12ms break
        self.SDI_Marking.value(0)
        utime.sleep_ms(13)
        #8.33ms marking
        self.SDI_Marking.value(1)
        utime.sleep_ms(9)
        #transmit command
        self.sdi12.write(msg)
        self.sdi12.flush() #wait for all data to be sent, if errors occur, try utime.sleep_ms(50)
        
    def read(self):
        print("reading")
        #enter reading mode
        self.RX_Enable.value(1)
        self.TX_Enable.value(1)
        utime.sleep_ms(500)
        #read
        response = self.sdi12.read()
        print(response)        

    def command(self, command = "1M!"): # Take measurements command for sensor address 1
        #send SDI12 command
        self.write(command)
        #read sensor answer
        self.read()
        
power_enable = Pin(1, Pin.OUT)
power_enable.on()
sdi12 = SDI12()
power_enable.off()



print("Testing LoRa")

spi = machine.SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
cs = Pin(48, Pin.OUT, value=1)
rst = Pin(15, Pin.OUT, value=1)
busy = Pin(16, Pin.IN) # Was 45 but fails as it is a strapping pin
dio1 = Pin(46, Pin.IN)

sx1262 = Transceiver(spi, cs, rst, busy, dio1)
sx1262.settings(power=17, sf=7, bw=125, cr=4/5, syn_word=0x12, inv_iq=False, crc=True, exp_header=True)
sx1262.set_freq(868.3)

for i in range(1, 4):
    print("Sending message", i)

    ok = sx1262.send("Hello World! {}".format(i))

    if ok:
        print(sx1262.receive())
        print(sx1262.get_meta())




