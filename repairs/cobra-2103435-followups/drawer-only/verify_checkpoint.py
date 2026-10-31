"""Fail-closed source/owner checkpoint; does NOT claim a final APK comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE='e0c6153588992001d84076d33fdf8f0d676c0d00'
LOCK='lock/infinity-cobra-2103435-user-approved-20261031'
LOCK_REF='refs/remotes/origin/'+LOCK
EXPECTED={
 'COBRA.zip':'e67dd28dab95206dcda8cb88903828453da57670468c532a32cd1db077663893',
 'INFINITY.zip':'a99e7bb789a0817fdfc9cc10b4e1649d52a2c78f0e3375f0735c55f4a91a0336',
 'MINIMAL_ANDROID_CONTRACT.zip':'432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8',
 'CHOOSER_SHELL.zip':'30589df7f2459a133b8fdd34f0bc56f8a5dc363d4f36accbb523a7ae47185f14'}
def sha(p):
 with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def load(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()

def verify(owner,host,components,out):
 assert git('branch','--show-current')=='work/cobra-only-from-2103435-20261031'
 assert git('rev-parse',LOCK_REF)==BASE
 assert git('ls-remote','origin','refs/heads/'+LOCK).split()[0]==BASE
 layout='repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsLayout.java'
 old=subprocess.check_output(['git','-C',str(REPO),'show',BASE+':'+layout]).decode()
 new=(REPO/layout).read_text()
 a='shell.getLocationInWindow(location);';b='CobraCardsDrawerViewport.location(a,shell,location);'
 assert old.count(a)==1 and new.count(b)==1 and new.replace(b,a,1)==old,'One Cards source coordinate call only'
 changed=git('diff','--name-only',BASE).splitlines()
 prefix='repairs/cobra-2103435-followups/'
 assert all(n==layout or n.startswith(prefix) for n in changed),changed
 untracked=git('ls-files','--others','--exclude-standard').splitlines()
 assert all(n.startswith(prefix) for n in untracked),untracked
 for name,pin in EXPECTED.items():assert sha(components/name)==pin,name
 build=load(owner/'BUILD.json');assert build['status']=='PASS_EXACT435_DRAWER_DELTA_OWNER_ONLY'
 for n,pin in build['compiler_sources'].items():assert sha(REPO/n)==pin,n
 for n,pin in build['output_DEX'].items():assert sha(owner/'owner-dex/COBRA'/n)==pin,n
 assert build['output_DEX']['part-1.dex']==build['baseline_DEX']['dex/part-1.dex']
 assert build['unchanged_classes']==7164 and len(build['changed_methods'])==2 and len(build['new_classes'])==2
 selection=load(host/'SELECTION.json');scope=load(HERE/'SCOPE.json')
 assert selection['methods']==scope['selected_host_methods']
 for name,pin in selection['source_SHA256'].items():assert sha(Path(name))==pin,name
 assert sha(host/'production.jar')==selection['production_sha256'] and sha(host/'support.jar')==selection['support_sha256']
 reports=sorted((host/'target/surefire-reports').glob('TEST-*.xml'));assert len(reports)==1
 root=ET.parse(reports[0]).getroot();assert all(root.get(n)=='0' for n in ['failures','errors','skipped'])
 methods=[c.get('name') for c in root.findall('testcase')]
 assert sorted(methods)==sorted(selection['methods']) and int(root.get('tests'))==5
 assert all(not list(c) or all(child.tag in ['system-out','system-err'] for child in c) for c in root.findall('testcase'))
 result=dict(status='PASS_TARGETED_SOURCE_OWNER_AND_FIVE_HOST_CASES_ONLY',source_parent=git('rev-parse','HEAD'),baseline_source=BASE,protected_lock=git('rev-parse',LOCK_REF),owner_build_sha256=sha(owner/'BUILD.json'),actual_owner_diff=build['changed_methods'],new_Cobra_classes=build['new_classes'],unchanged_Cobra_classes=7164,baseline_components=EXPECTED,unchanged_owner_payloads=['INFINITY','MINIMAL_ANDROID','CHOOSER_SHELL'],existing_functional_source_changes=[layout],source_budget='Exactly one Java coordinate-read call; two exact native/State calls in original DEX; new Cobra-only journey helper',drawer_animation='Original methods unchanged; no layout dimensions or animator mutations in helper',JUnit_methods=methods,JUnit_sha256=sha(reports[0]),measurements={p.name:sha(p) for p in sorted((host/'measurements').glob('*.json'))},media_review='BLOCKED: supplied timestamped PDF bytes/reference inaccessible; neither static frames nor full playback reviewed',Android_device_runtime='NOT_RUN',APK_member_comparison='PENDING: no successor APK has been created',signature='NOT_INVOKED; protected435 original identity unchanged',version='NOT_RESERVED',physical_Fold='USER_ACCEPTANCE_PENDING',shutdown='NOT_CHANGED_NOT_RUN',candidate_signed=False,promoted=False)
 out.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS two original-method deltas, two new Cobra helper classes,7164 unchanged classes, frozen owner ZIP hashes,5/5 selected host cases. PDF/native-device/final-APK gates NOT PASS.')

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('owner','host','components','out'):p.add_argument('--'+n,type=Path,required=True)
 verify(**vars(p.parse_args()))
