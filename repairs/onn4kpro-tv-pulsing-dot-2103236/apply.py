#!/usr/bin/env python3
"""2103236 RC16 — lightweight mobile-matched pulsing playing dot for TV Grid.

Parent: exact locked 2103235 RC15.

Authorized delta only:
- Port the approved mobile playing-dot visual language into the TV Grid channel identity column.
- Actual playback-session ownership remains the RC15 truth source.
- 1320 ms normal pulse, 1900 ms Night Cinema pulse.
- 180 ms channel-handoff bloom/fade, 240 ms accent<->Cinema color morph.
- OLED emissive core/glow floor from the approved mobile micro-polish.
- Normal color follows current Glass UI accent; Night Cinema uses locked #FFC247 amber.
- Ambient rendering stays retired on TV. No blur, no Ambient surface work, no playback mutation.
- 33 ms (~30 fps) micro-indicator repaint cadence to keep the 32-bit onn box lightweight.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103236
OLD_VERSION=2103235
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Final-Polish-RC15'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Pulsing-Dot-RC16'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label}: expected 1 anchor, got {s.count(a)}');return s.replace(a,b,1)
def span(text,name,kind='method'):
    if kind=='method':
        p=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    else:
        p=re.compile(r'(?m)^\s*(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b')
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();b=text.find('{',ms[0].end());d=0;q=None;esc=line=block=False
    for i in range(b,len(text)):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True
        elif c=='/' and n=='*':block=True
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return st,i+1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    req('COBRA_TV_FINAL_POLISH_BUILD="cobra_tv_final_polish_2103235"' in s,'Exact locked RC15 parent marker missing')
    req('class CobraTvPlayingDot' not in s,'TV pulsing dot already present')

    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen','closeFullscreenToCobraView',
      'cobraReturnToMultiFromFullscreen','setMultiAudio','cobraLayoutPlayerPanels',
      'cobraTvChannelPlaybackState','cobraTvChannelPlaying'
    ]
    protected={n:sha_bytes(member(s,n)) for n in protected_methods}

    marker='  private final class CobraBroadcastRow extends FrameLayout{'
    helpers=r'''  static final class CobraTvPlayingDotPolicy{
    static final int CINEMA_AMBER=0xffffc247;
    static final long HANDOFF_MS=180L;
    static final long COLOR_MORPH_MS=240L;
    static final long FRAME_MS=33L;
    static final int OLED_CORE_FLOOR_ALPHA=218;
    static final float OLED_GLOW_FLOOR=.58f;
    static final long NORMAL_PULSE_MS=1320L;
    static final long CINEMA_PULSE_MS=1900L;
    static float unit(float value){return Math.max(0f,Math.min(1f,value));}
    static float smooth(float value){float t=unit(value);return t*t*(3f-2f*t);}
    static long pulsePeriodMs(boolean cinema){return cinema?CINEMA_PULSE_MS:NORMAL_PULSE_MS;}
    static int glowAlpha(boolean cinema){return cinema?58:76;}
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
  }

  private int cobraTvPlayingDotColor(){
    boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
    return cinema?CobraTvPlayingDotPolicy.CINEMA_AMBER:cobraModeColor("accent");
  }

  private final class CobraTvPlayingDot extends View{
    final android.graphics.Paint paint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    Channel channel;boolean active,visualActive,colorReady;int handoffDirection,colorFrom,colorTo;long handoffStarted,colorStarted;
    CobraTvPlayingDot(){super(InfinityLiveActivity.this);setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);setVisibility(View.INVISIBLE);}
    void bind(Channel value){
      boolean same=channel!=null&&value!=null&&cobraChannelKey(channel).equals(cobraChannelKey(value));
      if(!same){active=false;visualActive=false;handoffDirection=0;colorReady=false;setVisibility(View.INVISIBLE);}
      channel=value;sync(same);
    }
    void sync(){sync(true);}
    void sync(boolean animate){
      boolean next=cobraTvChannelPlaying(channel);if(next==active){if(active||visualActive)invalidate();return;}
      long now=android.os.SystemClock.uptimeMillis();
      if(next){active=true;visualActive=true;handoffDirection=animate?1:0;handoffStarted=now;setVisibility(View.VISIBLE);invalidate();return;}
      active=false;String owner=cobraTvPlayingIndicatorKey();
      boolean replacement=animate&&owner!=null&&!owner.isEmpty()&&channel!=null&&!owner.startsWith(cobraChannelKey(channel)+":");
      if(replacement){visualActive=true;handoffDirection=-1;handoffStarted=now;setVisibility(View.VISIBLE);invalidate();}
      else{visualActive=false;handoffDirection=0;setVisibility(View.INVISIBLE);}
    }
    int interpolatedColor(long now){
      if(colorFrom==colorTo)return colorTo;float t=(now-colorStarted)/(float)CobraTvPlayingDotPolicy.COLOR_MORPH_MS;
      if(t>=1f){colorFrom=colorTo;return colorTo;}return CobraTvPlayingDotPolicy.blendColor(colorFrom,colorTo,t);
    }
    int renderedColor(long now){
      int target=cobraTvPlayingDotColor();
      if(!colorReady){colorReady=true;colorFrom=target;colorTo=target;colorStarted=now;return target;}
      if(target!=colorTo){int current=interpolatedColor(now);colorFrom=current;colorTo=target;colorStarted=now;}
      return interpolatedColor(now);
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();sync(false);}
    @Override protected void onDraw(android.graphics.Canvas canvas){
      if(!active&&!visualActive)return;
      boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
      long period=CobraTvPlayingDotPolicy.pulsePeriodMs(cinema),now=android.os.SystemClock.uptimeMillis();
      float wave=.5f+.5f*(float)Math.sin((now%period)*Math.PI*2d/period),handoff=1f;
      if(handoffDirection!=0){
        long elapsed=Math.max(0L,now-handoffStarted);
        if(elapsed>=CobraTvPlayingDotPolicy.HANDOFF_MS){
          if(handoffDirection<0){handoffDirection=0;visualActive=false;setVisibility(View.INVISIBLE);return;}
          handoffDirection=0;
        }else handoff=CobraTvPlayingDotPolicy.handoffAlpha(handoffDirection>0,elapsed);
      }
      int color=renderedColor(now),cx=getWidth()/2,cy=getHeight()/2;
      float core=dp(3),glow=dp(cinema?5:6),pulse=CobraTvPlayingDotPolicy.oledGlowFactor(wave);
      int baseGlow=CobraTvPlayingDotPolicy.glowAlpha(cinema);
      int outer=Math.round(baseGlow*.30f*pulse*handoff),inner=Math.round(baseGlow*pulse*handoff),coreAlpha=Math.round(CobraTvPlayingDotPolicy.oledCoreAlpha(wave)*handoff);
      paint.setColor(Color.argb(outer,Color.red(color),Color.green(color),Color.blue(color)));canvas.drawCircle(cx,cy,glow*(1.12f+.06f*wave),paint);
      paint.setColor(Color.argb(inner,Color.red(color),Color.green(color),Color.blue(color)));canvas.drawCircle(cx,cy,glow*(.76f+.20f*wave),paint);
      paint.setColor(Color.argb(coreAlpha,Color.red(color),Color.green(color),Color.blue(color)));canvas.drawCircle(cx,cy,core,paint);
      int hot=Math.round((cinema?92:132)*handoff);paint.setColor(Color.argb(hot,255,255,255));canvas.drawCircle(cx,cy,Math.max(1f,core*.24f),paint);
      postInvalidateDelayed(CobraTvPlayingDotPolicy.FRAME_MS);
    }
  }

'''
    s=once(s,marker,helpers+marker,'TV pulsing-dot helpers')

    s=once(s,
'    Channel channel;final Button title;final ArrayList<Button> cells=new ArrayList<>();final ArrayList<float[]> ranges=new ArrayList<>();int used=0,labelWidth;float downX,downY;boolean swiping;',
'    Channel channel;final Button title;final CobraTvPlayingDot playingDot=new CobraTvPlayingDot();final ArrayList<Button> cells=new ArrayList<>();final ArrayList<float[]> ranges=new ArrayList<>();int used=0,labelWidth;float downX,downY;boolean swiping;',
'TV grid dot field')

    s=once(s,
'''    CobraBroadcastRow(){super(InfinityLiveActivity.this);title=cobraTextButton("",cobraModeDark(),()->{});title.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);title.setPadding(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.1",8)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.2",2)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.3",6)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.4",2)));title.setMaxLines(2);title.setTextSize(vtheme().number("cobra.CobraBroadcastRow.numbers.1",12,8f,96f));addView(title);setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);}''',
'''    CobraBroadcastRow(){super(InfinityLiveActivity.this);title=cobraTextButton("",cobraModeDark(),()->{});title.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);int dotPad=Math.max(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.3",6)),dp(27));title.setPadding(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.1",8)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.2",2)),dotPad,dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.4",2)));title.setMaxLines(2);title.setTextSize(vtheme().number("cobra.CobraBroadcastRow.numbers.1",12,8f,96f));addView(title);addView(playingDot);setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);}''',
'TV grid dot layout')

    s=once(s,
'''      channel=c;boolean playing=cobraTvChannelPlaying(c);String playback=cobraTvChannelPlaybackState(c);
      setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("grid")));''',
'''      channel=c;boolean playing=cobraTvChannelPlaying(c);String playback=cobraTvChannelPlaybackState(c);playingDot.bind(c);
      setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("grid")));''',
'TV grid dot bind')

    s=once(s,
'''    @Override protected void onMeasure(int ws,int hs){int w=View.MeasureSpec.getSize(ws),h=cobraModeRowHeight("grid");labelWidth=Math.min(w,dp(mCobraModeLayout==null?106:mCobraModeLayout.channelWidth));setMeasuredDimension(w,h);title.measure(View.MeasureSpec.makeMeasureSpec(Math.max(1,labelWidth-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.9",2))),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.10",2)),View.MeasureSpec.EXACTLY));for(int i=0;i<used;i++){''',
'''    @Override protected void onMeasure(int ws,int hs){int w=View.MeasureSpec.getSize(ws),h=cobraModeRowHeight("grid");labelWidth=Math.min(w,dp(mCobraModeLayout==null?106:mCobraModeLayout.channelWidth));setMeasuredDimension(w,h);title.measure(View.MeasureSpec.makeMeasureSpec(Math.max(1,labelWidth-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.9",2))),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.10",2)),View.MeasureSpec.EXACTLY));int dot=dp(18);playingDot.measure(View.MeasureSpec.makeMeasureSpec(dot,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(dot,View.MeasureSpec.EXACTLY));for(int i=0;i<used;i++){''',
'TV grid dot measure')

    s=once(s,
'''    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){title.layout(0,0,title.getMeasuredWidth(),title.getMeasuredHeight());for(int i=0;i<used;i++){''',
'''    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){title.layout(0,0,title.getMeasuredWidth(),title.getMeasuredHeight());int dot=playingDot.getMeasuredWidth(),dx=Math.max(dp(4),labelWidth-dot-dp(5)),dy=Math.max(0,(getHeight()-dot)/2);playingDot.layout(dx,dy,dx+dot,dy+dot);for(int i=0;i<used;i++){''',
'TV grid dot position')

    row=member(s,'CobraBroadcastRow','class')
    row=once(row,'    Button obtainCell(int index){','    void refreshPlayingDot(){playingDot.sync();}\n    Button obtainCell(int index){','TV grid dot refresh')
    a,b=span(s,'CobraBroadcastRow','class');s=s[:a]+row+s[b:]

    # Existing RC15 playing-state refresh remains authoritative. Refresh the tiny visible dot too.
    s=once(s,
'''  private void cobraTvRefreshPlayingIndicatorIfChanged(){
    String next=cobraTvPlayingIndicatorKey();if(next.equals(mCobraTvPlayingIndicatorKey))return;mCobraTvPlayingIndicatorKey=next;
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
  }''',
'''  private void cobraTvRefreshPlayingIndicatorIfChanged(){
    String next=cobraTvPlayingIndicatorKey();if(next.equals(mCobraTvPlayingIndicatorKey))return;mCobraTvPlayingIndicatorKey=next;
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
    if(mCobraGuideList!=null)for(int i=0;i<mCobraGuideList.getChildCount();i++){View child=mCobraGuideList.getChildAt(i);if(child instanceof CobraBroadcastRow)((CobraBroadcastRow)child).refreshPlayingDot();}
  }''',
'TV dot state refresh')

    # Preservation gates.
    for n,d in protected.items():req(sha_bytes(member(s,n))==d,'Protected playback/session method changed: '+n)
    req('NORMAL_PULSE_MS=1320L' in s,'Normal pulse cadence missing')
    req('CINEMA_PULSE_MS=1900L' in s,'Night Cinema pulse cadence missing')
    req('CINEMA_AMBER=0xffffc247' in s,'Night Cinema amber missing')
    req('OLED_CORE_FLOOR_ALPHA=218' in s and 'OLED_GLOW_FLOOR=.58f' in s,'OLED floor missing')
    req('postInvalidateDelayed(CobraTvPlayingDotPolicy.FRAME_MS)' in s,'Lightweight TV repaint cadence missing')
    req('CobraPresentationEffects.ambientMode(mPrefs)' not in member(s,'cobraTvPlayingDotColor'),'TV dot depends on retired Ambient mode')
    req('CobraPresentationEffects.ambientMode(mPrefs)' not in member(s,'CobraTvPlayingDot','class'),'TV dot renderer depends on retired Ambient mode')
    req('AMBIENT MODE  •' not in s,'Ambient Mode returned')
    req('COBRA_TV_FINAL_POLISH_BUILD="cobra_tv_final_polish_2103235"' in s,'RC15 parent marker lost')
    req('KEYCODE_DPAD_RIGHT&&mCobraTvDrawerInline' in s,'RC15 Live TV Right-select lost')
    req('cobra_movies_search' in s and 'cobra_shows_search' in s,'RC15 VOD searches lost')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103235 RC15 parent')
    req(receipt.get('tv_right_select_scope')=='live-tv-only' and receipt.get('tv_vod_right_navigation_untouched') is True,'RC15 input scope missing')
    req(receipt.get('tv_movies_dedicated_search') is True and receipt.get('tv_shows_dedicated_search') is True,'RC15 VOD searches missing')
    req(receipt.get('tv_mini_player_playing_badge_removed') is True and receipt.get('tv_playing_channel_indicator') is True,'RC15 playing presentation missing')
    req(receipt.get('tv_ambient_mode_retired') is True and receipt.get('tv_glass_system') is True,'RC15 glass/Ambient parent missing')
    req(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'Expected isolated ARMv7 TV parent')

    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    before,after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_grid_pulsing_playing_dot=True,tv_playing_dot_actual_session=True,tv_playing_dot_focus_independent=True,
      tv_playing_dot_normal_pulse_ms=1320,tv_playing_dot_night_cinema_pulse_ms=1900,
      tv_playing_dot_handoff_ms=180,tv_playing_dot_color_morph_ms=240,
      tv_playing_dot_oled_core_floor_alpha=218,tv_playing_dot_oled_glow_floor=.58,
      tv_playing_dot_night_cinema_amber='0xffffc247',tv_playing_dot_glass_accent=True,
      tv_playing_dot_ambient_independent=True,tv_playing_dot_frame_ms=33,
      tv_playing_dot_no_blur=True,tv_playing_dot_playback_mutation=False,
      tv_ambient_mode_retired=True,tv_ambient_dynamic_layering=False,tv_glass_system=True,
      tv_right_select_scope='live-tv-only',tv_vod_right_navigation_untouched=True,
      tv_movies_dedicated_search=True,tv_shows_dedicated_search=True,
      tv_mini_player_playing_badge_removed=True,tv_playing_channel_indicator=True,
      tv_navigation_hierarchy='drawer-groups-grid-player',tv_back_reverses_hierarchy=True,
      tv_mini_player_preserved=True,tv_preview_engine_preserved=True,
      tv_multiview_row_focus_visible=True,multiview_two_to_one_session_preserved=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit236').mkdir(exist_ok=True)
    Path('audit236/tv-pulsing-dot-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'authorized_delta':'TV Grid pulsing true-playing dot only',
      'mobile_visual_reference':'2103237 OLED playing-dot micro-polish',
      'placement':'TV Grid channel identity column','actual_session_owned':True,'focus_independent':True,
      'normal_pulse_ms':1320,'night_cinema_pulse_ms':1900,'handoff_ms':180,'color_morph_ms':240,
      'oled_core_floor_alpha':218,'oled_glow_floor':.58,'night_cinema_amber':'0xffffc247',
      'glass_accent_normal':True,'ambient_renderer_used':False,'frame_ms':33,'real_time_blur':False,
      'playback_engine_unchanged':True,'native_engine_rebuilt':False,'mobile_fold_untouched':True,
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103236 lightweight mobile-matched TV Grid pulsing dot applied over exact locked 2103235 RC15')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
