# LoRaWAN Connection Test

This folder contains minimal LoRaWAN connection test scripts for the MoleNet v7.1 board with the onboard RA-01SH / SX1262 LoRa module.

## Setup Instructions

For the complete setup steps, follow [`MoleNet_v7_1_LoRaWAN_Setup.md`](MoleNet_v7_1_LoRaWAN_Setup.md).

The Markdown guide explains how to:

* connect the MoleNet v7.1 board to TTN
* create the TTN application and device
* create the required config file
* upload files using Thonny
* verify the payload in TTN Live Data

## Test Files

* `main_abp.py`
  LoRaWAN ABP connection test.

* `main_otaa.py`
  LoRaWAN OTAA connection test.

Both scripts send `hello` to TTN every 60 seconds.

## Required Files

Upload the selected test script as `main.py` together with the required library files from the `lib/` folder.

For ABP, use:

* `config_ABP.py`

For OTAA, use:

* `config_OTAA.py`

## Notes

* Use only one test script at a time.
* Keep the LoRa antenna connected.
* No sensors are required.
* These scripts only test LoRaWAN connection.
