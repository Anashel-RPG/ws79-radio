# Changes

## 1.0.0 (15 November 2026)

The first public version: the bench build, with a Raspberry Pi 4, one bar screen, the keypad and the speaker.

**What it includes**

- The radio program for the Pi. It shows its start on the screen, plays one transmission per key, stops it on the
  same key, sets the volume from the knob and sends the screen the spectrum of the sound that is playing.
- The screen program for the Qualia board. It draws the channel, a spectrum of 92 bars with peak dots and a marker on
  the tuned channel, in four colours.
- A card utility for Mac, Windows and Linux that sets the Pi's name, user, Wi-Fi and SSH key and checks what it
  wrote.
- An installer for the Pi that sets up the program, the keypad and the screen board in one pass. It asks before it
  erases a screen board. This version of the radio was installed with it on the first Pi and checked there: a steady
  screen, the six keys with their sounds, the knob, and a start by itself after a restart of the Pi.
- The parts list, with a picture and a sheet for each of the 21 parts.
- The wiring guide: the bench build with photos, the pins of the Pi, and the wiring plan of the whole radio with its
  drawings.
- The setup guide, an explanation of how the radio works and a list of problems with their fixes.
- Draft case files in STL and 3MF, with their plans: every opening of the face, each part to print and what the
  inside must hold. A script draws the plans and their tables from the print files.
- The Blender model and its renders.
- Stills from the demo video of the bench build, and a link to the video.
- 80 automated tests that run both programs, the card utility and the installer on a computer.

**What is not done yet**

- The installer has not run on a new card. It ran three times on the first Pi, which already had its system
  packages: on the radio as it was, on a screen board erased and waiting in its loader, and once more as a plain
  second run. A screen board fresh from the factory takes another way into its loader, done by hand once.
- The card utility has not set up a Pi from start to finish, and has not run on Windows or Linux.
- The case files have not been sliced or printed, and the inside of the case is not drawn.
- The meters, the microphone and the second screen are not wired.
