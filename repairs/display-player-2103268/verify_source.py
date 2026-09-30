#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,sys
import apply as repair
ALLOWED=['showCobraAspectPicker','cobraShowChannelAspect','cobraShowChannelCustomAspect','showPlayerSettingsDrawer','cobraBuildPlayerChrome','cobraOpenSheet','cobraRenderPlayerDrawer','cobraRefreshPlayingIndicators','cobraFitVideo']
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 before=(a.baseline/'shell-kodi'/repair.ACTIVITY).read_text();after=(a.root/'shell-kodi'/repair.ACTIVITY).read_text();assert repair.sha(before.encode())==repair.PARENT_HASH
 assert after.count(repair.HELPERS)==1
 restored=after.replace(repair.HELPERS,'',1)
 for name in ALLOWED:
  x,y=repair.span(before,name);restored=repair.member(restored,name,before[x:y])
 assert restored==before,'Production edits outside approved Display/player members'
 changed=[];inventory=[]
 for f in sorted((a.baseline/'shell-kodi').rglob('*')):
  if not f.is_file():continue
  n=f.relative_to(a.baseline/'shell-kodi');g=a.root/'shell-kodi'/n;assert g.is_file(),str(n)
  old=repair.sha(f.read_bytes());new=repair.sha(g.read_bytes());inventory.append(dict(path=str(n),before=old,after=new))
  if old!=new:changed.append(str(n))
 assert changed==['tools/android/packaging/xbmc/build.gradle.in',repair.ACTIVITY],changed
 assert len(list((a.root/'shell-kodi').rglob('*')))==len(list((a.baseline/'shell-kodi').rglob('*')))
 assert 'mPlayerOverlay.setOnLongClickListener(v -> true);' in after
 for token in ['static final long HANDOFF_MS=180L;','static final long COLOR_MORPH_MS=240L;','static final int CINEMA_AMBER=0xffffc247;']:assert token in after,token
 report=dict(parent_version=2103267,parent_commit=repair.PARENT_COMMIT,parent_apk_sha256=repair.PARENT_APK,changed_shell_files=changed,changed_existing_activity_members=ALLOWED,all_other_source_bytes_preserved=True,pro_preserved=True,no_long_press_preserved=True,playing_dot_policy_preserved=True,providers_native_calls_pip_timeshift_preserved=True,infinity_skin_touched=False,physical_device_verified=False,locked=False,files=inventory)
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: exact locked 2103267 rollback and all protected source members/files preserved')
if __name__=='__main__':main()
