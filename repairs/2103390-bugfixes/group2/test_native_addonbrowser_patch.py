"""Group #2 Kodi Add-on Browser native source-stage contract tests.

Runs on host without Android. Uses source-anchor fixtures for Python/staging
behavior; when INFINITY_NATIVE_SOURCE_ROOT is supplied tests real checked-out
native source. It does NOT prove a compiled APK or physical Fold input.
"""
from __future__ import annotations
import os
import unittest
import tempfile
from pathlib import Path
from hashlib import sha256
import native_addonbrowser_patch as p

SOURCE=Path(os.environ.get("INFINITY_NATIVE_SOURCE_ROOT","/no-native-source-checkout"))

def fixture(path):
    return ("\n".join(old for old,_ in p.PATCHES[path])+"\n").encode("utf-8")

class Group2NativePatch(unittest.TestCase):
    def test_01_only_four_specific_native_paths(self):
        self.assertEqual(len(p.FILES),4)
        self.assertEqual(len(set(p.FILES)),4)
        self.assertTrue(all(s.startswith("xbmc/addons/") for s in p.FILES))
        self.assertFalse(any("cobra" in s.lower() or "shutdown" in s.lower() for s in p.FILES))

    def test_02_all_source_preimages_are_unique_and_replaceable(self):
        for filename in p.FILES:
            with self.subTest(filename=filename):
                original=fixture(filename)
                patched=p.patch_member(filename,original).decode()
                for old,new in p.PATCHES[filename]:
                    self.assertIn(new,patched)
                    self.assertNotIn(old,patched)
                with self.assertRaises(ValueError):
                    p.patch_member(filename,patched.encode())

    def test_03_patch_can_be_perfectly_reversed_to_original(self):
        for filename in p.FILES:
            a=fixture(filename).decode()
            b=p.patch_member(filename,a.encode()).decode()
            for old,new in reversed(p.PATCHES[filename]):
                self.assertEqual(b.count(new),1)
                b=b.replace(new,old,1)
            self.assertEqual(b,a)

    def test_04_two_tap_behavior_is_restricted_to_native_browser(self):
        name=next(x for x in p.FILES if x.endswith("GUIWindowAddonBrowser.cpp"))
        s=p.patch_member(name,fixture(name)).decode()
        self.assertIn("iAction == ACTION_MOUSE_LEFT_CLICK",s)
        self.assertIn("InfinityAddonBrowserSkinActive()",s)
        self.assertIn("m_infinityArmedTouchItem != fingerprint",s)
        self.assertIn("std::to_string(iItem)",s)
        self.assertIn("iAction == ACTION_SHOW_INFO",s)

    def test_05_view_hide_has_reversible_path_and_no_addon_manager_writes(self):
        name=next(x for x in p.FILES if x.endswith("GUIWindowAddonBrowser.cpp"))
        s=p.patch_member(name,fixture(name)).decode()
        for marker in ('m_infinityHiddenFromBrowse.insert(id)','m_infinityHiddenFromBrowse.clear()',
                       'InfinityIsUserAddonSection(strDirectory)',
                       'addons://infinity-show-hidden/','items.Remove(i)'):
            self.assertIn(marker,s)
        self.assertNotIn("DisableAddon(",s)
        self.assertNotIn("UnInstall(",s)
        self.assertNotIn("DELETE FROM",s)

    def test_06_native_both_disable_entrances_confirm_only_in_browser(self):
        for suffix in ("GUIDialogAddonInfo.cpp","ContextMenus.cpp"):
            path=next(x for x in p.FILES if x.endswith(suffix))
            s=p.patch_member(path,fixture(path)).decode()
            self.assertIn('GetActiveWindow() == WINDOW_ADDON_BROWSER',s)
            self.assertIn('"skin.infinity.diggz"',s)
            self.assertIn('!CGUIDialogYesNo::ShowAndGetInput',s)
            self.assertTrue(s.index("!CGUIDialogYesNo::ShowAndGetInput")<
                            s.rindex("DisableAddon("))
            self.assertIn("This stops the add-on.",s)

    def test_07_real_root_routes_remain_true_even_when_updates_empty(self):
        path=next(x for x in p.FILES if x.endswith("GUIWindowAddonBrowser.cpp"))
        s=p.patch_member(path,fixture(path)).decode()
        for route in ("addons://outdated/","addons://recently_updated/",
                      "addons://install/"):
            self.assertIn(route,s)
        self.assertIn("ensureNativeRoute(",s)
        self.assertNotIn("plugin.video.",s)

    def test_08_unknown_member_and_unknown_native_source_fail_closed(self):
        with self.assertRaises(ValueError):p.patch_member("xbmc/guilib/GUIBaseContainer.cpp",b"x")
        for name in p.FILES:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):p.patch_member(name,fixture(name)+b"\\n"+fixture(name))

    def test_09_stage_never_mutates_sources_and_all_hashes_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"before";out=Path(tmp)/"after"
            hashes={}
            for name in p.FILES:
                f=root/name;f.parent.mkdir(parents=True,exist_ok=True)
                data=fixture(name);f.write_bytes(data);hashes[name]=p.sha256(data)
            with self.assertRaises(ValueError):p.stage(root,root,hashes)
            incomplete=dict(hashes);incomplete.pop(next(iter(hashes)))
            with self.assertRaises(ValueError):p.stage(root,out,incomplete)
            self.assertFalse(out.exists())
            result=p.stage(root,out,hashes)
            self.assertEqual(len(result["native_source_files_staged"]),4)
            self.assertFalse(result["applied_to_signed_apk"])
            self.assertFalse(result["Cobra_code_modified"])
            for name in p.FILES:
                self.assertEqual(p.sha256((root/name).read_bytes()),hashes[name])
                self.assertNotEqual((root/name).read_bytes(),(out/name).read_bytes())

    @unittest.skipUnless(SOURCE.is_dir(),"Real Kodi native source checkout not mounted")
    def test_10_actual_native_checkout_exact_anchor_guards(self):
        for name in p.FILES:
            self.assertNotEqual((SOURCE/name).read_bytes(),
                                p.patch_member(name,(SOURCE/name).read_bytes()))

if __name__=="__main__": unittest.main(verbosity=2)
