from pathlib import Path
import importlib.util
import json
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'addons/script.infinity.support'))


class ExportEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.skin = self.root / 'skin'
        self.skin.mkdir()
        (self.skin / 'addon.xml').write_text('<addon id="skin.xenon2"/>')
        (self.skin / 'Home.xml').write_text('<window/>')
        self.dest = self.root / 'exported'
        self.dest.mkdir()
        self.messages = []
        self.allow = True
        self.copy_ok = True
        outer = self
        class Dialog:
            def yesno(self, *args): return outer.allow
            def browseSingle(self, *args): return str(outer.dest)
            def ok(self, *args): outer.messages.append(args)
        class Addon:
            def __init__(self, addon_id=None):
                self.id = addon_id
                if addon_id == 'script.kodihealthcenter': raise RuntimeError('Not installed')
            def getAddonInfo(self, key):
                return str(outer.skin if self.id else outer.root / 'profile')
        def rpc(request):
            request = json.loads(request)
            self.assertEqual(request['method'], 'Settings.GetSettingValue')
            self.assertTrue(request['params']['setting'].startswith('lookandfeel.'))
            return json.dumps({'result': {'value': 'fixture'}})
        def translate(path):
            return str(self.root / path.replace('special://', '')) if path.startswith('special://') else path
        def copy(source, destination):
            if not self.copy_ok: return False
            shutil.copyfile(source, destination)
            return True
        modules = {
            'xbmc': SimpleNamespace(getSkinDir=lambda: 'skin.xenon2', executeJSONRPC=rpc, LOGERROR=4,
                                    log=lambda *args: None),
            'xbmcaddon': SimpleNamespace(Addon=Addon),
            'xbmcgui': SimpleNamespace(Dialog=Dialog),
            'xbmcvfs': SimpleNamespace(translatePath=translate, copy=copy, exists=lambda p: Path(p).exists(),
                        Stat=lambda p: SimpleNamespace(st_size=lambda: Path(p).stat().st_size))
        }
        self.patcher = patch.dict(sys.modules, modules)
        self.patcher.start()
        spec = importlib.util.spec_from_file_location('support_entry_fixture', ROOT / 'addons/script.infinity.support/default.py')
        self.entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.entry)

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_kodi_entry_exports_real_zip_using_actual_skin_id(self):
        self.entry.main()
        output = list(self.dest.glob('*.zip'))
        self.assertEqual(len(output), 1)
        with zipfile.ZipFile(output[0]) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(json.loads(archive.read('report.json'))['active_skin_id'], 'skin.xenon2')
        self.assertFalse(list((self.root / 'profile/reports').glob('*.zip')))
        self.assertIn('Saved skin.xenon2 report', self.messages[-1][1])

    def test_cancel_does_not_create_report(self):
        self.allow = False
        self.entry.main()
        self.assertFalse(list(self.root.rglob('*.zip')))

    def test_unwritable_destination_keeps_local_report(self):
        self.copy_ok = False
        self.entry.main()
        self.assertFalse(list(self.dest.glob('*.zip')))
        self.assertEqual(len(list((self.root / 'profile/reports').glob('*.zip'))), 1)
        self.assertIn('Local copy:', self.messages[-1][1])

    def test_missing_skin_is_reported_without_modification(self):
        (self.skin / 'addon.xml').unlink()
        self.entry.main()
        self.assertIn('Export did not finish', self.messages[-1][1])
        self.assertEqual((self.skin / 'Home.xml').read_text(), '<window/>')


if __name__ == '__main__':
    unittest.main()
