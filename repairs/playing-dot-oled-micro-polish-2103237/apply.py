#!/usr/bin/env python3
"""2103237: OLED micro-polish for the shared true-playing dot over locked 2103236.

Authorized delta only:
- 180 ms actual-channel handoff fade/bloom.
- Smooth Ambient accent and Night Cinema color morphing.
- Explicit OLED glow/core floor so the indicator never visually disappears.
- OLED-native emissive core + transparent micro-bloom rendering.
- Shared CobraPlayingDot only; all five existing placements inherit the treatment.
No playback/session ownership, buffering animation, layout placement, provider, timeshift,
Multi-View ownership, navigation, native engine, resource or theme redesign.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103237
OLD_VERSION=2103236
OLD_NAME='1.0.9-Cobra-All-Views-Playing-Indicator-RC1'
NEW_NAME='1.0.9-Cobra-Playing-Dot-OLED-Micro-Polish-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
ACT=SOURCE+'InfinityLiveActivity.java.in'
PARENT_ACTIVITY='0b1e50528f790dd6fdbc71a880eeffbd0c6c6bb13f9606ffacb8e7971f149dbf'
PATCHED_ACTIVITY='afa638f0f881c2d437fb5cad56c22453972a5900dcee18eac962537dba0bc255'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT_COMMIT='58371854afa059daea95a5cd5fe7492236d1459e'

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

def patch_activity(path:Path):
    before_b=path.read_bytes();req(hb(before_b)==PARENT_ACTIVITY,'Not exact locked 2103236 Activity preimage')
    s=before_b.decode()

    # Everything that determines playback truth, ownership, placement or player behavior is immutable here.
    protected_methods=[
      'buildPlayer','playChannel','cobraRestartLiveChannel','cobraRecoverUnexpectedLiveEnded',
      'cobraRecoverMultiTileSession','cobraRetryMultiTile','cobraFitBinding','cobraMultiSafeInsets',
      'onConfigurationChanged','cobraLayoutPlayerPanels','setMultiAudio','startCobraPreview',
      'promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'cobraPlayingIndicatorOwner','cobraChannelActuallyPlaying','cobraPlayingIndicatorColor',
      'cobraRefreshPlayingIndicators'
    ]
    protected_classes=[
      'CobraPlayerBinding','CobraVideoTile','CobraMultiRecoveryPolicy','CobraLiveEndedPolicy',
      'CobraAuditPolicy','CobraFoldAspectPolicy','CobraBroadcastRow','CobraMobileChannelRow',
      'CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow'
    ]
    mh={n:hb(member(s,n)) for n in protected_methods};ch={n:hb(member(s,n,'class')) for n in protected_classes}

    old_policy='''static final class CobraPlayingIndicatorPolicy {
    static final int CINEMA_AMBER=0xffffc247;
    static boolean active(boolean live,boolean requested,int suppression,int state,boolean error){
      return live&&requested&&!error&&suppression==Player.PLAYBACK_SUPPRESSION_REASON_NONE
          &&(state==Player.STATE_READY||state==Player.STATE_BUFFERING);
    }
    static int glowAlpha(int ambient,boolean cinema){
      if(cinema)return 58;
      return ambient==CobraPresentationEffects.IMMERSIVE?124:ambient==CobraPresentationEffects.SUBTLE?94:76;
    }
    static long pulsePeriodMs(boolean cinema){return cinema?1900L:1320L;}
  }'''
    new_policy='''static final class CobraPlayingIndicatorPolicy {
    static final int CINEMA_AMBER=0xffffc247;
    static final long HANDOFF_MS=180L;
    static final long COLOR_MORPH_MS=240L;
    static final int OLED_CORE_FLOOR_ALPHA=218;
    static final float OLED_GLOW_FLOOR=.58f;
    static boolean active(boolean live,boolean requested,int suppression,int state,boolean error){
      return live&&requested&&!error&&suppression==Player.PLAYBACK_SUPPRESSION_REASON_NONE
          &&(state==Player.STATE_READY||state==Player.STATE_BUFFERING);
    }
    static int glowAlpha(int ambient,boolean cinema){
      if(cinema)return 58;
      return ambient==CobraPresentationEffects.IMMERSIVE?124:ambient==CobraPresentationEffects.SUBTLE?94:76;
    }
    static long pulsePeriodMs(boolean cinema){return cinema?1900L:1320L;}
    static float unit(float value){return Math.max(0f,Math.min(1f,value));}
    static float smooth(float value){float t=unit(value);return t*t*(3f-2f*t);}
    static float handoffAlpha(boolean entering,long elapsedMs){
      float t=smooth(elapsedMs/(float)HANDOFF_MS);return entering?.42f+.58f*t:1f-t;
    }
    static int oledCoreAlpha(float wave){return Math.round(OLED_CORE_FLOOR_ALPHA+(255-OLED_CORE_FLOOR_ALPHA)*unit(wave));}
    static float oledGlowFactor(float wave){return OLED_GLOW_FLOOR+(1f-OLED_GLOW_FLOOR)*unit(wave);}
    static int blendColor(int from,int to,float amount){
      float t=smooth(amount);return Color.argb(
          Math.round(Color.alpha(from)+(Color.alpha(to)-Color.alpha(from))*t),
          Math.round(Color.red(from)+(Color.red(to)-Color.red(from))*t),
          Math.round(Color.green(from)+(Color.green(to)-Color.green(from))*t),
          Math.round(Color.blue(from)+(Color.blue(to)-Color.blue(from))*t));
    }
  }'''
    s=once(s,old_policy,new_policy,'OLED playing-indicator policy')

    old_dot='''private final class CobraPlayingDot extends View{
    final android.graphics.Paint dotPaint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    Channel channel;boolean active;
    CobraPlayingDot(){super(InfinityLiveActivity.this);setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);setVisibility(View.INVISIBLE);}
    void bind(Channel value){channel=value;sync();}
    void sync(){boolean next=cobraChannelActuallyPlaying(channel);if(next!=active){active=next;setVisibility(active?View.VISIBLE:View.INVISIBLE);}if(active)invalidate();}
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();sync();}
    @Override protected void onDraw(android.graphics.Canvas canvas){
      if(!active)return;boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
      int ambient=mPrefs==null?CobraPresentationEffects.OFF:CobraPresentationEffects.ambientMode(mPrefs);
      long period=CobraPlayingIndicatorPolicy.pulsePeriodMs(cinema),now=android.os.SystemClock.uptimeMillis();
      float wave=.5f+.5f*(float)Math.sin((now%period)*Math.PI*2d/period);
      int color=cobraPlayingIndicatorColor(),cx=getWidth()/2,cy=getHeight()/2;
      float core=dp(3),glow=dp(cinema?5:(ambient==CobraPresentationEffects.IMMERSIVE?7:6));
      dotPaint.setColor(Color.argb(Math.round(CobraPlayingIndicatorPolicy.glowAlpha(ambient,cinema)*(.58f+.42f*wave)),Color.red(color),Color.green(color),Color.blue(color)));
      canvas.drawCircle(cx,cy,glow*(.78f+.22f*wave),dotPaint);
      dotPaint.setColor(color);canvas.drawCircle(cx,cy,core,dotPaint);
      dotPaint.setColor(Color.argb(cinema?110:155,255,255,255));canvas.drawCircle(cx-core*.28f,cy-core*.28f,Math.max(1f,core*.22f),dotPaint);
      postInvalidateOnAnimation();
    }
  }'''
    new_dot='''private final class CobraPlayingDot extends View{
    final android.graphics.Paint dotPaint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    Channel channel;boolean active,visualActive,colorReady;int handoffDirection,colorFrom,colorTo;long handoffStarted,colorStarted;
    CobraPlayingDot(){super(InfinityLiveActivity.this);setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);setVisibility(View.INVISIBLE);}
    void bind(Channel value){
      boolean same=channel!=null&&value!=null&&java.util.Objects.equals(channel.id,value.id);
      if(!same){active=false;visualActive=false;handoffDirection=0;colorReady=false;setVisibility(View.INVISIBLE);}
      channel=value;sync(same);
    }
    void sync(){sync(true);}
    void sync(boolean animateHandoff){
      boolean next=cobraChannelActuallyPlaying(channel);if(next==active){if(active||visualActive)invalidate();return;}
      long now=android.os.SystemClock.uptimeMillis();
      if(next){active=true;visualActive=true;handoffDirection=animateHandoff?1:0;handoffStarted=now;setVisibility(View.VISIBLE);invalidate();return;}
      active=false;CobraPlayerBinding owner=cobraPlayingIndicatorOwner();
      boolean replacement=animateHandoff&&owner!=null&&owner.channel!=null&&channel!=null&&!java.util.Objects.equals(channel.id,owner.channel.id);
      if(replacement){visualActive=true;handoffDirection=-1;handoffStarted=now;setVisibility(View.VISIBLE);invalidate();}
      else{visualActive=false;handoffDirection=0;setVisibility(View.INVISIBLE);}
    }
    int renderedColor(long now){
      int target=cobraPlayingIndicatorColor();
      if(!colorReady){colorReady=true;colorFrom=target;colorTo=target;colorStarted=now;return target;}
      if(target!=colorTo){int current=interpolatedColor(now);colorFrom=current;colorTo=target;colorStarted=now;}
      return interpolatedColor(now);
    }
    int interpolatedColor(long now){
      if(colorFrom==colorTo)return colorTo;float t=(now-colorStarted)/(float)CobraPlayingIndicatorPolicy.COLOR_MORPH_MS;
      if(t>=1f){colorFrom=colorTo;return colorTo;}return CobraPlayingIndicatorPolicy.blendColor(colorFrom,colorTo,t);
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();sync(false);}
    @Override protected void onDraw(android.graphics.Canvas canvas){
      if(!active&&!visualActive)return;boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
      int ambient=mPrefs==null?CobraPresentationEffects.OFF:CobraPresentationEffects.ambientMode(mPrefs);
      long period=CobraPlayingIndicatorPolicy.pulsePeriodMs(cinema),now=android.os.SystemClock.uptimeMillis();
      float wave=.5f+.5f*(float)Math.sin((now%period)*Math.PI*2d/period),handoff=1f;
      if(handoffDirection!=0){long elapsed=Math.max(0L,now-handoffStarted);if(elapsed>=CobraPlayingIndicatorPolicy.HANDOFF_MS){if(handoffDirection<0){handoffDirection=0;visualActive=false;setVisibility(View.INVISIBLE);return;}handoffDirection=0;}else handoff=CobraPlayingIndicatorPolicy.handoffAlpha(handoffDirection>0,elapsed);}
      int color=renderedColor(now),cx=getWidth()/2,cy=getHeight()/2;
      float core=dp(3),glow=dp(cinema?5:(ambient==CobraPresentationEffects.IMMERSIVE?7:6)),pulse=CobraPlayingIndicatorPolicy.oledGlowFactor(wave);
      int glowAlpha=CobraPlayingIndicatorPolicy.glowAlpha(ambient,cinema);
      int outerAlpha=Math.round(glowAlpha*.30f*pulse*handoff),innerAlpha=Math.round(glowAlpha*pulse*handoff),coreAlpha=Math.round(CobraPlayingIndicatorPolicy.oledCoreAlpha(wave)*handoff);
      dotPaint.setColor(Color.argb(outerAlpha,Color.red(color),Color.green(color),Color.blue(color)));canvas.drawCircle(cx,cy,glow*(1.12f+.06f*wave),dotPaint);
      dotPaint.setColor(Color.argb(innerAlpha,Color.red(color),Color.green(color),Color.blue(color)));canvas.drawCircle(cx,cy,glow*(.76f+.20f*wave),dotPaint);
      dotPaint.setColor(Color.argb(coreAlpha,Color.red(color),Color.green(color),Color.blue(color)));canvas.drawCircle(cx,cy,core,dotPaint);
      int hot=Math.round((cinema?92:132)*handoff);dotPaint.setColor(Color.argb(hot,255,255,255));canvas.drawCircle(cx,cy,Math.max(1f,core*.24f),dotPaint);
      postInvalidateOnAnimation();
    }
  }'''
    s=once(s,old_dot,new_dot,'shared OLED playing-dot renderer')

    # Preservation proof: only the authorized shared renderer/policy may differ.
    for n,d in mh.items():req(hb(member(s,n))==d,'Protected playback/placement method changed: '+n)
    for n,d in ch.items():req(hb(member(s,n,'class'))==d,'Protected playback/placement class changed: '+n)

    path.write_text(s);req(sha(path)==PATCHED_ACTIVITY,'Unexpected 2103237 Activity postimage')
    return {'activity_before_sha256':hb(before_b),'activity_after_sha256':sha(path),
            'protected_methods_sha256':mh,'protected_classes_sha256':ch}

def patch_identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift');pack.write_text(p.replace(old,new))

def main():
    q=argparse.ArgumentParser();q.add_argument('--shell',type=Path,required=True);a=q.parse_args();shell=a.shell
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103236 generated source')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native receipt drift')
    activity=shell/ACT;frozen={str(p.relative_to(shell)):sha(p) for p in sorted(shell.rglob('*')) if p.is_file()}
    scope=patch_activity(activity);patch_identity(shell)
    changed=[n for n,d in frozen.items() if sha(shell/n)!=d]
    req(set(changed)=={ACT,'tools/android/packaging/xbmc/build.gradle.in'},'Unexpected generated source changes: '+str(changed))
    for n in changed:receipt['files'][n]['after']=sha(shell/n)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,native_engine_rebuilt=False,
      native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
      true_live_playing_indicator=True,playing_indicator_actual_session_owned=True,
      playing_indicator_focus_independent=True,playing_indicator_all_live_views=True,
      playing_indicator_tv_grid_preserved=True,playing_indicator_mobile=True,
      playing_indicator_compact=True,playing_indicator_cards=True,playing_indicator_focus=True,
      playing_indicator_ambient_adaptive=True,playing_indicator_night_cinema_adaptive=True,
      playing_indicator_night_cinema_amber='0xffffc247',
      playing_indicator_handoff_ms=180,playing_indicator_color_morph_ms=240,
      playing_indicator_oled_core_floor_alpha=218,playing_indicator_oled_glow_floor=.58,
      playing_indicator_oled_native_rendering=True,playing_indicator_playback_mutation=False,
      buffering_animation_untouched=True,view_placement_untouched=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for n,row in receipt['files'].items():req(sha(shell/n)==row['after'],'Receipt drift '+n)
    out=Path('audit237');out.mkdir(exist_ok=True)
    scope.update(
      build=VERSION,parent=OLD_VERSION,parent_commit=PARENT_COMMIT,changed_files=changed,
      native_engine_sha256=NATIVE,native_engine_rebuilt=False,
      authorized_delta='Shared playing-dot micro-polish only: handoff + color morph + OLED glow floor/rendering',
      inherited_views=['TV Grid','Mobile','Compact','Cards','Focus'],
      buffering_animation_untouched=True,view_placement_untouched=True,
      physical_device_verified=False,status='TEST CANDIDATE'
    )
    (out/'scope.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103237 OLED playing-dot micro-polish applied over exact locked 2103236 source')
if __name__=='__main__':main()
