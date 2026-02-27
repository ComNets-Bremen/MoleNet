Test LoRa between V6 and V7
===========================
 
This folder contain the test files and libraries used for LoRa communication tests between V6 boards (SX1276 chip) and V7 boards (SX1262 chip).

The scripts contain infinite send or receive loops for V6 or V7 boards.

- snd_V6.py 
- rec_V6.py
- snd_V7.py
- rec_V7.py

copy the files to board and run them - for example - by typing 

```
import snd_v6
````

from the Python REPL prompt on a V6 board. 