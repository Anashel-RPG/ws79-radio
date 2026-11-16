# WS-79 radio: the program that runs on the screen board
# (Adafruit Qualia ESP32-S3 with the 3.7 in 240 x 960 bar display, CircuitPython 10).
#
# The screen shows the channel in a cell on the left, then a spectrum of 92 bars with peak dots over a frequency
# axis, with a marker on the tuned channel. The fixed artwork comes from the images in /screens (drawn by
# tools/gen_screens.py). Only the bars are drawn live.
#
# The Raspberry Pi sends one line of text per message over USB serial:
#   S|<text>             a status line (start, network, ready)
#   F|<freq>|<label>     the radio view on a channel: <freq> picks the artwork, <label> is "CH nn  NAME"
#   P|<92 characters>    one spectrum frame: each character is chr(48 + level), level 0 to 63
#   V|<0-100>            the volume, shown for a moment
#   T|next               the next colour theme (amber, blue, red, green)
import math, random, sys, time
import bitmaptools, displayio, supervisor, terminalio
import adafruit_imageload
from adafruit_display_text import label
from adafruit_qualia.graphics import Graphics, Displays

AMBER = 0xFFB020
AMBER_LO = 0xE49618
PEAK = 0xFFD678
DIM = 0x96620F
FRAME_S = 1 / 30                           # the frame rate is capped at 30 a second (see docs/HOW-IT-WORKS.md)

g = Graphics(Displays.BAR240X960, default_bg=None, auto_refresh=False)
d = g.display
d.rotation = 90
W, H = d.width, d.height
print("PANEL", d.framebuffer.frequency, d.framebuffer.refresh_rate)

# Each frequency the Pi can tune, and the artwork that holds its channel cell.
FREQ_TO_CH = {"26.965": "00", "27.065": "01", "27.185": "19", "27.225": "22", "27.275": "25", "27.405": "40"}

root = displayio.Group()
d.root_group = root

# --- layer 1: the artwork. One base picture, then two small parts that change with the channel:
# the CH cell (left, 170 px wide) and the marker above the axis. A channel change redraws only those two.
art_group = displayio.Group()
root.append(art_group)
CELL_W = 170
MK_X0, MK_Y0, MK_W, MK_H = 556, 14, 26, 22           # the marker as drawn on channel 19's artwork
PITCH_A = (940 - 192) / 92
def marker_x(freq):
    m = (float(freq) - 26.965) / (27.405 - 26.965)
    return round(192 + 748 * m + PITCH_A * 0.3 - 12.4)
PALS = []                                            # every artwork palette on screen, for the colour themes
CELLS = {}
base_tile = cell_tile = marker_tile = None

def load_art():
    global base_tile, cell_tile, marker_tile
    base_bmp, base_pal = adafruit_imageload.load("/screens/ch19.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
    dark = min(range(len(base_pal)), key=lambda i: base_pal[i])
    mk = displayio.Bitmap(MK_W, MK_H, len(base_pal))
    bitmaptools.blit(mk, base_bmp, 0, 0, x1=MK_X0, y1=MK_Y0, x2=MK_X0 + MK_W, y2=MK_Y0 + MK_H)
    bitmaptools.fill_region(base_bmp, CELL_W + 8, MK_Y0, 958, MK_Y0 + MK_H, dark)   # the base keeps no marker
    PALS.append(base_pal)
    for ch in FREQ_TO_CH.values():
        bmp, pal = adafruit_imageload.load("/screens/ch%s.bmp" % ch, bitmap=displayio.Bitmap, palette=displayio.Palette)
        cell = displayio.Bitmap(CELL_W, 240, len(pal))
        bitmaptools.blit(cell, bmp, 0, 0, x1=0, y1=0, x2=CELL_W, y2=240)
        CELLS[ch] = (cell, pal)
        PALS.append(pal)
        del bmp
    base_tile = displayio.TileGrid(base_bmp, pixel_shader=base_pal)
    cell_tile = displayio.TileGrid(CELLS["19"][0], pixel_shader=CELLS["19"][1])
    marker_tile = displayio.TileGrid(mk, pixel_shader=base_pal, x=MK_X0, y=MK_Y0)
    for tg in (base_tile, cell_tile, marker_tile):
        art_group.append(tg)

def set_channel(freq):
    ch = FREQ_TO_CH.get(freq, "19")
    bmp, pal = CELLS[ch]
    if cell_tile.bitmap is not bmp:
        cell_tile.bitmap = bmp
        cell_tile.pixel_shader = pal
    x = marker_x(freq)
    if marker_tile.x != x:
        marker_tile.x = x

# --- layer 2: the live bars. Each bar is its own small opaque bitmap, so a frame only redraws the rows that moved.
# (Writing straight into the panel's framebuffer from Python is far too slow on this board.)
N, X0, X1, BASE = 92, 192, 940, 182
TOP = 36                                   # below the marker and the name line
HMAX = BASE - TOP - 8                      # room for the peak dot above the tallest bar
PITCH = (X1 - X0) / N
BW = max(2, round(PITCH * 0.68))
XS = [X0 + round(i * PITCH) for i in range(N)]
drawn_h = [-1] * N
drawn_p = [-1] * N
height = [0.0] * N
peak = [0.0] * N
target = [0] * N
last_p = 0

bpal = displayio.Palette(4)
bpal[0] = 0x050301; bpal[1] = AMBER_LO; bpal[2] = AMBER; bpal[3] = PEAK
bars_group = displayio.Group()
BMPS = []
for i in range(N):
    b = displayio.Bitmap(BW, BASE - TOP, 4)
    BMPS.append(b)
    bars_group.append(displayio.TileGrid(b, pixel_shader=bpal, x=XS[i], y=TOP))
root.append(bars_group)
bars_group.hidden = True
YB = BASE - TOP                            # the baseline, in each bar bitmap's rows

def draw_bar(i, h, pk):
    b = BMPS[i]
    oh, op = drawn_h[i], drawn_p[i]
    col = 2 if h > 60 else 1
    if oh < 0:                             # first draw: the whole column
        bitmaptools.fill_region(b, 0, 0, BW, YB, 0)
        if h:
            bitmaptools.fill_region(b, 0, YB - h, BW, YB, col)
    else:                                  # only the rows that changed
        if op:
            y = YB - op - 7
            if y >= 0:
                bitmaptools.fill_region(b, 0, y, BW, y + 3, 0)
        if h > oh:
            bitmaptools.fill_region(b, 0, YB - h, BW, YB - oh, col)
        elif h < oh:
            bitmaptools.fill_region(b, 0, YB - oh, BW, YB - h, 0)
        if (oh > 60) != (h > 60) and h:
            bitmaptools.fill_region(b, 0, YB - h, BW, YB, col)
    if pk:
        y = YB - pk - 7
        if y >= 0:
            bitmaptools.fill_region(b, 0, y, BW, y + 3, 3)

def redraw_all():
    for i in range(N):
        drawn_h[i] = -1

# With no sound playing the bars idle on this shape: a carrier in the middle and two weaker ones, kept low.
ENV = []
for i in range(N):
    t = i / (N - 1)
    ENV.append(0.10 + 0.86 * math.exp(-((t - 0.5) / 0.045) ** 2) + 0.42 * math.exp(-((t - 0.24) / 0.07) ** 2)
               + 0.30 * math.exp(-((t - 0.78) / 0.06) ** 2))

# --- layer 3: text
name = label.Label(terminalio.FONT, text="", color=DIM, scale=2, x=200, y=18)
status = label.Label(terminalio.FONT, text="BOOTING", color=AMBER, scale=4, x=40, y=120)
for item in (name, status):
    root.append(item)

# --- colour themes: every colour on screen is amber at some brightness, so a theme is one hue applied by brightness
THEMES = [("AMBER", (255, 176, 32)), ("BLUE", (40, 150, 255)), ("RED", (255, 50, 40)), ("GREEN", (60, 255, 110))]
theme = 0
ART_SRC = {}                               # each artwork palette's original colours

def tint(c, hue):
    r, g_, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    k = max(r, g_, b) / 255
    return (int(hue[0] * k) << 16) | (int(hue[1] * k) << 8) | int(hue[2] * k)

def apply_theme():
    hue = THEMES[theme][1]
    for pal in PALS:
        k = id(pal)
        if k not in ART_SRC:
            ART_SRC[k] = [pal[i] for i in range(len(pal))]
        for i, c in enumerate(ART_SRC[k]):
            pal[i] = tint(c, hue)
    bpal[1] = tint(AMBER_LO, hue); bpal[2] = tint(AMBER, hue); bpal[3] = tint(PEAK, hue)
    name.color = tint(DIM, hue); status.color = tint(AMBER, hue)

mode = "status"
note_until = 0                             # when the name line goes back from a volume or theme note to the channel name
current_label = ""
buf = ""
boot_start = time.monotonic()
last_msg = 0

def show_status(text):
    global mode
    mode = "status"
    status.text = text[:36]
    status.hidden = False
    art_group.hidden = True
    bars_group.hidden = True
    name.hidden = True

def show_freq(freq, lab):
    global mode, current_label
    mode = "freq"
    set_channel(freq)
    redraw_all()
    current_label = lab.split("  ", 1)[-1] if "  " in lab else lab
    name.text = current_label[:28]
    status.hidden = True
    art_group.hidden = False
    bars_group.hidden = False
    name.hidden = False

def show_note(text):
    global note_until
    name.text = text
    note_until = time.monotonic() + 1.5

def handle(line):
    global last_msg, last_p, theme
    last_msg = time.monotonic()
    parts = line.strip().split("|")
    k = parts[0]
    if k == "P" and len(parts) > 1:
        last_p = last_msg
        s = parts[1]
        for i in range(min(N, len(s))):
            target[i] = (ord(s[i]) - 48) * HMAX // 63
    elif k == "S" and len(parts) > 1:
        show_status(parts[1])
    elif k == "F" and len(parts) > 2:
        show_freq(parts[1], parts[2])
    elif k == "T":
        theme = (theme + 1) % len(THEMES)
        apply_theme()
        show_note(THEMES[theme][0])
    elif k == "V" and len(parts) > 1:
        try:
            show_note("VOL %d%%" % max(0, min(100, int(parts[1]))))
        except ValueError:
            pass

def step_bars():
    live = time.monotonic() - last_p < 0.4
    for i in range(N):
        tg = target[i] if live else ENV[i] * HMAX * 0.30 * (0.7 + 0.6 * random.random())
        h = height[i]
        h = tg if tg > h else h - max(3, (h - tg) * 0.25)      # rise at once, fall smoothly
        if h < 0:
            h = 0
        height[i] = h
        p = peak[i]
        p = h if h > p else p - 1.5                              # the peak dot holds, then sinks
        peak[i] = p
        hi = int(h)
        pk = int(p) if p > 30 else 0
        if hi == drawn_h[i] and pk == drawn_p[i]:
            continue
        draw_bar(i, hi, pk)
        drawn_h[i] = hi
        drawn_p[i] = pk

show_status("BOOTING")
d.refresh()
try:
    load_art()                             # every artwork is loaded once here, so a key press never waits on flash
except Exception as e:
    print("art", e)
art_group.hidden = True

while True:
    n = supervisor.runtime.serial_bytes_available
    if n:
        buf += sys.stdin.read(n)
        if len(buf) > 2000:                # never let a backlog grow: keep the newest lines
            buf = buf[buf.rfind("\n", 0, len(buf) - 400) + 1:]
        *lines, buf = buf.split("\n")
        latest_p = None
        for ln in lines:
            ln = ln.strip("\r")
            if ln.startswith("P|"):
                latest_p = ln              # only the newest spectrum frame matters
            elif ln:
                handle(ln)
        if latest_p:
            handle(latest_p)
    now = time.monotonic()
    if mode == "status" and last_msg == 0:
        status.text = "BOOTING" + "." * (int(now - boot_start) % 4)
    if mode == "freq":
        step_bars()
    if note_until and now > note_until:
        name.text = current_label[:28]
        note_until = 0
    d.refresh()
    spare = FRAME_S - (time.monotonic() - now)
    if spare > 0:
        time.sleep(spare)
