# Credits

The radio is built from other people's parts, programs and works. This list names them.

## Parts

| Part | Maker |
|---|---|
| Raspberry Pi 4 Model B | Raspberry Pi Ltd |
| Qualia ESP32-S3 board and 3.7 in bar display | Adafruit Industries |
| Amplified Speaker 2 | MonkMakes |
| 6-key keypad with a knob | SinLoon |

## Programs

The installer downloads these. None of them is copied into this repository.

| Program | What the radio uses it for | Home |
|---|---|---|
| Raspberry Pi OS | The system on the Pi | https://www.raspberrypi.com/software/ |
| CircuitPython 10.3.2 | The system on the screen board | https://circuitpython.org |
| Adafruit CircuitPython libraries: Qualia, Display Text, ImageLoad | The display, the text and the pictures on the screen board | https://github.com/adafruit |
| ch57x-keyboard-tool 1.7.0, by Mikhail Trishchenkov | Programs the keypad's keys, knob and light | https://github.com/kriomant/ch57x-keyboard-tool |
| esptool | Writes CircuitPython to the screen board | https://github.com/espressif/esptool |
| circup | Installs the CircuitPython libraries | https://github.com/adafruit/circup |
| pygame, NumPy, python-evdev, pySerial | Sound, spectrum, keypad and serial port in the Pi program | their own projects |

One file of Adafruit's Qualia library is included with one value changed, the display's clock:
`screen/lib-patch/bar240x960.py`. Its authors are Scott Shawcroft and Melissa LeBlanc-Williams, for Adafruit
Industries, and its MIT notice is at the top of the file.

## Works

| Work | Where it is used |
|---|---|
| The Lincolnshire Poacher, a shortwave numbers station | The recording on key 2 |
| Robot 36, a slow-scan television mode | The way the picture on key 4 is sent as sound |
| Exo, a typeface by Natanael Gama and The Exo Project Authors | The screen artwork, the case plans and the legends of the model |
| Plus Jakarta Sans and JetBrains Mono, two typefaces under the SIL Open Font License | The lettering of the wiring drawings. The fonts themselves are not in this repository. |
| The product pictures of the parts, by their makers and sellers | The parts list and the small pictures inside the wiring drawings |
