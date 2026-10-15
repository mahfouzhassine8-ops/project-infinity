#!/usr/bin/env python3
import argparse, hashlib, json, shutil
from pathlib import Path
from patch_source import apply_source, once

PARENT='c816160d25648741882e4a13f47af1ef20f08bda057a777e205a8fe13be2a237'
PARENT_COMMIT='e5f91a7e632ff581158131cba1a1cc8a33b54331'
LOCKED_PARENT='e0e70f6a0fc8ff9fbd8836f5979f90c64de4678fe0d468336fc59ce7cf4e9f0c'
LOCKED_ANCESTOR='dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0'
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
assert hashlib.sha256(a.parent.read_bytes()).hexdigest()==PARENT,'Not the exact tested 2103298 APK'
root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
receipt_path=root/'engine/background-resume-source.json';receipt=json.loads(receipt_path.read_text())
assert receipt['version_code']==2103298
assert receipt['base_apk_sha256']==LOCKED_PARENT
src=root/'shell-kodi'
for name,row in receipt['files'].items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==row['after'],name
before,after=apply_source(src)
receipt.update(version_code=2103299,release='1.0.9-Graceful-Exit-Handoff-RC1',
               base_apk_sha256=PARENT,base_source_commit=PARENT_COMMIT,
               locked_parent_apk_sha256=LOCKED_PARENT,
               locked_parent_source_commit='83d51d49ed07687fbccef94ec2892000f6feae1e',
               locked_ancestor_apk_sha256=LOCKED_ANCESTOR,
               locked_ancestor_source_commit='c562d7d1b0a5cb71df90484dc56a3fae6bf17001')
for path,digest in after.items():receipt['files'][path]={'before':before.get(path),'after':digest}
receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
for name in ('infinity_background_resume.py','package_background_resume.py'):
    path=root/'scripts'/name;s=path.read_text()
    s=s.replace('2103298','2103299').replace('Startup-Reliability-RC1','Graceful-Exit-Handoff-RC1')
    if name=='infinity_background_resume.py':
        s=once(s,LOCKED_PARENT,PARENT);s=once(s,'83d51d49ed07687fbccef94ec2892000f6feae1e',PARENT_COMMIT)
    else:
        s=s.replace('startup-reliability-2103299','graceful-exit-handoff-2103299')
        s=s.replace("'base_run':37100003228","'base_run':37105329683")
        s=s.replace('chooser-only 2103299 over exact signed 2103297',
                    'Java-only 2103299 over exact signed 2103298')
        s=once(s,"    require(old==new,'Compiled manifest drift from exact 2103208 base outside version identity')",'''    app=next(n for n in new['children'] if n['tag']=='application')
    bridge=[n for n in app['children'] if n['tag']=='activity' and 'InfinityPowerControlActivity' in n['attrs'].get('android:name','')]
    require(len(bridge)==1,'Exactly one private power bridge required')
    node=bridge[0]
    require(set(node['attrs'])=={'android:name','android:exported','android:excludeFromRecents','android:noHistory','android:theme'} and not node['children'],'Power bridge manifest expanded unexpectedly')
    require(node['attrs']['android:exported']=='(type 0x12)0x0','Power bridge must be private')
    require(node['attrs']['android:excludeFromRecents']=='(type 0x12)0xffffffff' and node['attrs']['android:noHistory']=='(type 0x12)0xffffffff','Power bridge must be transient')
    require(node['attrs']['android:theme']=='@0x01030055','Power bridge must use framework Theme.NoDisplay')
    app['children'].remove(node)
    require(old==new,'Compiled manifest drift beyond versions and exact private power bridge')''')
    path.write_text(s)
dest=root/'repairs/graceful-exit-handoff-2103299';dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(Path(__file__).parent/'DEVICE-TEST.txt',dest/'DEVICE-TEST.txt')
rows=[{'path':p,'before_2103298':before.get(p),'after_2103299':after.get(p),
       'status':'unchanged' if before.get(p)==after.get(p) else 'changed' if p in before else 'added'} for p in sorted(after)]
(out/'SOURCE-BYTE-MANIFEST-2103299.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'SOURCE-CHANGES-2103299.json').write_text(json.dumps([r for r in rows if r['status']!='unchanged'],indent=2)+'\n')
(out/'REPAIR-SCOPE-2103299.json').write_text(json.dumps({
    'direct_parent_2103298':PARENT,'direct_parent_source_commit':PARENT_COMMIT,
    'locked_parent_2103297':LOCKED_PARENT,'locked_ancestor_2103295':LOCKED_ANCESTOR,
    'native_recompiled':False,'apk_skin_assets_modified':False,'chooser_motion_or_layout_modified':False,
    'user_approved_skin_exception':'Runtime patch ONLY onclick bodies for Close Kodi (200) and Force Close Kodi (300), 13 known Infinity profiles; original files backed up; all other XML bytes preserved',
    'weather_change':'Read-only Main-owned capture of actual Kodi weather; cold chooser retains valid last-known reading; no GPS, network service or Kodi provider change',
    'Cobra_player_modified':False,'Resume_Hub_or_Command_Center_modified':False,
    'touch_or_Fold_reflow_modified':False,'physical_device_verified':False,'locked':False,
    'observed_trigger':'Power menu Close Kodi, then tap launcher; Force Close Kodi does not reproduce',
    'repair':'Pause/stop Android before dispatching existing graceful Application.Quit; no timed normal-close kill. Explicit Force uses current-package Java process termination, independently of the add-on. Closing Main excluded from live/fresh handoff.',
    'root_cause_status':'Shutdown ordering is a source-supported hypothesis, not physically proven; candidate requires measured Close/relaunch validation',
    'source_checks':'Strict 7-file Java/manifest/build delta + three Java helpers; all other source files identical'},indent=2)+'\n')
print('PASS: strict Java-only 2103299 delta over exact tested 2103298')
