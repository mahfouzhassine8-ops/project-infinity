"""Exact current owner delta against the protected signed433 payload inventory.

Undo only the one admitted host-selection prefix to verify the ENTIRE original
Activity class, including Pro, all callbacks, overlays, playback and shutdown.
No application execution; no new meaning assigned to prior test evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
OWNER=HERE.parent
REPO=OWNER.parents[2]
sys.path.insert(0,str(OWNER))
from projection_patch import methods

SOURCE='6f6abe78fae65046e1ef475c558957eae873130f'
CHANGED={'class:Lcom/projectinfinity/kodi/'+n+';' for n in (
 'CobraCardsLayout$State','CobraCardsLayout','CobraCardsReuse$Stamp','CobraCardsReuse$State',
 'CobraCardsReuse','CobraCardsTiles$Holder','CobraCardsTiles$MoreView','CobraComponent','InfinityLiveActivity')}
ADDED={'class:Lcom/projectinfinity/kodi/CobraCardsLayout$DensityProfile;'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def verify(work,out):
    old=json.loads(subprocess.check_output(['git','-C',str(REPO),'show',SOURCE+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    expected={k:v for k,v in old['payload'].items() if v['owner']=='COBRA' and k.startswith('class:')}
    actual={}
    for p in (work/'independent-canonical').rglob('*.smali'):
        raw=p.read_text();key='class:'+raw.splitlines()[0].split()[-1];assert key not in actual;actual[key]=raw
    assert set(expected)<=set(actual),'No protected433 Cobra class may disappear'
    changed={k for k in expected if expected[k]['sha256']!=digest(actual[k].encode())}
    added=set(actual)-set(expected)
    assert changed==CHANGED and added==ADDED,'Exact reviewed433 delta required'
    key='class:Lcom/projectinfinity/kodi/InfinityLiveActivity;';raw=actual[key]
    budget=json.loads((OWNER/'fullscreen-more/SOURCE-BUDGET.json').read_text());method=methods(raw)[budget['signature']]
    prefix=('    invoke-static {v7, v8}, Lcom/projectinfinity/kodi/CobraCardsLayout;->frontPlayerSheetHost(Landroid/app/Activity;Ljava/lang/String;)Landroid/widget/FrameLayout;\n\n'
            '    move-result-object v2\n\n    if-nez v2, :cond_2\n\n')
    assert method.count(prefix)==1 and method.count('    :cond_2\n    :goto_2\n')==1
    inverse=method.replace(prefix,'',1).replace('    :cond_2\n    :goto_2\n','    :goto_2\n',1)
    # One new conditional target adds one canonical cond label. Restore only
    # that method's sequential hexadecimal names, not any native instruction.
    inverse=re.sub(r':cond_([0-9a-f]+)',lambda m:':cond_'+format(int(m[1],16)-1,'x') if int(m[1],16)>=3 else m[0],inverse)
    assert digest(inverse.encode())==budget['preimage_sha256'],'Original native menu instructions must remain exact'
    reveal=methods(raw)[budget['reveal']['signature']]
    reveal_prefix=('    invoke-static {v0, v2}, Lcom/projectinfinity/kodi/CobraCardsLayout;->beginFrontCardsSheetReveal(Landroid/app/Activity;Landroid/view/View;)Z\n\n'
                   '    move-result v1\n\n    if-eqz v1, :cond_d\n\n')
    assert reveal.count(reveal_prefix)==1,'Exactly one once-start guard in native validated reveal path'
    reveal_inverse=reveal.replace(reveal_prefix,'',1)
    assert digest(reveal_inverse.encode())==budget['reveal']['preimage_sha256'],'Original native sheet geometry/animation instructions must remain exact'
    restored=raw.replace(method,inverse,1).replace(reveal,reveal_inverse,1)
    assert digest(restored.encode())==expected[key]['sha256'],'Entire433 Activity must match after only the two reviewed guard removals'
    key='class:Lcom/projectinfinity/kodi/CobraComponent;'
    assert actual[key].count('"2103435.cobra.1"')==1
    assert digest(actual[key].replace('"2103435.cobra.1"','"2103433.cobra.1"',1).encode())==expected[key]['sha256'],'Only genuine owner version changes'
    proof=dict(status='PASS_EXACT_SIGNED433_COBRA_DELTA',baseline_source=SOURCE,
      baseline_APK_sha256='874db7007b9fc79478844e5b37d4795d43c4c58de770c553d943734e1014b986',
      changed_classes=sorted(changed),added_classes=sorted(added),unchanged_existing_classes=len(expected)-len(changed),
      Activity='ENTIRE433_CLASS_EXACT_AFTER_ONLY_HOST_AND_ONCE_START_GUARD_REMOVAL',all_existing_menu_instructions_and_callbacks='EXACT433_AFTER_ONLY_TWO_REVIEWED_GUARDS_REMOVED',
      Pro_ProSports_MultiView_playback_PiP_shared_shutdown='EXACT433_METHODS_AND_FIELDS',
      scoped_helper_families=['CobraCardsLayout','CobraCardsTiles','CobraCardsReuse'],
      metadata='GENUINE_COBRA435_COMPONENT_VERSION_ONLY',APK='NOT_BUILT',runtime='NOT_RUN',shutdown='NOT_RUN')
    out.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return proof

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    verify(**vars(p.parse_args()))
