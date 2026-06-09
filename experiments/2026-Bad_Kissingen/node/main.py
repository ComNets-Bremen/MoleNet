import utime
import machine
from machine import I2C, Pin, deepsleep, SoftI2C, RTC
import onewire, ds18x20
import time
#import array
# import ubinascii # we use now data.hex() instead of ubinascii.hexify(data)
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
        self.ds_temp = nan
        self.bme_temp = nan
        self.bme_hum = nan
        self.bme_pres = nan

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
            
        # setup DS18B20
        ds_data_pin = Pin(42)
        self.ds_enable_pin = Pin(41,Pin.OUT,value=1)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_data_pin))
        roms = self.ds_sensor.scan()
        print(f'Found {len(roms)} ds devices: ', [rom.hex('-') for rom in roms])        
        self.ds_enable_pin.off()
        
        #setup SDI12
        self.num_sensors = 1
        rx = Pin(18)
        tx = Pin(17)
        marking = Pin(37, Pin.OUT, value=1)
        rx_enable = Pin(36, Pin.OUT, value=0)
        tx_enable = Pin(35, Pin.OUT, value=0)
        self.power_sdi12 = Pin(1, Pin.OUT, value=1)
        time.sleep_ms(165) # maximum power up time of the TEROS 11/12 sensor
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
            print("Ups, i have to join to LoRWAN (OTAA) again?") 
            self.lw.join_otaa(AppKey, joinEUI, devEUI, sf=12)
        
    def decode_measure_soil(self,message):
        text = message.decode().strip()
        result = []
        current = ""

        for c in text:
            if c in "+-" and current:
                result.append(current)
                current = c   # start new token WITH sign
            else:
                current += c

        if current:
            result.append(current)

        print(result)
        if len(result)==3:
            return int(result[0]), float(result[1]), float(result[2])
        else:
            raise Exception(f"3 values expected, but {len(result)} received.") 
    
    def measure_soil(self):
        val = self.sdi12.measure(1)
        try:
            id,perm,temp = self.decode_measure_soil(val)
        except Exception as exc:
            print("Exception measure soil: ",exc)
            print("value is ",val)
        if self.sd_available:
            with open("/sd/soil_data.csv","a") as f:
                f.write("{};{};{}\n".format(i, self.rtc.datetime(),val))
        utime.sleep_ms(50)
        try:
            self.soil_id = id
            self.soil_perm = perm
            self.soil_temp = temp
        except Exception as exc:
            print("Exception converting soil data: ", exc)
            
        
    def measure_air(self):
        self.bme_temp = float(self.bme.temperature[:-1])
        self.bme_hum = float(self.bme.humidity[:-1])
        self.bme_pres = float(self.bme.pressure[:-3])
        return self.bme_temp, self.bme_hum, self.bme_pres

    def measure_temp(self):
        # DS18B20 Temperature Sensor
        # https://esp32io.com/tutorials/esp32-temperature-sensor
        # https://docs.micropython.org/en/latest/esp8266/tutorial/onewire.html
        self.ds_enable_pin.on()
        self.ds_sensor.convert_temp()
        time.sleep_ms(750)
        roms = self.ds_sensor.scan()
        for rom in roms:
            self.ds_temp = self.ds_sensor.read_temp(rom)
            print(f"DS Temp {rom.hex('-')}:", self.ds_temp)        
        self.ds_enable_pin.off()
        
    def send(self):
        data = struct.pack('ffffff',self.soil_perm,self.soil_temp,self.ds_temp,self.bme_temp,self.bme_hum,self.bme_pres)
        print("Sending packet...", data.hex())
        self.lw.send(data)
        
molenet = MoleNet()
molenet.status_led.on()
molenet.measure_soil()
temp,hum,press = molenet.measure_air()
print (f"BME temp {temp} humidity {hum} pressure {press}")
molenet.measure_temp()
molenet.send()
molenet.status_led.off()
molenet.power_sdi12.off()
# machine.deepsleep(60000) # here 60 sec
# machine.deepsleep(900000) # in ms here 900'000 ms == 900 sec == 15 min  
machine.deepsleep(3600000) # in ms here 3'600'000 ms == 3'600 sec == 60 min  
