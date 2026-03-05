import time

def get_bme_start_dict(bme):
    if bme is None:
        print("No BME280")
    sensor_dict = dict()

    try:
        sensor_dict["BME280"] = {
                "name"              : "BME280",
                "temperature"       : bme.read_temperature() / 100.0,
                "temperature_unit"  : "C",
                "humidity"          : bme.read_humidity() // 1024,
                "humidity_unit"     : "%",
                "pressure"          : (bme.read_pressure() // 256) / 100.0,
                "pressure_unit"     : "hPa",
                "time"              : time.time(),
                }
    except Exception as e:
        print("BME error. Device disconnected?", e)

    return sensor_dict
