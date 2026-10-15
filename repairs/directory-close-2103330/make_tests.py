"""Retain all 329 parser tests; replace three removed-window tests with containment tests."""
from pathlib import Path

def generate(original):
    s=original.read_text().replace('LiveClosing329Test','LiveClosing330Test')
    def replace_method(text,name,new):
        start=text.index('  @Test public void '+name);a=text.index('{',start);depth=1;i=a+1
        while depth:depth+=(text[i]=='{')-(text[i]=='}');i+=1
        return text[:start]+new+text[i:]
    s=replace_method(s,'popupRejectsStaleOrMalformedIdentity', '''  @Test public void noClosingActivityIsRegistered()throws Exception{
    Application a=RuntimeEnvironment.getApplication();
    try{a.getPackageManager().getActivityInfo(new ComponentName(a.getPackageName(),a.getPackageName()+".InfinityClosingActivity"),0);fail("extra shutdown window still registered");}
    catch(PackageManager.NameNotFoundException expected){}
  }''')
    s=replace_method(s,'popupHasIndependentPrivateProcess', '''  @Test public void manifestKeepsThePrivateNoDisplayBridge()throws Exception{
    Application a=RuntimeEnvironment.getApplication();ActivityInfo info=a.getPackageManager().getActivityInfo(new ComponentName(a,InfinityPowerControlActivity.class),0);
    assertFalse(info.exported);assertEquals(a.getPackageName()+":kodi",info.processName);
  }''')
    s=replace_method(s,'independentCardRepaintsFromGuardWithoutKodiRenderer', '''  @Test public void notificationOpensChooserAndNeverTheRemovedWindow()throws Exception{
    InfinityCloseGuardService service=Robolectric.buildService(InfinityCloseGuardService.class).create().get();
    try{Field f=InfinityCloseGuardService.class.getDeclaredField("session");f.setAccessible(true);f.set(service,new InfinityCloseGuardService.Session(OWNER,OWNER,42,SystemClock.elapsedRealtime()));
      Method m=InfinityCloseGuardService.class.getDeclaredMethod("notice",String.class);m.setAccessible(true);
      Notification n=(Notification)m.invoke(service,"Finishing scripts");
      Intent intent=shadowOf(n.contentIntent).getSavedIntent();
      assertEquals(Splash.class.getName(),intent.getComponent().getClassName());
      assertEquals("infinity-shutdown-2103330-v1",InfinityCloseProgress.ENGINE);
    }finally{service.onDestroy();}
  }''')
    assert s.count('@Test')==24 and 'InfinityClosingActivity.class' not in s
    return s
