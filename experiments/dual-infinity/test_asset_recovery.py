import hashlib
from pathlib import Path
import tempfile
import unittest

import recover_assets as assets


class AssetRecoveryTests(unittest.TestCase):
    def test_incomplete_or_wrong_payload_cannot_be_admitted(self):
        expected = {'media/icon.png': hashlib.sha256(b'exact').hexdigest()}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'recovered'
            for payload in ({}, {'media/icon.png': b'wrong variant'}):
                with self.assertRaises(ValueError):
                    assets.write_verified_payload(expected, payload, output)
                self.assertFalse(output.exists())

    def test_jpeg_mismatch_is_reported_without_mutating_generated_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / 'media/splash.jpg'
            path.parent.mkdir(); path.write_bytes(b'wrong JPEG')
            expected = {'media/splash.jpg': hashlib.sha256(b'exact JPEG').hexdigest()}
            payload, evidence, errors = assets.recover_batch(expected, root, None)
            self.assertEqual(payload, {})
            self.assertEqual(errors, ['media/splash.jpg'])
            self.assertEqual(path.read_bytes(), b'wrong JPEG')

    def test_tvos_copy_requires_exact_protected_identity(self):
        name = 'xbmc/platform/darwin/tvos/Assets.xcassets/LaunchImage.launchimage/applaunch_screen.png'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / 'media/applaunch_screen.png'
            path.parent.mkdir(); path.write_bytes(b'exact image')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            expected = {'media/applaunch_screen.png': digest, name: digest}
            payload, _, errors = assets.recover_batch(expected, root, None)
            self.assertEqual(errors, [])
            self.assertEqual(payload[name], payload['media/applaunch_screen.png'])
            with self.assertRaises(ValueError):
                assets.recover_batch({name: digest}, root, None)


if __name__ == '__main__':
    unittest.main()
