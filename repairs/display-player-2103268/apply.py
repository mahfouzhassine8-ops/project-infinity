#!/usr/bin/env python3
"""Narrow forward Display/player repair over the exact locked 2103267 source."""
from pathlib import Path
import argparse,hashlib,json,re,difflib
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PARENT_HASH='d3fcd9e9c027912c0ded7034ddfed4cacb9e478b98ebaead8773de05ed28612a'
PARENT_APK='686d606534906358d35934bf6430972279efeab387731b4178d2dfbd2fe12070'
PARENT_COMMIT='292351efa4e0840c1f01b343a81e62b8905ba3f0'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,old,new):
    assert s.count(old)==1,(old[:100],s.count(old));return s.replace(old,new,1)
def span(s,name):
    matches=list(re.finditer(r'^  (?:private|public|protected|static) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',s,re.M))
    assert len(matches)==1,(name,len(matches));start=matches[0].start();p=s.index('{',start);depth=0;state='code';i=p
    while i<len(s):
        c=s[i];n=s[i:i+2]
        if state=='line':
            if c=='\n':state='code'
        elif state=='comment':
            if n=='*/':state='code';i+=1
        elif state in ('"',"'"):
            if c=='\\':i+=1
            elif c==state:state='code'
        elif n=='//':state='line';i+=1
        elif n=='/*':state='comment';i+=1
        elif c in ('"',"'"):state=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return start,i+1
        i+=1
    raise ValueError(name)
def member(s,name,new):
    a,b=span(s,name);return s[:a]+new.rstrip()+s[b:]
HELPERS=r'''
  private boolean cobraDisplaySheet(String kind){
    return "channel-aspect".equals(kind)||"aspect".equals(kind)||"default-aspect".equals(kind);
  }
  private String cobraDisplayDescription(int mode){
    switch(mode){
      case -1:return "Follow the current default • no channel override";
      case 0:return "Fill fullscreen • preserve proportions • center crop";
      case 1:case 13:return "Fill pane • preserve proportions • minimum center crop";
      case 12:return "Balanced fit • reduced black bands • bounded crop";
      case 2:case 3:return "Use the labeled shape • may reshape the source";
      case 4:case 5:case 6:return "Widen whole-frame fit horizontally • intentional stretch";
      case 7:return "Width 124% • height 84% • intentional reshape";
      case 8:case 9:case 10:return "Centered zoom of whole-frame fit • preserve proportions";
      case 11:return "Width and height independently • saved for this channel";
      default:return "";
    }
  }
  private void cobraRevealDisplaySelection(LinearLayout rows){
    FrameLayout owner=mCobraActionSheet;
    rows.post(()->{
      if(owner!=mCobraActionSheet||!cobraDisplaySheet(mCobraSheetKind)||!rows.isAttachedToWindow())return;
      View selected=null;for(int i=0;i<rows.getChildCount();i++)if(rows.getChildAt(i).isSelected()){selected=rows.getChildAt(i);break;}
      if(selected==null)return;View body=rows;while(body.getParent() instanceof View&&!(body.getParent() instanceof ScrollView))body=(View)body.getParent();
      if(body.getParent() instanceof ScrollView&&body instanceof android.view.ViewGroup){
        android.graphics.Rect rect=new android.graphics.Rect();selected.getDrawingRect(rect);
        ((android.view.ViewGroup)body).offsetDescendantRectToMyCoords(selected,rect);
        ((ScrollView)body.getParent()).requestChildRectangleOnScreen(body,rect,true);
      }
    });
  }
  private final class CobraPlayerDrawerRow extends FrameLayout{
    final Button button=cobraTextButton("",true,()->{});final CobraPlayingDot playing=new CobraPlayingDot();
    CobraPlayerDrawerRow(){super(InfinityLiveActivity.this);setFocusable(true);setDescendantFocusability(FOCUS_BLOCK_DESCENDANTS);setOnClickListener(v->button.performClick());setOnLongClickListener(v->button.performLongClick());button.setDuplicateParentStateEnabled(true);button.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);addView(button,new FrameLayout.LayoutParams(-1,-1));FrameLayout.LayoutParams dot=new FrameLayout.LayoutParams(dp(18),dp(18),Gravity.RIGHT|Gravity.CENTER_VERTICAL);dot.rightMargin=dp(10);playing.setTag("cobra_player_playing_dot");addView(playing,dot);}
    void bind(Channel channel){playing.bind(channel);setTag("cobra-player-channel-row:"+channel.id);button.setTag("cobra-player-channel:"+channel.id);}
    void group(){playing.bind(null);setTag(null);button.setTag(null);}
    void refreshPlaying(){playing.sync();}
  }
'''
def transform(s):
    s=once(s,'    if(cobraLiveChannel(mPlaying)){cobraShowChannelAspect(mPlaying);return;}',
        '    closeCobraPlayerDrawer();closeCobraMultiPicker(false);\n    if(cobraLiveChannel(mPlaying)){cobraShowChannelAspect(mPlaying);return;}')
    s=member(s,'showCobraAspectPicker',r'''  private void showCobraAspectPicker() {
    if(mPlayer==null||mCobraPlayerLocked)return;
    closeCobraPlayerDrawer();closeCobraMultiPicker(false);
    if(cobraLiveChannel(mPlaying)){cobraShowChannelAspect(mPlaying);return;}
    LinearLayout rows=cobraOpenSheet("Aspect / Display","Fullscreen fitting follows the actual pane. Preview and PiP keep the complete picture.","aspect");
    final int[] modes={12,13,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int mode:modes){final int selected=mode;cobraAddDetail(rows,"aspect",cobraAspectLabel(mode),mode==11?"Width and height independently • global setting":cobraDisplayDescription(mode),"cobra-player-aspect:"+mode,mAspectMode==mode,()->{
      mAspectMode=selected;mPrefs.edit().putInt(COBRA_ASPECT_MODE,selected).apply();applyCobraAspectTransform();if(selected==11)showCobraCustomAspectEditor();else showCobraAspectPicker();
    });}cobraRevealDisplaySelection(rows);
  }''')
    s=member(s,'cobraShowChannelAspect',r'''  private void cobraShowChannelAspect(Channel channel){
    if(!cobraLiveChannel(channel))return;final String key=cobraPreferenceKey(channel);CobraChannelPreferences prefs=cobraReadPreferences(key);
    LinearLayout rows=cobraOpenSheet("Channel display",channel.name,"channel-aspect");
    final int[] modes={12,13,-1,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int value:modes){final int selected=value;
      cobraAddDetail(rows,"aspect",selected<0?"Inherit default":cobraAspectLabel(selected),cobraDisplayDescription(selected),"cobra-channel-aspect:"+selected,prefs.aspect==selected,()->{
        CobraChannelPreferences p=cobraReadPreferences(key);p.aspect=selected;if(cobraSavePreferences(channel,key,p,false)){if(selected==11)cobraShowChannelCustomAspect(channel);else cobraShowChannelAspect(channel);}
      });
    }cobraRevealDisplaySelection(rows);
  }''')
    a,b=span(s,'cobraShowPlaybackDefaults');default=s[a:b]
    default=once(default,'cobraAspectLabel(selected),null,"cobra-default-aspect:"','cobraAspectLabel(selected),cobraDisplayDescription(selected),"cobra-default-aspect:"')
    default=once(default,'cobraShowPlaybackDefaults();});}\n    });','cobraShowPlaybackDefaults();});}cobraRevealDisplaySelection(choices);\n    });')
    default=once(default,'Inherited in fullscreen. Previews keep Best Fit. Multi-View tiles inherit Fold Fit / Fold Fill unless a channel overrides them.','Inherited in fullscreen. Previews keep the complete picture. Multi-View tiles inherit Fold Fit / Fold Fill unless a channel overrides them.')
    s=s[:a]+default+s[b:]
    a,b=span(s,'cobraShowChannelCustomAspect');old=s[a:b]
    new=old[:-1]+r'''  cobraAddDetail(rows,"recent","Reset width & height","Return both to 100%","cobra-channel-custom-reset",false,()->{
      CobraChannelPreferences p=cobraReadPreferences(key);p.aspect=11;p.x=1f;p.y=1f;
      if(cobraSavePreferences(channel,key,p,false))cobraShowChannelCustomAspect(channel);
    });
  }'''
    s=s[:a]+new+s[b:]
    s=once(s,'    closeCobraPlayerDrawer();if("player-settings".equals(mCobraSheetKind))',
        '    closeCobraPlayerDrawer();closeCobraMultiPicker(false);if("player-settings".equals(mCobraSheetKind))')
    s=once(s,'    float[] scale=CobraFoldAspectPolicy.foldMode(mode)',
        '    // Restore full-pane fullscreen Best Fit without changing Pro/preview or PiP safety fitting.\n    float[] scale=mode==0&&player==mPlayer&&mPlayerOverlay!=null&&!mInPictureInPicture\n        ?CobraFoldAspectPolicy.fill(size.width,size.height,size.pixelWidthHeightRatio,texture.getWidth(),texture.getHeight())\n        :CobraFoldAspectPolicy.foldMode(mode)')
    s=once(s,'    transport.addView(prev,new LinearLayout.LayoutParams(',
        '    boolean narrowTransport=width-left-right<dp(344);\n    transport.setTag("cobra_player_transport");\n    transport.addView(prev,new LinearLayout.LayoutParams(')
    s=once(s,'dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.16",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.17",56))',
        'dp(narrowTransport?48:vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.16",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.17",56))')
    s=once(s,'transport.addView(rewind,new LinearLayout.LayoutParams(dp(52),dp(52)))',
        'transport.addView(rewind,new LinearLayout.LayoutParams(dp(narrowTransport?48:52),dp(52)))')
    s=once(s,'new LinearLayout.LayoutParams(dp(shortScreen?56:68),dp(shortScreen?56:68));pp.leftMargin=dp(14);pp.rightMargin=dp(14)',
        'new LinearLayout.LayoutParams(dp(narrowTransport?52:shortScreen?56:68),dp(shortScreen?56:68));pp.leftMargin=dp(narrowTransport?2:14);pp.rightMargin=dp(narrowTransport?2:14)')
    s=once(s,'transport.addView(live,new LinearLayout.LayoutParams(dp(52),dp(52)))',
        'transport.addView(live,new LinearLayout.LayoutParams(dp(narrowTransport?48:52),dp(52)))')
    s=once(s,'dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.20",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.21",56))',
        'dp(narrowTransport?48:vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.20",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.21",56))')
    s=once(s,'    scroll.setFillViewport(false);scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);',r'''    scroll.setFillViewport(false);scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    if(cobraDisplaySheet(kind)){scroll.setTag("cobra_display_scroll");scroll.setVerticalScrollBarEnabled(true);scroll.setScrollbarFadingEnabled(false);scroll.setVerticalFadingEdgeEnabled(true);scroll.setFadingEdgeLength(dp(18));}''')
    s=once(s,'    panel.addView(scroll,new LinearLayout.LayoutParams(-1,-2));',r'''    panel.addView(scroll,new LinearLayout.LayoutParams(-1,-2));
    if(cobraDisplaySheet(kind)){TextView cue=cobraText("Scroll for more Display options",dark?0xffc4e6f1:0xff254b66,12);cue.setTag("cobra_display_scroll_cue");cue.setGravity(Gravity.CENTER);cue.setPadding(dp(4),dp(6),dp(4),dp(4));panel.addView(cue,new LinearLayout.LayoutParams(-1,-2));}''')
    s=once(s,'      public View getView(int p,View recycled,android.view.ViewGroup parent){Button row=recycled instanceof Button?(Button)recycled:cobraTextButton("",true,()->{});row.setTextSize',
        '      public View getView(int p,View recycled,android.view.ViewGroup parent){CobraPlayerDrawerRow holder=recycled instanceof CobraPlayerDrawerRow?(CobraPlayerDrawerRow)recycled:new CobraPlayerDrawerRow();Button row=holder.button;row.setTextSize')
    s=once(s,'dp(vtheme().dimension("cobra.cobraRenderPlayerDrawer.dimensions.2",12)),0);row.setGravity',
        'dp(36),0);row.setGravity')
    s=once(s,'row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(groups?52:82)));',
        'holder.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(groups?52:82)));')
    s=once(s,'if(groups){String group=names.get(p);row.setText(group);',
        'if(groups){holder.group();String group=names.get(p);row.setText(group);')
    s=once(s,'else {Channel c=channels.get(p);GuideProgram now=cobraCurrentProgram(c),next=cobraNextProgram(c);row.setText',
        'else {Channel c=channels.get(p);holder.bind(c);GuideProgram now=cobraCurrentProgram(c),next=cobraNextProgram(c);row.setText')
    s=once(s,'return true;});}\n        return row;}});\n    mCobraPlayerDrawerList.setAlpha',
        'return true;});}\n        holder.setSelected(row.isSelected());holder.setContentDescription(row.getText());return holder;}});\n    mCobraPlayerDrawerList.setAlpha')
    s=once(s,'  private void cobraRefreshPlayingIndicators(){\n    if(mCobraGuideList==null)return;',r'''  private void cobraRefreshPlayingIndicators(){
    if(mCobraPlayerDrawerList!=null)for(int i=0;i<mCobraPlayerDrawerList.getChildCount();i++){
      View child=mCobraPlayerDrawerList.getChildAt(i);if(child instanceof CobraPlayerDrawerRow)((CobraPlayerDrawerRow)child).refreshPlaying();
    }
    if(mCobraGuideList==null)return;''')
    return s[:s.rfind('\n}')]+HELPERS+s[s.rfind('\n}'):]
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    shell=a.root/'shell-kodi';f=shell/ACTIVITY;before=f.read_text();assert sha(f.read_bytes())==PARENT_HASH
    after=transform(before);f.write_text(after)
    g=shell/'tools/android/packaging/xbmc/build.gradle.in';g.write_text(once(g.read_text(),'versionCode 2103267','versionCode 2103268').replace('1.0.9-Cobra-Playing-Dot-Restore-RC1','1.0.9-Cobra-Display-Player-RC1'))
    script=a.root/'scripts/infinity_background_resume.py';v=script.read_text();v=once(v,'VERSION_CODE = 2103267','VERSION_CODE = 2103268');v=once(v,"RELEASE = '1.0.9-Cobra-Playing-Dot-Restore-RC1'","RELEASE = '1.0.9-Cobra-Display-Player-RC1'");v=once(v,"BASE_COMMIT = '490e995e77ad1d37c5b64fd11315e6f4a704952c'","BASE_COMMIT = '"+PARENT_COMMIT+"'");v=once(v,"BASE_APK_SHA256 = '4624c1ca66d29a4ac8c5f63892ca9669e6ef757894fe6a2e0b4c4d356e3ec455'","BASE_APK_SHA256 = '"+PARENT_APK+"'");script.write_text(v)
    package=a.root/'scripts/package_background_resume.py';v=package.read_text().replace('Infinity-2103267-Cobra-Playing-Dot-Restore-RC1','Infinity-2103268-Cobra-Display-Player-RC1').replace("'base_run':36675691445","'base_run':36684966394").replace("ROOT/'repairs/cobra-playing-dot-restore-2103267/DEVICE-TEST.md'","ROOT/'repairs/display-player-2103268/DEVICE-TEST.md'").replace('PASS: Cobra playing-dot restore over exact locked 2103266','PASS: Display/player repair over exact locked 2103267');package.write_text(v)
    receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=2103268,release='1.0.9-Cobra-Display-Player-RC1',candidate_locked=False,physical_device_verified=False)
    for n in [ACTIVITY,'tools/android/packaging/xbmc/build.gradle.in']:r['files'][n]['after']=sha((shell/n).read_bytes())
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    (a.out/'display-player.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='locked-2103267/'+ACTIVITY,tofile='candidate-2103268/'+ACTIVITY)))
    (a.out/'InfinityLiveActivity-2103267-before.java.in').write_text(before);(a.out/'InfinityLiveActivity-2103268-after.java.in').write_text(after)
    print('Applied scoped Display/player repairs over exact 2103267; no Pro or skin source changed.')
if __name__=='__main__':main()
