  private static final String COBRA_MINI_BACKGROUND="cobra_mini_background_playback";
  private static final String COBRA_FILE_PICKER_MODE="cobra_file_picker_mode";
  private static final String COBRA_FILE_PICKER_ASK="ask";
  private static final String COBRA_FILE_PICKER_SYSTEM="system";
  private static final String COBRA_FILE_PICKER_APPS="apps";
  private boolean mCobraMiniBackgroundActive=false;

  private String cobraNormalizeProviderGroup(String value){
    if(value==null)return "";
    return value.replace('\u00a0',' ').trim().replaceAll("\\s+"," ");
  }

  private boolean cobraMiniBackgroundEnabled(){return mPrefs!=null&&mPrefs.getBoolean(COBRA_MINI_BACKGROUND,false);}
  private String cobraMiniBackgroundLabel(){return cobraMiniBackgroundEnabled()?"ON":"OFF";}
  private boolean cobraMiniPreviewPlaying(){
    if(mPlayerOverlay!=null||mMultiOverlay!=null||mCobraPreviewPlayer==null)return false;
    try{int state=mCobraPreviewPlayer.getPlaybackState();return state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED&&(mCobraPreviewPlayer.isPlaying()||mCobraPreviewPlayer.getPlayWhenReady());}
    catch(Exception ignored){return false;}
  }
  private boolean cobraBeginMiniBackgroundPlayback(){
    if(!cobraMiniBackgroundEnabled()||!cobraMiniPreviewPlaying())return false;
    String title=mGuidePreviewChannel==null?"Cobra Live":mGuidePreviewChannel.name;
    boolean started=InfinityExtendedBackgroundService.startMiniPlayback(this,title);
    if(!started&&cobraMiniBackgroundEnabled())android.util.Log.w("InfinityBackground","Mini-player background audio unavailable");
    return started;
  }
  private void cobraEndMiniBackgroundPlayback(){
    if(mCobraMiniBackgroundActive||InfinityExtendedBackgroundService.isMiniPlaybackRunning())InfinityExtendedBackgroundService.stopMiniPlayback(this);
    mCobraMiniBackgroundActive=false;
  }
  private void showCobraMiniBackgroundPicker(){
    LinearLayout rows=cobraOpenSheet("Play in background","Applies only to the Cobra mini-player. Fullscreen playback keeps using Android picture-in-picture.","mini-background");
    boolean dark=cobraSheetIsDark();
    LinearLayout off=cobraSheetRow("settings","Off",cobraMiniBackgroundEnabled()?null:"Selected",false,dark,()->{mPrefs.edit().putBoolean(COBRA_MINI_BACKGROUND,false).apply();cobraEndMiniBackgroundPlayback();closeCobraActionSheet();showSettings();});off.setTag("cobra-mini-background:off");rows.addView(off);
    LinearLayout on=cobraSheetRow("audio","On",cobraMiniBackgroundEnabled()?"Selected":"Keep mini-player audio playing with Android media status",false,dark,()->{
      if(!InfinityExtendedBackgroundService.notificationsAllowed(this)){toast("Allow Infinity notifications to show native background playback");InfinityExtendedBackgroundService.openNotificationSettings(this);return;}
      mPrefs.edit().putBoolean(COBRA_MINI_BACKGROUND,true).apply();closeCobraActionSheet();toast("Mini-player background playback • On");showSettings();
    });on.setTag("cobra-mini-background:on");rows.addView(on);
  }

  private String cobraFilePickerMode(){String value=mPrefs==null?COBRA_FILE_PICKER_ASK:mPrefs.getString(COBRA_FILE_PICKER_MODE,COBRA_FILE_PICKER_ASK);return COBRA_FILE_PICKER_SYSTEM.equals(value)||COBRA_FILE_PICKER_APPS.equals(value)?value:COBRA_FILE_PICKER_ASK;}
  private String cobraFilePickerLabel(){String value=cobraFilePickerMode();return COBRA_FILE_PICKER_SYSTEM.equals(value)?"SYSTEM":COBRA_FILE_PICKER_APPS.equals(value)?"FILES APP":"ASK";}
  private void showCobraFilePickerPicker(){
    LinearLayout rows=cobraOpenSheet("File picker","Choose how Infinity opens files. Files app uses Android's app chooser and supports compatible managers such as MiXplorer.","file-picker");boolean dark=cobraSheetIsDark();String current=cobraFilePickerMode();
    String[] values={COBRA_FILE_PICKER_ASK,COBRA_FILE_PICKER_SYSTEM,COBRA_FILE_PICKER_APPS};String[] labels={"Ask every time","Android system picker","Files app chooser"};String[] details={"Choose System or Files app whenever a file is requested","Use Android Storage Access Framework","Choose MiXplorer or another compatible installed file manager"};
    for(int i=0;i<values.length;i++){final String value=values[i];LinearLayout row=cobraSheetRow("source",labels[i],value.equals(current)?"Selected":details[i],false,dark,()->{mPrefs.edit().putString(COBRA_FILE_PICKER_MODE,value).apply();closeCobraActionSheet();showSettings();});row.setTag("cobra-file-picker:"+value);rows.addView(row);}
  }
  private void cobraOpenFilePicker(int requestCode,String type,String[] mimeTypes,boolean persistable){
    String mode=cobraFilePickerMode();
    if(COBRA_FILE_PICKER_ASK.equals(mode)){
      LinearLayout rows=cobraOpenSheet("Choose file source","System keeps document-provider access. Files app lets you choose MiXplorer or another installed manager.","file-source");boolean dark=cobraSheetIsDark();
      rows.addView(cobraSheetRow("source","Android system picker","Storage Access Framework",false,dark,()->{closeCobraActionSheet();cobraLaunchFilePicker(requestCode,type,mimeTypes,persistable,false);}));
      rows.addView(cobraSheetRow("source","Files app","MiXplorer or another compatible file manager",false,dark,()->{closeCobraActionSheet();cobraLaunchFilePicker(requestCode,type,mimeTypes,persistable,true);}));
      return;
    }
    cobraLaunchFilePicker(requestCode,type,mimeTypes,persistable,COBRA_FILE_PICKER_APPS.equals(mode));
  }
  private void cobraLaunchFilePicker(int requestCode,String type,String[] mimeTypes,boolean persistable,boolean appChooser){
    Intent intent=new Intent(appChooser?Intent.ACTION_GET_CONTENT:Intent.ACTION_OPEN_DOCUMENT);intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType(type);if(mimeTypes!=null&&mimeTypes.length>0)intent.putExtra(Intent.EXTRA_MIME_TYPES,mimeTypes);intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);if(persistable&&!appChooser)intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
    try{startActivityForResult(appChooser?Intent.createChooser(intent,"Choose Files app"):intent,requestCode);}catch(android.content.ActivityNotFoundException missing){toast(appChooser?"No compatible Files app found":"Android file picker unavailable");}
  }
