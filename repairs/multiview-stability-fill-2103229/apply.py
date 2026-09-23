#!/usr/bin/env python3
"""2103229: exact-patch Multi-View stability + Fill Screen delta over locked 2103227."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess
from pathlib import Path

VERSION=2103229
OLD_VERSION=2103227
OLD_NAME='1.0.9-Cobra-Device-Live-Fold-MultiView-RC1'
NEW_NAME='1.0.9-Cobra-MultiView-Stability-Fill-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
ACT=SOURCE+'InfinityLiveActivity.java.in'
PARENT_ACTIVITY='d99ee556d5324e8f4467dde7a2fdf5ad7b9e29cbed6a44d3112a2e42199617c0'
PATCHED_ACTIVITY='4af3fc3775fe0711b932bb664385a705f0fc5080deba63b3b21de47986a9146e'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT_COMMIT='50fb6ed71243c61d6a5267e8477467989006087a'

PROTECTED_METHODS=[
  'buildPlayer','startSinglePlayer','cobraStartDirectSinglePlayer','cobraStartLocalTimeshift',
  'cobraRecoverLocalTimeshiftSource','cobraFallbackFromLocalTimeshift','cobraRewindLive','cobraGoLive',
  'playVodUrl','openSeries','cobraRenderMovieDetailPage','cobraRenderSeriesDetailPage',
  'loadXtream','loadM3u','multiToSingle','openMultiView','rebuildCobraMultiPreservingSessions',
  'cobraSyncMultiArrays','setMultiAudio','selectCobraMultiChannel','removeCobraMultiTileClean',
  'cobraAttachVideo','cobraDisposePlayer','applyCobraAspectTransform','cobraBindingAspect',
  'cobraChannelAspect','showSettings','cobraRecoverUnexpectedLiveEnded','cobraReattachObservedSurface',
  'cobraObserveSessions','cobraPrepareMultiForPip','cobraRestoreMultiAfterPip','cobraPromoteMultiTileFullscreen',
  'cobraReturnToMultiFromFullscreen'
]
PROTECTED_CLASSES=['CobraLayoutMath','CobraFoldAspectPolicy','CobraLiveEndedPolicy','CobraTimeshiftTransportPolicy','CobraWindowLifecyclePolicy']


def hb(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def sha(p):return hb(Path(p).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(s,a,b,label):
    c=s.count(a);req(c==1,f'{label}: expected one anchor, got {c}');return s.replace(a,b,1)
def span(text,name,kind='method'):
    if kind=='method':p=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:p=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}');st=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=com=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif com:
            if c=='*' and n=='/':com=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':com=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return st,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]

def patch_identity(shell):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text();r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version');r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME;req(p.count(old)==2,'packager identity drift');pack.write_text(p.replace(old,new));return gradle

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();shell=a.shell
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text());req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103227 reconstructed receipt');req(receipt.get('native_engine_sha256')==NATIVE,'Native receipt drift')
    activity=shell/ACT;req(sha(activity)==PARENT_ACTIVITY,'Not exact locked 2103227 Activity preimage');before=activity.read_text()
    protected_methods={n:hb(member(before,n)) for n in PROTECTED_METHODS};protected_classes={n:hb(member(before,n,'class')) for n in PROTECTED_CLASSES}
    frozen={k:sha(shell/v) for k,v in {'splash':SOURCE+'Splash.java.in','smart_return':SOURCE+'CobraSmartReturn.java.in','main':SOURCE+'Main.java.in','visual_renderer':SOURCE+'CobraVisualRenderer.java.in'}.items()}
    patch=b''.join(Path(__file__).with_name(f'activity.patch.{i:02d}').read_bytes() for i in range(4));subprocess.run(['patch','--dry-run','--batch','-p1'],cwd=shell,input=patch,check=True);subprocess.run(['patch','--batch','-p1'],cwd=shell,input=patch,check=True);req(sha(activity)==PATCHED_ACTIVITY,'Patched Activity hash mismatch')
    after=activity.read_text();
    for n,d in protected_methods.items():req(hb(member(after,n))==d,'Protected method changed: '+n)
    for n,d in protected_classes.items():req(hb(member(after,n,'class'))==d,'Protected class changed: '+n)
    gradle=patch_identity(shell)
    for k,v in {'splash':SOURCE+'Splash.java.in','smart_return':SOURCE+'CobraSmartReturn.java.in','main':SOURCE+'Main.java.in','visual_renderer':SOURCE+'CobraVisualRenderer.java.in'}.items():req(sha(shell/v)==frozen[k],'Frozen file changed: '+k)
    for name in (ACT,SOURCE+'Splash.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
    receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,multiview_stability_fill_audited=True,multiview_same_player_auto_recovery=True,multiview_auto_recovery_bounded=2,multiview_auto_recovery_idle=True,multiview_auto_recovery_error=True,multiview_auto_recovery_buffering_ms=18000,multiview_surface_recovery_preserved=True,multiview_live_ended_recovery_preserved=True,multiview_healthy_peers_untouched=True,multiview_auto_player_recreation=False,multiview_layout_fit_preserved=True,multiview_layout_fill_screen=True,multiview_fill_proportional=True,multiview_fill_minimum_center_crop=True,multiview_fill_safe_insets=True,multiview_fill_persistent=True,multiview_fill_player_recreated=False,multiview_fill_retune=False,multiview_fill_audio_interrupt=False,playback_core_unchanged=True,providers_unchanged=True,timeshift_core_unchanged=True,movie_tv_details_unchanged=True,drawer_owner_preserved=True,smart_return_preserved=True,choose_experience_ui_unchanged=True,health_center_unchanged=True,global_visual_renderer_unchanged=True)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\\n');
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Receipt drift '+name)
    scope={'build':VERSION,'parent':OLD_VERSION,'locked_source_parent':'locked-infinity-cobra-2103227-device-live-fold-multiview-passed','locked_parent_commit':PARENT_COMMIT,'preaudit_activity_sha256':PARENT_ACTIVITY,'activity_after_sha256':PATCHED_ACTIVITY,'authorized_delta':'Multi-View per-tile stability recovery + Fit/Fill Screen layout only','protected_methods_sha256':protected_methods,'protected_classes_sha256':protected_classes,'frozen_files_sha256':frozen,'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,'stability':{'automatic_same_player_only':True,'automatic_player_recreation':False,'max_reprepares_per_tile':2,'error_grace_ms':3000,'fallback_grace_ms':8000,'idle_grace_ms':6000,'buffer_stall_ms':18000,'recovery_cooldown_ms':20000,'stable_budget_reset_ms':60000,'surface_recovery_owner_preserved':True,'live_ended_owner_preserved':True,'timeshift_excluded':True,'healthy_peers_untouched':True},'layout':{'fit_preserved':True,'fill_screen':True,'persistent':True,'safe_insets':True,'proportional':True,'minimum_center_crop':True,'player_recreated':False,'retune':False,'audio_interrupted':False,'two_portrait_top_bottom':True,'two_landscape_side_by_side':True,'three_space_efficient':True,'four_edge_to_edge_2x2':True,'enlarge_reflows_peers':True},'physical_device_verified':False,'status':'TEST CANDIDATE'}
    Path('audit229').mkdir(exist_ok=True);Path('audit229/scope.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\\n');print('PASS: 2103229 exact Multi-View stability + Fill Screen patch applied over locked 2103227')
if __name__=='__main__':main()
