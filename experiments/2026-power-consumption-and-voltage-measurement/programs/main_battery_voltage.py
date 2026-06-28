from machine import Pin, ADC, deepsleep
import time

# --- Voltage Divider Pin Configuration and Update Time ---
MEAS_EN_PIN = 42    # controls MOSFET
ADC_PIN = 4         # measures voltage # Attention:  Not all PINS are valid for ADC!
SLEEP_TIME_MS = 60 * 60 * 1000  # 1 hour

# --- Resistor Setup and  Voltage Divider Factor Calculation ---
R1 = 47_070 # in ohms. Here 47.070kOhm for a 47k resistor.
R2 =  9_920 # in ohms. Here 09.920kOhm for a 10k resistor.
DIVIDER_FACTOR = (R1 + R2) / R2

# --- ADC Setup ---
adc = ADC(ADC_PIN) 
adc.atten(ADC.ATTN_11DB)  # up to ~3.3V, 3.6V is absolute maximum, the linear range is between 150mV and 2450mV when read with read_uv().
adc.width(ADC.WIDTH_12BIT)  

# callibration
# https://www.youtube.com/watch?v=4D8BNrNJ1KE&list=WL&index=164
# https://docs.micropython.org/en/latest/library/machine.ADC.html
# https://microcontrollerslab.com/esp32-esp8266-adc-micropython-measure-analog-readings/

# --- MOSFET Steuerung ---
meas_en = Pin(MEAS_EN_PIN, Pin.IN)  # AUS (hochohmig!)

# --- Funktion: Batteriespannung messen ---
# varianz-berechung mit shifted data nach https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
# Siehe auch https://de.wikipedia.org/wiki/Varianz_(Stochastik)

def read_battery():

    # MOSFET EIN
    meas_en.init(Pin.OUT)
    meas_en.value(1)

    time.sleep_ms(50)  # stabilisieren

    # mehrere Messungen mitteln
    samples = 10
    total = 0
    Ex = Ex2 = 0
    K = adc.read_uv()
    time.sleep_ms(2)
    for _ in range(samples):
        x = adc.read_uv()
        total += x
        Ex += x - K
        Ex2 += (x - K) ** 2        
        time.sleep_ms(2)

    uv = total / samples
    uv_variance = (Ex2 - Ex**2 / samples) / (samples - 1)
    uv_stddev = uv_variance**0.5
    # MOSFET AUS (wichtig!)
    meas_en.init(Pin.IN)

    # Spannung berechnen
    v_adc = uv / 1_000_000
    v_stddev = uv_stddev / 1_000_000
    v_bat = v_adc * DIVIDER_FACTOR
    v_bat_stddev = v_stddev * DIVIDER_FACTOR

    return v_bat, v_bat_stddev, v_adc, v_stddev


# --- Hauptprogramm ---
def main():

    voltage, voltage_stddev, v_adc, v_stddev = read_battery()

    # Hier könntest du senden (LoRa / TTN)
    print("Battery voltage:", voltage)

    # kurze Pause (optional)
    time.sleep_ms(100)

    # Deep Sleep
    deepsleep(SLEEP_TIME_MS)

def main_debug():

    print(f"Dangerous voltage limit: {3.6 * DIVIDER_FACTOR}V.")
    print(f"Normal voltage limit: {3.3 * DIVIDER_FACTOR}V.")
    print(f"Linear voltage range: min {0.15 * DIVIDER_FACTOR}V max {2.45 * DIVIDER_FACTOR}V.")

    
    while True:
        voltage ,voltage_stddev, v_adc, v_stddev = read_battery()

        # Hier könntest du senden (LoRa / TTN)
        print("Battery voltage:", voltage, "voltage stddev",voltage_stddev, "adc voltage:", v_adc, "adc stddev",v_stddev)
        if not 0.150 <= v_adc <= 2.450:
            print(f"Warning: value of {v_adc}V is out of the linear range of measurement! Should be between {0.150}V and {2.450}V.")

        # kurze Pause (optional)
        time.sleep_ms(100)
        
        time.sleep(10)
        
    # Deep Sleep
    deepsleep(SLEEP_TIME_MS)


# --- Start ---main()
#main()
main_debug()
