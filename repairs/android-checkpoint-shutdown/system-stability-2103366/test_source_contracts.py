"""Exact 2103365 protection plus inherited shutdown gates for this candidate."""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = 'faf41ee1d35fe55140bb1e193089643cc9ac06ee'
android = runpy.run_path(str(ROOT / 'android-close-2103365/test_source_contracts.py'))
native = runpy.run_path(str(ROOT / 'lifecycle-2103364/test_source_contracts.py'))

class Contracts(android['AndroidCloseHandoffTests'], native['SourceContracts']):
    def test_resume_and_identity_preserved(self):
        package = Path('tools/checkpoint-apk/package.py').read_text()
        self.assertIn('VERSION = 2103366', package)
        self.assertIn('1.0.9-System-Stability-RC1', package)

    def test_inherited_resume_speed_contracts(self):
        self.test_resume_and_identity_preserved()
        protocol = (android['SRC'] / 'InfinityCheckpointProtocol.java.in').read_text()
        self.assertIn('REQUIRED_OWNER_NAMES', protocol)

    def test_protected_shutdown_authority_and_unrelated_branches(self):
        protected = (
            'runtime/android/overlay/tools/android/packaging/xbmc/src/Main.java.in',
            'runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in',
            'runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityCheckpointProtocol.java.in',
            'runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityKodiShutdown.java.in',
            'runtime/native/overlay/xbmc/pvr/PVRManager.cpp',
            'runtime/native/overlay/xbmc/pvr/addons/PVRClients.cpp',
            'runtime/commandcenter/overlay/persistence_participant.py',
            'runtime/commandcenter/overlay/checkpoint_runtime.py',
            'installed/overlay/script.infinity.commandcenter/checkpoint_runtime.py',
            'installed/overlay/script.infinity.commandcenter/persistence_participant.py',
            'runtime/embedded-addons/manifest.json',
        )
        # Git contents are authoritative: no recapture of baseline preimages.
        for relative in protected:
            path = ROOT / relative
            if not path.exists():
                self.fail('Protected source missing: ' + relative)
            previous = subprocess.check_output(['git', 'show', BASE + ':' + path.relative_to(Path.cwd()).as_posix()])
            self.assertEqual(path.read_bytes(), previous, relative)
        for group in ('android', 'native', 'commandcenter'):
            path = ROOT / 'runtime' / group / 'manifest.json'
            prior = json.loads(subprocess.check_output(['git', 'show', BASE + ':' + path.relative_to(Path.cwd()).as_posix()]))
            current = json.loads(path.read_bytes())
            self.assertEqual(current['before'], prior['before'])
            self.assertEqual(current['deleted'], [])
            for name in current['changed']:
                self.assertEqual(hashlib.sha256((path.parent / 'overlay' / name).read_bytes()).hexdigest(), current['after'][name])

    def test_no_health_or_skin_replacement_in_apk_assets(self):
        import sys
        sys.path.insert(0, str(ROOT))
        import participant_asset
        manifest = json.loads((ROOT / 'system-stability-2103366/health/manifest.json').read_text())
        self.assertFalse(manifest['installed_identity_verified'])
        self.assertTrue(participant_asset.build())
        identity = json.loads((ROOT / 'system-stability-2103366/GREEN-2103365.json').read_text())
        self.assertIsNone(identity['installed_skin_version'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
