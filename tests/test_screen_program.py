"""The screen program, run on a computer against stand-ins for CircuitPython's display modules."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy, PIL             # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

if HAVE:
    from fake_circuitpython import Sim


def frame_of(levels):
    return "P|" + "".join(chr(48 + v) for v in levels) + "\n"


@unittest.skipUnless(HAVE, "needs numpy and Pillow")
class ScreenProgram(unittest.TestCase):
    def run_script(self, script, frames=40, on_frame=None):
        sim = Sim(script, frames=frames, on_frame=on_frame)
        return sim, sim.run()

    def test_starts_on_the_boot_line(self):
        sim, ns = self.run_script({}, frames=5)
        self.assertEqual(ns["mode"], "status")
        self.assertTrue(ns["status"].text.startswith("BOOTING"))
        self.assertTrue(ns["art_group"].hidden and ns["bars_group"].hidden)
        self.assertEqual(len(ns["CELLS"]), len(ns["FREQ_TO_CH"]), "every channel's artwork is loaded at start")

    def test_status_then_radio_view(self):
        sim, ns = self.run_script({2: "S|WS-79  READY\n", 6: "F|27.225|CH 22  ROBOT 36\n"}, frames=12)
        self.assertEqual(ns["mode"], "freq")
        self.assertTrue(ns["status"].hidden)
        self.assertFalse(ns["art_group"].hidden or ns["bars_group"].hidden or ns["name"].hidden)
        self.assertEqual(ns["name"].text, "ROBOT 36")
        self.assertIs(ns["cell_tile"].bitmap, ns["CELLS"]["22"][0])

    def test_marker_follows_the_frequency(self):
        seen = {}
        for freq in ("26.965", "27.185", "27.405"):
            sim, ns = self.run_script({2: "F|%s|CH 0  X\n" % freq}, frames=6)
            seen[freq] = ns["marker_tile"].x
        self.assertEqual(seen["27.185"], 556, "channel 19 sits where the artwork drew its marker")
        self.assertLess(seen["26.965"], seen["27.185"])
        self.assertLess(seen["27.185"], seen["27.405"])
        self.assertLessEqual(seen["27.405"] + 26, 960, "the marker stays on the screen")

    def test_bars_follow_the_spectrum(self):
        levels = [0] * 92
        levels[10], levels[50], levels[91] = 63, 30, 5
        script = {2: "F|27.185|CH 19  POACHER\n"}
        for k in range(4, 12):
            script[k] = frame_of(levels)
        sim, ns = self.run_script(script, frames=12)
        hmax = ns["HMAX"]
        # A bar held at one level breathes by 3 pixels: it falls a step, then rises back to the level.
        self.assertIn(ns["drawn_h"][10], range(hmax - 3, hmax + 1))
        self.assertIn(ns["drawn_h"][50], range(30 * hmax // 63 - 3, 30 * hmax // 63 + 1))
        self.assertEqual(ns["drawn_h"][0], 0)
        bar = ns["BMPS"][10]
        self.assertEqual(bar[0, ns["YB"] - 1], 2, "a tall bar is drawn in the bright colour down to the baseline")
        self.assertEqual(bar[0, ns["YB"] - ns["drawn_p"][10] - 7], 3, "its peak dot sits above it")
        self.assertGreaterEqual(ns["drawn_p"][10], ns["drawn_h"][10])

    def test_bars_fall_back_when_the_sound_stops(self):
        script = {2: "F|27.185|CH 19  POACHER\n", 4: frame_of([63] * 92)}
        sim, ns = self.run_script(script, frames=120)
        self.assertLess(max(ns["drawn_h"]), ns["HMAX"] // 2, "with no new frames the bars return to their idle shape")

    def test_only_the_newest_spectrum_frame_is_drawn(self):
        script = {2: "F|27.185|CH 19  POACHER\n", 5: frame_of([10] * 92) + frame_of([20] * 92) + frame_of([63] * 92)}
        sim, ns = self.run_script(script, frames=7)
        self.assertEqual(ns["target"][0], ns["HMAX"])

    def test_volume_and_theme_notes(self):
        script = {2: "F|27.185|CH 19  POACHER\n", 4: "V|85\n"}
        sim, ns = self.run_script(script, frames=8)
        self.assertEqual(ns["name"].text, "VOL 85%")
        sim, ns = self.run_script(dict(script), frames=80)
        self.assertEqual(ns["name"].text, "POACHER", "the note gives the line back to the channel name")
        sim, ns = self.run_script({2: "F|27.185|CH 19  POACHER\n", 4: "T|next\n"}, frames=8)
        self.assertEqual((ns["theme"], ns["name"].text), (1, "BLUE"))
        self.assertEqual(ns["bpal"][2], ns["tint"](ns["AMBER"], ns["THEMES"][1][1]))
        sim, ns = self.run_script({2: "F|27.185|CH 19  POACHER\n", 4: "T|next\nT|next\nT|next\nT|next\n"}, frames=8)
        self.assertEqual(ns["theme"], 0, "four presses come back to amber")
        self.assertEqual(ns["bpal"][2], 0xFFB020)

    def test_a_backlog_never_grows(self):
        flood = "".join(frame_of([k % 64] * 92) for k in range(400))
        sim, ns = self.run_script({2: "F|27.185|CH 19  POACHER\n", 4: flood}, frames=8)
        self.assertEqual(sim.pending, "")
        self.assertLess(len(ns["buf"]), 200)

    def test_unknown_lines_are_ignored(self):
        sim, ns = self.run_script({2: "F|27.185|CH 19  POACHER\n", 4: "garbage\nV|abc\nX|1\nF|only-one-field\n\n"}, frames=8)
        self.assertEqual(ns["mode"], "freq")

    def test_picture_can_be_composed(self):
        sim, ns = self.run_script({2: "F|27.405|CH 40  FOREST\n", 4: frame_of([40] * 92)}, frames=8)
        img = sim.compose()
        self.assertEqual(img.shape, (240, 960, 3))
        self.assertGreater(int(img.max()), 200)


if __name__ == "__main__":
    unittest.main()
