from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args();root=a.root
here=Path(__file__).parent;src=root/'shell-kodi/tools/android/packaging/xbmc/src'
def replace(s,old,new):
 assert s.count(old)==1,(old[:100],s.count(old))
 return s.replace(old,new)

f=src/'InfinityCobraFeatureRuntime.java.in';s=f.read_text()
s=replace(s,'  public String startRecording(', (here/'recording_state.java.fragment').read_text()+'  public String startRecording(')
s=replace(s,'    if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(intent); else context.startService(intent);\n    return session;', '''    recordingRequested(session);
    try { if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(intent); else context.startService(intent); }
    catch(RuntimeException failure){recordingFinished(session,null);InfinityCobraDiagnostics.failure(context,"recording-start",failure);return "";}
    return session;''')
s=replace(s,'  public void stopRecording(String session) {','  public void stopRecording(String session) {\n    if(session!=null&&!session.isEmpty()&&!recordingActive(session))return;')
f.write_text(s)

f=src/'InfinityCobraRecordingService.java.in';s=f.read_text()
s=replace(s,'      stopSession(intent.getStringExtra(InfinityCobraFeatureRuntime.EXTRA_SESSION));','      stopSession(intent.getStringExtra(InfinityCobraFeatureRuntime.EXTRA_SESSION));\n      if(sessions.isEmpty())stopSelfResult(startId);')
s=replace(s,'    if (url.isEmpty()) {','    if (url.isEmpty()) {\n      InfinityCobraFeatureRuntime.recordingFinished(sessionId,null);')
s=replace(s,'    if (!features.hasRecordingSpace()) {','    if (!features.hasRecordingSpace()) {\n      InfinityCobraFeatureRuntime.recordingFinished(sessionId,null);')
s=replace(s,'      session.future = pool.submit(() -> record(session, url, finalName, headers, endAt, sourceId, channelId));','''      InfinityCobraFeatureRuntime.recordingStarted(finalSession,session);
      try { session.future = pool.submit(() -> record(session, url, finalName, headers, endAt, sourceId, channelId)); }
      catch(java.util.concurrent.RejectedExecutionException stopped){sessions.remove(finalSession,session);InfinityCobraFeatureRuntime.recordingFinished(finalSession,session);if(sessions.isEmpty()){stopForeground(true);stopSelfResult(startId);}}''')
s=replace(s,'  public void onDestroy() {\n    for (Session session : sessions.values()) session.cancel.set(true);','  public void onDestroy() {\n    for (Session session : sessions.values()) {session.cancel.set(true);InfinityCobraFeatureRuntime.recordingFinished(session.id,session);}')
s=replace(s,'      sessions.remove(session.id);','      sessions.remove(session.id,session);\n      InfinityCobraFeatureRuntime.recordingFinished(session.id,session);')
s=replace(s,'''      if (sessions.isEmpty()) {
        stopForeground(true);
        stopSelf();
      }''','''      // Serialize the last-session check with onStartCommand. A finishing
      // worker must not stop a newer recording that started in the meantime.
      new android.os.Handler(getMainLooper()).post(() -> {
        if (sessions.isEmpty()) { stopForeground(true); stopSelf(); }
      });''')
f.write_text(s)

f=src/'InfinityLiveActivity.java.in';s=f.read_text()
s=replace(s,'  private void toggleRecording(Channel channel) {',(here/'recording_ui.java.fragment').read_text()+'  private void toggleRecording(Channel channel) {\n    cobraSyncRecordingState();')
s=replace(s,'mRecordingSession = ""; toast("Recording stop requested");','mRecordingSession = ""; mPrefs.edit().remove("cobra_active_recording_session").apply(); toast("Recording stop requested");')
s=replace(s,'          else toast("Recording started");','          else {mPrefs.edit().putString("cobra_active_recording_session",mRecordingSession).apply();toast("Recording started");}')
s=replace(s,'"At least 256 MB of free recording space is required."','"Recording could not start. Check available storage and Cobra Health Center for details."')
s=replace(s,'    LinearLayout rows=cobraOpenSheet("Player settings","Viewing preferences and recording","player-settings");','    cobraSyncRecordingState();\n    LinearLayout rows=cobraOpenSheet("Player settings","Viewing preferences and recording","player-settings");')
s=replace(s,'    rows.addView(cobraSheetRow("record",mRecordingSession.isEmpty()?"Record now":"Stop recording",null,false,true,()->{if(mPlaying!=null)toggleRecording(mPlaying);}));','    LinearLayout recording=cobraSheetRow("record",mRecordingSession.isEmpty()?"Record now":"Stop recording",null,false,true,()->{if(mPlaying!=null)toggleRecording(mPlaying);});recording.setTag("cobra_recording_action");rows.addView(recording);')
s=replace(s,'      if (!cobraGuidePresentationActive()) return;','      if (!cobraGuidePresentationActive()) return;\n      cobraSyncRecordingState();')
s=replace(s,'    cobraEndMiniBackgroundPlayback();\n    InfinityExtendedBackgroundService.sync(this);','    cobraEndMiniBackgroundPlayback();\n    cobraSyncRecordingState();\n    InfinityExtendedBackgroundService.sync(this);')
s=replace(s,'  private boolean cobraVodSeekable(){','''  private boolean cobraFinitePlayback(){
    if(mPlayingVodKey!=null&&!mPlayingVodKey.isEmpty())return true;
    return mPlaying!=null&&mPlaying.id!=null&&(mPlaying.id.startsWith("recording:")||mPlaying.id.startsWith("local:"));
  }
  private boolean cobraVodSeekable(){''')
s=replace(s,'if(mPlayingVodKey==null||mPlayingVodKey.isEmpty()||mPlayer==null)return false;','if(!cobraFinitePlayback()||mPlayer==null)return false;')
s=replace(s,'if(!mPlayingVodKey.isEmpty()){cobraSeekVodBy(-amountMs);return;}','if(cobraFinitePlayback()){cobraSeekVodBy(-amountMs);return;}')
s=replace(s,'if(!mPlayingVodKey.isEmpty()){cobraSeekVodBy(30000L);return;}','if(cobraFinitePlayback()){cobraSeekVodBy(30000L);return;}')
s=replace(s,'    if(!mPlayingVodKey.isEmpty()){\n      boolean enabled=cobraVodSeekable();','    if(cobraFinitePlayback()){\n      boolean enabled=cobraVodSeekable();')
s=replace(s,'boolean liveWindow=available&&!mCobraProviderCatchupActive&&mPlayingVodKey.isEmpty();','boolean liveWindow=available&&!mCobraProviderCatchupActive&&!cobraFinitePlayback();')
s=replace(s,'if(!mPlayingVodKey.isEmpty()&&mPlayer!=null&&mCobraPlayerSchedule!=null){','if(cobraFinitePlayback()&&mPlayer!=null&&mCobraPlayerSchedule!=null){')
f.write_text(s)

f=root/'shell-kodi/tools/android/packaging/xbmc/build.gradle.in';s=f.read_text().replace('versionCode 2103279','versionCode 2103280').replace('1.0.9-End-to-End-Repair-RC1','1.0.9-Audit-Followup-RC1');f.write_text(s)
base='60e1893d8591a29fab7e952ea2d3caedb0b13fa5';apk='cf7aedadded921e5ddc023ba08161638d8f6207dd7002f3258daf178073679cd'
f=root/'scripts/infinity_background_resume.py';s=f.read_text()
for key,value in [('VERSION_CODE','2103280'),('RELEASE',repr('1.0.9-Audit-Followup-RC1')),('BASE_COMMIT',repr(base)),('BASE_APK_SHA256',repr(apk))]:
 s,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,s,flags=re.M);assert n==1
f.write_text(s)
f=root/'scripts/package_background_resume.py';s=f.read_text().replace('Infinity-2103279-End-to-End-Repair-RC1','Infinity-2103280-Audit-Followup-RC1').replace("'base_run':36794611568","'base_run':36810766190");f.write_text(s)
f=root/'engine/background-resume-source.json';r=json.loads(f.read_text());r.update(base_source_commit=base,base_apk_sha256=apk,version_code=2103280,release='1.0.9-Audit-Followup-RC1',candidate_locked=False,physical_device_verified=False)
for name in ['InfinityLiveActivity.java.in','InfinityCobraFeatureRuntime.java.in','InfinityCobraRecordingService.java.in']:
 path='tools/android/packaging/xbmc/src/'+name;r['files'].setdefault(path,{})['after']=hashlib.sha256((root/'shell-kodi'/path).read_bytes()).hexdigest()
path='tools/android/packaging/xbmc/build.gradle.in';r['files'].setdefault(path,{})['after']=hashlib.sha256((root/'shell-kodi'/path).read_bytes()).hexdigest()
f.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
