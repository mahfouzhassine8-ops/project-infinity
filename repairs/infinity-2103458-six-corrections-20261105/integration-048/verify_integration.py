"""Consolidated source gate for the exact approved integration, without application execution."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
APPROVAL='04806da44330e5db4a795bf291625e72abded128'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    approved=json.loads((HERE.parent/'navigation-6a/MANIFEST.json').read_text())
    applied=json.loads((HERE/'APPLIED-APPROVED-PATCH.json').read_text())
    checks=[]
    def check(name,ok):
        checks.append({'name':name,'pass':bool(ok)})
        assert ok,name
    check('exact approval checkpoint',applied['approved_commit']==APPROVAL)
    patch=HERE.parent/'navigation-6a/UNAPPLIED-NAVIGATION.patch'
    check('reviewed patch unchanged',sha(patch.read_bytes())==approved['patch_sha256']==applied['approved_patch_sha256'])
    sources={}
    for name,row in applied['files'].items():
        raw=(ROOT/row['applied_source']).read_bytes();sources[name]=raw
        check('exact applied candidate: '+name,sha(raw)==approved['files'][name]['proposed_sha256'])
    with tempfile.TemporaryDirectory(prefix='infinity-approved-reverse-') as tmp:
        folder=Path(tmp)
        for name,raw in sources.items():
            dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        subprocess.run(['git','apply','--check','--reverse',str(patch)],cwd=folder,check=True,capture_output=True)
        subprocess.run(['git','apply','--reverse',str(patch)],cwd=folder,check=True,capture_output=True)
        for name,row in applied['files'].items():
            check('reverse-byte source preservation: '+name,sha((folder/name).read_bytes())==row['before_sha256'])
    prior=json.loads((HERE.parent/'integration-44da/PRESERVATION.json').read_text())
    members={}
    for row in prior['runtime_member_allowlist']:
        path=row['source'];raw=(ROOT/path).read_bytes()
        expected=applied['files'][path]['proposed_sha256'] if path in applied['files'] else row['candidate_sha256']
        check('completed skin correction preserved: '+path,sha(raw)==expected)
        ET.fromstring(raw)
        members[row['APK_member']]={'signed458_sha256':row['signed458_sha256'],'candidate_sha256':sha(raw),'source':path}
    helper=next(n for n in applied['files'] if n.endswith('/library_navigation.py'))
    ast.parse(sources[helper].decode())
    compile(sources[helper],helper,'exec')
    members['assets/addons/script.infinity.commandcenter/library_navigation.py']={'signed458_sha256':approved['files'][helper]['before_sha256'],'candidate_sha256':sha(sources[helper]),'source':helper}
    native='xbmc/video/windows/GUIWindowVideoNav.cpp'
    check('native base file immutable',sha((Path('/tmp/kodi451-restored-native')/native).read_bytes())==approved['files'][native]['before_sha256'])
    search=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py'
    check('Search safety implementation unchanged',sha(search.read_bytes())=='61501614f0b49b407dea024a27d7cc6698979a8fc56aa00ec786c368b4e63a78')
    retained=json.loads((HERE.parent/'navigation-6a/RESULT.json').read_text())
    check('reuse exact reviewed fragment evidence',retained['pass_count']==53 and all(c['pass'] for c in retained['checks']))
    delta=subprocess.check_output(['git','diff','--name-only',APPROVAL],cwd=ROOT,text=True).splitlines()
    allowed={r['applied_source'] for r in applied['files'].values()}|{'.github/workflows/infinity-six-navigation-arm64.yml'}
    check('no unrelated tracked source changes',all(n.startswith(str(HERE.relative_to(ROOT))+'/') or n in allowed for n in delta))
    out={'status':'PASS_EXACT_APPROVED_SOURCE_INTEGRATION','approval':APPROVAL,'immutable_base':2103458,'checks':checks,'pass_count':len(checks),'retained_not_rerun':{'navigation_fragment_checks':53,'prior_static_checks':23,'prior_Linux_changed_control_checks':58},'candidate_source_members':members,'native_source_delta':[native],'complete_ARM64_compile':'PENDING_REMOTE_NATIVE_STAGE','Android':'NOT RUN','Fold':'NOT RUN','Search_acceptance':'TWO_FAILS_RETAINED','Downloads':'BLOCKED_POSITIVE_CLASSIFICATION','APK':'NOT_BUILT','no_runtime_changes_outside_six_groups':True}
    (HERE/'SOURCE-INTEGRATION-RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'checks':len(checks),'APK_source_members':len(members),'native_files_changed':1}))


if __name__=='__main__':main()
