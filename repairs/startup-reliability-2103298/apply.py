#!/usr/bin/env python3
import argparse, hashlib, json, shutil
from pathlib import Path
from patch_source import apply_source, once

PARENT='e0e70f6a0fc8ff9fbd8836f5979f90c64de4678fe0d468336fc59ce7cf4e9f0c'
COMMIT='83d51d49ed07687fbccef94ec2892000f6feae1e'
OLD_PARENT='dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0'
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
assert hashlib.sha256(a.parent.read_bytes()).hexdigest()==PARENT,'Not the user-locked 2103297 APK'
root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
receipt_path=root/'engine/background-resume-source.json';receipt=json.loads(receipt_path.read_text())
assert receipt['version_code']==2103297
assert receipt['base_apk_sha256']==OLD_PARENT
src=root/'shell-kodi'
for name,row in receipt['files'].items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==row['after'],name
before,after=apply_source(src)
receipt.update(version_code=2103298,release='1.0.9-Startup-Reliability-RC1',base_apk_sha256=PARENT,base_source_commit=COMMIT,
               locked_ancestor_apk_sha256=OLD_PARENT,locked_ancestor_source_commit='c562d7d1b0a5cb71df90484dc56a3fae6bf17001')
for path,digest in after.items():receipt['files'][path]={'before':before.get(path),'after':digest}
receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
for name in ('infinity_background_resume.py','package_background_resume.py'):
    path=root/'scripts'/name;s=path.read_text()
    s=s.replace('2103297','2103298').replace('Cosmic-Motion-Lifecycle-RC1','Startup-Reliability-RC1')
    if name=='infinity_background_resume.py':
        s=once(s,OLD_PARENT,PARENT);s=once(s,'c562d7d1b0a5cb71df90484dc56a3fae6bf17001',COMMIT)
    else:
        s=s.replace('cosmic-motion-lifecycle-2103298','startup-reliability-2103298')
        s=s.replace("'base_run':37092252001","'base_run':37100003228")
        s=s.replace('exact signed 2103295','exact signed 2103297')
    path.write_text(s)
dest=root/'repairs/startup-reliability-2103298';dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(Path(__file__).parent/'DEVICE-TEST.txt',dest/'DEVICE-TEST.txt')
rows=[{'path':p,'before_2103297':before.get(p),'after_2103298':after.get(p),
       'status':'unchanged' if before.get(p)==after.get(p) else 'changed' if p in before else 'added'} for p in sorted(after)]
(out/'SOURCE-BYTE-MANIFEST-2103298.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'SOURCE-CHANGES-2103298.json').write_text(json.dumps([r for r in rows if r['status']!='unchanged'],indent=2)+'\n')
(out/'REPAIR-SCOPE-2103298.json').write_text(json.dumps({'direct_locked_parent':PARENT,'direct_parent_commit':COMMIT,'locked_ancestor':OLD_PARENT,
    'native_recompiled':False,'skin_modified':False,'chooser_motion_or_layout_modified':False,'Cobra_player_modified':False,
    'Resume_Hub_or_Command_Center_modified':False,'touch_or_Fold_reflow_modified':False,'physical_device_verified':False,'locked':False,
    'known_parent_issue':'~26.5s logo-to-chooser delay in video; precise stage not proven',
    'source_checks':'strict 2 Java classes + 2 new startup helpers + Java registration/version allowlist; every other source file identical'},indent=2)+'\n')
print('PASS: strict Java-only 2103298 delta over exact locked 2103297')
