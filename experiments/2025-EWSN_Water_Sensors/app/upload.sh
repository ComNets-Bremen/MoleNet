#!/usr/bin/env bash
# This code requires pyboard.py -> https://docs.micropython.org/en/latest/reference/pyboard.py.html

PORT=/dev/ttyACM0

./pyboard.py -d $PORT -f cp src/main.py :main.py
./pyboard.py -d $PORT -f mkdir lib
./pyboard.py -d $PORT -f cp src/lib/BME280.py :lib/BME280.py
./pyboard.py -d $PORT -f cp src/lib/ec_sensor.py :lib/ec_sensor.py
./pyboard.py -d $PORT -f cp src/lib/do_sensor.py :lib/do_sensor.py
./pyboard.py -d $PORT -f cp src/lib/ph_sensor.py :lib/ph_sensor.py
./pyboard.py -d $PORT -f cp src/lib/bme_sensor.py :lib/bme_sensor.py

screen $PORT
