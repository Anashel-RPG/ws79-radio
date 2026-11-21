"""Stand-ins for what pi/ws79.py needs from a Raspberry Pi, so the Pi program can run on any computer:
the keypad (evdev), the screen's serial port (pyserial) and a silent sound card (SDL's dummy driver).
"""
import importlib.util, os, sys, time, types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Done(Exception):
    """Raised when the scripted key presses are over."""


class ecodes:
    EV_KEY = 1
    KEY_MUTE, KEY_VOLUMEDOWN, KEY_VOLUMEUP = 113, 114, 115
    KEY_F13, KEY_F14, KEY_F15, KEY_F16, KEY_F17, KEY_F18 = 183, 184, 185, 186, 187, 188


class Event:
    def __init__(self, code, value=1, type=ecodes.EV_KEY):
        self.code, self.value, self.type = code, value, type


class FakeKeypad:
    """A keypad that plays a script: a list of (seconds to wait first, [events])."""
    class info:
        vendor, product = 0x1189, 0x8890

    def __init__(self, script):
        self.script = list(script)

    def read(self):
        if not self.script:
            raise Done()
        wait, events = self.script.pop(0)
        time.sleep(wait)
        return events


class FakeSelector:
    def __init__(self):
        self.devs = []

    def register(self, dev, _events):
        self.devs.append(dev)

    def select(self, timeout=None):
        return [(types.SimpleNamespace(fileobj=d), 1) for d in self.devs]


class FakeSerial:
    """Collects the lines the Pi program sends to the screen."""
    def __init__(self):
        self.lines, self._buf = [], ""

    def write(self, data):
        self._buf += data.decode("ascii")
        *done, self._buf = self._buf.split("\n")
        self.lines.extend(done)


class FakeLgpio(types.ModuleType):
    """The pins of the two needles. Records each (gpio, duty in %) the program sets."""
    def __init__(self):
        super().__init__("lgpio")
        self.claimed, self.duty = [], []

    def gpiochip_open(self, _chip):
        return 1

    def gpio_claim_output(self, _h, gpio, _level=0):
        self.claimed.append(gpio)

    def tx_pwm(self, _h, gpio, freq, duty):
        assert 0 <= duty <= 100 and freq > 0
        self.duty.append((gpio, duty))


class FastTime:
    """time, with every sleep cut short so a test does not wait."""
    def __getattr__(self, name):
        return getattr(time, name)

    @staticmethod
    def sleep(seconds):
        time.sleep(min(seconds, 0.02))


def load_pi_program():
    """Import pi/ws79.py with the stand-ins in place. Returns the module."""
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    evdev = types.ModuleType("evdev")
    evdev.ecodes, evdev.InputDevice, evdev.list_devices = ecodes, None, lambda: []
    serial = types.ModuleType("serial")
    serial.Serial = lambda *a, **k: (_ for _ in ()).throw(OSError("no serial port in tests"))
    sys.modules["evdev"], sys.modules["serial"] = evdev, serial
    sys.modules["lgpio"] = FakeLgpio()
    spec = importlib.util.spec_from_file_location("ws79", os.path.join(REPO, "pi", "ws79.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_pi_program(mod, key_script, network=("wifi", "10.0.0.7"), keypad_present=True):
    """Run the program's main() against a scripted keypad. Returns every line it sent to the screen."""
    port = FakeSerial()
    mod.screen.port = port
    mod.time = FastTime()
    mod.NETWORK_WAIT_S = 0
    mod.network_status = lambda: network
    pad = FakeKeypad(key_script)
    mod.find_keypad = lambda: [pad] if keypad_present else []
    mod.selectors = types.SimpleNamespace(DefaultSelector=FakeSelector, EVENT_READ=1)
    try:
        mod.main()
    except Done:
        pass
    time.sleep(0.15)                # let the spectrum thread send its last line
    return port.lines
