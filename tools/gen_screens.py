#!/usr/bin/env python3
"""Draw the WS-79 bar screen's fixed artwork, one picture per channel, into screen/screens/.

    python3 tools/gen_screens.py        (needs Pillow)

The design is channel_and_spectrum() in screen_art.py. Here it is drawn with every bar at zero: the screen board
draws the live bars on top. Each picture is a 960 x 240 BMP with a 32-colour palette, which is what the screen
program reads. To add a channel, add its number and frequency to CHANNELS below, run this, then add the frequency
to FREQ_TO_CH in screen/code.py and to CHANNELS in pi/ws79.py.
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen_art as T

BAND_LO, BAND_HI = 26.965, 27.405
CHANNELS = {"00": 26.965, "01": 27.065, "19": 27.185, "22": 27.225, "25": 27.275, "40": 27.405}

def render(ch, freq, out):
    im = Image.new("RGB", (960, 240), (5, 3, 1))
    d = ImageDraw.Draw(im)
    B = lambda x, y: (x, y)
    marker = (freq - BAND_LO) / (BAND_HI - BAND_LO)
    zero = [(0.0, 0.0, 0.0)] * 92
    T.channel_and_spectrum(d, B, 1.0, inside=True, channel=ch, levels=zero, marker=marker)
    # the zero-height bars leave a one-pixel line on the baseline row; the board redraws that row anyway
    im.quantize(colors=32, method=Image.Quantize.MEDIANCUT).save(out)

if __name__ == "__main__":
    OUTDIR = os.path.join(HERE, "..", "screen", "screens")
    os.makedirs(OUTDIR, exist_ok=True)
    for ch, f in CHANNELS.items():
        render(ch, f, os.path.join(OUTDIR, "ch%s.bmp" % ch))
    print("rendered", len(CHANNELS))
