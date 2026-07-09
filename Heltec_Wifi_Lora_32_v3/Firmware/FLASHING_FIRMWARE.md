# Firmware for Heltec WiFi LoRa 32 V3 Board

The Heltec WiFi LoRa 32 V3 board is equipped with an ESP32-S3 microcontroller. To program the board, you can download the generic MicroPython firmware binary from the official MicroPython website. The website also provides additional instructions for reference.

## Prerequisites

1. Before flashing the firmware, you need to ensure that the necessary drivers for USB to UART communication are installed on your Windows system. You can download the drivers from the Silicon Labs website. [Download](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads).

2. Python 3.7 or higher. [Download](https://www.python.org/downloads/)

3. esptool.py installed.
    ```
    pip3 install esptool
    ```

4. `.bin` file for the firmware. [Download](https://micropython.org/download/ESP32_GENERIC_S3/)

## Flashing the Generic MicroPython Firmware

To flash the generic MicroPython firmware onto the Heltec WiFi LoRa 32 V3 board, follow these steps:

1. Download the MicroPython firmware from the provided link

2. Connect the Heltec WiFi LoRa 32 V3 board to your Windows system using a USB cable.

3. Install the USB to UART drivers downloaded from the Silicon Labs website. Follow the installation instructions provided with the drivers.

4. Open a terminal or command prompt on your computer and navigate to the directory where you downloaded the MicroPython firmware.

5. Put the board into bootloader mode. This is usually done by pressing and holding the BOOT button while pressing the RESET button on the board, and then releasing the RESET button first followed by the BOOT button.

6. Erase the existing flash in the device
   ```
   esptool.py --chip esp32s3 --port <COM_PORT> erase_flash
   ```

7. Execute the following command in the terminal or command prompt to flash the firmware onto the board:
   ```
   esptool.py --chip esp32s3 --port <COM_PORT> write_flash 0 <path_to_firmware_file>.bin
   ```

   Replace `<COM_PORT>` with the appropriate COM port assigned to the board on your Windows system. [Guide to finding COM_PORT](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/establish-serial-connection.html#:~:text=Check%20Port%20on%20Windows)
   
   Replace `<path_to_firmware_file>` with the actual path to the downloaded firmware file.

8. Wait for the flashing process to complete. Once it's done, the MicroPython firmware will be successfully flashed onto the board.