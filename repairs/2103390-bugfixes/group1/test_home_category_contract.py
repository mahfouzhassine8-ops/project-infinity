"""Signed-base Home category route audit; no device or production mutation."""
from pathlib import Path
import hashlib
import io
import unittest
from zipfile import ZipFile
from home_category_contract import audited_homes, from_signed_apk, sha256, BASE_SHA256

APK = Path('/mnt/data/integrated-2103390/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk')

@unittest.skipUnless(APK.is_file(),'Signed original APK not mounted')
class HomeCategoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = APK.read_bytes()
        cls.report = audited_homes(cls.original)

    def test_exact_signed_base_and_fourteen_variants(self):
        self.assertEqual(sha256(self.original), BASE_SHA256)
        self.assertEqual(self.report['homes'],14)

    def test_all_four_panels_have_expected_owner_and_category(self):
        for entry in self.report['all_home_variants']:
            self.assertEqual(len(entry['controls']),4)
            self.assertEqual(entry['controls']['8101']['source_owner'],'plugin.video.umbrella')
            self.assertEqual(entry['controls']['8831']['section'],'tvshows')
            self.assertTrue(entry['selected_section_is_visibility_gate'])

    def test_all_existing_category_clicks_leave_home_for_videos(self):
        self.assertTrue(all(e['activate_category_leaves_home_for_videos'] for e in self.report['all_home_variants']))
        self.assertEqual(self.report['owner_split']['top_movies_tv'],'plugin.video.umbrella')

    def test_reject_unknown_base_before_reading_home(self):
        with self.assertRaises(ValueError):audited_homes(self.original+b'\n')

    def test_report_matches_original_and_contains_no_titles_or_urls(self):
        self.assertEqual(from_signed_apk(APK), self.report)
        self.assertTrue(all('plugin://' not in str(x) for x in self.report['all_home_variants']))

if __name__ == '__main__':unittest.main()
