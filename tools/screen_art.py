"""The WS-79 bar screen's artwork, in the screen's own 960 x 240 pixels: the channel cell on the left, then the
spectrum's axis, its frequency labels and the marker on the tuned channel.

The 3D model's screen texture is drawn by the same function, so the real screen and the renders share one design.
Fonts: Exo (SIL Open Font License), in fonts/.
"""
import math, os, random
from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EXO_B = os.path.join(HERE, "fonts", "Exo-Bold.ttf")
EXO_M = os.path.join(HERE, "fonts", "Exo-Medium.ttf")
AMBER = (255, 176, 32)

def channel_and_spectrum(d, B, u, inside=False, channel="19", levels=None, marker=0.5):
    """One bar's picture, in its own 960 x 240 pixels (B maps them to the image, u is one of them): the channel in a
    cell between two thin rules, then the spectrum. inside=True keeps the end labels within the bar's own pixels.
    The defaults draw the reference picture: channel 19 with a carrier in the middle and two weaker ones.
    channel is the two digits in the cell, levels is one (a, b, gain) per bar in place of the fixed random draw,
    marker is where the tuned frequency sits in the band, from 0 to 1."""
    f_big = ImageFont.truetype(EXO_B, int(96 * u)); f_small = ImageFont.truetype(EXO_M, int(24 * u)); f_tiny = ImageFont.truetype(EXO_M, int(19 * u))
    # the channel: one cell between two thin rules, the separator between the digits and the spectrum
    l19, _, r19, _ = f_big.getbbox(channel)
    x19 = (5 + 166) / 2 - (r19 - l19) / u / 2 - l19 / u
    d.line([B(5, 22), B(5, 218)], fill=(90, 58, 10), width=max(1, int(2 * u)))
    d.text(B(x19 + 4, 30), "CH", font=f_small, fill=(170, 112, 18))
    d.text(B(x19, 58), channel, font=f_big, fill=AMBER)
    d.text(B(x19 + 4, 176), "AM", font=f_small, fill=AMBER)
    d.text(B(x19 + 66, 176), "USB", font=f_small, fill=(96, 62, 10))
    d.line([B(166, 22), B(166, 218)], fill=(90, 58, 10), width=max(1, int(2 * u)))
    # spectrum: 92 bars, a carrier in the middle and two weaker ones
    random.seed(79)
    x0, x1, base = 192, 940, 182
    n = 92; pitch = (x1 - x0) / n
    for i in range(n):
        t = i / (n - 1)
        env = 0.10 + 0.86 * math.exp(-((t - 0.5) / 0.045) ** 2) + 0.42 * math.exp(-((t - 0.24) / 0.07) ** 2) + 0.30 * math.exp(-((t - 0.78) / 0.06) ** 2)
        if levels is None: hgt = min(1.0, env * (0.72 + 0.5 * random.random()) + 0.05 * random.random()) * 150
        else: hgt = min(1.0, env * levels[i][2] * (0.72 + 0.5 * levels[i][0]) + 0.05 * levels[i][1]) * 150
        xa = x0 + i * pitch
        col = AMBER if hgt > 60 else (228, 150, 24)
        d.rectangle([B(xa, base - hgt), B(xa + pitch * 0.68, base)], fill=col)
        if hgt > 30: d.rectangle([B(xa, base - hgt - 7), B(xa + pitch * 0.68, base - hgt - 4)], fill=(255, 214, 120))
    d.line([B(x0 - 4, base + 5), B(x1 + 2, base + 5)], fill=AMBER, width=max(1, int(2 * u)))
    for i in range(41):
        xa = x0 + (x1 - x0) * i / 40
        d.line([B(xa, base + 5), B(xa, base + (17 if i % 10 == 0 else 11))], fill=(200, 132, 20), width=max(1, int(1.6 * u)))
    for i, txt in enumerate(["26.965", "27.075", "27.185", "27.295", "27.405"]):
        xa = x0 + (x1 - x0) * i / 4
        l, t_, r, b = f_tiny.getbbox(txt)
        xt = B(xa, 0)[0] - (r - l) / 2
        if inside: xt = max(B(176, 0)[0], min(xt, B(952, 0)[0] - (r - l)))
        d.text((xt, B(0, 203)[1]), txt, font=f_tiny, fill=AMBER if i == 2 else (150, 98, 16))
    xm = x0 + (x1 - x0) * marker + pitch * 0.3
    d.polygon([B(xm - 9, 18), B(xm + 9, 18), B(xm, 32)], fill=AMBER)

