"""The Pi program, run on a computer against a scripted keypad and a silent sound card."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy, pygame          # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

if HAVE:
    import fake_pi
    from fake_pi import Event, ecodes


def press(code, wait=0.0):
    """A key going down then up."""
    return (wait, [Event(code, 1), Event(code, 0)])


@unittest.skipUnless(HAVE, "needs numpy and pygame")
class PiProgram(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ws79 = fake_pi.load_pi_program()
        script = [
            press(ecodes.KEY_F18),                 # key 1: Stinger OS
            press(ecodes.KEY_F18, wait=0.35),      # key 1 again: stop
            press(ecodes.KEY_F17, wait=0.05),      # key 2
            press(ecodes.KEY_F16, wait=0.2),       # key 3 while key 2 plays
            (0.0, [Event(ecodes.KEY_F16, 2)]),     # a held key repeating: ignored
            press(ecodes.KEY_VOLUMEDOWN),
            press(ecodes.KEY_VOLUMEDOWN),
            press(ecodes.KEY_VOLUMEUP),
            press(ecodes.KEY_MUTE),
            press(ecodes.KEY_MUTE),
            press(ecodes.KEY_F13),                 # key 6: colour theme
            press(ecodes.KEY_F15),                 # key 4
            press(ecodes.KEY_F14, wait=0.05),      # key 5
        ]
        cls.lines = fake_pi.run_pi_program(cls.ws79, script)
        cls.plain = [ln for ln in cls.lines if not ln.startswith("P|")]

    def test_start_sequence(self):
        self.assertEqual(self.plain[:4], ["S|WS-79  PI ONLINE", "S|WI-FI OK  10.0.0.7", "S|WS-79  READY", "F|27.185|CH 19  STANDBY"])

    def test_keys_follow_the_turned_keypad(self):
        self.assertEqual(self.ws79.KEY_NUMBER[ecodes.KEY_F18], 1)
        self.assertEqual(self.ws79.KEY_NUMBER[ecodes.KEY_F13], 6)

    def test_what_each_press_sends(self):
        self.assertEqual(self.plain[4:], [
            "F|26.965|CH 0  STINGER OS",
            "F|26.965|CH 0  STINGER OS  OFF",
            "F|27.185|CH 19  POACHER",
            "F|27.405|CH 40  FOREST",
            "V|95", "V|90", "V|95", "V|0", "V|95",
            "T|next",
            "F|27.225|CH 22  ROBOT 36",
            "F|27.275|CH 25  D79 FILE",
        ])

    def test_spectrum_frames(self):
        frames = [ln[2:] for ln in self.lines if ln.startswith("P|")]
        self.assertGreater(len(frames), 5, "a playing sound should stream its spectrum")
        for f in frames:
            self.assertEqual(len(f), 92)
            self.assertTrue(all(48 <= ord(c) <= 48 + 63 for c in f))
        self.assertIn("0" * 92, frames, "stopping a sound should send one flat frame")
        self.assertTrue(any(set(f) != {"0"} for f in frames), "a playing sound should not be flat")

    def test_every_sound_is_analysed(self):
        for n, (_freq, _label, name) in self.ws79.CHANNELS.items():
            frames = self.ws79.spectrum_of(os.path.join(self.ws79.SOUNDS, name))
            self.assertGreater(len(frames), 20, name)


@unittest.skipUnless(HAVE, "needs numpy and pygame")
class PiProgramWithoutNetworkOrKeypad(unittest.TestCase):
    def test_runs_offline(self):
        ws79 = fake_pi.load_pi_program()
        lines = fake_pi.run_pi_program(ws79, [press(ecodes.KEY_F18)], network=("", ""))
        plain = [ln for ln in lines if not ln.startswith("P|")]
        self.assertEqual(plain[:5], ["S|WS-79  PI ONLINE", "S|NO WI-FI  RUNNING OFFLINE", "S|WS-79  READY",
                                     "F|27.185|CH 19  STANDBY", "F|26.965|CH 0  STINGER OS"])

    def test_wired_network(self):
        ws79 = fake_pi.load_pi_program()
        lines = fake_pi.run_pi_program(ws79, [], network=("wired", "192.0.2.10"))
        self.assertIn("S|NETWORK OK  192.0.2.10", lines)

    def test_waits_for_a_missing_keypad(self):
        ws79 = fake_pi.load_pi_program()
        pad = fake_pi.FakeKeypad([press(ecodes.KEY_F17)])
        answers = [[], [], [pad]]                  # not there, not there, plugged in

        port = fake_pi.FakeSerial()
        ws79.screen.port = port
        ws79.time = fake_pi.FastTime()
        ws79.NETWORK_WAIT_S = 0
        ws79.network_status = lambda: ("wifi", "10.0.0.7")
        ws79.find_keypad = lambda: answers.pop(0) if answers else [pad]
        import types
        ws79.selectors = types.SimpleNamespace(DefaultSelector=fake_pi.FakeSelector, EVENT_READ=1)
        with self.assertRaises(fake_pi.Done):
            ws79.main()
        plain = [ln for ln in port.lines if not ln.startswith("P|")]
        self.assertEqual(plain[3:], ["F|27.185|CH 19  STANDBY", "S|KEYPAD NOT FOUND", "S|KEYPAD NOT FOUND",
                                     "F|27.185|CH 19  STANDBY", "F|27.185|CH 19  POACHER"])


if __name__ == "__main__":
    unittest.main()
