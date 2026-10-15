#!/usr/bin/env python3
"""Replay accepted Android-only 3290/3291/3292 source lineage before the chooser delta.

The controller payload is not rebuilt. Its original checksum is pinned here and
independently checked against the exact signed 3295 APK by apply.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

CONTROLLER='cb6a2de4ecf9a47b3953d06ab8eccdf8cfbbcb4fb3a209b87f2ccc41f71c6688'
PARENT3291='02f2c4049a5205927c1698e675ca64dcc77659677bd9441f82e2fe92f4f25ece'
NATIVE3291='36a8feba9e8f7c857ca987b7d6ec868d847fcfc46f5369654ddac3b3e7038b94'
TEMPLATE='834ad448e1f969ef06120c746ceb69293757346fa093f00db5b610ebc2d9951a'
JAVA=Path('tools/android/packaging/xbmc/src')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def restore(root,repo,out):
    out.mkdir(parents=True,exist_ok=True)
    repairs=repo/'repairs'
    template=repairs/'resume-hub-2103292/InfinityResumeHubInstaller.java.in'
    assert H(template)==TEMPLATE,'Inherited Resume Hub template changed'
    destination=root/'repairs/resume-hub-2103292/InfinityResumeHubInstaller.java.in'
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(template,destination)
    def run(script,*args):
        subprocess.run([sys.executable,str(repairs/script),*map(str,args)],check=True)
    run('native-responsive-2103290/package_metadata.py','--root',root,
        '--base-apk-sha',PARENT3291,'--native-sha',NATIVE3291,'--proof',out/'binding-3290.json')
    run('inplace-reflow-2103291/android_package_delta.py','--root',root,
        '--base-apk-sha',PARENT3291,'--native-sha',NATIVE3291,'--proof',out/'binding-3291.json')
    run('resume-hub-2103292/apply_android.py','apply','--root',root,
        '--controller-sha',CONTROLLER,'--parent-apk-sha',PARENT3291,
        '--native-sha',NATIVE3291,'--proof',out/'binding-3292.json')
    run('resume-hub-2103292/apply_android.py','verify','--root',root,'--controller-sha',CONTROLLER)
    shell=root/'shell-kodi'
    main=shell/JAVA/'Main.java.in'
    installer=shell/JAVA/'InfinityResumeHubInstaller.java.in'
    assert main.read_text().count('InfinityResumeHubInstaller.apply(this);')==1
    assert installer.read_text()==template.read_text().replace('@CONTROLLER_ASSET_SHA256@',CONTROLLER)
    proof={'controller_asset_sha256':CONTROLLER,'installer_template_sha256':TEMPLATE,
        'main_sha256':H(main),'installer_sha256':H(installer),
        'inherited_recipes':{str(script):H(repairs/script) for script in (
            Path('native-responsive-2103290/package_metadata.py'),
            Path('inplace-reflow-2103291/android_package_delta.py'),
            Path('resume-hub-2103292/apply_android.py'))},
        'new_resume_hub_behavior':False,'controller_rebuilt':False,'native_rebuilt':False}
    (out/'INHERITED-RESUME-HUB-SOURCE.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    print('PASS: exact inherited 3291 trace + 3292 installer and Main hook restored before chooser delta')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    restore(a.root.resolve(),a.repo.resolve(),a.out.resolve())
