#!/usr/bin/env python3
"""2103221 — surgical Cobra drawer-owned section persistence.

Parent is the exact locked 2103217 source state.
Only the Cobra activity navigation owner is changed.
Splash/chooser, Cobra Settings, Smart Return implementation, Main, playback,
providers, native engine and resources are protected.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION=2103221
OLD_VERSION=2103217
OLD_NAME='1.0.9-Cobra-Media-Return-Context-RC1'
NEW_NAME='1.0.9-Cobra-Drawer-Owner-Surgical-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT_ACTIVITY='f94415e13b3c83fa23f739335a109d14d357d977236d10cf5b54c5b91b114203'
PARENT_SPLASH='773e58b93abc782410b9d4cc4d3a69fb854b29e63d888ee9bc660834fddb7723'
PARENT_SMART='7bf7dc411149bee5482f5390d986a9e375b3b6b28f02a1e35bf1d6e92855b8fb'
PARENT_MAIN='ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318'

def hb(b): return hashlib.sha256(b).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label} anchor drift ({s.count(a)})')
    return s.replace(a,b,1)
def mr(s,sig):
    i=s.find(sig); req(i>=0,'Missing '+sig)
    b=s.find('{',i); d=0
    for j in range(b,len(s)):
        if s[j]=='{': d+=1
        elif s[j]=='}':
            d-=1
            if d==0: return i,j+1
    raise RuntimeError('Unbalanced '+sig)
def method(s,sig):
    a,b=mr(s,sig); return s[a:b]
def replace_method(s,sig,new):
    a,b=mr(s,sig); return s[:a]+new.rstrip()+s[b:]

PROTECT=[
 'private void showSettings()',
 'private void cobraShowSmartReturnSetting()',
 'private boolean cobraTrySmartReturn()',
 'private void cobraSaveSmartReturn()',
 'private void cobraShowVodDetails(VodItem item)',
 'private void openSeries(VodItem item)',
 'private void startSinglePlayer(String url)',
 'private void playChannel(Channel channel)',
 'private void cobraStartLocalTimeshift',
 'private LoadResult loadXtream(LiveSource source)',
 'private LoadResult loadM3u(LiveSource source)',
 'private void cobraRefreshAmbient()',
]
def protected_hashes(s):
    return {sig:hb(method(s,sig).encode()) for sig in PROTECT}

def patch_activity(path:Path):
    s=path.read_text()
    req(hb(s.encode())==PARENT_ACTIVITY,'Not exact locked 2103217 InfinityLiveActivity source')
    protected=protected_hashes(s)

    field='  private final ArrayList<View> mCobraVodReturnViews = new ArrayList<>();\n'
    fields='''  private static final String COBRA_ACTIVE_SECTION_PREF="cobra_active_section_owner";
  private static final String COBRA_SECTION_LIVE="live";
  private static final String COBRA_SECTION_MOVIES="movies";
  private static final String COBRA_SECTION_SHOWS="shows";
  private static final String COBRA_SECTION_RECORDINGS="recordings";
  private static final String COBRA_SECTION_MY_LIST="my_list";
  private String mCobraActiveSection="";
'''+field
    s=once(s,field,fields,'Active owner fields')

    marker='  private void cobraDiscardVodLandingReturn(){'
    helpers='''  private String cobraNormalizeActiveSection(String value){
    if(COBRA_SECTION_MOVIES.equals(value)||COBRA_SECTION_SHOWS.equals(value)||
        COBRA_SECTION_RECORDINGS.equals(value)||COBRA_SECTION_MY_LIST.equals(value)||
        COBRA_SECTION_LIVE.equals(value))return value;
    return COBRA_SECTION_LIVE;
  }

  private String cobraActiveSection(){
    if(mCobraActiveSection==null||mCobraActiveSection.isEmpty())
      mCobraActiveSection=cobraNormalizeActiveSection(
          mPrefs.getString(COBRA_ACTIVE_SECTION_PREF,COBRA_SECTION_LIVE));
    return mCobraActiveSection;
  }

  private void cobraSelectActiveSectionFromDrawer(String destination){
    String section=null;
    if("TV".equals(destination))section=COBRA_SECTION_LIVE;
    else if("MOVIES".equals(destination))section=COBRA_SECTION_MOVIES;
    else if("SHOWS".equals(destination))section=COBRA_SECTION_SHOWS;
    else if("RECORDINGS".equals(destination))section=COBRA_SECTION_RECORDINGS;
    else if("MY LIST".equals(destination))section=COBRA_SECTION_MY_LIST;
    if(section==null)return;
    mCobraActiveSection=section;
    mPrefs.edit().putString(COBRA_ACTIVE_SECTION_PREF,section).apply();
  }

  private boolean cobraIsActiveSectionLanding(){
    String owner=cobraActiveSection();
    String title=mCobraStageTitle==null?"":mCobraStageTitle;
    if(COBRA_SECTION_MOVIES.equals(owner))return "COBRA • MOVIES".equals(title);
    if(COBRA_SECTION_SHOWS.equals(owner))
      return "COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title);
    if(COBRA_SECTION_RECORDINGS.equals(owner))return "COBRA • RECORDINGS".equals(title);
    if(COBRA_SECTION_MY_LIST.equals(owner))return mCobraSmartWatchlist;
    return false;
  }

  private String cobraVisibleOwnedSection(){
    if(mCobraVodReturnCaptured)return mCobraVodReturnSeries?COBRA_SECTION_SHOWS:COBRA_SECTION_MOVIES;
    if(mCobraSmartWatchlist)return COBRA_SECTION_MY_LIST;
    String title=mCobraStageTitle==null?"":mCobraStageTitle;
    if("COBRA • MOVIES".equals(title))return COBRA_SECTION_MOVIES;
    if("COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title))return COBRA_SECTION_SHOWS;
    if("COBRA • RECORDINGS".equals(title))return COBRA_SECTION_RECORDINGS;
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return COBRA_SECTION_LIVE;
    if("COBRA • LIVE TV".equals(title)||"COBRA • TV GRID".equals(title))return COBRA_SECTION_LIVE;
    return "";
  }

  private void cobraReturnToActiveSection(){
    if(mPrefs==null||mStage==null||isFinishing())return;
    String section=cobraActiveSection();
    stopCobraPreview();
    mCobraInternalScreen="internal";
    if(COBRA_SECTION_MOVIES.equals(section)){showMovies();return;}
    if(COBRA_SECTION_SHOWS.equals(section)){showSeries();return;}
    if(COBRA_SECTION_RECORDINGS.equals(section)){showRecordings();return;}
    if(COBRA_SECTION_MY_LIST.equals(section)){showWatchlist();return;}
    mCobraInternalScreen="root";
    showCobraPrimaryView();
  }

  private void cobraReconcileActiveSectionAfterEntry(){
    if(mPrefs==null||mStage==null||isFinishing()||mSources.isEmpty())return;
    if(mPlayerOverlay!=null||mMultiOverlay!=null||isCobraInPictureInPicture())return;
    String visible=cobraVisibleOwnedSection();
    if(visible.isEmpty()||visible.equals(cobraActiveSection()))return;
    cobraReturnToActiveSection();
  }

'''
    s=once(s,marker,helpers+marker,'Active owner helpers')

    # Only drawer choices may write the owner.
    drawer=method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)')
    anchor='''      if(!settingsDestination)cobraDiscardVodLandingReturn();
      action.run();'''
    repl='''      if(!settingsDestination)cobraDiscardVodLandingReturn();
      cobraSelectActiveSectionFromDrawer(destination);
      action.run();'''
    req(anchor in drawer,'Drawer owner anchor drift')
    drawer=drawer.replace(anchor,repl,1)
    s=replace_method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)',drawer)

    # Fix the actual bug: 2103217's early internal-screen fallback went to Live TV
    # before the media/owner logic could run.
    back=method(s,'public void onBackPressed()')
    req('if(cobraRestoreVodLandingReturn())return;' in back,'2103217 media return hook missing')
    back=back.replace('    if(cobraRestoreVodLandingReturn())return;\n','',1)
    old='    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}'
    new='''    if(cobraRestoreVodLandingReturn())return;
    if(cobraIsActiveSectionLanding()){moveTaskToBack(true);return;}
    if(!"root".equals(mCobraInternalScreen)){cobraReturnToActiveSection();return;}
    if(!COBRA_SECTION_LIVE.equals(cobraActiveSection())){cobraReturnToActiveSection();return;}'''
    req(old in back,'Legacy internal->Live TV fallback missing')
    back=back.replace(old,new,1)
    s=replace_method(s,'public void onBackPressed()',back)

    # Lifecycle/shell rebuild paths must restore the drawer owner instead of
    # silently choosing Live TV. Live TV itself is unchanged when it is the owner.
    for sig in (
        'public void onConfigurationChanged(Configuration configuration)',
        'private void loadActiveSource(boolean showBusy)',
        'private void reloadCobraUiIfChanged()',
        'private void rebuildCobraShellIfNeeded()',
        'private void cobraConsumeLauncherPipReturn()',
    ):
        m=method(s,sig)
        if 'showCobraPrimaryView();' in m:
            m=m.replace('showCobraPrimaryView();','cobraReturnToActiveSection();')
            s=replace_method(s,sig,m)

    # Keep Smart Return implementation byte-identical. Only its old fallback is
    # redirected to the persistent drawer owner.
    fallback='if(!cobraTrySmartReturn())showCobraPrimaryView();'
    count=s.count(fallback)
    req(count>=2,'Expected 2103217 Smart Return entry fallbacks')
    s=s.replace(fallback,
        'if(!cobraTrySmartReturn())cobraReturnToActiveSection();else mMain.post(this::cobraReconcileActiveSectionAfterEntry);')

    # Warm resume: do nothing if current/temporary UI is valid; correct only a
    # top-level mismatch produced by Android lifecycle reconstruction.
    resume=method(s,'protected void onResume()')
    anchor='    mMain.post(()->{cobraConsumeLauncherPipReturn();cobraApplySystemBarsForSurface();});'
    req(anchor in resume,'Resume anchor drift')
    resume=resume.replace(anchor,anchor+'\n    mMain.postDelayed(this::cobraReconcileActiveSectionAfterEntry,160L);',1)
    s=replace_method(s,'protected void onResume()',resume)

    # Player close/rebuild should return to the drawer-selected owner.
    for sig in ('private void closeFullscreenToCobraView()',):
        m=method(s,sig)
        m=m.replace('showCobraPrimaryView();','cobraReturnToActiveSection();')
        s=replace_method(s,sig,m)

    req(s.count('cobraSelectActiveSectionFromDrawer(destination);')==1,
        'Drawer must be the only owner writer')
    for token in (
        'COBRA_ACTIVE_SECTION_PREF','cobraIsActiveSectionLanding()',
        'cobraReturnToActiveSection()','cobraReconcileActiveSectionAfterEntry',
        'if(cobraIsActiveSectionLanding()){moveTaskToBack(true);return;}',
    ):
        req(token in s,'Missing 2103221 owner contract: '+token)

    # Absolutely no collateral changes to protected behavior.
    req(protected_hashes(s)==protected,'Protected Cobra behavior changed')
    path.write_text(s)

def patch_identity(shell):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in'
    g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name')
    gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py')
    r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','Runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'Runtime name')
    runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py')
    p=pack.read_text(); old='Infinity-'+OLD_NAME; new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'Packager identity drift')
    pack.write_text(p.replace(old,new))
    return gradle

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
        'Expected exact 2103217 receipt')

    activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
    splash=shell/(SOURCE+'Splash.java.in')
    smart=shell/(SOURCE+'CobraSmartReturn.java.in')
    main=shell/(SOURCE+'Main.java.in')
    req(sha(activity)==PARENT_ACTIVITY,'2103217 Activity hash drift')
    req(sha(splash)==PARENT_SPLASH,'2103217 chooser/settings UI hash drift')
    req(sha(smart)==PARENT_SMART,'2103217 Smart Return hash drift')
    req(sha(main)==PARENT_MAIN,'2103217 Main hash drift')

    settings_before=hb(method(activity.read_text(),'private void showSettings()').encode())
    patch_activity(activity)
    gradle=patch_identity(shell)

    # Hard UI/smart-return gates: these files/methods may not move at all.
    req(sha(splash)==PARENT_SPLASH,'Chooser/settings UI changed')
    req(sha(smart)==PARENT_SMART,'Smart Return implementation changed')
    req(sha(main)==PARENT_MAIN,'Main changed')
    req(hb(method(activity.read_text(),'private void showSettings()').encode())==settings_before,
        'Cobra Settings UI changed')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine drift')

    for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'CobraSmartReturn.java.in',
                 SOURCE+'Splash.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'Receipt missing '+name)
        receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in'
    receipt['files'][rel]['after']=sha(gradle)

    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
      candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
      native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
      drawer_owned_section=True,active_section_changes_only_from_drawer=True,
      android_back_top_level_moves_task_to_back=True,
      android_back_internal_returns_to_drawer_owner=True,
      cold_entry_restores_drawer_owner=True,warm_resume_reconciles_drawer_owner=True,
      movies_stays_movies=True,tv_shows_stays_tv_shows=True,recordings_stays_recordings=True,
      my_list_stays_my_list=True,live_tv_changes_only_when_drawer_selected=True,
      smart_return_untouched=True,smart_return_file_sha256=PARENT_SMART,
      chooser_settings_ui_unchanged=True,splash_file_sha256=PARENT_SPLASH,
      cobra_settings_ui_unchanged=True,cobra_settings_method_sha256=settings_before,
      media_return_context_preserved=True,playback_protected=True,providers_protected=True,
      native_engine_unchanged=True,
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():
        req(sha(shell/name)==row['after'],'Final receipt drift: '+name)

    Path('audit221').mkdir(exist_ok=True)
    Path('audit221/scope.json').write_text(json.dumps({
      'build':VERSION,'parent_build':OLD_VERSION,
      'root_cause':'legacy internal-screen Back branch called showCobraPrimaryView before owner logic',
      'only_drawer_changes_active_section':True,
      'top_level_back':'move task to background; preserve owner for re-entry',
      'internal_back':'return to drawer-selected owner, never implicit Live TV',
      'cold_and_warm_entry_restore_owner':True,
      'smart_return_untouched':True,'smart_return_sha256':PARENT_SMART,
      'chooser_and_chooser_settings_untouched':True,'splash_sha256':PARENT_SPLASH,
      'cobra_settings_untouched':True,'cobra_settings_method_sha256':settings_before,
      'main_untouched':True,'native_engine_sha256':NATIVE,
      'physical_device_verified':False,
      'acceptance':[
        'Drawer > Movies; Android side Back moves app out; return => Movies',
        'Drawer > TV Shows; Android side Back moves app out; return => TV Shows',
        'See All / Genres Back => same media section',
        'Only selecting a different top-level drawer destination changes the owner'
      ],
      'status':'TEST CANDIDATE'
    },indent=2)+'\n')
    print('PASS: 2103221 surgical drawer owner; UI + Smart Return + protected systems unchanged')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--shell',type=Path,required=True)
    a=p.parse_args(); apply(a.shell)
if __name__=='__main__': main()
