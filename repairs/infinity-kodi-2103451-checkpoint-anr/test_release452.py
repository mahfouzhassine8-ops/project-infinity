"""Selected physical-candidate package/security checks; no app or shutdown run."""
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import release452 as r
from component_bundles import set_version


class Release452Policy(unittest.TestCase):
    def test_original_signer_and_all_runtime_producers_remain_exact(self):
        for name in ('assemble.py','component_bundles.py','signer_policy.py','inventory.py',
                     'release_authority.py','ownership-reviewed-roots.json'):
            p = r.ISO / name
            self.assertEqual(p.read_bytes(), __import__('subprocess').check_output(
                ['git','show',r.BASE+':'+str(p.relative_to(r.REPO))]), name)
        for name in r.FROZEN_NATIVE_SCRIPTS:
            p = HERE / name
            self.assertEqual(p.read_bytes(), __import__('subprocess').check_output(
                ['git','show',r.BASE+':'+str(p.relative_to(r.REPO))]), name)
        path = r.ISO / 'release_gate.py'
        before = r.cmd('git','show',r.BASE+':'+str(path.relative_to(r.REPO)))
        expected = before.replace("AUTHORITY_BRANCH = 'work/infinity-preview-2103450-fullscreen-display-20261102'", "AUTHORITY_BRANCH = '"+r.BRANCH+"'")
        anchor = "PREVIEW_BASELINE_COMMIT = '1fe75deaebdbf71d5873dc69ba3e21c0526954f0'\n"
        expected = expected.replace(anchor,anchor+"KODI451_BASELINE_REF = 'refs/heads/lock/infinity-preview-2103451-user-frozen-20261103'\nKODI451_BASELINE_COMMIT = '0b3450433adc3349056167a6697dae92dad63d86'\n")
        expected = expected.replace('EXTERNAL_BASELINE_REF, PREVIEW_BASELINE_REF)', 'EXTERNAL_BASELINE_REF, PREVIEW_BASELINE_REF, KODI451_BASELINE_REF)')
        anchor = "    require(refs.get(PREVIEW_BASELINE_REF) == PREVIEW_BASELINE_COMMIT, 'PREVIEW447_APPROVED_LOCK_MOVED')\n"
        expected = expected.replace(anchor,anchor+"    require(refs.get(KODI451_BASELINE_REF) == KODI451_BASELINE_COMMIT, 'KODI451_APPROVED_LOCK_MOVED')\n")
        self.assertEqual(path.read_text(), expected)

    def test_signer_inventory_adds_only_two_audited_unsigned_workflows(self):
        path = r.ISO / 'signer-policy.json'
        prior = json.loads(r.cmd('git','show',r.BASE+':'+str(path.relative_to(r.REPO))))
        current = r.load(path)
        self.assertEqual(current['sole_original_key_workflow_id'], 397702717)
        self.assertEqual(current['retired_original_key_workflows'], prior['retired_original_key_workflows'])
        ids = {406247408,406270295}
        self.assertEqual(set(current['reviewed_workflow_ids'])-set(prior['reviewed_workflow_ids']),ids)
        self.assertEqual(set(prior['reviewed_workflow_ids'])-set(current['reviewed_workflow_ids']),set())
        added = current['additional_unsigned_owner_workflows'][len(prior['additional_unsigned_owner_workflows']):]
        self.assertEqual({x['id'] for x in added},ids)
        for row in added:
            self.assertIs(row['original_key_access'],False)
            text=(r.REPO/row['path']).read_text()
            self.assertNotIn('secrets.',text)
            self.assertEqual(r.digest(text.encode()),row['workflow_sha256'])
        for key in set(prior)-{'reviewed_workflow_ids','additional_unsigned_owner_workflows','audit_workflows'}:
            self.assertEqual(current[key],prior[key],key)

    def test_single_original_key_step_is_after_strict_guards_and_no_runtime(self):
        raw=(r.REPO/'.github/workflows/infinity-combined-release.yml').read_text()
        config=yaml.safe_load(raw);triggers=config.get('on',config.get(True))
        self.assertEqual(set(triggers),{'workflow_dispatch'})
        self.assertEqual(config['permissions'],{'contents':'read','actions':'read'})
        self.assertEqual(set(config['jobs']),{'prepare-preview451','prepare-kodi452','combined'})
        key_steps=[]
        for job_name,job in config['jobs'].items():
            for index,step in enumerate(job['steps']):
                if 'INFINITY_KEYSTORE_B64' in step.get('env',{}):key_steps.append((job_name,index,step))
                for path in re.findall(r'python3 (repairs/[^\s\\]+\.py)',step.get('run','')):
                    self.assertTrue((r.REPO/path).is_file(),path)
        self.assertEqual(len(key_steps),1)
        job_name,index,key=key_steps[0];self.assertEqual(job_name,'combined')
        before='\n'.join(s.get('run','') for s in config['jobs'][job_name]['steps'][:index])
        for name in ('test_release452.py','signer_policy.py check','check_registered','release_gate.py','EXACT_VERIFIED_UNSIGNED_APK'):
            self.assertIn(name,before)
        self.assertIn('assemble.py sign',key['run'])
        self.assertIn('expected-generation "${{ steps.selected.outputs.generation }}"',key['run'])
        self.assertIn(r.BRANCH,config['jobs']['prepare-kodi452']['if'])
        self.assertIn('prepare-kodi452',config['jobs']['prepare-kodi452']['if'])
        self.assertIn('prepared_prefix',raw)
        for forbidden in ('continue-on-error','needs:','emulator-runner','adb shell','build.py compile','retire --'):
            self.assertNotIn(forbidden,raw)

    @staticmethod
    def archive(path,members):
        with ZipFile(path,'w') as z:
            for name,data in members.items():z.writestr(name,data)

    def test_actual_member_gate_rejects_unrelated_payload_and_wrong_native_or_version(self):
        ext=r.REPO/'repairs/infinity-2103445-standalone-external-player'
        sys.path.insert(0,str(ext));from patch_manifest import patch as external_manifest
        manifest=external_manifest((ext/'reference/AndroidManifest-2103445.xml.bin').read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp);base=d/'old.apk';new=d/'new.apk'
            original={'AndroidManifest.xml':set_version(manifest,2103451),r.LABEL:b'infinity.last_updated_in=2103451\ncobra.last_updated_in=2103445\n',r.NATIVE:b'original native','classes.dex':b'Splash','classes2.dex':b'shared','classes3.dex':b'Preview','classes4.dex':b'Cobra','classes5.dex':b'unchanged classes','resources.arsc':b'icons/themes','lib/arm64-v8a/libother.so':b'protected library','assets/addons/example':b'provider/skin'}
            self.archive(base,original)
            desired=dict(original,**{'AndroidManifest.xml':set_version(manifest,r.VERSION),r.LABEL:b'infinity.last_updated_in=2103452\ncobra.last_updated_in=2103445\n',r.NATIVE:b'compiled P0 native'})
            with patch.object(r,'APK_SHA',r.file_sha(base)),patch.object(r,'NATIVE_SHA',r.digest(desired[r.NATIVE])):
                self.archive(new,desired)
                self.assertEqual(r.compare(base,new,d/'ok')['Android'],r.RUNTIME)
                for name in set(original)-r.ALLOWED:
                    bad=dict(desired);bad[name]=b'tampered';self.archive(new,bad)
                    with self.subTest(member=name),self.assertRaisesRegex(Exception,'UNEXPECTED_APK_MEMBER_DELTA'):
                        r.compare(base,new,d/'bad')
                for name,value,reason in [(r.NATIVE,b'wrong native','EXACT_NATIVE_ARTIFACT'),('AndroidManifest.xml',set_version(manifest,r.VERSION+1),'VERSION_ONLY_MANIFEST'),(r.LABEL,b'fake Cobra version','TRUTHFUL_VERSION_METADATA_ONLY')]:
                    bad=dict(desired);bad[name]=value;self.archive(new,bad)
                    with self.assertRaisesRegex(Exception,reason):r.compare(base,new,d/'bad')
                bad=dict(desired);bad['new/unowned']=b'added';self.archive(new,bad)
                with self.assertRaisesRegex(Exception,'EXACT_APK_MEMBER_SET'):r.compare(base,new,d/'added')

    def test_input_identities_and_runtime_pending_evidence_refuse_false_claims(self):
        for asset in r.ASSETS.values():
            ident,run,name,size,sha=asset
            row=dict(id=ident,workflow_run={'id':run},name=name,size_in_bytes=size,digest='sha256:'+sha,expired=False)
            r.validate_metadata(row,asset)
            for key,value in [('id',0),('digest','sha256:'+'0'*64),('expired',True)]:
                bad=copy.deepcopy(row);bad[key]=value
                with self.assertRaises(Exception):r.validate_metadata(bad,asset)
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            valid=dict(run_id=1,source='a'*40,status='PASS_NATIVE_P0_PACKAGING_RUNTIME_PENDING',baseline=r.BASE,baseline_apk_sha256=r.APK_SHA,native_sha256=r.NATIVE_SHA,native_build_source=r.NATIVE_SOURCE,native_build_run=r.NATIVE_RUN,native_build_artifact=r.NATIVE_ARTIFACT,Android=r.RUNTIME,physical_Fold='PENDING',historical_watched_route='UNKNOWN',unknown_obligations='REMAIN_BLOCKING',accepted_pointer_updated=False)
            run=dict(status='completed',conclusion='success',head_sha=valid['source'],head_branch=r.BRANCH,path='.github/workflows/infinity-combined-release.yml')
            for field,value in [('Android','PASS'),('physical_Fold','PASS'),('historical_watched_route','LOCAL'),('unknown_obligations','IGNORED'),('accepted_pointer_updated',True),('native_sha256','0'*64)]:
                bad=dict(valid);bad[field]=value;(d/'PREPARATION.json').write_text(json.dumps(bad))
                with patch.object(r,'cmd',return_value=json.dumps(run)),self.assertRaisesRegex(Exception,'EXACT_PHYSICAL_TEST_CANDIDATE_SCOPE'):
                    r.official(d,1)
        prior=r.previous()
        self.assertEqual(prior['candidate_versionCode'],2103451)
        self.assertEqual(prior['components']['COBRA']['version'],'2103445.cobra.1')
        self.assertNotIn('MINIMAL_ANDROID_CONTRACT',r.TARGETS)


if __name__=='__main__':unittest.main(verbosity=2)
