import time

class DO(object):
    # TODO: change the calibration process
    VREF = 3300
    ADC_RES = 4095

    # Calibration values
    CAL1_T = 37 # °C
    raw1 =  1340
    CAL1_V = raw1 * VREF/ ADC_RES  # mV

    CAL2_T =  21 # °C
    raw2 =  850
    CAL2_V = raw2 * VREF/ ADC_RES # mV

    # DO saturation table in mg/l for 0–40 °C (from manufacturer data)
    DO_TABLE = [
        14.460, 14.220, 13.820, 13.440, 13.090, 12.740, 12.420, 12.110, 11.810, 11.530,
        11.260, 11.010, 10.770, 10.530, 10.300, 10.080, 9.860, 9.660, 9.460, 9.270,
        9.080, 8.900, 8.730, 8.570, 8.410, 8.250, 8.110, 7.960, 7.820, 7.690,
        7.560, 7.430, 7.300, 7.180, 7.070, 6.950, 6.840, 6.730, 6.630, 6.530, 6.410
    ]


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
        v_sat_do =  ((self.temp_c - self.CAL2_T) * (self.CAL1_V - self.CAL2_V) / (self.CAL1_T - self.CAL2_T)) + self.CAL2_V # from manufacturer data
        do_saturation = self.DO_TABLE[int(round(self.temp_c))]
        do_mg_l = self.get_avg_mv() * do_saturation / v_sat_do # from manufacturer data
        do_sat_percent = do_mg_l/do_saturation * 100
        return do_sat_percent



