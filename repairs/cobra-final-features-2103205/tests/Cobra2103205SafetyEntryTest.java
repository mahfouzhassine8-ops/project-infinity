package com.projectinfinity.kodi;

import android.app.*;
import android.content.Intent;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.lang.reflect.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;

/** Actual chooser factories and launch intents; never runs Kodi startup or a device. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205SafetyEntryTest {
  Cobra2103204EntryThemeTest helper;Splash a;
  @Before public void before()throws Exception{
    helper=new Cobra2103204EntryThemeTest();helper.before();a=helper.a;
    CobraPresentationSafety.cancel(a,false);CobraVisualTheme.deleteTree(CobraVisualTheme.store(a));CobraVisualTheme.deleteTree(CobraPresentationSafety.root(a));
    new Cobra2103205SafetyTest().clearStatic("stateCache");new Cobra2103205SafetyTest().clearStatic("initialized");
  }
  @After public void after(){helper.after();}
  Object call(String name,Class<?>[] types,Object...args)throws Exception{Method m=Splash.class.getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(a,args);}
  void draw(String name)throws Exception{
    View decor=a.getWindow().getDecorView();helper.controller.visible();decor.measure(View.MeasureSpec.makeMeasureSpec(412,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(915,View.MeasureSpec.EXACTLY));decor.layout(0,0,412,915);
    Bitmap bitmap=Bitmap.createBitmap(412,915,Bitmap.Config.ARGB_8888);decor.draw(new Canvas(bitmap));File directory=new File(System.getProperty("cobra.evidence","."));assertTrue(directory.isDirectory()||directory.mkdirs());try(FileOutputStream out=new FileOutputStream(new File(directory,"cobra205-safety-"+name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();
  }
  int countTag(View v,String tag){int n=tag.equals(v.getTag())?1:0;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)n+=countTag(((ViewGroup)v).getChildAt(i),tag);return n;}
  @Test public void builtInChooserKeepsExactlyTwoOriginalCardGears()throws Exception{
    helper.show("light",412,915,"safety-baseline");helper.controls();int gears=0;for(TextView v:helper.texts)if("⚙".contentEquals(v.getText())){assertTrue(v.getParent() instanceof FrameLayout);gears++;}assertEquals(2,gears);
    assertNull(a.findViewById(android.R.id.content).findViewWithTag("cobra-visual-theme-controls-chooser"));
  }
  @Test public void importedBlankRootCannotHideIndependentSingleCobraGear()throws Exception{
    Cobra2103205SafetyTest factory=new Cobra2103205SafetyTest();JSONObject json=factory.manifest("blank","#000000");json.getJSONObject("base").getJSONObject("styles").put("all.panel",new JSONObject().put("alpha",0));
    CobraVisualTheme theme=CobraVisualTheme.install(a,new ByteArrayInputStream(factory.zip(json)));CobraVisualRenderer.publish(theme,"test");Shadows.shadowOf(Looper.getMainLooper()).idle();
    call("showInfinityExperienceChooser",new Class<?>[]{});draw("blank-theme-recovery");ViewGroup host=a.findViewById(android.R.id.content);View gear=host.findViewWithTag("experience-settings-cobra");
    assertNotNull(gear);assertSame(host,gear.getParent());assertEquals(1,countTag(host,"experience-settings-cobra"));assertEquals(1f,gear.getAlpha(),0f);assertTrue(gear.getWidth()>=44&&gear.getHeight()>=44);assertTrue(gear.performClick());
    ListView list=ShadowAlertDialog.getLatestAlertDialog().getListView();assertEquals("Cobra Recovery",list.getAdapter().getItem(3));
  }
  @Test public void cobraOptionsRetainOriginalActionsBeforeRecovery()throws Exception{
    call("showExperienceCardSettings",new Class<?>[]{String.class},"live");ListView list=ShadowAlertDialog.getLatestAlertDialog().getListView();
    assertEquals(4,list.getAdapter().getCount());assertEquals("Remember & launch Cobra",list.getAdapter().getItem(0));assertEquals("Launch Cobra just this time",list.getAdapter().getItem(1));assertEquals("Ask every time",list.getAdapter().getItem(2));assertEquals("Cobra Recovery",list.getAdapter().getItem(3));
  }
  @Test public void legacyBlackOnBlackPaletteKeepsOriginalGearLocationAndReadableNativeInk()throws Exception{
    JSONObject json=new JSONObject().put("schema",1).put("scope","infinity-experience-chooser").put("minimum_bridge",1).put("copy",new JSONObject()).put("palette",new JSONObject().put("background","#000000").put("text","#000000").put("cobra_top","#000000").put("cobra_bottom","#000000").put("cobra_border","#000000"));
    Class<?> type=Class.forName("com.projectinfinity.kodi.Splash$ExperienceTheme");Constructor<?> constructor=type.getDeclaredConstructor(JSONObject.class);constructor.setAccessible(true);Object theme=constructor.newInstance(json);
    call("showStyledInfinityExperienceChooser",new Class<?>[]{type},theme);draw("legacy-contrast-recovery");ViewGroup host=a.findViewById(android.R.id.content);TextView gear=host.findViewWithTag("experience-settings-cobra");
    assertNotNull(gear);assertNotSame(host,gear.getParent());assertEquals(1,countTag(host,"experience-settings-cobra"));assertEquals(0xfff7faff,gear.getCurrentTextColor());assertEquals("⚙",gear.getText().toString());assertTrue(gear.getWidth()>=44&&gear.getHeight()>=44);assertTrue(gear.performClick());assertEquals("Cobra Recovery",ShadowAlertDialog.getLatestAlertDialog().getListView().getAdapter().getItem(3));
  }
  @Test public void infinityOptionsKeepThreeActionsAndLightBluePresentation()throws Exception{
    a.getSharedPreferences("infinity_cobra_live",0).edit().putString("cobra_appearance_mode","light").commit();call("showExperienceCardSettings",new Class<?>[]{String.class},"infinity");Shadows.shadowOf(Looper.getMainLooper()).idle();AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();
    assertEquals(3,dialog.getListView().getAdapter().getCount());assertEquals(0xff145fdf,dialog.getButton(AlertDialog.BUTTON_NEGATIVE).getCurrentTextColor());
  }
  @Test public void explicitCobraEntryGetsFreshWelcomeTokenAndClearsStaleSafeFlag()throws Exception{
    a.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true).putExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN,"old"));call("launchInfinityExperience",new Class<?>[]{String.class},"live");Intent started=Shadows.shadowOf(a).getNextStartedActivity();
    assertFalse(started.getBooleanExtra(CobraPresentationSafety.EXTRA_SAFE,false));assertNotNull(started.getStringExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN));assertNotEquals("old",started.getStringExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN));
  }
  @Test public void automaticDefaultLaunchHasNoWelcomeTokenOrStaleSafeFlag()throws Exception{
    a.setIntent(new Intent(Intent.ACTION_MAIN).putExtra(CobraPresentationSafety.EXTRA_SAFE,true).putExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN,"old"));a.getSharedPreferences("infinity_experience",0).edit().putString("default","live").commit();call("startXBMC",new Class<?>[]{});Intent started=Shadows.shadowOf(a).getNextStartedActivity();
    assertEquals("com.projectinfinity.kodi.InfinityLiveActivity",started.getComponent().getClassName());assertFalse(started.hasExtra(CobraPresentationSafety.EXTRA_ENTRY_TOKEN));assertFalse(started.hasExtra(CobraPresentationSafety.EXTRA_SAFE));
  }
  @Test public void recoverySafeStartSetsOnlyTemporaryIntentAndPreservesPreferences()throws Exception{
    a.getSharedPreferences("infinity_experience",0).edit().putString("default","infinity").commit();call("showCobraRecovery",new Class<?>[]{});ListView list=ShadowAlertDialog.getLatestAlertDialog().getListView();assertEquals("Restore Built-in Theme",list.getAdapter().getItem(1));list.performItemClick(null,0,0);Shadows.shadowOf(Looper.getMainLooper()).idle();Intent started=Shadows.shadowOf(a).getNextStartedActivity();
    assertTrue(started.getBooleanExtra(CobraPresentationSafety.EXTRA_SAFE,false));assertEquals("infinity",a.getSharedPreferences("infinity_experience",0).getString("default",""));
  }
}
