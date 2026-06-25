

\# LoRaWAN Connection Test



This folder contains minimal LoRaWAN connection test scripts for the MoleNet v7.1 board with the onboard RA-01SH / SX1262 LoRa module.



\## Setup Instructions



For the complete setup steps, follow the \*\*MoleNet v7.1 LoRaWAN Setup Guide PDF\*\* included in this folder.



The PDF explains how to:



\* connect the MoleNet v7.1 board to TTN

\* create the TTN application and device

\* create the required config file

\* upload files using Thonny

\* verify the payload in TTN Live Data



\## Test Files



\* `main\_abp.py`

&#x20; LoRaWAN ABP connection test



\* `main\_otaa.py`

&#x20; LoRaWAN OTAA connection test



Both scripts send:



`hello`



to TTN every 60 seconds.



\## Required Files



Upload the selected test script as `main.py` together with the required library files from the `lib/` folder.



For ABP, use:



\* `config\_ABP.py`



For OTAA, use:



\* `config\_OTAA.py`



\## Notes



\* Use only one test script at a time.

\* Keep the LoRa antenna connected.

\* No sensors are required.

\* These scripts only test LoRaWAN connection.



