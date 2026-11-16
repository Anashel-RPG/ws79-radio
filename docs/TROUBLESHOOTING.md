# Troubleshooting

These are the problems I ran into while building the first radio, with what fixed each one.

## The card

### Imager says the verification failed, or that it cannot read the storage

I got both messages with the SD slot built into a Mac. The card was not the cause: a full write and read test of the
card found no error. What worked for me was writing the same image to the same card with the `dd` command in place of
Imager. `dd` writes to whatever disk you name, so use it only if you know how to tell the card's disk from your own.
A USB card reader is the other thing to try. I have not tested one.

### The utility says the card does not read these first-start files

The card holds an older Raspberry Pi OS, or another system. Write the current Raspberry Pi OS (64-bit) with Raspberry
Pi Imager, then run the utility again.

### The utility does not find the card

Take the card out and put it back in, then press Enter. If your computer shows the `bootfs` drive and the utility
still does not see it, give it the path: `python3 setup/setup_sd.py --card /path/to/bootfs`.

## The network

### The Pi does not appear on the network

Give the first start time to finish: the Pi restarts once before it joins the Wi-Fi. If it still does not answer, the
Wi-Fi name or password on the card is the usual cause. Put the card back in your computer and run
`setup/setup_sd.py` again. It works on a card that has already started.

Two more things to check. The first is the Wi-Fi country, because the Pi keeps its Wi-Fi off without one. The second
is the network's security: the card stores a WPA2 key, and a network set to WPA3 only refuses it.

### `ws79.local` does not answer and the Pi is on

Some networks do not pass `.local` names. Find the Pi's address in your router's list of devices and use it in place
of the name: `ssh pi@192.168.1.23`. The radio also shows its address on the screen at each start.

### The Pi stops answering for a few minutes, then comes back

This happened to me once, a minute after an install had ended. The Pi stayed on. Its log showed my Wi-Fi router
asking it to move to another access point, and its Wi-Fi failing the move. It reconnected by itself about five
minutes later. On the Pi, `journalctl -b -u wpa_supplicant` shows such a moment as lines that hold
`WNM: Disassociation Imminent`. If your connection drops while the installer runs, connect again and run the
installer again.

### SSH says « Permission denied (publickey) »

The Pi does not have the public half of the key your computer is using. The usual cause is a `.pub` file that no
longer matches its private key. Run `setup/setup_sd.py` again on the card: it derives the public key from the
private key and tells you when the `.pub` file differs.

### SSH says « Host key verification failed » or warns that the host identification has changed

You set this Pi up again, so it has a new identity and your computer remembers the old one. The card utility
removes the old one when it writes a card. After any other kind of setup, remove it yourself:

```bash
ssh-keygen -R ws79.local
```

## The sound

### No sound at all

Check the speaker's power first. Its small light is on when it has power. The audio cable brings the sound only: the
amplifier takes its power from pins 2 and 6 of the Pi ([WIRING.md](WIRING.md)).

Then check that the radio is running: `systemctl status ws79`. Until the screen shows the radio view, the program is
still starting and does not read the keys.

### The sound is very quiet

The Pi's jack sometimes starts at a low level. The radio program sets it to full at each start, so restart the radio:
`sudo systemctl restart ws79`. Turn the knob to the right as well: the volume shows on the screen as you turn.

### A clip slips off or touches two pins of the speaker

Crocodile clips are wider than the gap between the pins, and they do not hold. Use female-to-female jumper wires
(A19 in [the parts list](BOM.md)): one socket slides onto the Pi's pin and the other onto the speaker's pin.

## The keypad

### Every key does the same thing, or nothing happens

The keypad has not been programmed. Out of the box its keys send the same letter. Run `./pi/install.sh` with the keypad
plugged in, and read the line of step 3.

### The keys are in the wrong order

The program expects the keypad turned end for end, knob on the left. For a keypad mounted the other way, set
`KEYPAD_TURNED = False` in `pi/ws79.py` and run the installer again.

### The screen says KEYPAD NOT FOUND

The keypad is unplugged or its cable only delivers power. The program keeps looking and goes on by itself when the
keypad appears.

## The screen

### The screen shows moving colours and never the radio

That is the test picture the board ships with. The board has no CircuitPython yet. Run `./pi/install.sh` with the
board plugged in.

### The screen stays on BOOTING

The screen program is running and the Pi is not talking to it. Check that the radio is running on the Pi
(`systemctl status ws79`) and that the cable between the Pi and the board is a data cable.

### The whole picture rolls or blinks

This happened to me after the screen program restarted by itself, and never after a full restart of the board.
Unplug the board's USB cable and plug it back in, or run the installer again: it ends with a full restart of the
board.

### The screen shows an error in small white text

The screen program stopped, and the board is showing why. The last lines name a line of `code.py`. If you changed
that file, the error is there. Run the tests on your computer to find it, then run the installer again.

### The installer cannot put CircuitPython on the board

The installer sends the board to its loader by itself, and that worked on my board. When it says the board did not
go to its loader, put it there by hand. Adafruit's guide for this board gives the way: hold the **Boot0** button,
press and release **Reset**, then release **Boot0**. I did not need it, so I have not tried it. Run the installer
again after that.

The installer also stops, without erasing anything, when two boards are waiting in their loader at the same time.
Unplug the one that is not the screen board.

## The radio program

### See what it is doing

```bash
systemctl status ws79
journalctl -u ws79 -n 30
```

### Start over cleanly

Run `./pi/install.sh` again. It copies every file to its place again, programs the keypad, refreshes the screen
board and restarts the radio.
