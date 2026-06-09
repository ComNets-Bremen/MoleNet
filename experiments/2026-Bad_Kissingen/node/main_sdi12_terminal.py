import utime
import machine
from machine import I2C, Pin, deepsleep, SoftI2C, RTC
#import array
import ubinascii
import BME280
import os
import struct
import EU868
from SDI12 import SDI12
from SX1276 import Transceiver
from LoRaWAN import LoRaWAN
from config_OTAA import *


nan = float("NAN")

class MoleNet:
    def __init__(self):
        #Variables
        self.soil_temp = nan
        self.soil_perm = nan
        self.soil_id = nan
        self.soil_econ = nan # electrical conductivity only for the TEROS12 sensor, not TEROS11
        #set status led to indicate sleep
        self.status_led = Pin(2, Pin.OUT, value=1)
        
        #setup RTC, Thonny automatically sync time with computer
        self.rtc = RTC()
        
        #setup bme280
        try:
            i2c = SoftI2C(scl=Pin(8), sda=Pin(9), freq=10000)
            self.bme = BME280.BME280(i2c=i2c)
        except Exception as exc:
            print(exc)
            
        #setup SDI12
        self.num_sensors = 1
        rx = Pin(18)
        tx = Pin(17)
        marking = Pin(37, Pin.OUT, value=1)
        rx_enable = Pin(36, Pin.OUT, value=0)
        tx_enable = Pin(35, Pin.OUT, value=0)
        power_sdi12 = Pin(1, Pin.OUT, value=1)
        self.sdi12 = SDI12(rx, tx, marking, rx_enable, tx_enable)
            
        #setup sd card
        try:
            sd = machine.SDCard(slot=2, sck=12, miso=13, mosi=11, cs=10, freq=200_000)
            utime.sleep(1)
            os.mount(sd, '/sd') # mount
            self.sd_available = True 
        except Exception as exc:
            print(exc)
            self.sd_available = False

        
        #setup LoRaWAN
        spi = machine.SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
        lora_cs = Pin(48, Pin.OUT, value=1)
        lora_rst = Pin(15, Pin.OUT, value=1)
        lora_dio0 = Pin(46, Pin.IN)
        
        sx1276 = Transceiver(spi, lora_cs, lora_rst, lora_dio0)
        self.lw = LoRaWAN(sx1276, EU868.FREQS)
        if not self.lw.joined:
            self.lw.join_otaa(AppKey, joinEUI, devEUI, sf=12)
        

    def measure_soil(self):
        val = self.sdi12.measure(1)
        try:
            id,perm,temp,econ = val.decode().strip().split('+')
        except Exception as exc:
            print("Exception measure soil: ",exc)
            print("value is ",val)
        if self.sd_available:
            with open("/sd/soil_data.csv","a") as f:
                f.write("{};{};{}\n".format(i, self.rtc.datetime(),val))
        utime.sleep_ms(50)
        try:
            self.soil_id = int(id)
            self.soil_perm = float(perm)
            self.soil_temp = float(temp)
            self.soil_econ = float(econ) 
        except Exception as exc:
            print("Exception converting soil data: ", exc)
            
        
    def measure_air(self):
        temp = self.bme.temperature
        hum = self.bme.humidity
        pres = self.bme.pressure
        return temp, hum, pres

    def send(self):
        data = struct.pack('iff',self.soil_id,self.soil_perm,self.soil_temp)
        print("Sending packet...", ubinascii.hexlify(data))
        self.lw.send(data)
        
molenet = MoleNet()
while True:
    print("SDI12> ",end='') 
    command = input()
    molenet.sdi12.command(command)
    
#machine.deepsleep(1800000)
