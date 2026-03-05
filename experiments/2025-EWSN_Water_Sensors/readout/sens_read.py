#!/usr/bin/env python3

##
# Read the data from the sensor via a serial connection
#
# Jens Dede, 2025 <jd@comnets.uni-bremen.de>
#

import numpy as np

from PIL import Image

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.image import FigureImage

import queue

from serial.tools import list_ports
from serial import Serial
from serial.threaded import ReaderThread, LineReader

import json
import pprint

DEBUG = False
# Background logo
BG_LOGO = "molly_mascot_digital.png"

q = queue.Queue()

# Sensor configuration: Which data shall we plot?
sensors = {
        "BME280" : {
            "title" : "BME280",
            "ax" : [
                {
                    "data_x_name" : "time",
                    "data_y_name" : "temperature",
                    "x_data" : [],
                    "y_data" : [],
                    "data_line": None,
                    "data_ax"  : None,
                    "xlabel": "Time",
                    "ylabel": "Temperature",
                    "linestyle" : ":",
                    "marker"    : "x",
                    "color"     : "r",
                },
                {
                    "data_x_name" : "time",
                    "data_y_name" : "humidity",
                    "x_data" : [],
                    "y_data" : [],
                    "data_line": None,
                    "data_ax"  : None,
                    "xlabel": "Time",
                    "ylabel": "Humidity",
                    "linestyle" : ":",
                    "marker"    : "x",
                    "color"     : "b",
                },

            ]
        },
        "sensor1" : {
            "title" : "pH-Value",
            "ax" : [
                {
                    "data_x_name" : "time",
                    "data_y_name" : "value",
                    "x_data" : [],
                    "y_data" : [],
                    "data_line": None,
                    "data_ax"  : None,
                    "xlabel": "Time",
                    "ylabel": "pH",
                    "linestyle" : ":",
                    "marker"    : "x",
                    "color"     : "b",
                },

            ]
        },
        "sensor2" : {
            "title" : "EC - Electrical Conductivity",
            "ax" : [
                {
                    "data_x_name" : "time",
                    "data_y_name" : "value",
                    "x_data" : [],
                    "y_data" : [],
                    "data_line": None,
                    "data_ax"  : None,
                    "xlabel": "Time",
                    "ylabel": "ms/cm",
                    "linestyle" : ":",
                    "marker"    : "x",
                    "color"     : "b",
                },

            ]
        },
        "sensor3" : {
            "title" : "DO - Dissolved Oxygen",
            "ax" : [
                {
                    "data_x_name" : "time",
                    "data_y_name" : "value",
                    "x_data" : [],
                    "y_data" : [],
                    "data_line": None,
                    "data_ax"  : None,
                    "xlabel": "Time",
                    "ylabel": "%",
                    "linestyle" : ":",
                    "marker"    : "x",
                    "color"     : "b",
                },

            ]
        },

    }


# Is the given data a json object?
def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True


# Redraw the canvas. Ensure the Logo stays nicely centered
def on_resize_event(event):
    add_watermark(fig, BG_LOGO)
    fig.tight_layout()
    fig.canvas.draw()

# Thread receiving the data and place it in the queue from where the UI thread
# reads the data for plotting
class SerialReaderProtocolLine(LineReader):
    port = None

    def connection_made(self, transport):
        """Called when reader thread is started"""
        print("Connected, ready to receive data...")

    def handle_line(self, line):
        """Called with snippets received from the serial port"""
        if line.startswith("#!") and is_json(line[2:]):
            json_data = json.loads(line[2:])
            q.put(json_data)
        else:
            if DEBUG:
                print(line)


# Update the data on the frame
def update_plot(frame):
    ret = []
    while not q.empty():
        item = q.get()
        pprint.pp(item)
        for sensor in sensors:
            for num_ax, sens_ax in enumerate(sensors[sensor]["ax"]):
                if sensor in item:
                    sensors[sensor]["ax"][num_ax]["x_data"].append(item[sensor][sensors[sensor]["ax"][num_ax]["data_x_name"]])
                    sensors[sensor]["ax"][num_ax]["y_data"].append(item[sensor][sensors[sensor]["ax"][num_ax]["data_y_name"]])
                    if len(sensors[sensor]["ax"][num_ax]["x_data"]) > 50:
                        sensors[sensor]["ax"][num_ax]["x_data"].pop(0)
                        sensors[sensor]["ax"][num_ax]["y_data"].pop(0)

                    sensors[sensor]["ax"][num_ax]["data_line"].set_data(
                            sensors[sensor]["ax"][num_ax]["x_data"],
                            sensors[sensor]["ax"][num_ax]["y_data"],
                        )
                    sensors[sensor]["ax"][num_ax]["data_ax"].relim()
                    sensors[sensor]["ax"][num_ax]["data_ax"].autoscale_view()
                    ret.append(sensors[sensor]["ax"][num_ax]["data_line"])

    return ret

# Add the centered logo to the background
def add_watermark(figure, source_file, max_scale=1, alpha=0.05):
    """ add a watermark to an image
    Parameters
    ----------
    figure : matplotlib.figure
        figure object
    source_file : Path / str
        source file
    max_scale : float
        maximum scale of watermark vs whole figure
    alpha : float
        transparency of watermark
    """

    wm = Image.open(source_file)

    wm_size = np.array(wm.size)

    max_size = figure.get_size_inches() * figure.dpi * max_scale
    scaling_factor = min(max_size / wm_size)

    img_size = (wm_size * scaling_factor).astype(int)
    wmr = wm.resize(img_size)

    x_offset = int((figure.bbox.xmax - img_size[0]) * 0.5)
    y_offset = int((figure.bbox.ymax - img_size[1]) * 0.5)

    # Remove all figure images
    found = False
    for c in figure.get_children():
        if type(c) == FigureImage:
            c.remove()

    figure.figimage(wmr, xo=x_offset, yo=y_offset, origin='upper', alpha=alpha)



## Main App

### Init graph
fig, ax = plt.subplots(len(sensors))
#add_watermark(fig, BG_LOGO)


for i, sensor in enumerate(sensors):
    lines_for_legend = []
    for num_ax, sens_ax in enumerate(sensors[sensor]["ax"]):
        new_ax = ax[i] if hasattr(ax, "__getitem__") else ax

        if num_ax == 1:
            new_ax = new_ax.twinx()

        sensors[sensor]["ax"][num_ax]["data_ax"] = new_ax
        sensors[sensor]["ax"][num_ax]["data_line"], = sensors[sensor]["ax"][num_ax]["data_ax"].plot(
                sensors[sensor]["ax"][num_ax]["x_data"],
                sensors[sensor]["ax"][num_ax]["y_data"],
                ls = sensors[sensor]["ax"][num_ax]["linestyle"],
                marker = sensors[sensor]["ax"][num_ax]["marker"],
                c = sensors[sensor]["ax"][num_ax]["color"],
                label=sensors[sensor]["ax"][num_ax]["ylabel"],
                )
        lines_for_legend.append(sensors[sensor]["ax"][num_ax]["data_line"])
        sensors[sensor]["ax"][num_ax]["data_ax"].set_title(sensors[sensor]["title"])
        sensors[sensor]["ax"][num_ax]["data_ax"].set_xlabel(sensors[sensor]["ax"][num_ax]["xlabel"])
        sensors[sensor]["ax"][num_ax]["data_ax"].set_ylabel(sensors[sensor]["ax"][num_ax]["ylabel"])
        sensors[sensor]["ax"][num_ax]["data_ax"].set_facecolor("none")
        if len(lines_for_legend) > 1:
            sensors[sensor]["ax"][num_ax]["data_ax"].legend(lines_for_legend, [l.get_label() for l in lines_for_legend], loc=0)


serial_port = None

for port in list_ports.comports():
    print(port.hwid, port.vid, port.pid)
    d = port.device
    print(d)
    if d.startswith("/dev/ttyACM"):
        serial_port = d

if serial_port is None:
    serial_port = "/dev/ttyACM0"

with Serial(serial_port, 19200, timeout=20) as ser:
    reader = ReaderThread(ser, SerialReaderProtocolLine)
    reader.start()
    plt.suptitle("Sensor Readings using MoleNet - Visit molenet.org", fontsize=14)
    ani = animation.FuncAnimation(fig, update_plot, interval=100) # Interval in ms
    cid = fig.canvas.mpl_connect("resize_event", on_resize_event)
    plt.tight_layout()
    plt.show()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        plt.close("all")


