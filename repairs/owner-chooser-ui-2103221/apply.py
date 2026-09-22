#!/usr/bin/env python3
"""2103221: drawer-owned Cobra section + styled Infinity/Cobra chooser options.

Parent: exact locked 2103217.
- Smart Return stays byte-identical.
- Only an explicit top-level drawer selection changes the active Cobra section.
- Every generic Cobra "primary view" fallback respects that drawer owner.
- Back from a top-level owned section backgrounds the app instead of stepping through Live TV.
- Both chooser gear menus use the existing Infinity-styled chooser dialog renderer.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103221
OLD_VERSION=2103217
OLD_NAME='1.0.9-Cobra-Media-Return-Context-RC1'
NEW_NAME='1.0.9-Cobra-Drawer-Owner-Chooser-UI-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b): return hashlib.sha256(b).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label} anchor drift ({s.count(a)})')
    return s.replace(a,b,1)
def mr(s,sig):
    i=s.find(sig);req(i>=0,'Missing '+sig);b=s.find('{',i);d=0
    for j in range(b,len(s)):
        if s[j]=='{': d+=1
        elif s[j]=='}':
            d-=1
            if d==0:return i,j+1
    raise RuntimeError('Unbalanced '+sig)
def method(s,sig):
    a,b=mr(s,sig);return s[a:b]
def replace_method(s,sig,new):
    a,b=mr(s,sig);return s[:a]+new.rstrip()+s[b:]

PROTECT_ACTIVITY=[
 'private void cobraRefreshAmbient()',
 'private void cobraApplyNightCinema(View header,View footer,View pause)',
 'private void cobraShowVodDetails(VodItem item)',
 'private void openSeries(VodItem item)',
 'private void startSinglePlayer(String url)',
 'private void playChannel(Channel channel)',
 'private void cobraStartLocalTimeshift',
 'private LoadResult loadXtream(LiveSource source)',
 'private LoadResult loadM3u(LiveSource source)',
 'private void showSettings()',
 'private void cobraShowSmartReturnSetting()',
 'private boolean cobraTrySmartReturn()',
 'private void cobraSaveSmartReturn()',
]
def hashes(s,sigs): return {x:hb(method(s,x).encode()) for x in sigs}

def patch_activity(path:Path):
    s=path.read_text()
    protected=hashes(s,PROTECT_ACTIVITY)

    field='  private final ArrayList<View> mCobraVodReturnViews = new ArrayList<>();\n'
    fields='''  private static final String COBRA_ACTIVE_SECTION_PREF="cobra_active_section_owner";
  private static final String COBRA_SECTION_LIVE="live";
  private static final String COBRA_SECTION_MOVIES="movies";
  private static final String COBRA_SECTION_SHOWS="shows";
  private static final String COBRA_SECTION_RECORDINGS="recordings";
  private static final String COBRA_SECTION_MY_LIST="my_list";
  private boolean mCobraOwnedPrimaryRouting=false;
'''+field
    s=once(s,field,fields,'active owner fields')

    marker='  private void cobraDiscardVodLandingReturn(){'
    helpers='''  private String cobraNormalizeActiveSection(String value){
    if(COBRA_SECTION_MOVIES.equals(value)||COBRA_SECTION_SHOWS.equals(value)||
        COBRA_SECTION_RECORDINGS.equals(value)||COBRA_SECTION_MY_LIST.equals(value)||
        COBRA_SECTION_LIVE.equals(value))return value;
    return COBRA_SECTION_LIVE;
  }

  private String cobraActiveSection(){
    return cobraNormalizeActiveSection(mPrefs.getString(COBRA_ACTIVE_SECTION_PREF,COBRA_SECTION_LIVE));
  }

  private void cobraSelectActiveSection(String destination){
    String section=null;
    if("TV".equals(destination))section=COBRA_SECTION_LIVE;
    else if("MOVIES".equals(destination))section=COBRA_SECTION_MOVIES;
    else if("SHOWS".equals(destination))section=COBRA_SECTION_SHOWS;
    else if("RECORDINGS".equals(destination))section=COBRA_SECTION_RECORDINGS;
    else if("MY LIST".equals(destination))section=COBRA_SECTION_MY_LIST;
    if(section!=null)mPrefs.edit().putString(COBRA_ACTIVE_SECTION_PREF,section).apply();
  }

  private boolean cobraBackOutOfOwnedLanding(){
    String owner=cobraActiveSection();
    String title=mCobraStageTitle==null?"":mCobraStageTitle;
    boolean landing=
        (COBRA_SECTION_MOVIES.equals(owner)&&"COBRA • MOVIES".equals(title))||
        (COBRA_SECTION_SHOWS.equals(owner)&&("COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title)))||
        (COBRA_SECTION_RECORDINGS.equals(owner)&&"COBRA • RECORDINGS".equals(title))||
        (COBRA_SECTION_MY_LIST.equals(owner)&&mCobraSmartWatchlist);
    if(!landing)return false;
    moveTaskToBack(true);
    return true;
  }

'''
    s=once(s,marker,helpers+marker,'active owner helpers')

    drawer_sig='private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)'
    drawer=method(s,drawer_sig)
    anchor='''      if(!settingsDestination)cobraDiscardVodLandingReturn();
      action.run();'''
    repl='''      if(!settingsDestination)cobraDiscardVodLandingReturn();
      cobraSelectActiveSection(destination);
      action.run();'''
    req(anchor in drawer,'drawer owner anchor missing')
    drawer=drawer.replace(anchor,repl,1)
    s=replace_method(s,drawer_sig,drawer)
    req(s.count('cobraSelectActiveSection(destination);')==1,'drawer must be the only active owner writer')

    # Centralize ALL legacy primary fallbacks through the drawer-selected owner.
    sig='private void showCobraPrimaryView()'
    old=method(s,sig)
    live=old.replace('private void showCobraPrimaryView()','private void cobraShowLivePrimaryView()',1)
    wrapper='''  private void showCobraPrimaryView() {
    if(!mCobraOwnedPrimaryRouting){
      String owner=cobraActiveSection();
      if(!COBRA_SECTION_LIVE.equals(owner)){
        mCobraOwnedPrimaryRouting=true;
        try{
          if(COBRA_SECTION_MOVIES.equals(owner)){showMovies();return;}
          if(COBRA_SECTION_SHOWS.equals(owner)){showSeries();return;}
          if(COBRA_SECTION_RECORDINGS.equals(owner)){showRecordings();return;}
          if(COBRA_SECTION_MY_LIST.equals(owner)){showWatchlist();return;}
        }finally{mCobraOwnedPrimaryRouting=false;}
      }
    }
    cobraShowLivePrimaryView();
  }

'''
    s=replace_method(s,sig,wrapper+live)

    # 2103217 inserted media-parent restore too late, after the generic internal fallback.
    # Move it before that fallback. Then top-level Movies/Shows/Recordings/My List back
    # backgrounds the task rather than forcing the legacy Live TV primary screen.
    back_sig='public void onBackPressed()'
    back=method(s,back_sig)
    back=back.replace('    if(cobraRestoreVodLandingReturn())return;\n','')
    internal='    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}'
    req(internal in back,'generic internal Back fallback missing')
    back=back.replace(internal,
        '    if(cobraRestoreVodLandingReturn())return;\n'
        '    if(cobraBackOutOfOwnedLanding())return;\n'
        +internal,1)
    req(back.index('cobraRestoreVodLandingReturn()')<back.index('if(!"root".equals(mCobraInternalScreen)'),
        'media restore must precede generic primary fallback')
    s=replace_method(s,back_sig,back)

    for token in ('COBRA_ACTIVE_SECTION_PREF','cobraBackOutOfOwnedLanding()',
                  'cobraShowLivePrimaryView()','cobraSelectActiveSection(destination)'):
        req(token in s,'owner contract missing '+token)

    path.write_text(s)
    req(hashes(s,PROTECT_ACTIVITY)==protected,'protected Cobra/Smart Return methods changed')

def patch_splash(path:Path):
    s=path.read_text()
    before_health=hb(method(s,'private void showInfinityHealthCenter()').encode())
    settings=method(s,'private void showExperienceCardSettings(String experience)')
    # Preserve every option and click action; replace only the visual builder selection.
    stock='''    (cobra ? new android.app.AlertDialog.Builder(this,
        "light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:
        android.R.style.Theme_Material_Dialog_Alert)
        : new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings"))'''
    styled='''    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings")'''
    req(stock in settings,'chooser settings builder preimage drift')
    settings=settings.replace(stock,styled,1)
    req('new android.app.AlertDialog.Builder' not in settings,'stock chooser settings dialog survived')
    req(settings.count('new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings")')==1,
        'styled chooser options builder missing')
    # Exact functional rows remain.
    for token in ('"Remember & launch " + label','"Launch " + label + " just this time"',
                  '"Ask every time"','"Infinity Health Center"','"Cobra Recovery"',
                  'launchInfinityExperience(experience)','showInfinityHealthCenter()','showCobraRecovery()'):
        req(token in settings,'chooser option/action lost '+token)
    s=replace_method(s,'private void showExperienceCardSettings(String experience)',settings)
    path.write_text(s)
    req(hb(method(s,'private void showInfinityHealthCenter()').encode())==before_health,
        'Infinity Health Center implementation changed')

def identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName')
    gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift');pack.write_text(p.replace(old,new))
    return gradle

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
        'Expected exact locked 2103217 source')
    activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
    splash=shell/(SOURCE+'Splash.java.in')
    smart=shell/(SOURCE+'CobraSmartReturn.java.in')
    main=shell/(SOURCE+'Main.java.in')
    for p in (activity,splash,smart,main):req(p.is_file(),'Missing '+str(p))
    smart_before=sha(smart);main_before=sha(main)

    patch_activity(activity)
    patch_splash(splash)
    gradle=identity(shell)

    req(sha(smart)==smart_before,'Smart Return file changed')
    req(sha(main)==main_before,'Kodi Main changed')
    req(receipt.get('native_engine_sha256')==NATIVE,'native engine drift')

    for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'Splash.java.in',
                 SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'receipt missing '+name)
        receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
      candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
      native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
      active_section_owner=True,active_section_changes_only_from_drawer=True,
      all_primary_fallbacks_respect_active_section=True,
      owned_landing_android_back='move task to background; owner unchanged',
      media_return_context_preserved=True,
      smart_return_untouched=True,smart_return_file_sha256=smart_before,
      cobra_options_styled=True,infinity_options_styled=True,
      chooser_options_renderer='CobraVisualRenderer.DialogBuilder / chooser.settings',
      chooser_option_actions_unchanged=True,
      health_center_unchanged=True,playback_unchanged=True,providers_unchanged=True,
      live_tv_blue_ambient_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():
        req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit221').mkdir(exist_ok=True)
    Path('audit221/scope.json').write_text(json.dumps({
      'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE,
      'smart_return_untouched':True,'smart_return_sha256':smart_before,
      'only_drawer_changes_active_section':True,
      'primary_fallback_routes_to_drawer_owner':True,
      'back_from_owned_landing_backgrounds_task':True,
      'media_parent_return_precedes_generic_back':True,
      'cobra_options_styled':True,'infinity_options_styled':True,
      'stock_alert_dialog_removed_from_both_chooser_option_surfaces':True,
      'chooser_option_actions_unchanged':True,'health_center_unchanged':True,
      'playback_unchanged':True,'providers_unchanged':True,'live_tv_blue_ambient_unchanged':True,
      'acceptance':[
        'Drawer > Movies; Android Back/edge gesture backgrounds app without changing owner; return/reopen => Movies',
        'Drawer > TV Shows; Android Back/edge gesture backgrounds app without changing owner; return/reopen => TV Shows',
        'Only selecting another top-level drawer destination changes the owner',
        'Cobra gear opens styled chooser options',
        'Infinity gear opens styled chooser options'
      ],
      'status':'TEST CANDIDATE'
    },indent=2)+'\n')
    print('PASS: 2103221 drawer-owner routing + styled Infinity/Cobra chooser options; Smart Return untouched')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True)
    apply(p.parse_args().shell)
if __name__=='__main__':main()
