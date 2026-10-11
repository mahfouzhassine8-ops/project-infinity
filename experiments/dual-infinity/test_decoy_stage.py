from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import stage_decoy as stage


class DecoyStagingTests(unittest.TestCase):
    def parent_manifest(self):
        root = Path(__file__).resolve().parents[2] / 'repairs/android-checkpoint-shutdown/runtime/android/overlay/tools/android/packaging/xbmc/AndroidManifest.xml.in'
        return root.read_text().replace('@APP_PACKAGE@', stage.NAMESPACE)

    def test_manifest_separates_install_scopes_but_keeps_native_class(self):
        result = stage.manifest(self.parent_manifest())
        stage.validate_manifest(result)
        root = ET.fromstring(result)
        root.set('package', stage.INSTALL_ID)
        stage.validate_manifest(ET.tostring(root, encoding='unicode'), compiled=True)
        components = root.find('application')
        primary = next(x for x in components if x.get(stage.ANDROID+'name') == stage.NAMESPACE+'.Main')
        self.assertEqual(primary.get(stage.ANDROID+'process'), ':kodi')

    def test_shared_uid_and_production_provider_are_rejected(self):
        root = ET.fromstring(stage.manifest(self.parent_manifest()))
        root.set(stage.ANDROID + 'sharedUserId', stage.NAMESPACE)
        with self.assertRaises(ValueError):
            stage.validate_manifest(ET.tostring(root, encoding='unicode'))
        root.attrib.pop(stage.ANDROID + 'sharedUserId')
        provider = root.find('application/provider')
        provider.set(stage.ANDROID + 'authorities', stage.NAMESPACE + '.file')
        with self.assertRaises(ValueError):
            stage.validate_manifest(ET.tostring(root, encoding='unicode'))

    def test_extra_exported_endpoint_is_rejected(self):
        root = ET.fromstring(stage.manifest(self.parent_manifest()))
        primary = next(x for x in root.find('application') if
                       x.get(stage.ANDROID+'name') == stage.NAMESPACE+'.Main')
        primary.set(stage.ANDROID+'exported', 'true')
        with self.assertRaises(ValueError):
            stage.validate_manifest(ET.tostring(root, encoding='unicode'))

    def test_unrelated_cobra_and_health_sources_are_not_transformed(self):
        for name in ('CobraPlayer.java.in', 'InfinityLiveActivity.java.in', 'InfinityHealthExport.java.in'):
            source = 'package @APP_PACKAGE@; // protected '+name
            self.assertEqual(stage.java_transform(name, source), source)


if __name__ == '__main__':
    unittest.main()
