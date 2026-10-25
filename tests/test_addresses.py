"""Verification tests. They run the real gpgv against the real keyring and the
signed file in data/, then check that every kind of tampering is refused."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mazedonate.core import addresses as a  # noqa: E402

GOOD = a.BUNDLED.read_bytes()
BTC = "bc1qz4kwr4mtrjsx47z0u8vu4lv3y3sa4ttq94xphp"
XMR = ("873xWTjJgAYaoZySnj8r1K1YRCeVpDxQxbjyLJ5e6P7UEV55LZDrW9zJ3bvghoAPaVJuoFbL"
       "7jCMufDxtGeJQMkRRdsZ6YH")


@unittest.skipUnless(a.KEYRING.is_file(), "mazelinux-keyring not installed")
class VerifyTests(unittest.TestCase):
    def test_bundled_file_verifies(self):
        s = a.verify(GOOD)
        self.assertEqual(s.btc, BTC)
        self.assertEqual(s.xmr, XMR)
        self.assertEqual(s.fingerprint, a.FINGERPRINT)
        self.assertEqual(s.date, "2026-10-19")
        self.assertIsNone(s.sponsors)
        self.assertEqual(s.sponsors_url, a.SPONSORS_URL)

    def test_changed_address_is_refused(self):
        bad = GOOD.replace(BTC.encode(), BTC[:-1].encode() + b"q")
        with self.assertRaises(a.VerifyError) as cm:
            a.verify(bad)
        self.assertEqual(cm.exception.reason, "bad_signature")

    def test_text_before_or_after_signature_is_refused(self):
        for bad in (b"Bitcoin (BTC):\nbc1qattacker\n" + GOOD,
                    GOOD + b"\nMonero (XMR):\n4AAAA\n"):
            with self.assertRaises(a.VerifyError) as cm:
                a.verify(bad)
            self.assertEqual(cm.exception.reason, "not_signed")

    def test_unsigned_text_is_refused(self):
        with self.assertRaises(a.VerifyError):
            a.verify(b"Bitcoin (BTC):\n" + BTC.encode() + b"\n")

    def test_oversized_is_refused(self):
        with self.assertRaises(a.VerifyError) as cm:
            a.verify(GOOD + b" " * a.MAX_BYTES)
        self.assertEqual(cm.exception.reason, "too_large")

    def test_other_key_is_refused(self):
        with mock.patch.object(a, "FINGERPRINT", "0" * 40):
            with self.assertRaises(a.VerifyError) as cm:
                a.verify(GOOD)
        self.assertEqual(cm.exception.reason, "wrong_key")

    def test_missing_keyring(self):
        with mock.patch.object(a, "KEYRING", Path("/nonexistent/keyring.gpg")):
            with self.assertRaises(a.VerifyError) as cm:
                a.verify(GOOD)
        self.assertEqual(cm.exception.reason, "no_keyring")


@unittest.skipUnless(a.KEYRING.is_file(), "mazelinux-keyring not installed")
class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.patches = [mock.patch.object(a, "USER_DIR", d),
                        mock.patch.object(a, "USER_COPY", d / "maze-donate.txt.asc")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_same_file_is_no_change(self):
        cur = a.verify(GOOD)
        new, changed = a.accept_update(GOOD, cur)
        self.assertFalse(changed)
        self.assertIs(new, cur)
        self.assertFalse(a.USER_COPY.exists())

    def test_older_signature_is_refused(self):
        cur = a.verify(GOOD)
        cur.sig_time += 1
        with self.assertRaises(a.VerifyError) as cm:
            a.accept_update(GOOD, cur)
        self.assertEqual(cm.exception.reason, "older")

    def test_newer_signature_is_saved_and_loaded(self):
        cur = a.verify(GOOD)
        cur.sig_time -= 1
        new, changed = a.accept_update(GOOD, cur)
        self.assertTrue(changed)
        self.assertEqual(a.USER_COPY.read_bytes(), GOOD)
        self.assertEqual(a.load().btc, BTC)

    def test_tampered_user_copy_falls_back_to_bundled(self):
        a.USER_COPY.write_bytes(GOOD.replace(XMR.encode(), XMR[:-1].encode() + b"Z"))
        s = a.load()
        self.assertEqual(s.source, "bundled")
        self.assertEqual(s.xmr, XMR)


class ParseTests(unittest.TestCase):
    def _plain(self, btc=BTC, xmr=XMR, extra=""):
        return (f"Tarih / Date: 2026-10-19\n\nBitcoin (BTC):\n{btc}\n\n"
                f"Monero (XMR):\n{xmr}\n{extra}")

    def test_sponsors_line_is_read(self):
        s = a._parse(self._plain(extra="\nGitHub Sponsors:\ngithub.com/sponsors/berk-kucuk\n"),
                     "", 1, a.FINGERPRINT, "bundled")
        self.assertEqual(s.sponsors_url, "https://github.com/sponsors/berk-kucuk")

    def test_bad_shapes_are_refused(self):
        for kw in ({"btc": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"}, {"xmr": XMR[:-1]},
                   {"btc": ""}, {"xmr": "8" + "0" * 94}):
            with self.assertRaises(a.VerifyError):
                a._parse(self._plain(**kw), "", 1, a.FINGERPRINT, "bundled")

    def test_conflicting_duplicates_are_refused(self):
        with self.assertRaises(a.VerifyError):
            a._parse(self._plain(extra="\nBitcoin (BTC):\nbc1qqqqqqqqqqqqqqqqqqqqq\n"),
                     "", 1, a.FINGERPRINT, "bundled")

    def test_grouping_round_trips(self):
        from mazedonate.gui.window import _grouped  # needs PyQt6, which maze-python has
        self.assertEqual(_grouped(XMR).replace(" ", ""), XMR)


if __name__ == "__main__":
    unittest.main()
