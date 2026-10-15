package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAlertDialog;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.zip.*;
import static org.junit.Assert.*;

/** Actual Android store, renderer and native dialogs. No device/decoder/network claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205SafetyTest {
  Context app;Activity activity;
  @Before public void setup()throws Exception{
    app=RuntimeEnvironment.getApplication();CobraVisualRenderer.loading.set(true);
    CobraPresentationSafety.cancel(app,false);drain();CobraVisualTheme.deleteTree(CobraPresentationSafety.root(app));CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
    clearStatic("stateCache");clearStatic("initialized");CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    activity=Robolectric.buildActivity(Activity.class).setup().get();activity.setContentView(new FrameLayout(activity));
  }
  @After public void finish()throws Exception{CobraPresentationSafety.cancel(app,false);drain();activity.finish();CobraVisualRenderer.clients.clear();CobraVisualRenderer.active=CobraVisualTheme.builtin();}
  void clearStatic(String name)throws Exception{java.lang.reflect.Field f=CobraPresentationSafety.class.getDeclaredField(name);f.setAccessible(true);Object value=f.get(null);if(value instanceof Map)((Map<?,?>)value).clear();else((Set<?>)value).clear();}
  void drain()throws Exception{Shadows.shadowOf(Looper.getMainLooper()).idle();CobraVisualRenderer.IO.submit(()->{}).get(8,TimeUnit.SECONDS);Shadows.shadowOf(Looper.getMainLooper()).idle();}
  CobraPresentationSafety.Lease lease()throws Exception{java.lang.reflect.Field f=CobraPresentationSafety.class.getDeclaredField("preview");f.setAccessible(true);return(CobraPresentationSafety.Lease)f.get(null);}
  JSONObject manifest(String id,String ink)throws Exception{return new JSONObject().put("schema",2).put("scope","cobra-presentation").put("minimum_runtime",2).put("minimum_build",2103160).put("id",id).put("name",id).put("assets",new JSONObject()).put("base",new JSONObject().put("colors",new JSONObject().put("palette.accent",ink)).put("styles",new JSONObject().put("all.button",new JSONObject().put("text",ink))));}
  byte[] zip(JSONObject value)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(out)){z.putNextEntry(new ZipEntry(CobraVisualTheme.PREFIX+CobraVisualTheme.MANIFEST));z.write(value.toString().getBytes(StandardCharsets.UTF_8));z.closeEntry();}return out.toByteArray();}
  CobraVisualTheme installed(String id,String color)throws Exception{CobraVisualTheme theme=CobraVisualTheme.install(app,new ByteArrayInputStream(zip(manifest(id,color))));CobraVisualRenderer.publish(theme,"test");drain();return theme;}
  CobraVisualTheme staged(String id,String color)throws Exception{return CobraVisualTheme.stagePreview(app,new ByteArrayInputStream(zip(manifest(id,color))));}
  Map<String,byte[]> legacy(String color)throws Exception{
    JSONObject contracts=new JSONObject();for(String key:new String[]{"rotation","fold","background_resume","renderer","provider_playback","infinity_handoff"})contracts.put(key,"native");
    JSONObject ui=new JSONObject().put("schema",1).put("runtime",new JSONObject().put("minimum_runtime",3).put("scope","cobra-live-only")).put("protected_contracts",contracts);
    Map<String,byte[]> files=new LinkedHashMap<>();files.put(CobraVisualTheme.PREFIX+"addon.xml","<addon id=\"script.infinity.cobra.theme\" version=\"1.0.0\"/>".getBytes(StandardCharsets.UTF_8));
    files.put(CobraVisualTheme.PREFIX+"resources/cobra-theme.json",new JSONObject().put("schema",2).put("background",color).toString().getBytes(StandardCharsets.UTF_8));
    files.put(CobraVisualTheme.PREFIX+"resources/cobra-ui.json",ui.toString().getBytes(StandardCharsets.UTF_8));return files;
  }
  void reject(Checked operation)throws Exception{try{operation.run();fail("Unsafe operation accepted");}catch(IOException expected){}}
  interface Checked{void run()throws Exception;}
  void assertReadCompletesWhileStoreLocked(Checked read)throws Exception{
    CountDownLatch started=new CountDownLatch(1),completed=new CountDownLatch(1);
    AtomicReference<Throwable> failure=new AtomicReference<>();
    Thread reader=new Thread(()->{
      started.countDown();try{read.run();}catch(Throwable error){failure.set(error);}finally{completed.countDown();}
    },"CobraWarmPresentationRead");
    try{
      synchronized(CobraVisualTheme.STORE_LOCK){
        reader.start();assertTrue("Reader must start",started.await(5,TimeUnit.SECONDS));
        // No elapsed-time benchmark: the lookup must finish before the store
        // owner releases its lock. Bounds only prevent a broken test hanging CI.
        assertTrue("Warm presentation read waited for background theme storage",completed.await(5,TimeUnit.SECONDS));
      }
    }finally{reader.join(5000);}
    assertFalse("Reader must terminate",reader.isAlive());if(failure.get()!=null)throw new AssertionError("Presentation read failed",failure.get());
  }
  @Test public void warmCachedStateDoesNotAcquireThemeStoreLock()throws Exception{
    JSONObject cached=CobraPresentationSafety.state(app);
    assertReadCompletesWhileStoreLocked(()->assertSame(cached,CobraPresentationSafety.state(app)));
  }
  @Test public void warmRendererColorLookupDoesNotAcquireThemeStoreLock()throws Exception{
    installed("warm-renderer","#123456");CobraVisualRenderer renderer=new CobraVisualRenderer(activity).mode("dark");
    assertEquals(Color.parseColor("#123456"),renderer.color("palette.accent",Color.BLUE));
    assertReadCompletesWhileStoreLocked(()->assertEquals(Color.parseColor("#123456"),renderer.color("palette.accent",Color.BLUE)));
  }
  @Test public void previewCancelKeepAndRestoreNeverMutatePublishedStateSnapshots()throws Exception{
    JSONObject initial=CobraPresentationSafety.state(app);String initialJson=initial.toString();
    CobraPresentationSafety.offerLegacy(activity,CobraPresentationSafety.stageLegacy(app,legacy("#123456")));
    assertSame(initial,CobraPresentationSafety.state(app));CobraPresentationSafety.cancel(activity,true);drain();assertSame(initial,CobraPresentationSafety.state(app));
    CobraPresentationSafety.offerLegacy(activity,CobraPresentationSafety.stageLegacy(app,legacy("#123456")));
    ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_POSITIVE).performClick();drain();
    JSONObject kept=CobraPresentationSafety.state(app);String keptJson=kept.toString();
    assertNotSame(initial,kept);assertEquals(initialJson,initial.toString());assertTrue(kept.optBoolean("visual_builtin"));assertFalse(kept.optBoolean("legacy_builtin"));
    CobraPresentationSafety.restoreBuiltIn(activity,null);drain();JSONObject restored=CobraPresentationSafety.state(app);String restoredJson=restored.toString();
    assertNotSame(kept,restored);assertEquals(keptJson,kept.toString());assertTrue(restored.optBoolean("legacy_builtin"));assertTrue(restored.optBoolean("visual_builtin"));
    CobraPresentationSafety.allowVisual(app);JSONObject allowed=CobraPresentationSafety.state(app);
    assertNotSame(restored,allowed);assertEquals(restoredJson,restored.toString());assertEquals(initialJson,initial.toString());assertFalse(allowed.optBoolean("visual_builtin"));
    assertReadCompletesWhileStoreLocked(()->assertSame(allowed,CobraPresentationSafety.state(app)));
  }
  @Test public void safeIntentIsActivityScopedAndDoesNotOverwritePreferences()throws Exception{
    installed("saved","#123456");String pointer=CobraVisualTheme.readPointer(app).toString();app.getSharedPreferences("infinity_cobra_live",0).edit().putString("source","kept").commit();
    activity.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));CobraVisualRenderer renderer=new CobraVisualRenderer(activity);
    assertTrue(CobraPresentationSafety.isSafe(new ContextWrapper(activity)));assertFalse(CobraPresentationSafety.isSafe(app));assertEquals(Color.BLUE,renderer.color("palette.accent",Color.BLUE));assertNull(CobraPresentationSafety.legacyDirectory(activity));
    assertEquals(pointer,CobraVisualTheme.readPointer(app).toString());assertEquals("kept",app.getSharedPreferences("infinity_cobra_live",0).getString("source",""));
  }
  @Test public void leavingSafeSessionRestoresSameInstalledTheme()throws Exception{
    installed("saved","#123456");activity.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));CobraVisualRenderer r=new CobraVisualRenderer(activity);assertEquals(7,r.color("palette.accent",7));
    activity.setIntent(new Intent());assertEquals(Color.parseColor("#123456"),r.color("palette.accent",7));assertEquals("saved",r.displayName());
  }
  @Test public void queuedPublicationCannotOverrideSafeInstance()throws Exception{
    CobraVisualTheme theme=installed("unsafe","#000000");activity.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));CobraVisualRenderer r=new CobraVisualRenderer(activity);
    CobraVisualRenderer.publish(theme,"late");drain();assertEquals(Color.WHITE,r.color("palette.accent",Color.WHITE));assertEquals("builtin",r.displayName());
  }
  @Test public void stageLeavesActivePreviousAndFilesUntouched()throws Exception{
    CobraVisualTheme first=installed("first","#123456"),second=installed("second","#654321");String before=CobraVisualTheme.readPointer(app).toString();CobraVisualTheme third=staged("third","#112233");
    assertEquals(before,CobraVisualTheme.readPointer(app).toString());assertEquals("second",CobraVisualTheme.load(app).id);assertTrue(first.directory.isDirectory());assertTrue(second.directory.isDirectory());assertTrue(third.directory.isDirectory());
  }
  @Test public void previewActuallyChangesNativeButtonAndRevertRestoresIt()throws Exception{
    installed("first","#112233");Button b=new Button(activity);b.setText("Preview surface");CobraVisualRenderer r=new CobraVisualRenderer(activity);r.paint(b,"widget.action");assertEquals(Color.parseColor("#112233"),b.getCurrentTextColor());
    CobraPresentationSafety.offerVisual(activity,staged("second","#145FDF"));assertEquals(Color.parseColor("#145FDF"),b.getCurrentTextColor());
    ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_NEGATIVE).performClick();drain();assertEquals(Color.parseColor("#112233"),b.getCurrentTextColor());assertFalse(CobraPresentationSafety.isPreviewing(activity));
  }
  @Test public void previewNeverReparentsOrStylesVideoTexture()throws Exception{
    TextureView texture=new TextureView(activity);FrameLayout parent=new FrameLayout(activity);parent.addView(texture,new FrameLayout.LayoutParams(100,80));Object params=texture.getLayoutParams();
    CobraVisualRenderer r=new CobraVisualRenderer(activity);r.tree(parent,"player.chrome");CobraPresentationSafety.offerVisual(activity,staged("candidate","#FFFFFF"));
    assertSame(parent,texture.getParent());assertSame(params,texture.getLayoutParams());assertEquals(0,texture.getPaddingLeft());assertNull(texture.getBackground());
  }
  @Test public void timeoutRestoresExactPointerHistoryAndUi()throws Exception{
    installed("first","#112233");installed("second","#223344");String pointer=CobraVisualTheme.readPointer(app).toString();CobraVisualRenderer r=new CobraVisualRenderer(activity);
    CobraPresentationSafety.offerVisual(activity,staged("third","#334455"));Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(21));drain();
    assertFalse(CobraPresentationSafety.isPreviewing(activity));assertEquals(pointer,CobraVisualTheme.readPointer(app).toString());assertEquals("second",r.displayName());
  }
  @Test public void onlyKeepCommitsDisplayedGeneration()throws Exception{
    CobraVisualTheme old=installed("first","#112233"),next=staged("second","#223344");CobraPresentationSafety.offerVisual(activity,next);
    ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_POSITIVE).performClick();drain();
    assertEquals(next.directory.getName(),CobraVisualTheme.readPointer(app).getString("active"));assertEquals(old.directory.getName(),CobraVisualTheme.readPointer(app).getString("previous"));assertEquals("second",CobraVisualTheme.load(app).id);
  }
  @Test public void staleTimeoutCannotRevertNewPreview()throws Exception{
    installed("first","#112233");CobraPresentationSafety.offerVisual(activity,staged("second","#223344"));CobraPresentationSafety.Lease old=lease();
    CobraPresentationSafety.offerVisual(activity,staged("third","#334455"));old.timeout.run();assertTrue(CobraPresentationSafety.isPreviewing(activity));assertEquals("third",new CobraVisualRenderer(activity).displayName());
  }
  @Test public void stoppedPreviewRevertsBindingsOnReturn()throws Exception{
    installed("first","#112233");Button b=new Button(activity);CobraVisualRenderer r=new CobraVisualRenderer(activity);r.paint(b,"widget.action");CobraPresentationSafety.offerVisual(activity,staged("second","#223344"));
    CobraPresentationSafety.onStop(activity);assertFalse(CobraPresentationSafety.isPreviewing(activity));CobraPresentationSafety.onResume(activity);assertEquals(Color.parseColor("#112233"),b.getCurrentTextColor());
  }
  @Test public void safeModeRefusesPreviewAndKeepsCommittedPointer()throws Exception{
    installed("first","#112233");String old=CobraVisualTheme.readPointer(app).toString();activity.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));CobraPresentationSafety.offerVisual(activity,staged("second","#223344"));
    assertFalse(CobraPresentationSafety.isPreviewing(activity));assertEquals(old,CobraVisualTheme.readPointer(app).toString());
  }
  @Test public void lateAsyncPreviewAfterStopIsDiscardedWithoutShowingUi()throws Exception{
    installed("committed","#112233");CobraVisualTheme pending=staged("late","#223344");CobraPresentationSafety.onStop(activity);CobraPresentationSafety.offerVisual(activity,pending);drain();
    assertFalse(CobraPresentationSafety.isPreviewing(activity));assertFalse(pending.directory.exists());assertEquals("committed",CobraVisualTheme.load(app).id);
    CobraPresentationSafety.onResume(activity);assertFalse(CobraPresentationSafety.isPreviewing(activity));
  }
  @Test public void repeatedAbandonedPreviewsAreRemovedButKeptThemeSurvives()throws Exception{
    CobraVisualTheme kept=installed("kept","#112233");for(int i=0;i<8;i++){CobraVisualTheme candidate=staged("discard"+i,"#223344");CobraPresentationSafety.offerVisual(activity,candidate);CobraPresentationSafety.cancel(activity,true);drain();assertFalse(candidate.directory.exists());}
    assertTrue(kept.directory.isDirectory());assertEquals("kept",CobraVisualTheme.load(app).id);
  }
  @Test public void nativeKeepPromptIgnoresMaliciousThemeText()throws Exception{
    CobraPresentationSafety.offerVisual(activity,staged("unreadable","#000000"));AlertDialog prompt=ShadowAlertDialog.getLatestAlertDialog();Button keep=prompt.getButton(AlertDialog.BUTTON_POSITIVE);
    assertEquals("Keep Theme",keep.getText().toString());assertTrue(keep.isEnabled());assertNotEquals(Color.BLACK,keep.getCurrentTextColor());assertTrue(prompt.isShowing());
  }
  @Test public void processReloadCannotLoadAnUnkeptVisualTheme()throws Exception{
    installed("committed","#112233");CobraPresentationSafety.offerVisual(activity,staged("preview","#223344"));assertEquals("preview",new CobraVisualRenderer(activity).displayName());
    assertEquals("committed",CobraVisualTheme.load(app).id); // Cold-process loader reads committed state only.
  }
  @Test public void abandonedVisualCleanupKeepsBothCommittedGenerations()throws Exception{
    CobraVisualTheme first=installed("first","#112233"),second=installed("second","#223344"),pending=staged("third","#334455");CobraVisualTheme.discardAbandonedPreviews(app);
    assertTrue(first.directory.isDirectory());assertTrue(second.directory.isDirectory());assertFalse(pending.directory.exists());assertEquals("second",CobraVisualTheme.load(app).id);
  }
  @Test public void malformedPreviewCannotChangeCurrentTheme()throws Exception{
    installed("first","#112233");JSONObject bad=manifest("bad","#223344");bad.put("player_owner","theme");String old=CobraVisualTheme.readPointer(app).toString();reject(()->CobraVisualTheme.stagePreview(app,new ByteArrayInputStream(zip(bad))));assertEquals(old,CobraVisualTheme.readPointer(app).toString());
  }
  @Test public void legacyPreviewLeavesExternalPackageUntouched()throws Exception{
    File original=CobraPresentationSafety.legacyDirectory(app),staged=CobraPresentationSafety.stageLegacy(app,legacy("#123456"));String saved=CobraPresentationSafety.state(app).toString();
    CobraPresentationSafety.offerLegacy(activity,staged);assertEquals(staged,CobraPresentationSafety.legacyDirectory(activity));assertEquals(saved,CobraPresentationSafety.state(app).toString());
    CobraPresentationSafety.cancel(activity,true);assertEquals(original,CobraPresentationSafety.legacyDirectory(activity));assertEquals(saved,CobraPresentationSafety.state(app).toString());
  }
  @Test public void legacyKeepSurvivesCacheReloadAndStillPreservesExternalPath()throws Exception{
    File original=CobraPresentationSafety.legacyDirectory(app),staged=CobraPresentationSafety.stageLegacy(app,legacy("#123456"));CobraPresentationSafety.offerLegacy(activity,staged);ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_POSITIVE).performClick();drain();clearStatic("stateCache");
    assertEquals(staged,CobraPresentationSafety.legacyDirectory(activity));assertNotEquals(original,staged);assertTrue(staged.isDirectory());
  }
  @Test public void legacyUnsafePathAndProtectedOwnerAreRejected()throws Exception{
    Map<String,byte[]> path=legacy("#123456");path.put(CobraVisualTheme.PREFIX+"../escape",new byte[]{1});reject(()->CobraPresentationSafety.stageLegacy(app,path));
    Map<String,byte[]> contract=legacy("#123456");String key=CobraVisualTheme.PREFIX+"resources/cobra-ui.json";JSONObject ui=new JSONObject(new String(contract.get(key),StandardCharsets.UTF_8));ui.getJSONObject("protected_contracts").put("renderer","theme");contract.put(key,ui.toString().getBytes(StandardCharsets.UTF_8));reject(()->CobraPresentationSafety.stageLegacy(app,contract));
  }
  @Test public void emergencyRestoreRetainsThemesAndPlaybackPreferences()throws Exception{
    CobraVisualTheme saved=installed("saved","#123456");File legacy=CobraPresentationSafety.stageLegacy(app,legacy("#123456"));app.getSharedPreferences("infinity_cobra_live",0).edit().putString("sources","kept").putBoolean("timeshift",true).commit();
    CobraPresentationSafety.offerVisual(activity,staged("preview","#223344"));CobraPresentationSafety.restoreBuiltIn(activity,null);drain();
    assertTrue(saved.directory.isDirectory());assertTrue(legacy.isDirectory());assertNull(CobraPresentationSafety.legacyDirectory(activity));assertEquals("builtin",new CobraVisualRenderer(activity).displayName());
    assertEquals("kept",app.getSharedPreferences("infinity_cobra_live",0).getString("sources",""));assertTrue(app.getSharedPreferences("infinity_cobra_live",0).getBoolean("timeshift",false));
  }
  @Test public void emergencyRestoreCannotBeUndoneByOldPreviewTimer()throws Exception{
    installed("saved","#123456");CobraPresentationSafety.offerVisual(activity,staged("preview","#223344"));CobraPresentationSafety.Lease old=lease();CobraPresentationSafety.restoreBuiltIn(activity,null);drain();old.timeout.run();
    assertEquals("builtin",new CobraVisualRenderer(activity).displayName());assertEquals("",CobraVisualTheme.readPointer(app).optString("active"));
  }
  @Test public void keptLegacyThemeRemainsSelectableAfterBuiltInRestore()throws Exception{
    File legacy=CobraPresentationSafety.stageLegacy(app,legacy("#123456"));CobraPresentationSafety.offerLegacy(activity,legacy);ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_POSITIVE).performClick();drain();
    assertTrue(new CobraVisualRenderer(activity).installed());assertEquals("Installed Cobra UI package",new CobraVisualRenderer(activity).displayName());
    new CobraVisualRenderer(activity).restoreBuiltIn(activity,null);drain();assertFalse(new CobraVisualRenderer(activity).installed());assertTrue(CobraPresentationSafety.hasPrevious(activity));
    CobraPresentationSafety.previewPrevious(activity);drain();assertTrue(CobraPresentationSafety.isPreviewing(activity));assertEquals(legacy,CobraPresentationSafety.legacyDirectory(activity));
    CobraPresentationSafety.cancel(activity,true);assertNull(CobraPresentationSafety.legacyDirectory(activity));assertTrue(legacy.isDirectory());
  }
  @Test public void existingVisualThemeSelectionAlsoPreviewsWithoutChangingPointer()throws Exception{
    installed("first","#112233");installed("second","#223344");CobraVisualTheme.reset(app);CobraVisualRenderer.publish(CobraVisualTheme.builtin(),"reset");drain();String prior=CobraVisualTheme.readPointer(app).toString();
    CobraPresentationSafety.previewPrevious(activity);drain();assertEquals("second",new CobraVisualRenderer(activity).displayName());assertEquals(prior,CobraVisualTheme.readPointer(app).toString());
    CobraPresentationSafety.cancel(activity,true);assertEquals(prior,CobraVisualTheme.readPointer(app).toString());assertEquals("builtin",new CobraVisualRenderer(activity).displayName());
  }
  @Test public void previousInstalledThemeIsExactButUncommittedUntilNativeKeep()throws Exception{
    CobraVisualTheme original=installed("hm-test","#123456");String generation=original.directory.getName();
    CobraPresentationSafety.restoreBuiltIn(activity,null);drain();
    assertEquals("builtin",CobraVisualRenderer.active.id);assertEquals("",CobraVisualTheme.readPointer(app).optString("active"));assertEquals(generation,CobraVisualTheme.readPointer(app).optString("previous"));
    CobraPresentationSafety.previewPrevious(activity);drain();CobraVisualRenderer renderer=new CobraVisualRenderer(activity);
    assertTrue(CobraPresentationSafety.isPreviewing(activity));assertEquals("hm-test",renderer.displayName());assertEquals(Color.parseColor("#123456"),renderer.color("palette.accent",Color.BLUE));
    assertEquals("builtin",CobraVisualRenderer.active.id);assertEquals("",CobraVisualTheme.readPointer(app).optString("active"));assertEquals("builtin",CobraVisualTheme.load(app).id);
    AlertDialog prompt=ShadowAlertDialog.getLatestAlertDialog();assertTrue(prompt.isShowing());assertEquals("Keep Theme",prompt.getButton(AlertDialog.BUTTON_POSITIVE).getText().toString());assertTrue(prompt.getButton(AlertDialog.BUTTON_POSITIVE).performClick());drain();
    assertFalse(CobraPresentationSafety.isPreviewing(activity));assertEquals("hm-test",CobraVisualRenderer.active.id);assertEquals(generation,CobraVisualTheme.readPointer(app).optString("active"));
    CobraVisualTheme cold=CobraVisualTheme.load(app);assertEquals("hm-test",cold.id);assertEquals(generation,cold.directory.getName());assertEquals(original.data.toString(),cold.data.toString());
    assertEquals(Color.parseColor("#123456"),renderer.color("palette.accent",Color.BLUE));
  }
}
