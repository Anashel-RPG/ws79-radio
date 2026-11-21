# Parts

The radio has 23 parts, labelled A1 to A23. One place needs soldering: the two lamp holes on each meter's driver
board, four joints in all. Nothing else is soldered. The drawings in [WIRING.md](WIRING.md) and in
[the case plans](../print/README.md) call each part by its label. The last column says where the part stands in
version 1.0: **wired** means it is part of the bench build, and **planned** means it is in the design and not connected
yet.

Each reference is the part I picked for the radio. Any
equivalent part works, except where a note says otherwise. The sizes and the electrical values come from each maker's
or seller's page, read between 10 and 16 November 2026. I have measured none of them myself. The openings of the case
are another matter: they are measured in its print files.

## The list

| No. | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Part | Qty | What it does | In version 1.0 |
|---|---|---|---|---|---|
| **A1** | <img src="images/parts/a01-raspberry-pi-4.jpg" width="96" alt="Raspberry Pi 4 Model B, 1 GB"> | [Raspberry Pi 4 Model B, 1 GB](#a1) | **×1** | Runs the radio program, plays the sounds and drives the screens | Wired |
| **A2** | <img src="images/parts/a02-power-supply.jpg" width="96" alt="USB-C power supply, 5.1 V 3 A"> | [USB-C power supply, 5.1 V 3 A](#a2) | **×1, came with A1** | Powers the whole radio through one cable | Wired |
| **A3** | <img src="images/parts/a03-microsd-card.jpg" width="96" alt="microSD card, 32 GB"> | [microSD card, 32 GB](#a3) | **×1** | Holds Raspberry Pi OS and the radio program | Wired |
| **A4** | <img src="images/parts/a04-sd-adapter.jpg" width="96" alt="microSD to SD adapter"> | [microSD to SD adapter](#a4) | **×1** | Lets a computer's SD slot write the card | Wired |
| **A5** | <img src="images/parts/a05-bar-display.jpg" width="96" alt="3.7 in bar display, 240 × 960 pixels"> | [3.7 in bar display, 240 × 960 pixels](#a5) | **×2** | Shows the frequency, the channel and the spectrum. The two sit end to end behind the window | One wired, one planned |
| **A6** | <img src="images/parts/a06-qualia-board.jpg" width="96" alt="Qualia ESP32-S3 board for RGB-666 displays"> | [Qualia ESP32-S3 board for RGB-666 displays](#a6) | **×2** | Drives one bar display each. The Pi talks to each board over USB | One wired, one planned |
| **A7** | <img src="images/parts/a07-usb-a-to-c-cable.jpg" width="96" alt="USB-A to USB-C cable, 91 cm"> | [USB-A to USB-C cable, 91 cm](#a7) | **×3** | Connects the Pi to each Qualia board, and to the keypad | Two wired, one planned |
| **A8** | <img src="images/parts/a08-keypad.jpg" width="96" alt="SinLoon keypad, 6 keys and a knob"> | [SinLoon keypad, 6 keys and a knob](#a8) | **×1** | The channel keys and the volume knob | Wired |
| **A9** | <img src="images/parts/a09-vu-meters.jpg" width="96" alt="Pair of VU meters, 0 to 500 µA"> | [Pair of VU meters, 0 to 500 µA](#a9) | **×1 pair** | The SIGNAL and AUDIO needles | Planned |
| **A10** | <img src="images/parts/a10-trim-potentiometer.jpg" width="96" alt="10 kΩ trim potentiometer"> | [10 kΩ trim potentiometer](#a10) | **×2** | Sets the full scale of each needle | Planned |
| **A11** | <img src="images/parts/a11-step-up-cable.jpg" width="96" alt="USB 5 V to 12 V step-up cable"> | [USB 5 V to 12 V step-up cable](#a11) | **×1** | Turns 5 V into the 12 V that lights the meters | Planned |
| **A12** | <img src="images/parts/a12-usb-a-socket-on-wires.jpg" width="96" alt="USB-A socket on four jumper wires"> | [USB-A socket on four jumper wires](#a12) | **×1** | Gives the step-up cable a USB socket on the Pi's header | Planned |
| **A13** | <img src="images/parts/a13-speaker.jpg" width="96" alt="MonkMakes Amplified Speaker 2"> | [MonkMakes Amplified Speaker 2](#a13) | **×1** | The speaker, with its own amplifier | Wired |
| **A14** | <img src="images/parts/a14-audio-cable.jpg" width="96" alt="3.5 mm audio cable, 30 cm, one end at a right angle"> | [3.5 mm audio cable, 30 cm, one end at a right angle](#a14) | **×1** | Takes the sound from the Pi's jack to the speaker | Wired |
| **A15** | <img src="images/parts/a15-cb-microphone.jpg" width="96" alt="Uniden BC645 CB microphone"> | [Uniden BC645 CB microphone](#a15) | **×1** | The hand microphone and its push-to-talk button | Planned |
| **A16** | <img src="images/parts/a16-microphone-socket.jpg" width="96" alt="GX16 4-pin socket with its wires attached"> | [GX16 4-pin socket with its wires attached](#a16) | **×1** | The socket that the microphone plugs into | Planned |
| **A17** | <img src="images/parts/a17-usb-sound-adapter.jpg" width="96" alt="USB sound adapter with a microphone input"> | [USB sound adapter with a microphone input](#a17) | **×1** | Gives the Pi the microphone input it lacks | Planned |
| **A18** | <img src="images/parts/a18-trrs-plug.jpg" width="96" alt="3.5 mm TRRS plug with screw terminals"> | [3.5 mm TRRS plug with screw terminals](#a18) | **×1** | Joins the microphone's wires to the sound adapter | Planned |
| **A19** | <img src="images/parts/a19-jumper-wires.jpg" width="96" alt="Female-to-female jumper wires, 30 cm"> | [Female-to-female jumper wires, 30 cm](#a19) | **×1 strip of 20** | Join the Pi's pins to the speaker, the needles and the push-to-talk button | Wired |
| **A20** | <img src="images/parts/a20-usb-c-panel-socket.jpg" width="96" alt="USB-C panel socket on a 30 cm cable"> | [USB-C panel socket on a 30 cm cable](#a20) | **×2** | The two sockets on the back of the case: power, and the PC | Planned |
| **A21** | <img src="images/parts/a21-rocker-switch-cable.jpg" width="96" alt="USB-C cable with a rocker switch"> | [USB-C cable with a rocker switch](#a21) | **×1** | The master switch | Planned |
| **A22** | <img src="images/parts/a22-lever-connectors.jpg" width="96" alt="Lever connectors for thin wire, 3 ways"> | [Lever connectors for thin wire, 3 ways](#a22) | **×1 pack of 50** | Join the microphone socket's wires to jumper wires, with no soldering | Planned |
| **A23** | <img src="images/parts/a23-power-data-splitter.jpg" width="96" alt="USB-C power and data splitter"> | [USB-C power and data splitter](#a23) | **×1** | Gives the Pi its power from the supply and its data from the PC | Planned |

Five notes on these parts.

- **The keypad must be this model.** The installer programs it over USB, and the tool it uses only speaks to keypads
  built on the CH57x chip that identify as `1189:8890`.
- **The screens and their boards must be these two.** The screen program is written for the Qualia board and the
  240 × 960 bar.
- **Use wires with a socket at each end on the Pi's pins.** The bench build first used crocodile clip leads. Their
  clips are too wide for pins that sit 2.54 mm apart and they did not hold, so A19 replaces them.
- **A2 comes with A1 in the kit.** My Pi came with its power supply in the same order. Buy A2 only if your Pi
  comes without one. The radio needs one supply.
- **One cable powers everything.** The supply A2 plugs into a socket A20 on the back. Inside, the switch cable A21
  takes the power to the splitter A23, then to the Pi, and the Pi powers every other part through its USB ports and its
  header. A second cable, to a PC, is optional: it plugs into the second socket A20 and carries data only. A PC's USB
  port cannot power the radio, so the supply stays plugged in.
  [WIRING.md](WIRING.md#power) shows the path.

## The sheets

One sheet for each part, in the order of the list.

### <a id="a1"></a>A1. Raspberry Pi 4 Model B, 1 GB

| | |
|---|---|
| <img src="images/parts/a01-raspberry-pi-4.jpg" width="200" alt="Raspberry Pi 4 Model B, 1 GB"> | Runs the radio program, plays the sounds and drives the screens. Every other part takes its power from it.<br><br>**Quantity:** ×1<br>**In version 1.0:** wired<br>**Reference:** PiShop 1GB-9002, bought with a power supply (A2) and 3 heat sinks<br>**Connects:** Every other part connects to it. [The diagram](WIRING.md#every-part-and-every-link) shows each link.<br>**Processor:** Broadcom BCM2711, four Cortex-A72 cores<br>**Memory:** 1 GB<br>**Ports:** 2 USB 3.0, 2 USB 2.0, USB-C for power<br>**Header:** 40 pins<br>**Audio:** 3.5 mm jack, 4 poles<br>**Board:** 85 × 56 mm<br>**Maker's page:** https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-product-brief.pdf |

### <a id="a2"></a>A2. USB-C power supply, 5.1 V 3 A

| | |
|---|---|
| <img src="images/parts/a02-power-supply.jpg" width="200" alt="USB-C power supply, 5.1 V 3 A"> | Powers the whole radio. Its cable is the only one that leaves the case: it plugs into the socket A20 on the back.<br><br>**Quantity:** ×1, came with A1<br>**In version 1.0:** wired<br>**Reference:** The supply that came with A1 in my order. Raspberry Pi's own 15 W USB-C supply is the model to buy on its own, and the one the switch cable A21 is made for.<br>**Connects:** Its cable plugs into the socket A20, direct. On the bench it plugs straight into the Pi.<br>**Output:** 5.1 V, 3 A<br>**Plug:** USB-C. On Raspberry Pi's own supply it ends a 1.5 m cable that does not come off.<br>**Maker's page:** https://www.raspberrypi.com/products/type-c-power-supply/ |

### <a id="a3"></a>A3. microSD card, 32 GB

| | |
|---|---|
| <img src="images/parts/a03-microsd-card.jpg" width="200" alt="microSD card, 32 GB"> | Holds Raspberry Pi OS and the radio program.<br><br>**Quantity:** ×1<br>**In version 1.0:** wired<br>**Reference:** Patriot 32 GB, Amazon B08KSSXKYR<br>**Connects:** Goes into the Pi's microSD slot, direct.<br>**Capacity:** 32 GB, microSDHC<br>**Adapter:** None in the box. A4 is the adapter. |

### <a id="a4"></a>A4. microSD to SD adapter

| | |
|---|---|
| <img src="images/parts/a04-sd-adapter.jpg" width="200" alt="microSD to SD adapter"> | Lets a computer's SD slot write the card.<br><br>**Quantity:** ×1<br>**In version 1.0:** wired<br>**Reference:** Adafruit 5447<br>**Connects:** Holds A3 in a computer's SD slot while you prepare the card. It does not go in the radio.<br>**Format:** microSD to SD, short version<br>**Maker's page:** https://www.adafruit.com/product/5447 |

### <a id="a5"></a>A5. 3.7 in bar display, 240 × 960 pixels

| | |
|---|---|
| <img src="images/parts/a05-bar-display.jpg" width="200" alt="3.7 in bar display, 240 × 960 pixels"> | Shows the frequency, the channel and the spectrum. The finished radio has two, end to end behind the window.<br><br>**Quantity:** ×2<br>**In version 1.0:** one wired, one planned<br>**Reference:** Adafruit 5799<br>**Connects:** Its ribbon goes straight into the Qualia board A6, direct.<br>**Model:** HD371001C40, no touch screen<br>**Driver:** ST7701S<br>**Interface:** TTL RGB on a 40-pin ribbon<br>**Outline:** 98.89 × 25.3 mm<br>**Lit area:** 91.44 × 22.86 mm<br>**Ribbon:** 20.5 mm wide, 50 mm long<br>**Maker's page:** https://www.adafruit.com/product/5799 |

### <a id="a6"></a>A6. Qualia ESP32-S3 board for RGB-666 displays

| | |
|---|---|
| <img src="images/parts/a06-qualia-board.jpg" width="200" alt="Qualia ESP32-S3 board for RGB-666 displays"> | Drives one bar display. Each display has its own board, and the Pi talks to each board over USB.<br><br>**Quantity:** ×2<br>**In version 1.0:** one wired, one planned<br>**Reference:** Adafruit 5800<br>**Connects:** A USB-A port of the Pi, with A7. The ribbon of A5, direct.<br>**Chip:** ESP32-S3, 16 MB of flash, 8 MB of PSRAM<br>**Display connector:** 40 pins, RGB-666<br>**USB:** USB-C, for power and programming<br>**Board:** 58 × 43 mm<br>**Maker's page:** https://learn.adafruit.com/adafruit-qualia-esp32-s3-for-rgb666-displays |

### <a id="a7"></a>A7. USB-A to USB-C cable, 91 cm

| | |
|---|---|
| <img src="images/parts/a07-usb-a-to-c-cable.jpg" width="200" alt="USB-A to USB-C cable, 91 cm"> | Connects a USB-A port of the Pi to a Qualia board. The third one goes to the keypad, in place of the keypad's own cable.<br><br>**Quantity:** ×3<br>**In version 1.0:** two wired, one planned<br>**Reference:** PiShop CS-PID-45<br>**Connects:** Two go from USB-A ports of the Pi to the two Qualia boards A6. One goes from a USB-A port to the keypad A8.<br>**Standard:** USB 2.0. It must be a data cable.<br>**Length:** 91 cm (3 ft). A shorter one fits the case better. |

### <a id="a8"></a>A8. SinLoon keypad, 6 keys and a knob

| | |
|---|---|
| <img src="images/parts/a08-keypad.jpg" width="200" alt="SinLoon keypad, 6 keys and a knob"> | The channel keys and the volume knob.<br><br>**Quantity:** ×1<br>**In version 1.0:** wired<br>**Reference:** Amazon B0DN9T9J75, model SL2024502<br>**Connects:** A USB-A port of the Pi, with A7.<br>**Keys:** 6 mechanical keys and 1 knob that turns and presses<br>**Light:** RGB, under the keys<br>**Connection:** USB-C, cable in the box<br>**USB identity:** `1189:8890`, which the installer looks for |

### <a id="a9"></a>A9. Pair of VU meters, 0 to 500 µA

| | |
|---|---|
| <img src="images/parts/a09-vu-meters.jpg" width="200" alt="Pair of VU meters, 0 to 500 µA"> | The SIGNAL and AUDIO needles.<br><br>**Quantity:** ×1 pair<br>**In version 1.0:** planned<br>**Reference:** Amazon B0GV1VC7PZ<br>**Connects:** Each needle: a pin of the Pi, the potentiometer A10, then the meter's + terminal, with A19 wires. The − terminal goes back to a ground pin with A19. The lamps: the two wires of A11, direct.<br>**In the box:** 2 meters and 2 driver boards<br>**Scale:** 0 to 500 µA<br>**Size:** 46 × 48 × 46 mm each<br>**Lamp:** 12 V LED<br>**Driver boards:** 6 to 12 V in, 55 mA |

### <a id="a10"></a>A10. 10 kΩ trim potentiometer

| | |
|---|---|
| <img src="images/parts/a10-trim-potentiometer.jpg" width="200" alt="10 kΩ trim potentiometer"> | Sets the full scale of each needle. One sits in series with each meter.<br><br>**Quantity:** ×2<br>**In version 1.0:** planned<br>**Reference:** PiShop 88<br>**Connects:** Sits between a pin of the Pi and the + terminal of a meter, with an A19 wire on each side.<br>**Value:** 10 kΩ<br>**Pins:** 3, spaced 2.54 mm |

### <a id="a11"></a>A11. USB 5 V to 12 V step-up cable

| | |
|---|---|
| <img src="images/parts/a11-step-up-cable.jpg" width="200" alt="USB 5 V to 12 V step-up cable"> | The meters' lamps need 12 V and the Pi only has 5 V. This cable takes 5 V on its USB-A plug and gives 12 V on two bare wires, red for + and black for −. Its plug goes into the socket A12, and its two wires go to the lamps of the two meters.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** SinLoon, Amazon B0F2YKGS25. It comes in a pack of 3: **the radio uses 1**.<br>**Connects:** Its USB plug goes into A12, direct. Its red and black wires go to the two holes marked AC/DC 6V-12V on each meter's driver board. Those holes take solder: it is the one place in the radio that needs it.<br>**Input:** USB-A plug, 5 V, 2 A at most<br>**Output:** 12 V, 0.8 A at most, on bare wires<br>**Length:** 88 cm |

### <a id="a12"></a>A12. USB-A socket on four jumper wires

| | |
|---|---|
| <img src="images/parts/a12-usb-a-socket-on-wires.jpg" width="200" alt="USB-A socket on four jumper wires"> | The four USB ports of the Pi are taken by the two Qualia boards, the keypad and the sound adapter. This short cable gives the step-up cable A11 a fifth USB-A socket, fed from two pins of the Pi's header. Only its red and black wires are used.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** Adafruit 4449.<br>**Connects:** Its red and black ends slide onto pins 4 and 34 of the Pi, direct. A11 plugs into its socket.<br>**Fit:** It must end in four separate sockets. A USB-A socket whose cable ends in one small 4-pin plug does not fit: the plug's contacts sit closer together than the Pi's pins, and jumper wires cannot hold in it.<br>**Socket:** USB-A female, on a 30 cm cable<br>**Wires:** Four female ends spaced 2.54 mm. Red is 5 V and goes to pin 4. Black is ground and goes to pin 34. Green and white are the data lines and stay free: their sockets are covered in plastic, so nothing needs tape.<br>**Maker's page:** https://www.adafruit.com/product/4449 |

### <a id="a13"></a>A13. MonkMakes Amplified Speaker 2

| | |
|---|---|
| <img src="images/parts/a13-speaker.jpg" width="200" alt="MonkMakes Amplified Speaker 2"> | The speaker, with its own amplifier.<br><br>**Quantity:** ×1<br>**In version 1.0:** wired<br>**Reference:** PiShop 348-1<br>**Connects:** Sound: the Pi's 3.5 mm jack, with A14. Power: pins 2 and 6 of the Pi, with two A19 wires.<br>**Power:** 3.3 to 6 V, 300 mA at most<br>**Speaker:** 8 Ω, 500 mW<br>**Input:** 3.5 mm jack<br>**Size:** 51 × 56 × 61 mm<br>**Maker's page:** https://monkmakes.com/downloads/datasheet_amp_speaker_2.pdf |

### <a id="a14"></a>A14. 3.5 mm audio cable, 30 cm, one end at a right angle

| | |
|---|---|
| <img src="images/parts/a14-audio-cable.jpg" width="200" alt="3.5 mm audio cable, 30 cm, one end at a right angle"> | Takes the sound from the Pi's jack to the speaker.<br><br>**Quantity:** ×1<br>**In version 1.0:** wired<br>**Reference:** Amazon B08F2GRHXC<br>**Connects:** From the Pi's 3.5 mm jack to the jack of the speaker A13.<br>**Plugs:** 3.5 mm male at both ends, one at 90°<br>**Length:** 30 cm |

### <a id="a15"></a>A15. Uniden BC645 CB microphone

| | |
|---|---|
| <img src="images/parts/a15-cb-microphone.jpg" width="200" alt="Uniden BC645 CB microphone"> | The hand microphone and its push-to-talk button. It plugs into the socket A16 on the face.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** Amazon B008CLIB5K<br>**Connects:** Its plug goes into the socket A16, direct.<br>**Plug:** 4 pins, female, wired the Cobra and Uniden way<br>**Cord:** Coiled, 2.4 m<br>**Button:** Push to talk |

### <a id="a16"></a>A16. GX16 4-pin socket with its wires attached

| | |
|---|---|
| <img src="images/parts/a16-microphone-socket.jpg" width="200" alt="GX16 4-pin socket with its wires attached"> | The socket on the face that the microphone A15 plugs into. It comes with four wires already attached at its back, so nothing is soldered. Pins 1 and 2 go under the screws of the plug A18. Pin 3 goes to the Pi through a lever connector A22. Pin 4 is not used.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** GX16, 4 Pin Male-Open, on Amazon B0CWF1H262.<br>**Connects:** Pin 1 wire: under screw G of A18, direct. Pin 2 wire: under screw M of A18, direct. Pin 3 wire: into a lever connector A22, then an A19 wire to pin 11 of the Pi. Pin 4 wire: cut short, not used.<br>**Pins:** 4, male, 16 mm round body with a nut<br>**Wires:** 4 wires of 20 AWG, 20 cm, attached and sealed at the back<br>**Fit:** Sellers list the GX16 4-pin as the CB microphone connector. I have not tried it with the BC645 yet: plug the microphone in before you mount the socket.<br>**Colours:** The listing does not say which colour goes to which pin. I check it on my socket when it arrives and write it here.<br>**Hole:** 16 mm. The face has a 16.2 mm hole for it. |

### <a id="a17"></a>A17. USB sound adapter with a microphone input

| | |
|---|---|
| <img src="images/parts/a17-usb-sound-adapter.jpg" width="200" alt="USB sound adapter with a microphone input"> | The Pi has a sound output but no microphone input. This adapter plugs into a USB port of the Pi and adds a 3.5 mm jack with a microphone input. The plug A18 goes into that jack.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** DuKabel, Amazon B07RS11M1T<br>**Connects:** A USB-A port of the Pi, direct, on its own cable. A18 plugs into its jack.<br>**Jack:** 3.5 mm, 4 poles (TRRS), microphone and output<br>**Standard:** CTIA<br>**Cable:** Braided, 25 cm |

### <a id="a18"></a>A18. 3.5 mm TRRS plug with screw terminals

| | |
|---|---|
| <img src="images/parts/a18-trrs-plug.jpg" width="200" alt="3.5 mm TRRS plug with screw terminals"> | A 3.5 mm plug whose four contacts end in screw terminals. The microphone's two audio wires, from the socket A16, are screwed in here, and the plug goes into the jack of the sound adapter A17. No soldering at this end.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** Amazon B08QFHHJ3Z. It comes in a pack of 2: **the radio uses 1**.<br>**Connects:** Plugs into the jack of A17, direct. The pin 1 wire of A16 goes under its screw G and the pin 2 wire under its screw M.<br>**Plug:** 3.5 mm male, 4 poles<br>**Terminals:** 4 screw terminals<br>**Length:** 32 cm |

### <a id="a19"></a>A19. Female-to-female jumper wires, 30 cm

| | |
|---|---|
| <img src="images/parts/a19-jumper-wires.jpg" width="200" alt="Female-to-female jumper wires, 30 cm"> | Join the Pi's header to the speaker's pins, to the needles and to the push-to-talk wires. A socket at each end slides onto a pin, so nothing is clipped.<br><br>**Quantity:** ×1 strip of 20<br>**In version 1.0:** wired<br>**Reference:** Adafruit 1949.<br>**Connects:** 9 of the 20: two for the speaker, three for each needle, and one for the push-to-talk button.<br>**Ends:** Female at both ends, spaced 2.54 mm<br>**Length:** 30 cm<br>**Wire:** 28 AWG, in a ribbon of 20 that peels apart<br>**Maker's page:** https://www.adafruit.com/product/1949 |

### <a id="a20"></a>A20. USB-C panel socket on a 30 cm cable

| | |
|---|---|
| <img src="images/parts/a20-usb-c-panel-socket.jpg" width="200" alt="USB-C panel socket on a 30 cm cable"> | The two sockets on the back of the case. One takes the power: the supply A2 plugs in from outside, and inside its cable goes to the switch cable A21. The other takes the PC: its cable plugs in from outside, and inside its cable goes to the DATA ONLY socket of the splitter A23.<br><br>**Quantity:** ×2<br>**In version 1.0:** planned<br>**Reference:** Adafruit 4218. Any USB-C panel socket on a cable works if it carries data, for the PC's socket.<br>**Connects:** Power: the supply A2 from outside, the switch cable A21 inside, direct. PC: the PC's cable from outside, the splitter A23 inside, direct.<br>**Ends:** USB-C female in the panel, USB-C male at the end of the cable<br>**Cable:** 30 cm<br>**Hole:** 21.5 to 27 mm across, in a panel up to 16 mm thick. The nut is about 29.5 mm across.<br>**Maker's page:** https://www.adafruit.com/product/4218 |

### <a id="a21"></a>A21. USB-C cable with a rocker switch

| | |
|---|---|
| <img src="images/parts/a21-rocker-switch-cable.jpg" width="200" alt="USB-C cable with a rocker switch"> | The master switch: one flip of its rocker cuts the power of the whole radio.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** RIITOP USB-C extension cable with on/off switch, 1 ft, Amazon B0FCS47Y8Q.<br>**Connects:** From the cable of the power socket A20 to the PWR ONLY socket of the splitter A23, direct.<br>**Ends:** USB-C female, where the cable of A20 plugs in, to USB-C male, which goes into A23<br>**Length:** 30 cm<br>**Switch:** A rocker on a small housing in the middle of the cable, like a lamp cord's<br>**Current:** 3 A at most<br>**Fit:** The housing sits inside the case and the rocker reaches through a slot in the back. The case has no slot for it yet.<br>**Seller's page:** https://www.amazon.ca/dp/B0FCS47Y8Q |

### <a id="a22"></a>A22. Lever connectors for thin wire, 3 ways

| | |
|---|---|
| <img src="images/parts/a22-lever-connectors.jpg" width="200" alt="Lever connectors for thin wire, 3 ways"> | Each lever opens a slot: push a stripped wire in and close the lever. The radio needs one: it joins the pin 3 wire of the socket A16 to an A19 jumper wire, whose other end slides onto pin 11 of the Pi.<br><br>**Quantity:** ×1 pack of 50<br>**In version 1.0:** planned<br>**Reference:** XHF2018 3-way lever connectors, Amazon B07H76HDBL, a pack of 50: **the radio uses 1**.<br>**Connects:** Joins the pin 3 wire of A16 to an A19 wire whose socket end goes on pin 11 of the Pi.<br>**Wire:** 0.08 to 2.5 mm², which is 28 to 12 AWG. Wago 221 connectors start at 24 AWG and do not hold the thin A19 wires.<br>**Ways:** 3 slots, joined inside |

### <a id="a23"></a>A23. USB-C power and data splitter

| | |
|---|---|
| <img src="images/parts/a23-power-data-splitter.jpg" width="200" alt="USB-C power and data splitter"> | It plugs into the Pi's USB-C port and keeps the power and the data of that port apart. The supply feeds one side, the PC the other, and only the ground is shared. Without it, a PC on the Pi's USB-C port would have to power the radio, and a PC's port cannot.<br><br>**Quantity:** ×1<br>**In version 1.0:** planned<br>**Reference:** PiKVM USB Power/Data Splitter.<br>**Connects:** Its plug goes into the Pi's USB-C port. Its PWR ONLY socket takes the switch cable A21. Its DATA ONLY socket takes the cable of the PC's socket A20.<br>**Ends:** USB-C male into the Pi, two USB-C female sockets marked PWR ONLY and DATA ONLY<br>**Current:** 3 A at most<br>**Use:** Made for a Raspberry Pi 4 used as a USB device. The radio's PC link is not built or tested yet.<br>**Maker's page:** https://pikvm.org/new/ |

## Tools

Nothing is soldered and nothing is taped. You need small scissors and a small screwdriver. A18 comes with one. [WIRING.md](WIRING.md#the-microphone-and-its-push-to-talk-button) shows the
microphone's wiring step by step.

## Where I bought them, in Canada

I live in Canada and bought the parts from these stores. I cannot say what is sold in your country. Where a part
comes from a maker such as Adafruit, Raspberry Pi or MonkMakes, the maker's own page lists its sellers around the
world.

| No. | Store | Page |
|---|---|---|
| **A1** | PiShop | <https://www.pishop.ca/product/raspberry-pi-4-model-b-1gb/> |
| **A2** | PiShop | <https://www.pishop.ca/product/raspberry-pi-15w-power-supply-us-black/> |
| **A3** | Amazon.ca | <https://www.amazon.ca/dp/B08KSSXKYR> |
| **A4** | Digi-Key | <https://www.digikey.ca/en/products/result?keywords=1528-5447-ND> |
| **A5** | Digi-Key | <https://www.digikey.ca/en/products/result?keywords=1528-5799-ND> |
| **A6** | Digi-Key | <https://www.digikey.ca/en/products/result?keywords=1528-5800-ND> |
| **A7** | PiShop | <https://www.pishop.ca/product/usb-type-c-to-usb-2-0-a-male-cable-3ft/> |
| **A8** | Amazon.ca | <https://www.amazon.ca/dp/B0DN9T9J75> |
| **A9** | Amazon.ca | <https://www.amazon.ca/dp/B0GV1VC7PZ> |
| **A10** | PiShop | <https://www.pishop.ca/product/breadboard-trim-potentiometer-10k/> |
| **A11** | Amazon.ca | <https://www.amazon.ca/dp/B0F2YKGS25> |
| **A12** | Digi-Key | <https://www.digikey.ca/en/products/result?keywords=adafruit%204449> |
| **A13** | PiShop | <https://www.pishop.ca/product/amplified-speaker-2-for-raspberry-pi-arduino/> |
| **A14** | Amazon.ca | <https://www.amazon.ca/dp/B08F2GRHXC> |
| **A15** | Amazon.ca | <https://www.amazon.ca/dp/B008CLIB5K> |
| **A16** | Amazon.com | <https://www.amazon.com/dp/B0CWF1H262> |
| **A17** | Amazon.ca | <https://www.amazon.ca/dp/B07RS11M1T> |
| **A18** | Amazon.ca | <https://www.amazon.ca/dp/B08QFHHJ3Z> |
| **A19** | Digi-Key | <https://www.digikey.ca/en/products/result?keywords=adafruit%201949> |
| **A20** | Digi-Key | <https://www.digikey.ca/en/products/result?keywords=adafruit%204218> |
| **A21** | Amazon.ca | <https://www.amazon.ca/dp/B0FCS47Y8Q> |
| **A22** | Amazon.com | <https://www.amazon.com/dp/B07H76HDBL> |
| **A23** | PiShop | <https://www.pishop.ca/product/pikvm-usb-power-data-splitter/> |

## Where the pictures come from

The pictures of the parts are the product pictures of their makers and sellers. They belong to their owners and
are here to identify the parts. They are not covered by this repository's licence
([LICENSE-MEDIA.md](../LICENSE-MEDIA.md)).
