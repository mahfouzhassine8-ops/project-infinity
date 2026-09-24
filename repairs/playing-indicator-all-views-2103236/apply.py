#!/usr/bin/env python3
"""2103236: extend the already-approved 2103235 true-playing dot to every Live TV view.

Authorized delta only:
- Preserve TV Grid's working actual-session indicator.
- Add the same CobraPlayingDot renderer to Mobile, Compact, Cards and Focus.
- Night Cinema uses the approved warm amber/yellow dot.
- Ambient pulse strength and all playback/session ownership remain exactly 2103235.
No player/provider/timeshift/Multi-View/navigation/native/resource redesign.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103236
OLD_VERSION=2103235
OLD_NAME='1.0.9-Cobra-Live-Playing-Indicator-RC1'
NEW_NAME='1.0.9-Cobra-All-Views-Playing-Indicator-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
ACT=SOURCE+'InfinityLiveActivity.java.in'
PARENT_ACTIVITY='edaf4a757ceded3099fc0e2adbbcfb5dbf98d394c713b321d41efe62ae6a7d54'
PATCHED_ACTIVITY='0b1e50528f790dd6fdbc71a880eeffbd0c6c6bb13f9606ffacb8e7971f149dbf'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT_COMMIT='ab19189da2852f33adc7fc1c07dfdf13368949e7'

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
    before_b=path.read_bytes();req(hb(before_b)==PARENT_ACTIVITY,'Not exact passed 2103235 Activity preimage')
    s=before_b.decode()

    # Playback/session truth must not move during this presentation-only expansion.
    protected_methods=[
      'buildPlayer','playChannel','cobraRestartLiveChannel','cobraRecoverUnexpectedLiveEnded',
      'cobraRecoverMultiTileSession','cobraRetryMultiTile','cobraFitBinding','cobraMultiSafeInsets',
      'onConfigurationChanged','cobraLayoutPlayerPanels','setMultiAudio','startCobraPreview',
      'promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'cobraPlayingIndicatorOwner','cobraChannelActuallyPlaying'
    ]
    protected_classes=[
      'CobraPlayerBinding','CobraVideoTile','CobraMultiRecoveryPolicy','CobraLiveEndedPolicy',
      'CobraAuditPolicy','CobraFoldAspectPolicy','CobraPlayingDot','CobraBroadcastRow'
    ]
    mh={n:hb(member(s,n)) for n in protected_methods};ch={n:hb(member(s,n,'class')) for n in protected_classes}

    # Approved Cinema treatment: warm amber/yellow. Pulse cadence stays 2103235.
    s=once(s,
'''  static final class CobraPlayingIndicatorPolicy {
    static boolean active(boolean live,boolean requested,int suppression,int state,boolean error){''',
'''  static final class CobraPlayingIndicatorPolicy {
    static final int CINEMA_AMBER=0xffffc247;
    static boolean active(boolean live,boolean requested,int suppression,int state,boolean error){''','cinema amber constant')

    s=once(s,
'''  private int cobraPlayingIndicatorColor(){
    boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
    return cinema?COBRA_LIVE_AMBIENT_BLUE:cobraModeColor("accent");
  }''',
'''  private int cobraPlayingIndicatorColor(){
    boolean cinema=mPrefs!=null&&mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
    return cinema?CobraPlayingIndicatorPolicy.CINEMA_AMBER:cobraModeColor("accent");
  }''','cinema amber mapping')

    # One refresh path for all five existing view renderers.
    s=once(s,
'''  private void cobraRefreshPlayingIndicators(){
    if(mCobraGuideList==null)return;
    for(int i=0;i<mCobraGuideList.getChildCount();i++){
      View child=mCobraGuideList.getChildAt(i);
      if(child instanceof CobraBroadcastRow)((CobraBroadcastRow)child).refreshPlaying();
    }
  }''',
'''  private void cobraRefreshPlayingIndicators(){
    if(mCobraGuideList==null)return;
    for(int i=0;i<mCobraGuideList.getChildCount();i++){
      View child=mCobraGuideList.getChildAt(i);
      if(child instanceof CobraBroadcastRow)((CobraBroadcastRow)child).refreshPlaying();
      else if(child instanceof CobraMobileChannelRow)((CobraMobileChannelRow)child).refreshPlaying();
      else if(child instanceof CobraCompactChannelRow)((CobraCompactChannelRow)child).refreshPlaying();
      else if(child instanceof CobraPosterChannelCard)((CobraPosterChannelCard)child).refreshPlaying();
      else if(child instanceof CobraFocusQueueRow)((CobraFocusQueueRow)child).refreshPlaying();
    }
  }''','all-mode refresh')

    # Mobile: dot in the channel identity headline, beside the channel name.
    s=once(s,
'''  private final class CobraMobileChannelRow extends LinearLayout{
    final CobraChannelMark mark=new CobraChannelMark();final TextView title=cobraModeLabel(15,true),now=cobraModeLabel(13,false),next=cobraModeLabel(11,false);final android.widget.ProgressBar progress=cobraProgress(cobraModeDark());''',
'''  private final class CobraMobileChannelRow extends LinearLayout{
    final CobraChannelMark mark=new CobraChannelMark();final CobraPlayingDot playing=new CobraPlayingDot();final TextView title=cobraModeLabel(15,true),now=cobraModeLabel(13,false),next=cobraModeLabel(11,false);final android.widget.ProgressBar progress=cobraProgress(cobraModeDark());''','mobile dot field')

    s=once(s,
'''    CobraMobileChannelRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.1",8)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.2",8)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.3",10)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.4",8)));addView(mark,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.5",54)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.6",54))));LinearLayout copy=new LinearLayout(InfinityLiveActivity.this);copy.setOrientation(VERTICAL);copy.addView(title);copy.addView(now);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.7",2)));p.topMargin=dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.8",6));p.bottomMargin=dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.9",5));copy.addView(progress,p);copy.addView(next);LinearLayout.LayoutParams text=new LinearLayout.LayoutParams(0,-2,1);text.leftMargin=dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.10",14));addView(copy,text);}''',
'''    CobraMobileChannelRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.1",8)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.2",8)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.3",10)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.4",8)));addView(mark,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.5",54)),dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.6",54))));LinearLayout copy=new LinearLayout(InfinityLiveActivity.this);copy.setOrientation(VERTICAL);LinearLayout headline=new LinearLayout(InfinityLiveActivity.this);headline.setOrientation(HORIZONTAL);headline.setGravity(Gravity.CENTER_VERTICAL);headline.addView(title,new LinearLayout.LayoutParams(0,-2,1));LinearLayout.LayoutParams dot=new LinearLayout.LayoutParams(dp(18),dp(18));dot.leftMargin=dp(6);headline.addView(playing,dot);copy.addView(headline);copy.addView(now);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.7",2)));p.topMargin=dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.8",6));p.bottomMargin=dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.9",5));copy.addView(progress,p);copy.addView(next);LinearLayout.LayoutParams text=new LinearLayout.LayoutParams(0,-2,1);text.leftMargin=dp(vtheme().dimension("cobra.CobraMobileChannelRow.dimensions.10",14));addView(copy,text);}''','mobile placement')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(14,false));mark.bind(c);title.setText(c.name);''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(14,false));mark.bind(c);playing.bind(c);title.setText(c.name);''','mobile bind')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(14,false));mark.bind(c);playing.bind(c);title.setText(c.name);title.setTextColor(cobraModeColor("text"));now.setTextColor(cobraModeColor("muted"));next.setTextColor(cobraModeColor("muted"));GuideProgram p=cobraCurrentProgram(c),n=cobraNextProgram(c);now.setText(p==null?cobraGuideStatus(c):p.title);next.setText(n==null?c.group:"Next · "+n.title);progress.setProgress(p==null?0:Math.round(CobraGuideMath.progress(p.start,p.stop,System.currentTimeMillis())*1000));progress.setVisibility(p==null?View.INVISIBLE:View.VISIBLE);setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("mobile")));}
  }''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(14,false));mark.bind(c);playing.bind(c);title.setText(c.name);title.setTextColor(cobraModeColor("text"));now.setTextColor(cobraModeColor("muted"));next.setTextColor(cobraModeColor("muted"));GuideProgram p=cobraCurrentProgram(c),n=cobraNextProgram(c);now.setText(p==null?cobraGuideStatus(c):p.title);next.setText(n==null?c.group:"Next · "+n.title);progress.setProgress(p==null?0:Math.round(CobraGuideMath.progress(p.start,p.stop,System.currentTimeMillis())*1000));progress.setVisibility(p==null?View.INVISIBLE:View.VISIBLE);setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("mobile")));}
    void refreshPlaying(){playing.sync();}
  }''','mobile refresh')

    # Compact: dot directly after channel-name column.
    s=once(s,
'''  private final class CobraCompactChannelRow extends LinearLayout{
    final TextView number=cobraModeLabel(11,false),title=cobraModeLabel(13,true),now=cobraModeLabel(12,false),end=cobraModeLabel(11,false);final android.graphics.Paint paint=new android.graphics.Paint();''',
'''  private final class CobraCompactChannelRow extends LinearLayout{
    final CobraPlayingDot playing=new CobraPlayingDot();final TextView number=cobraModeLabel(11,false),title=cobraModeLabel(13,true),now=cobraModeLabel(12,false),end=cobraModeLabel(11,false);final android.graphics.Paint paint=new android.graphics.Paint();''','compact dot field')

    s=once(s,
'''    CobraCompactChannelRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.1",8)),0,dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.2",8)),0);number.setTypeface(Typeface.MONOSPACE);end.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);addView(number,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.3",38)),-1));addView(title,new LinearLayout.LayoutParams(0,-1,1));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-1,1.12f);p.leftMargin=dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.4",10));addView(now,p);addView(end,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.5",58)),-1));}''',
'''    CobraCompactChannelRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.1",8)),0,dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.2",8)),0);number.setTypeface(Typeface.MONOSPACE);end.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);addView(number,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.3",38)),-1));addView(title,new LinearLayout.LayoutParams(0,-1,1));LinearLayout.LayoutParams dot=new LinearLayout.LayoutParams(dp(18),dp(18));dot.leftMargin=dp(4);dot.rightMargin=dp(4);addView(playing,dot);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-1,1.12f);p.leftMargin=dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.4",10));addView(now,p);addView(end,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraCompactChannelRow.dimensions.5",58)),-1));}''','compact placement')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(0,false));number.setText(String.format(Locale.US,"%03d",index+1));''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(0,false));playing.bind(c);number.setText(String.format(Locale.US,"%03d",index+1));''','compact bind')

    s=once(s,
'''    @Override protected void dispatchDraw(android.graphics.Canvas canvas){super.dispatchDraw(canvas);paint.setColor(cobraModeColor("line"));''',
'''    void refreshPlaying(){playing.sync();}
    @Override protected void dispatchDraw(android.graphics.Canvas canvas){super.dispatchDraw(canvas);paint.setColor(cobraModeColor("line"));''','compact refresh')

    # Cards: dot in the card identity/header hero, independent from SELECTED CHANNEL.
    s=once(s,
'''  private final class CobraPosterChannelCard extends LinearLayout{
    final FrameLayout hero=new FrameLayout(InfinityLiveActivity.this);final CobraChannelMark mark=new CobraChannelMark();final TextView category=cobraModeLabel(10,false),title=cobraModeLabel(15,true),now=cobraModeLabel(12,false),time=cobraModeLabel(10,false);final android.widget.ProgressBar progress=cobraProgress(cobraModeDark());''',
'''  private final class CobraPosterChannelCard extends LinearLayout{
    final FrameLayout hero=new FrameLayout(InfinityLiveActivity.this);final CobraChannelMark mark=new CobraChannelMark();final CobraPlayingDot playing=new CobraPlayingDot();final TextView category=cobraModeLabel(10,false),title=cobraModeLabel(15,true),now=cobraModeLabel(12,false),time=cobraModeLabel(10,false);final android.widget.ProgressBar progress=cobraProgress(cobraModeDark());''','cards dot field')

    s=once(s,
'''    CobraPosterChannelCard(){super(InfinityLiveActivity.this);setOrientation(VERTICAL);setClipToOutline(true);hero.addView(mark,new FrameLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraPosterChannelCard.dimensions.1",66)),dp(vtheme().dimension("cobra.CobraPosterChannelCard.dimensions.2",58)),Gravity.CENTER));category.setPadding''',
'''    CobraPosterChannelCard(){super(InfinityLiveActivity.this);setOrientation(VERTICAL);setClipToOutline(true);hero.addView(mark,new FrameLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraPosterChannelCard.dimensions.1",66)),dp(vtheme().dimension("cobra.CobraPosterChannelCard.dimensions.2",58)),Gravity.CENTER));FrameLayout.LayoutParams dot=new FrameLayout.LayoutParams(dp(18),dp(18),Gravity.TOP|Gravity.RIGHT);dot.topMargin=dp(8);dot.rightMargin=dp(8);hero.addView(playing,dot);category.setPadding''','cards placement')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(18,true));mark.bind(c);hero.setBackground''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(18,true));mark.bind(c);playing.bind(c);hero.setBackground''','cards bind')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(18,true));mark.bind(c);playing.bind(c);hero.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{cobraModeDark()?vtheme().color("cobra.CobraPosterChannelCard.colors.1",0xff223b50):vtheme().color("cobra.CobraPosterChannelCard.colors.2",0xffd7e9f5),cobraModeDark()?vtheme().color("cobra.CobraPosterChannelCard.colors.3",0xff162333):vtheme().color("cobra.CobraPosterChannelCard.colors.4",0xffebf2fa)}));category.setText(cobraModeSelected(c)?"SELECTED CHANNEL":c.group.toUpperCase(Locale.getDefault()));category.setTextColor(cobraModeSelected(c)?cobraModeColor("accent"):cobraModeColor("muted"));title.setText(c.name);title.setTextColor(cobraModeColor("text"));GuideProgram p=cobraCurrentProgram(c);now.setText(p==null?cobraGuideStatus(c):p.title);now.setTextColor(cobraModeColor("muted"));time.setText(p==null?"":"LIVE  ·  "+formatTime(p.start)+" – "+formatTime(p.stop));time.setTextColor(cobraModeColor("muted"));progress.setProgress(p==null?0:Math.round(CobraGuideMath.progress(p.start,p.stop,System.currentTimeMillis())*1000));progress.setVisibility(p==null?View.INVISIBLE:View.VISIBLE);setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("cards")));}
  }''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(18,true));mark.bind(c);playing.bind(c);hero.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{cobraModeDark()?vtheme().color("cobra.CobraPosterChannelCard.colors.1",0xff223b50):vtheme().color("cobra.CobraPosterChannelCard.colors.2",0xffd7e9f5),cobraModeDark()?vtheme().color("cobra.CobraPosterChannelCard.colors.3",0xff162333):vtheme().color("cobra.CobraPosterChannelCard.colors.4",0xffebf2fa)}));category.setText(cobraModeSelected(c)?"SELECTED CHANNEL":c.group.toUpperCase(Locale.getDefault()));category.setTextColor(cobraModeSelected(c)?cobraModeColor("accent"):cobraModeColor("muted"));title.setText(c.name);title.setTextColor(cobraModeColor("text"));GuideProgram p=cobraCurrentProgram(c);now.setText(p==null?cobraGuideStatus(c):p.title);now.setTextColor(cobraModeColor("muted"));time.setText(p==null?"":"LIVE  ·  "+formatTime(p.start)+" – "+formatTime(p.stop));time.setTextColor(cobraModeColor("muted"));progress.setProgress(p==null?0:Math.round(CobraGuideMath.progress(p.start,p.stop,System.currentTimeMillis())*1000));progress.setVisibility(p==null?View.INVISIBLE:View.VISIBLE);setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("cards")));}
    void refreshPlaying(){playing.sync();}
  }''','cards refresh')

    # Focus: dot anchored at far-right of the channel queue row.
    s=once(s,
'''  private final class CobraFocusQueueRow extends LinearLayout{
    final TextView number=cobraModeLabel(12,false),title=cobraModeLabel(14,true),now=cobraModeLabel(12,false),next=cobraModeLabel(10,false);''',
'''  private final class CobraFocusQueueRow extends LinearLayout{
    final CobraPlayingDot playing=new CobraPlayingDot();final TextView number=cobraModeLabel(12,false),title=cobraModeLabel(14,true),now=cobraModeLabel(12,false),next=cobraModeLabel(10,false);''','focus dot field')

    s=once(s,
'''    CobraFocusQueueRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.1",10)),dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.2",8)),dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.3",12)),dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.4",8)));number.setTypeface(Typeface.MONOSPACE);addView(number,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.5",34)),-1));LinearLayout copy=new LinearLayout(InfinityLiveActivity.this);copy.setOrientation(VERTICAL);copy.setGravity(Gravity.CENTER_VERTICAL);copy.addView(title);copy.addView(now);copy.addView(next);addView(copy,new LinearLayout.LayoutParams(0,-1,1));}''',
'''    CobraFocusQueueRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.1",10)),dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.2",8)),dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.3",12)),dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.4",8)));number.setTypeface(Typeface.MONOSPACE);addView(number,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.CobraFocusQueueRow.dimensions.5",34)),-1));LinearLayout copy=new LinearLayout(InfinityLiveActivity.this);copy.setOrientation(VERTICAL);copy.setGravity(Gravity.CENTER_VERTICAL);copy.addView(title);copy.addView(now);copy.addView(next);addView(copy,new LinearLayout.LayoutParams(0,-1,1));LinearLayout.LayoutParams dot=new LinearLayout.LayoutParams(dp(18),dp(18));dot.leftMargin=dp(8);addView(playing,dot);}''','focus placement')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(10,false));number.setText(cobraModeSelected(c)?"●":String.format(Locale.US,"%02d",index+1));''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(10,false));playing.bind(c);number.setText(cobraModeSelected(c)?"●":String.format(Locale.US,"%02d",index+1));''','focus bind')

    s=once(s,
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(10,false));playing.bind(c);number.setText(cobraModeSelected(c)?"●":String.format(Locale.US,"%02d",index+1));number.setTextColor(cobraModeSelected(c)?cobraModeColor("accent"):cobraModeColor("muted"));title.setText(c.name);title.setTextColor(cobraModeColor("text"));GuideProgram p=cobraCurrentProgram(c),n=cobraNextProgram(c);now.setText(p==null?cobraGuideStatus(c):p.title);next.setText(n==null?c.group:"Next  "+formatTime(n.start)+" · "+n.title);now.setTextColor(cobraModeColor("muted"));next.setTextColor(cobraModeColor("muted"));setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("focus")));}
  }''',
'''    void bind(Channel c,int index){cobraBindRow(this,c);setBackground(cobraModeSurface(10,false));playing.bind(c);number.setText(cobraModeSelected(c)?"●":String.format(Locale.US,"%02d",index+1));number.setTextColor(cobraModeSelected(c)?cobraModeColor("accent"):cobraModeColor("muted"));title.setText(c.name);title.setTextColor(cobraModeColor("text"));GuideProgram p=cobraCurrentProgram(c),n=cobraNextProgram(c);now.setText(p==null?cobraGuideStatus(c):p.title);next.setText(n==null?c.group:"Next  "+formatTime(n.start)+" · "+n.title);now.setTextColor(cobraModeColor("muted"));next.setTextColor(cobraModeColor("muted"));setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("focus")));}
    void refreshPlaying(){playing.sync();}
  }''','focus refresh')

    # Nothing in playback/session truth or dot animation/rendering itself may have changed.
    for n,d in mh.items():req(hb(member(s,n))==d,'Protected playback/session method changed: '+n)
    for n,d in ch.items():req(hb(member(s,n,'class'))==d,'Protected playback/session class changed: '+n)

    path.write_text(s);req(sha(path)==PATCHED_ACTIVITY,'Unexpected Activity postimage')
    return {'activity_before_sha256':hb(before_b),'activity_after_sha256':sha(path),'protected_methods_sha256':mh,'protected_classes_sha256':ch}

def patch_identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift');pack.write_text(p.replace(old,new));return gradle

def main():
    q=argparse.ArgumentParser();q.add_argument('--shell',type=Path,required=True);a=q.parse_args();shell=a.shell
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact 2103235 generated source')
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
      playing_indicator_night_cinema_amber='0xffffc247',playing_indicator_playback_mutation=False
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for n,row in receipt['files'].items():req(sha(shell/n)==row['after'],'Receipt drift '+n)
    out=Path('audit236');out.mkdir(exist_ok=True)
    scope.update(
      build=VERSION,parent=OLD_VERSION,parent_commit=PARENT_COMMIT,changed_files=changed,
      native_engine_sha256=NATIVE,native_engine_rebuilt=False,
      authorized_delta='Extend true-playing dot to Mobile/Compact/Cards/Focus + Night Cinema amber; preserve TV Grid/session truth',
      visual_reference_locked=True,physical_device_verified=False,status='TEST CANDIDATE'
    )
    (out/'scope.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103236 all-view playing indicator applied over exact 2103235 source')
if __name__=='__main__':main()
