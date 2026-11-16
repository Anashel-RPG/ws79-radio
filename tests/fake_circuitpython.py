"""A small stand-in for the CircuitPython modules that screen/code.py uses, so the screen program can run on a
computer: displayio, bitmaptools, supervisor, terminalio, adafruit_imageload, adafruit_display_text and
adafruit_qualia. It keeps time itself (one frame per refresh), feeds the program scripted serial lines, and can
compose what the screen would show into a picture.

It is stricter than the board in one way: a fill or a copy that reaches outside a bitmap raises an error here,
where the board would clip it silently.
"""
import os, random, struct, sys, time as _real_time, types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StopSim(Exception):
    """Raised from refresh() when the scripted run is over."""


# ---------------------------------------------------------------- displayio
class Bitmap:
    def __init__(self, width, height, value_count):
        self.width, self.height, self.value_count = width, height, value_count
        self.data = bytearray(width * height)

    def _index(self, key):
        if isinstance(key, tuple):
            x, y = key
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise IndexError("pixel (%d, %d) outside %dx%d" % (x, y, self.width, self.height))
            return y * self.width + x
        return key

    def __getitem__(self, key):
        return self.data[self._index(key)]

    def __setitem__(self, key, value):
        if not 0 <= value < self.value_count:
            raise ValueError("value %d outside the bitmap's %d values" % (value, self.value_count))
        self.data[self._index(key)] = value


class Palette:
    def __init__(self, count):
        self.colors = [0] * count
        self.transparent = set()

    def __len__(self):
        return len(self.colors)

    def __getitem__(self, i):
        return self.colors[i]

    def __setitem__(self, i, value):
        if isinstance(value, (tuple, list, bytes, bytearray)):
            value = (value[0] << 16) | (value[1] << 8) | value[2]
        self.colors[i] = int(value) & 0xFFFFFF

    def make_transparent(self, i):
        self.transparent.add(i)

    def make_opaque(self, i):
        self.transparent.discard(i)


class TileGrid:
    def __init__(self, bitmap, *, pixel_shader, x=0, y=0, **_):
        self.bitmap, self.pixel_shader, self.x, self.y, self.hidden = bitmap, pixel_shader, x, y, False


class Group:
    def __init__(self, *, scale=1, x=0, y=0):
        self.scale, self.x, self.y, self.hidden, self._items = scale, x, y, False, []

    def append(self, item):
        self._items.append(item)

    def pop(self, i=-1):
        return self._items.pop(i)

    def remove(self, item):
        self._items.remove(item)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, i):
        return self._items[i]


# ---------------------------------------------------------------- bitmaptools
def fill_region(dest, x1, y1, x2, y2, value):
    if not (0 <= x1 <= x2 <= dest.width and 0 <= y1 <= y2 <= dest.height):
        raise ValueError("fill_region (%d, %d)-(%d, %d) outside %dx%d" % (x1, y1, x2, y2, dest.width, dest.height))
    if not 0 <= value < dest.value_count:
        raise ValueError("value %d outside the bitmap's %d values" % (value, dest.value_count))
    row = bytes([value]) * (x2 - x1)
    for y in range(y1, y2):
        o = y * dest.width + x1
        dest.data[o:o + len(row)] = row


def blit(dest, source, x, y, *, x1=0, y1=0, x2=None, y2=None, skip_source_index=None, skip_dest_index=None):
    x2 = source.width if x2 is None else x2
    y2 = source.height if y2 is None else y2
    w, h = x2 - x1, y2 - y1
    if not (0 <= x1 <= x2 <= source.width and 0 <= y1 <= y2 <= source.height):
        raise ValueError("blit source region outside the source bitmap")
    if not (0 <= x and x + w <= dest.width and 0 <= y and y + h <= dest.height):
        raise ValueError("blit reaches outside the destination bitmap")
    for r in range(h):
        so = (y1 + r) * source.width + x1
        do = (y + r) * dest.width + x
        dest.data[do:do + w] = source.data[so:so + w]


# ---------------------------------------------------------------- text
class Label:
    def __init__(self, font, *, text="", color=0xFFFFFF, scale=1, x=0, y=0, **_):
        self.font, self.text, self.color, self.scale, self.x, self.y, self.hidden = font, text, color, scale, x, y, False


# ---------------------------------------------------------------- the display and the run
class _Framebuffer:
    frequency = 12000000
    refresh_rate = 29


class Display:
    def __init__(self, sim):
        self._sim, self._rotation, self.root_group, self.framebuffer = sim, 0, None, _Framebuffer()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = value

    @property
    def width(self):
        return 960 if self._rotation in (90, 270) else 240

    @property
    def height(self):
        return 240 if self._rotation in (90, 270) else 960

    def refresh(self, **_):
        self._sim._on_refresh()


class Sim:
    """One run of the screen program. script maps a frame number to the text that arrives before that frame."""
    FRAME_S = 1 / 30

    def __init__(self, script=None, frames=60, on_frame=None):
        self.script = dict(script or {})
        self.frames, self.on_frame = frames, on_frame
        self.frame, self.clock, self.pending = 0, 1000.0, ""
        self.display = Display(self)
        self.ns = None

    def _on_refresh(self):
        if self.on_frame:
            self.on_frame(self)
        self.frame += 1
        self.clock += self.FRAME_S
        if self.frame >= self.frames:
            raise StopSim()
        self.pending += self.script.get(self.frame, "")

    # what the program's `import` statements receive
    def _modules(self):
        sim = self
        m = {}
        d = types.ModuleType("displayio")
        d.Bitmap, d.Palette, d.TileGrid, d.Group = Bitmap, Palette, TileGrid, Group
        m["displayio"] = d
        b = types.ModuleType("bitmaptools")
        b.fill_region, b.blit = fill_region, blit
        m["bitmaptools"] = b
        t = types.ModuleType("terminalio")
        t.FONT = object()
        m["terminalio"] = t

        class _Runtime:
            @property
            def serial_bytes_available(self):
                return len(sim.pending)
        s = types.ModuleType("supervisor")
        s.runtime = _Runtime()
        m["supervisor"] = s

        il = types.ModuleType("adafruit_imageload")
        il.load = load_image
        m["adafruit_imageload"] = il
        adt = types.ModuleType("adafruit_display_text")
        lab = types.ModuleType("adafruit_display_text.label")
        lab.Label = Label
        adt.label = lab
        m["adafruit_display_text"], m["adafruit_display_text.label"] = adt, lab
        aq = types.ModuleType("adafruit_qualia")
        gr = types.ModuleType("adafruit_qualia.graphics")

        class Displays:
            BAR240X960 = "bar240x960"

        class Graphics:
            def __init__(self, display, **_):
                self.display = sim.display
        gr.Displays, gr.Graphics = Displays, Graphics
        aq.graphics = gr
        m["adafruit_qualia"], m["adafruit_qualia.graphics"] = aq, gr

        class _Stdin:
            def read(self, n):
                out, sim.pending = sim.pending[:n], sim.pending[n:]
                return out

        class _Proxy(types.ModuleType):
            """A module that answers like the real one, except for what is set on it."""
            def __init__(self, real):
                super().__init__(real.__name__)
                self.__dict__["_real"] = real

            def __getattr__(self, name):
                return getattr(self.__dict__["_real"], name)
        ft = _Proxy(_real_time)
        ft.monotonic = lambda: sim.clock
        ft.monotonic_ns = lambda: int(sim.clock * 1e9)
        ft.sleep = lambda s: None
        m["time"] = ft
        fs = _Proxy(sys)
        fs.stdin = _Stdin()
        m["sys"] = fs
        mc = types.ModuleType("microcontroller")          # only older versions of the screen program import this

        class _Cpu:
            reset_reason = "ResetReason.POWER_ON"
        mc.nvm, mc.cpu = bytearray(8), _Cpu()
        m["microcontroller"] = mc
        return m

    def run(self, code_path=None, seed=79):
        """Run the screen program until the scripted frames are over. Returns its global names."""
        code_path = code_path or os.path.join(REPO, "screen", "code.py")
        random.seed(seed)
        mods = self._modules()
        saved = {k: sys.modules.get(k) for k in mods}
        sys.modules.update(mods)
        self.ns = {"__name__": "__main__", "__file__": code_path}
        try:
            with open(code_path, encoding="utf-8") as f:
                exec(compile(f.read(), code_path, "exec"), self.ns)
        except StopSim:
            pass
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        return self.ns

    def compose(self):
        """What the panel would show now, as a numpy array (height, width, 3). Text labels are left out."""
        import numpy as np
        W, H = self.display.width, self.display.height
        img = np.zeros((H, W, 3), np.uint8)

        def draw(group, ox, oy):
            for item in group:
                if getattr(item, "hidden", False):
                    continue
                if isinstance(item, Group):
                    draw(item, ox + item.x, oy + item.y)
                elif isinstance(item, TileGrid):
                    bmp, pal = item.bitmap, item.pixel_shader
                    arr = np.frombuffer(bytes(bmp.data), np.uint8).reshape(bmp.height, bmp.width)
                    lut = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in pal.colors], np.uint8)
                    x0, y0 = ox + item.x, oy + item.y
                    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + bmp.width), min(H, y0 + bmp.height)
                    if xa >= xb or ya >= yb:
                        continue
                    src = arr[ya - y0:yb - y0, xa - x0:xb - x0]
                    rgb = lut[src]
                    if pal.transparent:
                        keep = ~np.isin(src, list(pal.transparent))
                        img[ya:yb, xa:xb][keep] = rgb[keep]
                    else:
                        img[ya:yb, xa:xb] = rgb
        if self.display.root_group is not None and not self.display.root_group.hidden:
            draw(self.display.root_group, 0, 0)
        return img

    def picture(self):
        """compose() as a Pillow image, with the text labels drawn in a plain font at their place and scale."""
        from PIL import Image, ImageDraw, ImageFont
        im = Image.fromarray(self.compose(), "RGB")
        font = ImageFont.load_default()

        def labels(group):
            for item in group:
                if getattr(item, "hidden", False):
                    continue
                if isinstance(item, Group):
                    labels(item)
                elif isinstance(item, Label) and item.text:
                    l, t, r, b = font.getbbox(item.text)
                    mask = Image.new("L", (r + 2, b + 2), 0)
                    ImageDraw.Draw(mask).text((0, 0), item.text, font=font, fill=255)
                    mask = mask.resize((mask.width * item.scale, mask.height * item.scale), Image.NEAREST)
                    c = item.color
                    im.paste(((c >> 16) & 255, (c >> 8) & 255, c & 255), (item.x, item.y - mask.height // 2), mask)
        if self.display.root_group is not None:
            labels(self.display.root_group)
        return im


def load_image(path, *, bitmap=None, palette=None):
    """adafruit_imageload.load for the 8-bit indexed BMP files in screen/screens/."""
    from PIL import Image
    real = os.path.join(REPO, "screen", path.lstrip("/"))
    with open(real, "rb") as f:
        head = f.read(54)
    bits, = struct.unpack_from("<H", head, 28)
    used, = struct.unpack_from("<I", head, 46)
    if bits != 8:
        raise ValueError("%s is not an 8-bit indexed BMP" % path)
    count = used or 256
    im = Image.open(real)
    bmp = Bitmap(im.width, im.height, count)
    bmp.data[:] = im.tobytes()
    pal = Palette(count)
    flat = im.getpalette()[:count * 3]
    for i in range(len(flat) // 3):
        pal[i] = (flat[i * 3] << 16) | (flat[i * 3 + 1] << 8) | flat[i * 3 + 2]
    return bmp, pal
