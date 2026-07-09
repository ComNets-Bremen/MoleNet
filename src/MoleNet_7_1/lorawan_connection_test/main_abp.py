from machine import SoftSPI, Pin
from SX1262 import Transceiver
from LoRaWAN import LoRaWAN
from config_ABP import NwkSKey, AppSKey, DevAddr, DevEUI
import EU868
import utime

# MoleNet v7.1 SX1262 pin mapping
LORA_SCK = 14
LORA_MOSI = 47
LORA_MISO = 21
LORA_CS = 48
LORA_RST = 15
LORA_BUSY = 39
LORA_DIO1 = 46

SEND_POWER = 17
SEND_SF = 7
SEND_INTERVAL_SECONDS = 60

print()
print("MoleNet v7.1 LoRaWAN ABP connection test")
print("Sending 'hello' every", SEND_INTERVAL_SECONDS, "seconds")

utime.sleep_ms(500)

try:
    spi = SoftSPI(
        baudrate=100000,
        polarity=0,
        phase=0,
        sck=Pin(LORA_SCK),
        mosi=Pin(LORA_MOSI),
        miso=Pin(LORA_MISO)
    )

    cs = Pin(LORA_CS, Pin.OUT, value=1)
    rst = Pin(LORA_RST, Pin.OUT, value=1)
    busy = Pin(LORA_BUSY, Pin.IN)
    dio1 = Pin(LORA_DIO1, Pin.IN)

    sx = Transceiver(spi, cs, rst, busy, dio1)
    lw = LoRaWAN(sx, EU868.FREQS)

    lw.setup_abp(NwkSKey, AppSKey, DevAddr, DevEUI)

    print("LoRaWAN ready")

except Exception as e:
    print("LoRa init/setup error:", e)
    raise

while True:
    try:
        payload = "hello"
        lw.send(payload, power=SEND_POWER, sf=SEND_SF)
        print("Sent:", payload)

    except Exception as e:
        print("Send error:", e)

    utime.sleep(SEND_INTERVAL_SECONDS)