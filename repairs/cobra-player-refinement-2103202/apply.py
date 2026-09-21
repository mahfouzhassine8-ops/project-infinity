from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,zipfile
ROOT=Path(__file__).resolve().parent
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PROTECTED_CLASSES=('CobraLayoutMath','CobraModeLayout','CobraLocalTimeshiftSession','CobraTimeshiftTransportPolicy','CobraTsParserPolicy','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy','CobraNetworkFamilyPolicy','CobraCallAudioPolicy','CobraWindowLifecyclePolicy','CobraTimeshiftRecoveryPolicy','CobraTimeshiftStallPolicy','CobraPreferencePolicy','CobraPlaybackPolicy')
PROTECTED_METHODS=('buildPlayer','cobraActivateLocalTimeshift','cobraRecoverLocalTimeshiftSource','cobraFallbackFromLocalTimeshift','cobraAttachVideo','cobraFitCaptions','cobraFitVideo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise RuntimeError(message)
def apply(source,receipt,out):
    reviewed=json.loads((ROOT/'reviewed.json').read_text());data=json.loads(receipt.read_text());expected=json.loads((ROOT/'parent-source-hashes.json').read_text())
    require(data['version_code']==2103201,'Wrong parent version')
    require({n:r['after'] for n,r in data['files'].items()}==expected,'Wrong parent receipt')
    for name,digest in expected.items():require(sha(source/name)==digest,'Parent input drift: '+name)
    require(sha(source/ACTIVITY)==reviewed['parent_activity_sha256'],'Wrong Activity parent')
    require(sha(ROOT/'activity.patch')==reviewed['patch_sha256'],'Patch changed after review')
    before=(source/ACTIVITY).read_text();out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(out/'pre-change-android-source.zip','x',zipfile.ZIP_DEFLATED) as z:
        for folder in ['tools/android/packaging','media']:
            for p in sorted((source/folder).rglob('*')):
                if p.is_file():z.write(p,str(p.relative_to(source)))
        z.write(source/'cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
    subprocess.run(['git','-C',str(source),'apply','--check',str(ROOT/'activity.patch')],check=True)
    subprocess.run(['git','-C',str(source),'apply',str(ROOT/'activity.patch')],check=True)
    require(sha(source/ACTIVITY)==reviewed['activity_sha256'],'Unexpected patched source')
    for name,digest in expected.items():
        if name!=ACTIVITY:require(sha(source/name)==digest,'Unrelated input changed: '+name)
    spec=importlib.util.spec_from_file_location('member_parser',ROOT.parent/'cobra-original-player-menu-2103197/apply.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    after=(source/ACTIVITY).read_text();preserved={}
    for kind,names in [('class',PROTECTED_CLASSES),('method',PROTECTED_METHODS)]:
        for name in names:
            a=m.member(before,name,kind) if kind=='class' else m.member(before,name)
            b=m.member(after,name,kind) if kind=='class' else m.member(after,name)
            require(a==b,'Protected runtime owner changed: '+name);preserved[name]=hashlib.sha256(a.encode()).hexdigest()
    result={'parent_build':2103201,'files':{ACTIVITY:{'before':reviewed['parent_activity_sha256'],'after':reviewed['activity_sha256']}},'protected_runtime_members':preserved,'native_engine_recompiled':False,'timeshift_transport_architecture_changed':False,'user_requested_controls':True,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: exact parent delta; protected runtime owners unchanged')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source.resolve(),a.receipt,a.out)
