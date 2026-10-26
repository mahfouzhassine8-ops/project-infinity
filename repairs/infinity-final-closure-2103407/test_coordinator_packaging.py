"""Exact410-to411 package boundaries and independent build routing."""
import io
import os
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile
import package_coordinator as packaging


class CoordinatorPackagingTests(unittest.TestCase):
    def archive(self,values):
        stream=io.BytesIO()
        with ZipFile(stream,'w') as z:
            for k,v in values.items():z.writestr(k,v)
        return ZipFile(io.BytesIO(stream.getvalue()))

    def test_actual_manifest_is_monotonic_and_only_typed_code_changes(self):
        with ZipFile(os.environ['INFINITY_COORDINATOR_PARENT_APK']) as z:raw=z.read('AndroidManifest.xml')
        changed=packaging.manifest(raw)
        self.assertEqual(changed.replace(struct.pack('<I',2103411),struct.pack('<I',2103410),1),raw)
        for bad in (raw+struct.pack('<I',2103410),changed,b'unknown'):
            with self.assertRaises(ValueError):packaging.manifest(bad)

    def test_only_two_owned_members_can_change_and_missing_changes_refuse(self):
        original={'AndroidManifest.xml':b'410','classes.dex':b'old','native':b'protected','VersionCheck':b'protected','Cobra':b'protected'}
        changes={'AndroidManifest.xml':b'411','classes.dex':b'new'}
        before=self.archive(original);candidate=dict(original,**changes)
        self.assertEqual(packaging.compare(before,self.archive(candidate),changes)['preserved_from_signed410_members'],3)
        for values in (dict(candidate,native=b'changed'),dict(candidate,VersionCheck=b'changed'),dict(candidate,Cobra=b'changed'),dict(candidate,extra=b'new'),original,{'AndroidManifest.xml':b'411','classes.dex':b'new'}):
            with self.assertRaises(ValueError):packaging.compare(before,self.archive(values),changes)

    def test_wrong_parent_fails_before_output_or_signing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'Infinity-2103410-VersionCheck-Corrective-INTERNAL-VERIFICATION.apk').write_bytes(b'wrong')
            with self.assertRaises(ValueError):packaging.build(root,root/'dex',root/'sdk',root/'out')
            self.assertFalse((root/'out').exists())

    def test_workflow_keeps_signing_and_behavioral_verification_independent(self):
        root=Path(__file__).resolve().parents[2]
        workflow=(root/'.github/workflows/infinity-2103407-search-pressure-host-gate.yml').read_text()
        self.assertIn("selected=='internal-coordinator-apk'",workflow)
        self.assertIn('package_coordinator.py',workflow)
        self.assertIn('test_coordinator_dispatch test_coordinator_packaging',workflow)
        for forbidden in ('needs:','workflow_run:','continue-on-error:','android17_shutdown_probe.py','android17_stress.py'):
            self.assertNotIn(forbidden,workflow)
        source=Path(packaging.__file__).read_text()
        for forbidden in ('essential_android_probe','adb(','force-stop'):self.assertNotIn(forbidden,source)
        self.assertIn('Audit finishes before any permanent signing credential is read',source)


if __name__=='__main__':unittest.main(verbosity=2)
