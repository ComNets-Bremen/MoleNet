import time

class EC(object):
    # Calibration values
    y_intercept_ec = -24.78009160168432
    slope_ec = 34.93918741731503


    def __init__(self, config, temp_c=25.0):
        self.config = config
        self.temp_c = temp_c
        print(f"{__name__}: Init done")


    def on(self):
        self.config["vcc"].on()
        self.config["gnd"].on()

    def off(self):
        self.config["vcc"].off()
        self.config["gnd"].off()


    def get_avg_mv(self):
        raw_vals = []
        for i in range(10):
            raw_vals.append(self.config["adc"].read_u16())
            time.sleep(0.01)

        raw_val = sum(raw_vals) / len(raw_vals)
        return self.config["convert"](raw_val)


    def get_reading(self):
        ec_value = (self.get_avg_mv() - self.y_intercept_ec)/self.slope_ec
        return ec_value



