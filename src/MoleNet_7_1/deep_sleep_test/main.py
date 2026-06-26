from machine import SoftSPI, Pin
from SX1262 import Transceiver
from LoRaWAN import LoRaWAN
from config_OTAA import DevEUI, JoinEUI, AppKey
import EU868
import machine
import esp32
import utime
import struct

# --------------------------------------------------
# MoleNet v7.1 Board + LoRa Deep Sleep Test
# --------------------------------------------------

SLEEP_MINUTES = 60
SLEEP_MS = SLEEP_MINUTES * 60 * 1000

# MoleNet v7.1 SX1262 pin mapping
LORA_SCK = 14
LORA_MOSI = 47
LORA_MISO = 21
LORA_CS = 48
LORA_RST = 15
LORA_BUSY = 39
LORA_DIO1 = 46

# Board LEDs
LED1_PIN = 2
LED2_PIN = 38

JOIN_SF = 7
SEND_SF = 7
SEND_POWER = 17

# Set True only if a fresh OTAA join is needed every boot
FORCE_OTAA_JOIN_EVERY_BOOT = False


def release_pin_holds():
    try:
        esp32.gpio_deep_sleep_hold(False)
        print("Released deep sleep pin holds")
    except Exception as e:
        print("Hold release error:", e)

    pins = [
        LORA_CS, LORA_RST, LORA_SCK, LORA_MOSI,
        LORA_MISO, LORA_BUSY, LORA_DIO1,
        LED1_PIN, LED2_PIN
    ]

    for pin_no in pins:
        try:
            Pin(pin_no, Pin.IN, hold=False)
        except Exception:
            pass


def disable_wifi_ble():
    try:
        import network
        network.WLAN(network.STA_IF).active(False)
        network.WLAN(network.AP_IF).active(False)
        print("WiFi disabled")
    except Exception as e:
        print("WiFi disable error:", e)

    try:
        import bluetooth
        bluetooth.BLE().active(False)
        print("BLE disabled")
    except Exception as e:
        print("BLE disable error:", e)


def leds_off():
    try:
        Pin(LED1_PIN, Pin.OUT, value=0)
        Pin(LED2_PIN, Pin.OUT, value=0)
        print("LEDs off")
    except Exception as e:
        print("LED off error:", e)
        
def wait_lora_not_busy(timeout_ms=1000):
    busy = Pin(LORA_BUSY, Pin.IN)
    start = utime.ticks_ms()

    while busy.value() == 1:
        if utime.ticks_diff(utime.ticks_ms(), start) > timeout_ms:
            print("LoRa BUSY wait timeout")
            break
        utime.sleep_ms(10)

    print("LoRa BUSY is LOW")

def lora_sleep_and_prepare_pins(sx):
    try:
        if sx is not None:
            sx.sleep()
            print("SX1262 sleep() called")
            
            # Wait until SX1262 finishes processing the sleep command
            wait_lora_not_busy(timeout_ms=1000)
            utime.sleep_ms(50)
    except Exception as e:
        print("SX1262 sleep error:", e)

    try:
        Pin(LORA_CS, Pin.OUT, value=1, hold=True)
        Pin(LORA_RST, Pin.OUT, value=1, hold=True)
        Pin(LORA_SCK, Pin.OUT, value=0, hold=True)
        Pin(LORA_MOSI, Pin.OUT, value=0, hold=True)

        Pin(LORA_MISO, Pin.IN)
        Pin(LORA_BUSY, Pin.IN)
        Pin(LORA_DIO1, Pin.IN)

        print("LoRa pins prepared for deep sleep")
    except Exception as e:
        print("LoRa pin preparation error:", e)


def go_to_deep_sleep(sx):
    print("Preparing for deep sleep")

    lora_sleep_and_prepare_pins(sx)

    try:
        Pin(LED1_PIN, Pin.OUT, value=0, hold=True)
        Pin(LED2_PIN, Pin.OUT, value=0, hold=True)
    except Exception:
        pass

    try:
        esp32.gpio_deep_sleep_hold(True)
        print("Deep sleep holds enabled")
    except Exception as e:
        print("Deep sleep hold error:", e)

    print("Going to deep sleep for", SLEEP_MINUTES, "minutes")
    utime.sleep_ms(500)
    machine.deepsleep(SLEEP_MS)


print()
print("Booting MoleNet v7.1 LoRa deep sleep test")
print("Wake reason:", machine.wake_reason())
print("Sleep interval:", SLEEP_MINUTES, "minutes")

if machine.reset_cause() != machine.DEEPSLEEP_RESET:
    print("Physical reset or fresh boot. Waiting 1 second for Thonny...")
    utime.sleep_ms(1000)
else:
    print("Deep sleep wakeup. Skipping boot delay...")

release_pin_holds()
disable_wifi_ble()
leds_off()

# Boot counter stored in RTC memory
rtc = machine.RTC()
rtc_data = rtc.memory()

if len(rtc_data) >= 4:
    boot_count = struct.unpack("<I", rtc_data[:4])[0]
else:
    boot_count = 0

boot_count += 1
rtc.memory(struct.pack("<I", boot_count))

print("Boot count:", boot_count)

sx = None
lw = None

try:
    print("Initializing SX1262 LoRa")

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

except Exception as e:
    print("LoRa init error:", e)
    go_to_deep_sleep(sx)


try:
    if FORCE_OTAA_JOIN_EVERY_BOOT:
        print("Forcing fresh OTAA join")
        lw.joined = False
        lw.join_otaa(AppKey, JoinEUI, DevEUI, retries=5, sf=JOIN_SF)

    elif not lw.joined:
        print("No saved LoRaWAN session. Trying OTAA join")
        lw.join_otaa(AppKey, JoinEUI, DevEUI, retries=5, sf=JOIN_SF)

    else:
        print("Using saved LoRaWAN session")

    print("Joined =", lw.joined)

    if lw.joined:
        payload = struct.pack("<f", float(boot_count))

        print("Payload length:", len(payload), "bytes")
        print("Sending boot count to TTN")

        lw.send(payload, power=SEND_POWER, sf=SEND_SF)

        print("Payload sent successfully")

    else:
        print("Join failed. Sleeping anyway")

except Exception as e:
    print("LoRaWAN send error:", e)


go_to_deep_sleep(sx)
