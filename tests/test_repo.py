"""The parts of the repository that must agree with each other: keys, sounds, screen artwork, keypad layout, case
files and version. Also what must stay out of it: camera and location data in pictures, and paths from someone's
computer."""
import ast, glob, os, re, struct, sys, unittest, wave, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as f:
        return f.read()


def literal(source, name):
    """The value of a top-level `name = <literal>` in a Python source text."""
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


class Repository(unittest.TestCase):
    def setUp(self):
        self.pi = read("pi", "ws79.py")
        self.screen = read("screen", "code.py")
        self.channels = literal(self.pi, "CHANNELS")

    def test_five_channels_and_a_theme_key(self):
        self.assertEqual(sorted(self.channels), [1, 2, 3, 4, 5])
        self.assertEqual(literal(self.pi, "THEME_KEY"), 6)

    def test_every_sound_is_there_and_is_a_16_bit_wav(self):
        for n, (_freq, _label, name) in self.channels.items():
            path = os.path.join(REPO, "pi", "sounds", name)
            self.assertTrue(os.path.isfile(path), name)
            with wave.open(path, "rb") as w:
                self.assertEqual(w.getsampwidth(), 2, name)
                self.assertGreater(w.getnframes(), w.getframerate(), name)
        on_disk = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "pi", "sounds", "*.wav")))
        self.assertEqual(on_disk, sorted(c[2] for c in self.channels.values()), "no sound without a key, no key without a sound")

    def test_the_sounds_hold_no_tags(self):
        for path in glob.glob(os.path.join(REPO, "pi", "sounds", "*.wav")):
            with open(path, "rb") as f:
                head = f.read(64)
            self.assertEqual(head[:4], b"RIFF")
            self.assertEqual(head[12:16], b"fmt ")
            self.assertNotIn(b"LIST", head, os.path.basename(path))

    def test_every_channel_has_its_artwork(self):
        freq_to_ch = literal(self.screen, "FREQ_TO_CH")
        tuned = [c[0] for c in self.channels.values()] + [literal(self.pi, "STANDBY")[0]]
        for freq in tuned:
            self.assertIn(freq, freq_to_ch)
        for ch in freq_to_ch.values():
            path = os.path.join(REPO, "screen", "screens", "ch%s.bmp" % ch)
            self.assertTrue(os.path.isfile(path), path)
            with open(path, "rb") as f:
                head = f.read(54)
            self.assertEqual(head[:2], b"BM")
            self.assertEqual(struct.unpack_from("<ii", head, 18), (960, 240))
            self.assertEqual(struct.unpack_from("<H", head, 28)[0], 8, "the screen program reads 8-bit indexed pictures")

    def test_channel_labels_show_the_artwork_number(self):
        freq_to_ch = literal(self.screen, "FREQ_TO_CH")
        for freq, label, _name in self.channels.values():
            shown = int(re.match(r"CH (\d+)  ", label).group(1))
            self.assertEqual(shown, int(freq_to_ch[freq]), label)

    def test_the_keypad_layout_sends_the_six_keys_the_program_reads(self):
        layout = read("pi", "keypad.yaml")
        self.assertEqual(re.findall(r'"(f1[3-8])"', layout), ["f13", "f14", "f15", "f16", "f17", "f18"])
        for knob in ("volumedown", "volumeup", "mute"):
            self.assertIn(knob, layout)

    def test_the_panel_driver_is_set_to_12_mhz(self):
        self.assertIn('"frequency": 12000000', read("screen", "lib-patch", "bar240x960.py"))

    def test_every_case_part_comes_in_both_formats(self):
        stl = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(REPO, "print", "stl", "*.stl")))
        mf = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(REPO, "print", "3mf", "*.3mf")))
        self.assertEqual(stl, mf)
        self.assertGreaterEqual(len(stl), 5)

    def test_the_version_is_the_changelog_s_latest(self):
        version = read("VERSION").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        first = re.search(r"^## (\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M)
        self.assertIsNotNone(first)
        self.assertEqual(first.group(1), version)

    def test_the_service_file_is_a_template(self):
        service = read("pi", "ws79.service")
        self.assertIn("User=__USER__", service)
        self.assertIn("ExecStart=/usr/bin/python3 /opt/ws79/ws79.py", service)


def picture_size(path):
    """The width and height of a JPEG or PNG file, read from its header."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack_from(">II", data, 16)
    pos = 2
    while pos + 9 < len(data):
        marker, size = data[pos + 1], struct.unpack_from(">H", data, pos + 2)[0]
        if 0xC0 <= marker <= 0xC3:                           # the frame header holds the height, then the width
            h, w = struct.unpack_from(">HH", data, pos + 5)
            return w, h
        pos += 2 + size
    raise ValueError(path)


class Guides(unittest.TestCase):
    """The guides and what they show: the parts list, the pictures set side by side, the case plans."""

    def test_the_parts_list_has_23_parts_each_with_its_label_quantity_and_sheet(self):
        text = read("docs", "PARTS-BOM.md")
        rows = re.findall(r"^\| \*\*(A\d+)\*\* \| <img [^|]*\| \[[^]]+\]\(#(a\d+)\) \| ([^|]+) \|", text, re.M)
        self.assertEqual([r[0] for r in rows], ["A%d" % n for n in range(1, 24)])
        for label, anchor, qty in rows:
            self.assertEqual(anchor, label.lower())
            self.assertRegex(qty.strip(), r"^\*\*×\d", "%s has no quantity such as ×2" % label)
            self.assertIn('<a id="%s"></a>%s. ' % (anchor, label), text)
        for picture in re.findall(r'src="images/parts/([^"]+)"', text):
            self.assertTrue(os.path.isfile(os.path.join(REPO, "docs", "images", "parts", picture)), picture)

    def test_the_guides_name_parts_that_exist(self):
        for name in (("docs", "WIRING.md"), ("print", "README.md"), ("docs", "TROUBLESHOOTING.md")):
            text = read(*name)
            self.assertNotRegex(text, r"\(parts? \d", "%s still uses the old part numbers" % name[-1])
            for n in re.findall(r"\bA(\d+)\)", text):
                self.assertTrue(1 <= int(n) <= 23, "%s names part A%s" % (name[-1], n))

    def test_pictures_set_side_by_side_have_one_shape(self):
        seen = 0
        for path in repository_files():
            if not path.endswith(".md"):
                continue
            for row in re.findall(r"<p>\s*((?:<img [^>]+>\s*){2,})</p>", read(path)):
                sizes = [picture_size(os.path.normpath(os.path.join(os.path.dirname(path), src)))
                         for src in re.findall(r'src="([^"]+)"', row)]
                seen += 1
                ratios = set(round(w / h, 2) for w, h in sizes)
                self.assertEqual(len(ratios), 1, "%s shows pictures of different shapes side by side: %s" % (os.path.relpath(path, REPO), sizes))
        self.assertGreaterEqual(seen, 4)

    def test_the_four_close_ups_are_the_same_size(self):
        sizes = set(picture_size(os.path.join(REPO, "images", "renders", n))
                    for n in ("ws79-keys.jpg", "ws79-meters.jpg", "ws79-mic.jpg", "ws79-back-square.jpg"))
        self.assertEqual(len(sizes), 1, sizes)

    def test_the_case_guide_holds_the_tables_measured_on_the_print_files(self):
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import case_plans
        held = case_plans.blocks(read("print", "README.md"))
        self.assertEqual(held.get("parts"), case_plans.parts_table(), "run tools/case_plans.py")
        self.assertEqual(held.get("openings"), case_plans.openings_table(), "run tools/case_plans.py")
        count, w, h = case_plans.shell_vents()
        self.assertIn("%d vent slots of %s × %s mm" % (count, case_plans.mm(w), case_plans.mm(h)), read("print", "README.md"))

    def test_the_face_file_holds_its_openings_and_its_pocket(self):
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import case_plans
        face = case_plans.face()
        labels = [g["label"] for g in face["groups"]]
        self.assertNotIn("Other opening", labels)
        self.assertEqual(len(labels), 8)
        self.assertIsNotNone(face["pocket"], "the keypad's pocket is missing from the face file")
        self.assertAlmostEqual(face["pocket"]["depth"], 2.0, places=2)

    def test_the_two_halves_make_the_whole_face(self):
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import case_plans
        whole, left, right = (case_plans.load("ws79_front_panel_%s.stl" % n) for n in ("draft", "left", "right"))
        (wl, wh), (ll, lh), (rl, rh) = case_plans.box(whole), case_plans.box(left), case_plans.box(right)
        self.assertAlmostEqual(lh[0] - ll[0] + rh[0] - rl[0], wh[0] - wl[0], places=2)
        self.assertAlmostEqual(lh[0], rl[0], places=2, msg="the halves meet on one line")
        self.assertAlmostEqual(case_plans.volume_cm3(left) + case_plans.volume_cm3(right), case_plans.volume_cm3(whole), places=1)

    def test_every_3mf_file_holds_its_stl_s_triangles(self):
        for stl in glob.glob(os.path.join(REPO, "print", "stl", "*.stl")):
            with open(stl, "rb") as f:
                f.seek(80)
                triangles = struct.unpack("<I", f.read(4))[0]
            mf = os.path.join(REPO, "print", "3mf", os.path.basename(stl)[:-4] + ".3mf")
            with zipfile.ZipFile(mf) as z:
                model = z.read("3D/3dmodel.model").decode("utf-8")
            self.assertEqual(model.count("<triangle "), triangles, "run tools/make_3mf.py: %s is older than its STL" % os.path.basename(mf))


def repository_files():
    for folder, folders, names in os.walk(REPO):
        folders[:] = [d for d in folders if d not in (".git", "__pycache__")]
        for name in names:
            yield os.path.join(folder, name)


def jpeg_segments(data):
    """The marker and the content of each segment of a JPEG file, up to the picture data."""
    pos = 2
    while pos + 4 <= len(data) and data[pos] == 0xFF:
        marker = data[pos + 1]
        if marker == 0xDA:                                   # start of the picture data
            return
        size = struct.unpack_from(">H", data, pos + 2)[0]
        yield marker, data[pos + 4:pos + 2 + size]
        pos += 2 + size


def png_chunks(data):
    pos = 8
    while pos + 8 <= len(data):
        size, kind = struct.unpack_from(">I4s", data, pos)
        yield kind
        pos += 12 + size


class Privacy(unittest.TestCase):
    """A photo straight from a phone holds the place it was taken, and a file saved by a program can hold the path of
    the folder it came from. Neither belongs in a public repository."""

    def test_no_picture_holds_camera_or_location_data(self):
        seen = 0
        for path in repository_files():
            ext = os.path.splitext(path)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png"):
                continue
            seen += 1
            with open(path, "rb") as f:
                data = f.read()
            name = os.path.relpath(path, REPO)
            if ext == ".png":
                self.assertEqual([k for k in png_chunks(data) if k in (b"eXIf", b"tEXt", b"iTXt", b"zTXt")], [], name)
            else:
                self.assertEqual(data[:2], b"\xff\xd8", name)
                for marker, content in jpeg_segments(data):
                    # APP1 holds EXIF (with GPS) or XMP, APP13 holds IPTC, COM holds a comment
                    self.assertNotIn(marker, (0xE1, 0xED, 0xFE), "%s holds metadata: rebuild it from its pixels" % name)
        self.assertGreater(seen, 10)

    def test_no_text_file_holds_a_path_from_someone_s_computer(self):
        homes = ("/" + "Users" + "/", "\\" + "Users" + "\\", "/" + "home" + "/", "Drop" + "box")
        for path in repository_files():
            if os.path.splitext(path)[1].lower() not in (".py", ".md", ".sh", ".yaml", ".yml", ".service", ".txt", ".json"):
                continue
            if os.sep + "licenses" + os.sep in path:
                continue
            text = read(path)
            for home in homes:
                self.assertNotIn(home, text, os.path.relpath(path, REPO))

    def test_every_local_link_in_the_documents_points_at_a_file(self):
        seen = 0
        for path in repository_files():
            if not path.endswith(".md"):
                continue
            text = read(path)
            for target in re.findall(r"\]\(([^)\s]+)\)", text) + re.findall(r'<img src="([^"]+)"', text):
                if re.match(r"[a-z]+:", target) or target.startswith("#"):
                    continue
                seen += 1
                there = os.path.normpath(os.path.join(os.path.dirname(path), target.split("#")[0]))
                self.assertTrue(os.path.exists(there), "%s links to %s" % (os.path.relpath(path, REPO), target))
        self.assertGreater(seen, 20)


if __name__ == "__main__":
    unittest.main()
