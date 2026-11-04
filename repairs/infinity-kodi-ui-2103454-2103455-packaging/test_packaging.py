"""Focused package/authority/recovery contracts; no application or shutdown suite."""
import ast
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import yaml
import release_ui as r


class Packaging(unittest.TestCase):
    def test_exact_overlay_checkpoint_and_full_allowlist(self):
        plan=r.load(r.UI/'SOURCE-PLAN.json')['changes']
        self.assertEqual(len(plan),11)
        self.assertEqual(sum(row['before'] is None for row in plan.values()),7)
        for n,row in plan.items():
            p=r.UI/'overlay'/n
            self.assertEqual(p.read_bytes(),r.original(p,r.SOURCE));self.assertEqual(r.file_sha(p),row['after'])
        self.assertEqual(len(set(plan)|r.META|{'AndroidManifest.xml'}),19)
        self.assertEqual(len(r.load(r.UI/'release-readiness/BASELINE-PROTECTED-MEMBER-HASHES.json')),7602)

    def test_only_exact_two_versions_allowed(self):
        with self.assertRaisesRegex(ValueError,'ONLY_AUTHORIZED_VERSIONS'):
            r.generate(Path('never-opened'),2103456,Path('never-created'))

    def test_ref_version_parser_ignores_hash_digits_but_detects_newer_ref(self):
        sha='a'*20+'2106853'+'b'*13
        self.assertEqual(r.ref_versions(sha+'\trefs/heads/infinity-kodi-upstream-toolkit-v1\n'),[])
        self.assertEqual(r.ref_versions(sha+'\trefs/heads/work/ui-2103454-2103455\n'),[2103454,2103455])
        self.assertEqual(r.ref_versions(sha+'\trefs/tags/testing-2103456\n'),[2103456])
        with self.assertRaisesRegex(ValueError,'VALID_REF_RECORD'):r.ref_versions('invalid refs/heads/version-2103454')

    def test_wrong_or_multiple_signer_rejected(self):
        with patch.object(r,'cmd',return_value='Signer #1 certificate SHA-256 digest: '+'0'*64):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_CERTIFICATE'):r.certificate(Path('unused'),Path('unused'))
        text='Signer #1 certificate SHA-256 digest: '+r.CERT_SHA+'\nSigner #2 certificate SHA-256 digest: '+r.CERT_SHA
        with patch.object(r,'cmd',return_value=text):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_CERTIFICATE'):r.certificate(Path('unused'),Path('unused'))

    def test_version_edit_requires_exactly_one_field(self):
        for value in (b'no field',b'version="x" version="x"'):
            with self.assertRaisesRegex(ValueError,'EXACT_SINGLE_VERSION_FIELD'):r.xml_replace(value,b'version="x"',b'version="y"')

    def test_native_manifest_verifier_path_contract_on_actual_signed_base(self):
        baseline=Path(os.environ.get('INFINITY_UI_BASELINE','/tmp/kodi453-published-signed/Infinity-2103453-Combined-Original-Signer.apk'))
        with tempfile.TemporaryDirectory(prefix='ui-original-module-check-') as tmp,ZipFile(baseline) as z:
            folder=Path(tmp);root=folder/'addons';root.mkdir()
            for n in z.namelist():
                if n.startswith('assets/addons/') and n.split('/')[2] in r.module_bundle.IDS:
                    p=root/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
            verifier=folder/'verifier'
            r.cmd('g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',r.FIRST/'verify_module_bundle.cpp',r.FIRST/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier)
            relative=Path(os.path.relpath(root))
            bad=r.subprocess.run([str(verifier),str(relative),str(r.FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')],capture_output=True,text=True)
            self.assertNotEqual(bad.returncode,0);self.assertIn('unavailable',bad.stderr)
            self.assertIn('NATIVE_VERIFIED package=0.3.5.54 protocol=1 files=76',r.verify_module(verifier,relative))

    def test_original_security_sources_frozen(self):
        for name in ('assemble.py','release_authority.py','component_bundles.py','signer_policy.py','signer-policy.json','accepted-combined-release.json'):
            p=r.ISO/name;self.assertEqual(p.read_bytes(),r.original(p))
        p=r.ISO/'release_gate.py'
        expected=r.original(p).replace(b"AUTHORITY_BRANCH = 'work/infinity-kodi-2103453-controlled-test-20261104'",("AUTHORITY_BRANCH = '"+r.BRANCH+"'").encode())
        self.assertEqual(p.read_bytes(),expected)

    def test_only_original_workflow_and_exact_branches_use_keys(self):
        path=r.REPO/'.github/workflows/infinity-combined-release.yml';workflow=yaml.safe_load(path.read_text())
        self.assertEqual(workflow['name'],'Infinity combined release | owner gate before original signing')
        self.assertEqual(workflow['concurrency']['group'],'infinity-combined-original-key-release')
        job=workflow['jobs']['prepare-ui454-455'];self.assertIn(r.BRANCH,job['if'])
        self.assertIn("inputs.operation == 'prepare-ui454-455'",job['if'])
        keyed=[s for s in job['steps'] if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
        self.assertEqual(len(keyed),1);self.assertIn('release_ui.py prepare',keyed[0]['run'])
        self.assertIn(r.BRANCH,workflow['jobs']['combined']['if'])
        self.assertIn('release_ui.py versions',str(workflow['jobs']['combined']))

    def test_signed_base_generates_only_proposed_metadata(self):
        baseline=Path(os.environ.get('INFINITY_UI_BASELINE','/tmp/kodi453-published-signed/Infinity-2103453-Combined-Original-Signer.apk'))
        self.assertTrue(baseline.exists(),'Exact original453 APK is required; do not skip this test')
        self.assertEqual(r.file_sha(baseline),r.APK_SHA)
        with tempfile.TemporaryDirectory(prefix='ui-metadata-contract-') as tmp,ZipFile(baseline) as z:
            for version,count in ((2103454,77),(2103455,76)):
                root=Path(tmp)/str(version);root.mkdir();changes=r.generate(baseline,version,root)
                manifest=changes[r.CC+'INFINITY-MODULES.v1'].decode().splitlines()
                self.assertEqual(len([n for n in manifest if n.startswith('file\t')]),count)
                self.assertEqual([n for n in manifest if n.startswith(('capability\t','entry\t','protocol\t'))],
                                 [n for n in z.read(r.CC+'INFINITY-MODULES.v1').decode().splitlines() if n.startswith(('capability\t','entry\t','protocol\t'))])
                for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
                    old=r.json.loads(z.read(r.SKIN+leaf));new=r.json.loads(changes[r.SKIN+leaf])
                    allowed={'candidate','version','candidate_version','skin_version','protected_files'}
                    self.assertEqual({k:v for k,v in old.items() if k not in allowed},{k:v for k,v in new.items() if k not in allowed})
                    if 'protected_files' in new:
                        changed={k for k in old['protected_files'] if old['protected_files'][k]!=new['protected_files'][k]}
                        expected={'addon.xml','infinity-skin.json'}
                        if version==2103454:expected|={'unified/Includes.xml','unified/MyVideoNav.xml','unified/Custom_1198_InfinityNav.xml'}
                        self.assertEqual(changed,expected)
                if version==2103455:self.assertEqual(set(changes),r.META-{r.CC+'INFINITY-MODULES.v1.sig'})


if __name__=='__main__':unittest.main(verbosity=2)
