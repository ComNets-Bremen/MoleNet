Setup an new or old device for TTN
==================================

Activation
----------

See (End Device Activation)[https://www.thethingsnetwork.org/docs/lorawan/end-device-activation/] in (The Things Network)[https://www.thethingsnetwork.org/].

### OTAA (Over the air activation)

See Appendix A of Danil Helms' masterthesis `Masterthesis_LoRaWAN-Stack_Helms_Daniel_4224385.pdf`.

### ABP (Activation By Personalization)

See MoleNet v7.1 LoRaWAN Setup `MoleNet v7.1 LoRaWAN Setup.pdf`.

When somethig does not work
---------------------------

When you see the message "Ups, i have to join to LoRWAN (OTAA) again?"

```sh
    activate # activate python venv in the directory where you find pyboard.py
    python pyboard.py -d /dev/tty.usbmodem* -f ls # Does .confog.cfg exist?
    python pyboard.py -d /dev/tty.usbmodem* -f rm .config.cfg  # delete it
    python pyboard.py -d /dev/tty.usbmodem* -f ls # Was it removed?
```

check the parameters in lib/config_OTAA.py!

When the device has moved to another Application: change the AppKey to the AppKey of the new application

Register Webhooks
-----------------

1. Go to webhooks on the application in ttn. 
2. select "+Add Webhook"
3. select "Custom Webhook"
4. Fill out som parameters in the form:
- Webhook ID: google-sheets
- Base URL: the Apps Script /exec URL from the Google Docs Extensions "Apps Script" Deploy action.
- Uplink message: Enable the select box but leave the text field empty

See also Part C in MoleNet v7.1 LoRaWAN Setup `LoRaWAN/MoleNet v7.1 LoRaWAN Setup.pdf` on page 5ff.

When something went wrong ttn does not help with finding the error. The first step is to use 'Postman'. Try on Postman to send a 'Post' message with

https://script.google.com/macros/s/AKfycbwxn_xvh74p6UPbFNSucKHgF2fEvTc__FJs00v9doGHmX6J3kDd0usndNf7NtM3uwMi/exec?contents={"device_id":"my device"} 

When you get an error 403 Forbidden go to the Google Apps Script and select Deploy/Test deployment. Call the url in a separate window and give access to the data. Now Postman should work with a get (info message) and as well a post method (probably status error because the JSON content is not correct).
