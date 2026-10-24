"""Clock display source guard against signed skin242 Home.xml."""
import hashlib
import os
import unittest
from pathlib import Path
from zipfile import ZipFile
from clock_reflow_scope import PREIMAGE_SHA256, OLD, NEW, transform

ZIP = os.environ.get('INFINITY_SIGNED_SKIN242_ZIP', '')

def baseline():
    if not ZIP:
        raise RuntimeError('INFINITY_SIGNED_SKIN242_ZIP not supplied')
    with ZipFile(ZIP) as z:
        return z.read('skin.infinity.diggz/unified/Home.xml')

class ClockScopeTest(unittest.TestCase):
    def test_surgically_widens_clock_only(self):
        original = baseline()
        self.assertEqual(hashlib.sha256(original).hexdigest(), PREIMAGE_SHA256)
        patched = transform(original)
        self.assertEqual(patched.count(NEW), 1)
        self.assertEqual(patched.replace(NEW, OLD, 1), original)
        self.assertEqual((Path(__file__).parent / "overlay/skin.infinity.diggz/unified/Home.xml").read_bytes(), patched)

    def test_geometry_preserves_right_margin(self):
        patched = transform(baseline())
        self.assertEqual(64 + 34, 98)
        self.assertIn(b'<param name="statusleft" value="48%" />', patched)
        self.assertIn(b'<param name="statuswidth" value="50%" />', patched)

    def test_incorrect_baseline_is_rejected(self):
        with self.assertRaises(ValueError):
            transform(baseline() + b' ')

if __name__ == '__main__':
    unittest.main()
