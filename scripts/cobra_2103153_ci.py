#!/usr/bin/env python3
"""Run the pinned parent reconstruction and promote only the audited Android delta."""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile
BASE='cce2de3042cca22b531fa8ed9e13659c19dab8a4'
RELEASE='1.0.9-Cobra-Guide-Session-Refinement'
VERSION=2103153
UI=['addons/script.infinity.cobra.theme/addon.xml','addons/script.infinity.cobra.theme/resources/cobra-ui.json']
def run(*args):subprocess.run(args,check=True)
def reconstruct():
    import yaml
    workflow=yaml.safe_load(subprocess.check_output(['git','show',BASE+':.github/workflows/infinity-cobra-2103152-player-reboot-lock.yml'],text=True))
    required={'Reconstruct protected RC3 Runtime v3 and 2103141 player source','Rebuild locked 2103151 presentation baseline','Apply 2103152 player reboot lock and continuity polish','Apply protected two-card chooser'}
    saved={p:Path(p).read_bytes() for p in UI}
    try:
        for p in UI:Path(p).write_bytes(subprocess.check_output(['git','show',BASE+':'+p]))
        seen=set()
        for step in workflow['jobs']['android-update']['steps']:
            if step.get('name') in required:
                print('::group::'+step['name'],flush=True)
                run('bash','-e','-o','pipefail','-c',step['run']);seen.add(step['name']);print('::endgroup::',flush=True)
        assert seen==required
    finally:
        for p,data in saved.items():Path(p).write_bytes(data)
    live=Path('kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
    Path('preflight/InfinityLiveActivity-2103152.java.in').write_bytes(live.read_bytes())
    from infinity_cobra_2103153_guide_session_refinement import BASE_SHA
    assert hashlib.sha256(live.read_bytes()).hexdigest()==BASE_SHA
    Path('preflight/locked-2103152-repository.zip').write_bytes(subprocess.check_output(['git','archive','--format=zip',BASE]))

def promote():
    for file,old,new in [
      ('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103138',f'versionCode {VERSION}'),
      ('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "1.0.9-Infinity-Lifecycle-Repair-RC3"',f'versionName "{RELEASE}"'),
      ('scripts/infinity_background_resume.py','VERSION_CODE = 2103138',f'VERSION_CODE = {VERSION}'),
      ('scripts/infinity_background_resume.py',"RELEASE = '1.0.9-Infinity-Lifecycle-Repair-RC3'",f"RELEASE = '{RELEASE}'"),
    ]:
        p=Path(file);text=p.read_text();assert text.count(old)==1,(file,old);p.write_text(text.replace(old,new,1))
    p=Path('scripts/package_background_resume.py');text=p.read_text();old='Infinity-1.0.9-Infinity-Lifecycle-Repair-RC3';assert old in text;p.write_text(text.replace(old,'Infinity-'+RELEASE))
    p=Path('engine/background-resume-source.json');row=json.loads(p.read_text())
    for name,value in row['files'].items():value['after']=hashlib.sha256((Path('kodi')/name).read_bytes()).hexdigest()
    row.update(version_code=VERSION,version_name=RELEASE,locked_2103152_commit=BASE,device_test_required=True,native_engine_unchanged=True)
    p.write_text(json.dumps(row,indent=2)+'\n')
    run('bash','-e','-o','pipefail','-c','git -C kodi diff --binary -- xbmc > engine/native-after-2103153.patch; cmp engine/native-before.patch engine/native-after-2103153.patch')

def verify():
    apk=Path('candidate-2103153/Infinity-'+RELEASE+'.apk');base=Path('baseline/Infinity-Run40-Exact-Base.apk')
    with zipfile.ZipFile(base) as before,zipfile.ZipFile(apk) as after:
        native={n for n in before.namelist() if n.startswith('lib/') and not n.endswith('/')}
        assert native=={n for n in after.namelist() if n.startswith('lib/') and not n.endswith('/')}
        for n in native:assert before.read(n)==after.read(n),n
        dex=b''.join(after.read(n) for n in after.namelist() if n.startswith('classes') and n.endswith('.dex'))
        for token in [b'cobra_persistent_live_shell',b'cobra_stable_multiview',b'cobra_video_first_player',b'cobra_themed_sheet',b'cobra-guide-v2.db',b'CONTROLS LOCKED']:
            assert token in dex,token
    report={'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'version_code':VERSION,'version_name':RELEASE,'native_libraries_verified':len(native),'native_libraries_unchanged':True,'locked_parent_commit':BASE,'device_playback_tested':False,'provider_epg_tested':False}
    Path('candidate-2103153/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    Path('candidate-2103153/SHA256SUMS').write_text(report['apk_sha256']+'  '+apk.name+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['reconstruct','promote','verify']);args=parser.parse_args();globals()[args.action]()
