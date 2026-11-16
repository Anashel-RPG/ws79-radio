# Security

The WS-79 is a hobby build, and some of its code handles secrets. Please report a security problem privately, not in
a public issue.

## How to report

Use **Report a vulnerability** on the [Security tab](https://github.com/Anashel-RPG/ws79-radio/security/advisories/new)
of this repository. Only I see the report. Say which file and which version, what someone could do, and how to repeat
it. I will answer there.

## What is worth a report

- **`setup/setup_sd.py`**, the card utility. It takes a user's password and the Wi-Fi password on your computer. It
  writes to the card the hash of the user's password, the Wi-Fi key derived from the Wi-Fi password, and the public
  half of an SSH key. A way to make it write a password in clear, send anything over the network, or touch a private
  key is a security problem.
- **`pi/install.sh`**, the installer. It runs on the Pi, calls `sudo`, and downloads CircuitPython, a keypad tool and
  Python libraries. Each download it makes itself is checked against a SHA-256 recorded in the script. A way around
  those checks, or a way to make it run something it did not intend, is a security problem.
- **`pi/ws79.py` and its service**, the radio program that runs at each start of the Pi.

A part that overheats, a short circuit in the wiring guide or a wrong value in the parts list is a safety problem.
Open an issue for those, so other builders see it.

## Versions

I fix the latest release. The radio has no automatic update: a fix reaches a radio when its owner copies the new
version to the Pi and runs `pi/install.sh` again.
