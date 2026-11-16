"""The Pi installer, run on this computer against stand-ins for the Pi's commands and devices.

The test runs a copy of pi/install.sh whose system paths point into a temporary folder. Small scripts stand in for
sudo, apt-get, systemctl, lsusb, lsblk, curl, stty, mount, esptool, circup and the keypad tool, and each one writes
what it was asked to do in a log. The test then reads the log and the folder.

It checks the order of the steps and the decisions the script takes: what it skips, when it asks, what it refuses.
It does not check that the real commands answer the same way on a Pi.
"""
import glob, hashlib, io, os, re, shutil, subprocess, sys, tarfile, tempfile, unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "pi", "install.sh")
BASH = shutil.which("bash")

HUBS = ["Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub",
        "Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub",
        "Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub"]
KEYPAD = "Bus 001 Device 004: ID 1189:8890 Acer Communications & Multimedia "
FACTORY_BOARD = "Bus 001 Device 003: ID 239a:8147 Adafruit Qualia ESP32-S3 RGB666"
CIRCUITPYTHON_BOARD = "Bus 001 Device 006: ID 239a:8148 Adafruit Qualia-S3-RGB666"
HELLO = 'print("Hello World!")\n'                  # the program CircuitPython writes on a board it has just been put on

LOG = 'echo "%s $*" >> "$WS79_SANDBOX/log"\n'
STUBS = {
    "sudo": 'exec "$@"\n',
    "apt-get": LOG % "apt-get",
    "amixer": LOG % "amixer",
    "alsactl": LOG % "alsactl",
    "chown": LOG % "chown",
    "sync": "exit 0\n",
    "sleep": "exit 0\n",
    "systemctl": LOG % "systemctl" + 'case "$*" in *is-active*) [ ! -e "$WS79_SANDBOX/state/service-down" ] ;; esac\n',
    "lsusb": 'cat "$WS79_SANDBOX/state/lsusb"\n',
    "lsblk": ('case "$*" in\n'
              '  *MOUNTPOINT*) cat "$WS79_SANDBOX/state/mountpoint" 2>/dev/null; echo ;;\n'
              '  *) echo "mmcblk0p1 bootfs"; echo "mmcblk0p2 rootfs"\n'
              '     if [ -e "$WS79_SANDBOX/state/circuitpy" ]; then echo "sda1 CIRCUITPY"; fi ;;\n'
              'esac\n'),
    "curl": LOG % "curl" + 'cp "$WS79_SANDBOX/fixtures/$(basename "$4")" "$3"\n',          # curl -fsSL -o <file> <url>
    "stty": (LOG % "stty" +
             'if [ -e "$WS79_SANDBOX/state/touch-works" ]; then\n'                         # the board goes to its loader
             '  rm -f "$WS79_SANDBOX"/byid/*Qualia*\n'
             '  mkdir -p "$WS79_SANDBOX/usb/1-1.1/1-1.1:1.0" "$WS79_SANDBOX/sys/tty/ttyACM0"\n'
             '  echo 303a > "$WS79_SANDBOX/usb/1-1.1/idVendor"; echo 1001 > "$WS79_SANDBOX/usb/1-1.1/idProduct"\n'
             '  ln -sfn "$WS79_SANDBOX/usb/1-1.1/1-1.1:1.0" "$WS79_SANDBOX/sys/tty/ttyACM0/device"\n'
             'fi\n'),
    "mount": LOG % "mount" + 'for last; do :; done\nrmdir "$last" && ln -s "$WS79_SANDBOX/drive" "$last"\n',
    "umount": LOG % "umount" + 'rm -f "$1" && mkdir -p "$1"\n',
    "python3": ('if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then\n'
                '  echo "python3 -m venv" >> "$WS79_SANDBOX/log"\n'
                '  mkdir -p "$3/bin" && cp "$WS79_SANDBOX"/venv-stubs/* "$3/bin/"\n'
                'elif [ "$1" = "-" ]; then\n'
                '  cat > "$WS79_SANDBOX/state/restart-script"; echo "python3 restart-board" >> "$WS79_SANDBOX/log"\n'
                'fi\n'),
}
VENV_STUBS = {
    "pip": LOG % "pip",
    "esptool": (LOG % "esptool" +
                'case "$*" in *write-flash*)\n'                                            # the board starts CircuitPython
                '  touch "$WS79_SANDBOX/state/circuitpy"\n'
                '  rm -rf "$WS79_SANDBOX"/sys/tty/ttyACM*\n'
                "  printf 'print(\"Hello World!\")\\n' > \"$WS79_SANDBOX/drive/code.py\"\n"
                '  touch "$WS79_SANDBOX/byid/usb-Adafruit_Qualia-S3-RGB666_TEST-if00" ;;\n'
                'esac\n'),
    "circup": (LOG % "circup" +                                                            # circup --path <drive> install ...
               'if [ -e "$WS79_SANDBOX/state/circup-fails" ]; then exit 1; fi\n'
               'mkdir -p "$2/lib/adafruit_qualia/displays" && touch "$2/lib/adafruit_qualia/displays/bar240x960.mpy"\n'),
}
KEYPAD_TOOL = (LOG % "ch57x-keyboard-tool" +
               'if [ "$1" = "upload" ]; then cat > "$WS79_SANDBOX/state/keypad-upload"; fi\n')
SHA256SUM = '''import hashlib, sys
ok = True
for line in sys.stdin:
    want, _, path = line.rstrip("\\n").partition("  ")
    try:
        with open(path, "rb") as f:
            ok = ok and hashlib.sha256(f.read()).hexdigest() == want
    except OSError:
        ok = False
sys.exit(0 if ok else 1)
'''


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class Sandbox:
    """A folder that stands in for the Pi: its commands, its devices and the places the installer writes to."""
    def __init__(self, test):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="ws79-pi-"))
        test.addCleanup(shutil.rmtree, self.root, True)
        if " " in self.root:
            test.skipTest("the temporary folder's path holds a space")
        for d in ("bin", "venv-stubs", "state", "byid", "sys/tty", "usb", "opt", "etc", "mnt", "usrlocal/bin", "home",
                  "fixtures", "proc", "drive"):
            os.makedirs(self.path(d))
        self.write("proc/model", "Raspberry Pi 4 Model B Rev 1.5")
        self.usb = list(HUBS)
        for name, body in STUBS.items():
            self.command("bin/" + name, body)
        for name, body in VENV_STUBS.items():
            self.command("venv-stubs/" + name, body)
        if not shutil.which("sha256sum"):                       # a Mac has shasum and no sha256sum
            self.write("bin/sha256sum.py", SHA256SUM)
            self.command("bin/sha256sum", 'exec "%s" "%s"\n' % (sys.executable, self.path("bin/sha256sum.py")))
        # the two files the installer downloads: a keypad tool and a CircuitPython image, both made up
        self.command("fixtures/ch57x-keyboard-tool", KEYPAD_TOOL)
        self.write("fixtures/example-mapping.yaml", "orientation: normal\n")
        self.tool_archive = self.path("fixtures/ch57x-keyboard-tool-aarch64-unknown-linux-gnu.tar.gz")
        with tarfile.open(self.tool_archive, "w:gz") as tar:
            tar.add(self.path("fixtures/ch57x-keyboard-tool"), "ch57x-keyboard-tool")
            tar.add(self.path("fixtures/example-mapping.yaml"), "example-mapping.yaml")
        self.image = self.path("fixtures/adafruit-circuitpython-adafruit_qualia_s3_rgb666-en_US-10.3.2.bin")
        with open(self.image, "wb") as f:
            f.write(b"a stand-in for the CircuitPython image")

    def path(self, rel):
        return os.path.join(self.root, *rel.split("/"))

    def write(self, rel, text):
        with open(self.path(rel), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def command(self, rel, body):
        self.write(rel, "#!/bin/sh\n" + body)
        os.chmod(self.path(rel), 0o755)

    # ------------------------------------------------------------ what is plugged into the stand-in Pi
    def plug_keypad(self):
        self.usb.append(KEYPAD)

    def plug_new_board(self, goes_to_its_loader=True):
        """A screen board as it leaves the factory: a serial port, and no CircuitPython drive."""
        self.usb.append(FACTORY_BOARD)
        self.write("byid/usb-Adafruit_Qualia_ESP32-S3_RGB666_TEST-if00", "")
        if goes_to_its_loader:
            self.write("state/touch-works", "")

    def plug_board_with_circuitpython(self, program=HELLO, mounted_by_the_system=False):
        self.usb.append(CIRCUITPYTHON_BOARD)
        self.write("byid/usb-Adafruit_Qualia-S3-RGB666_TEST-if00", "")
        self.write("state/circuitpy", "")
        self.write("drive/code.py", program)
        if mounted_by_the_system:
            self.write("state/mountpoint", self.path("drive"))

    def plug_board_in_its_loader(self, n=0, product="1001"):
        """An ESP32-S3 board already waiting in its loader, as serial port ttyACM<n>. The loader's USB product is
        1001, or 0009 when CircuitPython sent the board there."""
        names = {"1001": "Espressif USB JTAG/serial debug unit", "0009": "Espressif ESP32-S3"}
        self.usb.append("Bus 001 Device %03d: ID 303a:%s %s" % (n + 9, product, names[product]))
        dev = "usb/1-1.%d" % (n + 5)
        os.makedirs(self.path(dev + "/if0"))
        os.makedirs(self.path("sys/tty/ttyACM%d" % n))
        self.write(dev + "/idVendor", "303a\n")
        self.write(dev + "/idProduct", product + "\n")
        os.symlink(self.path(dev + "/if0"), self.path("sys/tty/ttyACM%d/device" % n))

    # ------------------------------------------------------------ running the installer
    def script(self, typed, wrong_checksum):
        s = read(SCRIPT)
        swaps = [('REPO="$(cd "$(dirname "$0")/.." && pwd)"', 'REPO="%s"' % REPO),
                 ("/proc/device-tree/model", self.path("proc/model")),
                 ("/sys/class/tty/", self.path("sys/tty") + "/"),
                 ("/dev/serial/by-id/", self.path("byid") + "/"),
                 ("/opt/ws79", self.path("opt/ws79")),
                 ("/etc/systemd/system/", self.path("etc") + "/"),
                 ("/mnt/ws79-circuitpy", self.path("mnt/ws79-circuitpy")),
                 ("/usr/local/bin/", self.path("usrlocal/bin") + "/")]
        if typed is not None:                                   # an answer is typed: let the script read it from a pipe
            swaps.append(("if [ ! -t 0 ]; then", "if false; then"))
        for old, new in swaps:
            if old not in s:
                raise AssertionError("pi/install.sh no longer holds %r: update this test" % old)
            s = s.replace(old, new)
        for name, path in (("CH57X_SHA256", self.tool_archive), ("CP_SHA256", self.image)):
            with open(path, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            if wrong_checksum == name:
                digest = "0" * 64
            s, n = re.subn(r'%s="[0-9a-f]{64}"' % name, '%s="%s"' % (name, digest), s)
            if n != 1:
                raise AssertionError("pi/install.sh no longer sets %s" % name)
        return s

    def run(self, typed=None, wrong_checksum=None):
        """Run the installer. typed is what the person types at the question, or None when no one is at the keyboard."""
        self.write("state/lsusb", "\n".join(self.usb) + "\n")
        self.write("install.sh", self.script(typed, wrong_checksum))
        env = {"PATH": os.pathsep.join([self.path("bin"), self.path("usrlocal/bin"), os.environ["PATH"]]),
               "HOME": self.path("home"), "WS79_SANDBOX": self.root}
        if "TMPDIR" in os.environ:
            env["TMPDIR"] = os.environ["TMPDIR"]
        return subprocess.run([BASH, self.path("install.sh")], input=typed or "", capture_output=True, text=True,
                              env=env, timeout=120)

    def log(self):
        try:
            return read(self.path("log")).splitlines()
        except OSError:
            return []

    def logged(self, start):
        return [line for line in self.log() if line.startswith(start)]


@unittest.skipIf(BASH is None or os.name == "nt", "needs bash")
class Installer(unittest.TestCase):
    def setUp(self):
        self.pi = Sandbox(self)

    def ran_well(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("The WS-79 is running.", result.stdout)

    # ------------------------------------------------------------ the program and its service
    def test_with_nothing_plugged_in_the_radio_is_installed_and_the_parts_are_skipped(self):
        r = self.pi.run()
        self.ran_well(r)
        self.assertIn("The keypad is not plugged in.", r.stdout)
        self.assertIn("The screen board is not plugged in.", r.stdout)
        self.assertEqual(read(self.pi.path("opt/ws79/ws79.py")), read(os.path.join(REPO, "pi", "ws79.py")))
        there = sorted(os.listdir(self.pi.path("opt/ws79/sounds")))
        self.assertEqual(there, sorted(os.listdir(os.path.join(REPO, "pi", "sounds"))))
        service = read(self.pi.path("etc/ws79.service"))
        me = subprocess.run(["id", "-un"], capture_output=True, text=True).stdout.strip()
        self.assertIn("User=%s\n" % me, service)
        self.assertNotIn("__USER__", service)
        self.assertEqual(self.pi.logged("esptool"), [])
        self.assertEqual(self.pi.logged("ch57x-keyboard-tool"), [])
        self.assertTrue(os.access(self.pi.path("usrlocal/bin/ch57x-keyboard-tool"), os.X_OK), "the keypad tool is installed")
        steps = [line for line in r.stdout.splitlines() if line.startswith("== ")]
        self.assertEqual([s[3:9] for s in steps], ["1 of 5", "2 of 5", "3 of 5", "4 of 5", "5 of 5"])

    def test_the_keypad_gets_the_layout_then_its_light(self):
        self.pi.plug_keypad()
        self.ran_well(self.pi.run())
        self.assertEqual(self.pi.logged("ch57x-keyboard-tool"), ["ch57x-keyboard-tool upload", "ch57x-keyboard-tool led 1"])
        self.assertEqual(read(self.pi.path("state/keypad-upload")), read(os.path.join(REPO, "pi", "keypad.yaml")))

    def test_a_second_run_downloads_nothing_again(self):
        self.pi.plug_keypad()
        self.ran_well(self.pi.run())
        self.assertEqual(len(self.pi.logged("curl")), 1)
        self.ran_well(self.pi.run())
        self.assertEqual(len(self.pi.logged("curl")), 1, "the keypad tool is already installed")

    def test_a_download_that_differs_from_its_checksum_is_refused(self):
        r = self.pi.run(wrong_checksum="CH57X_SHA256")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match its recorded checksum", r.stdout)
        self.assertFalse(os.path.exists(self.pi.path("usrlocal/bin/ch57x-keyboard-tool")))

    def test_a_radio_that_does_not_start_is_reported(self):
        self.pi.write("state/service-down", "")
        r = self.pi.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("The program did not start.", r.stdout)

    # ------------------------------------------------------------ the screen board
    def test_a_new_board_is_never_erased_when_no_one_is_at_the_keyboard(self):
        self.pi.plug_new_board()
        r = self.pi.run()
        self.ran_well(r)
        self.assertIn("erases everything that is on the board", r.stdout)
        self.assertIn("not running in a terminal", r.stdout)
        self.assertIn("The board is left as it is.", r.stdout)
        self.assertEqual(self.pi.logged("esptool"), [])
        self.assertEqual(self.pi.logged("stty"), [], "the board is not even sent to its loader")

    def test_any_answer_other_than_yes_leaves_the_board_alone(self):
        for answer in ("y\n", "YES\n", "\n", "no\n"):
            with self.subTest(answer=answer):
                pi = Sandbox(self)
                pi.plug_new_board()
                r = pi.run(typed=answer)
                self.ran_well(r)
                self.assertIn("The board is left as it is.", r.stdout)
                self.assertEqual(pi.logged("esptool"), [])

    def test_after_a_typed_yes_a_new_board_gets_circuitpython_then_the_radio_s_files(self):
        self.pi.plug_new_board()
        r = self.pi.run(typed="yes\n")
        self.ran_well(r)
        self.assertIn("screen board ready", r.stdout)
        self.assertEqual(self.pi.logged("esptool"), ["esptool --chip esp32s3 --port /dev/ttyACM0 erase-flash",
                                                     "esptool --chip esp32s3 --port /dev/ttyACM0 write-flash -z 0x0 "
                                                     + self.pi.path("home/.ws79-tools/circuitpython-10.3.2.bin")])
        log = self.pi.log()
        order = [next(i for i, line in enumerate(log) if line.startswith(start)) for start in
                 ("stty", "esptool --chip esp32s3 --port /dev/ttyACM0 erase", "esptool --chip esp32s3 --port /dev/ttyACM0 write",
                  "mount", "circup", "umount", "python3 restart-board", "systemctl restart ws79")]
        self.assertEqual(order, sorted(order), "\n".join(log))
        drive = self.pi.path("drive")
        self.assertEqual(read(os.path.join(drive, "code.py")), read(os.path.join(REPO, "screen", "code.py")))
        pictures = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "screen", "screens", "*.bmp")))
        self.assertEqual(sorted(os.listdir(os.path.join(drive, "screens"))), pictures)
        displays = os.path.join(drive, "lib", "adafruit_qualia", "displays")
        self.assertEqual(os.listdir(displays), ["bar240x960.py"], "the 12 MHz driver replaces the library's own")
        self.assertEqual(glob.glob(os.path.join(drive, "code-before-ws79-*")), [], "CircuitPython's first program is not kept")
        self.assertIn("microcontroller.reset()", read(self.pi.path("state/restart-script")))
        self.assertFalse(os.path.islink(self.pi.path("mnt/ws79-circuitpy")), "the drive is unmounted")

    def test_a_board_already_in_its_loader_is_found_under_either_usb_identity(self):
        for product in ("1001", "0009"):
            with self.subTest(product=product):
                pi = Sandbox(self)
                pi.plug_board_in_its_loader(0, product)
                r = pi.run(typed="yes\n")
                self.ran_well(r)
                self.assertNotIn("not plugged in. Skipped: plug it in", r.stdout.split("4 of 5")[1])
                self.assertEqual(pi.logged("stty"), [], "no serial port to send to the loader: it is already there")
                self.assertEqual(len(pi.logged("esptool")), 2)
                self.assertIn("--port /dev/ttyACM0 erase-flash", pi.logged("esptool")[0])
                self.assertEqual(read(pi.path("drive/code.py")), read(os.path.join(REPO, "screen", "code.py")))

    def test_another_usb_serial_device_is_never_taken_for_the_loader(self):
        self.pi.plug_new_board(goes_to_its_loader=False)
        os.makedirs(self.pi.path("usb/1-1.9/if0"))                       # for example an Arduino on ttyACM3
        os.makedirs(self.pi.path("sys/tty/ttyACM3"))
        self.pi.write("usb/1-1.9/idVendor", "2341\n")
        self.pi.write("usb/1-1.9/idProduct", "0043\n")
        os.symlink(self.pi.path("usb/1-1.9/if0"), self.pi.path("sys/tty/ttyACM3/device"))
        r = self.pi.run(typed="yes\n")
        self.ran_well(r)
        self.assertIn("did not go to its loader, so nothing was erased", r.stdout)
        self.assertEqual(self.pi.logged("esptool"), [])

    def test_a_board_that_does_not_reach_its_loader_is_not_erased(self):
        self.pi.plug_new_board(goes_to_its_loader=False)
        r = self.pi.run(typed="yes\n")
        self.ran_well(r)
        self.assertIn("did not go to its loader, so nothing was erased", r.stdout)
        self.assertEqual(self.pi.logged("esptool"), [])

    def test_with_two_boards_in_their_loader_nothing_is_erased(self):
        self.pi.plug_new_board()                    # it becomes ttyACM0 in its loader
        self.pi.plug_board_in_its_loader(1)         # another board, already in its loader
        r = self.pi.run(typed="yes\n")
        self.ran_well(r)
        self.assertIn("More than one board is waiting in its loader", r.stdout)
        self.assertEqual(self.pi.logged("esptool"), [])

    def test_a_board_with_circuitpython_is_set_up_without_a_question(self):
        self.pi.plug_board_with_circuitpython()
        r = self.pi.run()
        self.ran_well(r)
        self.assertNotIn("erases", r.stdout)
        self.assertEqual(self.pi.logged("esptool"), [])
        self.assertEqual(read(self.pi.path("drive/code.py")), read(os.path.join(REPO, "screen", "code.py")))
        self.assertEqual(len(self.pi.logged("mount")), 1)
        self.assertEqual(len(self.pi.logged("umount")), 1)

    def test_a_drive_the_system_mounted_is_used_where_it_is(self):
        self.pi.plug_board_with_circuitpython(mounted_by_the_system=True)
        self.ran_well(self.pi.run())
        self.assertEqual(self.pi.logged("mount") + self.pi.logged("umount"), [])
        self.assertEqual(read(self.pi.path("drive/code.py")), read(os.path.join(REPO, "screen", "code.py")))

    def test_another_program_on_the_board_is_kept_under_a_new_name(self):
        theirs = "import board\nprint('my own project')\n"
        self.pi.plug_board_with_circuitpython(program=theirs)
        r = self.pi.run()
        self.ran_well(r)
        kept = glob.glob(self.pi.path("drive/code-before-ws79-*.py"))
        self.assertEqual(len(kept), 1, r.stdout)
        self.assertEqual(read(kept[0]), theirs)
        self.assertIn(os.path.basename(kept[0]), r.stdout)
        self.assertEqual(read(self.pi.path("drive/code.py")), read(os.path.join(REPO, "screen", "code.py")))

    def test_the_radio_s_own_program_is_replaced_without_a_copy(self):
        self.pi.plug_board_with_circuitpython(program=read(os.path.join(REPO, "screen", "code.py")) + "# an older version\n")
        self.ran_well(self.pi.run())
        self.assertEqual(glob.glob(self.pi.path("drive/code-before-ws79-*")), [])
        self.assertEqual(read(self.pi.path("drive/code.py")), read(os.path.join(REPO, "screen", "code.py")))

    def test_a_failure_half_way_leaves_no_drive_mounted_and_starts_the_radio_again(self):
        self.pi.plug_board_with_circuitpython()
        self.pi.write("state/circup-fails", "")
        r = self.pi.run()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("The WS-79 is running.", r.stdout)
        self.assertEqual(len(self.pi.logged("umount")), 1, "\n".join(self.pi.log()))
        self.assertFalse(os.path.islink(self.pi.path("mnt/ws79-circuitpy")))
        self.assertEqual(self.pi.log()[-1], "systemctl start ws79", "the radio it stopped in step 2 runs again")

    def test_a_run_that_ends_well_starts_the_radio_once(self):
        self.ran_well(self.pi.run())
        self.assertEqual(self.pi.logged("systemctl start"), [])
        self.assertEqual(len(self.pi.logged("systemctl restart ws79")), 1)

    # ------------------------------------------------------------ where it refuses to run
    def test_it_refuses_to_run_as_root(self):
        self.pi.command("bin/id", 'case "$1" in -un) echo root ;; *) echo 0 ;; esac\n')
        r = self.pi.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("without sudo", r.stdout)
        self.assertEqual(self.pi.log(), [])

    def test_it_refuses_to_run_on_another_computer(self):
        self.pi.write("proc/model", "Some other board")
        r = self.pi.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not look like a Raspberry Pi", r.stdout)
        self.assertEqual(self.pi.log(), [])


if __name__ == "__main__":
    unittest.main()
