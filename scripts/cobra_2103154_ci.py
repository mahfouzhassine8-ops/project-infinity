#!/usr/bin/env python3
"""Build 2103154 from exact 2103153, retaining independent rollback/native gates."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
BASE='06f7dffa4b23af03030042bc057cfe1a8b672189'
VERSION=2103154
RELEASE='1.0.9-Cobra-Adaptive-View-Identities'
APK153='dff23c9488ff38790ad116fe6fa0d93f68c7a788e4b78fcffc88a38e247088b6'
JAVA=Path('kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
def run(*args):subprocess.run(args,check=True)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git_file(path):return subprocess.check_output(['git','show',BASE+':'+path])
def reconstruct():
    import yaml
    workflow=yaml.safe_load(git_file('.github/workflows/infinity-cobra-2103153-audited-build.yml'))
    # Previous deltas are sourced from an immutable commit, not mutable new work.
    delta=Path('refinement-delta')
    for base in ('patches/cobra-2103153','tests/cobra_2103153'):
        for file in (delta/base).rglob('*'):
            if file.is_file():assert file.read_bytes()==git_file(str(file.relative_to(delta))),file
    old='scripts/infinity_cobra_2103153_refinement.py';assert (delta/old).read_bytes()==git_file(old)
    names=('Verify both exact APK baselines','Reconstruct exact protected RC3 and 2103152 presentation','Apply integrated refinement and execute final production algorithms')
    done=[]
    for step in workflow['jobs']['android-update']['steps']:
        if step.get('name') in names:
            print('::group::'+step['name'],flush=True)
            run('bash','-e','-o','pipefail','-c',step['run']);done.append(step['name']);print('::endgroup::',flush=True)
    assert tuple(done)==names
    assert sha(JAVA)=='00d8984b7979db9400fd2e0799ae3736b3cb579953c6a847fd3d193ab1fa6872'
    oldapk=Path('rollback2103153/background-candidate/Infinity-1.0.9-Cobra-Guide-Player-Refinement.apk');assert sha(oldapk)==APK153
    backup=Path('rollback-package');backup.mkdir(exist_ok=True);shutil.copy2(oldapk,backup/'Infinity-Cobra-2103153.apk');shutil.copy2(JAVA,backup/'2103153-generated-activity.java.in')
    shutil.copy2('rollback2103153/ui-package/Infinity-Cobra-UI-1.3.8.zip',backup/'Infinity-Cobra-UI-1.3.8.zip')
    with (backup/'2103153-exact-repository.zip').open('wb') as out:subprocess.run(['git','archive','--format=zip',BASE],check=True,stdout=out)
    (backup/'README.txt').write_text('Exact pre-change 2103153 APK, matching UI, generated Activity and repository source.\nDevice settings/userdata are not backed up here. Do not uninstall or clear data to downgrade without a separate device-data backup.\n')
    (backup/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(backup.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
def apply():
    delta=Path('refinement-delta')
    for path in ('patches/cobra-2103154','tests/cobra_2103154'):shutil.copytree(delta/path,path,dirs_exist_ok=True)
    shutil.copy2(delta/'scripts/infinity_cobra_2103154_modes.py','scripts/')
    run('python3','scripts/infinity_cobra_2103154_modes.py','--source','kodi','--receipt','preflight/2103154-refinement.json')
    run('python3','tests/cobra_2103153/test_refinement.py','--before','preflight/2103152-exact-java-rollback.java.in','--after',str(JAVA),'--out','preflight/inherited-regressions')
    run('python3','tests/cobra_2103154/test_modes.py','--before','preflight/2103153-exact.java.in','--after',str(JAVA),'--out','preflight/mode-regressions')
    shutil.copy2(JAVA,'preflight/2103154-final.java.in')
    with open('engine/native-after-2103154.patch','w') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    assert Path('engine/native-before.patch').read_bytes()==Path('engine/native-after-2103154.patch').read_bytes()
def promote():
    gradle=Path('kodi/tools/android/packaging/xbmc/build.gradle.in');s=gradle.read_text();assert s.count('versionCode 2103138')==1
    s=s.replace('versionCode 2103138',f'versionCode {VERSION}',1).replace('versionName "1.0.9-Infinity-Lifecycle-Repair-RC3"',f'versionName "{RELEASE}"',1);gradle.write_text(s)
    receipt=Path('engine/background-resume-source.json');r=json.loads(receipt.read_text())
    for name in ('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in','tools/android/packaging/xbmc/src/Splash.java.in','tools/android/packaging/xbmc/build.gradle.in'):
        if name in r['files']:r['files'][name]['after']=sha(Path('kodi')/name)
    r.update(version_code=VERSION,version_name=RELEASE,locked_parent=2103153,cobra_ui_runtime=3,native_engine_unchanged=True,device_playback_verified=False)
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    p=Path('scripts/infinity_background_resume.py');s=p.read_text();assert s.count('VERSION_CODE = 2103138')==1;assert s.count("RELEASE = '1.0.9-Infinity-Lifecycle-Repair-RC3'")==1;p.write_text(s.replace('VERSION_CODE = 2103138',f'VERSION_CODE = {VERSION}',1).replace("RELEASE = '1.0.9-Infinity-Lifecycle-Repair-RC3'",f"RELEASE = '{RELEASE}'",1))
    p=Path('scripts/package_background_resume.py');s=p.read_text();assert 'Infinity-1.0.9-Infinity-Lifecycle-Repair-RC3' in s;p.write_text(s.replace('Infinity-1.0.9-Infinity-Lifecycle-Repair-RC3','Infinity-'+RELEASE))
    root=Path('addons/script.infinity.cobra.theme')
    with zipfile.ZipFile('rollback2103153/ui-package/Infinity-Cobra-UI-1.3.8.zip') as z:
        for name in ('addon.xml','resources/cobra-ui.json','resources/cobra-theme.json'):(root/name).write_bytes(z.read('script.infinity.cobra.theme/'+name))
    ui=json.loads((root/'resources/cobra-ui.json').read_text());ui['version']='1.3.9';ui['runtime']['minimum_build']=VERSION
    ui['views']['available']=['mobile','tv_guide'];ui['views']['tv_guide']['view_modes']={'grid':'broadcast_duration_timeline_all_orientations','compact':'dense_channel_directory','cards':'responsive_channel_identity_wall','focus':'watch_first_channel_or_schedule_queue'}
    ui['views']['mobile'].update(bottom_navigation=True,renderer='touch_dashboard',all_modes_reachable=True)
    ui['presentation'].update(adaptive_mode_layouts=True,mode_selector='illustrated_five_mode_sheet',tv_grid='slim_navigation_group_rail_fixed_channel_timeline')
    (root/'resources/cobra-ui.json').write_text(json.dumps(ui,indent=2)+'\n');addon=ET.parse(root/'addon.xml');addon.getroot().set('version','1.3.9');addon.write(root/'addon.xml',encoding='utf-8',xml_declaration=True)
    Path('preflight/rollback-pointer.json').write_text(json.dumps({'build':2103153,'commit':BASE,'run':35176733529,'artifact':10478399925,'apk_sha256':APK153,'device_userdata_backed_up':False},indent=2)+'\n')
def verify_apk():
    apk=Path('background-candidate/Infinity-'+RELEASE+'.apk')
    with zipfile.ZipFile(apk) as out:
        for baseline in ('background-rollback/Infinity-Run40-Exact-Base.apk','rollback2103153/background-candidate/Infinity-1.0.9-Cobra-Guide-Player-Refinement.apk'):
            with zipfile.ZipFile(baseline) as old:
                libs={n for n in old.namelist() if n.startswith('lib/') and not n.endswith('/')};assert libs
                assert libs=={n for n in out.namelist() if n.startswith('lib/') and not n.endswith('/')}
                for name in libs:assert old.read(name)==out.read(name),name
        dex=b''.join(out.read(n) for n in out.namelist() if n.startswith('classes') and n.endswith('.dex'))
        for token in (b'CobraModeLayout',b'CobraBroadcastRow',b'CobraMobileChannelRow',b'CobraCompactChannelRow',b'CobraPosterChannelCard',b'CobraFocusQueueRow',b'cobra_player_channel_drawer',b'Unlock controls'):assert token in dex,token
        assert b'CobraModesUiTest' not in dex
    report={'build':VERSION,'apk_sha256':sha(apk),'native_libraries_byte_identical_to_2103153':len(libs),'device_verified':False}
    Path('preflight/apk-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: exact protected native bytes retained; five renderers in release DEX')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['reconstruct','apply','promote','verify']);a=p.parse_args();{'reconstruct':reconstruct,'apply':apply,'promote':promote,'verify':verify_apk}[a.phase]()
