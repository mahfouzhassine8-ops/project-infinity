#!/usr/bin/env python3
"""Apply the reviewed player-only repairs to exact verified Cobra 2103200."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,zipfile

ROOT=Path(__file__).resolve().parent
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PREIMAGE='6d9dd616099b2e7f435c441445fd912af7b26e6d422632cd0d905c95486f0fbb'
MODULES=('apply_scrubber','apply_subtitles','apply_fold_motion','apply_menu')
PROTECTED_CLASSES=('CobraLayoutMath','CobraModeLayout','CobraLocalTimeshiftSession','CobraTimeshiftTransportPolicy','CobraTsParserPolicy','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy','CobraNetworkFamilyPolicy','CobraCallAudioPolicy','CobraWindowLifecyclePolicy','CobraTimeshiftRecoveryPolicy','CobraTimeshiftStallPolicy','CobraPreferencePolicy','CobraChannelPreferences','CobraPlaybackPolicy')
PROTECTED_METHODS=('buildPlayer','cobraActivateLocalTimeshift','cobraRecoverLocalTimeshiftSource','cobraFallbackFromLocalTimeshift','cobraStartProviderCatchup','cobraAttachVideo','cobraFitCaptions')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(value,message):
    if not value:raise RuntimeError(message)

def apply(source,receipt,out):
    data=json.loads(receipt.read_text())
    require(data['version_code']==2103200,'Requires verified 2103200')
    for name,row in data['files'].items():require(sha(source/name)==row['after'],'Parent receipt drift: '+name)
    require(sha(source/ACTIVITY)==PREIMAGE,'Wrong Activity parent')
    original=(source/ACTIVITY).read_text()
    transformed=original
    stages=[]
    for name in MODULES:
        path=ROOT/(name+'.py')
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        before=hashlib.sha256(transformed.encode()).hexdigest()
        transformed=module.transform(transformed)
        require(hashlib.sha256(transformed.encode()).hexdigest()!=before,'Empty repair transform: '+name)
        stages.append({'module':name,'recipe_sha256':sha(path),'before':before,'after':hashlib.sha256(transformed.encode()).hexdigest()})
    spec=importlib.util.spec_from_file_location('preserved_member_tools',ROOT.parent/'cobra-original-player-menu-2103197/apply.py')
    parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    preserved={}
    for kind,names in [('class',PROTECTED_CLASSES),('method',PROTECTED_METHODS)]:
        for name in names:
            old=parser.member(original,name,kind) if kind=='class' else parser.member(original,name)
            new=parser.member(transformed,name,kind) if kind=='class' else parser.member(transformed,name)
            require(old==new,'Protected runtime owner changed: '+name)
            preserved[name]=hashlib.sha256(new.encode()).hexdigest()
    # Produce the exact pre-change snapshot before writing runtime inputs.
    out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(out/'pre-change-android-source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for folder in ('tools/android/packaging','media'):
            for p in sorted((source/folder).rglob('*')):
                if p.is_file():z.write(p,str(p.relative_to(source)))
        z.write(source/'cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
    shutil.copy2(receipt,out/'pre-change-source-receipt.json')
    (source/ACTIVITY).write_text(transformed)
    for name,row in data['files'].items():
        if name!=ACTIVITY:require(sha(source/name)==row['after'],'Unrelated source changed: '+name)
    result={'parent_build':2103200,'files':{ACTIVITY:{'before':PREIMAGE,'after':sha(source/ACTIVITY)}},'stages':stages,'protected_runtime_members':preserved,'native_engine_recompiled':False,'timeshift_transport_architecture_changed':False,'new_controls':False,'duplicate_options_aspect_route_removed':True,'fold_fit_contract_changed':True,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: composed player repair; all other parent inputs preserved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
