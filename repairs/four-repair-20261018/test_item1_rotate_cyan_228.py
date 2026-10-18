"""Item #1 regression controls. Run with optional real --parent/--candidate files."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import zipfile
from xml.etree import ElementTree as ET

PATH = Path(__file__).with_name('item1_rotate_cyan_228.py')
spec=importlib.util.spec_from_file_location('item1_rotate_cyan_228',PATH)
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

ACTION1='StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED)'
ACTION2='StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_FOLLOW_DEVICE)'


def fixture(color=b'$VAR[InfinityPaletteFocus]',extra=b''):
    return (b'<window><controls><control type="group"><control type="button" id="263">'
      b'<onclick>'+ACTION1.encode()+b'</onclick><onclick>'+ACTION2.encode()+b'</onclick>'
      b'<onclick>Skin.ToggleSetting(Infinity.PlayerRotationUnlocked)</onclick>'
      b'</control><control type="image"><texture colordiffuse="FFFFFFFF">infinity_reference/rotate.png</texture>'
      b'<visible>!Skin.HasSetting(Infinity.PlayerRotationUnlocked)</visible></control>'
      b'<control type="image"><texture colordiffuse="'+color+b'">infinity_reference/rotate.png</texture>'
      b'<visible>Skin.HasSetting(Infinity.PlayerRotationUnlocked)</visible></control>'
      b'<control type="image"><texture colordiffuse="$VAR[InfinityPaletteFocus]">untouched.png</texture></control>'
      +extra+b'</control></controls></window>')


class Item1Controls(unittest.TestCase):
    def test_exact_rotate_image_only_and_independent_palette_preserved(self):
        prior=fixture()
        after=app.patch_layout(prior,'fixture/VideoOSD.xml')
        self.assertEqual(after,prior.replace(app.TEXTURE,app.CYAN,1))
        self.assertIn(b'<texture colordiffuse="$VAR[InfinityPaletteFocus]">untouched.png</texture>',after)
        app.osd_state(after,'fixture/VideoOSD.xml',True)

    def test_refuse_repeated_or_missing_rotate_state(self):
        with self.assertRaises(ValueError):app.patch_layout(fixture(color=b'FF00D9FF'),'fixture/VideoOSD.xml')
        with self.assertRaises(ValueError):app.patch_layout(fixture().replace(ACTION1.encode(),b'PlayerControl(Repeat)'),'fixture/VideoOSD.xml')
        with self.assertRaises(ValueError):app.patch_layout(fixture().replace(b'id="263"',b'id="265"'),'fixture/VideoOSD.xml')

    def test_refuse_redundant_display_mode_and_unexpected_extra_image(self):
        with self.assertRaises(ValueError):app.patch_layout(fixture(extra=b'<label>Display Mode</label>'),'fixture/VideoOSD.xml')
        with self.assertRaises(ValueError):app.patch_layout(fixture().replace(app.TEXTURE,app.TEXTURE+b'\n'+app.TEXTURE),'fixture/VideoOSD.xml')


def exact_archives(parent,candidate):
    import collections
    assert app.digest(parent.read_bytes())==app.PARENT_SHA256
    with zipfile.ZipFile(parent) as b,zipfile.ZipFile(candidate) as a:
        assert a.testzip() is None and b.namelist()==a.namelist()
        names=a.namelist()
        assert len(names)==3072
        changed={n for n in names if b.read(n)!=a.read(n)}
        approved={n for n in names if n.endswith('/VideoOSD.xml') and '/unified/' not in n}
        approved|={app.ADDON,app.MANIFEST}
        assert len(changed)==15 and changed==approved, sorted(changed^approved)
        assert b.read(app.PREFIX+'unified/VideoOSD.xml')==a.read(app.PREFIX+'unified/VideoOSD.xml')
        for n in changed:
            if n.endswith('/VideoOSD.xml'):
                assert a.read(n)==b.read(n).replace(app.TEXTURE,app.CYAN,1)
        for n in names:
            if n.endswith('/VideoOSD.xml'):app.osd_state(a.read(n),n,True)
            if 'cobra' in n.lower():assert a.read(n)==b.read(n)
        for name in ('unified/PlayerControls.xml','unified/Custom_1197_InfinityDisplayMode.xml',
                     'unified/Custom_1193_InfinityBrowse.xml','unified/Includes_InfinityHomeUnified.xml',
                     'unified/Includes_InfinityUIRepair.xml','unified/DialogContextMenu.xml'):
            assert a.read(app.PREFIX+name)==b.read(app.PREFIX+name)
        assert b'PlayerControl(Repeat)' in a.read(app.PREFIX+'unified/PlayerControls.xml')
    return {'item':1,'changed_approved_files':15,'cyan_osd_layouts':14,
            'byte_identical_other_files':3057,'unapproved_cobra_diffs':0,
            'build_sha256':app.digest(candidate.read_bytes()),'pass':True,
            'fold_accepted':False,'final_apk':False}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path);p.add_argument('--candidate',type=Path)
    args=p.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Item1Controls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    if args.parent and args.candidate:print(json.dumps(exact_archives(args.parent,args.candidate),indent=2))
