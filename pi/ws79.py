#!/usr/bin/env python3
"""WS-79 radio: the program that runs on the Raspberry Pi.

It starts with the Pi (ws79.service). It tells the bar screen what is happening, plays one sound per key of the
keypad, uses the knob as the volume, sends the screen the spectrum of the sound that is playing, and moves the two
needles with that sound (see "the two needles" below).

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

# ---------------------------------------------------------------- the two needles
# Each meter is driven by a pin of the Pi through its 10 kOhm knob. The pin sends 3.3 V pulses (PWM), and the share
# of time the pin is on sets how far the needle goes: 100 % is the end of the scale, set once with the knob.
#   SIGNAL, the left meter, pin 16: the hiss and bite of the station, the energy between 1.5 and 6 kHz. It moves on
#           consonants, static and tones. The volume knob does not change it. With nothing playing it trembles just
#           above zero, like a receiver hearing only noise.
#   AUDIO, the right meter, pin 18: how loud the sound is at the speaker. It follows the volume knob and drops to
#           zero when the sound is muted.
# Each sound is scaled to itself, so its quiet parts sit low on the dial and its loudest moments reach about 90 %.
NEEDLE_SIGNAL_GPIO = 23                          # pin 16
NEEDLE_AUDIO_GPIO = 24                           # pin 18
NEEDLE_PWM_HZ = 500
NEEDLE_FPS = 50                                  # needle updates a second
NEEDLE_TOP = 0.90                                # where a sound's loudest moments put the needle
SIGNAL_NOISE = 0.06                              # where SIGNAL trembles with no station
SIGNAL_BAND = (1500, 6000)                       # Hz
SIGNAL_RISE, SIGNAL_FALL = 0.55, 0.20            # share of the gap closed per update
AUDIO_RISE, AUDIO_FALL = 0.85, 0.35
SILENCE_DB = -55                                 # quieter than this, both needles fall to rest
_tracks = {}

def _scaled(db, quiet):
    """Decibels to 0..1 for one sound: its 5th percentile near the bottom, its 99th at NEEDLE_TOP."""
    live = db[~quiet] if (~quiet).any() else db
    lo, hi = np.percentile(live, 5), np.percentile(live, 99)
    lo = min(lo, hi - 20)                         # a steady sound stays steady instead of being stretched
    v = 0.05 + (db - lo) / max(hi - lo, 1e-6) * (NEEDLE_TOP - 0.05)
    v[quiet] = 0.0
    return np.clip(v, 0.0, 1.0)

def needle_tracks(path):
    """NEEDLE_FPS values a second of (signal, audio), each 0 to 1, before any easing or volume. Computed once."""
    if path in _tracks:
        return _tracks[path]
    with wave.open(path, "rb") as w:
        rate = w.getframerate(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    x /= 32768.0
    hop, win = rate // NEEDLE_FPS, 2048
    n = max(1, len(x) // hop)
    x = np.pad(x, (0, n * hop + win - len(x)))
    segs = x[np.arange(n)[:, None] * hop + np.arange(win)[None, :]]
    audio_db = 20 * np.log10(np.sqrt(np.mean(segs[:, :hop] ** 2, axis=1)) + 1e-9)
    freqs = np.fft.rfftfreq(win, 1 / rate)
    band = (freqs >= SIGNAL_BAND[0]) & (freqs < SIGNAL_BAND[1])
    mag = np.abs(np.fft.rfft(segs * np.hanning(win), axis=1))[:, band]
    signal_db = 20 * np.log10(mag.mean(axis=1) + 1e-9)
    quiet = audio_db < SILENCE_DB
    tracks = list(zip(_scaled(signal_db, quiet).tolist(), _scaled(audio_db, quiet).tolist()))
    _tracks[path] = tracks
    return tracks

def ease(now, target, rise, fall):
    """One update of a needle's travel toward its target: rise when going up, fall when coming down."""
    return now + (target - now) * (rise if target > now else fall)

class Needles:
    """The two meters. If the pins cannot be opened (no lgpio, not a Pi) the radio runs without them."""
    def __init__(self):
        self.signal = self.audio = 0.0
        self.chip = None
        try:
            import lgpio
            self.lgpio = lgpio
            self.chip = lgpio.gpiochip_open(0)
            for g in (NEEDLE_SIGNAL_GPIO, NEEDLE_AUDIO_GPIO):
                lgpio.gpio_claim_output(self.chip, g, 0)
        except Exception as e:
            self.chip = None
            print("needles off: %s" % e, file=sys.stderr)

    def move(self, signal_target, audio_target):
        self.signal = ease(self.signal, signal_target, SIGNAL_RISE, SIGNAL_FALL)
        self.audio = ease(self.audio, audio_target, AUDIO_RISE, AUDIO_FALL)
        if self.chip is None:
            return
        try:
            for g, v in ((NEEDLE_SIGNAL_GPIO, self.signal), (NEEDLE_AUDIO_GPIO, self.audio)):
                self.lgpio.tx_pwm(self.chip, g, NEEDLE_PWM_HZ, round(min(1.0, max(0.0, v)) * 100, 1))
        except Exception as e:
            print("needles: %s" % e, file=sys.stderr)

class Streamer:
    """Sends the playing sound's spectrum to the screen and moves the needles, in time with the audio."""
    def __init__(self, needles=None, gain=lambda: 1.0):
        self.frames = self.tracks = None
        self.t0 = 0
        self.needles, self.gain = needles, gain
        self.noise = SIGNAL_NOISE
        self.lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def start(self, frames, tracks=None):
        with self.lock:
            self.frames, self.tracks, self.t0 = frames, tracks, time.monotonic()

    def stop(self):
        with self.lock:
            self.frames = self.tracks = None
        screen.send("P|" + "0" * SPEC_BARS)

    def _run(self):
        sent = -1
        while True:
            with self.lock:
                frames, tracks, t0 = self.frames, self.tracks, self.t0
            signal, audio = None, 0.0
            if frames:
                t = time.monotonic() - t0
                i = int(t * SPEC_FPS)
                if i >= len(frames):
                    self.stop()
                    sent = -1
                else:
                    if i != sent:                   # the screen gets SPEC_FPS frames a second
                        screen.send("P|" + frames[i])
                        sent = i
                    k = int(t * NEEDLE_FPS)
                    if tracks and k < len(tracks):
                        signal, audio = tracks[k][0], tracks[k][1] * self.gain()
            else:
                sent = -1
            if signal is None:                    # no station: a small tremble of noise
                self.noise = min(2 * SIGNAL_NOISE, max(0.0, self.noise + np.random.uniform(-0.006, 0.006)))
                signal = self.noise
            if self.needles:
                self.needles.move(max(signal, SIGNAL_NOISE) if frames else signal, audio)
            time.sleep(1 / NEEDLE_FPS)

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
    sounds, spectra, tracks = {}, {}, {}
    for n, (_freq, _label, name) in CHANNELS.items():
        path = os.path.join(SOUNDS, name)
        try:
            sounds[n] = pygame.mixer.Sound(path)
            spectra[n] = spectrum_of(path)
            tracks[n] = needle_tracks(path)
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

    level, muted = 1.0, False
    gain = [1.0]                                  # what the AUDIO needle multiplies by: the volume, 0 when muted
    spec = Streamer(Needles(), lambda: gain[0])
    playing = None                                # the key whose sound is playing

    def show_volume():
        gain[0] = 0 if muted else level
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
                        spec.start(spectra[n], tracks.get(n))
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
