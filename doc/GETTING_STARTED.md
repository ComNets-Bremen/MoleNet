# Getting Started with MoleNet

Welcome to MoleNet! This guide helps you identify your MoleNet board version and find the corresponding software, hardware documentation, experiments, schematics, and setup resources.

---

## Step 1: Identify Your Hardware Version

Look at the version number printed on the green silkscreen of your MoleNet board.

Examples include:

* `MoleNet v7.1`
* `MoleNet v7.0`
* `MoleNet v6.3`
* `MoleNet v6.2`
* `MoleNet v6.1`
* `MoleNet v6.0`

Use this version number to select the correct software and hardware documentation in the following sections.

---

## Step 2: Access the MoleNet Code

The MoleNet source code and documentation are available in this GitHub repository.

You can access the repository in the following ways:

* Browse the files directly on GitHub.
* Download the repository as a ZIP file.
* Clone the repository using Git.

If you are new to Git and GitHub, the following resources explain how to clone repositories, work with branches, commit changes, and push code:

* [GitHub Git Handbook](https://docs.github.com/en/get-started/start-your-journey/git-handbook): A short introduction to Git concepts and commands.
* [Cloning a GitHub Repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository): Instructions for cloning a repository to your computer.
* [Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials): Detailed tutorials about Git workflows and collaboration.

---

## Step 3: Find the Correct Software and Hardware Documentation

Go to the [`src`](../src) directory and select the appropriate software folder for your board version.

> Before assigning GPIO pins in your code, check the hardware documentation for your board version. Some pins are already connected to onboard components and may not be available for general use.

### MoleNet v7.1

* MCU: ESP32-S3
* LoRa chip: SX1262 / RA-01SH
* Software folder: [`src/MoleNet_7_1`](../src/MoleNet_7_1)
* Hardware documentation: [`hw_doc/7.1.md`](./hw_doc/7.1.md)
* Contains: MicroPython board test scripts, LoRaWAN setup files, power-measurement files, drivers, and setup guides.

### MoleNet v7.0

* MCU: ESP32-S3
* LoRa chip: SX1262 / RA-01SH
* Software folder: [`src/MoleNet_7.0`](../src/MoleNet_7.0)
* Hardware documentation: [`hw_doc/7.0.md`](./hw_doc/7.0.md)
* Contains: MicroPython test scripts and required drivers.

### MoleNet v6.1, v6.2, and v6.3

* MCU: ESP32-S3
* LoRa chip: SX1276 / RA-01H
* Software folder: [`src/MoleNet_6.1`](../src/MoleNet_6.1)

These board versions use similar software. However, the LoRa reset pin must be configured according to the board version.

| Board version | `LORA_RST` | Hardware documentation                                    |
| ------------- | ---------: | --------------------------------------------------------- |
| MoleNet v6.1  |       `45` | No separate hardware Markdown file is currently available |
| MoleNet v6.2  |       `55` | [`hw_doc/6.2.md`](./hw_doc/6.2.md)                        |
| MoleNet v6.3  |       `15` | [`hw_doc/6.3.md`](./hw_doc/6.3.md)                        |

Before using additional GPIO pins, verify their availability using the corresponding hardware documentation, PCB layout, or schematic.

### MoleNet v6.0

* MCU: ESP32-S3
* LoRa chip: SX1276 / RA-01H
* Software folder: [`src/MoleNet_6.0`](../src/MoleNet_6.0)
* Contains: Arduino and MicroPython test code.
* Hardware documentation: No separate hardware Markdown file is currently available. See the [`PCB-Layouts`](../PCB-Layouts) directory for schematics and PCB files.

### STM32-Based Boards

* Setup and flashing instructions: [`stm32`](./stm32)

Follow the documentation in this folder to configure and flash STM32-based MoleNet boards.

### Legacy ATMEGA-Based Boards

* MCU: ATmega328P
* Radio: RFM69
* Software folder: [`src/ATMEGA-based`](../src/ATMEGA-based)
* Documentation: [`ATMEGA`](./ATMEGA)

---

## Step 4: Find General Documentation

The [`doc`](./) directory contains the general MoleNet documentation.

Useful folders and files include:

* [`FAQ.md`](./FAQ.md): General questions and answers about MoleNet design and usage.
* [`hw_doc`](./hw_doc): Hardware documentation and pin mappings for different MoleNet versions.
* [`stm32`](./stm32): STM32 board setup and flashing documentation.
* [`ATMEGA`](./ATMEGA): Documentation for legacy ATMEGA-based boards.

---

## Step 5: Find Experiments and Measurements

Go to the [`experiments`](../experiments) directory for experimental setups, results, and measurement data.

Examples include:

* [`2026-power-consumption-and-voltage-measurement`](../experiments/2026-power-consumption-and-voltage-measurement): Power-consumption and voltage-measurement results.
* [`2025-EWSN_Water_Sensors`](../experiments/2025-EWSN_Water_Sensors): Water-sensor experiments.
* [`2024-LoRa_Gateway_for_WUSN`](../experiments/2024-LoRa_Gateway_for_WUSN): LoRa gateway setup and related files.
* [`data_rangetest`](../experiments/data_rangetest): Wireless range-test data.

---

## Step 6: Find Schematics, PCB Files, and Enclosures

The following directories contain hardware design files and mechanical components:

* [`PCB-Layouts`](../PCB-Layouts): Schematics and KiCad PCB design files.
* [`PCB-Enclosures`](../PCB-Enclosures): 3D-printable cases, holders, and stands.
* [`Auxiliary Boards`](../Auxiliary%20Boards): Additional hardware boards and supporting circuit designs.

Use the PCB schematics and hardware documentation to verify pin connections before modifying the software or connecting additional components.

---

## Step 7: Flashing and Maintenance Tools

For ESP32 board flashing, firmware installation, and hardware testing, use:

* [`tools/MoleWarden`](../tools/MoleWarden): MoleNet tools for erasing, flashing, configuring, and testing supported boards.

Follow the README file inside the `MoleWarden` folder for installation and usage instructions.

For direct command-line flashing of Espressif devices, see:

* [esptool Documentation](https://docs.espressif.com/projects/esptool/en/latest/): Official documentation for erasing and flashing ESP32 devices.

---

## Step 8: MicroPython Setup and External Documentation

The official MicroPython documentation contains instructions for installing or updating MicroPython firmware, uploading code, accessing the REPL, and using ESP32 hardware peripherals.

### MicroPython Documentation

* [MicroPython Official Documentation](https://docs.micropython.org/): General MicroPython documentation and library references.
* [Getting Started with MicroPython on ESP32](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html): Instructions for installing firmware, flashing an ESP32 board, accessing the serial REPL, and troubleshooting.
* [MicroPython ESP32 Quick Reference](https://docs.micropython.org/en/latest/esp32/quickref.html): Examples for GPIO, I²C, SPI, UART, timers, deep sleep, and other ESP32 features.
* [`mpremote` Documentation](https://docs.micropython.org/en/latest/reference/mpremote.html): Command-line tool for connecting to MicroPython devices, uploading files, and running scripts.

### Optional IDE

[Thonny IDE](https://thonny.org/) can be used to:

* Connect to a MicroPython board.
* Access the MicroPython REPL.
* Upload and download files.
* Edit and run Python scripts directly on the board.

The MoleNet-specific flashing and testing procedures provided in this repository should be followed where available.

---

## Need Help?

If you are unsure which software folder, hardware document, or flashing procedure applies to your board:

1. Confirm the version printed on the board.
2. Check the corresponding hardware documentation.
3. Check the README file inside the relevant software folder.
4. Review the [`FAQ`](./FAQ.md).
5. Open an issue in the MoleNet GitHub repository if the required information is missing.
