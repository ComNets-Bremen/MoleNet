# MoleNet in Bavaria

**Alexander Förster, 2026** [axf@uni-bremen.de](mailto:axf@uni-bremen.de)

We installed two MoleNet nodes in Bad Kissingen at the Zukunftslabor. 

---

## Overview

This Repository contains all the configuration data and source code for the nodes, the TNN application and google sheets as one example data sink. The data is also available at [grafana.comnets.uni-bremen.de/](https://grafana.comnets.uni-bremen.de/)

## Directories and Files

### TTN (The Things Network)

- `payload_formater.js`: converts the binary data received from the nodes via LoRaWan to a json data structure which will be forwarded to the sinks.

### Node (Molenet Node Python Code)

Contains all python files which are on the nodes. The `main.py` program and
the `src` directory are used regulary. All other programs can be used for special purporses. Maybe started from Thonny or screen. 

- `main.py`: The default program. Sends all sensor data via LoRaWan to TTN and sleeps deeply in between for 60 seconds to 60 minutes (last command).
- `main_sdi12_terminal.py`: Used to communicate directly with the TEROS11/12 sensor to change it's configuration or get additional information from the sensor.
- `main_reader.py`: Almost the same as `main.py`, but will not go to deep sleep. Instead, it stays connected an the sensor data can be read conmtinously from the Thonny terminal.
- `main_lorawan_test_and_register_otaa.py`: Has to be used for register the node on TTN with OTAA (Over The Air Activation) instead of ABP (Activation By Personalization).
- `boot.py`: The boot script (called after startup and deepsleep). Normally empty.
- `.config.cfg`: A hidden file created and managed by `lib/LoRaWAN.py`. Contains keys after activation with TTN. Must be deleted before a new activation.
- `lib/config_OTAA.py`: The `lib` directory contains libraries for the sensors. Additionally, the file `config_OTAA.py` contains configuration information. 

### Google

The data from the two MoleNet nodes is stored on a [grafana instance](https://grafana.comnets.uni-bremen.de/)) and in a [google sheet](https://docs.google.com/spreadsheets/d/1am54Mm_Peyzo58hMVs5cYSzmUhW6zH7aOMFH0EJhQ6s/edit?usp=sharing). To add new data received from TTN a Google Apps Script `Code.gs` is required as extension to the spreadsheet.

- `Code.gs`: The script receives a json data block from TTN and converts it into a new row in the spreadsheet.

### Doc

- `setup.md`:
- `ttn.md`: 
- `teros.md`: How to configure a new TEROS11/12 soil sensor.

## Additional Information for ComNets members

The ComNets [KnowledeBase](https://kb.comnets.uni-bremen.de/books/mainzaun/page/deployment-bad-kissingen) and [NextCloud](https://nc.uni-bremen.de/index.php/apps/files/files/154767326?dir=/Bad%20Kissingen) contains additional information. 
