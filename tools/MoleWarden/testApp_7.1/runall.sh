#!/bin/sh

# Run all steps in one file
# Jens Dede <jd@comnets.uni-bremen.de>, 2026
# Hacky, but works ;-)

USAGE="Usage : $0 PORT"

if [ "$#" -ne 1 ]; then
    echo $USAGE
    exit 2
fi

PORT=$1
echo Using port \"$PORT\"...

DOWNLOAD_ESP32_FIRMWARE_LINK="https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20251209-v1.27.0.bin"
DOWNLOAD_PYBOARD_LINK="https://raw.githubusercontent.com/micropython/micropython/refs/heads/master/tools/pyboard.py"


# Check for tools
for f in esptool screen curl
do
    type $f 2>&1 > /dev/null
    if [ $? -ne 0 ] ; then
        echo \"$f\" does not exist. Please install it to run this script
        exit 1
    fi
done

# Check for files
if [ ! -e firmware.bin ] ; then
    echo \"firmware.bin\" does not exist. Downloading
    curl --output firmware.bin $DOWNLOAD_ESP32_FIRMWARE_LINK
else
    echo Using exitsing \"firmware.bin\"
fi

if [ ! -e pyboard.py ] ; then
    echo \"pyboard.py\" does not exist. Downloading
    curl --output pyboard.py $DOWNLOAD_PYBOARD_LINK
else
    echo Using exitsing \"pyboard.bin\"
fi

# Start the test
set -e # Abort in case of errors
esptool --port $PORT erase-flash
esptool --port $PORT --baud 460800 write_flash 0 firmware.bin

echo "Reset the board by pressing the reset button."
read -p "After, press any key to continue... " -n1 -s
echo "waiting for the board..."
sleep 3 # Let the board boot...
python3 ./pyboard.py -d $PORT -f cp src/main.py :main.py
python3 ./pyboard.py -d $PORT -f mkdir lib
python3 ./pyboard.py -d $PORT -f cp src/lib/* :lib/
screen $PORT

