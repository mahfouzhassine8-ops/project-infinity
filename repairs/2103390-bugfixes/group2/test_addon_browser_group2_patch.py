"""Signed 2103390, fail-closed Group #2 browser skin-only host tests."""
from __future__ import annotations
from io import BytesIO
import hashlib
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from addon_browser_group2_patch import (
    SIGNED_BASE_SHA256,SKIN_PREFIX,FILES,EXPECTED_LAYOUTS,
    HEADER_ARC,WRONG_HELP,CONTEXT_HELP,OLD_FOCUS,NEW_FOCUS,
    NEW_INCLUDE, patch_addon_browser,patch_includes,patch_file_browser,
    candidate_map,staged_inventory,sha,stage)

BASE=Path('/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk')

@unittest.skipUnless(BASE.is_file(),'Requires original 2103390 signed APK')
class Group2ExactBrowserScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=BASE.read_bytes()
        cls.original=ZipFile(BytesIO(cls.raw))
        cls.staged=candidate_map(BASE)
        cls.layouts=sorted(EXPECTED_LAYOUTS)

    @classmethod
    def tearDownClass(cls): cls.original.close()

    def asset(self,layout,kind,updated=False):
        path=f'{SKIN_PREFIX}{layout}/{kind}'
        return (self.staged[path] if updated else self.original.read(path))

    def test_01_original_signed_base_and_exact_42_allowlist(self):
        self.assertEqual(sha(self.raw),SIGNED_BASE_SHA256)
        self.assertEqual(len(self.original.namelist()),7430)
        self.assertEqual(len(self.staged),42)
        expected={f'{SKIN_PREFIX}{layout}/{filename}' for layout in EXPECTED_LAYOUTS for filename in FILES}
        self.assertEqual(set(self.staged),expected)
        self.assertEqual(len(self.original.namelist())-len(self.staged),7388)
        self.assertTrue(all(sha(self.original.read(path))!=sha(after) for path,after in self.staged.items()))
        for path in self.staged:
            self.assertNotIn('cobra',path.lower())
            self.assertFalse(path.startswith('lib/') or 'shutdown' in path or 'versioncheck' in path)
            self.assertFalse(path.startswith('assets/addons/plugin.'))

    def test_02_stray_arc_removed_only_from_addon_browser(self):
        for layout in self.layouts:
            with self.subTest(layout=layout):
                old=self.asset(layout,'AddonBrowser.xml')
                new=self.asset(layout,'AddonBrowser.xml',True)
                self.assertEqual(old.count(HEADER_ARC),1)
                self.assertNotIn(b'infinity_browser/header_arc.png',new)
                self.assertEqual([x.text for x in ET.fromstring(new).findall('.//texture') if x.text and ('infinity_logo.png' in x.text or 'infinity_mark.png' in x.text)], [x.text for x in ET.fromstring(old).findall('.//texture') if x.text and ('infinity_logo.png' in x.text or 'infinity_mark.png' in x.text)])
                self.assertEqual(new.count(b'<label>ADD-ON BROWSER</label>'),1)
                self.assertIn(b'<onclick>PreviousMenu</onclick>',new)
                # ZIP chooser header art is NOT part of blue-slash correction.
                self.assertEqual(self.asset(layout,'FileBrowser.xml').count(HEADER_ARC),1)

    def test_03_wrong_zip_help_replaced_and_existing_native_panel_kept(self):
        for layout in self.layouts:
            b=self.asset(layout,'AddonBrowser.xml',True)
            self.assertNotIn(WRONG_HELP,b)
            self.assertIn(CONTEXT_HELP,b)
            root=ET.fromstring(b)
            lst=root.find(".//control[@id='50']");self.assertIsNotNone(lst)
            self.assertEqual(lst.attrib.get('type'),'panel')
            self.assertEqual(root.find('views').text,'50')
            self.assertEqual(len(root.findall(".//control[@id='50']")),1)
            self.assertEqual(root.find(".//control[@id='9096']").findtext('onclick'),'PreviousMenu')

    def test_04_context_help_uses_six_actual_kodi_native_paths(self):
        for layout in self.layouts:
            before=self.asset(layout,'Includes_InfinityBrowser223.xml')
            after=self.asset(layout,'Includes_InfinityBrowser223.xml',True)
            self.assertTrue(after.endswith(NEW_INCLUDE+b'</includes>\n') or after.endswith(NEW_INCLUDE+b'</includes>'))
            self.assertEqual(after.replace(NEW_INCLUDE,b''),before)
            root=ET.fromstring(after)
            hints=root.find("./variable[@name='InfinityAddonBrowserHint']")
            footer=root.find("./variable[@name='InfinityAddonBrowserFooter']")
            self.assertIsNotNone(hints);self.assertIsNotNone(footer)
            for suffix in ('user','outdated','recently_updated','repos','search'):
                self.assertTrue(any('addons://'+suffix+'/' in (v.get('condition') or '') for v in hints.findall('value')))
            self.assertTrue(any('addons://' in (v.get('condition') or '') for v in hints.findall('value')))
            self.assertTrue(any('native ZIP file picker' in (v.text or '') for v in hints.findall('value')))
            self.assertTrue(any('different from hiding' in (v.text or '') for v in footer.findall('value')))

    def test_05_four_fake_footer_tabs_removed_and_no_new_click_handlers(self):
        for layout in self.layouts:
            old=self.asset(layout,'AddonBrowser.xml'); new=self.asset(layout,'AddonBrowser.xml',True)
            for label in (b'INSTALL ZIP',b'REPOSITORIES',b'UPDATES',b'DEPENDENCIES'):
                self.assertIn(b'<label>'+label+b'</label>',old)
                self.assertNotIn(b'<label>'+label+b'</label>',new)
            self.assertIn(b'<label>$VAR[InfinityAddonBrowserFooter]</label>',new)
            self.assertEqual(old.count(b'<onclick>'),new.count(b'<onclick>'))
            self.assertEqual(old.count(b'<control type="button"'),new.count(b'<control type="button"'))
            self.assertEqual(old.count(b'infinity_browser/footer.png'),new.count(b'infinity_browser/footer.png'))

    def test_06_addon_browser_focus_right_to_original_back(self):
        for layout in self.layouts:
            old=self.asset(layout,'AddonBrowser.xml');new=self.asset(layout,'AddonBrowser.xml',True)
            self.assertEqual(old.count(OLD_FOCUS),1)
            self.assertEqual(new.count(NEW_FOCUS),1)
            self.assertEqual(ET.fromstring(new).find(".//control[@id='50']").findtext('onright'),'9096')
            self.assertEqual(ET.fromstring(new).find(".//control[@id='9096']").findtext('onleft'),'50')

    def test_07_zip_picker_two_lists_focus_real_ok_directly(self):
        for layout in self.layouts:
            old=self.asset(layout,'FileBrowser.xml');new=self.asset(layout,'FileBrowser.xml',True)
            self.assertEqual(new.count(b'<onright>61</onright>'),0)
            self.assertEqual(new.count(b'<onright>413</onright>'),3)
            self.assertEqual(new.replace(b'<onright>413</onright>',b'<onright>61</onright>',2),old)
            root=ET.fromstring(new)
            for ident in ('450','451'):
                self.assertEqual(root.find(".//control[@id='"+ident+"']").findtext('onright'),'413')
            for ident in ('413','414','415','9410','61'):
                self.assertIsNotNone(root.find(".//control[@id='"+ident+"']"))
            self.assertEqual(ET.fromstring(old).find(".//control[@id='9410']").findtext('visible'),
                             root.find(".//control[@id='9410']").findtext('visible'))

    def test_08_existing_themes_all_variables_and_addon_routes_preserved(self):
        for layout in self.layouts:
            # existing include resource values were NOT changed
            old=self.asset(layout,'Includes_InfinityBrowser223.xml');new=self.asset(layout,'Includes_InfinityBrowser223.xml',True)
            o=ET.fromstring(old);n=ET.fromstring(new)
            def normalized(v):return [(x.get('condition'), x.text) for x in v.findall('value')]
            existing={v.get('name'):normalized(v) for v in o.findall('variable')}
            current={v.get('name'):normalized(v) for v in n.findall('variable')}
            self.assertEqual({k:current[k] for k in existing},existing)
            # native Add-on Browser control-onclick buttons were not changed, nor any installed addon state.
            o=ET.fromstring(self.asset(layout,'AddonBrowser.xml'))
            n=ET.fromstring(self.asset(layout,'AddonBrowser.xml',True))
            def actions(root): return [(c.get('id'),c.findtext('onclick')) for c in root.findall('.//control') if c.find('onclick') is not None]
            self.assertEqual(actions(o),actions(n))

    def test_09_original_signed_staging_never_rewrites_base(self):
        prior=sha(BASE.read_bytes())
        with tempfile.TemporaryDirectory(prefix='group2_test_') as root:
            self.assertRaises(ValueError,stage,BASE,BASE.parent)
            receipt=stage(BASE,Path(root)/'staged')
            self.assertEqual(receipt['proposed_changed_members'],42)
            self.assertEqual(receipt['unchanged_original_members'],7388)
            path=Path(root)/'staged'/SKIN_PREFIX/'unified'/'AddonBrowser.xml'
            self.assertTrue(path.is_file())
            self.assertEqual(sha(path.read_bytes()),sha(self.asset('unified','AddonBrowser.xml',True)))
        self.assertEqual(sha(BASE.read_bytes()),prior)

    def test_10_fail_closed_against_reapplication_or_modified_src(self):
        source=self.asset('unified','AddonBrowser.xml')
        with self.assertRaises(ValueError): patch_addon_browser(self.asset('unified','AddonBrowser.xml',True))
        with self.assertRaises(ValueError): patch_addon_browser(source.replace(HEADER_ARC,b''))
        with self.assertRaises(ValueError): patch_includes(self.asset('unified','Includes_InfinityBrowser223.xml',True))
        with self.assertRaises(ValueError): patch_file_browser(self.asset('unified','FileBrowser.xml',True))

if __name__=='__main__':unittest.main(verbosity=2)
