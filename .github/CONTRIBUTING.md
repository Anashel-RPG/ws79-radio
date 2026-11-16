# Contributing

The WS-79 is the radio I build for The Black Watchmen. Reports from other builders are the most useful thing you can
send: what you built, what worked, and where the guides were wrong.

## Reports

Open an issue with one of the two forms.

- **Something does not work**: a step of the guides, the installer, a program or a part. Say which part, which step,
  and paste what the screen or the terminal showed.
- **A question about the build**: anything the guides do not answer.

Before you paste a log or a picture, remove your Wi-Fi name and password, your SSH keys and your home address.

## Changes

Small fixes are welcome as pull requests: a wrong value in the parts list, a step of a guide, a bug in a program.
For a bigger change, a new part or a change to the case, open an issue first so we agree on it before you spend the
time.

Before you open a pull request:

1. Run the tests: `python3 -m unittest discover -s tests`. They need `numpy`, `pygame` and `Pillow`.
2. Say what you tried on real hardware, and what you only tried on a computer.
3. Check that your pictures hold no location or camera data, and that no file holds a password, a key or a local
   path.

The design of the radio, its look and its story stay mine. I may keep a change for a later version, or decline it.

## Licence

The code you send comes under the MIT licence in [LICENSE](../LICENSE). Pictures, drawings, sounds and case files
come under [LICENSE-MEDIA.md](../LICENSE-MEDIA.md). Send only what you made yourself or have the right to share.
