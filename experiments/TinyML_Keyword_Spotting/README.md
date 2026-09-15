# TinyML Keyword Spotting on MoleNet ESP32-S3

This experiment implements **on-device keyword spotting (KWS)** on the **MoleNet V7.1 ESP32-S3** using an **INMP441 I2S microphone**.

The system recognizes three spoken keywords:

- `YES`
- `NO`
- `UP`

The complete audio-processing and inference pipeline runs locally on the ESP32-S3.

The detected keyword controls the onboard D6 LED:

| Keyword | Action |
|---|---|
| `YES` | D6 LED ON |
| `NO` | D6 LED OFF |
| `UP` | D6 LED blinks 3 times |

---

## System Overview

```text
INMP441 microphone
        |
        v
2-second audio capture
        |
        v
1-second speech-region selection
        |
        v
MFCC feature extraction
        |
        v
INT8 ESP-DL CNN
        |
        v
YES / NO / UP
        |
        v
D6 LED action
```

The firmware records two seconds of audio at 16 kHz and automatically selects the strongest one-second speech region for classification.

---

## Hardware

### Required Hardware

- MoleNet V7.1 with ESP32-S3
- INMP441 I2S microphone
- USB cable

### INMP441 Wiring

| INMP441 | MoleNet V7.1 |
|---|---|
| VDD | 3.3 V |
| GND | GND |
| SCK / BCLK | GPIO40 |
| WS / LRCLK | GPIO41 |
| SD | GPIO42 |
| L/R | GND |

`L/R` is connected to GND, therefore the microphone is read from the left I2S channel.

The onboard action LED used in this experiment is:

```text
D6 -> GPIO38
```

---

## Project Structure

```text
TinyML_Keyword_Spotting/
|
├── README.md
|
└── firmware/
    ├── CMakeLists.txt
    ├── partitions.csv
    ├── sdkconfig.defaults
    ├── dependencies.lock
    |
    ├── components/
    │   └── kissfft/
    │       ├── CMakeLists.txt
    │       ├── kiss_fft.c
    │       ├── kiss_fft.h
    │       ├── kiss_fftr.c
    │       ├── kiss_fftr.h
    │       ├── _kiss_fft_guts.h
    │       ├── kiss_fft_log.h
            ├── COPYING.txt
    │       └── LICENSE
    |
    └── main/
        ├── CMakeLists.txt
        ├── idf_component.yml
        ├── main.cpp
        |
        ├── models/
        │   └── kws_3class.espdl
        |
        └── mfcc_params/
            ├── hann_window.bin
            ├── mel_filterbank_transposed.bin
            ├── dct_matrix.bin
            └── mfcc_params.txt
```

### Main Files

| File | Purpose |
|---|---|
| `main/main.cpp` | Audio capture, MFCC extraction, inference and LED control |
| `main/models/kws_3class.espdl` | Quantized keyword-spotting model |
| `main/mfcc_params/` | Parameters required for MFCC extraction |
| `main/idf_component.yml` | ESP-DL dependency |
| `components/kissfft/` | FFT implementation used for MFCC calculation |
| `partitions.csv` | Custom flash partition table |
| `sdkconfig.defaults` | Default ESP-IDF configuration |

---

# Build and Run

## 1. Install ESP-IDF

The experiment was tested with:

```text
ESP-IDF v6.0.2
Target: ESP32-S3
```

ESP-IDF installation:

https://docs.espressif.com/projects/esp-idf/en/release-v6.0/esp32s3/get-started/index.html

Windows setup:

https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/windows-setup.html

After installation, open an ESP-IDF terminal.

---

## 2. Open the Firmware Directory

From the MoleNet repository root:

```bash
cd experiments/TinyML_Keyword_Spotting/firmware
```

---

## 3. Set the ESP32-S3 Target

```bash
idf.py set-target esp32s3
```

---

## 4. Build the Firmware

```bash
idf.py build
```

ESP-DL is declared in:

```text
main/idf_component.yml
```

and is resolved by the ESP-IDF Component Manager during the build.

---

## 5. Connect the Board

Connect the MoleNet board to the computer using USB.

Identify the serial port.

Examples:

```text
Windows : COM34
Linux   : /dev/ttyUSB0
macOS   : /dev/cu.usbmodem...
```

---

## 6. Flash and Open the Serial Monitor

```bash
idf.py -p PORT flash monitor
```

Example:

```bash
idf.py -p COM34 flash monitor
```

Replace `PORT` with the port assigned to the board.

Exit the serial monitor with:

```text
Ctrl + ]
```

---

## 7. Test Keyword Recognition

Follow the prompt in the serial monitor and speak one of:

```text
YES
NO
UP
```

Expected LED behavior:

```text
YES -> D6 ON
NO  -> D6 OFF
UP  -> D6 blinks 3 times
```

An LED action is performed when prediction confidence is at least:

```text
70%
```

---

# How the Firmware Works

## 1. Audio Capture

The INMP441 microphone is sampled using the ESP32-S3 I2S interface.

```text
Sample rate : 16 kHz
Capture time: 2 seconds
Samples     : 32000
```

---

## 2. Speech-Region Selection

The model expects one second of audio.

The firmware searches the two-second recording for the strongest speech region and selects a one-second segment:

```text
16000 samples
```

This allows the keyword to be spoken anywhere within the capture period.

---

## 3. Audio Quality Check

Before feature extraction, the selected audio is checked for:

- low signal level
- clipping
- excessive microphone input level

The firmware uses an RMS threshold to reject very quiet recordings and checks the fraction of samples close to full-scale amplitude.

---

## 4. MFCC Feature Extraction

The selected one-second audio segment is converted to MFCC features directly on the ESP32-S3.

Configuration:

```text
Sample rate : 16000 Hz
FFT size    : 1024
Window      : 800 samples
Window time : 50 ms
Hop         : 160 samples
Hop time    : 10 ms
Mel filters : 128
MFCCs       : 40
Frames      : 101
```

Final model input:

```text
40 x 101 MFCC
```

Processing:

```text
Audio
  |
  v
Hann window
  |
  v
1024-point FFT
  |
  v
Power spectrum
  |
  v
Mel filterbank
  |
  v
dB conversion
  |
  v
DCT
  |
  v
40 x 101 MFCC
```

The following preprocessing parameters are embedded into the firmware:

```text
hann_window.bin
mel_filterbank_transposed.bin
dct_matrix.bin
```

KISS FFT is used for the FFT computation.

---

## 5. Neural-Network Inference

The MFCC features are passed to the embedded ESP-DL model:

```text
main/models/kws_3class.espdl
```

Output classes:

```text
0 -> YES
1 -> NO
2 -> UP
```

The predicted class and confidence are printed in the serial monitor.

Predictions below the configured confidence threshold do not trigger the LED action.

---

# Keyword-Spotting Model

The deployed model is a lightweight convolutional neural network.

```text
Input: 1 x 40 x 101

Conv2D
1 -> 8
3 x 3

ReLU
MaxPool

Conv2D
8 -> 16
3 x 3

ReLU
MaxPool

Adaptive Average Pool

Flatten

Linear
16 -> 3

Output:
YES / NO / UP
```

Total trainable parameters:

```text
1,299
```

The deployment pipeline is:

```text
PyTorch FP32 model
        |
        v
ONNX
        |
        v
ESP-PPQ quantization
        |
        v
W8A8 INT8 model
        |
        v
ESP-DL .espdl
        |
        v
ESP32-S3
```

`W8A8` means:

```text
8-bit weights
8-bit activations
```

---

## Model Performance

| Model | Test Accuracy |
|---|---:|
| FP32 | 95.87% |
| INT8 | 93.67% |

INT8 per-class accuracy:

| Keyword | Accuracy |
|---|---:|
| YES | 95.94% |
| NO | 90.12% |
| UP | 94.82% |

Final ESP-DL model size:

```text
11,616 bytes
approximately 11.34 KiB
```

---

# Dataset

The model was developed using the following classes from **Google Speech Commands v0.02**:

```text
yes
no
up
```

Google Speech Commands:

https://www.tensorflow.org/datasets/catalog/speech_commands

Speech Commands paper:

https://arxiv.org/abs/1804.03209

---

# ESP-DL

ESP-DL is used for neural-network inference on the ESP32-S3.

The project dependency is defined in:

```text
main/idf_component.yml
```

ESP-DL:

https://github.com/espressif/esp-dl

Documentation:

https://docs.espressif.com/projects/esp-dl/en/latest/getting_started/readme.html

Quantization documentation:

https://docs.espressif.com/projects/esp-dl/en/latest/tutorials/how_to_quantize_model.html

---

# ESP-PPQ

ESP-PPQ is used to quantize the ONNX model for ESP-DL deployment.

https://github.com/espressif/esp-ppq

---

# KISS FFT

KISS FFT is used for the FFT stage of MFCC extraction.

Source:

https://github.com/mborgerding/kissfft

The required source files are included in:

```text
firmware/components/kissfft/
```

The original BSD-3-Clause license is retained in:

```text
firmware/components/kissfft/LICENSE
```

---

# Custom Partition Configuration

The firmware uses the custom partition table:

```text
partitions.csv
```

The corresponding configuration is defined in:

```text
sdkconfig.defaults
```

```ini
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"
CONFIG_PARTITION_TABLE_FILENAME="partitions.csv"
```

---

# Troubleshooting

## No Microphone Signal

Check the wiring:

```text
VDD -> 3.3 V
GND -> GND
SCK -> GPIO40
WS  -> GPIO41
SD  -> GPIO42
L/R -> GND
```

---

## Input Level Too High

Speak at a normal volume or increase the distance between the speaker and microphone.

Strongly clipped audio can reduce recognition accuracy.

---

## ESP-DL Build Error

Run:

```bash
idf.py fullclean
idf.py set-target esp32s3
idf.py build
```

---

## Wrong Serial Port

Check the board's serial port and use:

```bash
idf.py -p PORT flash monitor
```

---

## Repeated Incorrect Prediction

Check:

- microphone wiring
- background noise
- microphone distance
- speech volume
- clipping
- correct `.espdl` model
- MFCC parameter files

---

# References

### ESP-IDF

https://docs.espressif.com/projects/esp-idf/en/release-v6.0/esp32s3/get-started/index.html

### ESP32-S3 I2S

https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/i2s.html

### ESP-DL

https://github.com/espressif/esp-dl

https://docs.espressif.com/projects/esp-dl/en/latest/getting_started/readme.html

### ESP-PPQ

https://github.com/espressif/esp-ppq

### ONNX

https://onnx.ai/

### PyTorch

https://pytorch.org/

### TorchAudio MFCC

https://docs.pytorch.org/audio/main/generated/torchaudio.transforms.MFCC

### Google Speech Commands

https://www.tensorflow.org/datasets/catalog/speech_commands

https://arxiv.org/abs/1804.03209

### INMP441

https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf

### KISS FFT

https://github.com/mborgerding/kissfft

---

# License

Refer to the repository-level `LICENSE` for the project license.

KISS FFT is distributed under its original BSD-3-Clause license:

```text
firmware/components/kissfft/LICENSE
```
