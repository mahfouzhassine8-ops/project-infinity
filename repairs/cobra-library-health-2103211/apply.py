#!/usr/bin/env python3
"""Apply the locked 2103211 Movies/TV Shows refinement and native Infinity Health Center.

Parent must be the exact 2103210 Android source. Native 2103209 Python 3.11 engine is reused.
Live TV/player/provider ownership is hash-protected and out of scope.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VERSION=2103211
OLD_VERSION=2103210
OLD_NAME='1.0.9-Cobra-Media-Library-Health-RC1'
NEW_NAME='1.0.9-Cobra-Library-Health-Refinement-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT={
 SOURCE+'InfinityLiveActivity.java.in':'0d5172b619c8901994eb332050ae2330b0b6b607dae5e58e84a5b332581a8f5b',
 SOURCE+'Splash.java.in':'e440ed7cfff5021c4e620ef825669c3e63126ce18e0fbeaa58a39cba3e216e93',
 SOURCE+'Main.java.in':'240d08c21cbdbdfbff8f06f4af3f7a633516d499e49a24481c304990a705173f',
}
PROTECTED={
 'private void cobraOpenLiveTv()':'ca2104682cc43724a138310dac87361973d57a40a00a5db0e6557a3fa8f6a602',
 'private void showGuide()':'f57772610779aea49fc43c6d94db2df804e911e9c82cf224d9e5f6f96f9a93a4',
 'private void startSinglePlayer(String url)':'1c1a40c28072b5876e61ecedc5c64cfb6483b8d1c464041a16ee2b0128213708',
 'private void cobraShowQuickPeek(Channel channel,View anchor)':'bea049b1f6941709e13545eefd647915c64c2500e6b6716da2e246ab3718f869',
 'private void cobraStartLocalTimeshift':'758df5bc2d2c32df5836b13c23b33a44c35a90ef910cf3513516e4f8a3a6800a',
 'private void playChannel(Channel channel)':'48729254f6a27441b487fe8425b899ede48a804819c3d6bb466695d654087de3',
 'private void startCobraPreview(Channel channel)':'db8403d7256e8d353c9b7cef8397076ef7874646782d3972e7b3db2afa0a227c',
 'private void releaseSinglePlayer()':'1cd0ff7182a28e632f6601202c57050c87de10a923080ee64c062ced76f5b385',
 'private void releaseMulti()':'cc1a975f97fbb11dc9faa12f07e76045980e89911ed1f6cc7f0d8899886a1cad',
 'private LoadResult loadXtream(LiveSource source)':'6e9c2300e1c65095f2f8340f8764783e6852cbd8ccbc23ad238d14172e3ac2cb',
 'private LoadResult loadM3u(LiveSource source)':'ba2a26616379cd59e6b0514258e2734a19925f48627065ca33095793977d11b0',
}
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(value,message):
 if not value:raise RuntimeError(message)
def once(text,old,new,label):
 require(text.count(old)==1,label+' anchor drift');return text.replace(old,new,1)
def method(text,sig):
 i=text.find(sig);require(i>=0,'Missing protected method: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise RuntimeError('Unbalanced method: '+sig)
def range_for(text,sig):
 i=text.find(sig);require(i>=0,'Missing range: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced range: '+sig)
def contract(text):
 out={}
 for sig,expected in PROTECTED.items():
  digest=sha_bytes(method(text,sig).encode());require(digest==expected,'Live TV/player parent drift: '+sig);out[sig]=digest
 return out

def patch_activity(path):
 s=path.read_text();before=contract(s)
 start=s.find('  /** Cinematic Movies/Shows browse surface.')
 require(start>=0,'2103210 cinematic VOD block missing')
 end=s.find('  private void renderVodItems(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {',start)
 require(end>start,'Legacy VOD renderer boundary missing')
 new=(ROOT/'vod-browse-v2.java.inc').read_text()
 s=s[:start]+new+s[end:]

 old_ctor='''            items.add(new VodItem(source.id, id, title, cat, o.optString(series ? "cover" : "stream_icon", ""), sanitizeExtension(o.optString("container_extension", "mp4")), series));'''
 new_ctor='''            long added = cobraVodParseEpoch(o.optString("added", o.optString("last_modified", "0")));
            double rating = o.optDouble("rating", o.optDouble("rating_5based", 0.0));
            String year = o.optString("year", o.optString("releaseDate", o.optString("release_date", "")));
            items.add(new VodItem(source.id, id, title, cat,
                o.optString(series ? "cover" : "stream_icon", ""),
                sanitizeExtension(o.optString("container_extension", "mp4")),
                series, added, rating, year));'''
 s=once(s,old_ctor,new_ctor,'VOD metadata capture')

 a,b=range_for(s,'  private static final class VodItem {')
 vod_class='''  private static final class VodItem {
    final String sourceId;
    final String id;
    final String title;
    final String category;
    final String icon;
    final String extension;
    final boolean series;
    final long addedEpoch;
    final double rating;
    final String year;
    VodItem(String sourceId, String id, String title, String category, String icon,
            String extension, boolean series) {
      this(sourceId,id,title,category,icon,extension,series,0L,0.0,"");
    }
    VodItem(String sourceId, String id, String title, String category, String icon,
            String extension, boolean series, long addedEpoch, double rating, String year) {
      this.sourceId = sourceId; this.id = id; this.title = title; this.category = category;
      this.icon = icon; this.extension = extension; this.series = series;
      this.addedEpoch = addedEpoch; this.rating = rating;
      this.year = year == null ? "" : year.trim();
    }
  }'''
 s=s[:a]+vod_class+s[b:]
 require('cobraVodChip("Movies"' not in s and 'cobraVodChip("Shows"' not in s,'Cross-destination media tabs remain')
 require('cobraAddVodShelf(page, "My List"' not in s,'My List must remain drawer-owned')
 for token in ('"Recent Releases"','"Popular Now"','cobraAddVodGenres(page, items, series)',
               '"Because You Watched…"','setFlipInterval(9000)','cobraShowVodDetails(item)'):
  require(token in s,'Missing locked media contract: '+token)
 require(s.index('"Popular Now"')<s.index('cobraAddVodGenres(page, items, series)')<
         s.index('"Because You Watched…"'),'Popular -> Genres -> conditional personalization order drift')
 path.write_text(s)
 require(contract(s)==before,'Live TV/player protected bytes changed')

def patch_main(path):
 s=path.read_text()
 fields='''  private XBMCJsonRPC mJsonRPC = null;
  private static final String INFINITY_HEALTH_CENTER_EXTRA = "infinity_launch_kodi_health_center";
  private static final String INFINITY_HEALTH_CENTER_ADDON = "script.kodihealthcenter";
  private boolean mInfinityHealthCenterPending = false;
  private int mInfinityHealthCenterAttempts = 0;
  private final Runnable mInfinityHealthCenterLaunch = new Runnable()
  {
    @Override public void run()
    {
      if (!mInfinityHealthCenterPending || mInfinityDestroyed) return;
      if (mJsonRPC == null) mJsonRPC = new XBMCJsonRPC();
      if (mJsonRPC.Ping())
      {
        String response = mJsonRPC.request_string("{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"Addons.ExecuteAddon\\\",\\\"params\\\":{\\\"addonid\\\":\\\"" + INFINITY_HEALTH_CENTER_ADDON + "\\\"},\\\"id\\\":1}");
        if (response != null && !response.contains("\\\"error\\\""))
        {
          mInfinityHealthCenterPending = false;
          mInfinityHealthCenterAttempts = 0;
          return;
        }
      }
      if (++mInfinityHealthCenterAttempts < 12) handler.postDelayed(this, 500L);
      else
      {
        mInfinityHealthCenterPending = false;
        mInfinityHealthCenterAttempts = 0;
        android.widget.Toast.makeText(Main.this, "Kodi Health Center is not installed or could not be opened.", android.widget.Toast.LENGTH_LONG).show();
      }
    }
  };
'''
 s=once(s,fields,'  private XBMCJsonRPC mJsonRPC = null;\n','Remove Kodi Health bridge fields')
 s=once(s,'    super.onCreate(savedInstanceState);\n    infinityCaptureHealthCenterRequest(getIntent());\n\n    setContentView(R.layout.activity_main);',
        '    super.onCreate(savedInstanceState);\n\n    setContentView(R.layout.activity_main);','Remove Health onCreate bridge')
 s=once(s,'''    super.onNewIntent(intent);
    boolean healthCenter = infinityCaptureHealthCenterRequest(intent);
    if (infinityHandlePlayerRotationIntent(intent)) return;
    if (healthCenter) { if (!mPaused) infinityScheduleHealthCenterLaunch(); return; }
    // Delay until after Resume''',
        '''    super.onNewIntent(intent);
    if (infinityHandlePlayerRotationIntent(intent)) return;
    // Delay until after Resume''','Remove Health new-intent bridge')
 helper='''    InfinityExtendedBackgroundService.sync(this);
    infinityScheduleHealthCenterLaunch();
  }


  private boolean infinityCaptureHealthCenterRequest(Intent intent)
  {
    if (intent == null || !intent.getBooleanExtra(INFINITY_HEALTH_CENTER_EXTRA, false)) return false;
    intent.removeExtra(INFINITY_HEALTH_CENTER_EXTRA);
    mInfinityHealthCenterPending = true;
    mInfinityHealthCenterAttempts = 0;
    return true;
  }

  private void infinityScheduleHealthCenterLaunch()
  {
    if (!mInfinityHealthCenterPending || mInfinityDestroyed) return;
    handler.removeCallbacks(mInfinityHealthCenterLaunch);
    handler.postDelayed(mInfinityHealthCenterLaunch, 250L);
  }'''
 s=once(s,helper,'    InfinityExtendedBackgroundService.sync(this);\n  }','Remove Health resume/helper bridge')
 s=once(s,'    mInfinityDestroyed = true;\n    handler.removeCallbacks(mInfinityHealthCenterLaunch);\n',
        '    mInfinityDestroyed = true;\n','Remove Health destroy callback')
 require('infinity_launch_kodi_health_center' not in s and 'INFINITY_HEALTH_CENTER_ADDON' not in s,
         'Kodi-dependent Health Center bridge remains in Main')
 path.write_text(s)

def patch_splash(path):
 s=path.read_text()
 constants='''  private static final String INFINITY_EXPERIENCE_PREFS = "infinity_experience";
  private static final String INFINITY_EXPERIENCE_DEFAULT = "default";
'''
 replacement=constants+'''  private static final int INFINITY_HEALTH_EXPORT_RESULT_CODE = 8951;
  private String mInfinityHealthExportText = "";
'''
 s=once(s,constants,replacement,'Health export constants')

 # Remove the 2103210 Kodi-launching settings method and shortcut, then replace with native Health Center.
 a,b=range_for(s,'  private void showExperienceCardSettings(String experience)')
 s=s[:a]+s[b:]
 a,b=range_for(s,'  private void launchKodiHealthCenter()')
 s=s[:a]+s[b:]
 insert=s.find('  private void showInfinityExperienceChooser()')
 require(insert>=0,'Chooser insertion point missing')
 s=s[:insert]+(ROOT/'splash-health-native.java.inc').read_text()+s[insert:]

 crash_gate='''    String preferred = getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE)
        .getString(INFINITY_EXPERIENCE_DEFAULT, "");'''
 gated='''    if (infinityShouldOfferCrashRecovery())
    {
      android.widget.Toast.makeText(this,
          "Infinity recovered from an abnormal exit. Health Center is available from either experience settings.",
          android.widget.Toast.LENGTH_LONG).show();
      showInfinityExperienceChooser();
      return;
    }

    String preferred = getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE)
        .getString(INFINITY_EXPERIENCE_DEFAULT, "");'''
 s=once(s,crash_gate,gated,'Crash-safe chooser gate')

 activity='''    super.onActivityResult(requestCode, resultCode, data);
    if (requestCode == PERMISSION_RESULT_CODE)
    {'''
 activity_new='''    super.onActivityResult(requestCode, resultCode, data);
    if (requestCode == INFINITY_HEALTH_EXPORT_RESULT_CODE)
    {
      if (resultCode == RESULT_OK && data != null && data.getData() != null && !mInfinityHealthExportText.isEmpty())
      {
        java.io.OutputStream output = null;
        try
        {
          output = getContentResolver().openOutputStream(data.getData(), "w");
          if (output != null)
          {
            output.write(mInfinityHealthExportText.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            output.flush();
            android.widget.Toast.makeText(this, "Infinity diagnostic report saved.", android.widget.Toast.LENGTH_SHORT).show();
          }
        }
        catch (Exception e)
        {
          android.widget.Toast.makeText(this, "Could not save the diagnostic report.", android.widget.Toast.LENGTH_LONG).show();
        }
        finally
        {
          if (output != null) try { output.close(); } catch (Exception ignored) {}
        }
      }
      mInfinityHealthExportText = "";
      return;
    }
    if (requestCode == PERMISSION_RESULT_CODE)
    {'''
 s=once(s,activity,activity_new,'Health export result')

 require('launchKodiHealthCenter' not in s and 'infinity_launch_kodi_health_center' not in s,
         'Chooser still launches Kodi for Health Center')
 for token in ('Infinity Health Center','getHistoricalProcessExitReasons','ACTION_CREATE_DOCUMENT',
               'infinityShouldOfferCrashRecovery','infinityHealthExitHistory(true)'):
  require(token in s,'Missing native Health Center contract: '+token)
 path.write_text(s)

def patch_packaging(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in'
 g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','Runtime version')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'Runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 require(p.count(old)>=2,'Packager identity drift');pack.write_text(p.replace(old,new))
 return gradle

def apply(shell):
 for name,digest in PARENT.items():require(sha(shell/name)==digest,'Not exact 2103210 parent source: '+name)
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in');splash=shell/(SOURCE+'Splash.java.in');main=shell/(SOURCE+'Main.java.in')
 patch_activity(activity);patch_splash(splash);patch_main(main)
 gradle=patch_packaging(shell)

 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Wrong 2103210 receipt')
 for name in PARENT:
  require(name in receipt['files'],'Receipt missing source: '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   live_tv_source_untouched=True,movies_tv_shows_locked_structure=True,
   media_cross_destination_tabs_removed=True,recent_releases_dynamic=True,
   genres_picker=True,conditional_personalization=True,poster_details_before_playback=True,
   infinity_native_health_center=True,kodi_health_center_shortcut_removed=True,
   crash_safe_chooser_after_abnormal_exit=True,diagnostic_export_without_adb=True)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)

 scope={
  'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
  'changed_java_files':sorted(PARENT),'live_tv_protected_methods':contract(activity.read_text()),
  'live_tv_source_untouched':True,'native_engine_rebuilt':False,
  'movies':['Featured','Recent Releases','Continue Watching','Trending Movies','Popular Now','Genres'],
  'tv_shows':['Featured','Recent Releases','Continue Watching','Trending Shows','Popular Now','Genres'],
  'conditional':['Because You Watched…'],'my_list_owner':'existing Cobra drawer',
  'search_owner':'existing Cobra navigation','health_owner':'Infinity Android chooser',
  'health_kodi_dependency':False,'crash_safe_chooser':True,'diagnostic_export':True,
 }
 Path('audit211').mkdir(exist_ok=True)
 Path('audit211/scope.json').write_text(json.dumps(scope,indent=2)+'\n')
 print('PASS: 2103211 library refinement + native Infinity Health Center; Live TV/native engine untouched')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
