# How the radio works

Two programs make the radio. One runs on the Raspberry Pi and decides what happens. The other runs on the screen
board and draws. They talk over the USB cable between them, one line of text at a time.

```
  keypad ──USB──▶ ┌──────────────────┐ ──3.5 mm jack──▶ speaker
                  │  Raspberry Pi    │
                  │  pi/ws79.py      │ ──USB serial──▶ ┌────────────────┐ ──ribbon──▶ bar display
                  └──────────────────┘                 │  Qualia board  │
                                                       │ screen/code.py │
                                                       └────────────────┘
```

## The program on the Pi

`pi/ws79.py` runs as a service named `ws79`, from `/opt/ws79`. The service starts it with the Pi and starts it again
if it stops.

At start it sets the audio jack to full level, waits for a network, loads the five sounds and works out the spectrum
of each one. It then reads the keypad. The keypad looks like a USB keyboard to the Pi: its six keys send F13 to F18
and its knob sends the volume keys. The program reads those keys directly from the keypad, so they reach it with no
screen or desktop session.

The sound goes out through the Pi's 3.5 mm jack. The program does not need the network to work. It waits for one at
start only to show the Pi's address on the screen, and it runs offline when none comes.

## The messages to the screen

Each message is one line of text that ends with a line feed.

| Message | Meaning |
|---|---|
| `S|text` | Show a status line: the start, the network, READY. |
| `F|27.185|CH 19  POACHER` | Show the radio view on a channel. The frequency chooses the artwork and the name after the two spaces is written above the bars. |
| `P|` followed by 92 characters | One frame of spectrum. Each character is a level from 0 to 63, written as the character with code 48 plus the level. |
| `V|85` | Show the volume for a moment. |
| `T|next` | Change to the next colour. |

## The spectrum

The Pi works out each sound's spectrum once, at start, so a key press costs nothing. It cuts the sound into 20 frames
a second and measures 92 bands in each frame, from 120 Hz to 9 kHz on a logarithmic scale. While a sound plays, a
second thread sends the frame that matches the time elapsed, which keeps the bars in step with the audio.

## The program on the screen board

`screen/code.py` is a CircuitPython program. The board runs the file named `code.py` at the root of its drive.

The picture has three layers. The first is the artwork: the channel cell, the axis, the frequency labels and the
marker. It comes from the pictures in `screen/screens/`, loaded once at start. The second is the 92 bars. The third is
the text above the bars.

The board is slow at moving pixels, and two choices follow from that.

- **Each bar is its own small picture.** When a bar moves, the program repaints only the rows that changed, and the
  display refreshes only those. Painting the whole spectrum each frame ran at 2 frames a second on this board.
- **A channel change repaints two small parts.** The channel cell and the marker are separate pictures laid over the
  base artwork, so tuning does not reload the whole screen.

The frame rate is capped at 30 a second, and the display's clock is lowered from 16 MHz to 12 MHz
(`screen/lib-patch/bar240x960.py`). I added both while chasing a picture that rolled. What made the picture stable
in the end was a full restart of the board after each change of its program, which the installer now does. I kept the
two settings because the build that works has them, and I have not tested the radio without them.

## What you can change

Run `./pi/install.sh` on the Pi after any of these changes. It copies the files to their place and restarts the radio.

### A sound

Replace a file in `pi/sounds/` with a WAV file of the same name, 16-bit, mono or stereo. To use another name, change
it in `CHANNELS` at the top of `pi/ws79.py`. Loud files work best on the small speaker. This command brings a
recording to the level of the five that ship:

```bash
ffmpeg -i in.mp3 -ac 1 -ar 44100 -af loudnorm=I=-12:TP=-1:LRA=11 -map_metadata -1 out.wav
```

### What a key plays

`CHANNELS` in `pi/ws79.py` gives each key a frequency, a label and a sound. The label is `CH`, the channel number,
two spaces, then the name shown above the bars.

### A new channel

A channel needs its artwork. Add its number and frequency to `CHANNELS` in `tools/gen_screens.py` and run the tool
(it needs Pillow). Add the same frequency to `FREQ_TO_CH` in `screen/code.py`, then use it in `pi/ws79.py`.

### The colours

`THEMES` in `screen/code.py` lists the colours key 6 steps through. Each one is a name and a red, green, blue value.
The screen keeps one hue at several brightnesses, so one value recolours everything.

### The keypad's direction

The radio mounts the keypad turned end for end, with its knob on the left. To use it the other way, with the knob on
the right, set `KEYPAD_TURNED = False` in `pi/ws79.py`.

## The tests

```bash
python3 -m unittest discover -s tests
```

The tests need `numpy`, `pygame` and `Pillow` on your computer. `tests/fake_pi.py` stands in for the keypad, the
serial port and the sound card. `tests/fake_circuitpython.py` stands in for the display modules of CircuitPython and
can compose the picture the screen would show. With them, both programs run on a computer: change a key or a
message, run the tests, and you know what the hardware will do before you touch it.
