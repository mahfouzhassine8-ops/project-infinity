"""Selected package, recovery and original-signer checks. No app execution."""
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
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import release453 as r
import forward_recovery as recovery
from component_bundles import set_version

class Release453Policy(unittest.TestCase):
    def test_original_signer_and_protected_validation_unchanged(self):
        for name in ('assemble.py','component_bundles.py','signer_policy.py','inventory.py',
                     'release_authority.py','ownership-reviewed-roots.json','accepted-combined-release.json'):
            path=r.ISO/name
            self.assertEqual(path.read_bytes(),__import__('subprocess').check_output(
                ['git','show',r.BASE+':'+str(path.relative_to(r.REPO))]),name)
        path=r.ISO/'release_gate.py'
        before=r.cmd('git','show',r.BASE+':'+str(path.relative_to(r.REPO)))
        expected=before.replace("AUTHORITY_BRANCH = 'work/infinity-kodi-2103451-checkpoint-anr-20261103'",
                                "AUTHORITY_BRANCH = '"+r.BRANCH+"'")
        self.assertEqual(path.read_text(),expected)
        for path in (r.CANDIDATE/'candidate/xbmc/messaging/ApplicationMessenger.cpp',
                     r.INTEGRATION/'evidence/NATIVE-SOURCE-MAP.json'):
            self.assertEqual(path.read_bytes(),__import__('subprocess').check_output(
                ['git','show',r.BASE+':'+str(path.relative_to(r.REPO))]))

    def test_signer_inventory_only_adds_verified_unsigned_native_workflow(self):
        path=r.ISO/'signer-policy.json'
        before=json.loads(r.cmd('git','show',r.BASE+':'+str(path.relative_to(r.REPO))))
        after=r.load(path)
        self.assertEqual(set(after['reviewed_workflow_ids'])-set(before['reviewed_workflow_ids']),{406545245})
        self.assertEqual(set(before['reviewed_workflow_ids'])-set(after['reviewed_workflow_ids']),set())
        for key in set(before)-{'reviewed_workflow_ids','additional_unsigned_owner_workflows','audit_workflows'}:
            self.assertEqual(before[key],after[key],key)
        added=after['additional_unsigned_owner_workflows'][len(before['additional_unsigned_owner_workflows']):]
        self.assertEqual(len(added),1); row=added[0]
        self.assertEqual(row['id'],406545245); self.assertIs(row['original_key_access'],False)
        raw=(r.REPO/row['path']).read_bytes()
        self.assertEqual(r.digest(raw),row['workflow_sha256']); self.assertNotIn(b'secrets.',raw)

    def test_original_key_step_is_guarded_and_recovery_precedes_signing(self):
        raw=(r.REPO/'.github/workflows/infinity-combined-release.yml').read_text()
        config=yaml.safe_load(raw); triggers=config.get('on',config.get(True))
        self.assertEqual(set(triggers),{'workflow_dispatch'})
        self.assertEqual(config['permissions'],{'contents':'read','actions':'read'})
        self.assertIn('prepare-kodi453',config['jobs'])
        keys=[(job,i,s) for job,v in config['jobs'].items() for i,s in enumerate(v['steps'])
              if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
        self.assertEqual(len(keys),1); job,i,key=keys[0];self.assertEqual(job,'combined')
        before='\n'.join(s.get('run','') for s in config['jobs'][job]['steps'][:i])
        for required in ('test_release453.py','signer_policy.py check','check_registered','release_gate.py','EXACT_VERIFIED_UNSIGNED_APK'):
            self.assertIn(required,before)
        self.assertIn('assemble.py sign',key['run'])
        self.assertIn('verify_recovery', (HERE/'release453.py').read_text())
        for forbidden in ('continue-on-error','needs:','emulator-runner','adb shell','build.py compile','retire --'):
            self.assertNotIn(forbidden,raw)
        self.assertIn(r.BRANCH,config['jobs']['prepare-kodi453']['if'])

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
            original={'AndroidManifest.xml':set_version(manifest,2103452),r.LABEL:b'infinity.last_updated_in=2103452\ncobra.last_updated_in=2103445\n',r.NATIVE:b'original native','classes.dex':b'Splash','classes2.dex':b'shared','classes3.dex':b'Preview','classes4.dex':b'Cobra','classes5.dex':b'unchanged classes','resources.arsc':b'icons/themes','lib/arm64-v8a/libother.so':b'protected library','assets/addons/example':b'provider/skin'}
            self.archive(base,original)
            desired=dict(original,**{'AndroidManifest.xml':set_version(manifest,r.VERSION),r.LABEL:b'infinity.last_updated_in=2103453\ncobra.last_updated_in=2103445\n',r.NATIVE:b'compiled P0 native'})
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


    def test_recovery_requires_forward_version_and_preserves_frozen_owners(self):
        prior=r.previous(); self.assertEqual(prior['candidate_versionCode'],2103452)
        payload=copy.deepcopy(prior['payload'])
        payload['member:'+r.NATIVE]['sha256']=r.NATIVE_SHA
        payload['member:'+r.LABEL]['sha256']=r.digest(recovery.labels(2103453))
        current=recovery.forward_authority(prior,payload,2103453,r.BASE)
        restored=copy.deepcopy(prior['payload'])
        restored['member:'+r.LABEL]['sha256']=r.digest(recovery.labels(2103454))
        next_authority=recovery.forward_authority(current,restored,2103454,r.BASE)
        self.assertEqual(next_authority['protected_contract'],prior['protected_contract'])
        for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
            self.assertEqual(next_authority['components'][owner],prior['components'][owner])
        with self.assertRaisesRegex(Exception,'RECOVERY_MUST_ADVANCE_VERSION'):
            recovery.forward_authority(current,restored,2103452,r.BASE)
        bad=copy.deepcopy(restored); key=next(k for k,v in bad.items() if v['owner']=='COBRA')
        bad[key]['sha256']='0'*64
        with self.assertRaises(Exception):recovery.forward_authority(current,bad,2103454,r.BASE)
        with tempfile.TemporaryDirectory() as temp:
            for version in (2103452,2103453):
                with self.assertRaisesRegex(Exception,'RECOVERY_MUST_ADVANCE_VERSION'):
                    recovery.build_unsigned_recovery(Path('unused'),Path(temp)/'no.apk',version,2103453)

    def test_verified_native_and_input_identity_are_fixed(self):
        self.assertEqual(r.NATIVE_SHA,'d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98')
        for asset in r.ASSETS.values():
            ident,run,name,size,sha=asset
            row=dict(id=ident,workflow_run={'id':run},name=name,size_in_bytes=size,digest='sha256:'+sha,expired=False)
            r.validate_metadata(row,asset)
            for key,value in [('id',0),('digest','sha256:'+'0'*64),('expired',True)]:
                bad=copy.deepcopy(row);bad[key]=value
                with self.assertRaises(Exception):r.validate_metadata(bad,asset)

    def test_false_runtime_or_retirement_claims_fail_official_preparation(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            valid=dict(run_id=1,source='a'*40,status='PASS_NATIVE_P0_PACKAGING_RUNTIME_PENDING',baseline=r.BASE,
                baseline_apk_sha256=r.APK_SHA,native_sha256=r.NATIVE_SHA,native_build_source=r.NATIVE_SOURCE,
                native_build_run=r.NATIVE_RUN,native_build_artifact=r.NATIVE_ARTIFACT,Android=r.RUNTIME,
                physical_Fold='PENDING',historical_watched_route='UNKNOWN',unknown_obligations='REMAIN_BLOCKING',
                accepted_pointer_updated=False)
            run=dict(status='completed',conclusion='success',head_sha=valid['source'],head_branch=r.BRANCH,
                     path='.github/workflows/infinity-combined-release.yml')
            for field,value in [('Android','PASS'),('physical_Fold','PASS'),('unknown_obligations','IGNORED'),
                                ('historical_watched_route','LOCAL'),('accepted_pointer_updated',True),('native_sha256','0'*64)]:
                bad=dict(valid);bad[field]=value;(d/'PREPARATION.json').write_text(json.dumps(bad))
                with patch.object(r,'cmd',return_value=json.dumps(run)),self.assertRaisesRegex(Exception,'EXACT_PHYSICAL_TEST_CANDIDATE_SCOPE'):
                    r.official(d,1)
            (d/'PREPARATION.json').write_text(json.dumps(valid))
            with patch.object(r,'cmd',return_value=json.dumps(run)),self.assertRaisesRegex(Exception,'FORWARD_RECOVERY_GATE'):
                r.official(d,1)

if __name__=='__main__':unittest.main(verbosity=2)
