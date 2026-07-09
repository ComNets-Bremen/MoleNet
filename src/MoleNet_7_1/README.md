# MoleNet v7.1 Test Files

This folder contains basic test files for the MoleNet v7.1 ESP32-S3 board.

## Folder Structure

* `lib/`
  Common MicroPython libraries used by the test scripts.

* `deep_sleep_test/`
  Minimal test to measure board + LoRa deep sleep current.

* `lorawan_connection_test/`
  Minimal ABP and OTAA scripts to test LoRaWAN connection with TTN.

## Notes

* The `lib/` folder does not contain `main.py`.
* Use only one test script as `main.py` on the board at a time.
* Copy the required files from `lib/` to the board together with the selected test script.
* The onboard BME280 is not used in these minimal tests.
* External sensors are not required for these tests.

## Included Tests

### Deep Sleep Test

Used to measure the deep sleep current of:

* MoleNet board + LoRa module
* MoleNet board only, if LoRa VDD / RA_VDD is disconnected

### LoRaWAN Connection Test

Used to check if the MoleNet v7.1 board can send data to TTN using:

* ABP
* OTAA

The LoRaWAN test sends:

`hello`

to TTN.
