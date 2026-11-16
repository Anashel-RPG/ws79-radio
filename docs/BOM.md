# Parts

The list covers the whole radio, in 21 numbered parts. The drawings in [WIRING.md](WIRING.md) and in
[the case plans](../print/README.md) call each part by its number here. The last column says where the part stands in
version 1.0: **wired** means it runs in the bench build, and **planned** means it is in the design and not connected
yet.

The references are the parts I ordered. Any equivalent part works, except where a note says otherwise. The sizes and
the electrical values come from each maker's or seller's page, read on 10 and 14 November 2026. I have measured none of
them myself. The openings of the case are another matter: they are measured in its print files.

## The list

| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | No. | Part | What it does | In version 1.0 |
|---|---|---|---|---|
| <img src="images/parts/part-01-raspberry-pi-4.jpg" width="96" alt="Raspberry Pi 4 Model B, 1 GB"> | 1 | [Raspberry Pi 4 Model B, 1 GB](#part-1) | Runs the radio program, plays the sounds and drives the screen | Wired |
| <img src="images/parts/part-02-microsd-card.jpg" width="96" alt="microSD card, 32 GB"> | 2 | [microSD card, 32 GB](#part-2) | Holds Raspberry Pi OS and the radio program | Wired |
| <img src="images/parts/part-03-bar-display.jpg" width="96" alt="3.7 in bar display, 240 × 960 pixels"> | 3 | [3.7 in bar display, 240 × 960 pixels](#part-3) | Shows the channel and the spectrum. The finished radio has two, end to end | One wired, one planned |
| <img src="images/parts/part-04-qualia-board.jpg" width="96" alt="Qualia ESP32-S3 board for RGB-666 displays"> | 4 | [Qualia ESP32-S3 board for RGB-666 displays](#part-4) | Drives one bar display. The Pi talks to it over USB | Wired |
| <img src="images/parts/part-05-vu-meters.jpg" width="96" alt="Pair of VU meters, 0 to 500 µA"> | 5 | [Pair of VU meters, 0 to 500 µA](#part-5) | The SIGNAL and AUDIO needles | Planned |
| <img src="images/parts/part-06-trim-potentiometer.jpg" width="96" alt="10 kΩ trim potentiometer"> | 6 | [10 kΩ trim potentiometer](#part-6) | Sets the full scale of each needle | Planned |
| <img src="images/parts/part-07-keypad.jpg" width="96" alt="SinLoon keypad, 6 keys and a knob"> | 7 | [SinLoon keypad, 6 keys and a knob](#part-7) | The channel keys and the volume knob | Wired |
| <img src="images/parts/part-08-cb-microphone.jpg" width="96" alt="Uniden BC645 CB microphone"> | 8 | [Uniden BC645 CB microphone](#part-8) | The hand microphone and its push-to-talk button | Planned |
| <img src="images/parts/part-09-usb-sound-adapter.jpg" width="96" alt="USB sound adapter with a microphone input"> | 9 | [USB sound adapter with a microphone input](#part-9) | The microphone's way into the Pi | Planned |
| <img src="images/parts/part-10-trrs-plug.jpg" width="96" alt="3.5 mm TRRS plug with screw terminals"> | 10 | [3.5 mm TRRS plug with screw terminals](#part-10) | Joins the microphone socket to the sound adapter without soldering | Planned |
| <img src="images/parts/part-11-speaker.jpg" width="96" alt="MonkMakes Amplified Speaker 2"> | 11 | [MonkMakes Amplified Speaker 2](#part-11) | The speaker, with its own amplifier | Wired |
| <img src="images/parts/part-12-audio-cable.jpg" width="96" alt="3.5 mm audio cable, 30 cm, one end at a right angle"> | 12 | [3.5 mm audio cable, 30 cm, one end at a right angle](#part-12) | Takes the sound from the Pi's jack to the speaker | Wired |
| <img src="images/parts/part-13-step-up-cable.jpg" width="96" alt="USB 5 V to 12 V step-up cable"> | 13 | [USB 5 V to 12 V step-up cable](#part-13) | Makes the 12 V for the meters' lamps | Planned |
| <img src="images/parts/part-14-usb-c-cable.jpg" width="96" alt="USB-C to USB-C cable, 91 cm"> | 14 | [USB-C to USB-C cable, 91 cm](#part-14) | Powers the finished radio from a computer. It is the only cable that leaves the case | Planned |
| <img src="images/parts/part-15-usb-a-to-c-cable.jpg" width="96" alt="USB-A to USB-C cable, 91 cm"> | 15 | [USB-A to USB-C cable, 91 cm](#part-15) | Connects the Pi to the Qualia board | Wired |
| <img src="images/parts/part-16-jumper-wires.jpg" width="96" alt="Jumper wires and clip leads"> | 16 | [Jumper wires and clip leads](#part-16) | Bring 5 V and ground from the Pi's pins to the speaker | Wired |
| <img src="images/parts/part-17-sd-adapter.jpg" width="96" alt="microSD to SD adapter"> | 17 | [microSD to SD adapter](#part-17) | Lets a computer's SD slot write the card | Wired |
| <img src="images/parts/part-04-qualia-board.jpg" width="96" alt="Second Qualia ESP32-S3 board"> | 18 | [Second Qualia ESP32-S3 board](#part-18) | Drives the second bar display | Planned |
| <img src="images/parts/part-15-usb-a-to-c-cable.jpg" width="96" alt="Second USB-A to USB-C cable"> | 19 | [Second USB-A to USB-C cable](#part-19) | Connects the second Qualia board to the Pi | Planned |
|  | 20 | [USB-A socket on four jumper wires](#part-20) | Brings 5 V from the Pi's header to the step-up cable | Planned |
|  | 21 | [4-pin chassis socket for a CB microphone](#part-21) | Lets the microphone plug into the front panel | Planned |

Three notes on these parts.

- **The keypad must be this model.** The installer programs it over USB, and the tool it uses only speaks to keypads
  built on the CH57x chip that identify as `1189:8890`.
- **The screen and its board must be these two.** The screen program is written for the Qualia board and the
  240 × 960 bar.
- **Two female-to-female jumper wires replace part 16.** The clips of the leads are too wide for pins that sit
  2.54 mm apart, which is why the bench build chains a jumper wire and a clip lead. A wire with a socket at each end
  goes straight from the Pi's pin to the speaker's pin.

## The sheets

One sheet for each part, in the order of the list.

### <a id="part-1"></a>1. Raspberry Pi 4 Model B, 1 GB

| | |
|---|---|
| <img src="images/parts/part-01-raspberry-pi-4.jpg" width="200" alt="Raspberry Pi 4 Model B, 1 GB"> | Runs the radio program, plays the sounds and drives the screen.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** PiShop 1GB-9002<br>**Comes with:** A 5.1 V 3 A USB-C power supply and 3 heat sinks<br>**Processor:** Broadcom BCM2711, four Cortex-A72 cores<br>**Memory:** 1 GB<br>**Ports:** 2 USB 3.0, 2 USB 2.0, USB-C for power<br>**Header:** 40 pins<br>**Audio:** 3.5 mm jack, 4 poles<br>**Board:** 85 × 56 mm<br>**Maker's page:** https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-product-brief.pdf |

### <a id="part-2"></a>2. microSD card, 32 GB

| | |
|---|---|
| <img src="images/parts/part-02-microsd-card.jpg" width="200" alt="microSD card, 32 GB"> | Holds Raspberry Pi OS and the radio program.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** Patriot 32 GB, Amazon B08KSSXKYR<br>**Capacity:** 32 GB, microSDHC<br>**Adapter:** None in the box. Part 17 is the adapter. |

### <a id="part-3"></a>3. 3.7 in bar display, 240 × 960 pixels

| | |
|---|---|
| <img src="images/parts/part-03-bar-display.jpg" width="200" alt="3.7 in bar display, 240 × 960 pixels"> | Shows the channel and the spectrum. The finished radio has two, end to end.<br><br>**Quantity:** 2<br>**In version 1.0:** one wired, one planned<br>**Reference:** Adafruit 5799<br>**Model:** HD371001C40, no touch screen<br>**Driver:** ST7701S<br>**Interface:** TTL RGB on a 40-pin ribbon<br>**Outline:** 98.89 × 25.3 mm<br>**Lit area:** 91.44 × 22.86 mm<br>**Ribbon:** 20.5 mm wide, 50 mm long<br>**Maker's page:** https://www.adafruit.com/product/5799 |

### <a id="part-4"></a>4. Qualia ESP32-S3 board for RGB-666 displays

| | |
|---|---|
| <img src="images/parts/part-04-qualia-board.jpg" width="200" alt="Qualia ESP32-S3 board for RGB-666 displays"> | Drives one bar display. The Pi talks to it over USB.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** Adafruit 5800<br>**Chip:** ESP32-S3, 16 MB of flash, 8 MB of PSRAM<br>**Display connector:** 40 pins, RGB-666<br>**USB:** USB-C, for power and programming<br>**Board:** 58 × 43 mm<br>**Maker's page:** https://learn.adafruit.com/adafruit-qualia-esp32-s3-for-rgb666-displays |

### <a id="part-5"></a>5. Pair of VU meters, 0 to 500 µA

| | |
|---|---|
| <img src="images/parts/part-05-vu-meters.jpg" width="200" alt="Pair of VU meters, 0 to 500 µA"> | The SIGNAL and AUDIO needles.<br><br>**Quantity:** 1 pair<br>**In version 1.0:** planned<br>**Reference:** Amazon B0GV1VC7PZ<br>**In the box:** 2 meters and 2 driver boards<br>**Scale:** 0 to 500 µA<br>**Size:** 46 × 48 × 46 mm each<br>**Lamp:** 12 V LED<br>**Driver boards:** 6 to 12 V in, 55 mA |

### <a id="part-6"></a>6. 10 kΩ trim potentiometer

| | |
|---|---|
| <img src="images/parts/part-06-trim-potentiometer.jpg" width="200" alt="10 kΩ trim potentiometer"> | Sets the full scale of each needle.<br><br>**Quantity:** 2<br>**In version 1.0:** planned<br>**Reference:** PiShop 88<br>**Value:** 10 kΩ<br>**Pins:** 3, spaced 2.54 mm |

### <a id="part-7"></a>7. SinLoon keypad, 6 keys and a knob

| | |
|---|---|
| <img src="images/parts/part-07-keypad.jpg" width="200" alt="SinLoon keypad, 6 keys and a knob"> | The channel keys and the volume knob.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** Amazon B0DN9T9J75, model SL2024502<br>**Keys:** 6 mechanical keys and 1 knob that turns and presses<br>**Light:** RGB, under the keys<br>**Connection:** USB-C, cable in the box<br>**USB identity:** `1189:8890`, which the installer looks for |

### <a id="part-8"></a>8. Uniden BC645 CB microphone

| | |
|---|---|
| <img src="images/parts/part-08-cb-microphone.jpg" width="200" alt="Uniden BC645 CB microphone"> | The hand microphone and its push-to-talk button.<br><br>**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** Amazon B008CLIB5K<br>**Plug:** 4 pins, wired the Cobra and Uniden way<br>**Cord:** Coiled, 2.4 m<br>**Button:** Push to talk |

### <a id="part-9"></a>9. USB sound adapter with a microphone input

| | |
|---|---|
| <img src="images/parts/part-09-usb-sound-adapter.jpg" width="200" alt="USB sound adapter with a microphone input"> | The microphone's way into the Pi.<br><br>**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** DuKabel, Amazon B07RS11M1T<br>**Jack:** 3.5 mm, 4 poles (TRRS), microphone and output<br>**Standard:** CTIA<br>**Cable:** Braided, 25 cm |

### <a id="part-10"></a>10. 3.5 mm TRRS plug with screw terminals

| | |
|---|---|
| <img src="images/parts/part-10-trrs-plug.jpg" width="200" alt="3.5 mm TRRS plug with screw terminals"> | Joins the microphone socket to the sound adapter without soldering.<br><br>**Quantity:** 1 of a pack of 2<br>**In version 1.0:** planned<br>**Reference:** Amazon B08QFHHJ3Z<br>**Plug:** 3.5 mm male, 4 poles<br>**Terminals:** 4 screw terminals<br>**Length:** 32 cm |

### <a id="part-11"></a>11. MonkMakes Amplified Speaker 2

| | |
|---|---|
| <img src="images/parts/part-11-speaker.jpg" width="200" alt="MonkMakes Amplified Speaker 2"> | The speaker, with its own amplifier.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** PiShop 348-1<br>**Power:** 3.3 to 6 V, 300 mA at most<br>**Speaker:** 8 Ω, 500 mW<br>**Input:** 3.5 mm jack<br>**Size:** 51 × 56 × 61 mm<br>**Maker's page:** https://monkmakes.com/downloads/datasheet_amp_speaker_2.pdf |

### <a id="part-12"></a>12. 3.5 mm audio cable, 30 cm, one end at a right angle

| | |
|---|---|
| <img src="images/parts/part-12-audio-cable.jpg" width="200" alt="3.5 mm audio cable, 30 cm, one end at a right angle"> | Takes the sound from the Pi's jack to the speaker.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** Amazon B08F2GRHXC<br>**Plugs:** 3.5 mm male at both ends, one at 90°<br>**Length:** 30 cm |

### <a id="part-13"></a>13. USB 5 V to 12 V step-up cable

| | |
|---|---|
| <img src="images/parts/part-13-step-up-cable.jpg" width="200" alt="USB 5 V to 12 V step-up cable"> | Makes the 12 V for the meters' lamps.<br><br>**Quantity:** 1 of a pack of 3<br>**In version 1.0:** planned<br>**Reference:** SinLoon, Amazon B0F2YKGS25<br>**Input:** USB-A, 5 V, 2 A at most<br>**Output:** 12 V, 0.8 A at most, on bare wires<br>**Length:** 88 cm |

### <a id="part-14"></a>14. USB-C to USB-C cable, 91 cm

| | |
|---|---|
| <img src="images/parts/part-14-usb-c-cable.jpg" width="200" alt="USB-C to USB-C cable, 91 cm"> | Powers the finished radio from a computer. It is the only cable that leaves the case.<br><br>**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** PiShop 700-1<br>**Standard:** USB 3.2 Gen 2<br>**Length:** 91 cm (3 ft) |

### <a id="part-15"></a>15. USB-A to USB-C cable, 91 cm

| | |
|---|---|
| <img src="images/parts/part-15-usb-a-to-c-cable.jpg" width="200" alt="USB-A to USB-C cable, 91 cm"> | Connects the Pi to the Qualia board.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** PiShop CS-PID-45<br>**Standard:** USB 2.0. It must be a data cable.<br>**Length:** 91 cm (3 ft). A shorter one fits the case better. |

### <a id="part-16"></a>16. Jumper wires and clip leads

| | |
|---|---|
| <img src="images/parts/part-16-jumper-wires.jpg" width="150" alt="Jumper wires and clip leads"> <img src="images/parts/part-16-clip-leads.jpg" width="150" alt="Jumper wires and clip leads"> | Bring 5 V and ground from the Pi's pins to the speaker.<br><br>**Quantity:** 2 wires of 40, 2 leads of 10<br>**In version 1.0:** wired<br>**References:** PiShop 283 for the wires, SparkFun 15186 for the leads<br>**Jumper wires:** Male to female, 20 cm, sockets spaced 2.54 mm<br>**Clip leads:** A clip at one end, a female socket at the other, 30 cm<br>**Maker's page:** https://www.sparkfun.com/products/15186 |

### <a id="part-17"></a>17. microSD to SD adapter

| | |
|---|---|
| <img src="images/parts/part-17-sd-adapter.jpg" width="200" alt="microSD to SD adapter"> | Lets a computer's SD slot write the card.<br><br>**Quantity:** 1<br>**In version 1.0:** wired<br>**Reference:** Adafruit 5447<br>**Format:** microSD to SD, short version<br>**Maker's page:** https://www.adafruit.com/product/5447 |

### <a id="part-18"></a>18. Second Qualia ESP32-S3 board

| | |
|---|---|
| <img src="images/parts/part-04-qualia-board.jpg" width="200" alt="Second Qualia ESP32-S3 board"> | Drives the second bar display.<br><br>**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** Adafruit 5800, the same board as part 4<br>**Maker's page:** https://www.adafruit.com/product/5800 |

### <a id="part-19"></a>19. Second USB-A to USB-C cable

| | |
|---|---|
| <img src="images/parts/part-15-usb-a-to-c-cable.jpg" width="200" alt="Second USB-A to USB-C cable"> | Connects the second Qualia board to the Pi.<br><br>**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** PiShop CS-PID-45, the same cable as part 15 |

### <a id="part-20"></a>20. USB-A socket on four jumper wires

Brings 5 V from the Pi's header to the step-up cable.

**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** Adafruit 4449<br>**Socket:** USB-A female, on a 30 cm cable<br>**Wires:** Four female ends spaced 2.54 mm. Red is 5 V and black is ground. Green and white are the data lines and stay free.<br>**Maker's page:** https://www.adafruit.com/product/4449

### <a id="part-21"></a>21. 4-pin chassis socket for a CB microphone

Lets the microphone plug into the front panel.

**Quantity:** 1<br>**In version 1.0:** planned<br>**Reference:** A 4-pin male chassis socket, of the kind used on Cobra and Uniden radios<br>**Mounting:** In the 16.2 mm hole of the face. Try it with the microphone's plug before you mount it.

## Where the pictures come from

The pictures of the parts are the product pictures of their makers and sellers. They belong to their owners and
are here to identify the parts. They are not covered by this repository's licence
([LICENSE-MEDIA.md](../LICENSE-MEDIA.md)). Parts 20 and 21 have no picture yet.
