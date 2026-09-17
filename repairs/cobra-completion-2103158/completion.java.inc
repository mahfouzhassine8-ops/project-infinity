  // 2103158: additive Cobra-only controls. No Kodi, stream, audio-focus or native owner.
  private static final String COBRA_CHANNEL_PREFS = "cobra_channel_playback_v1";
  private static final String COBRA_RECOVERY_ENABLED = "cobra_surface_recovery_enabled_v1";
  private boolean mCobraHealthForeground;
  private final CobraRecoveryBudget mCobraRecoveryBudget = new CobraRecoveryBudget();

  private static final class CobraPlaybackChoice {
    int aspect; float x,y;
    String audioLanguage="",audioSignature="",textLanguage="",textSignature="",captions="auto";
    int audioRole=0,textRole=0;
    boolean recovery=true;
    CobraPlaybackChoice(int mode,float width,float height){aspect=mode(mode);x=factor(width);y=factor(height);}
    static int mode(int value){return value>=0&&value<=11?value:0;}
    static float factor(float value){return Float.isNaN(value)||Float.isInfinite(value)?1f:Math.max(.55f,Math.min(1.8f,value));}
    static String language(String value){return value!=null&&value.length()<=48&&value.matches("[A-Za-z]{2,8}([_-][A-Za-z0-9]{1,8})*")?value.replace('_','-').toLowerCase(Locale.US):"";}
    static String digest(String value){
      try{byte[] bytes=java.security.MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format(Locale.US,"%02x",b&255));return out.toString();}
      catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
    }
    static String part(String value){String s=value==null?"":value;return s.length()+":"+s;}
    static String key(String profile,String source,String channel){return "v1:"+digest(part(profile)+part(source)+part(channel));}
    static String signature(String value){return value!=null&&value.matches("[0-9a-f]{64}")?value:"";}
  }

  // A failed attempt consumes its budget BEFORE touching the player. Success never resets it.
  private static final class CobraRecoveryBudget {
    private final ArrayList<Long> times=new ArrayList<>();
    boolean take(long now){while(!times.isEmpty()&&now-times.get(0)>=300000L)times.remove(0);if(times.size()>=4)return false;times.add(now);return true;}
  }
  private static final class CobraSurfaceRecovery {
    static final long GRACE=12000L,COOLDOWN=30000L;
    int attempts;long observed=-1,stamp=Long.MIN_VALUE,position=-1,lastAttempt=-COOLDOWN;
    String state="waiting_for_video";
    void suspend(String reason){observed=-1;stamp=Long.MIN_VALUE;position=-1;state=reason;}
    boolean inspect(long now,long textureStamp,long playbackPosition,boolean eligible){
      if(!eligible){suspend("not_eligible");return false;}
      if(observed<0||textureStamp!=stamp||playbackPosition<position){observed=now;stamp=textureStamp;position=playbackPosition;state=textureStamp>0?"frames_observed":"waiting_for_frames";return false;}
      if(now-observed<GRACE){return false;}
      if(playbackPosition-position<2000L){suspend("playback_not_advancing");return false;}
      if(attempts>=2){state="automatic_limit_reached";return false;}
      if(now-lastAttempt<COOLDOWN){state="cooldown";return false;}
      // Reserve the per-session slot, even if the global budget or rebind then fails.
      attempts++;lastAttempt=now;observed=now;position=playbackPosition;state="rebind_requested";return true;
    }
  }

  private String cobraPreferenceKey(Channel channel){
    if(channel==null||channel.id==null||channel.id.startsWith("vod:"))return "";
    return CobraPlaybackChoice.key(mFeatures==null?"default":mFeatures.activeProfileId(),sourceIdForChannel(channel),channel.id);
  }
  private CobraPlaybackChoice cobraReadChoice(String key){
    CobraPlaybackChoice choice=new CobraPlaybackChoice(mPrefs==null?0:mPrefs.getInt(COBRA_ASPECT_MODE,0),mPrefs==null?1f:mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f),mPrefs==null?1f:mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f));
    if(key.isEmpty())return choice;
    try{
      String raw=getSharedPreferences(COBRA_CHANNEL_PREFS,MODE_PRIVATE).getString(key,"");if(raw.isEmpty()||raw.length()>2048)return choice;
      JSONObject json=new JSONObject(raw);if(json.optInt("schema",0)!=1)return choice;
      choice.aspect=CobraPlaybackChoice.mode(json.optInt("aspect",choice.aspect));choice.x=CobraPlaybackChoice.factor((float)json.optDouble("x",choice.x));choice.y=CobraPlaybackChoice.factor((float)json.optDouble("y",choice.y));
      choice.audioLanguage=CobraPlaybackChoice.language(json.optString("audio_language",""));choice.audioSignature=CobraPlaybackChoice.signature(json.optString("audio_signature",""));choice.audioRole=Math.max(0,json.optInt("audio_role",0));
      choice.textLanguage=CobraPlaybackChoice.language(json.optString("text_language",""));choice.textSignature=CobraPlaybackChoice.signature(json.optString("text_signature",""));choice.textRole=Math.max(0,json.optInt("text_role",0));
      String captions=json.optString("captions","auto");choice.captions="off".equals(captions)||"on".equals(captions)?captions:"auto";choice.recovery=json.optBoolean("surface_recovery",true);
    }catch(Exception invalid){InfinityCobraDiagnostics.record(this,"channel-preferences","unreadable","defaults_used");}
    return choice;
  }
  private boolean cobraWriteChoice(Channel channel,String expectedKey,CobraPlaybackChoice choice){
    if(expectedKey.isEmpty()||!expectedKey.equals(cobraPreferenceKey(channel))||!isCobraAsyncAlive())return false;
    try{
      SharedPreferences store=getSharedPreferences(COBRA_CHANNEL_PREFS,MODE_PRIVATE);
      JSONObject json=new JSONObject();json.put("schema",1);json.put("aspect",CobraPlaybackChoice.mode(choice.aspect));json.put("x",CobraPlaybackChoice.factor(choice.x));json.put("y",CobraPlaybackChoice.factor(choice.y));
      json.put("audio_language",CobraPlaybackChoice.language(choice.audioLanguage));json.put("audio_signature",CobraPlaybackChoice.signature(choice.audioSignature));json.put("audio_role",choice.audioRole);
      json.put("text_language",CobraPlaybackChoice.language(choice.textLanguage));json.put("text_signature",CobraPlaybackChoice.signature(choice.textSignature));json.put("text_role",choice.textRole);json.put("captions",choice.captions);json.put("surface_recovery",choice.recovery);json.put("updated",System.currentTimeMillis());
      SharedPreferences.Editor edit=store.edit();Map<String,?> all=store.getAll();
      // Bound the new preference store without deleting any legacy data or current-profile records at random.
      if(!all.containsKey(expectedKey)&&all.size()>=1024){toast("Channel preference storage is full; reset an unused channel first");return false;}
      edit.putString(expectedKey,json.toString()).apply();cobraApplyChoiceToSessions(expectedKey,choice);return true;
    }catch(Exception failure){InfinityCobraDiagnostics.failure(this,"channel-preferences",failure);toast("Channel preferences could not be saved");return false;}
  }
  private void cobraApplyChoiceToSessions(String key,CobraPlaybackChoice choice){
    for(CobraPlayerBinding binding:new ArrayList<>(mCobraPlayerBindings.values()))if(binding.current()&&key.equals(binding.preferenceKey)){
      binding.choice=choice;cobraRestoreChannelTracks(binding);if(binding.player==mPlayer)mAspectMode=choice.aspect;cobraFitBinding(binding);
    }
  }
  private String cobraTrackSignature(Format format){
    return CobraPlaybackChoice.digest(CobraPlaybackChoice.part(format.language)+CobraPlaybackChoice.part(format.label)+CobraPlaybackChoice.part(format.sampleMimeType)+format.roleFlags+":"+format.channelCount);
  }
  private TrackSelectionOverride cobraSavedTrack(Tracks tracks,int type,String signature,String language,int role){
    TrackSelectionOverride best=null;int score=0;
    for(Tracks.Group group:tracks.getGroups())if(group.getType()==type)for(int i=0;i<group.length;i++)if(group.isTrackSupported(i)){
      Format format=group.getTrackFormat(i);int match=!signature.isEmpty()&&signature.equals(cobraTrackSignature(format))?100:!language.isEmpty()&&language.equals(CobraPlaybackChoice.language(format.language))?(format.roleFlags==role?20:10):0;
      if(match>score){score=match;best=new TrackSelectionOverride(group.getMediaTrackGroup(),i);}
    }
    return best;
  }
  private void cobraRestoreChannelTracks(CobraPlayerBinding binding){
    if(!binding.current()||binding.restoringTracks||binding.preferenceKey.isEmpty())return;
    binding.restoringTracks=true;
    try{
      CobraPlaybackChoice c=binding.choice;
      androidx.media3.common.TrackSelectionParameters.Builder parameters=binding.player.getTrackSelectionParameters().buildUpon();
      // Start from this session's original audio/text defaults, preserving unrelated constraints.
      parameters.clearOverridesOfType(C.TRACK_TYPE_AUDIO).clearOverridesOfType(C.TRACK_TYPE_TEXT)
          .setPreferredAudioLanguages(binding.trackDefaults.preferredAudioLanguages.toArray(new String[0]))
          .setPreferredAudioRoleFlags(binding.trackDefaults.preferredAudioRoleFlags)
          .setPreferredTextLanguages(binding.trackDefaults.preferredTextLanguages.toArray(new String[0]))
          .setPreferredTextRoleFlags(binding.trackDefaults.preferredTextRoleFlags)
          .setSelectUndeterminedTextLanguage(binding.trackDefaults.selectUndeterminedTextLanguage)
          .setTrackTypeDisabled(C.TRACK_TYPE_TEXT,binding.trackDefaults.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
      if(!c.audioLanguage.isEmpty())parameters.setPreferredAudioLanguage(c.audioLanguage).setPreferredAudioRoleFlags(c.audioRole);
      TrackSelectionOverride audio=cobraSavedTrack(binding.player.getCurrentTracks(),C.TRACK_TYPE_AUDIO,c.audioSignature,c.audioLanguage,c.audioRole);if(audio!=null)parameters.setOverrideForType(audio);
      if(!"auto".equals(c.captions))parameters.setTrackTypeDisabled(C.TRACK_TYPE_TEXT,"off".equals(c.captions));
      if("on".equals(c.captions)){
        parameters.setPreferredTextLanguage(c.textLanguage.isEmpty()?null:c.textLanguage).setPreferredTextRoleFlags(c.textRole).setSelectUndeterminedTextLanguage(c.textLanguage.isEmpty());
        TrackSelectionOverride text=cobraSavedTrack(binding.player.getCurrentTracks(),C.TRACK_TYPE_TEXT,c.textSignature,c.textLanguage,c.textRole);if(text!=null)parameters.setOverrideForType(text);
      }
      androidx.media3.common.TrackSelectionParameters updated=parameters.build();if(!updated.equals(binding.player.getTrackSelectionParameters()))binding.player.setTrackSelectionParameters(updated);binding.trackRestoreFailed=false;
    }catch(RuntimeException failure){if(!binding.trackRestoreFailed)InfinityCobraDiagnostics.failure(this,"channel-track-restore",failure);binding.trackRestoreFailed=true;}finally{binding.restoringTracks=false;}
  }
  private CobraPlayerBinding cobraSessionFor(Channel channel){String key=cobraPreferenceKey(channel);if(key.isEmpty())return null;CobraPlayerBinding full=mCobraPlayerBindings.get(mPlayer);if(full!=null&&full.current()&&key.equals(full.preferenceKey))return full;for(CobraPlayerBinding b:mCobraPlayerBindings.values())if(b.current()&&key.equals(b.preferenceKey))return b;return null;}
  private Channel cobraHealthChannel(){return mPlaying!=null&&!mPlaying.id.startsWith("vod:")?mPlaying:mGuidePreviewChannel;}

  private void showCobraChannelPreferences(Channel channel){
    final String key=cobraPreferenceKey(channel);if(key.isEmpty()){toast("Select a live channel first");return;}
    CobraPlaybackChoice c=cobraReadChoice(key);LinearLayout rows=cobraOpenSheet("Channel playback",channel.name+" · saved separately for this profile and source","channel-playback");boolean dark=cobraSheetIsDark();
    cobraCompletionRow(rows,"aspect","Display",cobraAspectLabel(c.aspect),"cobra_pref_display",()->cobraChooseChannelAspect(channel));
    cobraCompletionRow(rows,"audio","Audio & subtitles","Remember a language and track identity, not a changing track number","cobra_pref_tracks",()->cobraShowChannelTracks(channel));
    cobraCompletionRow(rows,"cc","Subtitles: "+("auto".equals(c.captions)?"Stream default":c.captions),"Toggle off / on when available","cobra_pref_captions",()->{CobraPlaybackChoice latest=cobraReadChoice(key);latest.captions="off".equals(latest.captions)?"on":"off";if(cobraWriteChoice(channel,key,latest))showCobraChannelPreferences(channel);});
    cobraCompletionRow(rows,"recent","Surface recovery: "+(c.recovery?"Allowed":"Disabled"),"Never recreates the player; global safety limits still apply","cobra_pref_recovery",()->{CobraPlaybackChoice latest=cobraReadChoice(key);latest.recovery=!latest.recovery;if(cobraWriteChoice(channel,key,latest))showCobraChannelPreferences(channel);});
    cobraCompletionRow(rows,"remove","Reset this channel","Other channels and your global defaults are not changed","cobra_pref_reset",()->cobraConfirmResetChannel(channel,key));
  }
  private void cobraConfirmResetChannel(Channel channel,String key){
    LinearLayout rows=cobraOpenSheet("Reset channel playback?","Only this profile's preferences for this channel will be removed.","channel-reset");
    cobraCompletionRow(rows,"remove","Reset channel preferences",null,"cobra_pref_reset_confirm",()->{
      if(!key.equals(cobraPreferenceKey(channel)))return;
      getSharedPreferences(COBRA_CHANNEL_PREFS,MODE_PRIVATE).edit().remove(key).apply();cobraApplyChoiceToSessions(key,cobraReadChoice(key));showCobraChannelPreferences(channel);
    });cobraCompletionRow(rows,"close","Cancel",null,"cobra_pref_reset_cancel",()->showCobraChannelPreferences(channel));
  }
  private void cobraChooseChannelAspect(Channel channel){
    final String key=cobraPreferenceKey(channel);if(key.isEmpty())return;
    CobraPlaybackChoice current=cobraReadChoice(key);LinearLayout rows=cobraOpenSheet("Channel display","Best Fit preserves proportions. Changes apply to this channel only.","channel-aspect");
    for(int i=0;i<12;i++){final int mode=i;cobraCompletionRow(rows,"aspect",cobraAspectLabel(i),current.aspect==i?"Selected":null,"cobra_channel_aspect:"+i,()->{CobraPlaybackChoice choice=cobraReadChoice(key);choice.aspect=mode;if(cobraWriteChoice(channel,key,choice)&&mode==11)cobraEditChannelSize(channel);});}
  }
  private void cobraEditChannelSize(Channel channel){
    final String key=cobraPreferenceKey(channel);if(key.isEmpty())return;
    LinearLayout rows=cobraOpenSheet("Custom channel display","Width and height · choose Apply size to save","channel-size");CobraPlaybackChoice current=cobraReadChoice(key);boolean dark=cobraSheetIsDark();
    final android.widget.SeekBar[] controls=new android.widget.SeekBar[2];
    for(boolean horizontal:new boolean[]{true,false}){
      final boolean x=horizontal;TextView label=cobraText((x?"Width":"Height")+"  "+Math.round((x?current.x:current.y)*100)+"%",dark?Color.WHITE:cobraModeColor("text"),14);label.setPadding(dp(12),dp(8),dp(12),0);rows.addView(label);
      android.widget.SeekBar slider=new android.widget.SeekBar(this);controls[x?0:1]=slider;slider.setTag(x?"cobra_channel_width":"cobra_channel_height");slider.setMax(125);slider.setProgress(Math.round(((x?current.x:current.y)-.55f)*100));slider.setContentDescription(x?"Channel width percent":"Channel height percent");
      slider.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
        public void onProgressChanged(android.widget.SeekBar bar,int value,boolean user){label.setText((x?"Width":"Height")+"  "+(55+value)+"%");}
        public void onStartTrackingTouch(android.widget.SeekBar bar){}
        public void onStopTrackingTouch(android.widget.SeekBar bar){}
      });rows.addView(slider,new LinearLayout.LayoutParams(-1,dp(56)));
    }
    cobraCompletionRow(rows,"aspect","Apply size","Save both dimensions for this channel","cobra_channel_size_apply",()->{CobraPlaybackChoice choice=cobraReadChoice(key);choice.aspect=11;choice.x=(55+controls[0].getProgress())/100f;choice.y=(55+controls[1].getProgress())/100f;if(cobraWriteChoice(channel,key,choice))toast("Channel display saved");});
    cobraCompletionRow(rows,"recent","Reset width & height","Return both to 100%","cobra_channel_size_reset",()->{CobraPlaybackChoice choice=cobraReadChoice(key);choice.x=choice.y=1f;if(cobraWriteChoice(channel,key,choice))cobraEditChannelSize(channel);});
  }
  private void cobraShowChannelTracks(Channel channel){CobraPlayerBinding b=cobraSessionFor(channel);if(b==null){toast("Play this channel to see the tracks it supplies");return;}cobraShowTracksFor(b.player,channel);}
  private void cobraShowTracksFor(ExoPlayer player,Channel channel){
    if(player==null||mCobraPlayerLocked)return;final CobraPlayerBinding binding=mCobraPlayerBindings.get(player);if(binding==null||!binding.current())return;
    final String key=binding.preferenceKey;LinearLayout rows=cobraOpenSheet("Audio & subtitles",key.isEmpty()?"Applies to this playback session":"Saved for this channel · unavailable tracks fall back safely","tracks");boolean dark=cobraSheetIsDark();
    cobraCompletionRow(rows,"cc","Subtitles off",null,"cobra_tracks_off",()->{
      if(!binding.current())return;
      if(key.isEmpty())player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_TEXT,true).build());
      else{CobraPlaybackChoice c=cobraReadChoice(key);c.captions="off";cobraWriteChoice(channel,key,c);}
    });
    cobraCompletionRow(rows,"recent","Use stream track defaults","Remove saved audio and subtitle choices only","cobra_tracks_default",()->{
      if(!binding.current())return;if(key.isEmpty()){player.setTrackSelectionParameters(binding.trackDefaults);return;}
      CobraPlaybackChoice c=cobraReadChoice(key);c.audioLanguage=c.audioSignature=c.textLanguage=c.textSignature="";c.audioRole=c.textRole=0;c.captions="auto";cobraWriteChoice(channel,key,c);
    });
    int count=0;for(Tracks.Group group:player.getCurrentTracks().getGroups())if(group.getType()==C.TRACK_TYPE_AUDIO||group.getType()==C.TRACK_TYPE_TEXT)for(int i=0;i<group.length;i++)if(group.isTrackSupported(i)){
      final int index=i;final Format format=group.getTrackFormat(i);final boolean audio=group.getType()==C.TRACK_TYPE_AUDIO;
      String label=format.label!=null?format.label:format.language!=null?format.language:"Track "+(i+1);
      cobraCompletionRow(rows,audio?"audio":"cc",label,(audio?"Audio":"Subtitles")+(group.isTrackSelected(i)?" · Selected":""),"cobra_track:"+(count++),()->{
        if(!binding.current())return;
        // A delayed sheet must not apply an override for a track group that no longer exists.
        if(!player.getCurrentTracks().getGroups().contains(group)){toast("Tracks changed; open the chooser again");return;}
        if(key.isEmpty()){player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(group.getType(),false).setOverrideForType(new TrackSelectionOverride(group.getMediaTrackGroup(),index)).build());return;}
        CobraPlaybackChoice c=cobraReadChoice(key);
        if(audio){c.audioLanguage=CobraPlaybackChoice.language(format.language);c.audioSignature=cobraTrackSignature(format);c.audioRole=format.roleFlags;}
        else{c.textLanguage=CobraPlaybackChoice.language(format.language);c.textSignature=cobraTrackSignature(format);c.textRole=format.roleFlags;c.captions="on";}
        cobraWriteChoice(channel,key,c);
      });
    }
    if(count==0)cobraHealthText(rows,"No additional tracks supplied","This stream has not exposed selectable audio or subtitle tracks.");
  }

  private void cobraInspectSurfaceRecovery(){
    if(Looper.myLooper()!=Looper.getMainLooper())return;
    for(CobraPlayerBinding binding:new ArrayList<>(mCobraPlayerBindings.values())){
      if(!binding.current())continue;
      TextureView texture=binding.texture;CobraSurfaceRecovery recovery=binding.recovery;
      try{
      boolean eligible=mCobraHealthForeground&&!mBackgroundStopped&&!mInPictureInPicture&&mPrefs!=null&&mPrefs.getBoolean(COBRA_RECOVERY_ENABLED,true)&&binding.choice.recovery
          &&texture!=null&&texture.isAttachedToWindow()&&texture.isShown()&&texture.isAvailable()&&texture.getWidth()>1&&texture.getHeight()>1
          &&binding.error.isEmpty()&&binding.player.getPlaybackState()==Player.STATE_READY&&binding.player.getPlayWhenReady()
          &&binding.player.getPlaybackSuppressionReason()==Player.PLAYBACK_SUPPRESSION_REASON_NONE&&binding.player.getCurrentTracks().isTypeSelected(C.TRACK_TYPE_VIDEO);
        long stamp=eligible?texture.getSurfaceTexture().getTimestamp():0;
        long now=android.os.SystemClock.elapsedRealtime();
        if(!recovery.inspect(now,stamp,eligible?binding.player.getCurrentPosition():0,eligible))continue;
        if(!mCobraRecoveryBudget.take(now)){recovery.state="global_limit_reached";continue;}
        // Same live binding, same assigned texture, main thread; never prepare/play/release or change audio ownership.
        if(!binding.current()||binding.texture!=texture){recovery.suspend("superseded");continue;}
        binding.player.clearVideoTextureView(texture);binding.player.setVideoTextureView(texture);cobraFitBinding(binding);
        recovery.state="rebound_waiting_for_frames";InfinityCobraDiagnostics.record(this,"surface-recovery","rebind","attempt="+recovery.attempts);
      }catch(RuntimeException failure){if(!"surface_probe_or_rebind_failed".equals(recovery.state))InfinityCobraDiagnostics.failure(this,"surface-recovery",failure);recovery.state="surface_probe_or_rebind_failed";}
    }
  }
  private void cobraSuspendRecovery(){for(CobraPlayerBinding binding:mCobraPlayerBindings.values())binding.recovery.suspend("lifecycle_or_surface_transition");}
  private LinearLayout cobraCompletionRow(LinearLayout rows,String icon,String title,String detail,String tag,Runnable action){
    LinearLayout row=cobraSheetRow(icon,title,detail,false,cobraSheetIsDark(),action);row.setTag(tag);rows.addView(row,new LinearLayout.LayoutParams(-1,-2));return row;
  }
  private void cobraHealthText(LinearLayout rows,String title,String detail){
    boolean dark=cobraSheetIsDark();LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(14),dp(12),dp(14),dp(12));card.setBackground(cobraModeSurface(14,false));
    TextView heading=cobraText(title,dark?Color.WHITE:cobraModeColor("text"),15);heading.setTypeface(Typeface.create("sans-serif-medium",0));card.addView(heading,new LinearLayout.LayoutParams(-1,-2));
    TextView body=cobraText(detail,dark?0xffb3c3d4:cobraModeColor("muted"),12);body.setPadding(0,dp(5),0,0);body.setTextIsSelectable(true);card.addView(body,new LinearLayout.LayoutParams(-1,-2));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.bottomMargin=dp(8);rows.addView(card,p);
  }
  private static String cobraPlaybackStateName(int state){return state==Player.STATE_READY?"Ready":state==Player.STATE_BUFFERING?"Buffering":state==Player.STATE_ENDED?"Ended":state==Player.STATE_IDLE?"Idle":"Unknown";}
  private void showCobraHealthCenter(){
    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}
    String raw=cobraFreshHealthSnapshot();LinearLayout rows=cobraOpenSheet("Cobra Health Center","Live observations · not a crash-free certificate","health-center");rows.setTag("cobra_health_center");
    try{
      JSONObject data=new JSONObject(raw);JSONArray players=data.optJSONArray("players");
      cobraHealthText(rows,"Cobra · "+data.optString("cobra_version","Installed build"),"Build "+data.optString("version_code","Unknown")+" · "+cobraModeName(mCobraGuideStyle)+" · "+cobraAppearanceLabel());
      if(players==null||players.length()==0)cobraHealthText(rows,"Playback · not active","No bound Cobra player is currently observed. This does not test your provider.");
      else for(int i=0;i<players.length();i++){
        JSONObject p=players.getJSONObject(i);cobraHealthText(rows,"Playback "+(i+1)+" · "+cobraPlaybackStateName(p.optInt("state",0)),
          "Playing: "+p.optBoolean("is_playing")+" · requested: "+p.optBoolean("play_when_ready")+" · suppression: "+p.optInt("suppression_reason",-1)+"\nVideo: "+p.optString("video_format","Not exposed")+"\nSurface: "+p.optInt("surface_width",0)+" × "+p.optInt("surface_height",0)+" · attached: "+p.optBoolean("surface_attached")+" · available: "+p.optBoolean("surface_available")+"\nRecovery: "+p.optString("surface_recovery_state","not_observed")+" · attempts "+p.optInt("surface_recovery_attempts",0)+" / 2\nLast player error: "+p.optString("last_error_code","").replace("\n"," "));
      }
      cobraHealthText(rows,"Programme guide",data.optInt("cached_guide_source_count",0)+" source snapshots · "+data.optInt("guide_requests_in_flight",0)+" full requests · "+data.optInt("short_guide_requests_in_flight",0)+" short requests.\nCached data is not evidence of provider availability or completeness.");
      cobraHealthText(rows,"Playback ownership",data.optInt("multiview_tiles",0)+" Multi-View tiles · audio owner index "+data.optInt("audio_owner",-1)+"\nRecording: "+data.optString("recording_state","Unknown")+" · PiP: "+data.optBoolean("picture_in_picture"));
      cobraHealthText(rows,"Device memory",data.optString("device_memory","Unavailable"));
    }catch(Exception unavailable){cobraHealthText(rows,"Snapshot unavailable","Use the diagnostic export for retained evidence. No healthy status is inferred.");}
    final Channel channel=cobraHealthChannel();
    cobraCompletionRow(rows,"recent","Refresh observations","Read current state without restarting playback","cobra_health_refresh",()->showCobraHealthCenter());
    if(channel!=null){cobraCompletionRow(rows,"guide","Refresh current channel guide","Keeps successful cached data and playback","cobra_health_guide",()->cobraRefreshGuide(channel));cobraCompletionRow(rows,"settings","Channel playback preferences",null,"cobra_health_preferences",()->showCobraChannelPreferences(channel));}
    cobraCompletionRow(rows,"recent","Automatic surface recovery: "+(mPrefs.getBoolean(COBRA_RECOVERY_ENABLED,true)?"On":"Off"),"At most 2 rebinds per session; 4 across Cobra in 5 minutes","cobra_health_recovery",()->{mPrefs.edit().putBoolean(COBRA_RECOVERY_ENABLED,!mPrefs.getBoolean(COBRA_RECOVERY_ENABLED,true)).apply();cobraSuspendRecovery();showCobraHealthCenter();});
    cobraCompletionRow(rows,"source","Export Crash & Diagnostics ZIP","You choose the destination; nothing is uploaded automatically","cobra_health_export",()->showCobraDiagnosticExport());
    cobraCompletionRow(rows,"more","Detailed snapshot","Fresh structured data with explicit unavailable states","cobra_health_raw",()->showCobraHealthRaw());
  }
  private void showCobraHealthRaw(){LinearLayout rows=cobraOpenSheet("Cobra diagnostic snapshot","Current observations; retained crash history is in the export","health-raw");TextView report=cobraText(cobraFreshHealthSnapshot(),cobraSheetIsDark()?Color.WHITE:cobraModeColor("text"),12);report.setTypeface(Typeface.MONOSPACE);report.setTextIsSelectable(true);rows.addView(report,new LinearLayout.LayoutParams(-1,-2));}
