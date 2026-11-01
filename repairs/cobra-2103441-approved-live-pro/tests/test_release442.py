"""Selected release protocol tests; no application or shutdown execution."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import release442 as release
import release_gate

class ReleaseTests(unittest.TestCase):
    def test_authorized_release_route_and_frozen_guards(self):
        self.assertEqual(release_gate.AUTHORITY_BRANCH,release.BRANCH)
        self.assertEqual(release_gate.DISPLAY_PROTECTED_COMMIT,release.BASE)
        current=(release.ISO/'release_gate.py').read_text()
        old=release.cmd('git','show',release.AUTHORITY_BASE+':repairs/dual-experience-isolation-2103420/release_gate.py')
        self.assertEqual(current,old)
    def test_workflow_keys_follow_payload_gates(self):
        data=yaml.safe_load((release.REPO/'.github/workflows/infinity-combined-release.yml').read_text())
        self.assertEqual(data['name'],'Infinity combined release | owner gate before original signing')
        for name,job in data['jobs'].items():
            self.assertIn(release.BRANCH,job['if'])
            import re
            for step in job['steps']:
                for path in re.findall(r'python3 (repairs/[^ \\n]+\.py)',step.get('run','')):self.assertTrue((release.REPO/path).is_file(),path)
            key_steps=[i for i,s in enumerate(job['steps']) if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
            if name!='combined':self.assertEqual(key_steps,[]);continue
            self.assertEqual(len(key_steps),1);i=key_steps[0]
            before='\n'.join(s.get('run','') for s in job['steps'][:i])
            for guard in ('test_release442.py','signer_policy.py check','check_registered','release_gate.py'):self.assertIn(guard,before)
            self.assertIn('assemble.py sign',job['steps'][i]['run'])
        self.assertNotIn('continue-on-error',(release.REPO/'.github/workflows/infinity-combined-release.yml').read_text())
    def test_exact_member_comparison_rejects_extra_change(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);base=d/'base.apk';cand=d/'candidate.apk';plan=d/'plan.json'
            members={'AndroidManifest.xml':b'436',release.LABEL:b'436','assets/loading':b'old','classes4.dex':b'frozen Cobra'}
            with ZipFile(base,'w') as z:
                for n,v in members.items():z.writestr(n,v)
            members.update({'AndroidManifest.xml':b'438',release.LABEL:b'438','assets/loading':b'new'})
            plan.write_text(json.dumps({'changed_members':['assets/loading']}))
            def write():
                with ZipFile(cand,'w') as z:
                    for n,v in members.items():z.writestr(n,v)
            with patch.object(release,'APK_SHA',release.file_sha(base)),patch.object(release,'normalize_manifest',side_effect=lambda b:(b'identity',2103442 if b==b'438' else 2103438)):
                write();report=release.compare(base,cand,plan,d/'pass')
                self.assertEqual(report['status'],'PASS_EXACT438_APK_MEMBER_COMPARISON')
                members['classes4.dex']=b'changed Cobra';write()
                with self.assertRaisesRegex(Exception,'EXACT_APK_DELTA'):release.compare(base,cand,plan,d/'fail')
    def test_original_signed_input_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.apk';p.write_bytes(b'wrong baseline')
            with self.assertRaisesRegex(Exception,'EXACT_SIGNED438_APK'):release.compare(p,p,p,Path(d))

if __name__=='__main__':
    names=json.loads((ROOT/'SCOPE.json').read_text())['selected_release_tests']
    if sorted(names)!=unittest.defaultTestLoader.getTestCaseNames(ReleaseTests):raise RuntimeError('Test selection drift')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(ReleaseTests(n) for n in names))
    raise SystemExit(not result.wasSuccessful())
