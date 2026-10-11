"""Actual forward/rollback Java installers and real crash/failure filesystem peers."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import rollback_2103365 as r

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--json-jar',type=Path,required=True)
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location('installer_peers',r.R/'test_checkpoint_installer.py')
    f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    with tempfile.TemporaryDirectory(prefix='verified-green-rollback-') as tmp:
        tmp=Path(tmp);payloads=tmp/'payloads';r.assets_and_sources(a.baseline,payloads)
        with zipfile.ZipFile(a.baseline) as apk:
            for version,component,assetname,current in (
                (19,'InfinityCheckpointAddonInstaller','checkpoint-controller.zip',r.participant_asset.build()),
                (20,'InfinityCheckpointController20Installer','checkpoint-controller-20.zip',r.android_ci.installed_build.build('script.infinity.commandcenter'))):
                addon_xml=(r.R/('runtime/commandcenter/unchanged' if version==19 else 'installed/parent/script.infinity.commandcenter')/'addon.xml').read_bytes()
                with zipfile.ZipFile(__import__('io').BytesIO(apk.read('assets/infinity/'+assetname))) as old:
                    green={n[8:]:old.read(n) for n in old.namelist() if n.startswith('payload/')}
                with zipfile.ZipFile(__import__('io').BytesIO(current)) as new:
                    candidate={n[8:]:new.read(n) for n in new.namelist() if n.startswith('payload/')}
                reverse=(payloads/assetname).read_bytes()
                source=tmp/('src'+str(version));classes={}
                for relative,content in f.STUBS.items():
                    target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
                file=source/'com/projectinfinity/kodi/InfinityCheckpointAddonInstaller.java'
                for kind,path in [('forward',r.R/'runtime/android/overlay/tools/android/packaging/xbmc/src'/(component+'.java.in')),
                                  ('rollback',payloads/(component+'.java.in'))]:
                    code=path.read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi')
                    code=code.replace('InfinityCheckpointController20Installer','InfinityCheckpointAddonInstaller').replace('checkpoint-controller-20.zip','checkpoint-controller.zip').replace('infinity-infinitycheckpointcontroller20installer','infinity-checkpoint-code')
                    file.write_text(code);classes[kind]=tmp/('classes-'+str(version)+'-'+kind)
                    subprocess.run(['java','com.sun.tools.javac.Main','--release','8','-Xlint:all','-Werror','-cp',str(a.json_jar),'-d',str(classes[kind]),*[str(p) for p in source.rglob('*.java')]],check=True)
                def initialize(name,data,asset):
                    root=tmp/(str(version)+'-'+name);addon=root/'external/.kodi/addons/script.infinity.commandcenter';addon.mkdir(parents=True)
                    (root/'private').mkdir();assets=root/'assets/infinity';assets.mkdir(parents=True);(assets/'checkpoint-controller.zip').write_bytes(asset)
                    (addon/'addon.xml').write_bytes(addon_xml)
                    for n,b in data.items():(addon/n).write_bytes(b)
                    (addon/'unrelated.py').write_bytes(b'PRESERVED unrelated code\n')
                    user=root/'external/.kodi/userdata/addon_data/script.infinity.commandcenter';user.mkdir(parents=True);(user/'resume_hub.json').write_bytes(b'PRESERVED REAL USER STATE\n')
                    return root,addon
                def run(root,kind='rollback',mode='',expected=0):
                    result=subprocess.run(['java','-Dinfinity.test.mode='+mode,'-cp',str(classes[kind])+':'+str(a.json_jar),'com.projectinfinity.kodi.InstallerMain',str(root)],capture_output=True,text=True,timeout=10)
                    assert result.returncode==expected,(version,kind,mode,expected,result.stdout,result.stderr)
                def check(root,addon):
                    for n,b in green.items():assert (addon/n).read_bytes()==b,(version,n)
                    assert (addon/'addon.xml').read_bytes()==addon_xml
                    assert (addon/'unrelated.py').read_bytes()==b'PRESERVED unrelated code\n'
                    assert (root/'external/.kodi/userdata/addon_data/script.infinity.commandcenter/resume_hub.json').read_bytes()==b'PRESERVED REAL USER STATE\n'
                for mode,expected in [('',0),('fail',10),('crash',73)]:
                    root,addon=initialize('candidate-'+(mode or 'normal'),candidate,reverse);before=f.contents(root/'external')
                    run(root,mode=mode,expected=expected)
                    if mode=='fail':assert f.contents(root/'external')==before
                    if mode:run(root)
                    check(root,addon);run(root);check(root,addon)
                for phase in ('applying','committed','corrupt'):
                    root,addon=initialize('legacy-'+phase,green,current)
                    run(root,'forward',mode='crash',expected=73)
                    journal=root/'private/infinity-checkpoint-code-transaction/journal.json';row=json.loads(journal.read_text())
                    if phase=='committed':row['phase']='committed';journal.write_text(json.dumps(row))
                    if phase=='corrupt':row['asset_sha256']='0'*64;journal.write_text(json.dumps(row))
                    (root/'assets/infinity/checkpoint-controller.zip').write_bytes(reverse);before=f.contents(root/'external')
                    run(root,expected=10 if phase=='corrupt' else 0)
                    if phase=='corrupt':assert f.contents(root/'external')==before
                    else:check(root,addon)
                root,addon=initialize('unknown',candidate,reverse)
                (addon/'plugin.py').write_bytes(b'UNKNOWN USER CUSTOMIZATION\n');before=f.contents(root/'external');run(root,expected=10);assert f.contents(root/'external')==before
                root,addon=initialize('bad-asset',candidate,reverse+b'corrupt');before=f.contents(root/'external');run(root,expected=10);assert f.contents(root/'external')==before
                print('PASS CC'+str(version)+' actual reverse/forward pin matching, same-state preservation, hard-death/failed rollback, authentic forward journals, unknown edit and corrupt archive refusal')
if __name__=='__main__':main()
