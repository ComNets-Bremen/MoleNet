# Getting Started with MoleNet

Welcome to MoleNet. This guide helps you find the correct resources, software, and hardware files based on your MoleNet board version.

---

## Step 1: Identify Your Hardware Version

Look at the version number printed on your MoleNet board's green silkscreen, for example: `MoleNet v7.1`, `MoleNet v7.0`, `MoleNet v6.3`, `MoleNet v6.2`, `MoleNet v6.1`, or `MoleNet v6.0`.

Use this version number to select the correct software and documentation in the next steps.

---

## Step 2: Find the Correct Software

Go to the [`src`](./src) directory and select the correct folder for your board version.

### MoleNet v7.1

- MCU: ESP32-S3
- LoRa chip: SX1262 / RA-01SH
- Folder: [`src/MoleNet_7_1`](./src/MoleNet_7_1)
- Contains: MicroPython board test scripts, LoRaWAN setup files, power measurement files, and setup guides.

### MoleNet v7.0

- MCU: ESP32-S3
- LoRa chip: SX1262 / RA-01SH
- Folder: [`src/MoleNet_7.0`](./src/MoleNet_7.0)
- Contains: MicroPython test scripts and required drivers.

### MoleNet v6.1, v6.2, and v6.3

- MCU: ESP32-S3
- LoRa chip: SX1276 / Ra-01H
- Folder: [`src/MoleNet_6.1`](./src/MoleNet_6.1)

These versions use similar software, but the LoRa reset pin is different:

| Board version | `LORA_RST` |
|---|---:|
| MoleNet v6.1 | `45` |
| MoleNet v6.2 | `55` |
| MoleNet v6.3 | `15` |

### MoleNet v6.0

- MCU: ESP32-S3
- LoRa chip: SX1276 / Ra-01H
- Folder: [`src/MoleNet_6.0`](./src/MoleNet_6.0)
- Contains: Arduino and MicroPython test code.

### STM32-based boards

- Folder: [`doc/stm32`](./doc/stm32)
- Use this folder for STM32 setup and flashing instructions.

### Legacy ATMEGA-based boards

- MCU: ATmega328P
- Radio: RFM69
- Folder: [`src/ATMEGA-based`](./src/ATMEGA-based)

---

## Step 3: Find Documentation

Go to the [`doc`](./doc) directory.

Useful folders and files:

- [`doc/FAQ.md`](./doc/FAQ.md): General questions and answers.
- [`doc/hw_doc`](./doc/hw_doc): Hardware pin mappings for different MoleNet versions.
- [`doc/stm32`](./doc/stm32): STM32 board documentation.
- [`doc/ATMEGA`](./doc/ATMEGA): Legacy ATMEGA board documentation.

---

## Step 4: Find Experiments and Measurements

Go to the [`experiments`](./experiments) directory.

Examples:

- [`2026-power-consumption-and-voltage-measurement`](./experiments/2026-power-consumption-and-voltage-measurement): Power and voltage measurement results.
- [`2025-EWSN_Water_Sensors`](./experiments/2025-EWSN_Water_Sensors): Water sensor experiments.
- [`2024-LoRa_Gateway_for_WUSN`](./experiments/2024-LoRa_Gateway_for_WUSN): LoRa gateway setup.
- [`data_rangetest`](./experiments/data_rangetest): Wireless range test data.

---

## Step 5: Find Schematics and Enclosures

- [`PCB-Layouts`](./PCB-Layouts): Schematics and KiCad PCB files.
- [`PCB-Enclosures`](./PCB-Enclosures): 3D-printable cases and stands.
- [`Auxiliary Boards`](./Auxiliary%20Boards): Additional hardware boards.

---

## Step 6: Maintenance and Flashing Tools

For ESP32 board flashing and testing, use:

[`tools/MoleWarden`](./tools/MoleWarden)

Follow the README in that folder to install and run the tool.
