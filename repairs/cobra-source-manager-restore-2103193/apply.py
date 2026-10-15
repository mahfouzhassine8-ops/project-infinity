#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103192
BASE_NAME='1.0.9-Cobra-Provider-Pace-Guard-RC1'
BASE_COMMIT='6277ab3bf7bc9e65010af84d0e62534c3e75ce18'

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':
        return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=matches(text,name,kind)
    if len(ms)!=1: raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': block=True;i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103192 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103192 Activity preimage mismatch')
    text=before

    protected_methods=[
      'buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady',
      'cobraActivateLocalTimeshift','cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer',
      'cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup','showCobraDiagnosticExport',
      'cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged',
      'cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel',
      'showSources','showSourceActions','chooseSourceType','loadActiveSource','loadAllEnabledSources',
      'editCustomEpg','showProfiles'
    ]
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in [
      'CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy',
      'CobraTsParserPolicy','CobraTsTimelinePolicy','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy'
    ]}

    settings=member(text,'showSettings')
    settings=once(settings,
      '    Button filePicker = action("FILE PICKER  •  " + cobraFilePickerLabel());\n    filePicker.setTag("cobra_file_picker");\n    filePicker.setOnClickListener(v -> showCobraFilePickerPicker());',
      '''    Button filePicker = action("FILE PICKER  •  " + cobraFilePickerLabel());
    filePicker.setTag("cobra_file_picker");
    filePicker.setOnClickListener(v -> showCobraFilePickerPicker());

    Button tvSources = action("TV SOURCES");
    tvSources.setTag("cobra_tv_sources");
    tvSources.setOnClickListener(v -> showSources());''',
      'TV sources settings button')

    settings=once(settings,
      '    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));\n    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));',
      '    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));\n    list.addView(tvSources, new LinearLayout.LayoutParams(-1, dp(56)));\n    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));',
      'TV sources placement')
    text=replace_member(text,'showSettings',settings)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected source/playback owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected class changed: '+n)

    required=[
      'Button tvSources = action("TV SOURCES")','tvSources.setTag("cobra_tv_sources")',
      'tvSources.setOnClickListener(v -> showSources())','list.addView(tvSources',
      'private void showSources()','+  ADD TV SOURCE','showSourceActions(source)',
      'REFRESH CURRENT SOURCE','REFRESH ALL ENABLED SOURCES','PROFILES & PARENTAL CONTROLS',
      'timeshift_provider_pace_limited','REWRITE_ENABLED=false','DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',
      'cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text: raise RuntimeError('2103193 contract missing: '+token)

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,
      'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'source_manager_route_restored':True,'source_manager_existing_screen_reused':True,
      'source_manager_label':'TV SOURCES','source_manager_tag':'cobra_tv_sources',
      'show_sources_changed':False,'source_actions_changed':False,'source_loading_changed':False,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,
      'buffer_policy_changed':False,'parser_flags_changed':False,'clock_rewrite_changed':False,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103193 restores the existing TV Sources route in Settings over exact passed 2103192; source/provider/playback owners preserved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
