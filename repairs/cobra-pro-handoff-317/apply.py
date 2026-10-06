#!/usr/bin/env python3
"""Cobra Pro-only edits over the exact locked 2103317 source export."""
from pathlib import Path
import sys

root=Path(sys.argv[1]);src=root/'tools/android/packaging/xbmc/src'
def one(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a))
    return s.replace(a,b)
def method(s,start,end,new):
    a=s.index(start);b=s.index(end,a)
    return s[:a]+new+'\n'+s[b:]

p=src/'InfinityLiveActivity.java.in';s=p.read_text()
s=one(s,'  private String mCobraProSource="FROM CHANNELS";','  private String mCobraProSource="FROM CHANNELS";\n  private boolean mCobraProPlaybackOwned,mCobraProHeroBrowsing;')
s=one(s,'  private void cobraDrawerView(LinearLayout items){','  private void cobraDrawerView(LinearLayout items){\n    if(cobraTouchFirstDevice())return;')
s=one(s,'    rows.addView(cobraSheetRow("favorite","My Teams",cobraSportsChoices().myTeams().size()+" teams • favorite, pin or follow",false,dark,this::showCobraSportsFavoriteLeagues));\n','')
s=one(s,'    LinearLayout rows=cobraOpenSheet("Sports settings","Teams • reminders • scores • Multi-View","sports-settings");','    LinearLayout rows=cobraOpenSheet("Sports settings","Reminders • scores • Multi-View","sports-settings");')
s=one(s,'    if(session==null){playChannel(channel);return;}','    if(session==null){cobraPlayChannelFullscreen(channel);return;}')
s=one(s,'  private void playChannel(Channel channel) {','  private void playChannel(Channel channel) {\n    if(mCobraProActive&&"focus".equals(mCobraGuideStyle)&&mPlayerOverlay==null&&mMultiOverlay==null){cobraProPlayChannel(channel);return;}\n    cobraPlayChannelFullscreen(channel);\n  }\n\n  private void cobraPlayChannelFullscreen(Channel channel) {')
s=one(s,'    // The guide shell and its original TextureView remain mounted behind fullscreen.','    if(mCobraProActive){mCobraProPlaybackOwned=true;mCobraProHeroBrowsing=false;mCobraProState=COBRA_PRO_WATCHING;mCobraPreviewMuted=cobraMediaMuted(session);cobraProSelectPlayingSlot(channel);}\n    // The guide shell and its original TextureView remain mounted behind fullscreen.')
s=one(s,'    if(mCobraProActive){\n      if(mCobraProObserved!=null','    if(mCobraProActive){\n      mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;\n      if(mCobraProObserved!=null')
s=one(s,'    if(!mCobraProActive)return;cobraProSetSportsCompact(false,false);mCobraProSportsAdapter=null;mCobraProActive=false;','    if(!mCobraProActive)return;cobraProSetSportsCompact(false,false);mCobraProSportsAdapter=null;mCobraProActive=false;mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;')
s=one(s,'    if(!mCobraProActive)return;cobraProSetSportsCompact(false,false);','    if(!mCobraProActive)return;if(mCobraProPlaybackOwned){mCobraProPriorAutoplayAllowed=mCobraPreviewAutoplayAllowed;ExoPlayer current=mCobraPreviewPlayer;if(current!=null){mCobraProPriorPlaying=current.getPlayWhenReady();mCobraProPriorMuted=cobraMediaMuted(current);}}cobraProSetSportsCompact(false,false);')
s=one(s,'    if(first){mCobraProActive=true;mCobraProState=COBRA_PRO_RESTING;','    if(first){mCobraProActive=true;mCobraProState=COBRA_PRO_RESTING;mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;')
# Explicit Play owns the stream. Focus/browsing owns only the carousel selection.
s=method(s,'  private void cobraProRetuneResting(','  private void cobraProPauseAndMute(){','''  private void cobraProSelectPlayingSlot(Channel channel){
    int index=cobraFindProSlot(channel);if(index<0){mCobraProSlots.add(0,new CobraProSlot(cobraProSourceForSelection(channel),channel));index=0;}
    mCobraProHeroIndex=index;mCobraProSource=cobraProSourceForSelection(channel);
  }
  private void cobraProPlayChannel(Channel channel){
    if(channel==null||!cobraChannelAllowed(channel)||!isCobraAsyncAlive())return;
    cobraProSelectPlayingSlot(channel);mCobraProHeroBrowsing=false;mCobraProPlaybackOwned=true;mCobraProState=COBRA_PRO_WATCHING;
    mCobraPreviewMuted=false;mCobraPreviewAutoplayAllowed=true;
    mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);mGuidePreviewArmed=true;
    if(mCobraPreviewPlayer==null||!cobraChannelKey(channel).equals(mCobraPreviewSessionKey))startCobraPreview(channel);
    ExoPlayer player=mCobraPreviewPlayer;if(player!=null){if(cobraMediaMuted(player))cobraUserUnmute(player);if(!player.getPlayWhenReady())cobraUserPlay(player);}
    cobraRememberChannelTransition(channel);cobraSetProState(COBRA_PRO_WATCHING,true);cobraRefreshProHero();
    if(mCobraProHeroUi!=null)mCobraProHeroUi.revealControls();
  }
  private void cobraProRetuneResting(Channel channel,String source,boolean animate){
    if(channel==null)return;mCobraProSource=source==null||source.isEmpty()?"FROM CHANNELS":source;
    mCobraProHeroBrowsing=mCobraProPlaybackOwned;
    if(!mCobraProPlaybackOwned){stopCobraPreviewPlayerOnly();mCobraPreviewMuted=true;mCobraPreviewAutoplayAllowed=false;mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);mGuidePreviewArmed=true;}
    mPrefs.edit().putString("cobra_pro_hero_channel",channel.id).putString("cobra_pro_hero_source",mCobraProSource).apply();
    cobraRefreshProHero();cobraSetProState(mCobraProPlaybackOwned?COBRA_PRO_WATCHING:COBRA_PRO_RESTING,animate);
  }
''')
s=one(s,'    if(!mCobraProActive)return;Channel channel=cobraProCurrentChannel();if(channel==null)return;mCobraPreviewMuted=true;mCobraPreviewAutoplayAllowed=true;','    if(!mCobraProActive)return;Channel channel=cobraProCurrentChannel();if(channel==null)return;mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;mCobraProState=COBRA_PRO_PREVIEW;mCobraPreviewMuted=true;mCobraPreviewAutoplayAllowed=true;')
s=one(s,'    if(!mCobraProActive)return;if(mCobraPreviewPlayer==null)cobraProPreview();','    if(!mCobraProActive)return;if(mCobraPreviewPlayer==null)cobraProPreview();mCobraProPlaybackOwned=true;mCobraProHeroBrowsing=false;')
s=one(s,'    mCobraProHeroUi.bind(data,mCobraProHeroIndex,mCobraProSlots.size());','    mCobraProHeroUi.browsing(mCobraProHeroBrowsing);mCobraProHeroUi.bind(data,mCobraProHeroIndex,mCobraProSlots.size());\n    if(mCobraProPlaybackOwned)mCobraProHeroUi.player[1].setSelected(mGuidePreviewChannel!=null&&mFavorites.contains(mGuidePreviewChannel.id));')
s=one(s,'      public void preview(){cobraProPreview();}','      public void controlsChanged(){cobraLayoutGuide();}\n      public void preview(){cobraProPreview();}')
s=one(s,'    CobraModeLayout.box(layout.rail,0,0,0,0);CobraModeLayout.box(layout.directory,0,0,0,0);CobraModeLayout.box(layout.footer,0,0,0,0);','    if(mCobraProState==COBRA_PRO_WATCHING&&mCobraProHeroUi!=null&&!mCobraProHeroUi.controlsVisible&&!mCobraProHeroBrowsing){int delta=Math.min(74,Math.max(0,layout.video[3]-112));layout.video[3]-=delta;if(layout.details[3]>0)layout.details[1]-=delta;if(layout.browser[1]>layout.video[1]){layout.browser[1]-=delta;layout.browser[3]+=delta;}}\n    CobraModeLayout.box(layout.rail,0,0,0,0);CobraModeLayout.box(layout.directory,0,0,0,0);CobraModeLayout.box(layout.footer,0,0,0,0);')
s=one(s,'CobraProUi.Program data=sports?cobraProSportsProgram(cobraProCurrentSportsGame()):cobraProProgram(mGuidePreviewChannel);','CobraProUi.Program data=sports?cobraProSportsProgram(cobraProCurrentSportsGame()):cobraProProgram(cobraProCurrentChannel());')
s=one(s,'mCobraProHeroUi.playback(!sports&&player!=null&&player.getPlayWhenReady(),!sports&&(player==null||cobraMediaMuted(player)),!sports&&player!=null&&cobraCaptionsRequested(player),!sports&&player!=null);','mCobraProHeroUi.playback(player!=null&&player.getPlayWhenReady(),player==null||cobraMediaMuted(player),player!=null&&cobraCaptionsRequested(player),player!=null);')
s=one(s,'      if(preferred!=null&&preferred.live()&&cobraSportsRank(preferred)<2&&mCobraProState==COBRA_PRO_RESTING){int slot=cobraProSportsSlotIndex();if(slot>=0){mCobraProHeroIndex=slot;cobraProRetuneSports(null,true);}}','      int slot=cobraProSportsSlotIndex();if(slot>=0){mCobraProHeroIndex=slot;cobraProRetuneSports(null,true);}')
s=method(s,'  private void cobraProRetuneSports(','  private void cobraProSportsWatch(){','''  private void cobraProRetuneSports(CobraSportsGame requested,boolean animate){
    if(requested==null)mCobraProSportsManualSelection=false;CobraSportsGame game=requested==null?cobraProPreferredSportsGame():requested;
    mCobraProSource="LIVE SPORTS";mCobraProSportsResolvedChannel=null;mCobraProSportsResolvingId="";mCobraProHeroBrowsing=mCobraProPlaybackOwned;
    mCobraProSportsGameId=game==null?"":game.id;
    if(!mCobraProPlaybackOwned){stopCobraPreviewPlayerOnly();mCobraPreviewMuted=true;mCobraPreviewAutoplayAllowed=false;mGuidePreviewChannel=null;mGuidePreviewKey="";mGuidePreviewArmed=false;}
    cobraRefreshProHero();cobraSetProState(mCobraProPlaybackOwned?COBRA_PRO_WATCHING:COBRA_PRO_RESTING,animate);
    if(game==null)return;final String gameId=game.id,profile=mFeatures.activeProfileId();mCobraProSportsResolvingId=gameId;
    final ArrayList<CobraSportsChannelInfo> snapshot=cobraSportsChannelSnapshot();
    submitCobraIo(()->{ArrayList<CobraSportsMatch> matches=cobraSportsResolve(game,snapshot);publishCobraUi(()->{
      if(!mCobraProActive||!cobraProSportsHeroActive()||!profile.equals(mFeatures.activeProfileId())||!gameId.equals(mCobraProSportsGameId)||!gameId.equals(mCobraProSportsResolvingId))return;
      mCobraProSportsResolvingId="";if(cobraSportsUniqueStrong(matches))mCobraProSportsResolvedChannel=matches.get(0).channel;
      cobraRefreshProHero();
    });});
  }
''')
s=one(s,'"No games live right now"','"No games are live right now."')
# A date can be published while its time is explicitly unconfirmed.
s=one(s,'long startMs=0L;boolean completed=false;','long startMs=0L;boolean completed=false,timeConfirmed=true;')
s=one(s,'g.completed=type!=null&&type.optBoolean("completed",false);JSONObject venue=', 'g.completed=type!=null&&type.optBoolean("completed",false);g.timeConfirmed=g.startMs>0&&e.optBoolean("timeValid",true)&&c.optBoolean("timeValid",true)&&!g.detail.toUpperCase(Locale.US).contains("TBD")&&!g.detail.toUpperCase(Locale.US).contains("TBA");JSONObject venue=')
s=one(s,'data.time=game.startMs>0?new SimpleDateFormat("h:mm a z",Locale.getDefault()).format(new Date(game.startMs)):"Time TBA";', 'data.time=game.startMs>0&&game.timeConfirmed?new SimpleDateFormat("h:mm a z",Locale.getDefault()).format(new Date(game.startMs)):"Time TBA";')
s=one(s,'game.finalGame()?"FINAL":cobraSportsClock(game.startMs);','game.finalGame()?"FINAL":game.timeConfirmed?cobraSportsClock(game.startMs):(game.startMs>0?new SimpleDateFormat("EEE • MMM d, yyyy",Locale.getDefault()).format(new Date(game.startMs))+" • Time TBA":"Date and time TBA");')
# A resolver result is metadata; only a successfully allocated second player is a launch.
s=one(s,'selectCobraMultiChannel(channel);mCobraSportsMultiAssignments.put(channel.id,game);mMain.post(this::cobraSportsRefreshMultiOverlays);return;','cobraLaunchMultiSportsChannel(channel,current);return;')
s=one(s,'selectCobraMultiChannel(channel);mCobraSportsMultiAssignments.put(channel.id,latest);mMain.post(InfinityLiveActivity.this::cobraSportsRefreshMultiOverlays);','cobraLaunchMultiSportsChannel(channel,latest);')
s=one(s,'  private void cobraPickMultiSportsGame(','''  private boolean cobraLaunchMultiSportsChannel(Channel channel,CobraSportsGame game){
    if(channel==null||game==null||!game.live()||!cobraChannelAllowed(channel))return false;
    try{selectCobraMultiChannel(channel);}catch(RuntimeException error){toast("Unable to open this broadcast; choose another channel");return false;}
    CobraVideoTile tile=mCobraTiles.get(channel.id);
    if(mMultiOverlay==null||mMultiChannels==null||mMultiChannels.length<2||tile==null||tile.player==null){toast("Broadcast screen unavailable; choose another channel");return false;}
    mCobraSportsMultiAssignments.put(channel.id,game);mMain.post(this::cobraSportsRefreshMultiOverlays);return true;
  }
  private void cobraPickMultiSportsGame(''')
# The hero has navigation and real programme identity; scores and matchup marks remain in game rows.
s=one(s,'data.title=cobraSportsMatchup(game);data.schedule=game.live()||game.finalGame()?cobraSportsScoreLine(game):cobraSportsClock(game.startMs);data.next=cobraSportsMeta(game);','data.title="Live Sports";data.schedule=game.leagueLabel;data.next="Select a game below to watch";')
# Plain page backgrounds previously erased the ambient finish at each Pro restyle.
s=one(s,'    if (mCobraGuideBrowser != null) mCobraGuideBrowser.setBackgroundColor(page);','    if (mCobraGuideBrowser != null) mCobraGuideBrowser.setBackgroundColor(page);\n    if(mCobraEffects!=null){mCobraEffects.backdrop(mCobraGuideShell,page,mCobraAmbientTint,cobraStaticAmbientMode());mCobraEffects.backdrop(mCobraGuideBrowser,page,mCobraAmbientTint,cobraStaticAmbientMode());}')
# LIVE availability follows the seekable default edge, rather than seekable alone.
s=method(s,'  private boolean cobraCanGoLive(){','  private void cobraUpdateLiveRewindControls(){','''  private boolean cobraCanGoLive(){
    if(!cobraChannelRewindEnabled(mPlaying)||mPlayer==null||mPlaying==null||!cobraLiveChannel(mPlaying))return false;
    if(mCobraProviderCatchupActive)return true;
    if(!cobraLiveWindowSeekable())return false;
    try{androidx.media3.common.Timeline timeline=mPlayer.getCurrentTimeline();
      if(!timeline.isEmpty()){androidx.media3.common.Timeline.Window window=timeline.getWindow(mPlayer.getCurrentMediaItemIndex(),new androidx.media3.common.Timeline.Window());long edge=window.getDefaultPositionMs();if(edge!=C.TIME_UNSET&&edge>=0)return edge-Math.max(0L,mPlayer.getCurrentPosition())>1500L;}
    }catch(RuntimeException unavailable){}
    return false;
  }
''')
s=one(s,'    cobraUpdatePlaybackLabels();cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();\n  }','    cobraUpdatePlaybackLabels();cobraUpdateTimeshiftSeek();cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();\n  }')
# Retain Button labels, layout, theme hooks, and the exact power action bodies.
s=one(s,'    Button switchInfinity = action(vtheme().copy("cobra.showCobraPowerMenu.copy.2","∞  Switch to Infinity"));\n    Button exit = action(vtheme().copy("cobra.showCobraPowerMenu.copy.3","⏻  Exit"));\n    Button cancel = action(vtheme().copy("cobra.showCobraPowerMenu.copy.4","Cancel"));','''    CobraProUi.PowerIcon switchIcon=new CobraProUi.PowerIcon(this,"infinity",cobraThemeColor("text",mTheme.text));
    CobraProUi.PowerIcon exitIcon=new CobraProUi.PowerIcon(this,"exit",cobraThemeColor("text",mTheme.text));
    CobraProUi.PowerIcon cancelIcon=new CobraProUi.PowerIcon(this,"cancel",cobraThemeColor("text",mTheme.text));
    Button switchInfinity = action(vtheme().copy("cobra.showCobraPowerMenu.copy.2","Switch to Infinity").replaceFirst("^∞\\\\s*", ""));
    Button exit = action(vtheme().copy("cobra.showCobraPowerMenu.copy.3","Exit").replaceFirst("^⏻\\\\s*", ""));
    Button cancel = action(vtheme().copy("cobra.showCobraPowerMenu.copy.4","Cancel"));
    Button[] powerButtons={switchInfinity,exit,cancel};CobraProUi.PowerIcon[] powerIcons={switchIcon,exitIcon,cancelIcon};
    for(int i=0;i<powerButtons.length;i++){final CobraProUi.PowerIcon icon=powerIcons[i];Button button=powerButtons[i];button.setCompoundDrawablesRelativeWithIntrinsicBounds(icon,null,null,null);button.setCompoundDrawablePadding(dp(12));button.setTag("cobra_power_"+icon.kind);button.setOnTouchListener((v,event)->{icon.pressed(event.getActionMasked()==android.view.MotionEvent.ACTION_DOWN);return false;});}
''')
s=one(s,'    switchInfinity.setOnClickListener(v -> {\n      closeCobraPowerMenu();','    switchInfinity.setOnClickListener(v -> switchIcon.activate(switchInfinity,()->{\n      closeCobraPowerMenu();')
s=one(s,'      returnToInfinity();\n    });\n    exit.setOnClickListener(v -> {','      returnToInfinity();\n    }));\n    exit.setOnClickListener(v -> exitIcon.activate(exit,()->{')
s=one(s,'      finishAndRemoveTask();\n    });\n    cancel.setOnClickListener(v -> closeCobraPowerMenu());','      finishAndRemoveTask();\n    }));\n    cancel.setOnClickListener(v -> cancelIcon.activate(cancel,()->closeCobraPowerMenu()));')
p.write_text(s)

p=src/'CobraProUi.java.in';s=p.read_text()
s=one(s,'  interface Actions { void preview();','  interface Actions { default void controlsChanged(){} void preview();')
s=one(s,'    final Actions actions;final Art art;','    boolean browsing,controlsVisible=true;\n    final Runnable collapse=this::collapseControls;\n    void collapseControls(){if(state==WATCHING&&!isAccessibilityFocused()&&!hasFocus()){controlsVisible=false;applyModeVisibility();requestLayout();actions.controlsChanged();}}\n    void browsing(boolean value){if(browsing!=value){browsing=value;controlsVisible=false;applyModeVisibility();requestLayout();}}\n    void revealControls(){controlsVisible=true;applyModeVisibility();requestLayout();actions.controlsChanged();removeCallbacks(collapse);if(state==WATCHING)postDelayed(collapse,4000L);}\n    final Actions actions;final Art art;')
s=one(s,'void applyModeVisibility(){boolean sports=sportsMode&&state!=WATCHING;preview.setVisibility(!sports&&state==RESTING?VISIBLE:GONE);unmute.setVisibility(!sports&&state==PREVIEW?VISIBLE:GONE);muted.setVisibility(GONE);muteIcon.setVisibility(GONE);sportsWatch.setVisibility(sports?VISIBLE:GONE);sportsStats.setVisibility(sports?VISIBLE:GONE);sportsMulti.setVisibility(sports?VISIBLE:GONE);for(Action a:player)a.setVisibility(!sportsMode&&state==WATCHING?VISIBLE:GONE);}', 'void applyModeVisibility(){boolean watching=state==WATCHING,show=watching&&controlsVisible,sports=sportsMode&&(!watching||browsing&&!show);preview.setVisibility(!sports&&((!watching&&state==RESTING)||(browsing&&!show))?VISIBLE:GONE);unmute.setVisibility(!sports&&state==PREVIEW?VISIBLE:GONE);muted.setVisibility(GONE);muteIcon.setVisibility(GONE);sportsWatch.setVisibility(sports?VISIBLE:GONE);sportsStats.setVisibility(sports?VISIBLE:GONE);sportsMulti.setVisibility(sports?VISIBLE:GONE);for(Action a:player)a.setVisibility(show?VISIBLE:GONE);transport.setVisibility(watching&&!controlsVisible&&!browsing?GONE:VISIBLE);}')
s=one(s,'      if(sportsMode){logo.setVisibility(GONE);info.setVisibility(GONE);sportsAway.setVisibility(d.live?VISIBLE:GONE);sportsHome.setVisibility(d.live?VISIBLE:GONE);sportsMatchup.setVisibility(d.live?VISIBLE:GONE);sportsScore.setVisibility(d.live?VISIBLE:GONE);sportsMeta.setVisibility(d.live?VISIBLE:GONE);','      if(sportsMode){logo.setVisibility(GONE);info.setVisibility(VISIBLE);info.bind(d,art);sportsAway.setVisibility(GONE);sportsHome.setVisibility(GONE);sportsMatchup.setVisibility(GONE);sportsScore.setVisibility(GONE);sportsMeta.setVisibility(GONE);')
s=one(s,'      if(old!=state)shade.setBackground','      if(old!=state){controlsVisible=true;removeCallbacks(collapse);if(state==WATCHING)postDelayed(collapse,4000L);}\n      if(old!=state)shade.setBackground')
s=one(s,'@Override public boolean performClick(){super.performClick();return true;}','@Override public boolean performClick(){super.performClick();if(state==WATCHING)revealControls();return true;}')
s=one(s,'@Override protected void onDetachedFromWindow(){info.animate().cancel();animationToken++;super.onDetachedFromWindow();}','@Override protected void onDetachedFromWindow(){removeCallbacks(collapse);info.animate().cancel();animationToken++;super.onDetachedFromWindow();}')
s=one(s,'bed=px(getContext(),state==WATCHING?82:80)','bed=px(getContext(),state==WATCHING&&!controlsVisible&&!browsing?0:state==WATCHING?82:80)')
s=one(s,'place(info,0,0,0,0);}\n      else if(info.getParent()==this)', '}\n      if(info.getParent()==this)')
s=one(s,'if(active){p.setColor(CYAN);c.drawRect(den*10,h-den*2,w-den*10,h,p);}','if(isSelected()){p.setColor(CYAN);c.drawRect(den*10,h-den*2,w-den*10,h,p);}\n        if(isFocused()&&!isSelected()){p.setStyle(Paint.Style.STROKE);p.setColor(ink);p.setStrokeWidth(den);c.drawRoundRect(den*3,den*3,w-den*3,h-den*5,den*5,den*5,p);p.setStyle(Paint.Style.FILL);}')
s=one(s,'static final class ChannelRow extends ViewGroup {','static final class ChannelRow extends ViewGroup implements MaterialSurface {\n    public void refreshMaterial(){setBackground(surface(getContext(),light,isSelected(),10));}')
s=one(s,'setBackground(active?surface(getContext(),light,true,10):null);','setBackground(surface(getContext(),light,active,10));')
# Icon-only animation: cancellation/detachment can never execute a stale power action.
s=one(s,'  static String fit(String value,Paint p,float width){','''  static final class PowerIcon extends Drawable {
    final String kind;final Context context;final Paint paint=new Paint(3);final int ink;float progress;boolean down,busy;ValueAnimator animator;
    PowerIcon(Context c,String kind,int ink){context=c;this.kind=kind;this.ink=ink;}
    @Override public int getIntrinsicWidth(){return px(context,28);}@Override public int getIntrinsicHeight(){return px(context,28);}
    void pressed(boolean value){down=value;invalidateSelf();}
    void activate(View owner,Runnable action){
      if(busy)return;busy=true;
      if(!motion()||!owner.isAttachedToWindow()){busy=false;action.run();return;}
      animator=ValueAnimator.ofFloat(0,1);animator.setDuration(280);animator.setInterpolator(new android.view.animation.DecelerateInterpolator());
      animator.addUpdateListener(a->{progress=(float)a.getAnimatedValue();invalidateSelf();});
      animator.addListener(new android.animation.AnimatorListenerAdapter(){boolean cancelled;@Override public void onAnimationCancel(android.animation.Animator a){cancelled=true;}@Override public void onAnimationEnd(android.animation.Animator a){progress=0;down=false;busy=false;invalidateSelf();if(!cancelled&&owner.isAttachedToWindow())action.run();}});
      owner.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){public void onViewAttachedToWindow(View v){}public void onViewDetachedFromWindow(View v){if(animator!=null)animator.cancel();v.removeOnAttachStateChangeListener(this);}});
      animator.start();
    }
    @Override public void draw(Canvas c){Rect b=getBounds();c.save();c.translate(b.left,b.top);c.scale(b.width()/28f,b.height()/28f);
      float pulse=(float)Math.sin(progress*Math.PI);int color=(down||progress>0)?("cancel".equals(kind)?0xffff5a67:CYAN):ink;
      paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(1.9f);paint.setStrokeCap(Paint.Cap.ROUND);paint.setStrokeJoin(Paint.Join.ROUND);paint.setColor(color);paint.setShader(null);
      if("infinity".equals(kind)){c.scale(1+.14f*pulse,1+.14f*pulse,14,14);Path path=new Path();path.moveTo(14,14);path.cubicTo(8,3,1,8,3,16);path.cubicTo(5,23,10,19,14,14);path.cubicTo(20,3,27,8,25,16);path.cubicTo(23,23,18,19,14,14);c.drawPath(path,paint);}
      else if("exit".equals(kind)){c.drawRoundRect(3,4,14,24,2,2,paint);c.save();c.translate(progress*5,0);c.drawLine(10,14,24,14,paint);c.drawLine(20,10,24,14,paint);c.drawLine(20,18,24,14,paint);c.restore();}
      else{c.drawCircle(14,14,10,paint);c.drawLine(10,10,18,18,paint);c.drawLine(18,10,10,18,paint);}c.restore();
    }
    @Override public void setAlpha(int value){paint.setAlpha(value);invalidateSelf();}@Override public void setColorFilter(ColorFilter f){paint.setColorFilter(f);invalidateSelf();}@Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
  static String fit(String value,Paint p,float width){''')
p.write_text(s)
