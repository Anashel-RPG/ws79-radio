# Setup

The setup has three parts: the card, the first start and the installation. The first happens on your computer, and
the last happens on the Pi over SSH.

## The card

### Writing the system

Open Raspberry Pi Imager. Choose **Raspberry Pi 4** as the device, **Raspberry Pi OS (64-bit)** as the system and your
card as the storage, then write. Imager offers to set a name, a user and a Wi-Fi network. Skip those pages, because
the utility below sets the same things and checks them afterwards.

Imager ejects the card when it is done. Take the card out and put it back in, so your computer shows its `bootfs`
drive again.

### Running the utility

```bash
python3 setup/setup_sd.py
```

On Windows, open a terminal in this folder and run `py setup\setup_sd.py`.

The utility finds the card by itself. It then asks five questions and proposes an answer for most of them.

| Question | What it sets |
|---|---|
| Name of the Pi on your network | The Pi answers to this name followed by `.local`. The default is `ws79`. |
| User name on the Pi | The account you log in with. The default is `pi`. |
| Wi-Fi network | The utility lists the networks your computer knows. Type a number, or type the name. To keep that list off a shared screen, start the utility with `--no-wifi-list` and type the name. |
| Country of the Wi-Fi | Two letters. The Pi keeps its Wi-Fi off until it has a country. |
| Time zone | The default is your computer's own. |

It shows the five answers and asks if they are right. After that it asks for the Wi-Fi password, twice, then looks
for your SSH key.

- **With an SSH key**, you log in from your computer with the key, and the Pi refuses passwords over SSH. The utility
  offers to set a password for the user. That password only serves at a keyboard and a screen plugged into the Pi.
- **Without an SSH key**, the utility asks for a password of at least 8 characters, and the Pi accepts it over SSH
  from your network. Choose a long one.

In both cases the user runs `sudo` on the Pi without typing a password.

The last lines are a list of checks read back from the card, then `CHECK PASSED`. The utility ejects the card on a
Mac and on Linux. On Windows, eject it yourself.

### What the utility stores

| On the card | Kept on your computer |
|---|---|
| The hash of the user's password | The password itself |
| The Wi-Fi key derived from the network name and its password | The Wi-Fi password |
| The public half of your SSH key | The private half |

The Wi-Fi key is enough to join that one network, and the hash can be tested against guessed passwords. Keep the
card as you would keep the Wi-Fi password.

The utility reads `~/.ssh/id_ed25519`. When your computer has no key, it offers to create one, and `ssh-keygen` asks
you for a passphrase. The utility derives the public key from the private key. It does not trust the `.pub` file
beside it, because a `.pub` file that no longer matches its key makes the Pi refuse every login. A key with a
passphrase cannot be read that way, so the utility then uses the `.pub` file as it is and says so.

If your computer already knows a machine with the Pi's name, the utility removes that entry from
`~/.ssh/known_hosts` and says so. The card gives the Pi a new identity, and `ssh` would refuse to connect to it under
the old one. `ssh-keygen` keeps the file as it was beside it, as `known_hosts.old`.

The utility sends nothing over the network.

The utility also works on a card that has already started once. Run it again to move the Pi to another Wi-Fi network
or to change its user, and the Pi applies the new files at its next start.

## The first start

Put the card in the Pi and plug in the power. On its first start the Pi grows its system to fill the card, applies
your settings and restarts once. It is ready when it answers on the network:

```bash
ssh pi@ws79.local
```

Use the user and the name you chose. Your computer asks once if you trust this new machine. Answer yes.

## The installation

Plug the screen board, the keypad and the speaker into the Pi before this step, because the installer programs the
keypad and the screen board over USB.

Copy this folder to the Pi, then run the installer there:

```bash
scp -r ws79-radio pi@ws79.local:
ssh pi@ws79.local
./ws79-radio/pi/install.sh
```

If the Pi has `git`, cloning the repository on the Pi does the same as the copy.

The installer works in five steps and says which one it is on.

| Step | What it does |
|---|---|
| 1 | Installs the system packages the radio program needs. |
| 2 | Copies the program and its sounds to `/opt/ws79`, installs the `ws79` service and sets the audio jack to full level. |
| 3 | Downloads the keypad tool, then programs the keypad: six keys, the knob as volume, the light on. |
| 4 | Installs CircuitPython on the screen board when it has none, then its libraries, the artwork and the screen program. It ends with a full restart of the board. |
| 5 | Starts the radio. |

Step 4 erases a screen board that has no CircuitPython yet. The installer says so and waits for you to type `yes`.
Any other answer leaves the board as it is, and so does a run with no one at the keyboard. When the board already
runs CircuitPython with another program, the installer keeps that program on the board as
`code-before-ws79-<date>.py` before it copies the radio's.

The keypad tool and the CircuitPython image each have a fixed version and a checksum written in the script, and the
installer stops if either file differs. `esptool` and `circup` have a fixed version. The system packages and the
CircuitPython libraries are the current ones on the day you run the installer.

The installer needs the internet each time it runs. If a step fails, it starts the radio again with what is already
installed, and you can run it again. If your connection to the Pi drops while it runs, connect again and run it
again.

A part that is not plugged in is skipped with a message. Plug it in and run the installer again: it skips what is
already done. Run it again as well after you change a sound, a key or the screen program, since it copies the files
from this folder to the Pi and to the screen board.

## Day-to-day commands

| To | Run on the Pi |
|---|---|
| See if the radio is running | `systemctl status ws79` |
| Read what the program says | `journalctl -u ws79 -n 30` |
| Restart the radio | `sudo systemctl restart ws79` |
| Stop it until the next start | `sudo systemctl stop ws79` |
| Turn the Pi off before unplugging it | `sudo poweroff` |
