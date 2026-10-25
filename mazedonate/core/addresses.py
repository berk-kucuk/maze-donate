"""The official donation addresses, and only ever the signed ones.

The addresses are not written in this code. They come from
`maze-donate.txt.asc` — the same clearsigned file the website publishes —
verified with `gpgv` against the Maze Linux package key that the
mazelinux-keyring package installs. What the window shows is the text gpgv
hands back *after* the signature checked out, so a file edited on disk, on the
mirror or on the website cannot put a different address on screen: it would
no longer verify, and then nothing is shown.

Two copies can exist:

  * the one shipped in the package (/opt/maze-donate/data/), and
  * a newer one the user fetched with "Check for new addresses", saved to
    ~/.local/share/maze-donate/.

The newest one that verifies wins. "Newest" is the signature's own timestamp,
which is inside the signature, so an old signed file cannot be replayed to
roll the addresses back to ones that were retired.

Qt-free on purpose, so the tests can run it without a display.
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLED = ROOT / "data" / "maze-donate.txt.asc"
USER_DIR = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "maze-donate"
USER_COPY = USER_DIR / "maze-donate.txt.asc"

KEYRING = Path("/usr/share/pacman/keyrings/mazelinux.gpg")
# Pinned: a signature from any other key in the keyring is not enough.
FINGERPRINT = "7C4D515A6B930CB04794CEF6147C8159B3E2EE5F"

REMOTE_URL = "https://mazelinux.berkkucukk.com.tr/maze-donate.txt.asc"
WEBSITE_URL = "https://mazelinux.berkkucukk.com.tr/#donate"
KEY_URL = "https://mazelinux.berkkucukk.com.tr/mazelinux.gpg"
MAX_BYTES = 64 * 1024

# GitHub Sponsors is a card payment page, not an address anyone could swap for
# their own, and the signed file predates it. If a later signed file lists it
# ("GitHub Sponsors:" followed by the link), the signed link is used instead.
SPONSORS_URL = "https://github.com/sponsors/berk-kucuk"

# Strict shapes, checked after the signature: a signed file with a typo in it
# should fail loudly rather than show something no wallet accepts.
_BTC = re.compile(r"^bc1[02-9ac-hj-np-z]{11,71}$")
_XMR = re.compile(r"^[48][1-9A-HJ-NP-Za-km-z]{94}$")
_SPONSORS = re.compile(r"^https://github\.com/sponsors/[A-Za-z0-9-]{1,39}$")

_HEADINGS = {
    "Bitcoin (BTC):": "btc",
    "Monero (XMR):": "xmr",
    "GitHub Sponsors:": "sponsors",
}


class VerifyError(Exception):
    """The file did not verify; `reason` is a short key for the UI."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass
class Signed:
    btc: str
    xmr: str
    sponsors: str | None
    date: str              # the "Date:" line of the signed text
    sig_time: int          # signature timestamp (seconds since the epoch)
    fingerprint: str
    text: str              # the full clearsigned file, as published
    source: str = "bundled"
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def sponsors_url(self) -> str:
        return self.sponsors or SPONSORS_URL


def pretty_fingerprint(fpr: str = FINGERPRINT) -> str:
    return " ".join(fpr[i:i + 4] for i in range(0, len(fpr), 4))


def _gpgv(asc: bytes) -> tuple[str, list[list[str]]]:
    """Run gpgv; return the verified plaintext and the [GNUPG:] status lines."""
    if not KEYRING.is_file():
        raise VerifyError("no_keyring", str(KEYRING))
    try:
        proc = subprocess.run(
            ["gpgv", "--status-fd", "2", "--keyring", str(KEYRING), "--output", "-", "-"],
            input=asc, capture_output=True, timeout=20, check=False,
            # gpgv only needs the keyring it is given; keep it away from the
            # user's own ~/.gnupg.
            env={"PATH": "/usr/bin:/bin", "GNUPGHOME": "/nonexistent", "LC_ALL": "C"},
        )
    except FileNotFoundError as e:
        raise VerifyError("no_gpgv", str(e)) from e
    except subprocess.TimeoutExpired as e:
        raise VerifyError("bad_signature", "gpgv timed out") from e
    status = [line[9:].split() for line in proc.stderr.decode("utf-8", "replace").splitlines()
              if line.startswith("[GNUPG:] ")]
    if proc.returncode != 0:
        raise VerifyError("bad_signature", f"gpgv exit {proc.returncode}")
    return proc.stdout.decode("utf-8", "strict"), status


def verify(asc: bytes, source: str = "bundled") -> Signed:
    if len(asc) > MAX_BYTES:
        raise VerifyError("too_large")
    if not asc.lstrip().startswith(b"-----BEGIN PGP SIGNED MESSAGE-----"):
        raise VerifyError("not_signed")
    # Anything after the signature block is unsigned, yet the "signed text"
    # view would show it; a file that carries any is refused outright.
    end = asc.find(b"-----END PGP SIGNATURE-----")
    if end < 0 or asc[end + 27:].strip():
        raise VerifyError("not_signed", "text outside the signature")
    plain, status = _gpgv(asc)

    kinds = [s[0] for s in status if s]
    if any(k in ("BADSIG", "ERRSIG", "EXPKEYSIG", "REVKEYSIG", "EXPSIG") for k in kinds):
        raise VerifyError("bad_signature", ",".join(kinds))
    valid = [s for s in status if s and s[0] == "VALIDSIG"]
    # Exactly one signature, made by the pinned key (primary fingerprint is the
    # last field of VALIDSIG; the first is the signing (sub)key).
    if len(valid) != 1 or kinds.count("NEWSIG") > 1:
        raise VerifyError("bad_signature", "expected exactly one signature")
    v = valid[0]
    primary = v[-1].upper() if len(v) >= 11 else v[1].upper()
    if FINGERPRINT not in (primary, v[1].upper()):
        raise VerifyError("wrong_key", primary)
    try:
        sig_time = int(v[3])
    except (IndexError, ValueError) as e:
        raise VerifyError("bad_signature", "no timestamp") from e

    return _parse(plain, asc.decode("utf-8", "replace"), sig_time, primary, source)


def _parse(plain: str, text: str, sig_time: int, fpr: str, source: str) -> Signed:
    found: dict[str, str] = {}
    date = ""
    lines = [ln.strip() for ln in plain.splitlines()]
    for i, ln in enumerate(lines):
        if ln.startswith("Tarih / Date:"):
            date = ln.split(":", 1)[1].strip()
        key = _HEADINGS.get(ln)
        if key:
            nxt = next((x for x in lines[i + 1:] if x), "")
            if key in found and found[key] != nxt:
                raise VerifyError("malformed", f"two different {key} entries")
            found[key] = nxt

    btc, xmr = found.get("btc", ""), found.get("xmr", "")
    if not _BTC.match(btc):
        raise VerifyError("malformed", "bitcoin address")
    if not _XMR.match(xmr):
        raise VerifyError("malformed", "monero address")
    sponsors = found.get("sponsors")
    if sponsors is not None:
        if not sponsors.startswith("https://"):
            sponsors = "https://" + sponsors
        if not _SPONSORS.match(sponsors):
            raise VerifyError("malformed", "sponsors link")
    return Signed(btc=btc, xmr=xmr, sponsors=sponsors, date=date, sig_time=sig_time,
                  fingerprint=fpr, text=text, source=source)


def _read(path: Path, source: str) -> Signed | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return verify(data, source)


def load() -> Signed:
    """The newest copy that verifies. Raises VerifyError if none does."""
    best: Signed | None = None
    first_error: VerifyError | None = None
    for path, source in ((BUNDLED, "bundled"), (USER_COPY, "updated")):
        try:
            s = _read(path, source)
        except VerifyError as e:
            # A user copy that stopped verifying (edited, truncated) is simply
            # ignored; the bundled one still stands.
            first_error = first_error or e
            continue
        if s and (best is None or s.sig_time > best.sig_time):
            best = s
    if best is None:
        raise first_error or VerifyError("missing", str(BUNDLED))
    return best


def accept_update(asc: bytes, current: Signed | None) -> tuple[Signed, bool]:
    """Verify a freshly downloaded file; keep it if it is newer.

    Returns (the signed set to show now, whether it changed anything).
    An older signature than the one on screen is refused, not just skipped:
    that is what a rollback to retired addresses would look like.
    """
    new = verify(asc, "updated")
    if current is not None:
        if new.sig_time < current.sig_time:
            raise VerifyError("older")
        if new.sig_time == current.sig_time and new.text == current.text:
            return current, False
    USER_DIR.mkdir(parents=True, exist_ok=True)
    tmp = USER_COPY.with_suffix(".tmp")
    tmp.write_bytes(asc)
    os.replace(tmp, USER_COPY)
    return new, True
