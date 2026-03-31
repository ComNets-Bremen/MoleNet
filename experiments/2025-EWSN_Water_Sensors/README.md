# Water Sensors

**Jens Dede, 2025** [jd@comnets.uni-bremen.de](mailto:jd@comnets.uni-bremen.de)

This repository contains the source code for the demo accompanying the paper:  
**"Slippery Signals: Investigating Sensor Crosstalk in Water Measurements"** *Published at EWSN 2025 in Leuven.*

---

## Overview

This project reads data from multiple sensors (electrical conductivity, dissolved oxygen, pH value) using a **MoleNet board** (with a custom adaptation board). The readings are transmitted via a serial connection to a desktop application that provides live updates.

### Objective
The primary goal is to demonstrate the effects of **duty cycling** on sensors: How are different sensors affected when placed simultaneously in a conductive liquid like water?

---

## Technical Details

This code has been tested on **MoleNet 6.3** using the MicroPython firmware:  
`ESP32_GENERIC_S3-20250911-v1.26.1.bin`

### Directory Structure

* `app/`: Contains the firmware logic. 
    * Upload the contents of `app/src` to the MoleNet board. 
    * It processes sensor data and outputs it as a JSON object to the serial line.
    * Includes additional convenience scripts for setup and testing.
* `readout/`: The PC-side application used to visualize the incoming data from the board.
* `2025-09-10_schematic.pdf`: The hardware schematic. 

> [!IMPORTANT]
> **Note on Hardware:** Two circuit versions exist with slightly different pinouts. If in doubt, please refer to the source code for the definitive pin assignments.
