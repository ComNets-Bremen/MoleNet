# Documentation

This directory contains the documentation of MoleNet. For the previous
versions, please refer to the [ATMEGA](ATMEGA) or [stm32](stm32) directory, respectively.


# The Hardware

MoleNet 6.1 with all available components assembled. Click on the image for a
high resolution version.

[![The MoleNet 6.3 hardware](/images/MoleNet_6.3_lr.jpg)](/images/MoleNet_6.3.jpg)

## Available Components

- LoRa via
  - [SX1276](https://www.semtech.com/products/wireless-rf/lora-connect/sx1276) [Ra-01H](https://docs.ai-thinker.com/en/Ra-01H/) module till MoleNet 6.3
  - [SX1262](https://www.semtech.com/products/wireless-rf/lora-connect/sx1262) [RA-01SH](https://docs.ai-thinker.com/en/Ra-01SH/index.html) module since MoleNet 7.0
- BME280
- SD-card holder
- qwiic for external I2C components
- LEDs
- SDI-12 for environmental sensors
- Additional pins (analog and digital)

## Components and their Connections

MoleNet contains various different on-board parts. The following tables list
the connections and other relevant information for the major parts. For further
details, refer to [schematics of the corresponding board](../PCB-Layouts/).

- [Table MoleNet 7.0](hw_doc/7.0.md)
- [Table MoleNet 6.3](hw_doc/6.3.md)
- [Table MoleNet 6.2](hw_doc/6.2.md)

**Please check also the [CHANGELOG](../CHANGELOG.md) for further changes and issues**


## Pins on the ESP32

For the usage of the pins, please refer to the hardware section in this
document or the schematics of the corresponding versions available in [the PCB-Layouts directory](../PCB-Layouts/).

# Setup using Arduino

1) Install **Arduino IDE** -> [arduino.cc](https://www.arduino.cc/en/software/)
2) Install the **esp32** package by Espressif via the **Boards Manager** in the IDE
3) Select the **ESP32S3 Dev Module** as the board
4) Select the corresponding USB port
5) Set USB CDC On Boot: Enabled
6) Set USB Mode: USB-OTG (Tiny USB)

**⚠️ Attention: Different ports!**

Different ports are created at various times when the MoleNet platform is connected to the computer. One port is to flash the firmware, while the second is to access the MoleNet Platform’s serial port. The first is the default after a reset. The second is usually entered if the boot button is pressed during reset or when powering up the board.

Usually, you have to setup the board twice according to the settings above. Be
aware that the port identifier can change depending on your operating system.

# Setup using MicroPython

Please use the documentation for the ESP32 available at
[micropython.org](https://micropython.org/download/ESP32_GENERIC_S3/).
