"""Selected release and negative preservation tests, without application execution."""
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
H=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(H))
import release447 as release
import release_gate
import release_guard
import patch_manifest

class ReleaseTests(unittest.TestCase):
    def test_original_signer_assembler_and_other_guards_frozen(self):
        for name in ('assemble.py','component_bundles.py','signer_policy.py','inventory.py'):
            path=release.ISO/name
            self.assertEqual(path.read_text(),release.cmd('git','show',release.BASE+':'+str(path.relative_to(release.REPO))))
        old=release.cmd('git','show',release.BASE+':repairs/dual-experience-isolation-2103420/release_gate.py')
        expected=old.replace("AUTHORITY_BRANCH = 'work/cobra-2103444-rotation-audio-preserved-20261101'",
            "EXTERNAL_BASELINE_REF = 'refs/heads/lock/infinity-cobra-2103445-user-approved-20261101'\nEXTERNAL_BASELINE_COMMIT = '"+release.BASE+"'\nAUTHORITY_BRANCH = '"+release.BRANCH+"'")
        expected=expected.replace('QUALITY_PROTECTED_REF, ROTATION_PROTECTED_REF)','QUALITY_PROTECTED_REF, ROTATION_PROTECTED_REF, EXTERNAL_BASELINE_REF)')
        expected=expected.replace('    require(refs.get(ROTATION_PROTECTED_REF)',"    require(refs.get(EXTERNAL_BASELINE_REF) == EXTERNAL_BASELINE_COMMIT, 'EXTERNAL445_APPROVED_LOCK_MOVED')\n    require(refs.get(ROTATION_PROTECTED_REF)")
        self.assertEqual((release.ISO/'release_gate.py').read_text(),expected)
        roots=json.loads(release.cmd('git','show',release.BASE+':repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'))
        roots['project_roots'].update(ExternalVideoRoute='CHOOSER_SHELL',InfinityExternalState='INFINITY',InfinityExternalEngine='INFINITY',InfinityExternalPlayerActivity='INFINITY')
        self.assertEqual(release.load(release.ISO/'ownership-reviewed-roots.json'),roots)

    def test_workflow_keys_after_all_gates_and_exact_branch(self):
        raw=(release.REPO/'.github/workflows/infinity-combined-release.yml').read_text()
        data=yaml.safe_load(raw)
        self.assertEqual(set(data['jobs']),{'prepare-external447','combined'})
        for name,job in data['jobs'].items():
            self.assertIn(release.BRANCH,job['if'])
            for step in job['steps']:
                for path in re.findall(r'python3 (repairs/[^\s\\]+\.py)',step.get('run','')):
                    self.assertTrue((release.REPO/path).is_file(),path)
            keys=[i for i,s in enumerate(job['steps']) if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
            if name!='combined':self.assertEqual(keys,[]);continue
            self.assertEqual(len(keys),1)
            before='\n'.join(s.get('run','') for s in job['steps'][:keys[0]])
            for guard in ('test_release447.py','signer_policy.py check','check_registered','release_gate.py'):
                self.assertIn(guard,before)
            self.assertIn('assemble.py sign',job['steps'][keys[0]]['run'])
        self.assertNotIn('continue-on-error',raw)

    def proposal(self):
        old=release.previous();new=copy.deepcopy(old)
        new['candidate_versionCode']=2103447
        raw=patch_manifest.patch((release.REPO/release_guard.REFERENCE).read_bytes())
        pin=release.digest(release.normalize_manifest(raw)[0])
        new['payload']['member:AndroidManifest.xml']['sha256']=pin
        names=(release_guard.AUTH,release_guard.REFERENCE,release_guard.PREFIX+'patch_manifest.py',release_guard.PREFIX+'release_guard.py')
        new['external_player_manifest_exception']=dict(schema=1,authorization=release_guard.AUTH,authorization_sha256=release_guard.AUTH_SHA,
            reference=release_guard.REFERENCE,reference_sha256=release_guard.REFERENCE_SHA,candidate_manifest_sha256=pin,
            source_inputs={n:release.file_sha(release.REPO/n) for n in names})
        return old,new

    def test_manifest_exception_rejects_shared_executable_or_artwork_change(self):
        old,new=self.proposal()
        release_guard.transition(old,new,release.TARGETS)
        release_guard.verify_evidence(new,lambda n:(release.REPO/n).read_bytes())
        shared=[k for k,v in old['payload'].items() if v['owner']==release_guard.OWNER and k!='member:AndroidManifest.xml']
        for key in (shared[0],next(k for k in shared if k.startswith('class:'))):
            bad=copy.deepcopy(new);bad['payload'][key]['sha256']='0'*64
            with self.assertRaisesRegex(Exception,'SHARED_EXECUTABLE_RESOURCE_NATIVE_BYTES_FROZEN'):
                release_guard.transition(old,bad,release.TARGETS)
        bad=copy.deepcopy(new);bad['launcher_icon_exception']={}
        with self.assertRaisesRegex(Exception,'ORIGINAL_LAUNCHER_ARTWORK_PROOF_FROZEN'):
            release_guard.transition(old,bad,release.TARGETS)

    def test_manifest_evidence_rejects_forged_reference_and_transform(self):
        _,new=self.proposal()
        with self.assertRaisesRegex(Exception,'EXTERNAL_MANIFEST_REVIEWED_SOURCE'):
            release_guard.verify_evidence(new,lambda n:b'forged' if n==release_guard.REFERENCE else (release.REPO/n).read_bytes())
        bad=copy.deepcopy(new);bad['payload']['member:AndroidManifest.xml']['sha256']='0'*64
        bad['external_player_manifest_exception']['candidate_manifest_sha256']='0'*64
        with self.assertRaisesRegex(Exception,'EXTERNAL_EXACT_DERIVED_MANIFEST'):
            release_guard.verify_evidence(bad,lambda n:(release.REPO/n).read_bytes())

    def test_exact_apk_allowlist_rejects_cobra_native_or_skin_change(self):
        from component_bundles import set_version
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);base=d/'base.apk';candidate=d/'new.apk';plan=d/'plan.json'
            manifest=(release.REPO/release_guard.REFERENCE).read_bytes()
            members={'AndroidManifest.xml':manifest,release.LABEL:b'old labels','classes.dex':b'old shell','classes3.dex':b'old Infinity',
                     'classes4.dex':b'frozen Cobra','lib/arm64-v8a/libkodi.so':b'frozen native','assets/skin':b'frozen skin'}
            def write(path,values):
                with ZipFile(path,'w') as z:
                    for n,v in values.items():z.writestr(n,v)
            write(base,members)
            changed=dict(members,**{'AndroidManifest.xml':set_version(patch_manifest.patch(manifest),2103447),
                release.LABEL:b'infinity.last_updated_in=2103447\ncobra.last_updated_in=2103445\n','classes.dex':b'new shell','classes3.dex':b'new Infinity'})
            plan.write_text(json.dumps({'compiled_members':{n:release.digest(changed[n]) for n in ('classes.dex','classes3.dex')}}))
            with patch.object(release,'APK_SHA',release.file_sha(base)):
                write(candidate,changed)
                self.assertEqual(release.compare(base,candidate,plan,d/'pass')['status'],'PASS_EXACT_SIGNED445_PRESERVATION')
                for name in ('classes4.dex','lib/arm64-v8a/libkodi.so','assets/skin'):
                    bad=dict(changed);bad[name]=b'tampered';write(candidate,bad)
                    with self.assertRaisesRegex(Exception,'UNEXPECTED_APK_MEMBER_DELTA'):
                        release.compare(base,candidate,plan,d/'fail')

    def test_wrong_baseline_rejected_before_packaging(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'wrong.apk';p.write_bytes(b'not signed445')
            with self.assertRaisesRegex(Exception,'EXACT_SIGNED445_APK'):
                release.compare(p,p,p,Path(tmp))

if __name__=='__main__':unittest.main(verbosity=2)
