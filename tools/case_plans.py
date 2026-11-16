#!/usr/bin/env python3
"""WS-79: draw the case's plans from its print files, and write the tables of print/README.md.

    python3 tools/case_plans.py             the drawings, into print/images/, and the tables of print/README.md
    python3 tools/case_plans.py --tables    the tables, as Markdown, on the screen

Every size comes from the STL files in print/stl/: the outline of each part, each opening of the face, each volume.
Nothing is typed in by hand, so a change to a print file shows in the drawings and in the tables. tests/test_repo.py
checks that print/README.md holds the tables this script writes.

Needs numpy and Pillow.
"""
import math, os, struct, sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(REPO, "print", "stl")
OUT = os.path.join(REPO, "print", "images")
FONTS = os.path.join(REPO, "tools", "fonts")

PARTS = [  # file, what it is, how many to make
    ("ws79_front_panel_draft.stl", "Face, in one piece", "1, or the two halves"),
    ("ws79_front_panel_left.stl", "Face, left half", "1, with the right half"),
    ("ws79_front_panel_right.stl", "Face, right half", "1, with the left half"),
    ("ws79_shell_draft.stl", "Shell", "1"),
    ("ws79_side_draft.stl", "Side", "2, the second one mirrored"),
]

# ---------------------------------------------------------------- reading a print file

def load(name):
    """The triangles of a binary STL file, as an array of shape (n, 3, 3), in millimetres."""
    with open(os.path.join(STL, name), "rb") as f:
        data = f.read()
    n = struct.unpack_from("<I", data, 80)[0]
    record = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    return np.frombuffer(data, dtype=record, count=n, offset=84)["v"].astype(np.float64)


def box(tri):
    pts = tri.reshape(-1, 3)
    return pts.min(0), pts.max(0)


def volume_cm3(tri):
    return abs(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum()) / 6000.0


def outlines(tri, axis, level, tol=1e-3):
    """The closed outlines of the flat face that lies at `level` along `axis`: the part's edge and every opening.
    Each outline is an array of points in the two other axes."""
    keep = [a for a in range(3) if a != axis]
    flat = tri[np.all(np.abs(tri[:, :, axis] - level) < tol, axis=1)][:, :, keep]
    count = {}
    for t in flat:
        ks = [(round(float(p[0]), 3), round(float(p[1]), 3)) for p in t]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = (ks[a], ks[b]) if ks[a] <= ks[b] else (ks[b], ks[a])
            count[e] = count.get(e, 0) + 1
    link = {}
    for (a, b), c in count.items():
        if c == 1:                               # an edge used once is on an outline
            link.setdefault(a, []).append(b)
            link.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in link:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            step = next((p for p in link[cur] if p != prev and p not in seen), None)
            if step is None:
                break
            loop.append(step)
            seen.add(step)
            prev, cur = cur, step
        if len(loop) >= 3:
            loops.append(np.array(loop))
    return loops


def area(loop):
    x, y = loop[:, 0], loop[:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2.0


def shape(loop):
    """A loop as a dictionary: round or rectangular, its size and its centre."""
    lo, hi = loop.min(0), loop.max(0)
    w, h = hi - lo
    round_ = abs(w - h) < 0.05 and 0.68 < area(loop) / (w * h) < 0.80        # a circle fills 0.785 of its square, a 12-sided one 0.75
    return {"round": bool(round_), "w": float(w), "h": float(h), "cx": float((lo[0] + hi[0]) / 2),
            "cy": float((lo[1] + hi[1]) / 2), "loop": loop}

# ---------------------------------------------------------------- the face

def face(name="ws79_front_panel_draft.stl"):
    """What the face file holds: its size, each opening seen from the front, and the pocket on its back if there is one."""
    tri = load(name)
    lo, hi = box(tri)
    front = sorted((shape(l) for l in outlines(tri, 2, hi[2])), key=lambda s: -s["w"] * s["h"])[1:]   # without the plate's own edge
    groups = []

    def group(label, pick, note=""):
        found = [s for s in front if pick(s)]
        for s in found:
            front.remove(s)
        if found:
            groups.append({"label": label, "shapes": found, "note": note})
    group("Window of the two bar screens", lambda s: not s["round"] and s["w"] > 150)
    group("Opening of the six keys", lambda s: not s["round"] and 30 < s["w"] <= 150)
    group("Hole of the knob", lambda s: s["round"] and 6 < s["w"] <= 12)
    group("Opening of a meter", lambda s: s["round"] and s["w"] > 30)
    group("Screw hole of a meter", lambda s: s["round"] and 2.6 < s["w"] < 2.95)
    group("Hole of the microphone socket", lambda s: s["round"] and 12 < s["w"] <= 30)
    group("Hole of the speaker grille", lambda s: s["round"] and 2.95 <= s["w"] < 3.2)
    corners = lambda s: s["round"] and abs(abs(s["cx"] - (lo[0] + hi[0]) / 2) - ((hi[0] - lo[0]) / 2 - 6)) < 0.6
    group("Corner hole for an M3 screw", corners)
    group("Other opening", lambda s: True)
    pocket = None
    levels = np.unique(np.round(tri.reshape(-1, 3)[:, 2], 3))
    for z in levels[1:-1]:                       # a flat face between the back and the front is the floor of a pocket
        inner = sorted((shape(l) for l in outlines(tri, 2, z)), key=lambda s: -s["w"] * s["h"])
        if inner and inner[0]["w"] > 20:
            pocket = dict(inner[0], depth=float(z - lo[2]))
    return {"lo": lo, "hi": hi, "groups": groups, "pocket": pocket, "tri": tri}


def mm(v):
    s = "%.1f" % v
    return s[:-2] if s.endswith(".0") else s


def parts_table():
    """The table of the parts to make, as Markdown text."""
    out = ["| Part | File | Size in mm | Volume | To make |", "|---|---|---|---|---|"]
    for name, label, count in PARTS:
        tri = load(name)
        lo, hi = box(tri)
        size = " × ".join(mm(v) for v in sorted(hi - lo, reverse=True))
        out.append("| %s | `%s` | %s | %s cm³ | %s |" % (label, name, size, mm(volume_cm3(tri)), count))
    return "\n".join(out) + "\n"


def shell_vents():
    """The vent slots on the top of the shell: how many, and the size of one."""
    tri = load("ws79_shell_draft.stl")
    slots = [shape(l) for l in outlines(tri, 2, box(tri)[1][2])]
    slots = [q for q in slots if q["w"] < 20 or q["h"] < 20]
    return len(slots), min(slots[0]["w"], slots[0]["h"]), max(slots[0]["w"], slots[0]["h"])


def openings_table():
    """The table of the face's openings, as Markdown text."""
    f = face()
    x0, y0 = f["lo"][0], f["lo"][1]
    out = ["| No. | Opening | Size in mm | Centre, from the left edge | Centre, from the bottom edge | How many |",
           "|---|---|---|---|---|---|"]
    for n, g in enumerate(f["groups"], 1):
        s = g["shapes"]
        size = ("⌀ " + mm(s[0]["w"])) if s[0]["round"] else "%s × %s" % (mm(s[0]["w"]), mm(s[0]["h"]))
        if len(s) > 8:                           # the grille: give the whole pattern
            xs = [k["cx"] for k in s]
            ys = [k["cy"] for k in s]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            across = max(max(xs) - min(xs), max(ys) - min(ys)) + s[0]["w"]
            out.append("| %d | %s | %s, in a pattern %s across | %s | %s | %d |" % (n, g["label"], size, mm(across), mm(cx - x0), mm(cy - y0), len(s)))
        else:
            xs = sorted(set(mm(k["cx"] - x0) for k in s), key=float)
            ys = sorted(set(mm(k["cy"] - y0) for k in s), key=float)
            out.append("| %d | %s | %s | %s | %s | %d |" % (n, g["label"], size, ", ".join(xs), ", ".join(ys), len(s)))
    if f["pocket"]:
        p = f["pocket"]
        out.append("| %d | Pocket for the keypad, on the back, %s mm deep | %s × %s | %s | %s | 1 |"
                   % (len(f["groups"]) + 1, mm(p["depth"]), mm(p["w"]), mm(p["h"]), mm(p["cx"] - x0), mm(p["cy"] - y0)))
    return "\n".join(out) + "\n"

# ---------------------------------------------------------------- drawing

INK, PLATE, PAPER, MUTED, GREEN = (17, 20, 24), (232, 235, 238), (255, 255, 255), (74, 82, 96), (29, 107, 69)
SS = 2                                           # the drawings are made at twice their size, then reduced


class Sheet:
    """A white sheet to draw on in millimetres, with size lines, numbered marks and labels."""
    def __init__(self, width, height):
        from PIL import Image, ImageDraw, ImageFont
        self.Image = Image
        self.im = Image.new("RGB", (width * SS, height * SS), PAPER)
        self.d = ImageDraw.Draw(self.im)
        self.font = lambda size, bold=False: ImageFont.truetype(os.path.join(FONTS, "Exo-Bold.ttf" if bold else "Exo-Medium.ttf"), size * SS)
        self.k, self.ox, self.oy = 1.0, 0.0, 0.0

    def view(self, k, ox, oy):
        """Set the scale (pixels per millimetre) and the pixel that stands for the point (0, 0). y grows upward."""
        self.k, self.ox, self.oy = k, ox, oy

    def p(self, x, y):
        return ((self.ox + x * self.k) * SS, (self.oy - y * self.k) * SS)

    def poly(self, pts, fill=None, outline=INK, width=2):
        q = [self.p(x, y) for x, y in pts]
        if fill is not None:
            self.d.polygon(q, fill=fill)
        if outline is not None:
            self.d.line(q + [q[0]], fill=outline, width=width * SS, joint="curve")

    def line(self, a, b, fill=INK, width=2, dash=None):
        (x0, y0), (x1, y1) = self.p(*a), self.p(*b)
        if not dash:
            self.d.line([(x0, y0), (x1, y1)], fill=fill, width=width * SS)
            return
        length = math.hypot(x1 - x0, y1 - y0)
        on, off = dash[0] * SS, dash[1] * SS
        t = 0.0
        while t < length:
            u = min(t + on, length)
            self.d.line([(x0 + (x1 - x0) * t / length, y0 + (y1 - y0) * t / length),
                         (x0 + (x1 - x0) * u / length, y0 + (y1 - y0) * u / length)], fill=fill, width=width * SS)
            t += on + off

    def dashed(self, pts, fill=GREEN, width=2, dash=(10, 6)):
        for a, b in zip(pts, list(pts[1:]) + [pts[0]]):
            self.line(a, b, fill, width, dash)

    def text(self, x, y, s, size=20, bold=False, fill=INK, anchor="mm", px=False):
        pos = (x * SS, y * SS) if px else self.p(x, y)
        self.d.text(pos, s, font=self.font(size, bold), fill=fill, anchor=anchor)

    def mark(self, x, y, n, to=None):
        """A numbered mark at (x, y), with a thin line to the point it names."""
        cx, cy = self.p(x, y)
        if to is not None:
            self.d.line([(cx, cy), self.p(*to)], fill=INK, width=SS + 1)
            tx, ty = self.p(*to)
            self.d.ellipse([tx - 4 * SS, ty - 4 * SS, tx + 4 * SS, ty + 4 * SS], fill=INK)
        r = 17 * SS
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PAPER, outline=INK, width=2 * SS)
        self.d.text((cx, cy), str(n), font=self.font(18, True), fill=INK, anchor="mm")

    def size(self, a, b, label, offset=0.0, side=1):
        """A size line from a to b (millimetres), moved `offset` pixels to one side, with its label in the middle."""
        (x0, y0), (x1, y1) = self.p(*a), self.p(*b)
        length = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / length * side, (x1 - x0) / length * side
        o = offset * SS
        x0, y0, x1, y1 = x0 + nx * o, y0 + ny * o, x1 + nx * o, y1 + ny * o
        self.d.line([(x0, y0), (x1, y1)], fill=MUTED, width=SS + 1)
        for x, y in ((x0, y0), (x1, y1)):
            self.d.line([(x - nx * 9 * SS, y - ny * 9 * SS), (x + nx * 9 * SS, y + ny * 9 * SS)], fill=MUTED, width=SS + 1)
        font = self.font(20, True)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        box_ = self.d.textbbox((cx, cy), label, font=font, anchor="mm")
        self.d.rectangle([box_[0] - 8 * SS, box_[1] - 5 * SS, box_[2] + 8 * SS, box_[3] + 5 * SS], fill=PAPER)
        self.d.text((cx, cy), label, font=font, fill=INK, anchor="mm")

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        w, h = self.im.size
        self.im.resize((w // SS, h // SS), self.Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
        print("wrote print/images/" + name)


def draw_plate(sheet, tri, x0, y0, with_marks=None):
    """A face file seen from the front, with its lower left corner at (0, 0)."""
    lo, hi = box(tri)
    loops = sorted(outlines(tri, 2, hi[2]), key=area, reverse=True)
    w, h = hi[0] - lo[0], hi[1] - lo[1]
    sheet.poly([(0, 0), (w, 0), (w, h), (0, h)], fill=PLATE, outline=INK, width=3)
    for l in loops[1:]:
        sheet.poly([(x - x0, y - y0) for x, y in l], fill=PAPER, outline=INK, width=2)
    return w, h


def face_plan():
    f = face()
    x0, y0 = f["lo"][0], f["lo"][1]
    w, h = f["hi"][0] - x0, f["hi"][1] - y0
    k = 3.8
    s = Sheet(1600, 800)
    s.view(k, 130, 130 + h * k)
    draw_plate(s, f["tri"], x0, y0)
    if f["pocket"]:
        s.dashed([(x - x0, y - y0) for x, y in f["pocket"]["loop"]])
    left = load("ws79_front_panel_left.stl")
    split = box(left)[1][0] - x0
    s.line((split, -6), (split, h + 6), fill=GREEN, width=2, dash=(12, 7))
    s.text(split + 3, h + 8, "the two halves meet here, %s from the left edge" % mm(split), size=17, fill=GREEN, anchor="lb")
    s.size((0, h), (w, h), "%s mm" % mm(w), offset=92, side=-1)
    s.size((0, 0), (0, h), "%s mm" % mm(h), offset=62, side=-1)
    # the numbered marks, one per kind of opening, placed beside the first opening of its kind
    for n, g in enumerate(f["groups"], 1):
        first = min(g["shapes"], key=lambda q: (q["cx"], -q["cy"]))
        cx, cy = first["cx"] - x0, first["cy"] - y0
        if len(g["shapes"]) > 8:                 # the grille: mark its middle, from below
            xs = [q["cx"] - x0 for q in g["shapes"]]
            ys = [q["cy"] - y0 for q in g["shapes"]]
            s.mark((min(xs) + max(xs)) / 2, min(ys) - 9, n)
        elif first["w"] < 12:                    # a small hole: the mark stands beside it
            dx = 9 if cx < w / 2 else -9
            s.mark(cx + dx, cy + (-9 if cy > h / 2 else 9) * (1 if first["w"] < 5 else 1.4), n, to=(cx, cy))
        else:
            s.mark(cx, cy, n)
    if f["pocket"]:
        p = f["pocket"]
        left, mid = p["cx"] - x0 - p["w"] / 2, p["cy"] - y0
        s.mark(left - 7, mid + 16, len(f["groups"]) + 1, to=(left, mid + 16))
    # where the centres are, from the left edge
    big = [q for g in f["groups"] for q in g["shapes"] if q["w"] > 5]
    grille = [q for g in f["groups"] if len(g["shapes"]) > 8 for q in g["shapes"]]
    xs = sorted(set(round(q["cx"] - x0, 1) for q in big if q["w"] < 150))
    if grille:
        gx = [q["cx"] - x0 for q in grille]
        xs = sorted(set(xs + [round((min(gx) + max(gx)) / 2, 1)]))
    base = -13.5
    s.line((0, base), (w, base), fill=MUTED, width=1)
    for x in [0.0] + xs + [w]:
        s.line((x, base - 2.2), (x, base + 2.2), fill=MUTED, width=2)
        s.text(x, base - 4, mm(x), size=17, bold=True, anchor="mt")
    s.text(0, base - 12.5, "Centres of the openings, in millimetres from the left edge", size=17, fill=MUTED, anchor="lt")
    s.save("face-plan.png")


def face_halves():
    left, right = load("ws79_front_panel_left.stl"), load("ws79_front_panel_right.stl")
    (llo, lhi), (rlo, rhi) = box(left), box(right)
    lw, rw, h = lhi[0] - llo[0], rhi[0] - rlo[0], lhi[1] - llo[1]
    k, gap = 3.6, 18.0
    s = Sheet(1600, 640)
    s.view(k, 80, 96 + h * k)
    draw_plate(s, left, llo[0], llo[1])
    s.size((0, h), (lw, h), "left half, %s mm" % mm(lw), offset=44, side=-1)
    s.view(k, 80 + (lw + gap) * k, 96 + h * k)
    draw_plate(s, right, rlo[0], rlo[1])
    s.size((0, h), (rw, h), "right half, %s mm" % mm(rw), offset=44, side=-1)
    s.size((rw, 0), (rw, h), "%s mm" % mm(h), offset=50, side=1)
    s.save("face-halves.png")


def side_profile():
    tri = load("ws79_side_draft.stl")
    lo, hi = box(tri)
    loop = max(outlines(tri, 0, hi[0]), key=area)            # the board's large flat face
    pts = [(y - lo[1], z - lo[2]) for y, z in loop]
    d, h = hi[1] - lo[1], hi[2] - lo[2]
    k = 3.6
    s = Sheet(1000, 720)
    s.view(k, 150, 110 + h * k)
    s.poly(pts, fill=PLATE, outline=INK, width=3)
    s.size((0, 0), (d, 0), "%s mm" % mm(d), offset=46, side=1)
    s.size((0, 0), (0, h), "%s mm" % mm(h), offset=62, side=-1)
    # the edge that leans is the front of the case
    lean = None
    for (ya, za), (yb, zb) in zip(pts, pts[1:] + pts[:1]):
        length = math.hypot(yb - ya, zb - za)
        angle = abs(math.degrees(math.atan2(yb - ya, zb - za)))
        angle = min(angle, 180 - angle)
        if length > 60 and 3 < angle < 40:
            lean = (angle, ((ya + yb) / 2, (za + zb) / 2))
    if lean:
        front_at_left = lean[1][0] < d / 2
        s.text(lean[1][0] + (9 if front_at_left else -9), lean[1][1] + 12, "the front leans back %s°" % mm(lean[0]), size=19, bold=True,
               anchor="lm" if front_at_left else "rm")
    s.text(d / 2 + 8, h / 2 - 14, "a board %s mm thick" % mm(hi[0] - lo[0]), size=19, fill=MUTED)
    s.save("side-profile.png")


def drawn_edges(tri, along, limit=25.0):
    """The edges a line drawing shows when the part is seen along the axis `along`: those where two faces meet at an
    angle, and those where the surface turns away from the eye."""
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    faces = {}
    for i, t in enumerate(tri):
        ks = [tuple(float(v) for v in np.round(p, 3)) for p in t]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = (ks[a], ks[b]) if ks[a] <= ks[b] else (ks[b], ks[a])
            faces.setdefault(e, []).append(i)
    cos = math.cos(math.radians(limit))
    out = []
    for e, fs in faces.items():
        if len(fs) != 2:
            out.append(e)
            continue
        a, b = n[fs[0]], n[fs[1]]
        if float(np.dot(a, b)) < cos or (a[along] > 1e-6) != (b[along] > 1e-6):       # one face looks at the eye, the other does not
            out.append(e)
    return out


def shell_views():
    tri = load("ws79_shell_draft.stl")
    lo, hi = box(tri)
    w, d, h = hi - lo
    k, gap = 2.35, 90
    s = Sheet(1600, int(110 + d * k + gap + h * k + 100))
    left, top = 120, 90
    views = (("from above", 0, 1, left, top + d * k, w, d),
             ("from the front", 0, 2, left, top + d * k + gap + h * k, w, h),
             ("from the side", 1, 2, left + w * k + gap + 40, top + d * k + gap + h * k, d, h))
    for label, ax, ay, ox, oy, vw, vh in views:
        s.view(k, ox, oy)
        for a, b in drawn_edges(tri, 3 - ax - ay):
            s.line((a[ax] - lo[ax], a[ay] - lo[ay]), (b[ax] - lo[ax], b[ay] - lo[ay]), fill=INK, width=1)
        s.size((0, 0), (vw, 0), "%s mm" % mm(vw), offset=40, side=1)
        s.text(0, vh + 7, label, size=19, bold=True, anchor="lb")
    s.view(k, left, top + d * k)
    s.size((0, 0), (0, d), "%s mm" % mm(d), offset=58, side=-1)
    s.view(k, left, top + d * k + gap + h * k)
    s.size((0, 0), (0, h), "%s mm" % mm(h), offset=58, side=-1)
    s.save("shell-views.png")


def tables():
    n, w, h = shell_vents()
    return parts_table() + "\n" + openings_table() + "\nThe shell's top has %d vent slots of %s × %s mm.\n" % (n, mm(w), mm(h))


def blocks(text):
    """The parts of print/README.md that this script writes: name -> text between its two marker lines."""
    found = {}
    for name in ("parts", "openings"):
        a, b = "<!-- case_plans:%s -->\n" % name, "<!-- /case_plans:%s -->" % name
        if a in text and b in text:
            found[name] = text.split(a, 1)[1].split(b, 1)[0]
    return found


def update_readme():
    path = os.path.join(REPO, "print", "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for name, new in (("parts", parts_table()), ("openings", openings_table())):
        a, b = "<!-- case_plans:%s -->\n" % name, "<!-- /case_plans:%s -->" % name
        head, rest = text.split(a, 1)
        text = head + a + new + b + rest.split(b, 1)[1]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote the two tables of print/README.md")


if __name__ == "__main__":
    if "--tables" in sys.argv:
        sys.stdout.write(tables())
    else:
        face_plan()
        face_halves()
        side_profile()
        shell_views()
        update_readme()
