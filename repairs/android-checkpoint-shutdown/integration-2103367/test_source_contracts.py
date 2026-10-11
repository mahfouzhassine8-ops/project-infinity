"""Preserved Android close gates plus the exact 2103367 recovery contract."""
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
android = runpy.run_path(str(ROOT / 'android-close-2103365/test_source_contracts.py'))
native = runpy.run_path(str(ROOT / 'lifecycle-2103364/test_source_contracts.py'))
recovery = runpy.run_path(str(ROOT / 'integration-2103367/test_recovery_contracts.py'))


class Contracts(android['AndroidCloseHandoffTests'], native['SourceContracts'], recovery['RecoveryContracts']):
    def test_resume_and_identity_preserved(self):
        package = (ROOT.parents[1] / 'tools/checkpoint-apk/package.py').read_text()
        self.assertIn('VERSION = 2103367', package)
        self.assertIn('1.0.9-Recovery-Integration-RC1', package)
        native_header = (ROOT / 'runtime/native/overlay/xbmc/platform/android/activity/InfinityShutdownTrace.h').read_text()
        self.assertIn('infinity-checkpoint-recovery-integration-2103367-v1', native_header)

    def test_inherited_resume_speed_contracts(self):
        self.test_resume_and_identity_preserved()
        protocol = (android['SRC'] / 'InfinityCheckpointProtocol.java.in').read_text()
        for token in ('REQUIRED_OWNER_NAMES', 'peripherals', 'pvr'):
            self.assertIn(token, protocol)
        for name in ('service.py', 'resume_hub.py', 'plugin.py'):
            self.assertTrue((ROOT / 'runtime/commandcenter/overlay' / name).is_file())

    def test_context_ingress_preserves_addon_identity_and_existing_extensions(self):
        import xml.etree.ElementTree as ET
        for parent, current in [(ROOT / 'runtime/commandcenter/unchanged/addon.xml', ROOT / 'runtime/commandcenter/overlay/addon.xml'),
                                (ROOT / 'installed/parent/script.infinity.commandcenter/addon.xml', ROOT / 'installed/overlay/script.infinity.commandcenter/addon.xml')]:
            before, after = ET.parse(parent).getroot(), ET.parse(current).getroot()
            self.assertEqual(before.attrib, after.attrib)
            context = after.findall("extension[@point='kodi.context.item']")
            self.assertEqual(len(context), 1)
            self.assertEqual([e.get('library') for e in context[0].findall('./menu/item')], ['context.py', 'context.py'])
            after.remove(context[0]); self.assertEqual(ET.tostring(before), ET.tostring(after))


if __name__ == '__main__':
    unittest.main(verbosity=2)
