# LoRa Gateway for WUSN

LoRa Gateway for WUSN, created by Daniel Helms <dhelms@uni-bremen.de>, https://github.com/B00mb0x/LoRa_Gateway_for_WUSN

It is based on the PyCom boards / ESP32 with LoRa transceiver. https://pycom.io/

## Versions

This repository contains two versions of the gateway:

1) **Deepsleep** is a Python based version which uses the deep sleep
functionality. This version has a higher delay and should not be used for
scenarios, where messages are sent frequently.

2) **Lightsleep** is an Arduino-based version of the gateway. It requires more
energy but also higher packet rates.

## Field experiment
The measured data of the field experiment can be found in the folder Field_Experiment
