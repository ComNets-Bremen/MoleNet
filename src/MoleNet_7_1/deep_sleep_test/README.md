# Deep Sleep Test

Minimal test to measure MoleNet v7.1 deep sleep current with the onboard RA-01SH / SX1262 LoRa module.

## Files to Upload

Upload these files to the board:

* `main.py`
* `SX1262.py`
* `LoRaWAN.py`
* `EU868.py`
* `config_OTAA.py`
* `cmac.py`

## Before Measurement

* Remove external sensors.
* Do not use the onboard BME280 in this test.
* Remove the SD card from J13.
* Remove the SD card jumper pins from J13, if used.
* Remove the LED jumper from J4 pins 1 and 2.
* Remove the jumper from J16.
* Keep the LoRa antenna connected.

## Board + LoRa Measurement

* Keep LoRa VDD / RA_VDD connected.
* Run `main.py`.
* Wait until the board enters deep sleep.
* Measure the stable current.

This gives the board + LoRa deep sleep current.

## Board Only Measurement

* Disconnect LoRa VDD / RA_VDD.
* Keep the J13 SD card removed.
* Keep the J13 SD card jumper pins removed, if used.
* Keep the J4 LED jumper removed.
* Keep the J16 jumper removed.
* Run `main.py`.
* Wait until the board enters deep sleep.
* Measure the stable current.

This gives the board only deep sleep current.

## Notes

* `sx.sleep()` puts the LoRa chip into sleep mode but does not remove LoRa supply current.
* To measure board only current, LoRa VDD / RA_VDD must be disconnected.
* For the lowest board only deep sleep current, remove J4, J13, J16, and disconnect LoRa VDD / RA_VDD.
