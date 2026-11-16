# Changes

## Since 1.0.0

These changes are in the guides only. The programs are those of 1.0.0.

- The parts list labels its parts A1 to A21, gives each one a quantity, and lists each part once with its quantity:
  two displays, two Qualia boards, three USB-A to USB-C cables.
- The crocodile clip leads did not hold on the Pi's pins. Female-to-female jumper wires (A19) replace them.
- The radio now takes its power from the Pi's own 5.1 V 3 A supply (A2), through a USB-C socket on the back (A20) and a
  switch cable that is the master switch (A21). The USB-C cable to a computer is no longer in the list.
- The microphone socket for the face has a reference, the Workman C-4P (A16), and every part has a picture.
- The wiring guide explains the power path, and the wiring drawings use the new labels.
- Nothing needs soldering. The microphone socket A16 is now a GX16 socket sold with its wires attached, and two lever
  connectors (A22) join its push-to-talk wires to jumper wires.
- The parts list is now `docs/PARTS-BOM.md`. It ends with the Canadian stores where I bought each part, and the master
  switch A21 is now one sold in Canada.
- The wiring drawings show a picture of every part, the Pi included. The speaker and the meters' lamps have a drawing
  each.
- The repository has a contributing guide, a security policy, a code of conduct, two issue forms and a pull request
  template, in `.github/`.

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
