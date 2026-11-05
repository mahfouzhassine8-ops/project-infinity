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
        for v in (2103455,2103458):
            with self.assertRaisesRegex(ValueError,'ONLY_CONTROLLED_AND_RECOVERY_VERSIONS'):r.generate(Path('unused'),v,Path('unused'))

    def test_all_twelve_completed_sources_match_checkpoint(self):
        self.assertEqual(len(r.plan()),12)
        self.assertEqual(sum(v['baseline451_sha256'] is None for v in r.plan().values()),7)
        for n,row in r.plan().items():
            p=r.ROOT/row['source'];self.assertEqual(p.read_bytes(),r.original(p));self.assertEqual(r.file_sha(p),row['candidate_source_sha256'])
        approved=r.load(r.ROOT/'repairs/infinity-native-touch-2103451-20261105/APPLIED-SOURCE-DELTA.json')
        self.assertEqual(len(approved['changed_files']),2)
        for n,row in approved['changed_files'].items():self.assertEqual(r.file_sha(r.ROOT/'repairs/infinity-native-touch-2103451-20261105/native'/n),row['after_sha256'])

    def test_actual_signed451_metadata_generations_and_precise_allowlist(self):
        baseline=Path(os.environ.get('INFINITY_CONTROLLED_BASELINE','/tmp/kodi451-signed-baseline/Infinity-2103451-Combined-Original-Signer.apk'))
        self.assertEqual(r.file_sha(baseline),r.APK_SHA)
        with tempfile.TemporaryDirectory(prefix='controlled-source-metadata-',dir='/tmp') as tmp,ZipFile(baseline) as z:
            for version,count,skin in ((2103456,77,254),(2103457,76,255)):
                root=Path(tmp)/str(version);root.mkdir();changes=r.generate(baseline,version,root,b'host-only-unexecuted-engine-placeholder')
                expected=(set(r.plan())|r.META|{r.NATIVE} if version==2103456 else r.META)-{r.CC+'INFINITY-MODULES.v1.sig'}
                self.assertEqual(set(changes),expected)
                text=changes[r.CC+'INFINITY-MODULES.v1'].decode()
                self.assertEqual(sum(line.startswith('file\t') for line in text.splitlines()),count)
                self.assertIn('package\t0.3.5.'+('57' if version==2103456 else '58')+'\n',text)
                prior=z.read(r.CC+'INFINITY-MODULES.v1').decode().splitlines()
                self.assertEqual([s for s in text.splitlines() if s.startswith(('entry\t','capability\t','protocol\t'))],[s for s in prior if s.startswith(('entry\t','capability\t','protocol\t'))])
                self.assertEqual(r.json.loads(changes[r.SKIN+'infinity-skin.json'])['candidate'],skin)
                if version==2103457:self.assertNotIn(r.NATIVE,changes)

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
        self.assertEqual(r.retained_ui.ref_versions(sha+' refs/heads/work/version-2103456'),[2103456])

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
        self.assertIn("'leftover_helper_rejected_by_original_import_contract'",recovery)
        self.assertIn("HERE/'recovery_checks.py'",body)
        self.assertNotIn('from recovery_checks import',body)

    def test_native_ABI_and_dependency_mismatches_refuse_before_signing(self):
        baseline=Path(os.environ.get('INFINITY_CONTROLLED_BASELINE','/tmp/kodi451-signed-baseline/Infinity-2103451-Combined-Original-Signer.apk'))
        with tempfile.TemporaryDirectory(prefix='controlled-ABI-negative-',dir='/tmp') as tmp:
            p=Path(tmp);lib=p/'new.so';lib.write_bytes(b'unexecuted-host-fixture')
            for mode,reason in [('dependency','ORIGINAL_NATIVE_LINK_CONTRACT'),('symbol','ORIGINAL_NATIVE_STRONG_ABI'),('same',None)]:
                def inspect(*args):
                    new=Path(args[-1])==lib
                    if args[1]=='-h':return 'ELF64 AArch64'
                    if args[1]=='-d':return '(NEEDED) [libc.so]\n'+('(NEEDED) [unapproved.so]' if new and mode=='dependency' else '')
                    return '1: 0001 2 FUNC GLOBAL DEFAULT 12 '+('changed' if new and mode=='symbol' else 'preserved')
                # Only this decoder-negative fixture is synthetic/bounded.
                # Real ELF bytes remain mandatory in the Actions preparation.
                with patch.object(r,'cmd',side_effect=inspect),patch.object(r,'FROZEN_NATIVE',r.digest(b'original-ELF-fixture')),patch.object(r,'ZipFile') as archive:
                    archive.return_value.__enter__.return_value.read.return_value=b'original-ELF-fixture'
                    if reason:
                        with self.assertRaisesRegex(ValueError,reason):r.native_compatibility(baseline,lib,p/'proof.json')
                    else:self.assertEqual(r.native_compatibility(baseline,lib,p/'proof.json')['status'],'PASS_NATIVE_TARGET_DEPENDENCIES_AND_STRONG_ABI')

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
        for job,operation in [('prepare-controlled456-457','prepare-controlled456-457'),('review-controlled456-457','review-controlled456-457')]:
            self.assertIn(r.BRANCH,new['jobs'][job]['if']);self.assertIn(operation,new['jobs'][job]['if'])
        review=new['jobs']['review-controlled456-457'];self.assertNotIn('secrets.',str(review))
        keyed=[s for s in new['jobs']['prepare-controlled456-457']['steps'] if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
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
        expected=old.replace(b"AUTHORITY_BRANCH = 'work/infinity-kodi-ui-2103454-2103455-packaging-20261104'",("AUTHORITY_BRANCH = '"+r.BRANCH+"'").encode())
        self.assertEqual(p.read_bytes(),expected)
        p=r.ISO/'signer-policy.json';old=r.json.loads(r.original(p));new=r.load(p)
        fields={'reviewed_workflow_ids','additional_unsigned_owner_workflows'}
        self.assertEqual({k:v for k,v in old.items() if k not in fields},{k:v for k,v in new.items() if k not in fields})
        self.assertEqual(set(new['reviewed_workflow_ids'])-set(old['reviewed_workflow_ids']),{407785045,407812103})
        extra=new['additional_unsigned_owner_workflows'][len(old['additional_unsigned_owner_workflows']):]
        self.assertEqual(len(extra),2)
        for row in extra:
            self.assertIs(row['original_key_access'],False)
            raw=subprocess.check_output(['git','show',row['source']+':'+row['path']],cwd=r.ROOT)
            self.assertEqual(r.digest(raw),row['workflow_sha256']);self.assertNotIn(b'secrets.',raw)

if __name__=='__main__':unittest.main(verbosity=2)
