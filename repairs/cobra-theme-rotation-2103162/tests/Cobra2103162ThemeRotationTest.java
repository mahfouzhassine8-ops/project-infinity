package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import androidx.media3.common.Format;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.concurrent.TimeUnit;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Android UI/storage/bridge acceptance; no physical decoder or provider claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103162ThemeRotationTest {
  CobraNavigationUiTest ui; Context app;
  @Before public void before(){
    app=RuntimeEnvironment.getApplication();
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
    app.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).edit().clear().commit();
    ui=new CobraNavigationUiTest();ui.clock();
  }
  @After public void after(){
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
  }
  // The inherited UI fixture attaches views without running onCreate/onResume.
  // Arrange the resumed precondition explicitly and use the REAL existing bridge.
  InfinityLiveActivity foregroundFixture()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);set(a,"mCobraRotationResumed",true);
    InfinityCobraDeviceBridge bridge=new InfinityCobraDeviceBridge(a,()->{
      try{return (Boolean)call(a,"hasCobraVideo");}catch(Exception e){throw new AssertionError(e);}
    });set(a,"mDeviceBridge",bridge);bridge.onResume();return a;
  }
  ExoPlayer activePlayer(InfinityLiveActivity a)throws Exception{
    ExoPlayer player=fakeVideoPlayer(new int[]{Player.STATE_READY},new boolean[]{true});
    FrameLayout overlay=new FrameLayout(a);a.setContentView(overlay);set(a,"mPlayerOverlay",overlay);set(a,"mPlayer",player);
    a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).edit().putInt("mode",1).commit();
    call(a,"cobraApplyPlayerRotation","arrange-active");assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());return player;
  }
  void closeFixture(InfinityLiveActivity a)throws Exception{
    InfinityCobraDeviceBridge bridge=(InfinityCobraDeviceBridge)CobraNavigationUiTest.get(a,"mDeviceBridge");if(bridge!=null)bridge.close();ui.clean(a);
  }
  Object call(Object owner,String name,Object...args)throws Exception{
    Method found=null;
    for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){found=m;break;}
    if(found==null)throw new NoSuchMethodException(name);found.setAccessible(true);return found.invoke(owner,args);
  }
  void set(Object owner,String name,Object value)throws Exception{
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);
  }
  View tag(android.app.Activity a,String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  TextView findText(View v,String text){
    if(v instanceof TextView&&text.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView r=findText(g.getChildAt(i),text);if(r!=null)return r;}}
    return null;
  }
  View clickableAncestor(View v){
    View p=v;
    while(p!=null&&!p.isClickable()){android.view.ViewParent parent=p.getParent();p=parent instanceof View?(View)parent:null;}
    return p;
  }
  boolean await(java.util.concurrent.Callable<Boolean> condition)throws Exception{
    long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
    // A frozen idle() alone does not advance pending frame/publication messages.
    // Advance bounded Android frames, retain the timeout and all real assertions.
    while(System.nanoTime()<end){Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));if(condition.call())return true;Thread.sleep(10);}
    return false;
  }
  JSONObject node(String slot,int x,int y,int w,int h)throws Exception{return new JSONObject().put("id",slot).put("type","slot").put("slot",slot).put("rect",new JSONArray(java.util.Arrays.asList(x,y,w,h)));}
  JSONObject theme(String id)throws Exception{
    JSONObject scene=new JSONObject().put("width",412).put("height",915).put("nodes",new JSONArray()
      .put(node("enter.infinity",20,250,372,64)).put(node("settings.infinity",20,320,372,52))
      .put(node("enter.cobra",20,500,372,64)).put(node("settings.cobra",20,570,372,52)));
    return new JSONObject().put("schema",2).put("scope","cobra-presentation").put("minimum_runtime",2).put("minimum_build",2103162)
      .put("id",id).put("name","Theme "+id).put("assets",new JSONObject()).put("base",new JSONObject().put("scenes",new JSONObject().put("chooser",scene)));
  }
  final java.util.ArrayList<String> playerCommands=new java.util.ArrayList<>();
  ExoPlayer fakeVideoPlayer(int[] state,boolean[] playWhenReady){
    return (ExoPlayer)Proxy.newProxyInstance(getClass().getClassLoader(),new Class[]{ExoPlayer.class},(proxy,method,args)->{
      String n=method.getName();
      if(n.equals("hashCode"))return System.identityHashCode(proxy);
      if(n.equals("equals"))return proxy==args[0];
      if(n.equals("toString"))return "ControlledVideoPlayer";
      if(n.equals("prepare")||n.equals("release")||n.equals("stop")||n.equals("pause")||n.equals("setMediaItem"))playerCommands.add(n);
      if(n.equals("getVideoFormat"))return new Format.Builder().setSampleMimeType("video/avc").build();
      if(n.equals("getPlaybackState"))return state[0];
      if(n.equals("isPlaying"))return state[0]==Player.STATE_READY&&playWhenReady[0];
      if(n.equals("getPlayWhenReady"))return playWhenReady[0];
      Class<?> t=method.getReturnType();
      if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;
      return null;
    });
  }

  @Test public void settingsUseOneThemeEntryAndNoLegacyThemeButtonStack()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      call(a,"showSettings");ui.measure(a,412,915);
      View theme=tag(a,"cobra_theme_management");assertNotNull(theme);assertTrue(theme instanceof TextView);
      assertTrue(((TextView)theme).getText().toString().contains("BUILT-IN"));
      assertNotNull(tag(a,"cobra_background_mode"));
      assertNull(tag(a,"cobra_theme_install"));assertNull(tag(a,"cobra_visual_theme_state"));
      assertNull(tag(a,"cobra-visual-theme-controls:previous"));assertNull(tag(a,"cobra-visual-theme-controls:builtin"));
    }finally{closeFixture(a);}
  }

  @Test public void oneThemeSheetSwitchesToBuiltInThenBackToSameInstalledTheme()throws Exception{
    CobraVisualRuntimeTest harness=new CobraVisualRuntimeTest();harness.context=app;
    CobraVisualTheme installed=harness.install(theme("hm-test"));harness.activate(installed);
    InfinityLiveActivity a=foregroundFixture();try{
      call(a,"showSettings");ui.measure(a,412,915);assertTrue(((TextView)tag(a,"cobra_theme_management")).getText().toString().contains("CUSTOM"));
      assertTrue(tag(a,"cobra_theme_management").performClick());ui.measure(a,412,915);
      TextView builtin=findText(a.getWindow().getDecorView(),"Built-in appearance");assertNotNull(builtin);
      View builtRow=clickableAncestor(builtin);assertNotNull(builtRow);assertTrue(builtRow.performClick());
      assertTrue("Built-in snapshot must be published while Android frames advance",await(()->CobraVisualRenderer.active.id.equals("builtin")));
      assertTrue(CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
      assertFalse(CobraVisualTheme.readPointer(a).optString("previous","").isEmpty());
      call(a,"showSettings");ui.measure(a,412,915);assertTrue(tag(a,"cobra_theme_management").performClick());ui.measure(a,412,915);
      TextView custom=findText(a.getWindow().getDecorView(),"Installed visual theme");assertNotNull(custom);
      View customRow=clickableAncestor(custom);assertNotNull(customRow);assertTrue(customRow.performClick());
      assertTrue("The exact installed theme must be restored",await(()->CobraVisualRenderer.active.id.equals("hm-test")));
      assertFalse(CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void backgroundModeStillUsesTheExistingNormalExtendedContract()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      a.getSharedPreferences("infinity_runtime",Context.MODE_PRIVATE).edit().putBoolean("extended_background",true).commit();
      call(a,"showSettings");ui.measure(a,412,915);
      TextView background=(TextView)tag(a,"cobra_background_mode");assertNotNull(background);assertTrue(background.getText().toString().contains("EXTENDED"));
      assertTrue(background.performClick());ui.measure(a,412,915);
      View normal=tag(a,"cobra-background-mode:normal");View extended=tag(a,"cobra-background-mode:extended");
      assertNotNull(normal);assertNotNull(extended);assertTrue(normal.performClick());
      assertFalse(InfinityExtendedBackgroundService.isEnabled(a));
      call(a,"showSettings");ui.measure(a,412,915);
      assertTrue(((TextView)tag(a,"cobra_background_mode")).getText().toString().contains("NORMAL"));
    }finally{InfinityExtendedBackgroundService.setEnabled(a,false);closeFixture(a);}
  }

  @Test public void chooserStillConsumesSystemBarInsets()throws Exception{
    CobraVisualRuntimeTest harness=new CobraVisualRuntimeTest();harness.context=app;harness.activate(harness.install(theme("safe-area")));
    ExperienceChooserUiTest.reflect();ExperienceChooserUiTest old=new ExperienceChooserUiTest();Splash a=old.activity();try{
      ExperienceChooserUiTest.chooser.invoke(a);View root=tag(a,"experience-themed-root");assertNotNull(root);
      android.view.WindowInsets insets=new android.view.WindowInsets.Builder().setSystemWindowInsets(android.graphics.Insets.of(0,32,0,20)).build();
      root.dispatchApplyWindowInsets(insets);
      assertEquals(32,root.getPaddingTop());assertEquals(20,root.getPaddingBottom());
      assertEquals(0,root.getPaddingLeft());assertEquals(0,root.getPaddingRight());
      assertNotNull(tag(a,"experience-card-infinity"));assertNotNull(tag(a,"experience-card-cobra"));
    }finally{old.closeWindows();}
  }

  @Test public void playerChromeHasRotationBesideLockAndUsesSharedInfinityPreference()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      FrameLayout overlay=new FrameLayout(a);a.setContentView(overlay);set(a,"mPlayerOverlay",overlay);
      overlay.measure(View.MeasureSpec.makeMeasureSpec(412,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(915,View.MeasureSpec.EXACTLY));overlay.layout(0,0,412,915);
      call(a,"cobraBuildPlayerChrome");
      View rotate=tag(a,"cobra_player_rotation");assertNotNull(rotate);
      assertTrue(rotate.getContentDescription().toString().contains("follows device"));
      assertEquals(0,a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).getInt("mode",0));
      assertTrue(rotate.performClick());assertEquals(1,a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).getInt("mode",0));
      assertTrue(rotate.getContentDescription().toString().contains("unlocked"));
      assertTrue(rotate.performClick());assertEquals(0,a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).getInt("mode",1));
    }finally{closeFixture(a);}
  }

  @Test public void unlockedRotationRequestsFullSensorOnlyForEligibleActiveVideo()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      int[] state={Player.STATE_READY};boolean[] playWhenReady={true};
      FrameLayout overlay=new FrameLayout(a);a.setContentView(overlay);set(a,"mPlayerOverlay",overlay);set(a,"mPlayer",fakeVideoPlayer(state,playWhenReady));
      a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).edit().putInt("mode",1).commit();
      call(a,"cobraApplyPlayerRotation","test-active");assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());
      state[0]=Player.STATE_ENDED;call(a,"cobraApplyPlayerRotation","test-ended");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      state[0]=Player.STATE_READY;set(a,"mBackgroundStopped",true);call(a,"cobraApplyPlayerRotation","test-background");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
    }finally{closeFixture(a);}
  }

  @Test public void latePlaybackCallbackCannotReacquireRotationAfterPause()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      ExoPlayer player=activePlayer(a);call(a,"onPause");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      call(a,"cobraApplyPlayerRotation","late-playback-callback");
      ((InfinityCobraDeviceBridge)CobraNavigationUiTest.get(a,"mDeviceBridge")).onWindowChanged("late-policy-change");
      assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      assertSame(player,CobraNavigationUiTest.get(a,"mPlayer"));assertTrue(playerCommands.isEmpty());
      assertEquals(1,a.getSharedPreferences("infinity_player_rotation",0).getInt("mode",0));
    }finally{closeFixture(a);}
  }

  @Test public void fullscreenToPreviewReleasesRotationWithoutReplacingThePlayer()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);
      Object preview=CobraNavigationUiTest.get(a,"mCobraPreviewTexture");
      Object channel=((java.util.List<?>)CobraNavigationUiTest.get(a,"mChannels")).get(0);
      ExoPlayer player=fakeVideoPlayer(new int[]{Player.STATE_READY},new boolean[]{true});
      FrameLayout overlay=new FrameLayout(a);((FrameLayout)a.getWindow().getDecorView()).addView(overlay);
      set(a,"mPlayerOverlay",overlay);set(a,"mPlayer",player);set(a,"mPlaying",channel);
      a.getSharedPreferences("infinity_player_rotation",0).edit().putInt("mode",1).commit();
      call(a,"cobraApplyPlayerRotation","fullscreen");assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());
      call(a,"closeFullscreenToCobraView");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      assertNull(CobraNavigationUiTest.get(a,"mPlayerOverlay"));assertNull(CobraNavigationUiTest.get(a,"mCobraPlayerRotationButton"));
      assertSame(player,CobraNavigationUiTest.get(a,"mCobraPreviewPlayer"));assertSame(preview,CobraNavigationUiTest.get(a,"mCobraPreviewTexture"));
      assertTrue("Handoff must not restart or release playback",playerCommands.isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void splitWindowCallbackBlocksLateRotationUntilExit()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      activePlayer(a);a.onMultiWindowModeChanged(true,a.getResources().getConfiguration());assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      call(a,"cobraApplyPlayerRotation","late-window-callback");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      a.onMultiWindowModeChanged(false,a.getResources().getConfiguration());assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());assertTrue(playerCommands.isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void pipAndTelevisionNeverAcquireRotation()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      activePlayer(a);set(a,"mInPictureInPicture",true);call(a,"cobraApplyPlayerRotation","pip");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      set(a,"mInPictureInPicture",false);Shadows.shadowOf(a.getPackageManager()).setSystemFeature("android.software.leanback",true);
      call(a,"cobraApplyPlayerRotation","tv");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());assertTrue(playerCommands.isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void controlsLockPreventsRotationPreferenceChanges()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      activePlayer(a);set(a,"mCobraPlayerLocked",true);call(a,"cobraTogglePlayerRotation");
      assertEquals(1,a.getSharedPreferences("infinity_player_rotation",0).getInt("mode",0));
      assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());assertTrue(playerCommands.isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void invalidMultiviewRequestLeavesFullscreenOrientationAlone()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      activePlayer(a);call(a,"openMultiView",(Object)null);
      assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());assertTrue(playerCommands.isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void repeatedBuiltInResetKeepsTheSameThemeRestorable()throws Exception{
    CobraVisualRuntimeTest helper=new CobraVisualRuntimeTest();helper.context=app;
    CobraVisualTheme installed=helper.install(theme("keep-me"));helper.activate(installed);
    app.getSharedPreferences("untouched-user-data",0).edit().putString("playlist","preserved").commit();
    CobraVisualTheme.reset(app);String pointer=CobraVisualTheme.readPointer(app).toString();CobraVisualTheme.reset(app);CobraVisualTheme.reset(app);
    assertEquals(pointer,CobraVisualTheme.readPointer(app).toString());assertEquals("keep-me",CobraVisualTheme.rollback(app).id);
    assertEquals("preserved",app.getSharedPreferences("untouched-user-data",0).getString("playlist",""));
  }

  @Test public void corruptSavedThemeCannotReplaceBuiltInSnapshot()throws Exception{
    CobraVisualRuntimeTest helper=new CobraVisualRuntimeTest();helper.context=app;
    CobraVisualTheme installed=helper.install(theme("corrupt-saved"));CobraVisualTheme.reset(app);String pointer=CobraVisualTheme.readPointer(app).toString();
    try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(installed.directory,CobraVisualTheme.MANIFEST))){out.write("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    boolean rejected=false;try{CobraVisualTheme.rollback(app);}catch(Exception expected){rejected=true;}
    assertTrue("Corrupt snapshot must be rejected, not published",rejected);assertEquals(pointer,CobraVisualTheme.readPointer(app).toString());assertEquals("builtin",CobraVisualTheme.load(app).id);
  }

  @Test public void pausedIdleEndedOrMissingVideoCannotOwnOrientation()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      int[] state={Player.STATE_READY};boolean[] play={true};ExoPlayer player=fakeVideoPlayer(state,play);
      FrameLayout overlay=new FrameLayout(a);set(a,"mPlayerOverlay",overlay);set(a,"mPlayer",player);
      a.getSharedPreferences("infinity_player_rotation",0).edit().putInt("mode",1).commit();
      for(int stopped:new int[]{Player.STATE_IDLE,Player.STATE_ENDED}){state[0]=stopped;call(a,"cobraApplyPlayerRotation","state");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());}
      state[0]=Player.STATE_READY;play[0]=false;call(a,"cobraApplyPlayerRotation","paused");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      play[0]=true;set(a,"mPlayer",null);call(a,"cobraApplyPlayerRotation","no-player");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      set(a,"mPlayer",player);a.getSharedPreferences("infinity_player_rotation",0).edit().putInt("mode",0).commit();call(a,"cobraApplyPlayerRotation","follow-device");assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());assertTrue(playerCommands.isEmpty());
    }finally{closeFixture(a);}
  }

  @Test public void themePickerBindsNewRowRolesAndDefaultButtonsMatch()throws Exception{
    InfinityLiveActivity a=foregroundFixture();try{
      call(a,"showSettings");ui.measure(a,412,915);View theme=tag(a,"cobra_theme_management"),background=tag(a,"cobra_background_mode");
      assertNotNull(theme.getBackground());assertEquals(theme.getBackground().getClass(),background.getBackground().getClass());
      assertEquals(((TextView)theme).getCurrentTextColor(),((TextView)background).getCurrentTextColor());assertEquals(((TextView)theme).getTextSize(),((TextView)background).getTextSize(),.01f);
      theme.performClick();ui.measure(a,412,915);
      for(String role:new String[]{"cobra_theme_builtin","cobra_theme_installed","cobra_theme_install"}){View row=tag(a,role);assertNotNull(role,row);assertTrue(row.isClickable());assertTrue(row.getHeight()>=48);}
      call(a,"closeCobraActionSheet");
    }finally{closeFixture(a);}
  }
}
