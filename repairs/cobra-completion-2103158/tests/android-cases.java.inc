  boolean completionText(View v,String part){if(v instanceof android.widget.TextView&&((android.widget.TextView)v).getText().toString().contains(part))return true;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)if(completionText(((ViewGroup)v).getChildAt(i),part))return true;return false;}
  View completionDescription(View v,String prefix){CharSequence text=v.getContentDescription();if(text!=null&&text.toString().startsWith(prefix))return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View result=completionDescription(((ViewGroup)v).getChildAt(i),prefix);if(result!=null)return result;}return null;}
  Object completionChannel(InfinityLiveActivity a,int index)throws Exception{return ((List<?>)get(a,"mChannels")).get(index);}
  SharedPreferences completionStore(InfinityLiveActivity a){return a.getSharedPreferences("cobra_channel_playback_v1",Context.MODE_PRIVATE);}
  void completionImage(InfinityLiveActivity a,String name)throws Exception{View v=a.getWindow().getDecorView();File dir=new File(System.getProperty("cobra.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}b.recycle();}

  @Test(timeout=90000) public void completionDrawerViewAndHealthKeepAllFiveModes()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(96);
    try{call(a,"cobraOpenLiveTv");measure(a,412,915);Object texture=get(a,"mCobraPreviewTexture");
      for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
        call(a,"cobraSwitchMode",mode);measure(a,412,915);call(a,"toggleCobraDrawer");measure(a,412,915);
        View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(drawer.findViewWithTag("cobra_drawer_view"));assertFalse(completionText(drawer,"VIEW MODES"));assertNotNull(drawer.findViewWithTag("cobra_drawer_health"));
        assertTrue(drawer.findViewWithTag("cobra_drawer_view").performClick());measure(a,412,915);assertNull(a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer"));View sheet=(View)get(a,"mCobraActionSheet");
        for(String name:new String[]{"Mobile","TV Grid","Compact","Cards","Focus"})assertNotNull(completionDescription(sheet,name+", "));
        assertTrue(completionDescription(sheet,(String)call(a,"cobraModeName",mode)+", ").isSelected());a.onBackPressed();assertEquals(mode,get(a,"mCobraGuideStyle"));
        call(a,"showCobraViewModeMenu");assertTrue(completionDescription((View)get(a,"mCobraActionSheet"),"TV Grid, ").performClick());measure(a,412,915);assertEquals("grid",get(a,"mCobraGuideStyle"));assertSame(texture,get(a,"mCobraPreviewTexture"));
      }
      call(a,"toggleCobraDrawer");assertTrue(a.getWindow().getDecorView().findViewWithTag("cobra_drawer_health").performClick());measure(a,412,915);assertEquals("health-center",get(a,"mCobraSheetKind"));assertSame(texture,get(a,"mCobraPreviewTexture"));completionImage(a,"cobra-health-center-dark");a.onBackPressed();assertNull(get(a,"mCobraActionSheet"));guide(a);
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionChannelPreferencesIsolateProfileSourceAndChannel()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);
    try{completionStore(a).edit().clear().commit();Object channel=completionChannel(a,0),other=completionChannel(a,1);String key=(String)call(a,"cobraPreferenceKey",channel);Object choice=call(a,"cobraReadChoice",key);put(choice,"aspect",3);put(choice,"x",1.2f);assertEquals(true,call(a,"cobraWriteChoice",channel,key,choice));assertEquals(3,get(call(a,"cobraReadChoice",key),"aspect"));assertEquals(0,get(call(a,"cobraReadChoice",call(a,"cobraPreferenceKey",other)),"aspect"));
      InfinityCobraFeatureRuntime features=(InfinityCobraFeatureRuntime)get(a,"mFeatures");String original=features.activeProfileId(),profile=features.createProfile("Fixture Other","",false);assertTrue(features.unlockAndSelectProfile(profile,""));String otherKey=(String)call(a,"cobraPreferenceKey",channel);assertNotEquals(key,otherKey);assertEquals(0,get(call(a,"cobraReadChoice",otherKey),"aspect"));assertEquals(false,call(a,"cobraWriteChoice",channel,key,choice));assertTrue(features.unlockAndSelectProfile(original,""));assertEquals(3,get(call(a,"cobraReadChoice",key),"aspect"));
      // The production scope function is independently checked for source collision resistance.
      Class<?> policy=Class.forName(InfinityLiveActivity.class.getName()+"$CobraPlaybackChoice");Method scoped=policy.getDeclaredMethod("key",String.class,String.class,String.class);scoped.setAccessible(true);assertNotEquals(scoped.invoke(null,"p","source-a","same"),scoped.invoke(null,"p","source-b","same"));
      call(a,"buildShell");assertEquals(3,get(call(a,"cobraReadChoice",key),"aspect"));assertEquals(1.2f,(Float)get(call(a,"cobraReadChoice",key),"x"),.001f);
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionChannelResetRequiresConfirmation()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);
    try{completionStore(a).edit().clear().commit();Object channel=completionChannel(a,0),other=completionChannel(a,1);String key=(String)call(a,"cobraPreferenceKey",channel),otherKey=(String)call(a,"cobraPreferenceKey",other);Object choice=call(a,"cobraReadChoice",key);put(choice,"aspect",2);call(a,"cobraWriteChoice",channel,key,choice);call(a,"cobraWriteChoice",other,otherKey,choice);
      call(a,"showCobraChannelPreferences",channel);((View)get(a,"mCobraActionSheet")).findViewWithTag("cobra_pref_reset").performClick();assertEquals("channel-reset",get(a,"mCobraSheetKind"));assertTrue(completionStore(a).contains(key));((View)get(a,"mCobraActionSheet")).findViewWithTag("cobra_pref_reset_cancel").performClick();assertTrue(completionStore(a).contains(key));
      ((View)get(a,"mCobraActionSheet")).findViewWithTag("cobra_pref_reset").performClick();((View)get(a,"mCobraActionSheet")).findViewWithTag("cobra_pref_reset_confirm").performClick();assertFalse(completionStore(a).contains(key));assertTrue(completionStore(a).contains(otherKey));assertFalse(((SharedPreferences)get(a,"mPrefs")).contains("cobra_aspect_mode"));
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionMalformedPreferenceAndCapacityFailSafely()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);
    try{SharedPreferences store=completionStore(a);store.edit().clear().commit();Object channel=completionChannel(a,0);String key=(String)call(a,"cobraPreferenceKey",channel);
      for(String raw:new String[]{"broken-json","{\"schema\":99,\"aspect\":9}","{\"schema\":1,\"aspect\":99,\"audio_language\":\"https://secret\",\"x\":-100}"}){store.edit().putString(key,raw).commit();Object choice=call(a,"cobraReadChoice",key);assertEquals(0,get(choice,"aspect"));assertEquals("",get(choice,"audioLanguage"));assertTrue((Float)get(choice,"x")>=.55f);}
      store.edit().clear().commit();SharedPreferences.Editor edit=store.edit();for(int i=0;i<1024;i++)edit.putString("fixture:"+i,"{}");edit.commit();Object choice=call(a,"cobraReadChoice",key);assertEquals(false,call(a,"cobraWriteChoice",channel,key,choice));assertEquals(1024,store.getAll().size());assertFalse(store.contains(key));store.edit().clear().commit();
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionTrackIdentityUsesFormatsNotOldIndices()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);
    try{
      androidx.media3.common.Format first=new androidx.media3.common.Format.Builder().setSampleMimeType("audio/aac").setLanguage("en").setLabel("Main").setChannelCount(2).build();
      androidx.media3.common.Format second=new androidx.media3.common.Format.Builder().setSampleMimeType("audio/aac").setLanguage("en").setLabel("Description").setRoleFlags(androidx.media3.common.C.ROLE_FLAG_DESCRIBES_VIDEO).setChannelCount(2).build();
      String signature=(String)call(a,"cobraTrackSignature",first);androidx.media3.common.TrackGroup group=new androidx.media3.common.TrackGroup("fixture-audio",second,first);
      androidx.media3.common.Tracks tracks=new androidx.media3.common.Tracks(java.util.Collections.singletonList(new androidx.media3.common.Tracks.Group(group,false,new int[]{androidx.media3.common.C.FORMAT_HANDLED,androidx.media3.common.C.FORMAT_HANDLED},new boolean[]{false,true})));
      androidx.media3.common.TrackSelectionOverride found=(androidx.media3.common.TrackSelectionOverride)call(a,"cobraSavedTrack",tracks,androidx.media3.common.C.TRACK_TYPE_AUDIO,signature,"en",0);assertNotNull(found);assertEquals(Integer.valueOf(1),found.trackIndices.get(0));assertEquals(group,found.mediaTrackGroup);
      assertNull(call(a,"cobraSavedTrack",tracks,androidx.media3.common.C.TRACK_TYPE_AUDIO,"","fr",0));
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionCustomSizeHasExplicitKeyboardSaveAndCancel()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);
    try{completionStore(a).edit().clear().commit();Object channel=completionChannel(a,0);String key=(String)call(a,"cobraPreferenceKey",channel);call(a,"cobraEditChannelSize",channel);measure(a,412,915);View sheet=(View)get(a,"mCobraActionSheet");android.widget.SeekBar width=sheet.findViewWithTag("cobra_channel_width"),height=sheet.findViewWithTag("cobra_channel_height");assertTrue(width.isFocusable());width.setProgress(65);height.setProgress(95);assertFalse(completionStore(a).contains(key));assertTrue(sheet.findViewWithTag("cobra_channel_size_apply").performClick());Object choice=call(a,"cobraReadChoice",key);assertEquals(11,get(choice,"aspect"));assertEquals(1.2f,(Float)get(choice,"x"),.001f);assertEquals(1.5f,(Float)get(choice,"y"),.001f);
      call(a,"cobraEditChannelSize",channel);((android.widget.SeekBar)((View)get(a,"mCobraActionSheet")).findViewWithTag("cobra_channel_width")).setProgress(10);a.onBackPressed();assertEquals(1.2f,(Float)get(call(a,"cobraReadChoice",key),"x"),.001f);
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionHealthPalettesAndLargeTextHaveHonestStates()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);
    try{call(a,"cobraOpenLiveTv");measure(a,412,915);Configuration config=new Configuration(a.getResources().getConfiguration());config.fontScale=1.5f;a.getResources().updateConfiguration(config,a.getResources().getDisplayMetrics());
      for(String mode:new String[]{"light","dark","oled"}){((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",mode).commit();call(a,"showCobraHealthSnapshot");measure(a,412,915);View sheet=(View)get(a,"mCobraActionSheet");assertTrue(completionText(sheet,"Cobra Health Center"));assertTrue(completionText(sheet,"not active"));assertTrue(completionText(sheet,"not a crash-free certificate"));assertNotNull(sheet.findViewWithTag("cobra_health_export"));org.json.JSONObject snapshot=new org.json.JSONObject((String)call(a,"cobraFreshHealthSnapshot"));assertEquals(1,snapshot.getInt("health_center_schema"));assertEquals(0,snapshot.getJSONArray("players").length());if(mode.equals("oled")){android.graphics.drawable.GradientDrawable background=(android.graphics.drawable.GradientDrawable)((ViewGroup)sheet).getChildAt(0).getBackground();assertEquals(android.graphics.Color.BLACK,background.getColor().getDefaultColor());}completionImage(a,"cobra-health-"+mode+"-large-text");a.onBackPressed();}
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void completionPreferencesPreservePeerVolumeAndIdleRecovery()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(24);androidx.media3.exoplayer.ExoPlayer first=null,second=null;
    try{completionStore(a).edit().clear().commit();Object channel=completionChannel(a,0),other=completionChannel(a,1);first=new androidx.media3.exoplayer.ExoPlayer.Builder(a).build();second=new androidx.media3.exoplayer.ExoPlayer.Builder(a).build();first.setVolume(.25f);second.setVolume(.75f);
      Object b1=construct("CobraPlayerBinding",a,first,channel),b2=construct("CobraPlayerBinding",a,second,other);((Map)get(a,"mCobraPlayerBindings")).put(first,b1);((Map)get(a,"mCobraPlayerBindings")).put(second,b2);
      String key=(String)call(a,"cobraPreferenceKey",channel);Object choice=call(a,"cobraReadChoice",key);put(choice,"audioLanguage","es");put(choice,"captions","off");assertEquals(true,call(a,"cobraWriteChoice",channel,key,choice));assertEquals("es",first.getTrackSelectionParameters().preferredAudioLanguages.get(0));assertTrue(first.getTrackSelectionParameters().disabledTrackTypes.contains(androidx.media3.common.C.TRACK_TYPE_TEXT));assertTrue(second.getTrackSelectionParameters().preferredAudioLanguages.isEmpty());assertEquals(.25f,first.getVolume(),.001f);assertEquals(.75f,second.getVolume(),.001f);
      put(a,"mCobraHealthForeground",true);for(int i=0;i<5;i++)call(a,"cobraInspectSurfaceRecovery");assertEquals(0,get(get(b1,"recovery"),"attempts"));assertEquals(0,get(get(b2,"recovery"),"attempts"));
      org.json.JSONArray players=new org.json.JSONObject((String)call(a,"cobraFreshHealthSnapshot")).getJSONArray("players");assertEquals(2,players.length());for(int i=0;i<2;i++){assertFalse(players.getJSONObject(i).getBoolean("surface_available"));assertEquals(0,players.getJSONObject(i).getInt("surface_recovery_attempts"));}
    }finally{if(first!=null)call(a,"cobraDisposePlayer",first);if(second!=null)call(a,"cobraDisposePlayer",second);clean(a);}
  }
