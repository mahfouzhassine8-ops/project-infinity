#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
from patch_source import apply_source, once, H

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
src=root/'shell-kodi'
before,after=apply_source(src)
manifest=root/'engine/background-resume-source.json'
receipt=json.loads(manifest.read_text())
receipt.update(version_code=2103297,release='1.0.9-Cosmic-Motion-Lifecycle-RC1')
for path,digest in after.items():
    receipt['files'][path]={'before':receipt['files'].get(path,{}).get('before'),'after':digest}
manifest.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
for name in ('infinity_background_resume.py','package_background_resume.py'):
    f=root/'scripts'/name;s=f.read_text().replace('2103296','2103297').replace('Cosmic-Chooser-RC1','Cosmic-Motion-Lifecycle-RC1')
    # Original checklist path is retained in the old script until replaced below.
    if name=='package_background_resume.py':
        s=s.replace("ROOT/'repairs/cosmic-chooser-2103297/DEVICE-TEST.txt'","ROOT/'repairs/cosmic-motion-lifecycle-2103297/DEVICE-TEST.txt'")
    f.write_text(s)
import shutil
dest=root/'repairs/cosmic-motion-lifecycle-2103297';dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(Path(__file__).parent/'DEVICE-TEST.txt',dest/'DEVICE-TEST.txt')
rows=[{'path':p,'before_3296':before.get(p),'after_3297':after.get(p),'status':'unchanged' if before.get(p)==after.get(p) else 'changed' if p in before else 'added'} for p in sorted(set(before)|set(after))]
(out/'MOTION-LIFECYCLE-SOURCE-MANIFEST.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'MOTION-LIFECYCLE-SOURCE-AUDIT.json').write_text(json.dumps({'parent_apk_sha256':receipt['base_apk_sha256'],'version_code':2103297,
    'source_changes':[r for r in rows if r['status']!='unchanged'],'native_rebuilt':False,'skin_modified':False,
    'physical_device_verified':False,'locked':False,'checks':'strict Java allowlist; inherited Resume Hub hook; all other reconstructed files hash-identical'},indent=2)+'\n')
print('PASS: 2103297 strict forward Java motion/lifecycle delta; parent payload remains exact 2103295')
