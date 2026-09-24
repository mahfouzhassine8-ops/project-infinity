#!/usr/bin/env python3
"""2103235: locked Live TV true-playing indicator over exact passed 2103230 source.

Authorized delta only:
- Add a small pulsing playing dot to the TV Grid channel label region.
- Bind visibility to the actual current Live TV playback owner/session, never row focus/selection.
- Adapt glow to Ambient Mode and Night Cinema preference.
No playback, provider, timeshift, navigation, Multi-View ownership, native, resource or theme redesign.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103235
OLD_VERSION=2103230
OLD_NAME='1.0.9-Cobra-Final-Preservation-Audit-RC1'
NEW_NAME='1.0.9-Cobra-Live-Playing-Indicator-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
ACT=SOURCE+'InfinityLiveActivity.java.in'
PARENT_ACTIVITY='1324e98736c24e203941261cc34c468596892a7897e0679b51f5915e26bd34b6'
PATCHED_ACTIVITY='edaf4a757ceded3099fc0e2adbbcfb5dbf98d394c713b321d41efe62ae6a7d54'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT_COMMIT='1f5ea888a1cc1daa5c0617cf51bb09cc3b432060'

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
    before_b=path.read_bytes();req(hb(before_b)==PARENT_ACTIVITY,'Not exact passed 2103230 Activity preimage')
    s=before_b.decode()
    protected_methods=['buildPlayer','playChannel','cobraRestartLiveChannel','cobraRecoverUnexpectedLiveEnded','cobraRecoverMultiTileSession','cobraRetryMultiTile','cobraFitBinding','cobraMultiSafeInsets','onConfigurationChanged','cobraLayoutPlayerPanels','setMultiAudio','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen']
    protected_classes=['CobraPlayerBinding','CobraVideoTile','CobraMultiRecoveryPolicy','CobraLiveEndedPolicy','CobraAuditPolicy','CobraFoldAspectPolicy']
    mh={n:hb(member(s,n)) for n in protected_methods};ch={n:hb(member(s,n,'class')) for n in protected_classes}

    s=once(s,
'''    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}
    cobraRefreshModeDetails();
  }''',
'''    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}
    cobraRefreshPlayingIndicators();
    cobraRefreshModeDetails();
  }''','guide playing-indicator refresh')

    marker='  private final class CobraBroadcastRow extends FrameLayout{'
    helpers=r'''  static final class CobraPlayingIndicatorPolicy {
    static boolean active(boolean live,boolean requested,int suppression,int state,boolean error){
      return live&&requested&&!error&&suppression==Player.PLAYBACK_SUPPRESSION_REASON_NONE
          &&(state==Player.STATE_READY||state==Player.STATE_BUFFERING);
    }
    static int glowAlpha(int ambient,boolean cinema){
      if(cinema)return 58;
      return ambient==CobraPresentationEffects.IMMERSIVE?124:ambient==CobraPresentationEffects.SUBTLE?94:76;
    }
    static long pulsePeriodMs(boolean cinema){return cinema?1900L:1320L;}
  }

  private CobraPlayerBinding cobraPlayingIndicatorOwner(){
    ExoPlayer player=null;
    if(mPlayer!=null&&mPlayingVodKey.isEmpty()&&!mCobraProviderCatchupActive)player=mPlayer;
    else if(mMultiOverlay!=null&&!mCobraMultiFullscreenActive&&mMultiPlayers!=null&&mMultiChannels!=null
        &&mAudioTile>=0&&mAudioTile<mMultiPlayers.length&&mAudioTile<mMultiChannels.length)player=mMultiPlayers[mAudioTile];
    else if(mCobraPreviewPlayer!=null)player=mCobraPreviewPlayer;
    else if(mCobraMiniBackgroundActive&&mCobraMiniBackgroundPlayer!=null)player=mCobraMiniBackgroundPlayer;
    if(player==null)return null;
    CobraPlayerBinding binding=mCobraPlayerBindings.get(player);
    if(binding==null||!binding.current()||binding.channel==null)return null;
    if(!CobraPlayingIndicatorPolicy.active(binding.vitals.live,player.getPlayWhenReady(),player.getPlaybackSuppressionReason(),
        player.getPlaybackState(),!binding.error.isEmpty()))return null;
    return binding;
  }

  private boolean cobraChannelActuallyPlaying(Channel channel){
    if(channel==null)return false;CobraPlayerBinding owner=cobraPlayingIndicatorOwner();
    return owner!=null&&owner.channel!=null&&channel.id.equals(owner.channel.id);
  }

  private int cobraPlayingIndicatorColor(){
    boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
    return cinema?COBRA_LIVE_AMBIENT_BLUE:cobraModeColor("accent");
  }

  private void cobraRefreshPlayingIndicators(){
    if(mCobraGuideList==null)return;
    for(int i=0;i<mCobraGuideList.getChildCount();i++){
      View child=mCobraGuideList.getChildAt(i);
      if(child instanceof CobraBroadcastRow)((CobraBroadcastRow)child).refreshPlaying();
    }
  }

  private final class CobraPlayingDot extends View{
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
  }

'''+marker
    s=once(s,marker,helpers,'playing-indicator helpers')
    s=once(s,'    Channel channel;final Button title;final ArrayList<Button> cells=new ArrayList<>();final ArrayList<float[]> ranges=new ArrayList<>();int used=0,labelWidth;float downX,downY;boolean swiping;',
      '    Channel channel;final Button title;final CobraPlayingDot playing=new CobraPlayingDot();final ArrayList<Button> cells=new ArrayList<>();final ArrayList<float[]> ranges=new ArrayList<>();int used=0,labelWidth;float downX,downY;boolean swiping;','row indicator field')
    s=once(s,
'''    CobraBroadcastRow(){super(InfinityLiveActivity.this);title=cobraTextButton("",cobraModeDark(),()->{});title.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);title.setPadding(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.1",8)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.2",2)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.3",6)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.4",2)));title.setMaxLines(2);title.setTextSize(vtheme().number("cobra.CobraBroadcastRow.numbers.1",12,8f,96f));addView(title);setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);}''',
'''    CobraBroadcastRow(){super(InfinityLiveActivity.this);title=cobraTextButton("",cobraModeDark(),()->{});title.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);int indicatorPad=Math.max(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.3",6)),dp(28));title.setPadding(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.1",8)),dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.2",2)),indicatorPad,dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.4",2)));title.setMaxLines(2);title.setTextSize(vtheme().number("cobra.CobraBroadcastRow.numbers.1",12,8f,96f));addView(title);addView(playing);setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);}''','row indicator layout')
    s=once(s,'      channel=c;setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("grid")));title.setText(String.format(Locale.US,"%03d  ",position+1)+c.name);title.setTag("cobra-channel:"+c.id);',
      '      channel=c;setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("grid")));title.setText(String.format(Locale.US,"%03d  ",position+1)+c.name);playing.bind(c);title.setTag("cobra-channel:"+c.id);','row bind indicator')
    s=once(s,
'''    @Override protected void onMeasure(int ws,int hs){int w=View.MeasureSpec.getSize(ws),h=cobraModeRowHeight("grid");labelWidth=Math.min(w,dp(mCobraModeLayout==null?106:mCobraModeLayout.channelWidth));setMeasuredDimension(w,h);title.measure(View.MeasureSpec.makeMeasureSpec(Math.max(1,labelWidth-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.9",2))),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.10",2)),View.MeasureSpec.EXACTLY));for(int i=0;i<used;i++){''',
'''    @Override protected void onMeasure(int ws,int hs){int w=View.MeasureSpec.getSize(ws),h=cobraModeRowHeight("grid");labelWidth=Math.min(w,dp(mCobraModeLayout==null?106:mCobraModeLayout.channelWidth));setMeasuredDimension(w,h);title.measure(View.MeasureSpec.makeMeasureSpec(Math.max(1,labelWidth-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.9",2))),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.10",2)),View.MeasureSpec.EXACTLY));int indicator=dp(18);playing.measure(View.MeasureSpec.makeMeasureSpec(indicator,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(indicator,View.MeasureSpec.EXACTLY));for(int i=0;i<used;i++){''','row measure indicator')
    s=once(s,
'''    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){title.layout(0,0,title.getMeasuredWidth(),title.getMeasuredHeight());for(int i=0;i<used;i++){''',
'''    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){title.layout(0,0,title.getMeasuredWidth(),title.getMeasuredHeight());int indicator=playing.getMeasuredWidth(),ix=Math.max(dp(4),labelWidth-indicator-dp(6)),iy=Math.max(0,(getHeight()-indicator)/2);playing.layout(ix,iy,ix+indicator,iy+indicator);for(int i=0;i<used;i++){''','row position indicator')
    row=member(s,'CobraBroadcastRow','class')
    row=once(row,'    Button obtainCell(int index){','    void refreshPlaying(){playing.sync();}\n    Button obtainCell(int index){','row refresh method')
    a,b=span(s,'CobraBroadcastRow','class');s=s[:a]+row+s[b:]

    for n,d in mh.items():req(hb(member(s,n))==d,'Protected playback method changed: '+n)
    for n,d in ch.items():req(hb(member(s,n,'class'))==d,'Protected playback class changed: '+n)
    path.write_text(s);req(sha(path)==PATCHED_ACTIVITY,'Unexpected Activity postimage')
    return {'activity_before_sha256':hb(before_b),'activity_after_sha256':sha(path),'protected_methods_sha256':mh,'protected_classes_sha256':ch}

def patch_identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text();r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version');r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME;req(p.count(old)>=2,'packager identity drift');pack.write_text(p.replace(old,new));return gradle

def main():
    q=argparse.ArgumentParser();q.add_argument('--shell',type=Path,required=True);a=q.parse_args();shell=a.shell
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text());req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact passed 2103230 generated source');req(receipt.get('native_engine_sha256')==NATIVE,'Native receipt drift')
    activity=shell/ACT;frozen={str(p.relative_to(shell)):sha(p) for p in sorted(shell.rglob('*')) if p.is_file()}
    scope=patch_activity(activity);gradle=patch_identity(shell)
    changed=[n for n,d in frozen.items() if sha(shell/n)!=d];req(set(changed)=={ACT,'tools/android/packaging/xbmc/build.gradle.in'},'Unexpected generated source changes: '+str(changed))
    for n in changed:receipt['files'][n]['after']=sha(shell/n)
    receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,true_live_playing_indicator=True,playing_indicator_actual_session_owned=True,playing_indicator_focus_independent=True,playing_indicator_ambient_adaptive=True,playing_indicator_night_cinema_adaptive=True,playing_indicator_playback_mutation=False)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for n,row in receipt['files'].items():req(sha(shell/n)==row['after'],'Receipt drift '+n)
    out=Path('audit235');out.mkdir(exist_ok=True);scope.update(build=VERSION,parent=OLD_VERSION,parent_commit=PARENT_COMMIT,changed_files=changed,native_engine_sha256=NATIVE,native_engine_rebuilt=False,authorized_delta='TV Grid true-playing pulsing dot only',physical_device_verified=False,status='TEST CANDIDATE')
    (out/'scope.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\n');print('PASS: 2103235 true-playing indicator applied over exact passed 2103230 source')
if __name__=='__main__':main()
