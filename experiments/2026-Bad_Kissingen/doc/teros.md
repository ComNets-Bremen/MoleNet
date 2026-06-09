TEROS setup
===========

The TEROS ground soil sensor has to be configured when new. 
We can use the program `main_sdi12_terminal.py`, which is on the node, to setup the sensor.
We have to type some command strings which can be found in the user manual (TEROS 11/12 INTEGRATOR GUIDE).

~~~terminal
MPY: soft reboot
Init SDI12
16
SPI working, version check passed
Read config
SDI12> 0I!   # The default ID is 0, but the sensor behaves differently with id 0.
writing
reading
b'013METER   TER11 303T11-00044991\r\n'
SDI12> 0A1!  # Set another ID, for example 1, when we have only one SDI12 sensor on the node. 
writing
reading
b'1\r\n'
SDI12> 1I!   # Check if the sensor is reachable under it's new ID 1.
writing
reading
b'113METER   TER11 303T11-00044991\r\n'
SDI12> 
~~~
