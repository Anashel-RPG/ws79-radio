#!/usr/bin/env python3
"""WS-79 radio: the program that runs on the Raspberry Pi.

It starts with the Pi (ws79.service). It tells the bar screen what is happening, plays one sound per key of the
keypad, uses the knob as the volume, and sends the screen the spectrum of the sound that is playing.

The screen board listens on its USB serial port. Each message is one line of text:

    S|<text>             a status line (start, network, ready)
    F|<freq>|<label>     the radio view on a channel: <freq> picks the artwork, <label> is "CH nn  NAME"
    P|<92 characters>    one spectrum frame: each character is chr(48 + level), level 0 to 63
    V|<0-100>            the volume, shown for a moment
    T|next               the next colour theme
"""
import glob, os, selectors, signal, socket, subprocess, sys, threading, time, wave

os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
os.environ.setdefault("AUDIODEV", "plughw:CARD=Headphones,DEV=0")   # the Pi's 3.5 mm jack
import numpy as np
import pygame
import serial
from evdev import InputDevice, ecodes, list_devices

HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDS = os.path.join(HERE, "sounds")

# ---------------------------------------------------------------- what each key does
# Keys are numbered as you look at the radio, knob on the left: 1 2 3 on the top row, 4 5 6 on the bottom row.
# A channel is (frequency, label, sound). The frequency must be one the screen has artwork for (screen/code.py,
# FREQ_TO_CH). The sound is a 16-bit WAV file in pi/sounds/.
CHANNELS = {
    1: ("26.965", "CH 0  STINGER OS", "key1-stinger-os.wav"),
    2: ("27.185", "CH 19  POACHER", "key2-numbers-station.wav"),
    3: ("27.405", "CH 40  FOREST", "key3-forest.wav"),
    4: ("27.225", "CH 22  ROBOT 36", "key4-robot36.wav"),
    5: ("27.275", "CH 25  D79 FILE", "key5-d79-file.wav"),
}
THEME_KEY = 6                                    # this key changes the screen's colour
STANDBY = ("27.185", "CH 19  STANDBY")           # the view before any key is pressed

# pi/keypad.yaml programs the keypad's own keys as F13 to F18, in its own order (knob on the right).
# The WS-79 mounts the keypad turned end for end, knob on the left, so the keypad's last key is key 1.
KEYPAD_TURNED = True
_KEYPAD_ORDER = [ecodes.KEY_F13, ecodes.KEY_F14, ecodes.KEY_F15, ecodes.KEY_F16, ecodes.KEY_F17, ecodes.KEY_F18]
KEY_NUMBER = {code: n for n, code in enumerate(reversed(_KEYPAD_ORDER) if KEYPAD_TURNED else _KEYPAD_ORDER, 1)}
KEYPAD_USB_ID = (0x1189, 0x8890)                 # SinLoon 6 keys + knob (CH57x)

NETWORK_WAIT_S = 40                              # how long the start waits for a network before it runs offline
VOLUME_STEP = 0.05                               # one click of the knob

# ---------------------------------------------------------------- the screen
class Screen:
    """Lines of text to the screen board. A board that is unplugged or restarting is found again on the next line."""
    def __init__(self):
        self.port = None
        self.lock = threading.Lock()

    def _open(self):
        for p in glob.glob("/dev/serial/by-id/*Qualia*"):
            try:
                self.port = serial.Serial(p, 115200, timeout=0, write_timeout=1)
                return True
            except Exception:
                self.port = None
        return False

    def send(self, line):
        with self.lock:
            for _ in range(2):
                if self.port is None and not self._open():
                    return
                try:
                    self.port.write((line + "\n").encode("ascii", "replace"))
                    return
                except Exception:
                    self.port = None

screen = Screen()

# ---------------------------------------------------------------- the network, for the start screen only
def network_status():
    """("wifi", address), ("wired", address) or ("", "") when the Pi has no network yet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))         # nothing is sent: this asks the system which address it would use
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        return "", ""
    try:
        with open("/sys/class/net/wlan0/operstate") as f:
            wifi = f.read().strip() == "up"
    except OSError:
        wifi = False
    return ("wifi" if wifi else "wired"), ip

# ---------------------------------------------------------------- the keypad
def find_keypad():
    devs = []
    for p in list_devices():
        try:
            d = InputDevice(p)
        except Exception:
            continue
        if (d.info.vendor, d.info.product) == KEYPAD_USB_ID:
            devs.append(d)
    return devs

# ---------------------------------------------------------------- the spectrum
SPEC_FPS = 20
SPEC_BARS = 92
_spectra = {}

def spectrum_of(path):
    """The sound as SPEC_FPS frames a second of 92 bands, 120 Hz to 9 kHz on a log scale.
    Each frame is 92 characters, chr(48 + level) with level 0 to 63. Computed once per sound."""
    if path in _spectra:
        return _spectra[path]
    with wave.open(path, "rb") as w:
        rate = w.getframerate(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    x /= 32768.0
    hop = rate // SPEC_FPS
    win = 4096
    window = np.hanning(win)
    freqs = np.fft.rfftfreq(win, 1 / rate)
    edges = np.geomspace(120, 9000, SPEC_BARS + 1)
    idx = [np.where((freqs >= edges[i]) & (freqs < edges[i + 1]))[0] for i in range(SPEC_BARS)]
    frames = []
    for start in range(0, max(1, len(x) - win), hop):
        seg = x[start:start + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        mag = np.abs(np.fft.rfft(seg * window))
        row = ""
        last = 0
        for b in idx:
            if len(b):
                m = mag[b].mean()
                db = 20 * np.log10(m + 1e-9)      # roughly -40 (quiet) to +40 (loud)
                last = int(np.clip((db + 15) / 55 * 63, 0, 63))
            row += chr(48 + last)                 # a low band too narrow to hold a frequency repeats its neighbour
        frames.append(row)
    _spectra[path] = frames
    return frames

class Streamer:
    """Sends the playing sound's spectrum to the screen, in time with the audio."""
    def __init__(self):
        self.frames = None
        self.t0 = 0
        self.lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def start(self, frames):
        with self.lock:
            self.frames, self.t0 = frames, time.monotonic()

    def stop(self):
        with self.lock:
            self.frames = None
        screen.send("P|" + "0" * SPEC_BARS)

    def _run(self):
        while True:
            with self.lock:
                frames, t0 = self.frames, self.t0
            if frames:
                i = int((time.monotonic() - t0) * SPEC_FPS)
                if i >= len(frames):
                    self.stop()
                else:
                    screen.send("P|" + frames[i])
            time.sleep(1 / SPEC_FPS)

# ---------------------------------------------------------------- the program
def main():
    screen.send("S|WS-79  PI ONLINE")
    try:                                          # the jack's volume resets to a low level on some starts
        subprocess.run(["amixer", "-q", "-c", "Headphones", "sset", "PCM", "100%", "unmute"], timeout=5)
    except Exception:
        pass

    link, ip = "", ""
    deadline = time.monotonic() + NETWORK_WAIT_S
    while True:
        link, ip = network_status()
        if ip or time.monotonic() >= deadline:
            break
        screen.send("S|WS-79  WAITING FOR WI-FI")
        time.sleep(2)
    if ip:
        screen.send("S|%s OK  %s" % ("WI-FI" if link == "wifi" else "NETWORK", ip))
    else:
        screen.send("S|NO WI-FI  RUNNING OFFLINE")
    shown = time.monotonic()

    pygame.mixer.pre_init(44100, -16, 2, 4096)
    pygame.mixer.init()
    signal.signal(signal.SIGTERM, signal.SIG_DFL)    # the sound library takes over this signal; give it back so the
    voice = pygame.mixer.Channel(1)                  # service stops as soon as it is asked to

    # Load and analyse every sound once, so a key press never waits on the card.
    sounds, spectra = {}, {}
    for n, (_freq, _label, name) in CHANNELS.items():
        path = os.path.join(SOUNDS, name)
        try:
            sounds[n] = pygame.mixer.Sound(path)
            spectra[n] = spectrum_of(path)
        except Exception as e:
            print("sound %s: %s" % (name, e), file=sys.stderr)
    time.sleep(max(0.0, 2.5 - (time.monotonic() - shown)))     # leave the network line on screen long enough to read

    screen.send("S|WS-79  READY")
    time.sleep(1.5)
    screen.send("F|%s|%s" % STANDBY)

    devs = find_keypad()
    if not devs:
        while not devs:
            screen.send("S|KEYPAD NOT FOUND")
            time.sleep(3)
            devs = find_keypad()
        screen.send("F|%s|%s" % STANDBY)
    sel = selectors.DefaultSelector()
    for d in devs:
        sel.register(d, selectors.EVENT_READ)

    spec = Streamer()
    level, muted = 1.0, False
    playing = None                                # the key whose sound is playing

    def show_volume():
        voice.set_volume(0 if muted else level)
        screen.send("V|%d" % (0 if muted else round(level * 100)))

    while True:
        for key, _ in sel.select(timeout=1):
            try:
                events = list(key.fileobj.read())
            except OSError:
                # The keypad was unplugged. Leave: the service starts the program again and it waits for the keypad.
                sys.exit("keypad unplugged")
            for ev in events:
                if ev.type != ecodes.EV_KEY or ev.value != 1:
                    continue
                n = KEY_NUMBER.get(ev.code)
                if n in CHANNELS:
                    freq, label, name = CHANNELS[n]
                    if playing == n and voice.get_busy():       # the same key again stops its sound
                        voice.stop()
                        spec.stop()
                        playing = None
                        screen.send("F|%s|%s  OFF" % (freq, label))
                        continue
                    screen.send("F|%s|%s" % (freq, label))
                    voice.stop()
                    if n in sounds:
                        voice.play(sounds[n])
                        playing = n
                        spec.start(spectra[n])
                    else:
                        playing = None
                        screen.send("S|SOUND ERROR %s" % name)
                elif n == THEME_KEY:
                    screen.send("T|next")
                elif ev.code == ecodes.KEY_VOLUMEUP:
                    muted = False
                    level = min(1.0, level + VOLUME_STEP)
                    show_volume()
                elif ev.code == ecodes.KEY_VOLUMEDOWN:
                    muted = False
                    level = max(0.0, level - VOLUME_STEP)
                    show_volume()
                elif ev.code == ecodes.KEY_MUTE:
                    muted = not muted
                    show_volume()

if __name__ == "__main__":
    main()
