import time

class PH(object):
    # Calibration values
    y_intercept_ph = 605.35798
    slope_ph = -40.70071466666667


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
        ph_value = (self.get_avg_mv() - self.y_intercept_ph)/self.slope_ph
        return ph_value + 12 #TODO do a proper calibration. 10 is just a guess. Remove after interecept and slope were changed!



