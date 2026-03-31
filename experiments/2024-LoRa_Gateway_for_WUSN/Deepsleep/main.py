import pycom
import RFM69
from RFM69registers import *
import time
from network import LoRa
import machine
import socket
import ubinascii
import struct

#lower power consumption
pycom.heartbeat(False)
pycom.rgbled(0x000000)
pycom.wifi_on_boot(False)

###########VARS#################
receivedData =[]

###########SETUP RFM################
if machine.wake_reason()[0] == 0: #If the LoPy just got startet, configure RFM69 and go to deepsleep for power saving
    print("Gerade hochgefahren, führe Setup durch")
    rfm = RFM69.RFM69(RF69_433MHZ, 1, 42, False)
    results = rfm.readAllRegs()
    for result in results:
        print(result)
    rfm.rcCalibration()
    rfm.setHighPower(True)
    rfm.encrypt("sampleEncryptKey")
    rfm.receiveBegin()
    f = open('/flash/data.csv', 'w')
    f.write('')
    f.close()
    print("Gute Nacht")
    machine.pin_deepsleep_wakeup(['P9'], machine.WAKEUP_ANY_HIGH)
    machine.deepsleep(200000)

elif machine.wake_reason()[0] == 2:
    print("Timer interrupt")
elif machine.wake_reason()[0] == 1: #If the LoPy woke up from deepsleep, define the class, but don't reset the RFM chip
    print("Pin Interrupt")
    rfm = RFM69.RFM69(RF69_433MHZ, 1, 42, False, wakeup = True)
    rfm.receiveMessage()
    receivedData = (["".join([chr(letter) for letter in rfm.DATA]), rfm.SENDERID, rfm.RSSI])
    if rfm.ACKRequested():
        rfm.sendACK()

    # #####UNGETESTET##########
    # f = open('/flash/data.csv', 'a')
    # oldData = f.readall()
    # if oldData == '':
    #     f.write(currentData)
    #     f.close()
    #     #put RFM69 in receiving Mode and put it back to deepsleep
    #     rfm.receiveBegin()
    #     print("Gute Nacht")
    #     machine.pin_deepsleep_wakeup(['P9'], machine.WAKEUP_ANY_HIGH)
    #     machine.deepsleep(200000)
    # elif len(oldData.split(';')) < 5:
    #     f.write(';' + str(currentData))
    #     f.close()
    #     #put RFM69 in receiving Mode and put it back to deepsleep
    #     rfm.receiveBegin()
    #     print("Gute Nacht")
    #     machine.pin_deepsleep_wakeup(['P9'], machine.WAKEUP_ANY_HIGH)
    #     machine.deepsleep(200000)
    # else:
    #     receivedData = oldData.split(';').append(currentData)
    #     f.close()
    #     f.open('/flash/data.csv', 'a')
    #     f.write('')
    #     f.close()


###########SETUP LORA###############
# Initialise LoRa in LORAWAN mode.
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# create an OTAA authentication parameters
app_eui = ubinascii.unhexlify('70B3D57ED001A20A')
app_key = ubinascii.unhexlify('10DC7520366D57071EB4B4AC23968E39')

# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(2.5)
    print('Not yet joined...')

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
# selecting confirmed type of messages
s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
s.setblocking(True)

print("SENDING")
# send receivedData
try:
    s.send(str(receivedData))
except:
    print("Senden fehlgeschlagen")

# make the socket non-blocking
# (because if there's no data received it will block forever...)
s.setblocking(False)

#put RFM69 in receiving Mode and put it back to deepsleep
rfm.receiveBegin()
print("Gute Nacht")
machine.pin_deepsleep_wakeup(['P9'], machine.WAKEUP_ANY_HIGH)
machine.deepsleep(200000)
