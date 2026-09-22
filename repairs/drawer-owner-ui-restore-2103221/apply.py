#!/usr/bin/env python3
"""2103221 — restore approved chooser settings presentation and enforce drawer-owned Cobra sections.

Parent: exact locked 2103217 Media Return Context.
Scope:
- Smart Return implementation/file is byte-preserved.
- Only Cobra drawer choices may change the persistent active section.
- Android Back/edge-swipe never falls through from Movies/Shows/etc. to Live TV.
- Every legacy showCobraPrimaryView() fallback obeys the drawer-owned section.
- Choose Your Experience Infinity/Cobra option panels use the approved styled dialog renderer,
  never the plain framework AlertDialog fallback shown by 2103220.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

VERSION=2103221
OLD_VERSION=2103217
OLD_NAME='1.0.9-Cobra-Media-Return-Context-RC1'
NEW_NAME='1.0.9-Cobra-Drawer-Owner-UI-Restore-RC1'
SRC='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b): return hashlib.sha256(b).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1, f'{label} anchor drift ({s.count(a)})')
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

ACTIVITY_PROTECTED=[
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
SPLASH_PROTECTED=[
 'private void showInfinityExperienceChooser()',
 'private void showStyledInfinityExperienceChooser(ExperienceTheme theme)',
 'private boolean showVisualExperienceScene(ExperienceTheme fallback)',
 'private void launchInfinityExperience(String experience)',
]
def hashes(s,names): return {n:hb(method(s,n).encode()) for n in names}

def patch_activity(path:Path):
    s=path.read_text(); before=hashes(s,ACTIVITY_PROTECTED)

    # Persistent owner. This preference is written by drawer destinations only.
    marker='  private final ArrayList<View> mCobraVodReturnViews = new ArrayList<>();\n'
    fields='''  private static final String COBRA_DRAWER_OWNER_PREF="cobra_drawer_active_section";
  private static final String COBRA_OWNER_LIVE="live";
  private static final String COBRA_OWNER_MOVIES="movies";
  private static final String COBRA_OWNER_SHOWS="shows";
  private static final String COBRA_OWNER_RECORDINGS="recordings";
  private static final String COBRA_OWNER_MY_LIST="my_list";
  private String mCobraDrawerOwner="";
'''+marker
    s=once(s,marker,fields,'drawer owner fields')

    marker2='  private void cobraDiscardVodLandingReturn(){'
    helpers='''  private String cobraDrawerOwner(){
    if(mCobraDrawerOwner==null||mCobraDrawerOwner.isEmpty()){
      String stored=mPrefs==null?COBRA_OWNER_LIVE:mPrefs.getString(COBRA_DRAWER_OWNER_PREF,COBRA_OWNER_LIVE);
      if(!COBRA_OWNER_MOVIES.equals(stored)&&!COBRA_OWNER_SHOWS.equals(stored)&&
          !COBRA_OWNER_RECORDINGS.equals(stored)&&!COBRA_OWNER_MY_LIST.equals(stored)&&
          !COBRA_OWNER_LIVE.equals(stored))stored=COBRA_OWNER_LIVE;
      mCobraDrawerOwner=stored;
    }
    return mCobraDrawerOwner;
  }

  private void cobraSelectDrawerOwner(String destination){
    String owner=null;
    if("TV".equals(destination))owner=COBRA_OWNER_LIVE;
    else if("MOVIES".equals(destination))owner=COBRA_OWNER_MOVIES;
    else if("SHOWS".equals(destination))owner=COBRA_OWNER_SHOWS;
    else if("RECORDINGS".equals(destination))owner=COBRA_OWNER_RECORDINGS;
    else if("MY LIST".equals(destination))owner=COBRA_OWNER_MY_LIST;
    if(owner==null)return;
    mCobraDrawerOwner=owner;
    mPrefs.edit().putString(COBRA_DRAWER_OWNER_PREF,owner).apply();
  }

  private boolean cobraSurfaceMatchesDrawerOwner(){
    String owner=cobraDrawerOwner();
    String title=mCobraStageTitle==null?"":mCobraStageTitle;
    if(COBRA_OWNER_MOVIES.equals(owner))
      return "COBRA • MOVIES".equals(title)||(mCobraVodReturnCaptured&&!mCobraVodReturnSeries);
    if(COBRA_OWNER_SHOWS.equals(owner))
      return "COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title)||
          (mCobraVodReturnCaptured&&mCobraVodReturnSeries);
    if(COBRA_OWNER_RECORDINGS.equals(owner))return "COBRA • RECORDINGS".equals(title);
    if(COBRA_OWNER_MY_LIST.equals(owner))return mCobraSmartWatchlist||"COBRA • MY LIST".equals(title);
    return mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()||
        "COBRA • LIVE TV".equals(title)||"COBRA • TV GRID".equals(title);
  }

  private boolean cobraHandleDrawerOwnedBack(){
    String owner=cobraDrawerOwner();
    String title=mCobraStageTitle==null?"":mCobraStageTitle;
    if(COBRA_OWNER_LIVE.equals(owner))return false;
    if(COBRA_OWNER_MOVIES.equals(owner)){
      if("COBRA • MOVIES".equals(title)){moveTaskToBack(true);return true;}
      showMovies();return true;
    }
    if(COBRA_OWNER_SHOWS.equals(owner)){
      if("COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title)){moveTaskToBack(true);return true;}
      showSeries();return true;
    }
    if(COBRA_OWNER_RECORDINGS.equals(owner)){
      if("COBRA • RECORDINGS".equals(title)){moveTaskToBack(true);return true;}
      showRecordings();return true;
    }
    if(COBRA_OWNER_MY_LIST.equals(owner)){
      if(mCobraSmartWatchlist||"COBRA • MY LIST".equals(title)){moveTaskToBack(true);return true;}
      showWatchlist();return true;
    }
    return false;
  }

'''
    s=once(s,marker2,helpers+marker2,'drawer owner helpers')

    # Drawer is the sole writer.
    sig='private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)'
    drawer=method(s,sig)
    anchor='      action.run();'
    req(anchor in drawer,'drawer action anchor missing')
    drawer=drawer.replace(anchor,'      cobraSelectDrawerOwner(destination);\n'+anchor,1)
    s=replace_method(s,sig,drawer)
    req(s.count('cobraSelectDrawerOwner(destination);')==1,'drawer owner write is not unique')

    # Every inherited "primary view" fallback now means "the drawer-selected top-level section".
    sig='private void showCobraPrimaryView()'
    old=method(s,sig)
    req('cobraPrimaryView()' in old,'legacy primary live behavior missing')
    new='''private void showCobraPrimaryView() {
    String owner=cobraDrawerOwner();
    if(COBRA_OWNER_MOVIES.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showMovies();return;}
    if(COBRA_OWNER_SHOWS.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showSeries();return;}
    if(COBRA_OWNER_RECORDINGS.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showRecordings();return;}
    if(COBRA_OWNER_MY_LIST.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showWatchlist();return;}
    mCobraInternalScreen="root";
    if ("guide".equals(cobraPrimaryView())) showGuide();
    else showCobraMobileView();
    mMain.post(this::cobraApplySystemBarsForSurface);
  }'''
    s=replace_method(s,sig,new)

    # Exact media-parent restore and drawer-owner Back handling must run BEFORE the old
    # "internal -> primary view" branch that caused Movies -> Live TV on edge swipe.
    back=method(s,'public void onBackPressed()')
    early='    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}'
    req(early in back,'old internal Back fallback missing')
    prefix='''    if(cobraRestoreVodLandingReturn())return;
    if(cobraHandleDrawerOwnedBack())return;
'''
    back=back.replace(early,prefix+early,1)
    # Remove the late duplicate 2103217 parent-restore insertion if present.
    back=back.replace('    if(cobraRestoreVodLandingReturn())return;\n    if("grid".equals(mCobraGuideStyle)', '    if("grid".equals(mCobraGuideStyle)',1)
    s=replace_method(s,'public void onBackPressed()',back)
    req(method(s,'public void onBackPressed()').index('cobraHandleDrawerOwnedBack()') <
        method(s,'public void onBackPressed()').index('!"root".equals(mCobraInternalScreen)'),
        'drawer-owned Back does not precede legacy fallback')

    # Smart Return code stays byte-identical. At its callers only, if it restores a different
    # top-level surface than the drawer owner, immediately return to the drawer owner.
    fallback='if(!cobraTrySmartReturn())showCobraPrimaryView();'
    count=s.count(fallback); req(count>=2,'Smart Return caller anchors missing')
    s=s.replace(fallback,'if(!cobraTrySmartReturn()||!cobraSurfaceMatchesDrawerOwner())showCobraPrimaryView();')

    # Surviving Activity resume: do not touch temporary/settings surfaces; only correct an
    # actual Live/owned top-level mismatch caused by Android task re-entry.
    resume=method(s,'protected void onResume()')
    anchor='    mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");cobraApplyDisplayPerformance("resume");cobraSyncPerformanceOverlay();'
    req(anchor in resume,'resume anchor missing')
    resume=resume.replace(anchor,anchor+'''\n    mMain.postDelayed(()->{\n      if(mPlayerOverlay!=null||mMultiOverlay!=null||isCobraInPictureInPicture())return;\n      String title=mCobraStageTitle==null?"":mCobraStageTitle;\n      boolean topLevel="COBRA • LIVE TV".equals(title)||"COBRA • TV GRID".equals(title)||\n          "COBRA • MOVIES".equals(title)||"COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title)||\n          "COBRA • RECORDINGS".equals(title)||"COBRA • MY LIST".equals(title);\n      if(topLevel&&!cobraSurfaceMatchesDrawerOwner())showCobraPrimaryView();\n    },80L);''',1)
    s=replace_method(s,'protected void onResume()',resume)

    for token in ('COBRA_DRAWER_OWNER_PREF','cobraSelectDrawerOwner(destination)',
                  'cobraHandleDrawerOwnedBack()','cobraSurfaceMatchesDrawerOwner()'):
        req(token in s,'drawer ownership contract missing '+token)

    path.write_text(s)
    req(hashes(s,ACTIVITY_PROTECTED)==before,'Smart Return/protected Cobra behavior changed')

def patch_splash(path:Path):
    s=path.read_text(); before=hashes(s,SPLASH_PROTECTED)

    settings=method(s,'private void showExperienceCardSettings(String experience)')
    # Both Infinity and Cobra chooser gears use the same approved visual renderer.
    pattern=re.compile(r'\s*\(cobra \? new android\.app\.AlertDialog\.Builder\(this,[\s\S]*?: new CobraVisualRenderer\.DialogBuilder\(this,vtheme\(\),\"chooser\.settings\"\)\)')
    req(pattern.search(settings) is not None,'plain Cobra options builder anchor missing')
    settings=pattern.sub('\n    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings")',settings,count=1)
    req('new android.app.AlertDialog.Builder' not in settings,'plain framework builder remains in experience settings')
    req('new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings")' in settings,'styled chooser settings missing')
    s=replace_method(s,'private void showExperienceCardSettings(String experience)',settings)

    recovery=method(s,'private void showCobraRecovery()')
    recovery=recovery.replace('new android.app.AlertDialog.Builder(this,android.R.style.Theme_Material_Dialog_Alert)',
                              'new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.recovery")')
    req('new android.app.AlertDialog.Builder' not in recovery,'plain Cobra recovery dialog remains')
    req(recovery.count('new CobraVisualRenderer.DialogBuilder')>=2,'styled recovery/confirmation missing')
    s=replace_method(s,'private void showCobraRecovery()',recovery)

    path.write_text(s)
    req(hashes(s,SPLASH_PROTECTED)==before,'main chooser/routing presentation changed')

def identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in'; g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName'); gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py'); r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name'); runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py'); p=pack.read_text(); old='Infinity-'+OLD_NAME; new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift'); pack.write_text(p.replace(old,new))
    return gradle

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
        'Expected exact locked 2103217 reconstruction')
    activity=shell/(SRC+'InfinityLiveActivity.java.in')
    splash=shell/(SRC+'Splash.java.in')
    smart=shell/(SRC+'CobraSmartReturn.java.in')
    main=shell/(SRC+'Main.java.in')
    for p in (activity,splash,smart,main): req(p.is_file(),'Missing '+str(p))

    smart_before=sha(smart); main_before=sha(main)
    patch_activity(activity); patch_splash(splash); gradle=identity(shell)
    req(sha(smart)==smart_before,'Smart Return file changed')
    req(sha(main)==main_before,'Kodi Main changed')
    req(receipt.get('native_engine_sha256')==NATIVE,'native engine drift')

    for name in (SRC+'InfinityLiveActivity.java.in',SRC+'Splash.java.in',SRC+'CobraSmartReturn.java.in',SRC+'Main.java.in'):
        req(name in receipt['files'],'receipt missing '+name)
        receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in'; receipt['files'][rel]['after']=sha(gradle)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
      candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
      native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
      drawer_active_section_owner=True,active_section_changes_only_from_drawer=True,
      android_edge_back_preserves_owner=True,primary_view_fallback_obeys_owner=True,
      movies_stays_movies=True,tv_shows_stays_tv_shows=True,recordings_stays_recordings=True,my_list_stays_my_list=True,
      smart_return_untouched=True,smart_return_file_sha256=smart_before,
      chooser_settings_styled=True,plain_cobra_options_dialog_removed=True,
      infinity_options_styled=True,cobra_options_styled=True,cobra_recovery_styled=True,
      media_return_context_preserved=True,live_tv_blue_ambient_unchanged=True,
      cobra_settings_ui_unchanged=True,health_center_unchanged=True,playback_unchanged=True,providers_unchanged=True)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items(): req(sha(shell/name)==row['after'],'receipt drift '+name)

    Path('audit221').mkdir(exist_ok=True)
    Path('audit221/scope.json').write_text(json.dumps({
      'build':VERSION,'parent':OLD_VERSION,'native_engine_sha256':NATIVE,
      'smart_return_untouched':True,'smart_return_sha256':smart_before,
      'only_drawer_changes_active_section':True,
      'root_cause_fixed':'legacy onBackPressed internal-screen branch called Live-TV primary view before 2103217 media-return handling',
      'chooser_settings_ui':{
        'Infinity':'styled CobraVisualRenderer chooser.settings',
        'Cobra':'styled CobraVisualRenderer chooser.settings',
        'Cobra Recovery':'styled CobraVisualRenderer chooser.recovery',
        'plain_framework_dialog_for_cobra_options':False
      },
      'acceptance':[
        'Drawer > Movies > Android edge Back at Movies root backgrounds task; reopen => Movies',
        'Drawer > Movies > See All/Details > Back => Movies hierarchy, never Live TV',
        'Drawer > TV Shows > Android edge Back/reopen => TV Shows',
        'Drawer > Live TV => Live TV remains owner',
        'Only a drawer top-level selection changes the owner',
        'Both chooser gear panels remain styled; no plain white Cobra options fallback'
      ],
      'native_engine_rebuilt':False,'playback_unchanged':True,'providers_unchanged':True,
      'health_center_unchanged':True,'status':'TEST CANDIDATE'
    },indent=2)+'\n')
    print('PASS: 2103221 drawer owner + chooser settings UI restore; Smart Return untouched')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--shell',type=Path,required=True)
    a=p.parse_args(); apply(a.shell)
if __name__=='__main__': main()
