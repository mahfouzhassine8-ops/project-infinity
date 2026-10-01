from pathlib import Path
build=Path('build280');out=build/'xbmc/src/androidTest/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
source=Path('repairs/audit-followup-2103280')
head=(source/'CobraRuntimeFollowupTest.java').read_text()
head=head.replace('void check(String name,Action action){long start=', 'void check(String name,Action action){if(!name.toLowerCase(java.util.Locale.US).contains("recording"))return;long start=')
body=(source/'journey.java.fragment').read_text()
assert 'Finished recording clears active UI' in body
old='screenshot("recorded-playback");runUi(()->call(a,"closeFullscreenToCobraView"));'
new='''
   ExoPlayer local=ui(()->(ExoPlayer)get(a,"mPlayer"));runUi(()->{local.pause();call(a,"showPlayerChromeTemporarily");call(a,"cobraUpdateTimeshiftSeek");});
   await("Recording has a seekable file timeline",()->Boolean.TRUE.equals(call(a,"cobraVodSeekable")),10000);
   await("Recording scrubber is visible",()->{View v=(View)get(a,"mCobraTimeshiftSeek");return v!=null&&v.isShown()&&v.getWidth()>50;},5000);
   Rect timeline=ui(()->{Rect r=new Rect();((View)get(a,"mCobraTimeshiftSeek")).getGlobalVisibleRect(r);return r;});
   long expected=ui(local::getDuration)/2L,down=SystemClock.uptimeMillis();
   for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_MOVE,MotionEvent.ACTION_UP}){MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,timeline.exactCenterX(),timeline.exactCenterY(),0);try{ins.sendPointerSync(e);}finally{e.recycle();}SystemClock.sleep(60);}
   await("Recording scrubber seeks the existing decoder",()->Math.abs(local.getCurrentPosition()-expected)<500L,5000);assertSame(local,ui(()->get(a,"mPlayer")));
   screenshot("recording-seek");press("Rewind 30 seconds");await("Recording rewind reaches beginning",()->local.getCurrentPosition()<200L,5000);
   screenshot("recorded-playback");runUi(()->call(a,"closeFullscreenToCobraView"));'''
assert body.count(old)==1;body=body.replace(old,new)
(out/'CobraRuntimeFollowupTest.java').write_text(head+body)
with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testBuildType "release"; defaultConfig { testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner" } }
dependencies { androidTestImplementation "androidx.test:runner:1.6.2"; androidTestImplementation "androidx.test.ext:junit:1.2.1" }
''')
