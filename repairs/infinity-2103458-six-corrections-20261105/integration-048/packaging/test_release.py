"""Controlled package/authentication contracts only; no application suites."""
from pathlib import Path
import ast
import copy
import os
import tempfile
import unittest
import subprocess
import yaml
from unittest.mock import patch
from zipfile import ZipFile
import release_controlled as r


class ControlledRelease(unittest.TestCase):
    def test_only_two_exact_versions_allowed(self):
        for v in (2103459,2103462):
            with self.assertRaisesRegex(ValueError,'ONLY_CONTROLLED_AND_RECOVERY_VERSIONS'):r.generate(Path('unused'),v,Path('unused'))

    def test_five_integrated_sources_match_checkpoint(self):
        self.assertEqual(len(r.plan()),5)
        self.assertEqual(sum(v['baseline458_sha256'] is None for v in r.plan().values()),0)
        for n,row in r.plan().items():
            p=r.ROOT/row['source'];self.assertEqual(p.read_bytes(),r.original(p));self.assertEqual(r.file_sha(p),row['candidate_source_sha256'])
        approved=r.load(r.ROOT/'repairs/infinity-native-touch-2103451-20261105/APPLIED-SOURCE-DELTA.json')
        self.assertEqual(len(approved['changed_files']),2)
        for n,row in approved['changed_files'].items():self.assertEqual(r.file_sha(r.ROOT/'repairs/infinity-native-touch-2103451-20261105/native'/n),row['after_sha256'])

    def test_signed458_metadata_generations_and_precise_allowlist(self):
        baseline=Path(os.environ.get('INFINITY_CONTROLLED_BASELINE','/tmp/immutable458/Infinity-2103458-Combined-Original-Signer.apk'))
        self.assertEqual(r.file_sha(baseline),r.APK_SHA)
        with tempfile.TemporaryDirectory(prefix='controlled-source-metadata-',dir='/tmp') as tmp,ZipFile(baseline) as z:
            for version,count,skin in ((2103460,78,258),(2103461,78,259)):
                root=Path(tmp)/str(version);root.mkdir();changes=r.generate(baseline,version,root,b'host-only-unexecuted-engine-placeholder')
                expected=(set(r.plan())|r.META|{r.NATIVE} if version==2103460 else r.META)-{r.CC+'INFINITY-MODULES.v1.sig'}
                self.assertEqual(set(changes),expected)
                text=changes[r.CC+'INFINITY-MODULES.v1'].decode()
                self.assertEqual(sum(line.startswith('file\t') for line in text.splitlines()),count)
                self.assertIn('package\t0.3.5.'+('61' if version==2103460 else '62')+'\n',text)
                prior=z.read(r.CC+'INFINITY-MODULES.v1').decode().splitlines()
                self.assertEqual([s for s in text.splitlines() if s.startswith(('entry\t','capability\t','protocol\t'))],[s for s in prior if s.startswith(('entry\t','capability\t','protocol\t'))])
                self.assertEqual(r.json.loads(changes[r.SKIN+'infinity-skin.json'])['candidate'],skin)
                if version==2103461:self.assertNotIn(r.NATIVE,changes)

    def test_single_original_signer_and_all_security_sources_unchanged(self):
        for name in ('assemble.py','release_authority.py','component_bundles.py','inventory.py','signer_policy.py','accepted-combined-release.json'):
            p=r.ISO/name;self.assertEqual(p.read_bytes(),r.original(p))
        for name in ('SignInfinityModules.java','ORIGINAL-INFINITY-PUBLIC-KEY.pem','InfinityInstalledModules.java.in','isolated-native/InfinityModuleManifest.cpp','isolated-native/InfinityModuleManifest.h'):
            p=r.FIRST/name;self.assertEqual(p.read_bytes(),r.original(p))

    def test_wrong_signer_and_ambiguous_certificate_fail_closed(self):
        for text in ('Signer #1 certificate SHA-256 digest: '+'0'*64,'Signer #1 certificate SHA-256 digest: '+r.CERT_SHA+'\nSigner #2 certificate SHA-256 digest: '+r.CERT_SHA):
            with patch.object(r.retained_ui,'cmd',return_value=text):
                with self.assertRaisesRegex(ValueError,'ORIGINAL_CERTIFICATE'):r.retained_ui.certificate(Path('unused'),Path('unused'))

    def test_versions_do_not_parse_commit_hash_as_version(self):
        sha='a'*20+'2109999'+'b'*13
        self.assertEqual(r.retained_ui.ref_versions(sha+' refs/heads/work/no-version'),[])
        self.assertEqual(r.retained_ui.ref_versions(sha+' refs/heads/work/version-2103458'),[2103458])

    def test_no_application_or_shutdown_execution_in_release_preparer(self):
        raw=Path(r.__file__).read_text();module=ast.parse(raw)
        fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
        body=ast.get_source_segment(raw,fn)
        self.assertLess(body.index('verify_native(native)'),body.index('INFINITY_KEYSTORE_B64'))
        self.assertLess(body.index('native_compatibility('),body.index('INFINITY_KEYSTORE_B64'))
        self.assertLess(body.index('check(load('),body.index('INFINITY_KEYSTORE_B64'))
        self.assertNotIn('adb',body);self.assertNotIn('test_shutdown',body)
        recovery=(r.HERE/'recovery_checks.py').read_text()
        self.assertIn("'userdata_sentinel_preserved'",recovery)
        self.assertIn("'invalid_original_signature_refused_without_writes'",recovery)
        self.assertIn("'library_helper_restores_exact_signed458_code'",recovery)
        self.assertIn("HERE/'recovery_checks.py'",body)
        self.assertNotIn('from recovery_checks import',body)

    def test_native_verification_and_engine_pins_remain_exact(self):
        pin=r.engine_record()
        self.assertEqual(pin['source_commit'],'3f3f47bdf9b0f14f9ac3b42fcff6f8710ceeda05')
        self.assertEqual(pin['changed_native_sources'],['xbmc/video/windows/GUIWindowVideoNav.cpp'])
        self.assertEqual(pin['signed458_source_map_sha256'],'3755bedfe8431d967b5f67cb020494b5714e9cea3f7d4c9f98a33280c763e739')
        record=r.load(r.HERE.parent/'APPLIED-APPROVED-PATCH.json')
        self.assertEqual(r.file_sha(r.ROOT/record['files'][pin['changed_native_sources'][0]]['applied_source']),
                         '06e225a5ca9ce552dbdd00c270a0f0423c779b755a5d758fd550955a30e83c1f')

    def test_original_signer_gate_steps_and_historical_jobs_remain(self):
        path=r.ROOT/'.github/workflows/infinity-combined-release.yml'
        old=yaml.safe_load(r.original(path));new=yaml.safe_load(path.read_text())
        self.assertEqual(old['concurrency'],new['concurrency'])
        self.assertEqual(old['permissions'],new['permissions'])
        for job in ('prepare-preview451','prepare-kodi452','prepare-kodi453','prepare-ui454-455'):
            self.assertEqual(old['jobs'][job],new['jobs'][job])
        before={s.get('name'):s for s in old['jobs']['combined']['steps']}
        after={s.get('name'):s for s in new['jobs']['combined']['steps']}
        for name in ('Hard original pre-sign payload ownership and source guard','Original signer after all source and payload gates'):
            self.assertEqual(before[name],after[name])
        for job,operation in [('prepare-six460-461','prepare-six460-461'),('review-six460-461','review-six460-461')]:
            self.assertIn(r.BRANCH,new['jobs'][job]['if']);self.assertIn(operation,new['jobs'][job]['if'])
        review=new['jobs']['review-six460-461'];self.assertNotIn('secrets.',str(review))
        keyed=[s for s in new['jobs']['prepare-six460-461']['steps'] if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
        self.assertEqual(len(keyed),1);self.assertIn('release_controlled.py prepare',keyed[0]['run'])
        self.assertNotIn('continue-on-error',path.read_text())

    def test_workflow_embedded_code_parses_without_execution(self):
        workflow=yaml.safe_load((r.ROOT/'.github/workflows/infinity-combined-release.yml').read_text())
        for job in workflow['jobs'].values():
            for step in job.get('steps',[]):
                text=step.get('run','')
                if "<<'PYCODE'" in text:ast.parse(text.split("<<'PYCODE'",1)[1].lstrip('\n').split('\nPYCODE',1)[0])
                result=subprocess.run(['bash','-n'],input=text,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_only_exact_authority_route_and_unsigned_workflow_records_change(self):
        p=r.ISO/'release_gate.py';old=r.original(p)
        expected=old.replace(b"AUTHORITY_BRANCH = 'work/infinity-browser-visual-correction-from-2103456-20261105'",("AUTHORITY_BRANCH = '"+r.BRANCH+"'").encode())
        self.assertEqual(p.read_bytes(),expected)
        p=r.ISO/'signer-policy.json';old=r.json.loads(r.original(p));new=r.load(p)
        added=[row for row in new['additional_unsigned_owner_workflows'] if row not in old['additional_unsigned_owner_workflows']]
        self.assertEqual(len(added),1)
        self.assertEqual(added[0]['id'],408828503)
        self.assertFalse(added[0]['original_key_access'])
        self.assertEqual(added[0]['path'],'.github/workflows/infinity-six-navigation-arm64.yml')
        new['additional_unsigned_owner_workflows'].remove(added[0])
        new['reviewed_workflow_ids'].remove(added[0]['id'])
        new['audit_workflows']-=1
        self.assertEqual(old,new)

if __name__=='__main__':unittest.main(verbosity=2)
