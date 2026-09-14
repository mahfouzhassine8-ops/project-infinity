"""Non-runnable APK fixtures; verify presentation isolation, not phone behavior."""
import json,os,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import infinity71 as e
import infinity_mobile_presentation as p

class MobilePresentation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.base=self.root/'NONRUNNABLE-FIXTURE.apk';self.manifest=self.root/'engine.json'
        self.out=self.root/'NONRUNNABLE-output.apk';self.receipt=self.root/'presentation.json'
        source=Path(os.environ['INFINITY_KODI_SOURCE'])
        with zipfile.ZipFile(self.base,'w') as z:
            z.writestr('AndroidManifest.xml',b'<manifest package="com.projectinfinity.kodi"/>')
            z.write(os.environ['INFINITY_TEST_DEX'],'classes.dex')
            z.writestr('lib/arm64-v8a/libkodi.so',b'NOT AN ENGINE: UNIT TEST FIXTURE')
            for f in (source/'addons/skin.estuary').rglob('*'):
                if f.is_file() and f.suffix=='.xml':z.write(f,'assets/'+f.relative_to(source).as_posix())
            z.writestr(p.RESUME,'msgctxt "#12021"\nmsgid "Play from beginning"\nmsgstr ""\n\nmsgctxt "#12022"\nmsgid "Resume from {0:s}"\nmsgstr ""\n')
        e.record_engine(self.base,self.manifest,'NONRUNNABLE-MOBILE-TEST')
    def tearDown(self):self.tmp.cleanup()
    def build(self):p.build(self.base,self.manifest,self.out,self.receipt)
    def test_native_and_dex_stay_identical(self):
        self.build();before=e.apk_hashes(self.base);after=e.apk_hashes(self.out)
        for n in ('classes.dex','lib/arm64-v8a/libkodi.so','AndroidManifest.xml'):self.assertEqual(before[n],after[n])
    def test_original_lock_and_icon_preserved(self):
        self.build()
        with zipfile.ZipFile(self.out) as z:
            for n,path in e.LOCK_FILES.items():self.assertEqual(z.read(path),(e.ASSETS/n).read_bytes())
            self.assertEqual(z.read(p.SKIN+'media/infinity/icon.png'),(e.ASSETS/'project_infinity_icon.png').read_bytes())
    def test_all_palettes_cover_the_entire_color_schema(self):
        self.build()
        with zipfile.ZipFile(self.out) as z:
            defaults=p.color_sets(z.read(p.SKIN+'colors/defaults.xml'))['dark']
            for mode in ('Light','Dark','OLED'):
                self.assertEqual(set(defaults),{c.get('name') for c in p.ET.fromstring(z.read(p.SKIN+'colors/Infinity '+mode+'.xml')).findall('color')})
    def test_system_manual_theme_menu_no_skin_reload(self):
        self.build()
        with zipfile.ZipFile(self.out) as z:
            dialog=z.read(p.SKIN+'xml/Custom_1198_InfinityAppearance.xml').decode()
            for mode in ('system','light','dark','oled'):self.assertIn('Infinity.ThemePolicy,'+mode,dialog)
            self.assertNotIn('ReloadSkin',dialog)
            variables=z.read(p.SKIN+'xml/Variables.xml').decode()
            self.assertIn('Window(Home).Property(Infinity.SystemTheme)',variables)
    def test_resume_only_curated_labels(self):
        self.build()
        with zipfile.ZipFile(self.out) as z:
            po=z.read(p.RESUME).decode();self.assertIn('Start Over',po);self.assertIn('Continue from {0:s}',po)
    def test_tampered_native_is_rejected(self):
        self.build();bad=self.root/'bad.apk'
        with zipfile.ZipFile(self.out) as src,zipfile.ZipFile(bad,'w') as dst:
            for item in src.infolist():dst.writestr(item,b'bad' if item.filename.endswith('libkodi.so') else src.read(item.filename))
        with self.assertRaises(ValueError):p.verify(bad,self.manifest,self.receipt)
    def test_receipt_cannot_allow_native_change(self):
        self.build();r=json.loads(self.receipt.read_text());r['changes']['classes.dex']='a'*64;self.receipt.write_text(json.dumps(r))
        with self.assertRaises(ValueError):p.verify(self.out,self.manifest,self.receipt)
    def test_existing_output_not_overwritten(self):
        self.build();before=self.out.read_bytes()
        with self.assertRaises(ValueError):self.build()
        self.assertEqual(before,self.out.read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
