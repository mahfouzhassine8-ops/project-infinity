"""Read-only signed APK proof that Option B direct touch hook is still unresolved."""
from pathlib import Path
import os
import tempfile,unittest
from input_longpress_audit import analyze

ORIGINAL=Path(os.environ.get('INFINITY_2103390_APK', '/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk'))

@unittest.skipUnless(ORIGINAL.is_file(),'Signed original required')
class InputScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.evidence=analyze(ORIGINAL)
    def test_01_original_28_releases_panels(self):
        self.assertEqual(self.evidence['top_movie_tv_panels_verified'],28)
        self.assertEqual(self.evidence['original_members_unmodified'],7430)
    def test_02_built_in_global_hold_is_native_contextmenu(self):
        self.assertEqual(self.evidence['touch_global_longpress'],'RightClick')
        self.assertFalse(self.evidence['home_specific_touch_mapping_present'])
    def test_03_does_not_invent_unverified_popup_hook(self):
        self.assertFalse(self.evidence['direct_home_option_b_longpress_connected'])
        self.assertEqual(self.evidence['native_rail_hold_reuse'],'NOT_PROVEN_FOR_PANELS_8101_8102')
    def test_04_unknown_apk_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            bad=Path(d)/'invalid.apk';bad.write_bytes(b'NOT_APK')
            with self.assertRaises(ValueError):analyze(bad)

if __name__=='__main__':unittest.main(verbosity=2)
