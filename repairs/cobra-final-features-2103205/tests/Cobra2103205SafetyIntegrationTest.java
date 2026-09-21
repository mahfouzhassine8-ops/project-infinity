package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Looper;
import android.view.TextureView;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Activity loaders/refresh with controlled player and unstarted local
 * timeshift transport. Ownership assertions are not physical playback proof. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w1600dp-h900dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205SafetyIntegrationTest {
  Cobra2103201MenuPolishTest fixture;InfinityLiveActivity a;Cobra2103205SafetyTest data;
  @Before public void before()throws Exception{
    Context app=RuntimeEnvironment.getApplication();CobraPresentationSafety.cancel(app,false);CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));CobraVisualTheme.deleteTree(CobraPresentationSafety.root(app));
    data=new Cobra2103205SafetyTest();data.clearStatic("stateCache");data.clearStatic("initialized");
    fixture=new Cobra2103201MenuPolishTest();fixture.before();a=fixture.a;data.app=a.getApplicationContext();
  }
  @After public void after()throws Exception{CobraPresentationSafety.cancel(a,false);data.drain();fixture.after();}
  Object call(String name,Object...args)throws Exception{return CobraNavigationUiTest.call(a,name,args);}
  Object get(Object owner,String name)throws Exception{return CobraNavigationUiTest.get(owner,name);}
  Object load(String name)throws Exception{Class<?> type=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+name);Method method=type.getDeclaredMethod("load",Context.class);method.setAccessible(true);return method.invoke(null,a);}
  File legacyConfigured()throws Exception{
    Map<String,byte[]> files=data.legacy("#FF00FF");String themeKey=CobraVisualTheme.PREFIX+"resources/cobra-theme.json",uiKey=CobraVisualTheme.PREFIX+"resources/cobra-ui.json";
    JSONObject palette=new JSONObject(new String(files.get(themeKey),StandardCharsets.UTF_8));palette.put("palettes",new JSONObject().put("dark",new JSONObject().put("background","#FF00FF")));files.put(themeKey,palette.toString().getBytes(StandardCharsets.UTF_8));
    JSONObject ui=new JSONObject(new String(files.get(uiKey),StandardCharsets.UTF_8));ui.put("navigation",new JSONObject().put("mode","rail"));files.put(uiKey,ui.toString().getBytes(StandardCharsets.UTF_8));
    File directory=CobraPresentationSafety.stageLegacy(a,files);JSONObject state=new JSONObject().put("legacy_active",directory.getName().substring(7));CobraPresentationSafety.writeState(a,state);return directory;
  }
  @Test public void actualActivitySafeLoadersIgnoreLegacyPaletteLayoutAndSystemBarOverrides()throws Exception{
    legacyConfigured();assertEquals(Color.MAGENTA,get(load("Theme"),"background"));assertEquals("rail",get(load("UiContract"),"navigationMode"));
    a.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));a.cobraRefreshSafetyPresentation();
    assertEquals(Color.BLACK,get(get(a,"mTheme"),"background"));assertEquals("drawer",get(get(a,"mUi"),"navigationMode"));assertNull(call("cobraAppearancePalette","dark"));assertEquals("dark",call("cobraEffectiveAppearanceMode"));assertEquals(Color.BLACK,call("cobraBrowseSystemBarSurfaceColor"));
  }
  @Test public void actualSafeRefreshKeepsPlayerAndReturnsToOriginalConfiguration()throws Exception{
    File legacy=legacyConfigured();Object player=get(a,"mPlayer"),texture=get(a,"mPlayerTexture");String state=CobraPresentationSafety.state(a).toString();
    a.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));a.cobraRefreshSafetyPresentation();a.setIntent(new Intent());a.cobraRefreshSafetyPresentation();
    assertSame(player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertEquals(Color.MAGENTA,get(get(a,"mTheme"),"background"));assertEquals("rail",get(get(a,"mUi"),"navigationMode"));assertEquals(state,CobraPresentationSafety.state(a).toString());assertTrue(legacy.isDirectory());
  }
  @Test public void visualPreviewAndRevertRetainPlayerTextureTimeshiftAndTransportCounters()throws Exception{
    Object player=get(a,"mPlayer"),texture=get(a,"mPlayerTexture"),overlay=get(a,"mPlayerOverlay");
    Object session=CobraNavigationUiTest.construct("CobraLocalTimeshiftSession",a.getCacheDir(),"https://example.invalid/test.ts",Collections.emptyMap(),60,0);
    CobraNavigationUiTest.put(a,"mCobraTimeshiftSession",session);int writes=fixture.controlled.writes.size();
    CobraPresentationSafety.offerVisual(a,data.staged("preview","#145FDF"));fixture.fixture.ui.measure(a,1600,900);
    assertSame(player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertSame(overlay,get(a,"mPlayerOverlay"));assertSame(session,get(a,"mCobraTimeshiftSession"));assertEquals(false,get(session,"stopped"));
    CobraPresentationSafety.cancel(a,true);assertSame(player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertSame(session,get(a,"mCobraTimeshiftSession"));
    for(String operation:fixture.controlled.writes.subList(writes,fixture.controlled.writes.size()))assertFalse(operation,operation.equals("release")||operation.equals("prepare")||operation.startsWith("seek")||operation.contains("VideoTexture"));
    Cobra2103201MenuPolishTest.capture(a,fixture.fixture.ui,"cobra205-safety-player-restored",1600,900);
  }
  @Test public void legacyPreviewRestylesActualThemeWithoutRebuildingFullscreenSurface()throws Exception{
    File legacy=legacyConfigured();Object player=get(a,"mPlayer"),texture=get(a,"mPlayerTexture"),overlay=get(a,"mPlayerOverlay");String prior=CobraPresentationSafety.state(a).toString();
    File candidate=CobraPresentationSafety.stageLegacy(a,data.legacy("#123456"));CobraPresentationSafety.offerLegacy(a,candidate);
    assertEquals(Color.parseColor("#123456"),get(get(a,"mTheme"),"background"));assertSame(player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertSame(overlay,get(a,"mPlayerOverlay"));
    CobraPresentationSafety.onStop(a);CobraPresentationSafety.onResume(a);assertEquals(Color.MAGENTA,get(get(a,"mTheme"),"background"));assertEquals(prior,CobraPresentationSafety.state(a).toString());assertEquals(legacy,CobraPresentationSafety.legacyDirectory(a));
  }
}
