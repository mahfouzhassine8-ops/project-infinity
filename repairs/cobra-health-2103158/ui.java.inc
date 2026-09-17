  // Native text and vector details scale with display density; no low-resolution menu bitmaps.
  private LinearLayout cobraDetailRow(String icon,String title,String detail,String tag,boolean selected,Runnable action){
    boolean dark=cobraSheetIsDark();LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);
    row.setPadding(dp(10),dp(10),dp(12),dp(10));row.setMinimumHeight(dp(58));row.setBackground(cobraModeSurface(14,true));
    row.setFocusable(true);row.setClickable(true);row.setSelected(selected);row.setTag(tag);
    CobraIconButton glyph=cobraIcon(icon,title,dark,v->{});glyph.setEnabled(false);glyph.setFocusable(false);row.addView(glyph,new LinearLayout.LayoutParams(dp(36),dp(36)));
    LinearLayout text=new LinearLayout(this);text.setOrientation(LinearLayout.VERTICAL);
    TextView heading=cobraText(title,dark?Color.WHITE:cobraModeColor("text"),15);heading.setTypeface(Typeface.create("sans-serif-medium",0));heading.setMaxLines(3);text.addView(heading,new LinearLayout.LayoutParams(-1,-2));
    if(detail!=null&&!detail.isEmpty()){TextView sub=cobraText(detail,dark?0xffb0c2d5:cobraModeColor("muted"),12);sub.setMaxLines(4);text.addView(sub,new LinearLayout.LayoutParams(-1,-2));}
    LinearLayout.LayoutParams body=new LinearLayout.LayoutParams(0,-2,1);body.leftMargin=dp(10);row.addView(text,body);
    if(selected){TextView check=cobraText("✓",cobraModeColor("accent"),18);check.setGravity(Gravity.CENTER);row.addView(check,new LinearLayout.LayoutParams(dp(30),dp(36)));}
    row.setContentDescription(title+(detail==null||detail.isEmpty()?"":", "+detail)+(selected?", selected":""));
    row.setOnClickListener(v->{closeCobraActionSheet();action.run();});return row;
  }
  private void cobraAddDetail(LinearLayout parent,String icon,String title,String detail,String tag,boolean selected,Runnable action){
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(6);parent.addView(cobraDetailRow(icon,title,detail,tag,selected,action),p);
  }
  private TextView cobraInfoText(LinearLayout parent,String value){
    TextView text=cobraText(value,cobraSheetIsDark()?0xffc2d0df:cobraModeColor("muted"),13);text.setPadding(dp(12),dp(10),dp(12),dp(10));text.setLineSpacing(dp(3),1f);parent.addView(text,new LinearLayout.LayoutParams(-1,-2));return text;
  }
  private final class CobraBrandMark extends View {
    final android.graphics.Paint ink=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    CobraBrandMark(){super(InfinityLiveActivity.this);setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);}
    @Override protected void onDraw(android.graphics.Canvas c){
      int save=c.save();c.scale(getWidth()/40f,getHeight()/40f);ink.setStyle(android.graphics.Paint.Style.FILL);ink.setColor(cobraModeColor("panel"));c.drawRoundRect(1,1,39,39,12,12,ink);
      ink.setStyle(android.graphics.Paint.Style.STROKE);ink.setStrokeWidth(3);ink.setStrokeCap(android.graphics.Paint.Cap.ROUND);ink.setColor(cobraModeColor("accent"));c.drawArc(10,9,30,31,42,276,false,ink);
      ink.setStrokeWidth(2);c.drawLine(26,12,31,12,ink);ink.setStyle(android.graphics.Paint.Style.FILL);c.drawCircle(29,10,1,ink);c.restoreToCount(save);
    }
  }
  private View cobraBrandHeader(){
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(0,dp(4),0,dp(12));
    header.addView(new CobraBrandMark(),new LinearLayout.LayoutParams(dp(44),dp(44)));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);TextView title=cobraText("COBRA",cobraModeColor("text"),20);title.setTypeface(Typeface.create("sans-serif-medium",0));title.setLetterSpacing(.13f);copy.addView(title);
    TextView sub=cobraText("An Infinity experience",cobraModeColor("muted"),11);copy.addView(sub);
    LinearLayout.LayoutParams body=new LinearLayout.LayoutParams(0,-2,1);body.leftMargin=dp(12);header.addView(copy,body);
    header.addView(cobraIcon("back","Collapse navigation",cobraModeDark(),v->closeCobraExperienceDrawer()),new LinearLayout.LayoutParams(dp(48),dp(48)));return header;
  }
  private void cobraDrawerView(LinearLayout items){
    LinearLayout row=cobraDetailRow("multi","View",cobraModeName(mCobraGuideStyle)+"  ·  Choose layout","cobra-drawer-view",false,()->{closeCobraExperienceDrawer();showCobraViewModeMenu();});
    row.setContentDescription("View");items.addView(row,new LinearLayout.LayoutParams(-1,-2));
    LinearLayout health=cobraDetailRow("health","Health Center","Playback, guide and recovery","cobra-drawer-health",false,()->{closeCobraExperienceDrawer();showCobraHealthCenter();});
    health.setContentDescription("Health Center");items.addView(health,new LinearLayout.LayoutParams(-1,-2));
  }
  private void cobraPremiumViewMenu(){
    LinearLayout rows=cobraOpenSheet("View","Choose your Cobra layout. Your channel and live session stay with you.","view-mode");boolean dark=cobraSheetIsDark();
    String[] descriptions={"Touch-first browsing with a generous preview and a live channel feed.","A broadcast workspace with channel rows, time-aligned programmes and contextual groups.","A precise channel directory with dense Now/Next rows and a compact preview.","A spacious channel wall with bold identity cards and responsive columns.","A watch-first theatre with a focused channel or upcoming-programme queue."};
    String[] badges={"TOUCH-FIRST","BROADCAST GUIDE","INFORMATION-DENSE","CHANNEL WALL","WATCH-FIRST"};
    for(int i=0;i<CobraModeLayout.MODES.length;i++){
      final String mode=CobraModeLayout.MODES[i];boolean selected=mode.equals(mCobraGuideStyle);
      LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(12),dp(12),dp(12),dp(12));card.setBackground(cobraModeSurface(18,true));card.setSelected(selected);card.setFocusable(true);card.setClickable(true);card.setTag("cobra-view-mode:"+mode);
      LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);CobraModeThumbnail visual=new CobraModeThumbnail(mode,dark);top.addView(visual,new LinearLayout.LayoutParams(dp(108),dp(76)));
      LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);TextView label=cobraText(badges[i],cobraModeColor("accent"),10);label.setLetterSpacing(.08f);copy.addView(label);
      TextView title=cobraText(cobraModeName(mode),dark?Color.WHITE:cobraModeColor("text"),18);title.setTypeface(Typeface.create("sans-serif-medium",0));title.setMaxLines(2);copy.addView(title);
      TextView state=cobraText(selected?"✓  Current view":"Select layout",dark?0xffb0c2d5:cobraModeColor("muted"),12);copy.addView(state);
      LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,-2,1);cp.leftMargin=dp(12);top.addView(copy,cp);card.addView(top,new LinearLayout.LayoutParams(-1,-2));
      TextView description=cobraText(descriptions[i],dark?0xffb0c2d5:cobraModeColor("muted"),13);description.setPadding(0,dp(10),0,0);description.setMaxLines(5);card.addView(description,new LinearLayout.LayoutParams(-1,-2));
      card.setContentDescription(cobraModeName(mode)+(selected?", selected":"")+", "+descriptions[i]);card.setOnClickListener(v->cobraSwitchMode(mode));
      LinearLayout.LayoutParams gap=new LinearLayout.LayoutParams(-1,-2);gap.topMargin=dp(8);rows.addView(card,gap);
    }
  }

  private void showCobraHealthCenter(){
    LinearLayout rows=cobraOpenSheet("Cobra Health Center","Observed playback and guide state • private, on-device diagnostics","health-center");
    mCobraHealthSummary=cobraInfoText(rows,"");mCobraHealthSummary.setTag("cobra-health-summary");cobraRefreshHealthSummary();
    cobraAddDetail(rows,"recent","Refresh observations","Read current state; no provider scan or stream restart","cobra-health-refresh",false,()->showCobraHealthCenter());
    cobraAddDetail(rows,"source","Export diagnostics ZIP","Choose where to save the redacted report","cobra-health-export",false,()->showCobraDiagnosticExport());
    cobraAddDetail(rows,"health","Health Snapshot","Inspect timestamped state and captured failures","cobra-health-snapshot",false,()->showCobraHealthSnapshot());
    cobraAddDetail(rows,"settings","Playback defaults","Automatic recovery and default display preferences","cobra-health-defaults",false,()->cobraShowPlaybackDefaults());
    int shown=0;for(LiveSource source:mSources){if(shown++>=64)break;final LiveSource selected=source;
      String state=mCobraEpgStatus.get(source.id);String detail=mFeatures.sourceEnabled(source.id)?state==null?"Guide not observed":InfinityCobraDiagnostics.redact(state):"Disabled";
      cobraAddDetail(rows,"source",source.name,detail,"cobra-health-source:"+InfinityCobraFeatureRuntime.hashId(source.id),false,()->cobraShowSourceHealth(selected));
    }
    if(mSources.size()>64)cobraInfoText(rows,"Showing the first 64 sources. All sources remain configured.");
    if(mSources.isEmpty())cobraInfoText(rows,"No sources configured. This is not a successful connectivity test.");
    cobraStartHealthTicker();
  }
  private void cobraRefreshHealthSummary(){
    if(!"health-center".equals(mCobraSheetKind)||mCobraHealthSummary==null)return;
    StringBuilder text=new StringBuilder("OBSERVED  ").append(new SimpleDateFormat("HH:mm:ss",Locale.getDefault()).format(new Date()));
    text.append("\n").append(mCobraPlayerBindings.size()).append(" app-local player sessions • ").append(mSources.size()).append(" sources");
    text.append("\nProvider-wide connection use is not known.");
    long now=android.os.SystemClock.elapsedRealtime();int count=0;
    for(CobraPlayerBinding b:mCobraPlayerBindings.values()){
      if(++count>6)break;CobraSessionVitals s=b.vitals;ExoPlayer p=b.player;
      text.append("\n\n").append(InfinityCobraDiagnostics.redact(b.channel.name)).append("  ·  ").append(cobraPlayerState(p));
      Format format=p.getVideoFormat();if(format!=null)text.append("\nVideo ").append(format.width).append(" × ").append(format.height).append(" · ").append(format.sampleMimeType==null?"Codec not reported":format.sampleMimeType);
      text.append("\nCounter sample: ").append(s.observedAt<0?"Not observed":Math.max(0,now-s.observedAt)+" ms ago");
      text.append("\nVideo output frames: ").append(s.frameCount<0?"Not observed":s.frameCount).append(" • dropped: ").append(s.droppedFrames<0?"Not observed":s.droppedFrames);
      text.append("\nFirst frame: ").append(s.firstFrameAt<0?"Not observed":Math.max(0,s.firstFrameAt-s.createdAt)+" ms");
      text.append("\nBuffered: ").append(Math.max(0,p.getTotalBufferedDuration())).append(" ms");
      text.append("\nLast media load: ").append(s.lastLoadMs<0?"Not observed":s.lastLoadMs+" ms / "+s.lastLoadBytes+" bytes");
      text.append("\nVideo host: ").append(b.texture==null?"Not attached":b.texture.getWidth()+" × "+b.texture.getHeight()+" / "+(b.texture.isAvailable()?"surface available":"surface not available"));
      text.append("\nRecovery: ").append(cobraRecoveryEnabled(b)?s.recovery.state:"Disabled").append(" • ").append(s.recovery.attempts).append("/2 attempts");
      text.append("\nLast captured error: ").append(s.lastError.isEmpty()?"None captured (not a crash guarantee)":s.lastError);
    }
    if(count==0)text.append("\n\nNo active playback to evaluate. Start a channel to collect frame and load observations.");
    text.append("\n\nFrame counters and surface timestamps do not prove the picture is visually correct. Media-load duration is not a network-speed test.");
    String value=text.toString();if(!value.contentEquals(mCobraHealthSummary.getText()))mCobraHealthSummary.setText(value);
  }
  private void cobraShowSourceHealth(LiveSource source){
    LinearLayout rows=cobraOpenSheet("Source health",InfinityCobraDiagnostics.redact(source.name),"source-health");CobraEpgData data=mCobraEpg.get(source.id);String state=mCobraEpgStatus.get(source.id);int count=0;
    for(Channel channel:mChannels)if(source.id.equals(sourceIdForChannel(channel)))count++;
    cobraInfoText(rows,"Source: "+(mFeatures.sourceEnabled(source.id)?"Enabled":"Disabled")+"\nLoaded channels: "+count+"\nGuide state: "+(state==null?"Not observed":InfinityCobraDiagnostics.redact(state))+"\nGuide request: "+(mCobraEpgRequest.containsKey(source.id)?"In progress":"Idle")+"\nLast successful guide fetch: "+(data==null?"Not observed":cobraAge(data.fetched,System.currentTimeMillis()))+"\nGuide keys: "+(data==null?0:data.programs.size())+"\nPartial guide: "+(data==null?"Unknown":data.truncated?"Yes":"No")+"\n\nA loaded cache is not proof of current provider connectivity or programme coverage.");
    cobraAddDetail(rows,"recent","Refresh this guide","Preserves last-known-good cache if the request fails","cobra-source-refresh",false,()->{
      for(Channel c:mChannels)if(source.id.equals(sourceIdForChannel(c))){cobraRefreshGuide(c);return;}
      toast("No loaded channel for this source. Refresh it from Sources first.");
    });
    cobraAddDetail(rows,"back","Back to Health Center",null,"cobra-source-health-back",false,()->showCobraHealthCenter());
  }
  private void cobraShowPlaybackDefaults(){
    LinearLayout rows=cobraOpenSheet("Playback defaults","Channel-specific choices override these defaults","playback-defaults");boolean enabled=mPrefs.getBoolean(COBRA_AUTO_RECOVERY,true);
    cobraAddDetail(rows,"health","Automatic video-surface recovery",enabled?"On • at most two reattachments per player session":"Off","cobra-recovery-default",enabled,()->{mPrefs.edit().putBoolean(COBRA_AUTO_RECOVERY,!enabled).apply();for(CobraPlayerBinding b:mCobraPlayerBindings.values())b.vitals.recovery.suspend();cobraShowPlaybackDefaults();});
    cobraInfoText(rows,"Acts only on sustained missing-video evidence while visible, foreground audio playback is progressing. Never changes the stream URL or recreates the player. Paused, buffering, audio-only, background and PiP playback are excluded. A channel can opt out independently.");
    cobraAddDetail(rows,"aspect","Default fullscreen aspect",cobraAspectLabel(mPrefs.getInt(COBRA_ASPECT_MODE,0)),"cobra-default-aspect",false,()->{
      LinearLayout choices=cobraOpenSheet("Default fullscreen aspect","Inherited in fullscreen. Previews keep Best Fit unless the channel overrides it.","default-aspect");
      for(int i=0;i<11;i++){final int value=i;cobraAddDetail(choices,"aspect",cobraAspectLabel(i),null,"cobra-default-aspect:"+i,mPrefs.getInt(COBRA_ASPECT_MODE,0)==i,()->{mPrefs.edit().putInt(COBRA_ASPECT_MODE,value).apply();for(CobraPlayerBinding b:mCobraPlayerBindings.values())cobraFitBinding(b);if(mPlaying!=null){mAspectMode=cobraChannelAspect(mPlaying);applyCobraAspectTransform();}cobraShowPlaybackDefaults();});}
    });
  }
  private void cobraShowChannelPreferences(Channel channel){
    if(!cobraLiveChannel(channel)){toast("Choose a loaded live channel first");return;}
    final String key=cobraPreferenceKey(channel);CobraChannelPreferences prefs=cobraReadPreferences(key);
    LinearLayout rows=cobraOpenSheet("Channel playback",channel.name+" • saved for this profile and source","channel-playback");
    cobraAddDetail(rows,"aspect","Aspect / display",prefs.aspect<0?"Inherit default":cobraAspectLabel(prefs.aspect),"cobra-channel-aspect",false,()->cobraShowChannelAspect(channel));
    cobraAddDetail(rows,"audio","Preferred audio language",prefs.audio.isEmpty()?"Automatic / default":prefs.audio,"cobra-channel-audio",false,()->cobraShowChannelLanguage(channel,false));
    cobraAddDetail(rows,"cc","Subtitles",prefs.subtitles,"cobra-channel-subtitles",false,()->cobraShowChannelLanguage(channel,true));
    cobraAddDetail(rows,"source","Configured stream fallback","primary".equals(prefs.fallback)?"Primary only":"Use configured fallback after an error","cobra-channel-fallback",false,()->{CobraChannelPreferences p=cobraReadPreferences(key);p.fallback="primary".equals(p.fallback)?"allow":"primary";if(cobraSavePreferences(channel,key,p,false))cobraShowChannelPreferences(channel);});
    cobraAddDetail(rows,"health","Automatic video-surface recovery",prefs.recovery,"cobra-channel-recovery",false,()->{
      LinearLayout choices=cobraOpenSheet("Channel recovery","Choose an override or inherit the default","channel-recovery");
      for(String value:new String[]{"inherit","on","off"}){final String choice=value;cobraAddDetail(choices,"health","inherit".equals(value)?"Inherit default":"on".equals(value)?"On":"Off",null,"cobra-channel-recovery:"+value,value.equals(prefs.recovery),()->{CobraChannelPreferences p=cobraReadPreferences(key);p.recovery=choice;if(cobraSavePreferences(channel,key,p,false))cobraShowChannelPreferences(channel);});}
    });
    cobraAddDetail(rows,"recent","Reset this channel","Only this profile's playback preferences; no favorites, source or account deletion","cobra-channel-reset",false,()->{
      LinearLayout confirm=cobraOpenSheet("Reset channel playback?",channel.name,"channel-reset");cobraAddDetail(confirm,"recent","Reset playback preferences","Use inherited defaults again","cobra-channel-reset-confirm",false,()->{if(cobraSavePreferences(channel,key,new CobraChannelPreferences(),true))cobraShowChannelPreferences(channel);});
    });
    cobraInfoText(rows,"Languages are preferences, not promises of available tracks. Missing languages fall back to the stream defaults. Track indexes are never saved across streams. Video preferences do not change Multi-View's audio owner.");
  }
  private void cobraShowChannelAspect(Channel channel){
    if(!cobraLiveChannel(channel))return;final String key=cobraPreferenceKey(channel);CobraChannelPreferences prefs=cobraReadPreferences(key);
    LinearLayout rows=cobraOpenSheet("Channel display",channel.name,"channel-aspect");
    for(int i=-1;i<=11;i++){final int value=i;cobraAddDetail(rows,"aspect",i<0?"Inherit default":cobraAspectLabel(i),null,"cobra-channel-aspect:"+i,prefs.aspect==i,()->{
      CobraChannelPreferences p=cobraReadPreferences(key);p.aspect=value;if(cobraSavePreferences(channel,key,p,false)){if(value==11)cobraShowChannelCustomAspect(channel);else cobraShowChannelPreferences(channel);}
    });}
  }
  private void cobraShowChannelCustomAspect(Channel channel){
    final String key=cobraPreferenceKey(channel);LinearLayout rows=cobraOpenSheet("Custom channel display",channel.name+" • 55–180%","channel-custom-aspect");
    for(int axis=0;axis<2;axis++){final int selectedAxis=axis;CobraChannelPreferences prefs=cobraReadPreferences(key);TextView label=cobraInfoText(rows,(axis==0?"Width":"Height")+"  "+Math.round((axis==0?prefs.x:prefs.y)*100)+"%");
      android.widget.SeekBar slider=new android.widget.SeekBar(this);slider.setMax(125);slider.setProgress(Math.round((axis==0?prefs.x:prefs.y)*100)-55);slider.setContentDescription(axis==0?"Channel width":"Channel height");
      slider.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(android.widget.SeekBar bar,int value,boolean user){label.setText((selectedAxis==0?"Width":"Height")+"  "+(55+value)+"%");}public void onStartTrackingTouch(android.widget.SeekBar bar){}public void onStopTrackingTouch(android.widget.SeekBar bar){CobraChannelPreferences p=cobraReadPreferences(key);p.aspect=11;if(selectedAxis==0)p.x=(55+bar.getProgress())/100f;else p.y=(55+bar.getProgress())/100f;cobraSavePreferences(channel,key,p,false);}});
      rows.addView(slider,new LinearLayout.LayoutParams(-1,dp(54)));
    }
  }
  private void cobraShowChannelLanguage(Channel channel,boolean text){
    final String key=cobraPreferenceKey(channel);CobraChannelPreferences prefs=cobraReadPreferences(key);
    LinearLayout rows=cobraOpenSheet(text?"Channel subtitles":"Channel audio language",channel.name,"channel-language");
    java.util.LinkedHashSet<String> languages=new java.util.LinkedHashSet<>();
    for(CobraPlayerBinding b:mCobraPlayerBindings.values())if(key.equals(b.vitals.preferenceKey))for(Tracks.Group group:b.player.getCurrentTracks().getGroups())if(group.getType()==(text?C.TRACK_TYPE_TEXT:C.TRACK_TYPE_AUDIO))for(int i=0;i<group.length;i++){String language=CobraPreferencePolicy.language(group.getTrackFormat(i).language);if(group.isTrackSupported(i)&&!language.isEmpty())languages.add(language);}
    languages.addAll(java.util.Arrays.asList("en","es","fr","ar","de","it","pt"));
    ArrayList<String> values=new ArrayList<>();values.add("inherit");if(text){values.add("off");values.add("auto");}values.addAll(languages);
    for(String value:values){final String selected=value;String label="inherit".equals(value)?"Inherit default":"off".equals(value)?"Off":"auto".equals(value)?"Automatic subtitles":value;
      cobraAddDetail(rows,text?"cc":"audio",label,null,"cobra-channel-language:"+value,value.equals(text?prefs.subtitles:prefs.audio.isEmpty()?"inherit":prefs.audio),()->{CobraChannelPreferences p=cobraReadPreferences(key);if(text)p.subtitles=selected;else p.audio="inherit".equals(selected)?"":selected;if(cobraSavePreferences(channel,key,p,false))cobraShowChannelPreferences(channel);});
    }
  }
