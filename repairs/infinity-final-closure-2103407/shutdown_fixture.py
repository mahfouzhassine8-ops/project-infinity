"""Exact physical Compat82 in a disposable CI profile, never a production repair."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/'repairs/android-checkpoint-shutdown/installed'
ADDON='service.infinity.compat'
FILES={
 'addon.xml':('parent','6105af7bbb1d179f32326c82c323c9b2a6d2f7935b4f82f91f06614041bb3720'),
 'runtime_service.py':('overlay','657d75dee8f04d5cbdb1307893eed55efe05f32a1cefc0fa11c5213395080dca'),
 'checkpoint_runtime.py':('overlay','eb07f7cac8e773b5edc770d853618ca12a21c6279224fcfb04e23801c90077be'),
 'compat_runtime.py':('parent','f70cc391f88a4ccad1327c7bea36378e5a615549da0ca31fc077347decff4878'),
 'layout_service.py':('parent','227cf88d71febf61fe46b5dce5d8c131a31f0bfa11bc66d1bd4b02176582abdf'),
 'theme_contract.py':('parent','93320b9c0bfdb3ea87b1d76d2aae1a39bef715015977326a74740f3490410735'),
}


def source_bytes(root=ROOT):
    result={}
    for name,(location,wanted) in FILES.items():
        path=Path(root)/location/ADDON/name
        if path.is_symlink() or not path.is_file():raise ValueError('Missing or linked physical Compat source: '+name)
        value=path.read_bytes()
        if hashlib.sha256(value).hexdigest()!=wanted:raise ValueError('Physical Compat source differs: '+name)
        result[name]=value
    return result


def stage(folder,args,report,device,aid,root=ROOT):
    # Invoked only before the original fresh-only runner pushes its fixture.
    import android17_candidate_probe as candidate
    candidate.require_disposable(device)
    if args.case!='final-participant' or aid!='service.future.persistence.7fa29':raise ValueError('Independent participant fixture only')
    if Path(folder).resolve()!=args.out.resolve()/'fixture':raise ValueError('Unexpected disposable stage')
    target=Path(folder)/ADDON
    if target.exists() or target.is_symlink():raise ValueError('Existing Compat stage refused')
    values=source_bytes(root);target.mkdir()
    for name,value in values.items():(target/name).write_bytes(value)
    report['independent_compat_fixture']=dict(version='0.8.2',files={k:v[1] for k,v in FILES.items()},
        basis='actual physical manifest/runtime and exact retained native six-file contract',production_APK_changed=False)


def enable(device,out):
    details=device.rpc('Addons.GetAddonDetails',{'addonid':ADDON,'properties':['version','enabled']})['addon']
    if details.get('version')!='0.8.2':raise RuntimeError('Physical Compat fixture not discovered')
    if not details.get('enabled'):
        if device.rpc('Addons.SetAddonEnabled',{'addonid':ADDON,'enabled':True})!='OK':raise RuntimeError('Could not enable actual Compat service')
    (Path(out)/'COMPAT-FIXTURE-ENABLE.json').write_text(json.dumps(dict(addon=ADDON,version='0.8.2',normal_Kodi_API=True))+'\n')
