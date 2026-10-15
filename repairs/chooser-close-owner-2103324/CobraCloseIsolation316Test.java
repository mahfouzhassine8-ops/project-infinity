package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Intent;
import android.net.Uri;
import android.widget.FrameLayout;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** Executes production Splash routing without creating a native Kodi activity. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public final class CobraCloseIsolation316Test {
  org.robolectric.android.controller.ActivityController<Splash> controller;Splash a;
  @Before public void before(){
    controller=Robolectric.buildActivity(Splash.class,new Intent(Intent.ACTION_MAIN));a=controller.get();
    a.setTheme(android.R.style.Theme_NoTitleBar);a.setContentView(new FrameLayout(a));
    a.getSharedPreferences("infinity_experience",0).edit().clear().commit();
    ReflectionHelpers.setField(a,"mInfinityStartupTrace",new InfinityStartupTrace(a));
    ReflectionHelpers.setStaticField(InfinityKodiShutdown.class,"cached",new InfinityKodiShutdown.Snapshot(
      24758,"closing-kodi","launch","",1791268400000L,1791268518551L,InfinityExitCompletion.Plan.Phase.DESTROYING,true,false,false));
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.loading.set(true);
    Main.MainActivity=null;
  }
  @After public void after(){controller.destroy();ReflectionHelpers.setStaticField(InfinityKodiShutdown.class,"cached",InfinityKodiShutdown.Snapshot.empty());Main.MainActivity=null;}
  void launch(String experience,boolean explicit,boolean safe){
    ReflectionHelpers.callInstanceMethod(a,"launchInfinityExperience",ReflectionHelpers.ClassParameter.from(String.class,experience),
        ReflectionHelpers.ClassParameter.from(boolean.class,explicit),ReflectionHelpers.ClassParameter.from(boolean.class,safe));
  }
  Intent started(){return Shadows.shadowOf(a).getNextStartedActivity();}
  void assertCobra(Intent i){assertNotNull(i);assertEquals("com.projectinfinity.kodi.InfinityLiveActivity",i.getComponent().getClassName());
    assertEquals("cobra",i.getStringExtra("infinity_live_profile"));assertTrue((i.getFlags()&Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP)!=0);assertNull(Main.MainActivity);}
  @Test public void cobraLaunchBypassesPendingKodiAndPreservesItsIntent(){
    InfinityKodiShutdown.Snapshot closing=InfinityKodiShutdown.state();
    a.setIntent(new Intent(Intent.ACTION_VIEW,Uri.parse("https://example.invalid/stream"))
        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION).putExtra("existing-extra","kept")
        .putExtra(CobraPresentationSafety.EXTRA_SAFE,true).putExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN,"old"));
    launch("live",true,false);Intent i=started();assertCobra(i);assertTrue(a.isFinishing());
    assertEquals("kept",i.getStringExtra("existing-extra"));assertEquals(a.getIntent().getData(),i.getData());
    assertTrue((i.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
    assertFalse(i.hasExtra(CobraPresentationSafety.EXTRA_SAFE));assertNotEquals("old",i.getStringExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN));
    assertSame("Launching Cobra cannot change Kodi shutdown",closing,InfinityKodiShutdown.state());assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void safeRecoveryEntryRemainsIndependent(){
    launch("live",true,true);Intent i=started();assertCobra(i);assertTrue(i.getBooleanExtra(CobraPresentationSafety.EXTRA_SAFE,false));
  }
  @Test public void cobraCanReplaceAQueuedInfinityHandoffWithoutSignallingKodi(){
    InfinityStartupHandoff handoff=new InfinityStartupHandoff(a,a.findViewById(android.R.id.content));final int[] sent={0};
    assertTrue(handoff.enqueue(()->sent[0]++));ReflectionHelpers.setField(a,"mInfinityHandoff",handoff);
    ReflectionHelpers.setField(a,"mInfinityLaunchQueued",true);ReflectionHelpers.setField(a,"mInfinityPendingMain",new Intent());
    launch("live",true,false);assertCobra(started());assertFalse(ReflectionHelpers.<Boolean>getField(a,"mInfinityLaunchQueued"));
    assertNull(ReflectionHelpers.getField(a,"mInfinityPendingMain"));assertTrue(ReflectionHelpers.<Boolean>getField(handoff,"closed"));
    handoff.resume();handoff.onDraw();Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();assertEquals(0,sent[0]);
    assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void rememberedCobraBypassesEvenUninitializedKodiMonitorAndPreparation(){
    a.getSharedPreferences("infinity_experience",0).edit().putString("default","live").commit();
    ReflectionHelpers.setField(a,"mInfinityKodiStateReady",false);
    ReflectionHelpers.callInstanceMethod(a,"infinityInitializeStartup");Intent i=started();assertCobra(i);
    assertFalse(i.hasExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN));assertFalse(i.hasExtra(CobraPresentationSafety.EXTRA_SAFE));
    assertFalse(ReflectionHelpers.<Boolean>getField(a,"mInfinityInitializationStarted"));
    assertNull(ReflectionHelpers.getField(a,"mInfinityPreparation"));
  }
  @Test public void rememberedCobraAlsoBypassesTheStartXbmcPendingGate(){
    a.getSharedPreferences("infinity_experience",0).edit().putString("default","live").commit();a.startXBMC();assertCobra(started());
  }
  @Test public void defaultCobraCannotOverrideAnExistingChooserOrInfinityDeepLink(){
    a.getSharedPreferences("infinity_experience",0).edit().putString("default","live").commit();
    ReflectionHelpers.setField(a,"mInfinityChooserVisible",true);
    assertFalse(ReflectionHelpers.<Boolean>callInstanceMethod(a,"infinityLaunchPreferredCobra"));assertNull(started());
    ReflectionHelpers.setField(a,"mInfinityChooserVisible",false);a.setIntent(new Intent(Intent.ACTION_VIEW,Uri.parse("file:///video.mp4")));
    assertFalse(ReflectionHelpers.<Boolean>callInstanceMethod(a,"infinityLaunchPreferredCobra"));assertNull(started());
    a.setIntent(new Intent(Intent.ACTION_MAIN));ReflectionHelpers.setField(a,"mInfinityPendingMain",new Intent());
    assertFalse(ReflectionHelpers.<Boolean>callInstanceMethod(a,"infinityLaunchPreferredCobra"));assertNull(started());
  }
  @Test public void infinityStillCannotStartWhileItsOwnerIsClosing(){
    launch("infinity",true,false);assertNull(started());assertFalse(a.isFinishing());
    assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityChooserVisible"));assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void ordinaryChooserDoesNotShowAClosingRecoveryPrompt(){
    a.startXBMC();assertNull(started());assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityChooserVisible"));
    assertNull(org.robolectric.shadows.ShadowDialog.getLatestDialog());assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void visibleChooserNeverReplaysTheDefaultInfinityRecoveryPrompt(){
    a.getSharedPreferences("infinity_experience",0).edit().putString("default","infinity").commit();
    ReflectionHelpers.setField(a,"mInfinityChooserVisible",true);a.startXBMC();assertNull(started());
    assertNull(org.robolectric.shadows.ShadowDialog.getLatestDialog());assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void anInfinityDefaultRetainsRecoveryForItsClosingOwner(){
    a.getSharedPreferences("infinity_experience",0).edit().putString("default","infinity").commit();
    a.startXBMC();assertNull(started());assertNotNull(org.robolectric.shadows.ShadowDialog.getLatestDialog());assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void explicitInfinitySelectionRetainsRecoveryForItsClosingOwner(){
    launch("infinity",true,false);assertNull(started());assertNotNull(org.robolectric.shadows.ShadowDialog.getLatestDialog());assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void infinityDeepLinkRetainsRecoveryWithoutLaunchingASecondOwner(){
    a.setIntent(new Intent(Intent.ACTION_VIEW,Uri.parse("file:///video.mp4")));a.startXBMC();assertNull(started());
    assertNotNull(org.robolectric.shadows.ShadowDialog.getLatestDialog());assertTrue(InfinityKodiShutdown.pending());
  }
  @Test public void infinityIsQueuedForReopeningAfterSameOwnerCompletes(){
    ReflectionHelpers.setStaticField(InfinityKodiShutdown.class,"cached",new InfinityKodiShutdown.Snapshot(
      24758,"closing-kodi","launch","",1791268400000L,1791268518551L,InfinityExitCompletion.Plan.Phase.COMPLETE,false,false,true));
    InfinityStartupHandoff handoff=new InfinityStartupHandoff(a,a.findViewById(android.R.id.content));
    ReflectionHelpers.setField(a,"mInfinityHandoff",handoff);ReflectionHelpers.setField(a,"mInfinityPreparationReady",true);
    launch("infinity",true,false);assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityLaunchQueued"));
    assertNotNull(ReflectionHelpers.getField(handoff,"pending"));assertNull(started());assertFalse(InfinityKodiShutdown.pending());
  }
}
