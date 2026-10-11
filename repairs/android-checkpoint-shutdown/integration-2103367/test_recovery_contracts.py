"""Verify recovered source and protected authority before a 2103367 build.

These gates admit only the two already-saved diagnostic hooks in protected
Android authority files. They do not establish device or release acceptance.
"""
from pathlib import Path
import hashlib
import json
import re
import runpy
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE = 'faf41ee1d35fe55140bb1e193089643cc9ac06ee'


def baseline(path):
    return subprocess.check_output(
        ['git', 'show', BASE + ':' + path.relative_to(REPO).as_posix()], cwd=REPO)


class RecoveryContracts(unittest.TestCase):
    def test_protected_authority_has_only_saved_diagnostic_hooks(self):
        android = 'runtime/android/overlay/tools/android/packaging/xbmc/src/'
        protected = {
            android + 'Main.java.in': None,
            android + 'InfinityCloseGuardService.java.in':
                b'    InfinityCheckpointEvidence.register(this);\n',
            android + 'InfinityCheckpointProtocol.java.in':
                b'    InfinityCheckpointEvidence.mirror(path,row);\n',
            android + 'InfinityKodiShutdown.java.in': None,
            'runtime/native/overlay/xbmc/pvr/PVRManager.cpp': None,
            'runtime/native/overlay/xbmc/pvr/addons/PVRClients.cpp': None,
            'runtime/commandcenter/overlay/persistence_participant.py': None,
            'installed/overlay/script.infinity.commandcenter/persistence_participant.py': None,
            'runtime/embedded-addons/manifest.json': None,
        }
        for relative, hook in protected.items():
            with self.subTest(path=relative):
                path = ROOT / relative
                current, original = path.read_bytes(), baseline(path)
                if hook is not None:
                    self.assertNotIn(hook, original)
                    self.assertEqual(current.count(hook), 1)
                    current = current.replace(hook, b'', 1)
                self.assertEqual(current, original)

    def test_source_manifests_keep_protected_preimages_and_exact_postimages(self):
        for group in ('native', 'android', 'commandcenter'):
            folder = ROOT / 'runtime' / group
            manifest_path = folder / 'manifest.json'
            current = json.loads(manifest_path.read_text())
            original = json.loads(baseline(manifest_path))
            with self.subTest(group=group):
                self.assertEqual(current['before'], original['before'])
                self.assertEqual(current['deleted'], [])
                for name in current['changed']:
                    self.assertEqual(hashlib.sha256((folder / 'overlay' / name).read_bytes()).hexdigest(),
                                     current['after'][name], name)

    def test_installed_payloads_and_bundled_payload_are_deterministic(self):
        sys.path.insert(0, str(ROOT))
        try:
            import participant_asset
            installed = runpy.run_path(str(ROOT / 'installed/build.py'))
            self.assertEqual(participant_asset.build(), participant_asset.build())
            for addon in installed['VERSIONS']:
                with self.subTest(addon=addon):
                    self.assertEqual(installed['build'](addon), installed['build'](addon))
        finally:
            sys.path.pop(0)

    def test_native_classifier_pins_both_exact_command_center_sources(self):
        source = (ROOT / 'runtime/native/overlay/xbmc/platform/android/activity/'
                  'InfinityScriptCheckpointContracts.cpp').read_text()
        pairs = re.findall(r'\{"script\.infinity\.commandcenter/([^"\n]+)", "([0-9a-f]{64})"\}', source)
        pins = {}
        for name, digest in pairs:
            pins.setdefault(name, set()).add(digest)
        bundled = json.loads((ROOT / 'runtime/commandcenter/manifest.json').read_text())['after']
        installed = json.loads((ROOT / 'installed/manifest.json').read_text())['script.infinity.commandcenter']['after']
        for name in ('addon.xml', 'checkpoint_runtime.py', 'common.py', 'default.py',
                     'experience.py', 'persistence_participant.py', 'plugin.py',
                     'resume_hub.py', 'service.py', 'skin_upgrade.py', 'view_mode.py'):
            with self.subTest(path=name):
                self.assertIn(bundled[name], pins.get(name, set()))
                self.assertIn(installed[name], pins.get(name, set()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
