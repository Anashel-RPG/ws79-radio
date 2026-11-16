"""The card setup utility: its two hashes against published test vectors, and a full run on a folder that stands in
for the card."""
import builtins, io, json, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "setup"))
import setup_sd

# A made-up public key in the right shape. It belongs to no one.
KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleKeyForTestsOnly000000000000000000000 ws79"


def fake_card(first_start_files=True):
    d = tempfile.mkdtemp(prefix="ws79-card-")
    with open(os.path.join(d, "config.txt"), "w") as f:
        f.write("[all]\n")
    with open(os.path.join(d, "cmdline.txt"), "w") as f:
        f.write("console=serial0,115200 console=tty1 root=PARTUUID=00000000-02 rootfstype=ext4 rootwait quiet\n")
    if first_start_files:
        for n in ("user-data", "meta-data", "network-config"):
            with open(os.path.join(d, n), "w") as f:
                f.write("# as shipped\n")
    return d


def config(**over):
    cfg = {"hostname": "ws79", "user": "agent", "pwhash": setup_sd.sha512_crypt("a-test-password"), "ssid": 'Lab "5G" net',
           "wifi_key": setup_sd.wifi_key('Lab "5G" net', "wifi-test-password"), "country": "US",
           "timezone": "America/New_York", "pubkey": KEY}
    cfg.update(over)
    return cfg


class Hashes(unittest.TestCase):
    def test_sha512_crypt_matches_the_specification(self):
        # Test vectors from Ulrich Drepper's SHA-crypt specification.
        self.assertEqual(setup_sd.sha512_crypt("Hello world!", salt="saltstring"),
                         "$6$saltstring$svn8UoSVapNtMuq1ukKS4tPQd8iKwSMHWjl/O817G3uBnIFNjnQJuesI68u4OTLiBFdcbYEdFCoEOfaS35inz1")
        self.assertEqual(setup_sd.sha512_crypt("Hello world!", salt="saltstringsaltstring", rounds=10000).split("$")[-1],
                         "OW1/O6BYHV6BcXZu8QVeXbDWra3Oeqh0sbHbbMCVNSnCM/UrjmM0Dp8vOuZeHBy/YTBmSK6H9qs/y3RnOaw5v.")

    def test_wifi_key_matches_the_standard(self):
        # Test vectors from IEEE 802.11i, annex H.4.
        self.assertEqual(setup_sd.wifi_key("IEEE", "password"),
                         "f42c6fc52df0ebef9ebb4b90b38a5f902e83fe1b135a70e23aed762e9710a12e")
        self.assertEqual(setup_sd.wifi_key("ThisIsASSID", "ThisIsAPassword"),
                         "0dc0d6eb90555ed6419756b9a15ec3e3209b63df707dd508d14581f8982721af")

    def test_a_new_salt_each_time(self):
        self.assertNotEqual(setup_sd.sha512_crypt("same"), setup_sd.sha512_crypt("same"))


class Names(unittest.TestCase):
    def test_hostnames(self):
        for good in ("ws79", "radio-2", "A1"):
            self.assertTrue(setup_sd.valid_hostname(good), good)
        for bad in ("", "-ws79", "ws79-", "ws 79", "ws_79", "ws79.local"):
            self.assertFalse(setup_sd.valid_hostname(bad), bad)

    def test_usernames(self):
        for good in ("pi", "agent_7", "a-b"):
            self.assertTrue(setup_sd.valid_username(good), good)
        for bad in ("", "root", "Pi", "7agent", "a b"):
            self.assertFalse(setup_sd.valid_username(bad), bad)


class Card(unittest.TestCase):
    def setUp(self):
        self.card = fake_card()
        self.addCleanup(shutil.rmtree, self.card, True)

    def write_and_check(self, cfg):
        iid = setup_sd.write_card(self.card, cfg)
        with redirect_stdout(io.StringIO()) as out:
            ok = setup_sd.check_card(self.card, cfg, iid)
        self.assertTrue(ok, out.getvalue())
        return iid

    def read(self, name):
        with open(os.path.join(self.card, name), encoding="utf-8") as f:
            return f.read()

    def test_key_and_password(self):
        cfg = config()
        self.write_and_check(cfg)
        ud = json.loads(self.read("user-data").split("\n", 1)[1])
        user = ud["users"][0]
        self.assertEqual(user["passwd"], cfg["pwhash"])
        self.assertEqual(user["ssh_authorized_keys"], [KEY])
        self.assertFalse(ud["ssh_pwauth"], "with a key on the Pi, SSH does not take passwords")
        self.assertTrue(os.path.exists(os.path.join(self.card, "ssh")))

    def test_key_only(self):
        self.write_and_check(config(pwhash=None))
        user = json.loads(self.read("user-data").split("\n", 1)[1])["users"][0]
        self.assertTrue(user["lock_passwd"])
        self.assertNotIn("passwd", user)

    def test_password_only(self):
        self.write_and_check(config(pubkey=None))
        ud = json.loads(self.read("user-data").split("\n", 1)[1])
        self.assertTrue(ud["ssh_pwauth"])
        self.assertNotIn("ssh_authorized_keys", ud["users"][0])

    def test_no_password_reaches_the_card(self):
        self.write_and_check(config())
        everything = "".join(self.read(n) for n in ("user-data", "network-config", "meta-data", "cmdline.txt"))
        self.assertNotIn("a-test-password", everything)
        self.assertNotIn("wifi-test-password", everything)

    def test_the_files_are_valid_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("needs PyYAML")
        self.write_and_check(config())
        ud = yaml.safe_load(self.read("user-data"))
        nc = yaml.safe_load(self.read("network-config"))
        self.assertEqual(ud["hostname"], "ws79")
        self.assertEqual(list(nc["network"]["wifis"]["wlan0"]["access-points"]), ['Lab "5G" net'])
        self.assertEqual(yaml.safe_load(self.read("meta-data"))["dsmode"], "local")

    def test_writing_twice_keeps_the_start_line_clean(self):
        self.write_and_check(config())
        first = self.read("cmdline.txt")
        self.write_and_check(config(country="FR"))
        second = self.read("cmdline.txt")
        self.assertEqual(first.count("\n"), 1)
        self.assertEqual(second.count("ieee80211_regdom="), 1)
        self.assertTrue(second.rstrip().endswith("cfg80211.ieee80211_regdom=FR"))
        self.assertIn("root=PARTUUID=00000000-02", second)

    def test_each_run_gets_a_new_setup_id(self):
        cfg = config()
        a = setup_sd.build_files(cfg, "ws79-1")["meta-data"]
        b = setup_sd.build_files(cfg, "ws79-2")["meta-data"]
        self.assertNotEqual(a, b)

    def test_a_card_without_first_start_files_is_refused(self):
        old = fake_card(first_start_files=False)
        self.addCleanup(shutil.rmtree, old, True)
        self.assertFalse(setup_sd.takes_first_start_files(old))
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                setup_sd.pick_boot(old)


class Conversation(unittest.TestCase):
    """The whole utility, with the keyboard replaced by scripted answers."""
    def run_main(self, typed, secrets_typed, pubkey=KEY, argv=(), wifi_names=("First net", "Home net")):
        card = fake_card()
        self.addCleanup(shutil.rmtree, card, True)
        typed, secrets_typed = iter(typed), iter(secrets_typed)

        def names(limit=9):
            if wifi_names is None:
                raise AssertionError("the Wi-Fi list was read although it is switched off")
            return list(wifi_names)
        saved = (builtins.input, setup_sd.getpass.getpass, setup_sd.known_wifi_names, setup_sd.ssh_public_key,
                 setup_sd.forget_old_host, setup_sd.eject, sys.argv)
        builtins.input = lambda prompt="": next(typed)
        setup_sd.getpass.getpass = lambda prompt="": next(secrets_typed)
        setup_sd.known_wifi_names = names
        setup_sd.ssh_public_key = lambda: pubkey
        setup_sd.forget_old_host = lambda hostname: ["radio.local"]
        setup_sd.eject = lambda boot: False
        sys.argv = ["setup_sd.py", "--card", card] + list(argv)
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                setup_sd.main()
        finally:
            (builtins.input, setup_sd.getpass.getpass, setup_sd.known_wifi_names, setup_sd.ssh_public_key,
             setup_sd.forget_old_host, setup_sd.eject, sys.argv) = saved
        with open(os.path.join(card, "user-data"), encoding="utf-8") as f:
            ud = json.loads(f.read().split("\n", 1)[1])
        with open(os.path.join(card, "network-config"), encoding="utf-8") as f:
            nc = json.load(f)
        return out.getvalue(), ud, nc

    def test_full_run(self):
        text, ud, nc = self.run_main(
            ["radio", "agent", "2", "us", "", "y"],        # name, user, Wi-Fi number 2, country, time zone, confirm
            ["wifi-test-password", "wifi-test-password", "a-test-password", "a-test-password"])
        self.assertIn("CHECK PASSED", text)
        self.assertIn("ssh agent@radio.local", text)
        self.assertNotIn("test-password", text)
        self.assertIn("known_hosts", text, "the utility says what it removed from known_hosts")
        self.assertEqual((ud["hostname"], ud["users"][0]["name"]), ("radio", "agent"))
        aps = nc["network"]["wifis"]["wlan0"]["access-points"]
        self.assertEqual(aps, {"Home net": {"password": setup_sd.wifi_key("Home net", "wifi-test-password")}})
        self.assertEqual(nc["network"]["wifis"]["wlan0"]["regulatory-domain"], "US")

    def test_without_a_key_the_utility_says_ssh_takes_the_password(self):
        text, ud, _nc = self.run_main(
            ["radio", "agent", "1", "us", "", "y"],
            ["wifi-test-password", "wifi-test-password", "a-test-password", "a-test-password"], pubkey=None)
        self.assertIn("No SSH key", text)
        self.assertTrue(ud["ssh_pwauth"])
        self.assertNotIn("test-password", text)

    def test_the_wifi_list_can_be_switched_off(self):
        text, _ud, nc = self.run_main(
            ["radio", "agent", "Typed net", "us", "", "y"],
            ["wifi-test-password", "wifi-test-password", "", ], argv=["--no-wifi-list"], wifi_names=None)
        self.assertIn("CHECK PASSED", text)
        self.assertNotIn("networks this computer knows", text)
        self.assertEqual(list(nc["network"]["wifis"]["wlan0"]["access-points"]), ["Typed net"])


@unittest.skipUnless(shutil.which("ssh-keygen"), "needs ssh-keygen")
class SshKey(unittest.TestCase):
    """The SSH key and known_hosts, with the real ssh-keygen and a folder that stands in for the home folder."""
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="ws79-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        patcher = mock.patch.dict(os.environ, {"HOME": self.home, "USERPROFILE": self.home})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.key = os.path.join(self.home, ".ssh", "id_ed25519")

    def make_key(self, passphrase=""):
        os.makedirs(os.path.dirname(self.key), mode=0o700)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", passphrase, "-f", self.key, "-C", "test"], check=True)
        with open(self.key + ".pub") as f:
            return f.read().split()[:2]

    def test_the_public_key_comes_from_the_private_key(self):
        real = self.make_key()
        with open(self.key + ".pub", "w") as f:
            f.write(KEY + "\n")                                    # a .pub file that no longer matches its key
        with redirect_stdout(io.StringIO()) as out:
            pub = setup_sd.ssh_public_key()
        self.assertEqual(pub.split()[:2], real)
        self.assertIn("does not match", out.getvalue())

    def test_a_key_with_a_passphrase_uses_its_pub_file_and_says_so(self):
        real = self.make_key("a-test-passphrase")
        with redirect_stdout(io.StringIO()) as out:
            pub = setup_sd.ssh_public_key()
        self.assertEqual(pub.split()[:2], real)
        self.assertIn("has a passphrase", out.getvalue())

    def test_a_new_key_leaves_the_passphrase_question_to_ssh_keygen(self):
        calls, real_run = [], subprocess.run

        def run(cmd, **kw):
            calls.append(list(cmd))
            if "-t" in cmd:                                         # the creation: answer the passphrase question here
                return real_run(list(cmd) + ["-N", ""], **kw)
            return real_run(cmd, **kw)
        with mock.patch.object(setup_sd.subprocess, "run", run), \
                mock.patch.object(builtins, "input", lambda prompt="": "y"), redirect_stdout(io.StringIO()) as out:
            pub = setup_sd.ssh_public_key()
        creation = [c for c in calls if "-t" in c]
        self.assertEqual(len(creation), 1)
        self.assertNotIn("-N", creation[0], "the utility must not choose an empty passphrase for the person")
        self.assertIn("passphrase", out.getvalue())
        self.assertTrue(pub.startswith("ssh-ed25519 "))
        self.assertTrue(os.path.exists(self.key))

    def test_declining_creates_no_key(self):
        with mock.patch.object(builtins, "input", lambda prompt="": "n"), redirect_stdout(io.StringIO()):
            self.assertIsNone(setup_sd.ssh_public_key())
        self.assertFalse(os.path.exists(self.key))

    def test_only_the_pi_s_earlier_identity_leaves_known_hosts(self):
        k = self.make_key()
        known = os.path.join(self.home, "known_hosts")
        with open(known, "w") as f:
            for host in ("radio.local", "radio", "other.local"):
                f.write("%s %s %s\n" % (host, k[0], k[1]))
        self.assertEqual(setup_sd.forget_old_host("radio", known), ["radio.local", "radio"])
        with open(known) as f:
            self.assertEqual([ln.split()[0] for ln in f if ln.strip()], ["other.local"])
        self.assertTrue(os.path.exists(known + ".old"), "ssh-keygen keeps the file as it was")
        self.assertEqual(setup_sd.forget_old_host("radio", known), [])


if __name__ == "__main__":
    unittest.main()
