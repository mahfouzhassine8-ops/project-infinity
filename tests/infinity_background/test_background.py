#!/usr/bin/env python3
"""Execute actual background Java code with platform/player doubles plus SDK compile.

These are deterministic host-side tests, not Android/Fold runtime acceptance.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def method(text, name):
    match = re.search(r'  (?:private|protected|public) (?:static )?(?:void|boolean) ' + name + r'\([^)]*\)\s*\{', text)
    assert match, name
    level, end = 1, match.end()
    while level:
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


def compile_run(folder, files, name):
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for path, text in files.items():
        p = folder / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        paths.append(str(p))
    out = folder / 'classes'
    subprocess.run(['javac', '-d', str(out)] + paths, check=True)
    subprocess.run(['java', '-cp', str(out), name], check=True)


STUBS = {
'android/Manifest.java': '''package android; public class Manifest { public static class permission { public static String POST_NOTIFICATIONS="notify"; } }''',
'android/R.java': '''package android; public class R { public static class drawable { public static int stat_notify_sync_noanim=1,ic_menu_close_clear_cancel=2; } }''',
'android/os/Build.java': '''package android.os; public class Build { public static class VERSION { public static int SDK_INT=35; } }''',
'android/os/IBinder.java': '''package android.os; public interface IBinder {}''',
'android/util/Log.java': '''package android.util; public class Log { public static int w(String a,String b){return 0;} }''',
'android/net/Uri.java': '''package android.net; public class Uri { public static Uri parse(String s){return new Uri();} }''',
'android/provider/Settings.java': '''package android.provider; public class Settings { public static String ACTION_APP_NOTIFICATION_SETTINGS="notifications",EXTRA_APP_PACKAGE="package",ACTION_APPLICATION_DETAILS_SETTINGS="app"; }''',
'android/content/pm/PackageManager.java': '''package android.content.pm; public class PackageManager { public static int PERMISSION_GRANTED=0; public android.content.Intent getLaunchIntentForPackage(String p){return new android.content.Intent();} }''',
'android/content/pm/ServiceInfo.java': '''package android.content.pm; public class ServiceInfo { public static int FOREGROUND_SERVICE_TYPE_SPECIAL_USE=0x40000000; }''',
'android/content/ComponentName.java': '''package android.content; public class ComponentName {}''',
'android/content/Intent.java': '''package android.content; public class Intent { public static final int FLAG_ACTIVITY_NEW_TASK=1,FLAG_ACTIVITY_SINGLE_TOP=2; public static final String ACTION_MAIN="main",CATEGORY_LAUNCHER="launcher"; String action; public Intent(){} public Intent(Context c,Class<?> k){} public Intent(String a){action=a;} public Intent(String a,android.net.Uri u){action=a;} public Intent addFlags(int f){return this;} public Intent addCategory(String s){return this;} public Intent setAction(String s){action=s;return this;} public String getAction(){return action;} public Intent putExtra(String k,String v){return this;} }''',
'android/content/SharedPreferences.java': '''package android.content; public class SharedPreferences { public static boolean enabled; public boolean getBoolean(String k,boolean d){return enabled;} public Editor edit(){return new Editor();} public static class Editor { boolean value; public Editor putBoolean(String k,boolean v){value=v;return this;} public void apply(){enabled=value;} } }''',
'android/content/Context.java': '''package android.content; public class Context { public static final int MODE_PRIVATE=0; public static final String NOTIFICATION_SERVICE="notification"; public static int starts,fgStarts,stops,activities,permission; public static boolean rejectStart,nullStart; public SharedPreferences getSharedPreferences(String n,int m){return new SharedPreferences();} public Object getSystemService(String n){return android.app.NotificationManager.manager;} public int checkSelfPermission(String p){return permission;} public ComponentName startForegroundService(Intent i){fgStarts++;if(rejectStart)throw new IllegalStateException();return nullStart?null:new ComponentName();} public ComponentName startService(Intent i){starts++;if(rejectStart)throw new SecurityException();return nullStart?null:new ComponentName();} public boolean stopService(Intent i){stops++;return true;} public void startActivity(Intent i){activities++;} public String getPackageName(){return "com.projectinfinity.kodi";} public android.content.pm.PackageManager getPackageManager(){return new android.content.pm.PackageManager();} }''',
'android/app/Activity.java': '''package android.app; public class Activity extends android.content.Context { public boolean finishing,destroyed; public boolean isFinishing(){return finishing;} public boolean isDestroyed(){return destroyed;} }''',
'android/app/NotificationManager.java': '''package android.app; public class NotificationManager { public static final int IMPORTANCE_NONE=0,IMPORTANCE_LOW=2; public static NotificationManager manager=new NotificationManager(); public boolean enabled=true,fail; public NotificationChannel channel; public boolean areNotificationsEnabled(){if(fail)throw new IllegalStateException();return enabled;} public NotificationChannel getNotificationChannel(String n){return channel;} public void createNotificationChannel(NotificationChannel c){channel=c;} }''',
'android/app/NotificationChannel.java': '''package android.app; public class NotificationChannel { int importance; public NotificationChannel(String a,String b,int c){importance=c;} public int getImportance(){return importance;} public void setDescription(String s){} public void setShowBadge(boolean b){} }''',
'android/app/PendingIntent.java': '''package android.app; public class PendingIntent { public static int FLAG_UPDATE_CURRENT=1,FLAG_IMMUTABLE=2; public static PendingIntent getActivity(android.content.Context c,int n,android.content.Intent i,int f){return new PendingIntent();} public static PendingIntent getService(android.content.Context c,int n,android.content.Intent i,int f){return new PendingIntent();} }''',
'android/app/Notification.java': '''package android.app; public class Notification { public static String CATEGORY_SERVICE="service"; public static int FOREGROUND_SERVICE_IMMEDIATE=1; public static class Builder { public Builder(android.content.Context c){} public Builder(android.content.Context c,String s){} public Builder setSmallIcon(int n){return this;} public Builder setContentTitle(String s){return this;} public Builder setContentText(String s){return this;} public Builder setContentIntent(PendingIntent p){return this;} public Builder setCategory(String s){return this;} public Builder setOngoing(boolean b){return this;} public Builder setOnlyAlertOnce(boolean b){return this;} public Builder setShowWhen(boolean b){return this;} public Builder addAction(Action a){return this;} public Builder setForegroundServiceBehavior(int b){return this;} public Notification build(){return new Notification();} } public static class Action { public static class Builder { public Builder(int i,String s,PendingIntent p){} public Action build(){return new Action();} } } }''',
'android/app/Service.java': '''package android.app; public class Service extends android.content.Context { public static final int START_STICKY=1,START_NOT_STICKY=2; public static int promotions,ends,lastType; public static boolean failPromotion; public int onStartCommand(android.content.Intent i,int f,int id){return 0;} public void startForeground(int id,Notification n){if(failPromotion)throw new SecurityException();promotions++;lastType=0;} public void startForeground(int id,Notification n,int type){startForeground(id,n);lastType=type;} public void stopForeground(boolean b){} public void stopSelf(){ends++;} public void onTaskRemoved(android.content.Intent i){} public void onDestroy(){} public android.os.IBinder onBind(android.content.Intent i){return null;} }''',
'com/projectinfinity/kodi/Splash.java': '''package com.projectinfinity.kodi; public class Splash extends android.app.Activity {}'''
}

SERVICE_TEST = '''package com.projectinfinity.kodi;
import android.app.*; import android.content.*; import android.os.Build;
public class ServiceTest {
 static int checks;
 static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 static Activity reset(int api){new InfinityExtendedBackgroundService().onDestroy();SharedPreferences.enabled=false;Context.starts=Context.fgStarts=Context.stops=Context.activities=Context.permission=0;Context.rejectStart=Context.nullStart=false;Service.promotions=Service.ends=Service.lastType=0;Service.failPromotion=false;NotificationManager.manager=new NotificationManager();Build.VERSION.SDK_INT=api;return new Activity();}
 public static void main(String[] args){
  Activity a=reset(35); check(!InfinityExtendedBackgroundService.isEnabled(a),"default OFF");
  InfinityExtendedBackgroundService.sync(a);check(Context.fgStarts==0,"no unsolicited service");
  check(InfinityExtendedBackgroundService.setEnabled(a,true),"enable accepted");
  check(Context.fgStarts==1&&!InfinityExtendedBackgroundService.isRunning(),"request != active");
  InfinityExtendedBackgroundService s=new InfinityExtendedBackgroundService();
  check(s.onStartCommand(null,0,1)==Service.START_STICKY,"sticky restart allowed after opt-in");
  check(InfinityExtendedBackgroundService.isRunning()&&Service.lastType==0x40000000,"actual special-use foreground promotion");
  InfinityExtendedBackgroundService.sync(a);check(Context.fgStarts==1,"resume deduplicates running service");
  s.onDestroy();InfinityExtendedBackgroundService.sync(a);check(Context.fgStarts==2,"manual foreground resumes enabled session");
  check(InfinityExtendedBackgroundService.setEnabled(a,false),"disable succeeds");
  check(!SharedPreferences.enabled&&Context.stops==1,"disable cancels request and stops");
  check(s.onStartCommand(null,0,2)==Service.START_NOT_STICKY,"no resurrection after disable");
  a=reset(35);Context.permission=-1;check(!InfinityExtendedBackgroundService.setEnabled(a,true)&&!SharedPreferences.enabled,"notification permission denied -> remains off");
  a=reset(35);NotificationManager.manager.enabled=false;check(!InfinityExtendedBackgroundService.setEnabled(a,true),"app notifications blocked");
  a=reset(35);NotificationManager.manager.channel=new NotificationChannel("x","x",0);check(!InfinityExtendedBackgroundService.setEnabled(a,true),"channel blocked");
  a=reset(35);NotificationManager.manager.fail=true;check(!InfinityExtendedBackgroundService.setEnabled(a,true),"OS notification-query error is contained");
  a=reset(35);Context.rejectStart=true;check(!InfinityExtendedBackgroundService.setEnabled(a,true)&&!SharedPreferences.enabled,"start restriction is contained and rolls back preference");
  a=reset(35);Context.nullStart=true;check(!InfinityExtendedBackgroundService.setEnabled(a,true),"null start result not success");
  a=reset(35);a.finishing=true;check(!InfinityExtendedBackgroundService.setEnabled(a,true)&&Context.fgStarts==0,"finishing activity cannot start");
  a=reset(35);a.destroyed=true;SharedPreferences.enabled=true;InfinityExtendedBackgroundService.sync(a);check(Context.fgStarts==0,"destroyed activity cannot sync");
  a=reset(35);SharedPreferences.enabled=true;Service.failPromotion=true;s=new InfinityExtendedBackgroundService();check(s.onStartCommand(null,0,1)==Service.START_NOT_STICKY&&!InfinityExtendedBackgroundService.isRunning()&&Service.ends==1,"promotion failure cleanly stops");
  a=reset(35);SharedPreferences.enabled=true;s=new InfinityExtendedBackgroundService();s.onStartCommand(null,0,1);s.onTaskRemoved(new Intent());check(!InfinityExtendedBackgroundService.isRunning()&&Service.ends==1&&SharedPreferences.enabled,"task swipe ends session, retains preference");
  a=reset(35);SharedPreferences.enabled=true;s=new InfinityExtendedBackgroundService();s.onStartCommand(null,0,1);check(s.onStartCommand(new Intent().setAction("com.projectinfinity.kodi.action.DISABLE_EXTENDED_BACKGROUND"),0,2)==Service.START_NOT_STICKY&&!SharedPreferences.enabled&&!InfinityExtendedBackgroundService.isRunning(),"notification Turn off stops and disables");
  for(int api:new int[]{21,23,24,26,31,33,34,35}){a=reset(api);check(InfinityExtendedBackgroundService.setEnabled(a,true),"API enable "+api);s=new InfinityExtendedBackgroundService();s.onStartCommand(null,0,1);check(Service.promotions==1&&Service.lastType==(api>=34?0x40000000:0),"API promotion "+api);check(Context.fgStarts==(api>=26?1:0)&&Context.starts==(api<26?1:0),"API launch "+api);}
  check(Context.activities==0,"service never launches activity by itself");
  System.out.println("PASS: "+checks+" actual service behavior assertions");
 }
}'''

PLAYER_TEST = '''
  public static void main(String[] args) {
    BackgroundPlayerTest t=new BackgroundPlayerTest();
    t.mPlayer=new ExoPlayer(true,Player.STATE_READY);t.pauseCobraForBackground();t.pauseCobraForBackground();t.resumeCobraAfterBackground();
    check(t.mPlayer.plays==1&&t.mPlayer.pauses==1,"duplicate stop retains exact resume intent");
    t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(false,Player.STATE_READY);t.pauseCobraForBackground();t.resumeCobraAfterBackground();check(t.mPlayer.plays==0,"manually paused stays paused");
    t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(true,Player.STATE_BUFFERING);t.pauseCobraForBackground();check(!t.mPlayer.ready,"buffering also pauses");t.resumeCobraAfterBackground();check(t.mPlayer.plays==1&&t.mMain.posts==1,"buffering resumes and watchdog rearms");
    t=new BackgroundPlayerTest();t.mMultiPlayers=new ExoPlayer[]{new ExoPlayer(true,3),new ExoPlayer(false,3),null,new ExoPlayer(true,3)};t.pauseCobraForBackground();t.resumeCobraAfterBackground();check(t.mMultiPlayers[0].plays==1&&t.mMultiPlayers[1].plays==0&&t.mMultiPlayers[3].plays==1,"each multiview tile keeps its pause state");
    t=new BackgroundPlayerTest();ExoPlayer old=new ExoPlayer(true,3);t.mPlayer=old;t.pauseCobraForBackground();t.mPlayer=new ExoPlayer(false,3);t.resumeCobraAfterBackground();check(old.plays==0&&t.mPlayer.plays==0,"stale player never resumed");
    for(int state:new int[]{Player.STATE_ENDED,Player.STATE_IDLE}){t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(true,3);t.pauseCobraForBackground();t.mPlayer.state=state;t.resumeCobraAfterBackground();check(t.mPlayer.plays==0,"stopped/ended player never restarted");}
    t=new BackgroundPlayerTest();t.pauseCobraForBackground();t.mPlayer=new ExoPlayer(false,2);t.startCobraPlayer(t.mPlayer);check(t.mPlayer.plays==0,"late async start deferred while hidden");t.resumeCobraAfterBackground();check(t.mPlayer.plays==1,"late start resumes on foreground");
    t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(true,2);t.mBufferingSince=System.currentTimeMillis()-13000;t.mBackgroundStopped=true;t.mStallWatchdog.run();check(t.mPlayer.plays==0&&t.mMain.posts==0,"watchdog cannot restart hidden playback");
    t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(false,2);t.mBufferingSince=System.currentTimeMillis()-13000;t.mStallWatchdog.run();check(t.mPlayer.plays==0,"watchdog respects manual pause");
    t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(true,2);t.mBufferingSince=System.currentTimeMillis()-13000;t.mStallWatchdog.run();check(t.mPlayer.plays==1&&t.mPlayer.prepares==1,"foreground stall recovery retained");
    t=new BackgroundPlayerTest();t.pip=true;t.mPlayer=new ExoPlayer(true,3);t.onStop();check(t.mPlayer.pauses==0,"PiP playback not paused by stop");
    t=new BackgroundPlayerTest();t.mPlayer=new ExoPlayer(true,3);t.pauseCobraForBackground();t.finishing=true;t.resumeCobraAfterBackground();check(t.mPlayer.plays==0,"finishing activity does not resume");
    System.out.println("PASS: "+checks+" actual Cobra background/player assertions");
  }
}'''


def run(source, out, android_jar):
    java_root = source / 'tools/android/packaging/xbmc/src'
    service = (java_root / 'InfinityExtendedBackgroundService.java.in').read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi')
    compile_run(out / 'service', {**STUBS, 'com/projectinfinity/kodi/InfinityExtendedBackgroundService.java': service,
                               'com/projectinfinity/kodi/ServiceTest.java': SERVICE_TEST}, 'com.projectinfinity.kodi.ServiceTest')
    live = (java_root / 'InfinityLiveActivity.java.in').read_text()
    bodies = '\n'.join(method(live, n) for n in ('startCobraPlayer','rememberAndPauseCobraPlayer','isCurrentCobraPlayer','pauseCobraForBackground','resumeCobraAfterBackground','onStop'))
    a = live.index('  private final Runnable mStallWatchdog =')
    b = live.index('  private final Runnable mAutoRefresh =',a)
    watchdog = live[a:b]
    harness = '''import java.util.*;
class Player {static final int STATE_IDLE=1,STATE_BUFFERING=2,STATE_READY=3,STATE_ENDED=4;}
class ExoPlayer {boolean ready;int state,plays,pauses,prepares;ExoPlayer(boolean r,int s){ready=r;state=s;}boolean getPlayWhenReady(){return ready;}int getPlaybackState(){return state;}void play(){ready=true;plays++;}void pause(){ready=false;pauses++;}void prepare(){prepares++;}}
class Parent {protected void onStop(){}}
public class BackgroundPlayerTest extends Parent {
 static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 ExoPlayer mPlayer;ExoPlayer[] mMultiPlayers;boolean mBackgroundStopped,pip,finishing;
 java.util.IdentityHashMap<ExoPlayer,Boolean> mBackgroundResumePlayers=new java.util.IdentityHashMap<>();
 long mBufferingSince;int mPlaybackRetryCount;
 class Handler {int posts;void removeCallbacks(Runnable r){}void postDelayed(Runnable r,long n){posts++;}} Handler mMain=new Handler();
 boolean isCobraInPictureInPicture(){return pip;}boolean isFinishing(){return finishing;}
''' + watchdog + bodies + PLAYER_TEST
    compile_run(out / 'player', {'BackgroundPlayerTest.java':harness}, 'BackgroundPlayerTest')
    if android_jar:
        sdk = out / 'sdk/com/projectinfinity/kodi'
        sdk.mkdir(parents=True,exist_ok=True)
        (sdk / 'InfinityExtendedBackgroundService.java').write_text(service)
        (sdk / 'Splash.java').write_text(STUBS['com/projectinfinity/kodi/Splash.java'])
        subprocess.run(['javac','-source','8','-target','8','-cp',str(android_jar),'-d',str(out/'sdk/classes'),*[str(p) for p in sdk.glob('*.java')]],check=True)
        print('PASS: service compiles against real Android 35 SDK')
    manifest = ET.fromstring((source/'tools/android/packaging/xbmc/AndroidManifest.xml.in').read_text())
    ns='{http://schemas.android.com/apk/res/android}'
    svc=[s for s in manifest.findall('./application/service') if s.get(ns+'name')=='.InfinityExtendedBackgroundService']
    assert len(svc)==1 and svc[0].get(ns+'exported')=='false' and svc[0].get(ns+'foregroundServiceType')=='specialUse'
    main=(java_root/'Main.java.in').read_text()
    assert method(main,'onResume').index('mPaused = false') < method(main,'onResume').index('infinityApplyPlayerRotation("resume")') < method(main,'onResume').index('InfinityExtendedBackgroundService.sync(this)')
    assert 'InfinityExtendedBackgroundService.sync(this)' in method(live,'onResume')
    for s in (main,live):
        for n in ('onPause','onStop'):
            assert 'InfinityExtendedBackgroundService.sync' not in method(s,n)
    assert 'mBackgroundResumePlayers.remove(mPlayer)' in method(live,'releaseSinglePlayer')
    assert 'mBackgroundResumePlayers.remove(player)' in method(live,'releaseMulti')
    for forbidden in ('PowerManager.WakeLock','PARTIAL_WAKE_LOCK','FULL_WAKE_LOCK','AlarmManager','startActivity(launch)'):
        assert forbidden not in service,forbidden
    print('PASS: lifecycle ordering, manifest, cleanup, foreground-only start and no-wake-lock contracts')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--android-jar',type=Path)
    a=p.parse_args();run(a.source,a.out,a.android_jar)
