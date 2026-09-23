#!/usr/bin/env python3
"""2103229: exact-patch Multi-View stability + Fill Screen delta over locked 2103227."""
from __future__ import annotations
import argparse,base64,hashlib,json,re,subprocess,zlib
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
PATCH_ZLIB_B64='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'

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
    patch=zlib.decompress(base64.b64decode(PATCH_ZLIB_B64));subprocess.run(['patch','--dry-run','--batch','-p1'],cwd=shell,input=patch,check=True);subprocess.run(['patch','--batch','-p1'],cwd=shell,input=patch,check=True);req(sha(activity)==PATCHED_ACTIVITY,'Patched Activity hash mismatch')
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
