#!/usr/bin/env python3
"""Restore the locked Cobra 2103237 true-playing OLED dot onto locked 2103266.

Authorized functional delta only:
- restore actual-session owned playing dot to TV Grid, Mobile, Compact, Cards, Focus;
- restore 180 ms handoff, 240 ms color morph, OLED floor, Night Cinema amber;
- refresh it from the existing programme refresh path.

Everything else in 2103266 is preserved, including Ambient/Glass/Cinema, Pro, LIVE styling,
removed full-screen hold menu, playback/provider/timeshift/Multi-View/lifecycle/native engine.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

VERSION=2103267
RELEASE='1.0.9-Cobra-Playing-Dot-Restore-RC1'
PARENT_VERSION=2103266
PARENT_RELEASE='1.0.9-Ambient-Glass-Cinema-RC1'
PARENT_COMMIT='490e995e77ad1d37c5b64fd11315e6f4a704952c'
PARENT_RUN=36675691445
PARENT_APK_SHA256='4624c1ca66d29a4ac8c5f63892ca9669e6ef757894fe6a2e0b4c4d356e3ec455'
NATIVE_SHA256='c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'
PARENT_ACTIVITY_SHA256='1c98cc47233a9a9535a7c2d46aee6933e994f67064f18227505ee1b2860bb790'
REFERENCE237_ACTIVITY_SHA256='afa638f0f881c2d437fb5cad56c22453972a5900dcee18eac962537dba0bc255'
ACT=Path('shell-kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
GRADLE=Path('shell-kodi/tools/android/packaging/xbmc/build.gradle.in')
RUNTIME=Path('scripts/infinity_background_resume.py')
PACKAGER=Path('scripts/package_background_resume.py')
RECEIPT=Path('engine/background-resume-source.json')
EXPECTED={
 ACT:'1c98cc47233a9a9535a7c2d46aee6933e994f67064f18227505ee1b2860bb790',
 GRADLE:'0c4c5315e940afef394fb6f97aa35fcf28f9dc69268bbf02c61ed4302b08aff6',
 RUNTIME:'1d13c5144fac586e59507efd5d9df3fa754f23b6a4472f9a4e78a386c55a0f90',
 PACKAGER:'28974e9f2c055d631ae876bfefa8c5e69aa8860bc9ff9fce78a5b970f2a92f8e',
 RECEIPT:'c27d6feeae5633b532af13d2737e3a99026fe88b1222f3acce9b03f3873290d0',
}
CLASS_PREIMAGE={
 'CobraBroadcastRow':'462d734fc2ed499058189a27eeabe05b81c5ec140e8adca0e824334bac220cc3',
 'CobraMobileChannelRow':'31c45f74b6b604b4104ce18d20b65e18f602d1cbb94c150421830bae69df2a71',
 'CobraCompactChannelRow':'f9d41e5c080fa40c2da122ea9c735aecda9430d781b36dc30c55d251897e0c19',
 'CobraPosterChannelCard':'4476f018c9da72cf33ecd88e0c7e6c56f23cae2f518f1d8060dc6e55b70e169d',
 'CobraFocusQueueRow':'9a91ab97656b5106bde7761db2da5d572b18db83d6ae8f374b00e3138c3ba1ef',
}
CLASS_TARGET={
 'CobraBroadcastRow':'299cc7f5fbb069771900fbff77a2e95976605256f51730325bb27b4ec9c22cda',
 'CobraMobileChannelRow':'61dc24c65d793193bad19fc2abadc6a56071caf796af7df8eae5b4607f2926e0',
 'CobraCompactChannelRow':'b019fdbb76fa17f21c78e374f7d105851339e5299d6774592db210b3dc8bfc60',
 'CobraPosterChannelCard':'445b224068945ae148ab0e68973af8dd1d6df9e600fd371de35100f30970f0f2',
 'CobraFocusQueueRow':'df771b9a7e1f1a95f8ca492523a7f39466c4f812b760aab48700451a94b01cc4',
}
HELPERS_SHA='350ef39694fdbb32c59a0cd63a43ad681331a92bffd4f2e5f6239688f0c82db6'

def h(data:bytes|str)->str:
    if isinstance(data,str): data=data.encode()
    return hashlib.sha256(data).hexdigest()

def req(v,m):
    if not v: raise RuntimeError(m)

def once(s,a,b,label):
    c=s.count(a); req(c==1,f'{label}: expected one anchor, got {c}'); return s.replace(a,b,1)

def member_span(text,name,kind='class'):
    if kind=='class':
        p=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    else:
        p=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    ms=list(p.finditer(text)); req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start(); i=text.index('{',ms[0].end()); d=0; q=None; esc=line=com=False
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif com:
            if c=='*' and n=='/': com=False; i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True; i+=1
        elif c=='/' and n=='*': com=True; i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0: return st,i+1,text[st:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)

def method(text,name):
    return member_span(text,name,'method')[2]

def class_block(text,name):
    return member_span(text,name,'class')[2]

def file_inventory(root:Path):
    return {str(p.relative_to(root)):h(p.read_bytes()) for p in root.rglob('*') if p.is_file()}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--evidence',type=Path,required=True); ap.add_argument('--reference237',type=Path,required=True)
    args=ap.parse_args(); root=args.root.resolve(); evidence=args.evidence.resolve(); reference237=args.reference237.resolve()
    req(not evidence.exists(),'Evidence output already exists')
    for rel,expected in EXPECTED.items():
        req(h((root/rel).read_bytes())==expected,'Wrong locked 2103266 preimage: '+str(rel))
    receipt=json.loads((root/RECEIPT).read_text())
    req(receipt.get('version_code')==PARENT_VERSION and receipt.get('version_name')==PARENT_RELEASE,'Wrong parent receipt identity')
    req(receipt.get('native_engine_sha256')==NATIVE_SHA256,'Native engine receipt drift')
    req(receipt.get('cobra_video_hold_opens_menu') is False,'No-hold device-passed repair not present in parent')

    before_shell=file_inventory(root/'shell-kodi')
    act=(root/ACT).read_text(); before_act=act
    req(h(act)==PARENT_ACTIVITY_SHA256,'Activity parent hash drift')
    req('mPlayerOverlay.setOnLongClickListener(v -> true);' in act,'No-hold callback missing before restore')
    for token in ('CobraPlayingIndicatorPolicy','CobraPlayingDot','cobraPlayingIndicatorOwner','cobraRefreshPlayingIndicators'):
        req(token not in act,'Playing-dot implementation unexpectedly already present: '+token)

    protected_methods=['buildPlayer','playChannel','cobraRestartLiveChannel','cobraRecoverUnexpectedLiveEnded','cobraRecoverMultiTileSession','cobraRetryMultiTile','cobraFitBinding','cobraMultiSafeInsets','onConfigurationChanged','cobraLayoutPlayerPanels','setMultiAudio','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen','cobraRefreshVisualEffects','cobraStartPresentationTicker','cobraBuildPlayerChrome']
    method_hash={}
    for name in protected_methods:
        try: method_hash[name]=h(method(act,name))
        except RuntimeError: pass
    protected_classes=['CobraPlayerBinding','CobraVideoTile','CobraMultiRecoveryPolicy','CobraLiveEndedPolicy','CobraAuditPolicy','CobraFoldAspectPolicy','CobraAmbientGlassDrawable']
    class_hash={}
    for name in protected_classes:
        try: class_hash[name]=h(class_block(act,name))
        except RuntimeError: pass

    reference=reference237.read_text(); req(h(reference)==REFERENCE237_ACTIVITY_SHA256,'Wrong locked 2103237 reference source')
    hs=reference.index('  static final class CobraPlayingIndicatorPolicy {'); he=reference.index('  private final class CobraBroadcastRow extends FrameLayout{',hs); helpers=reference[hs:he]
    req(h(helpers)==HELPERS_SHA,'Helper reference drift')
    marker='  private final class CobraBroadcastRow extends FrameLayout{'
    req(act.count(marker)==1,'Broadcast row marker drift')
    act=act.replace(marker,helpers+marker,1)

    programme_anchor='''    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}\n    cobraRefreshModeDetails();'''
    programme_new='''    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}\n    cobraRefreshPlayingIndicators();\n    cobraRefreshModeDetails();'''
    act=once(act,programme_anchor,programme_new,'periodic playing indicator refresh')

    for name in CLASS_PREIMAGE:
        st,en,current=member_span(act,name,'class')
        req(h(current)==CLASS_PREIMAGE[name],f'{name} locked 2103266 preimage drift')
        target=class_block(reference,name)
        req(h(target)==CLASS_TARGET[name],f'{name} 2103237 target drift')
        act=act[:st]+target+act[en:]

    req('mPlayerOverlay.setOnLongClickListener(v -> true);' in act,'No-hold callback was lost')
    req('setText("PLAYING"' not in act,'Redundant PLAYING text was reintroduced')
    for name,digest in method_hash.items(): req(h(method(act,name))==digest,'Protected method changed: '+name)
    for name,digest in class_hash.items(): req(h(class_block(act,name))==digest,'Protected class changed: '+name)

    (root/ACT).write_text(act)
    g=(root/GRADLE).read_text(); g=once(g,'versionCode 2103266','versionCode 2103267','Gradle versionCode'); g=once(g,'versionName "'+PARENT_RELEASE+'"','versionName "'+RELEASE+'"','Gradle versionName'); (root/GRADLE).write_text(g)
    r=(root/RUNTIME).read_text()
    for a,b,label in [
        ('VERSION_CODE = 2103266','VERSION_CODE = 2103267','runtime version'),
        ("RELEASE = '"+PARENT_RELEASE+"'","RELEASE = '"+RELEASE+"'",'runtime release'),
        ("BASE_COMMIT = 'e650b9b0954029f4f9f168531313eabf5a7aeb68'","BASE_COMMIT = '"+PARENT_COMMIT+"'",'runtime parent commit'),
        ("BASE_APK_SHA256 = '6ae458dcc400c6259ac793f4d1fc26fc897aa592f6889febcd0fd084d860626c'","BASE_APK_SHA256 = '"+PARENT_APK_SHA256+"'",'runtime parent apk'),
    ]: r=once(r,a,b,label)
    (root/RUNTIME).write_text(r)
    p=(root/PACKAGER).read_text()
    p=once(p,"Infinity-2103266-Ambient-Glass-Cinema-RC1-unsigned.apk","Infinity-2103267-Cobra-Playing-Dot-Restore-RC1-unsigned.apk",'unsigned name')
    p=once(p,"Infinity-2103266-Ambient-Glass-Cinema-RC1.apk","Infinity-2103267-Cobra-Playing-Dot-Restore-RC1.apk",'final name')
    p=once(p,"'base_run':36671687282","'base_run':36675691445",'base run')
    p=once(p,"ROOT/'repairs/ambient-glass-2103266/DEVICE-TEST.txt'","ROOT/'repairs/cobra-playing-dot-restore-2103267/DEVICE-TEST.md'",'device test')
    p=once(p,"PASS: Recovery and fixed chooser TEST CANDIDATE; exact 2103259 native/assets/resources; permanent signer verified","PASS: Cobra playing-dot restore over exact locked 2103266; native/assets/resources preserved; permanent signer verified",'packager success text')
    (root/PACKAGER).write_text(p)

    after_shell=file_inventory(root/'shell-kodi')
    changed=sorted(n for n in set(before_shell)|set(after_shell) if before_shell.get(n)!=after_shell.get(n))
    allowed=['tools/android/packaging/xbmc/build.gradle.in','tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in']
    req(changed==allowed,'Unexpected Android shell source delta: '+repr(changed))

    for name in changed:
        req(name in receipt.get('files',{}),'Receipt has no hash slot for '+name)
        receipt['files'][name]['after']=after_shell[name]
    receipt.update(
        version_code=VERSION,version_name=RELEASE,source_parent=PARENT_VERSION,source_parent_commit=PARENT_COMMIT,source_parent_locked=True,
        base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK_SHA256,
        true_live_playing_indicator=True,playing_indicator_actual_session_owned=True,playing_indicator_focus_independent=True,
        playing_indicator_all_live_views=True,playing_indicator_tv_grid_preserved=True,playing_indicator_mobile=True,
        playing_indicator_compact=True,playing_indicator_cards=True,playing_indicator_focus=True,
        playing_indicator_ambient_adaptive=True,playing_indicator_night_cinema_adaptive=True,
        playing_indicator_night_cinema_amber='0xffffc247',playing_indicator_handoff_ms=180,
        playing_indicator_color_morph_ms=240,playing_indicator_oled_core_floor_alpha=218,
        playing_indicator_oled_glow_floor=.58,playing_indicator_oled_native_rendering=True,
        playing_indicator_playback_mutation=False,buffering_animation_untouched=True,view_placement_restored_from_locked_2103237=True,
        ambient_glass_2103266_preserved=True,cobra_video_hold_opens_menu=False,native_engine_recompiled=False,native_engine_unchanged=True,
        native_engine_sha256=NATIVE_SHA256,physical_device_verified=False,runtime_device_tested=False,candidate_locked=False)
    (root/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items(): req(h((root/'shell-kodi'/name).read_bytes())==row['after'],'Receipt drift: '+name)

    evidence.mkdir(parents=True)
    (evidence/'InfinityLiveActivity-2103266-before.java.in').write_text(before_act)
    (evidence/'InfinityLiveActivity-2103267-after.java.in').write_text(act)
    import difflib
    (evidence/'playing-dot-restore.patch').write_text(''.join(difflib.unified_diff(before_act.splitlines(True),act.splitlines(True),fromfile='2103266/InfinityLiveActivity.java.in',tofile='2103267/InfinityLiveActivity.java.in')))
    result={
      'version_code':VERSION,'version_name':RELEASE,'parent_version':PARENT_VERSION,'parent_commit':PARENT_COMMIT,
      'parent_apk_sha256':PARENT_APK_SHA256,'native_engine_sha256':NATIVE_SHA256,'native_recompiled':False,
      'parent_activity_sha256':PARENT_ACTIVITY_SHA256,'candidate_activity_sha256':h(act),
      'changed_shell_files':changed,'other_shell_files_byte_identical':len(before_shell)-len(changed),
      'restored_from_locked_reference':2103237,'views':['TV Grid','Mobile','Compact','Cards','Focus'],
      'actual_session_owned':True,'focus_independent':True,'handoff_ms':180,'color_morph_ms':240,
      'oled_core_floor_alpha':218,'oled_glow_floor':.58,'night_cinema_amber':'#FFC247',
      'no_hold_preserved':True,'ambient_glass_2103266_preserved':True,'buffering_animation_untouched':True,
      'device_verified':False,'status':'TEST CANDIDATE'}
    (evidence/'source-verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: restored locked Cobra playing-dot behavior over exact locked 2103266; only Activity + build identity changed')

if __name__=='__main__': main()
