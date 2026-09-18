  // @method cobraMiniPreviewPlaying
  private boolean cobraMiniPreviewPlaying(){
    if(!isCobraAsyncAlive()||isFinishing()||isDestroyed()||!mCobraHealthForeground||mPlayerOverlay!=null||mMultiOverlay!=null||mCobraPreviewPlayer==null||mCobraPreviewHost==null||!mCobraPreviewHost.isAttachedToWindow())return false;
    try{int state=mCobraPreviewPlayer.getPlaybackState();return state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED&&(mCobraPreviewPlayer.isPlaying()||(state==Player.STATE_BUFFERING&&mCobraPreviewPlayer.getPlayWhenReady()));}
    catch(RuntimeException ignored){return false;}
  }
  // @method cobraBeginMiniBackgroundPlayback
  private boolean cobraBeginMiniBackgroundPlayback(){
    if(!cobraMiniBackgroundEnabled()||!cobraMiniPreviewPlaying())return false;
    final ExoPlayer selected=mCobraPreviewPlayer;
    String title=mGuidePreviewChannel==null?"Cobra Live":mGuidePreviewChannel.name;
    boolean requested=InfinityExtendedBackgroundService.startMiniPlayback(this,selected,title,()->{
      if(mCobraPreviewPlayer==selected){mCobraMiniBackgroundActive=false;mBackgroundResumePlayers.remove(selected);}
    });
    if(requested&&mCobraPreviewTexture!=null){selected.clearVideoTextureView(mCobraPreviewTexture);mCobraMiniBackgroundSurfaceDetached=true;}
    return requested;
  }
  // @method cobraEndMiniBackgroundPlayback
  private void cobraEndMiniBackgroundPlayback(){
    InfinityExtendedBackgroundService.stopMiniPlayback(this);
    mCobraMiniBackgroundActive=false;
    if(mCobraMiniBackgroundSurfaceDetached&&mCobraHealthForeground&&mCobraPreviewPlayer!=null&&mCobraPreviewTexture!=null&&!isFinishing()&&!isDestroyed()){
      mCobraPreviewPlayer.setVideoTextureView(mCobraPreviewTexture);
      CobraPlayerBinding binding=mCobraPlayerBindings.get(mCobraPreviewPlayer);
      if(binding!=null)cobraFitBinding(binding);
    }
    mCobraMiniBackgroundSurfaceDetached=false;
  }
  // @method showCobraMiniBackgroundPicker
  private void showCobraMiniBackgroundPicker(){
    LinearLayout rows=cobraOpenSheet("Play in background","Mini-player audio only. Fullscreen continues to use picture-in-picture.","mini-background");
    cobraAddMiniBackgroundSwitch(rows);
  }
  // @new cobraAddMiniBackgroundSwitch
  private void cobraAddMiniBackgroundSwitch(LinearLayout rows){
    android.widget.Switch toggle=new android.widget.Switch(this);
    toggle.setText("Play in background");toggle.setTextColor(cobraSheetIsDark()?Color.WHITE:cobraThemeColor("text",mTheme.text));
    toggle.setTextOn("On");toggle.setTextOff("Off");toggle.setShowText(true);toggle.setTag("cobra-mini-background-switch");
    toggle.setMinHeight(dp(56));toggle.setPadding(dp(12),dp(8),dp(12),dp(8));toggle.setChecked(cobraMiniBackgroundEnabled());
    toggle.setOnCheckedChangeListener((button,checked)->{
      if(checked&&!InfinityExtendedBackgroundService.notificationsAllowed(this)){button.setChecked(false);toast("Allow Infinity notifications, then enable background playback");InfinityExtendedBackgroundService.openNotificationSettings(this);return;}
      mPrefs.edit().putBoolean(COBRA_MINI_BACKGROUND,checked).apply();if(!checked)cobraEndMiniBackgroundPlayback();
    });rows.addView(toggle,new LinearLayout.LayoutParams(-1,-2));
  }
  // @method cobraLaunchFilePicker
  private void cobraLaunchFilePicker(int requestCode,String type,String[] mimeTypes,boolean persistable,boolean appChooser){
    Intent intent=new Intent(appChooser?Intent.ACTION_GET_CONTENT:Intent.ACTION_OPEN_DOCUMENT);
    intent.addCategory(Intent.CATEGORY_OPENABLE);
    intent.setType(appChooser&&"application/zip".equals(type)?"*/*":type);
    if(mimeTypes!=null&&mimeTypes.length>0)intent.putExtra(Intent.EXTRA_MIME_TYPES,mimeTypes);
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
    if(persistable&&!appChooser)intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
    try{startActivityForResult(appChooser?Intent.createChooser(intent,"Choose Files app"):intent,requestCode);}
    catch(android.content.ActivityNotFoundException|SecurityException unavailable){
      toast(appChooser?"Files app unavailable. Choose Android system picker instead.":"Android document picker unavailable. Choose Files app instead.");
    }
  }
  // @new cobraProviderGroups
  private java.util.SortedMap<String,Integer> cobraProviderGroups(boolean sourceScoped){
    java.util.TreeMap<String,Integer> groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);
    for(Channel c:mChannels){
      if(!cobraChannelAllowed(c)||(sourceScoped&&!mCobraGuideSource.isEmpty()&&!mCobraGuideSource.equals(sourceIdForChannel(c))))continue;
      String group=cobraNormalizeProviderGroup(c.group);if(group.isEmpty())group="Other";
      Integer count=groups.get(group);groups.put(group,count==null?1:count+1);
    }
    return groups;
  }
  // @new cobraGroupMatches
  private boolean cobraGroupMatches(String selected,String group){
    String normalized=cobraNormalizeProviderGroup(group);if(normalized.isEmpty())normalized="Other";
    return cobraNormalizeProviderGroup(selected).equalsIgnoreCase(normalized);
  }
  // @new cobraSheetSafeBounds
  private android.graphics.Rect cobraSheetSafeBounds(View parent,boolean playerSettings){
    int w=Math.max(1,parent.getMeasuredWidth()),h=Math.max(1,parent.getMeasuredHeight());
    android.graphics.Rect safe=new android.graphics.Rect(0,0,w,h);
    android.view.WindowInsets insets=Build.VERSION.SDK_INT>=23?parent.getRootWindowInsets():null;
    if(insets!=null){safe.left=Math.min(w-1,insets.getSystemWindowInsetLeft());safe.top=Math.min(h-1,insets.getSystemWindowInsetTop());safe.right=Math.max(safe.left+1,w-insets.getSystemWindowInsetRight());safe.bottom=Math.max(safe.top+1,h-insets.getSystemWindowInsetBottom());}
    int pad=dp(12);safe.inset(Math.min(pad,Math.max(0,(safe.width()-1)/2)),Math.min(pad,Math.max(0,(safe.height()-1)/2)));
    // Keep the bottom player controls visible rather than covering the More button.
    if(playerSettings&&safe.height()>dp(240))safe.bottom-=dp(64);
    return safe;
  }
  // @new cobraConstrainSheet
  private void cobraConstrainSheet(FrameLayout scrim,LinearLayout panel,boolean playerSettings){
    if(scrim!=mCobraActionSheet||scrim.getMeasuredWidth()<=0||scrim.getMeasuredHeight()<=0)return;
    android.graphics.Rect safe=cobraSheetSafeBounds(scrim,playerSettings);
    FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)panel.getLayoutParams();
    int width=Math.max(1,Math.min(dp(440),safe.width()));int gravity=playerSettings||scrim.getMeasuredHeight()>scrim.getMeasuredWidth()?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:Gravity.RIGHT|Gravity.CENTER_VERTICAL;
    int left=safe.left,right=scrim.getMeasuredWidth()-safe.right,top=safe.top,bottom=scrim.getMeasuredHeight()-safe.bottom;
    if(p.width!=width||p.gravity!=gravity||p.leftMargin!=left||p.rightMargin!=right||p.topMargin!=top||p.bottomMargin!=bottom){p.width=width;p.height=-2;p.gravity=gravity;p.setMargins(left,top,right,bottom);panel.setLayoutParams(p);}
  }
