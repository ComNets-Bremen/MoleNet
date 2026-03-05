# Test read out of analog sensors
# Jens Dede <jd@comnets.uni-bremen.de>

import machine
import network
import os
import time
import binascii

import json

import BME280

from ec_sensor import EC
from do_sensor import DO
from ph_sensor import PH
from bme_sensor import get_bme_start_dict as start_dict

# Config

ENABLE_JSON = True
ALWAYS_ON   = True


## LED
GPIO_LED_1 = 2
GPIO_LED_2 = 38
LED_TIME = 0.5 #s

## BME
BME_I2C_SCL = 8
BME_I2C_SDA = 9
BME_I2C_FREQ = 10000


## Sensor 1: PH
sensors = dict()

sensors["sensor1"] = dict()
sensors["sensor1"]["name"] = "PH"
sensors["sensor1"]["vcc_pin"] = 40 # TODO: Check (collision)
sensors["sensor1"]["gnd_pin"] = 42
sensors["sensor1"]["vcc_drive"] = machine.Pin.DRIVE_3
sensors["sensor1"]["adc_pin"] = 3  # ADC1 Channel, CH 2
sensors["sensor1"]["convert"] = lambda x : x / 28.342 * 3.0

## Sensor 2: EC
sensors["sensor2"] = dict()
sensors["sensor2"]["name"] = "EC"
sensors["sensor2"]["vcc_pin"] = 45
sensors["sensor2"]["gnd_pin"] = 16
sensors["sensor2"]["vcc_drive"] = machine.Pin.DRIVE_3
sensors["sensor2"]["adc_pin"] = 6  # ADC1 Channel, CH 5
sensors["sensor2"]["convert"] = lambda x : x / 28.310 * 3.0
# EC with jumper VCC / GPIO45

## Sensor 3: DO
sensors["sensor3"] = dict()
sensors["sensor3"]["name"] = "DO"
sensors["sensor3"]["vcc_pin"] = 39
sensors["sensor3"]["gnd_pin"] = 39 # TODO: Check (collision)
sensors["sensor3"]["adc_pin"] = 5  # ADC1 Channel, CH 4
sensors["sensor3"]["convert"] = lambda x : x / 60.766 * 3.0

# End Config

# Start init
## General
node_id = binascii.hexlify(machine.unique_id()).decode()

led1 = machine.Pin(GPIO_LED_1, machine.Pin.OUT)
led2 = machine.Pin(GPIO_LED_2, machine.Pin.OUT)

## BME
i2c = machine.SoftI2C(
        scl=machine.Pin(BME_I2C_SCL),
        sda=machine.Pin(BME_I2C_SDA),
        freq=BME_I2C_FREQ,
        )

try:
    bme = BME280.BME280(i2c=i2c)
except:
    bme = None

## Sensors

for sensor in sensors:
    print(f"Init sensor {sensor}")
    sensors[sensor]["vcc"] = machine.Pin(
            sensors[sensor]["vcc_pin"],
            machine.Pin.OUT,
            drive=sensors[sensor].get("vcc_drive", 0),
            )
    sensors[sensor]["vcc"].off()
    sensors[sensor]["gnd"] = machine.Pin(sensors[sensor]["gnd_pin"], machine.Pin.OUT)
    sensors[sensor]["gnd"].off()
    sensors[sensor]["adc"] = machine.ADC(sensors[sensor]["adc_pin"], atten=machine.ADC.ATTN_11DB) # TODO: Check, https://docs.micropython.org/en/latest/esp32/quickref.html#adc-analog-to-digital-conversion

# End init

ec = None
do = None
ph = None

for sensor in sensors:
    if sensors[sensor]["name"] == "EC":
        ec = EC(sensors[sensor])
    elif sensors[sensor]["name"] == "DO":
        do = DO(sensors[sensor])
    elif sensors[sensor]["name"] == "PH":
        ph = PH(sensors[sensor])
    else:
        print(f"Unknown sensor {sensors[sensor]}")
if ALWAYS_ON:
    ph.on()
    ec.on()
    do.on()

# Start main loop
while True:
    sensor_dict = start_dict(bme)

    if ec is not None:
        led1.on()
        if not ALWAYS_ON:
            ec.on()
        time.sleep(1)
        sensor_dict["sensor2"] = {}
        sensor_dict["sensor2"]["value"] = ec.get_reading()
        sensor_dict["sensor2"]["unit"]  = "ms/cm"
        sensor_dict["sensor2"]["time"]  = time.time()
        if not ALWAYS_ON:
            ec.off()
        led1.off()

    if do is not None:
        led2.on()
        if not ALWAYS_ON:
            do.on()
        time.sleep(1)
        sensor_dict["sensor3"] = {}
        sensor_dict["sensor3"]["value"] = do.get_reading()
        sensor_dict["sensor3"]["unit"]  = "%"
        sensor_dict["sensor3"]["time"]  = time.time()
        if not ALWAYS_ON:
            do.off()
        led2.off()

    if ph is not None:
        led1.on()
        led2.on()
        if not ALWAYS_ON:
            ph.on()
        time.sleep(1)
        sensor_dict["sensor1"] = {}
        sensor_dict["sensor1"]["value"] = ph.get_reading()
        sensor_dict["sensor1"]["unit"] = ""
        sensor_dict["sensor1"]["time"]  = time.time()
        if not ALWAYS_ON:
            ph.off()
        led1.off()
        led2.off()

    print(f"#!{json.dumps(sensor_dict)}")

    time.sleep(4)
