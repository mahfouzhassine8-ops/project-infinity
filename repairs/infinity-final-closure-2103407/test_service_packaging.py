"""Scoped packaging rejection and workflow boundaries; no application execution."""
import io
import os
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile
import package_versioncheck as packaging


class ServicePackagingTests(unittest.TestCase):
    def archive(self,values):
        stream=io.BytesIO()
        with ZipFile(stream,'w') as z:
            for k,v in values.items():z.writestr(k,v)
        return ZipFile(io.BytesIO(stream.getvalue()))

    def test_typed_real409_manifest_changes_only_monotonic_code(self):
        with ZipFile(os.environ['INFINITY_SERVICE_PARENT_APK']) as z:raw=z.read('AndroidManifest.xml')
        changed=packaging.manifest(raw);self.assertEqual(len(changed),len(raw))
        self.assertEqual(changed.replace(struct.pack('<I',2103410),struct.pack('<I',2103409),1),raw)
        for bad in (b'bad',raw.replace(struct.pack('<I',2103409),struct.pack('<I',2103408)),raw+struct.pack('<I',2103409)):
            with self.assertRaises(ValueError):packaging.manifest(bad)

    def test_every_other_member_must_remain_exact(self):
        original={'AndroidManifest.xml':b'oldmanifest','service.py':b'oldservice','classes.dex':b'exactDEX',
                  'lib/arm64-v8a/libkodi.so':b'exactnative','assets/cobra.dat':b'exactCobra'}
        changes={'AndroidManifest.xml':b'newmanifest','service.py':b'newservice'}
        before=self.archive(original);after=self.archive(dict(original,**changes))
        report=packaging.compare(before,after,changes)
        self.assertEqual(report['preserved_from_signed409_members'],3);self.assertEqual(report['unexpected_differences'],[])
        for name in ('classes.dex','lib/arm64-v8a/libkodi.so','assets/cobra.dat'):
            with self.assertRaises(ValueError):packaging.compare(before,self.archive(dict(original,**changes,**{name:b'changed'})),changes)

    def test_added_missing_unapproved_or_absent_expected_changes_are_rejected(self):
        original={'a':b'old','protected':b'exact'};changes={'a':b'new'};before=self.archive(original)
        for values in ({'a':b'new'},{'a':b'new','protected':b'exact','new':b'extra'},original,
                       {'a':b'wrong','protected':b'exact'}):
            with self.assertRaises(ValueError):packaging.compare(before,self.archive(values),changes)

    def test_wrong_parent_fails_before_signing_or_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'Infinity-2103409-Integrated-INTERNAL-VERIFICATION.apk').write_bytes(b'wrong')
            with self.assertRaises(ValueError):packaging.build(root,root/'sdk',root/'out')
            self.assertFalse((root/'out').exists())

    def test_build_has_no_application_or_shutdown_transport(self):
        source=Path(packaging.__file__).read_text()
        for forbidden in ('android17_shutdown_probe','essential_android_probe','adb(','CLOSE_KODI','force-stop'):
            self.assertNotIn(forbidden,source)
        self.assertIn('Audit finishes before any permanent signing credential is read',source)
        self.assertIn("'--v3-signing-enabled','true'",source)

    def test_existing_build_workflow_keeps_behavioral_verification_independent(self):
        root=Path(__file__).resolve().parents[2]
        workflow=(root/'.github/workflows/infinity-2103407-search-pressure-host-gate.yml').read_text()
        self.assertIn("selected=='internal-service-apk'",workflow)
        self.assertIn('package_versioncheck.py',workflow)
        self.assertIn('test_versioncheck_scope.py test_service_packaging.py',workflow)
        for forbidden in ('needs:','workflow_run:','continue-on-error:','android17_shutdown_probe.py','android17_stress.py'):
            self.assertNotIn(forbidden,workflow)
        self.assertIn("if: steps.selected.outputs.selection == 'internal-apk'",workflow)


if __name__=='__main__':unittest.main(verbosity=2)
