MoleNet Test: Micropython
=========================

Quick and dirty test for main functionality of new boards.

Jens Dede <jd@comnets.uni-bremen.de>

Prerequisites and Automatic Testing
-----------------------------------

Perform the following steps in this directory:

- Ideally, you use a virtual environment: `python3 -m venv venv`
- Activate the venv: `. ./venv/bin/activate`
- Install the requirements: `pip install -r requirements.txt`
- Run the script: `runall.sh <PORTNAME>` where the `<PORTNAME>` is the name of
  the serial port according to your OS (for example, `/dev/ttyACM0` on Linux.

This `runall.sh` downloads and installs some additional files (if they do not
exist):
- pyboard.py from https://raw.githubusercontent.com/micropython/micropython/refs/heads/master/tools/pyboard.py
- MicroPython VM from
  https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20250415-v1.25.0.bin)

Manual Board Test
-----------------

We assume the board is connected to `/dev/ttyACM0`
- Set the board to boot mode (boot button + reset)
- Erase board: `esptool.py --port /dev/ttyACM0 erase_flash`
- Install VM: `esptool.py --port /dev/ttyACM0 --baud 460800 write_flash 0
  ESP32_GENERIC_S3-20250415-v1.25.0.bin`
- Reset board (reset button)
- Upload example code: `./pyboard.py -d /dev/ttyACM0 -f cp src/main.py
  :main.py`
- Create lib dir: `./pyboard.py -d /dev/ttyACM0 -f mkdir lib`
- Upload BME280 lib: `./pyboard.py -d /dev/ttyACM0 -f cp src/lib/*
  :lib/`
- Connect to the serial port `screen /dev/ttyACM0` to check the output and
  restart the device using `ctrl-d`
- Test the next device

Example output
--------------
    *** Testing board with ID aabbccddeeff ***
    ## Step 1: Test LED
    ## Step 1: Done
    ## Step 2: Test BME280
    Temperature: 25.57C
    Humidity   : 40.44%
    Pressure   : 1024.80hPa
    ## Step 2: Done
    ## Step 3: Test WiFi
    WiFis: Uni-Bremen, eduroam
    ## Step 3: Done

FAQ
---

### How to kill screen?

- CTRL-A, k, y

Further readings
----------------

- pyboard docs:
  https://docs.micropython.org/en/latest/reference/pyboard.py.html
- esptool docs:
  https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html
- screen docs: https://www.gnu.org/software/screen/manual/screen.html
- Driver for SX LoRa transceiver: https://github.com/B00mb0x/LoRaWAN-Stack-for-Micropython

