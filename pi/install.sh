#!/bin/bash
# WS-79: install everything on the Raspberry Pi. Run it on the Pi, from the repository folder:
#
#     ./pi/install.sh
#
# It installs the radio program and its service, programs the keypad, and sets up the screen board
# (CircuitPython, its libraries, the artwork and the screen program). Each step checks what is already done,
# so the script can run again at any time, for example after plugging in a part that was missing.
#
# One step destroys something: putting CircuitPython on a screen board erases that board. The script asks before
# it does that, and it goes on only when you type yes.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ME="$(id -un)"
TOOLS="$HOME/.ws79-tools"

# What this script downloads:
# - The CircuitPython image and the keypad tool are installed as they are. Each has a fixed version and a checksum,
#   and a file that differs is refused.
# - esptool and circup have a fixed version. pip chooses the versions of the packages they depend on.
# - The system packages and the CircuitPython libraries that circup installs are the current ones on the day you
#   run this.
CP_VERSION="10.3.2"
CP_BOARD="adafruit_qualia_s3_rgb666"
CP_URL="https://downloads.circuitpython.org/bin/$CP_BOARD/en_US/adafruit-circuitpython-$CP_BOARD-en_US-$CP_VERSION.bin"
CP_SHA256="1ac2db646b0715373389e39483ef3b056db0133a8c9cd50a3cf9969cc2993bfa"
CH57X_VERSION="v1.7.0"
CH57X_URL="https://github.com/kriomant/ch57x-keyboard-tool/releases/download/$CH57X_VERSION/ch57x-keyboard-tool-aarch64-unknown-linux-gnu.tar.gz"
CH57X_SHA256="565958f1732d064905a96bc1b0daabd03f7e5baf1fcca76f834bc2b3efe266ab"
ESPTOOL_VERSION="5.6.0"
CIRCUP_VERSION="3.1.0"

tmp=""              # what cleanup() puts back in order, whatever happens: a temporary folder, a drive this script
drive=""            # mounted, and the radio if this script stopped it and did not get to start it again
mounted_here=""
radio_stopped=""

cleanup() {
    [ -n "$mounted_here" ] && sudo umount "$drive" 2>/dev/null
    [ -n "$tmp" ] && rm -rf "$tmp"
    [ -n "$radio_stopped" ] && sudo systemctl start ws79 2>/dev/null
    return 0
}
trap cleanup EXIT

say() { printf "\n== %s\n" "$1"; }

matches() {         # matches <file> <sha256>: true when the file is the one recorded in this script
    echo "$2  $1" | sha256sum -c --quiet - >/dev/null 2>&1
}

fetch() {           # fetch <url> <sha256> <file>: download the file unless it is already there, refuse any other file
    matches "$3" "$2" && return 0
    curl -fsSL -o "$3" "$1"
    if ! matches "$3" "$2"; then
        rm -f "$3"
        echo "The file from $1 does not match its recorded checksum. Nothing was installed from it."
        exit 1
    fi
}

confirm() {         # confirm <question>: true only when the person at the keyboard types yes
    local answer=""
    if [ ! -t 0 ]; then
        echo "$1? That needs an answer typed at the keyboard, and this script is not running in a terminal."
        return 1
    fi
    read -r -p "$1? Type yes to go on: " answer || true
    [ "$answer" = "yes" ]
}

usb_has() {         # usb_has <vendor:product>: true when that USB device is plugged in
    case "$(lsusb 2>/dev/null)" in *"ID $1"*) return 0 ;; *) return 1 ;; esac
}

screen_port() { ls /dev/serial/by-id/*Qualia* 2>/dev/null | head -1 || true; }
circuitpy_partition() { lsblk -o NAME,LABEL -rn | awk '$2=="CIRCUITPY"{print $1}' | head -1; }

# An ESP32-S3 waiting in its built-in loader shows up as USB 303a:1001. It shows up as 303a:0009 when a program
# that used the USB port itself, such as CircuitPython, sent it there.
loader_plugged_in() { usb_has "303a:1001" || usb_has "303a:0009"; }

loader_ports() {    # the serial ports of the ESP32-S3 chips waiting in their built-in loader, one per line
    local tty usb
    for tty in /sys/class/tty/ttyACM*; do
        usb="$tty/device/.."
        [ -r "$usb/idVendor" ] || continue
        if [ "$(cat "$usb/idVendor")" = "303a" ]; then
            case "$(cat "$usb/idProduct")" in
                1001|0009) echo "/dev/${tty##*/}" ;;
            esac
        fi
    done
}

if [ "$(id -u)" = "0" ]; then
    echo "Run this as your own user, without sudo. It asks for sudo itself where it needs it."
    exit 1
fi
if ! grep -qs "Raspberry Pi" /proc/device-tree/model; then
    echo "This does not look like a Raspberry Pi. The script is meant to run on the Pi itself."
    exit 1
fi

say "1 of 5: system packages"
sudo apt-get update -qq
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    python3-pygame python3-evdev python3-serial python3-numpy python3-venv alsa-utils curl >/dev/null
echo "done"

say "2 of 5: the radio program (/opt/ws79) and its service"
sudo systemctl stop ws79 2>/dev/null || true
radio_stopped="yes"
sudo mkdir -p /opt/ws79
sudo rm -rf /opt/ws79/sounds
sudo cp "$REPO/pi/ws79.py" /opt/ws79/
sudo cp -r "$REPO/pi/sounds" /opt/ws79/
sudo chown -R "$ME:" /opt/ws79
sed "s/__USER__/$ME/g" "$REPO/pi/ws79.service" | sudo tee /etc/systemd/system/ws79.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable ws79 >/dev/null 2>&1
amixer -q -c Headphones sset PCM 100% unmute 2>/dev/null || true     # the 3.5 mm jack at full level
sudo alsactl store 2>/dev/null || true
echo "done"

say "3 of 5: the keypad (SinLoon, 6 keys and a knob, USB 1189:8890)"
if ! command -v ch57x-keyboard-tool >/dev/null; then
    tmp="$(mktemp -d)"
    fetch "$CH57X_URL" "$CH57X_SHA256" "$tmp/ch57x.tgz"
    tar xzf "$tmp/ch57x.tgz" -C "$tmp"
    sudo install -m 755 "$(find "$tmp" -type f -name ch57x-keyboard-tool | head -1)" /usr/local/bin/ch57x-keyboard-tool
    rm -rf "$tmp"
    tmp=""
fi
if usb_has "1189:8890"; then
    sudo ch57x-keyboard-tool upload < "$REPO/pi/keypad.yaml"
    sudo ch57x-keyboard-tool led 1
    echo "keypad programmed: keys F13 to F18, knob as volume, light on"
else
    echo "The keypad is not plugged in. Skipped: plug it in and run this script again."
fi

say "4 of 5: the screen board (Adafruit Qualia ESP32-S3 with the 3.7 in bar)"
board="ready"
if [ -z "$(screen_port)" ] && [ -z "$(circuitpy_partition)" ] && ! loader_plugged_in; then
    echo "The screen board is not plugged in. Skipped: plug it in and run this script again."
    board="skipped"
fi

if [ "$board" = "ready" ]; then
    [ -x "$TOOLS/bin/pip" ] || python3 -m venv "$TOOLS"
    "$TOOLS/bin/pip" install -q "esptool==$ESPTOOL_VERSION" "circup==$CIRCUP_VERSION"
    for _ in 1 2 3 4 5; do                           # a board that was just plugged in takes a moment to show its drive
        [ -n "$(circuitpy_partition)" ] && break
        sleep 1
    done
fi

if [ "$board" = "ready" ] && [ -z "$(circuitpy_partition)" ]; then
    echo "The board shows no CIRCUITPY drive: it has no CircuitPython yet, or its drive is switched off."
    echo "Installing CircuitPython $CP_VERSION erases everything that is on the board."
    if confirm "Erase the screen board and install CircuitPython"; then
        bin="$TOOLS/circuitpython-$CP_VERSION.bin"
        fetch "$CP_URL" "$CP_SHA256" "$bin"
        port="$(screen_port)"
        if [ -n "$port" ]; then                      # opening the port at 1200 baud sends the board to its loader
            stty -F "$port" 1200 || true
            sleep 6
        fi
        loaders="$(loader_ports)"
        case "$(printf '%s\n' "$loaders" | grep -c . || true)" in
            1)
                "$TOOLS/bin/esptool" --chip esp32s3 --port "$loaders" erase-flash
                "$TOOLS/bin/esptool" --chip esp32s3 --port "$loaders" write-flash -z 0x0 "$bin"
                for _ in $(seq 1 30); do
                    [ -n "$(circuitpy_partition)" ] && break
                    sleep 2
                done
                ;;
            0)
                echo "The board did not go to its loader, so nothing was erased."
                echo "Unplug the board, plug it back in and run this script again. docs/TROUBLESHOOTING.md gives"
                echo "the way to put the board in its loader by hand."
                board="skipped"
                ;;
            *)
                echo "More than one board is waiting in its loader, and this script cannot tell which is the screen board."
                echo "Nothing was erased. Unplug the other boards and run this script again."
                board="skipped"
                ;;
        esac
    else
        echo "The board is left as it is. Run this script again when you want to set it up."
        board="skipped"
    fi
fi

if [ "$board" = "ready" ]; then
    part="$(circuitpy_partition)"
    if [ -z "$part" ]; then
        echo "The board's CIRCUITPY drive did not appear. Unplug the board, plug it back in, and run this script again."
        exit 1
    fi
    drive="$(lsblk -no MOUNTPOINT "/dev/$part" | head -1)"
    if [ -z "$drive" ]; then
        drive="/mnt/ws79-circuitpy"
        sudo mkdir -p "$drive"
        sudo mount -o "uid=$(id -u),gid=$(id -g)" "/dev/$part" "$drive"
        mounted_here="yes"
    fi
    "$TOOLS/bin/circup" --path "$drive" install adafruit_qualia adafruit_display_text adafruit_imageload >/dev/null
    displays="$drive/lib/adafruit_qualia/displays"
    rm -f "$displays/bar240x960.mpy"                 # replaced by the same driver set to a 12 MHz panel clock
    cp "$REPO/screen/lib-patch/bar240x960.py" "$displays/"
    mkdir -p "$drive/screens"
    cp "$REPO"/screen/screens/*.bmp "$drive/screens/"
    # A program that is not this radio's is kept under another name. CircuitPython's own first program is not kept.
    if [ -f "$drive/code.py" ] && ! grep -q "WS-79" "$drive/code.py" \
            && [ "$(tr -d '\r\n' < "$drive/code.py")" != 'print("Hello World!")' ]; then
        kept="code-before-ws79-$(date +%Y%m%d-%H%M%S).py"
        cp "$drive/code.py" "$drive/$kept"
        echo "The board already held a program. It is kept on the board as $kept."
    fi
    cp "$REPO/screen/code.py" "$drive/code.py"
    sync
    sleep 2
    if [ -n "$mounted_here" ]; then
        sudo umount "$drive"
        mounted_here=""
    fi

    # Restart the board fully. After a plain reload the picture can roll; after a full restart it is stable.
    python3 - <<'PY'
import glob, time
import serial
ports = glob.glob("/dev/serial/by-id/*Qualia*")
if ports:
    p = serial.Serial(ports[0], 115200, timeout=0.3)
    p.write(b"\x03"); time.sleep(0.5)
    p.write(b"\x03"); time.sleep(0.5)
    p.read(100000)
    p.write(b"\r\nimport microcontroller; microcontroller.reset()\r\n")
    time.sleep(1)
PY
    for _ in $(seq 1 20); do
        sleep 2
        [ -n "$(screen_port)" ] && break
    done
    if [ -n "$(screen_port)" ]; then echo "screen board ready"; else echo "The screen board did not come back. Unplug it and plug it back in."; fi
fi

say "5 of 5: start"
radio_stopped=""
sudo systemctl restart ws79
sleep 3
if systemctl is-active --quiet ws79; then
    echo "The WS-79 is running. It starts by itself every time the Pi powers on."
else
    echo "The program did not start. See: journalctl -u ws79 -n 30"
    exit 1
fi
