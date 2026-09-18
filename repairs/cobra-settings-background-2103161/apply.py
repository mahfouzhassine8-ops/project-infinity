#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,json,argparse
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
SPLASH='tools/android/packaging/xbmc/src/Splash.java.in'
RENDER='tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in'
THEME='tools/android/packaging/xbmc/src/CobraVisualTheme.java.in'
HASHES={
 ACT:'d0257bab6d079bf040534944813e5cd3cd62ef31e8bb904c0f24bfa3ba71ab33',
 SPLASH:'86251b07ce742124086792babd731bc20b60eeccd11eef3c2c62b835d0b11851',
 RENDER:'fdd984093f882ba0d663fad5dc68ef90e4de09fcbb4a1f8a953159f8c1a95ba7',
 THEME:'c380fc86a25aaa5800c4533a38c59e7ca3acb5437220d3d3fec01405c1e14aab',
}
def sha(x):
 if isinstance(x,str):x=x.encode()
 return hashlib.sha256(x).hexdigest()
def span(s,name):
 pat=re.compile(r'\n  (?:@Override\s+)?(?:public|private|protected)\s+[^\n;{}]*\b'+re.escape(name)+r'\s*\([^)]*\)\s*(?:throws\s+[^\{]+)?\{')
 ms=list(pat.finditer(s))
 if len(ms)!=1: raise ValueError(f'{name}: expected one method, got {len(ms)}')
 m=ms[0];start=m.start()+1;i=m.end();d=1;in_str=False;quote='';esc=False
 while i<len(s) and d:
  c=s[i]
  if in_str:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c==quote:in_str=False
  else:
   if c in ('"',"'"):in_str=True;quote=c
   elif c=='{':d+=1
   elif c=='}':d-=1
  i+=1
 if d: raise ValueError('unclosed '+name)
 return start,i
def replace_method(s,name,new):
 a,b=span(s,name);return s[:a]+new.rstrip()+s[b:]
def insert_before_final(s,block):
 i=s.rfind('\n}')
 if i<0:raise ValueError('no final class brace')
 return s[:i]+'\n'+block.rstrip()+'\n'+s[i:]

def patch_activity(s):
 show='''  private void showSettings() {
    mCobraInternalScreen = "internal";
    clearStage("COBRA • SETTINGS");
    status("One Infinity app • Cobra Live runtime");

    LinearLayout list = new LinearLayout(this);
    list.setOrientation(LinearLayout.VERTICAL);
    list.setPadding(0, dp(vtheme().dimension("cobra.showSettings.dimensions.1",4)), 0, dp(vtheme().dimension("cobra.showSettings.dimensions.2",12)));

    Button chooser = action(vtheme().copy("cobra.showSettings.copy.1","ASK WHICH EXPERIENCE ON NEXT LAUNCH"));
    chooser.setOnClickListener(v -> {
      getSharedPreferences(EXPERIENCE_PREFS, MODE_PRIVATE).edit().remove(EXPERIENCE_DEFAULT).apply();
      toast("Experience chooser will appear next launch");
    });

    Button installUi = action("INSTALL COBRA UI / VISUAL THEME ZIP");
    installUi.setTag("cobra_theme_install");
    installUi.setOnClickListener(v -> openCobraUiPackagePicker());

    Button guideView = action(vtheme().copy("cobra.showSettings.copy.3","GUIDE VIEW  •  ") + cobraGuideViewLabel());
    guideView.setOnClickListener(v -> showCobraGuideViewPicker(false));

    Button appearance = action(vtheme().copy("cobra.showSettings.copy.4","APPEARANCE  •  ") + cobraAppearanceLabel());
    appearance.setOnClickListener(v -> showCobraAppearancePicker());

    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());

    TextView uiState = text(activeCobraUiLabel(), cobraThemeColor("accent_soft", mTheme.accentSoft), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);

    TextView visualThemeState = text("VISUAL THEME  •  " + vtheme().displayName(),
        cobraThemeColor("accent_soft", mTheme.accentSoft), 13, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    visualThemeState.setTag("cobra_visual_theme_state");

    Button previousTheme = cobraThemeRecoveryButton("PREVIOUS VISUAL THEME", "cobra-visual-theme-controls:previous");
    previousTheme.setOnClickListener(v -> vtheme().restorePrevious(this, () -> { if(!isFinishing()&&!isDestroyed()){toast("Previous visual theme restored");showSettings();} }));

    Button builtInTheme = cobraThemeRecoveryButton("REMOVE VISUAL THEME  •  BUILT-IN APPEARANCE", "cobra-visual-theme-controls:builtin");
    builtInTheme.setOnClickListener(v -> vtheme().restoreBuiltIn(this, () -> { if(!isFinishing()&&!isDestroyed()){toast("Built-in appearance restored");showSettings();} }));

    Button reloadTheme = action(vtheme().copy("cobra.showSettings.copy.5","RELOAD COBRA UI THEME"));
    reloadTheme.setOnClickListener(v -> {
      mTheme = Theme.load(this);mUi = UiContract.load(this);buildShell();showCobraPrimaryView();toast("Cobra UI reloaded");
    });

    Button refresh = action(vtheme().copy("cobra.showSettings.copy.6","REFRESH CURRENT SOURCE"));
    refresh.setOnClickListener(v -> loadActiveSource(true));
    Button allSources = action(vtheme().copy("cobra.showSettings.copy.7","REFRESH ALL ENABLED SOURCES"));
    allSources.setOnClickListener(v -> loadAllEnabledSources(true));
    Button profiles = action(vtheme().copy("cobra.showSettings.copy.8","PROFILES & PARENTAL CONTROLS"));
    profiles.setOnClickListener(v -> showProfiles());
    Button health = action(vtheme().copy("cobra.showSettings.copy.9","COBRA HEALTH CENTER"));
    health.setOnClickListener(v -> showCobraHealthCenter());
    Button exportDiagnostics = action(vtheme().copy("cobra.showSettings.copy.10","EXPORT CRASH & DIAGNOSTICS ZIP"));
    exportDiagnostics.setOnClickListener(v -> showCobraDiagnosticExport());
    Button customEpg = action(vtheme().copy("cobra.showSettings.copy.11","CUSTOM EPG FOR ACTIVE SOURCE"));
    customEpg.setOnClickListener(v -> editCustomEpg());

    TextView subscriptionStatus = text(cobraSubscriptionCachedLabel(), cobraThemeColor("accent_soft", mTheme.accentSoft), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    subscriptionStatus.setTag("cobra_subscription_status");

    TextView themeInfo = text(
        "VISUAL THEME RUNTIME 2\n" +
        "Theme ZIPs can change Cobra presentation without replacing playback, providers or the native engine.",
        cobraThemeColor("muted", mTheme.muted), 14, Gravity.LEFT | Gravity.CENTER_VERTICAL);

    list.addView(chooser, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(installUi, new LinearLayout.LayoutParams(-1, dp(60)));
    list.addView(appearance, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));
    list.addView(visualThemeState, new LinearLayout.LayoutParams(-1, dp(48)));
    list.addView(previousTheme, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(builtInTheme, new LinearLayout.LayoutParams(-1, dp(62)));
    list.addView(reloadTheme, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(refresh, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(allSources, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(profiles, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(health, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(exportDiagnostics, new LinearLayout.LayoutParams(-1, dp(64)));
    list.addView(customEpg, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(subscriptionStatus, new LinearLayout.LayoutParams(-1, dp(86)));
    list.addView(themeInfo, new LinearLayout.LayoutParams(-1, dp(96)));

    vtheme().tree(list,"settings");
    ScrollView settingsScroll = new ScrollView(this);
    settingsScroll.setFillViewport(true);settingsScroll.addView(list);
    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));
    refreshCobraSubscriptionStatus();
  }'''
 s=replace_method(s,'showSettings',show)
 health_start='root.put("background_stopped",mBackgroundStopped);root.put("picture_in_picture",mInPictureInPicture);'
 if health_start not in s:raise ValueError('health anchor drift')
 s=s.replace(health_start,health_start+'root.put("background_mode",cobraBackgroundModeLabel());root.put("extended_background_requested",InfinityExtendedBackgroundService.isEnabled(this));root.put("extended_background_running",InfinityExtendedBackgroundService.isRunning());',1)
 helpers='''  private String cobraBackgroundModeLabel(){
    return InfinityExtendedBackgroundService.isEnabled(this)?"EXTENDED":"NORMAL";
  }

  private void showCobraBackgroundModePicker(){
    LinearLayout rows=cobraOpenSheet("Background Mode","Normal uses standard Android lifecycle behavior. Extended preserves the Infinity session while Android allows; it does not guarantee uninterrupted background media playback.","background-mode");
    boolean dark=cobraSheetIsDark();
    LinearLayout normal=cobraSheetRow("settings","Normal",InfinityExtendedBackgroundService.isEnabled(this)?null:"Selected",false,dark,()->{
      InfinityExtendedBackgroundService.setEnabled(this,false);closeCobraActionSheet();toast("Infinity background mode • Normal");showSettings();
    });normal.setTag("cobra-background-mode:normal");rows.addView(normal);
    LinearLayout extended=cobraSheetRow("settings","Extended",InfinityExtendedBackgroundService.isEnabled(this)?"Selected":"Preserve session continuity with a foreground notification",false,dark,()->{
      if(!InfinityExtendedBackgroundService.notificationsAllowed(this)){
        toast("Allow Infinity notifications, then choose Extended again");InfinityExtendedBackgroundService.openNotificationSettings(this);return;
      }
      boolean accepted=InfinityExtendedBackgroundService.setEnabled(this,true);closeCobraActionSheet();toast(accepted?"Infinity background mode • Extended requested":"Android refused Extended background mode");showSettings();
    });extended.setTag("cobra-background-mode:extended");rows.addView(extended);
  }

  private Button cobraThemeRecoveryButton(String label,String tag){
    Button button=new Button(this);button.setText(label);button.setAllCaps(false);button.setTextColor(0xfff7faff);button.setTextSize(13);button.setTag(tag);
    button.setPadding(dp(12),dp(7),dp(12),dp(7));button.setBackground(focusSurface(0xff0b1623,0xff4cbcff,14));button.setStateListAnimator(null);button.setMinHeight(dp(48));return button;
  }'''
 s=insert_before_final(s,helpers)
 return s

def patch_splash(s):
 a,b=span(s,'showVisualExperienceScene');block=s[a:b]
 old='root.setOnLongClickListener(v->{vtheme().manager(this);return true;});setContentView(root);slots.get("enter.infinity").requestFocus();'
 new='''root.setOnLongClickListener(v->{vtheme().manager(this);return true;});
      root.setOnApplyWindowInsetsListener((v,insets)->{int left=insets.getSystemWindowInsetLeft(),top=insets.getSystemWindowInsetTop(),right=insets.getSystemWindowInsetRight(),bottom=insets.getSystemWindowInsetBottom();if(v.getPaddingLeft()!=left||v.getPaddingTop()!=top||v.getPaddingRight()!=right||v.getPaddingBottom()!=bottom)v.setPadding(left,top,right,bottom);return insets;});
      setContentView(root);root.requestApplyInsets();slots.get("enter.infinity").requestFocus();'''
 if block.count(old)!=1:raise ValueError('safe area anchor drift')
 block=block.replace(old,new,1)
 return s[:a]+block+s[b:]

def patch_renderer(s):
 old='if(view==null||"cobra-visual-theme-controls".equals(view.getTag())||view instanceof TextureView'
 new='if(view==null||(view.getTag() instanceof String&&((String)view.getTag()).startsWith("cobra-visual-theme-controls"))||view instanceof TextureView'
 if s.count(old)!=1:raise ValueError('renderer recovery tag anchor drift')
 s=s.replace(old,new,1)
 manager='''  public String displayName(){String name=active.data.optString("name","").trim();return name.isEmpty()?active.id:name;}
  public void restoreBuiltIn(Activity activity,Runnable after){
    IO.execute(()->{try{synchronized(CobraVisualTheme.STORE_LOCK){CobraVisualTheme.reset(activity.getApplicationContext());publish(CobraVisualTheme.builtin(),"Built-in appearance restored");}if(after!=null)MAIN.post(after);}catch(Exception e){MAIN.post(()->Toast.makeText(activity,"Theme reset failed; current theme unchanged",Toast.LENGTH_LONG).show());}});
  }
  public void restorePrevious(Activity activity,Runnable after){
    IO.execute(()->{try{synchronized(CobraVisualTheme.STORE_LOCK){publish(CobraVisualTheme.rollback(activity.getApplicationContext()),"Previous theme restored");}if(after!=null)MAIN.post(after);}catch(Exception e){MAIN.post(()->Toast.makeText(activity,"Previous theme unavailable; current theme unchanged",Toast.LENGTH_LONG).show());}});
  }
  public void manager(Activity activity){
    new AlertDialog.Builder(activity).setTitle("Cobra theme controls").setMessage(description()+"\n\nReset and rollback change presentation only. Reopen menus to refresh source-driven layout and copy. No playlists or playback preferences are deleted.")
      .setPositiveButton("Built-in appearance",(d,w)->restoreBuiltIn(activity,null))
      .setNeutralButton("Previous theme",(d,w)->restorePrevious(activity,null))
      .setNegativeButton("Close",null).show();
  }'''
 a,b=span(s,'manager');s=s[:a]+manager+s[b:]
 return s

def patch_theme(s):
 old='public static final int RUNTIME=2, BUILD=2103160;'
 new='public static final int RUNTIME=2, BUILD=2103161;'
 if s.count(old)!=1:raise ValueError('theme build anchor drift')
 return s.replace(old,new,1)

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 funcs={ACT:patch_activity,SPLASH:patch_splash,RENDER:patch_renderer,THEME:patch_theme};report={'base_build':2103160,'target_build':2103161,'files':{}}
 for rel,fn in funcs.items():
  path=a.source/rel;before=path.read_text();actual=sha(before)
  if actual!=HASHES[rel]:raise ValueError(f'preimage drift {rel}: {actual}')
  after=fn(before);path.write_text(after);report['files'][rel]={'before':actual,'after':sha(after)}
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: exact 2103160 -> 2103161 settings/theme/background/safe-area delta applied')
if __name__=='__main__':main()
