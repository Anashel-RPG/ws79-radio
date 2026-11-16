#!/usr/bin/env python3
"""WS-79: set up a Raspberry Pi OS card from a Mac, a Windows PC or a Linux computer.

Write Raspberry Pi OS (64-bit) to the card with Raspberry Pi Imager, put the card back in the computer, then run:

    python3 setup/setup_sd.py          (Mac, Linux)
    py setup\\setup_sd.py              (Windows)

It asks for the Pi's name, a user, a password and the Wi-Fi network, finds or creates your SSH key, writes the
first-start files that Raspberry Pi OS reads (cloud-init), then reads them back from the card and checks them.
It also works on a card that has already started once: use it to change the Wi-Fi or the user without writing the
card again.

What it stores on the card: the hash of the user's password, the Wi-Fi key derived from the Wi-Fi password, and the
public half of the SSH key. The two passwords and the private key stay on this computer. Nothing is sent anywhere.
The Wi-Fi key is enough to join that one network, so keep the card as you would keep the Wi-Fi password.

Standard library only. Needs Python 3.8 or later.
"""
import argparse, getpass, glob, hashlib, json, locale, os, platform, re, secrets, shutil, string, subprocess, sys, time

try:
    import readline          # arrow keys and editing in the questions (the Windows console edits by itself)
except ImportError:
    pass

GROUPS = "users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo"

# ---------------------------------------------------------------- finding the card

def boot_candidates():
    """Mounted volumes that look like a Raspberry Pi boot partition."""
    system = platform.system()
    if system == "Darwin":
        paths = glob.glob("/Volumes/*")
    elif system == "Windows":
        paths = ["%s:\\" % c for c in string.ascii_uppercase[3:]]
    else:
        paths = glob.glob("/media/*/*") + glob.glob("/run/media/*/*") + glob.glob("/media/*") + glob.glob("/mnt/*")
    found = []
    for p in paths:
        try:
            if os.path.isfile(os.path.join(p, "cmdline.txt")) and os.path.isfile(os.path.join(p, "config.txt")):
                found.append(p)
        except OSError:
            pass
    return found


def takes_first_start_files(boot):
    """Raspberry Pi OS reads user-data, network-config and meta-data only on the images that ship them."""
    return any(os.path.isfile(os.path.join(boot, n)) for n in ("user-data", "meta-data"))


def pick_boot(explicit=None):
    while True:
        found = [explicit] if explicit else boot_candidates()
        if explicit and not os.path.isfile(os.path.join(explicit, "cmdline.txt")):
            sys.exit("%s is not a Raspberry Pi boot partition (no cmdline.txt)." % explicit)
        if len(found) == 1:
            boot = found[0]
        elif len(found) > 1:
            for i, p in enumerate(found, 1):
                print("  %d. %s" % (i, p))
            n = ask("Which one is the Pi's card", "1")
            if not (n.isdigit() and 1 <= int(n) <= len(found)):
                continue
            boot = found[int(n) - 1]
        else:
            print("No Raspberry Pi card found. Put the card in this computer: its 'bootfs' drive should appear.")
            input("Press Enter to look again, or Ctrl-C to stop. ")
            continue
        if not takes_first_start_files(boot):
            sys.exit("The card at %s holds a system that does not read these first-start files.\n"
                     "Write the current Raspberry Pi OS (64-bit) to it with Raspberry Pi Imager, then run this again." % boot)
        print("SD card found: %s" % boot)
        return boot

# ---------------------------------------------------------------- questions

def ask(question, default=None):
    answer = input("%s%s: " % (question, " [%s]" % default if default else "")).strip()
    return answer or (default or "")


def ask_valid(question, default, check, why):
    while True:
        answer = ask(question, default)
        if check(answer):
            return answer
        print("  " + why)


def ask_secret(question, min_len=0, optional=False):
    while True:
        a = getpass.getpass("%s (hidden as you type): " % question)
        if optional and a == "":
            return ""
        b = getpass.getpass("Again, to be sure: ")
        if a != b:
            print("  The two entries differ. Try again.")
        elif len(a) < min_len:
            print("  At least %d characters." % min_len)
        else:
            return a


def valid_hostname(name):
    return bool(re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?", name))


def valid_username(name):
    return bool(re.fullmatch(r"[a-z_][a-z0-9_-]{0,30}", name)) and name != "root"

# ---------------------------------------------------------------- the user's password: SHA-512 crypt ($6$)

_B64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _b64_from_24bit(b2, b1, b0, n):
    w = (b2 << 16) | (b1 << 8) | b0
    out = ""
    for _ in range(n):
        out += _B64[w & 0x3F]
        w >>= 6
    return out


def sha512_crypt(password, salt=None, rounds=5000):
    """The « $6$ » hash of /etc/shadow (Ulrich Drepper's SHA-crypt). The card stores this, never the password."""
    if salt is None:
        salt = "".join(secrets.choice(_B64) for _ in range(16))
    p, s = password.encode(), salt.encode()[:16]
    b = hashlib.sha512(p + s + p).digest()
    a = hashlib.sha512(p + s)
    for _ in range(len(p) // 64):
        a.update(b)
    a.update(b[:len(p) % 64])
    i = len(p)
    while i:
        a.update(b if i & 1 else p)
        i >>= 1
    a = a.digest()
    dp = hashlib.sha512(p * len(p)).digest()
    P = (dp * (len(p) // 64 + 1))[:len(p)]
    ds = hashlib.sha512(s * (16 + a[0])).digest()
    S = (ds * (len(s) // 64 + 1))[:len(s)]
    c = a
    for r in range(rounds):
        h = hashlib.sha512()
        h.update(P if r & 1 else c)
        if r % 3:
            h.update(S)
        if r % 7:
            h.update(P)
        h.update(c if r & 1 else P)
        c = h.digest()
    order = [(0, 21, 42), (22, 43, 1), (44, 2, 23), (3, 24, 45), (25, 46, 4), (47, 5, 26), (6, 27, 48),
             (28, 49, 7), (50, 8, 29), (9, 30, 51), (31, 52, 10), (53, 11, 32), (12, 33, 54), (34, 55, 13),
             (56, 14, 35), (15, 36, 57), (37, 58, 16), (59, 17, 38), (18, 39, 60), (40, 61, 19), (62, 20, 41)]
    out = "".join(_b64_from_24bit(c[x], c[y], c[z], 4) for x, y, z in order) + _b64_from_24bit(0, 0, c[63], 2)
    return "$6$%s$%s" % (salt, out)

# ---------------------------------------------------------------- the Wi-Fi

def wifi_key(ssid, password):
    """The 256-bit key WPA2 derives from the network name and its password, as 64 hex digits (PBKDF2, 4096 rounds).
    The card stores this key and not the password. The key is enough to join that one network."""
    return hashlib.pbkdf2_hmac("sha1", password.encode(), ssid.encode(), 4096, 32).hex()


def _run(cmd, timeout=8):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def known_wifi_names(limit=9):
    """Wi-Fi names this computer knows, the most likely first. Empty when the system does not give them."""
    names, system = [], platform.system()
    if system == "Darwin":
        ports = _run(["networksetup", "-listallhardwareports"])
        m = re.search(r"Hardware Port: (?:Wi-Fi|AirPort)\s*\nDevice: (\S+)", ports)
        if m:
            out = _run(["networksetup", "-listpreferredwirelessnetworks", m.group(1)])
            names = [ln.strip() for ln in out.splitlines()[1:] if ln.strip()]
    elif system == "Windows":
        out = _run(["netsh", "wlan", "show", "interfaces"])
        names = [m.group(1).strip() for m in re.finditer(r"^\s*SSID\s*:\s*(.+)$", out, re.M)]
    else:
        out = _run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
        rows = [ln.split(":", 1) for ln in out.splitlines() if ":" in ln]
        names = [s for a, s in rows if a == "yes"] + [s for a, s in rows if a != "yes"]
    seen, unique = set(), []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            unique.append(n)
    return unique[:limit]


def ask_wifi_name(listing=True):
    """The network's name: picked from the networks this computer knows, or typed when listing is off."""
    names = known_wifi_names() if listing else []
    if names:
        print("Wi-Fi networks this computer knows:")
        for i, n in enumerate(names, 1):
            print("  %d. %s" % (i, n))
        while True:
            a = ask("Number of the network the Pi will use, or type its name")
            if a.isdigit() and 1 <= int(a) <= len(names):
                return names[int(a) - 1]
            if a and not a.isdigit():
                return a
    while True:
        a = ask("Wi-Fi network name (exactly, with its capitals)")
        if a:
            return a

# ---------------------------------------------------------------- the SSH key

def ssh_public_key():
    """This computer's ed25519 public key, derived from the private key so a stale .pub file never reaches the Pi.
    Offers to create the key when there is none. Returns None when there is no key to use."""
    key = os.path.join(os.path.expanduser("~"), ".ssh", "id_ed25519")
    keygen = shutil.which("ssh-keygen")
    if not keygen:
        print("ssh-keygen was not found. On Windows: Settings, Apps, Optional features, OpenSSH Client.")
        return None
    if not os.path.exists(key):
        if not ask("This computer has no SSH key yet. Create one now (y/n)", "y").lower().startswith("y"):
            return None
        print("Creating %s. ssh-keygen now asks for a passphrase: it protects the key if someone copies it from\n"
              "this computer. Press Enter twice for a key without one." % key)
        os.makedirs(os.path.dirname(key), mode=0o700, exist_ok=True)
        if subprocess.run([keygen, "-q", "-t", "ed25519", "-f", key, "-C", "ws79"]).returncode != 0:
            print("  The key was not created.")
            return None
    r = subprocess.run([keygen, "-y", "-P", "", "-f", key], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.startswith("ssh-"):
        pub = r.stdout.strip()
        try:
            with open(key + ".pub") as f:
                if f.read().split()[:2] != pub.split()[:2]:
                    print("Note: %s.pub does not match your private key. I use the key derived from the private key." % key)
        except OSError:
            pass
        return pub
    try:                                         # the private key has a passphrase: its .pub file is the public half
        with open(key + ".pub") as f:
            pub = f.read().strip()
    except OSError:
        return None
    if not pub.startswith("ssh-"):
        return None
    print("Note: your SSH key has a passphrase, so I use %s.pub as it is." % key)
    return pub


def forget_old_host(hostname, known=None):
    """A Pi set up again has a new identity. Remove the old one from known_hosts so ssh does not refuse to connect.
    Returns the names that were removed. ssh-keygen keeps the file as it was beside it, as known_hosts.old."""
    keygen = shutil.which("ssh-keygen")
    known = known or os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
    removed = []
    if keygen and os.path.exists(known):
        for name in (hostname + ".local", hostname):
            found = subprocess.run([keygen, "-F", name, "-f", known], capture_output=True, text=True)
            if found.returncode == 0 and found.stdout.strip():
                subprocess.run([keygen, "-R", name, "-f", known], capture_output=True, text=True)
                removed.append(name)
    return removed

# ---------------------------------------------------------------- defaults read from this computer

def default_timezone():
    try:
        real = os.path.realpath("/etc/localtime")
        if "zoneinfo/" in real:
            return real.split("zoneinfo/", 1)[1]
    except OSError:
        pass
    return "America/New_York"


def default_country():
    try:
        code = (locale.getlocale()[0] or "").split("_")[-1]
        if re.fullmatch(r"[A-Z]{2}", code):
            return code
    except Exception:
        pass
    return "US"

# ---------------------------------------------------------------- the files on the card

def jdump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"       # JSON is valid YAML, which cloud-init reads


def build_files(cfg, instance_id):
    """The three first-start files, as text."""
    user = {"name": cfg["user"], "groups": GROUPS, "shell": "/bin/bash", "sudo": "ALL=(ALL) NOPASSWD:ALL",
            "lock_passwd": not cfg["pwhash"]}
    if cfg["pwhash"]:
        user["passwd"] = cfg["pwhash"]
    if cfg["pubkey"]:
        user["ssh_authorized_keys"] = [cfg["pubkey"]]
    user_data = {
        "hostname": cfg["hostname"], "manage_etc_hosts": True, "timezone": cfg["timezone"],
        "users": [user],
        "ssh_pwauth": bool(cfg["pwhash"]) and not cfg["pubkey"],     # with a key on the Pi, SSH takes the key only
        "enable_ssh": True,
        "bootcmd": [["sh", "-c", "raspi-config nonint do_wifi_country %s || true; rfkill unblock wifi || true" % cfg["country"]]],
        "runcmd": [["sh", "-c", "rfkill unblock wifi || true; nmcli radio wifi on || true"],
                   ["systemctl", "enable", "--now", "ssh"]],
    }
    network = {"network": {"version": 2, "wifis": {"renderer": "NetworkManager", "wlan0": {
        "dhcp4": True, "optional": True, "regulatory-domain": cfg["country"],
        "access-points": {cfg["ssid"]: {"password": cfg["wifi_key"]}}}}}}
    meta = {"dsmode": "local", "instance-id": instance_id, "instance_id": instance_id}
    return {"user-data": "#cloud-config\n" + jdump(user_data), "network-config": jdump(network), "meta-data": jdump(meta)}


def write_card(boot, cfg):
    instance_id = "ws79-%d" % int(time.time())    # a new id makes the Pi apply the files even if it already started once
    for name, text in build_files(cfg, instance_id).items():
        with open(os.path.join(boot, name), "w", newline="\n", encoding="utf-8") as f:
            f.write(text)
    cmd_path = os.path.join(boot, "cmdline.txt")
    with open(cmd_path, encoding="utf-8") as f:
        cmd = f.read().strip()
    cmd = re.sub(r"\s*cfg80211\.ieee80211_regdom=\S+", "", cmd) + " cfg80211.ieee80211_regdom=%s" % cfg["country"]
    with open(cmd_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(cmd + "\n")
    open(os.path.join(boot, "ssh"), "w").close()
    return instance_id


def check_card(boot, cfg, instance_id):
    """Read the card back and compare it with what was asked. Prints one line per check."""
    ok = True

    def chk(cond, msg):
        nonlocal ok
        print(("  OK    " if cond else "  FAIL  ") + msg)
        ok = ok and bool(cond)
    with open(os.path.join(boot, "user-data"), encoding="utf-8") as f:
        ud_raw = f.read()
    ud = json.loads(ud_raw.split("\n", 1)[1])
    with open(os.path.join(boot, "network-config"), encoding="utf-8") as f:
        nc = json.load(f)
    with open(os.path.join(boot, "meta-data"), encoding="utf-8") as f:
        md = json.load(f)
    with open(os.path.join(boot, "cmdline.txt"), encoding="utf-8") as f:
        cmd = f.read()
    u = ud["users"][0]
    aps = nc["network"]["wifis"]["wlan0"]["access-points"]
    chk(ud_raw.startswith("#cloud-config"), "first-start file header")
    chk(ud["hostname"] == cfg["hostname"], "Pi name '%s'" % cfg["hostname"])
    chk(u["name"] == cfg["user"], "user '%s'" % cfg["user"])
    if cfg["pwhash"]:
        chk(u.get("passwd") == cfg["pwhash"] and not u.get("lock_passwd"), "password stored as a hash")
    else:
        chk(u.get("lock_passwd") is True and "passwd" not in u, "no password: SSH key only")
    if cfg["pubkey"]:
        chk(u.get("ssh_authorized_keys") == [cfg["pubkey"]], "SSH public key")
    chk(list(aps) == [cfg["ssid"]] and aps[cfg["ssid"]]["password"] == cfg["wifi_key"], "Wi-Fi '%s' and its key" % cfg["ssid"])
    chk(md["instance-id"] == instance_id, "new setup id, so the Pi applies these files at its next start")
    chk(cmd.count("\n") == 1 and "root=" in cmd and cmd.count("ieee80211_regdom=") == 1, "start line intact, Wi-Fi country set")
    chk(os.path.exists(os.path.join(boot, "ssh")), "SSH switched on")
    return ok


def eject(boot):
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["diskutil", "eject", boot], check=True, capture_output=True)
            return True
        if system == "Linux":
            subprocess.run(["sync"])
            subprocess.run(["umount", boot], check=True, capture_output=True)
            return True
    except Exception:
        pass
    return False

# ---------------------------------------------------------------- the conversation

def main():
    ap = argparse.ArgumentParser(description="Set up a Raspberry Pi OS card for the WS-79 radio.")
    ap.add_argument("--card", help="path of the card's boot partition, when it is not found by itself")
    ap.add_argument("--no-wifi-list", action="store_true",
                    help="type the Wi-Fi name yourself: the networks this computer knows are not shown on screen")
    args = ap.parse_args()

    print("WS-79 · Raspberry Pi card setup\n")
    boot = pick_boot(args.card)
    print()
    cfg = {}
    while True:
        cfg["hostname"] = ask_valid("Name of the Pi on your network", cfg.get("hostname", "ws79"), valid_hostname,
                                    "Letters, digits and hyphens only.")
        cfg["user"] = ask_valid("User name on the Pi", cfg.get("user", "pi"), valid_username,
                                "Lowercase letters, digits, hyphens and underscores, starting with a letter.")
        cfg["ssid"] = ask_wifi_name(listing=not args.no_wifi_list)
        cfg["country"] = ask_valid("Country of the Wi-Fi, two letters", cfg.get("country", default_country()),
                                   lambda c: bool(re.fullmatch(r"[A-Za-z]{2}", c)), "Two letters, like CA, US or FR.").upper()
        cfg["timezone"] = ask("Time zone", cfg.get("timezone", default_timezone()))
        print("\n  Pi name     %s  (you will reach it as %s.local)" % (cfg["hostname"], cfg["hostname"]))
        print("  User        %s" % cfg["user"])
        print("  Wi-Fi       %s  (%s)" % (cfg["ssid"], cfg["country"]))
        print("  Time zone   %s" % cfg["timezone"])
        if ask("Is this right (y/n)", "y").lower().startswith("y"):
            break
        print()
    wifi_password = ask_secret("Password of the Wi-Fi '%s'" % cfg["ssid"], min_len=8)
    cfg["wifi_key"] = wifi_key(cfg["ssid"], wifi_password)
    cfg["pubkey"] = ssh_public_key()
    if cfg["pubkey"]:
        print("SSH key ready: its public half goes on the card, and the Pi will refuse passwords over SSH.")
        password = ask_secret("Password for '%s' on the Pi, for a keyboard and screen (Enter for none)" % cfg["user"],
                              min_len=8, optional=True)
    else:
        print("No SSH key: the Pi will accept this password over SSH from your network. Choose a long one.")
        password = ask_secret("Password for '%s' on the Pi" % cfg["user"], min_len=8)
    cfg["pwhash"] = sha512_crypt(password) if password else None
    del wifi_password, password

    print("\nWriting the card...")
    instance_id = write_card(boot, cfg)
    print("Reading it back:")
    if not check_card(boot, cfg, instance_id):
        print("\nCHECK FAILED. Do not use the card yet. Run this again.")
        sys.exit(2)
    print("\nCHECK PASSED")
    removed = forget_old_host(cfg["hostname"])
    if removed:
        print("This card gives the Pi a new identity, so I removed the earlier one (%s) from your known_hosts file.\n"
              "ssh-keygen kept the file as it was beside it, as known_hosts.old." % ", ".join(removed))
    ejected = eject(boot)
    print("The card is %s. Put it in the Pi and plug in the power." % ("ejected" if ejected else "ready: eject it from this computer"))
    print("The first start sets the Pi up and restarts it once. When it is on the network, connect with:\n")
    print("    ssh %s@%s.local" % (cfg["user"], cfg["hostname"]))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
