Setup
=====

0. Flash the firmware. To do this, go `../../../tools/MoleWarden/` and the version directory of your node. Setup a python `venv` and run `runme.sh` (adjust the USB device setting in `runme.sh` if necessary).
1. Copy all files from this directory and its subdirectory to the device (Molenet). Run `copy-all.sh` from this directory to do so.
2. Register the device as a 'new device' on TTN.
3. Edit the `lib/config_OTAA.py` file and populate it with the data from TTN. It is best to do this using Thonny.
4. Edit `main.py` if necessary to adjust timings, add/remove sensors, or make other program improvements (e.g., using a loop instead of deep sleep).
5. Run the script from the `main.py` view in Thonny.
6. First, check the Thonny output to see if data is being sent; then check TTN to see if data is being received.
7. Switch the payload formatter in TTN to JavaScript and copy the code from `payload_formater.js` (from the TTN directory) into it.
8. Define a webhook (e.g., Google Docs), start a remote MQTT client, or set up another method to utilize the data.
9. Run the device continuously on battery power.

Errors 
------

### Connection canot be established 

1. Maybe you have to delete the internal configuration file for OTAA. See `tnn.md` for additional information.

~~~shell
python ../pyboard.py -d /dev/tty.usbmodem* -f ls
python ../pyboard.py -d /dev/tty.usbmodem1201 -f rm .config.cfg
~~~

2. Maybe you do not have a LoRaWan gateway in the neighborhood. Borrow one, buy one or go to a place where one is reachable.

