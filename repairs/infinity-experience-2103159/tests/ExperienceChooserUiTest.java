package com.projectinfinity.kodi;

import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.IdentityHashMap;
import java.util.Map;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;

/** Production Splash chooser rendering with a real installed JSON file.
 * No Kodi native startup, physical Fold panel, GPU or installation claim.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class ExperienceChooserUiTest {
  static Method chooser;
  @BeforeClass public static void reflect()throws Exception{chooser=Splash.class.getDeclaredMethod("showInfinityExperienceChooser");chooser.setAccessible(true);}
  final Map<Splash,ActivityController<Splash>> controllers=new IdentityHashMap<>();
  Splash activity()throws Exception{
    ActivityController<Splash> controller=Robolectric.buildActivity(Splash.class);
    Splash a=controller.get();controllers.put(a,controller);return a;
  }
  void layout(Splash a,int width,int height){
    View decor=a.getWindow().getDecorView();
    // Run 35275938034 drew an unattached DecorView: Android 34 needs a ViewRootImpl.
    // Match the locked Cobra fixture: build the real UI, then attach its window.
    // Do NOT call setup()/onCreate(): native startup is outside this rendering test.
    ActivityController<Splash> controller=controllers.get(a);
    assertNotNull("Splash must belong to this test fixture",controller);
    if(!decor.isAttachedToWindow())controller.visible();
    assertTrue("Chooser window must be attached before layout",decor.isAttachedToWindow());
    decor.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
    decor.layout(0,0,width,height);
  }
  @After public void closeWindows(){
    AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();
    if(dialog!=null&&dialog.isShowing())dialog.dismiss();
    for(ActivityController<Splash> controller:controllers.values())controller.destroy();
    controllers.clear();
  }
  File themeFile(Splash a){return new File(a.getExternalFilesDir(null),".kodi/addons/script.infinity.cobra.theme/resources/experience-chooser.json");}
  void installTheme(Splash a)throws Exception{
    File file=themeFile(a);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());byte[] data=Files.readAllBytes(Paths.get(System.getProperty("experience.theme.source")));
    try(FileOutputStream out=new FileOutputStream(file)){out.write(data);}
  }
  void show(Splash a,boolean themed,int width,int height)throws Exception{
    File f=themeFile(a);if(f.exists())assertTrue(f.delete());if(themed)installTheme(a);chooser.invoke(a);
    layout(a,width,height);
  }
  View tag(Splash a,String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  List<String> texts(View root){ArrayList<String> out=new ArrayList<>();if(root instanceof TextView)out.add(((TextView)root).getText().toString());if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++)out.addAll(texts(((ViewGroup)root).getChildAt(i)));return out;}
  boolean contains(List<String> values,String text){for(String value:values)if(value.contains(text))return true;return false;}
  void shot(Splash a,String name)throws Exception{
    View view=a.getWindow().getDecorView();Bitmap bitmap=Bitmap.createBitmap(Math.max(1,view.getWidth()),Math.max(1,view.getHeight()),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));File root=new File(System.getProperty("cobra.evidence"));assertTrue(root.isDirectory()||root.mkdirs());try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();
  }
  @Test public void approvedCopyAndHmRenderWithoutRemovedWording()throws Exception{
    Splash a=activity();show(a,true,412,915);List<String> copy=texts(a.getWindow().getDecorView());
    assertNotNull(tag(a,"experience-themed-root"));assertNotNull(tag(a,"experience-initials"));assertTrue(copy.contains("HM"));assertTrue(copy.contains("Choose Your Experience"));assertTrue(copy.contains("BEYOND ENTERTAINMENT"));
    assertTrue(copy.contains("YOUR HOME FOR MOVIES, SHOWS AND MORE"));assertTrue(copy.contains("FOCUSED. FAST. POWERFUL."));
    assertFalse(contains(copy,"2-IN-1"));assertFalse(contains(copy,"Two separate environments"));assertFalse(contains(copy,"Live TV"));shot(a,"experience-approved-412x915");
  }
  @Test public void cardSettingsAndLaunchOwnershipRemainFunctional()throws Exception{
    Splash settings=activity();show(settings,true,412,915);View gear=tag(settings,"experience-settings-infinity");assertNotNull(gear);assertTrue(gear.performClick());AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();assertNotNull(dialog);assertEquals("Infinity options",Shadows.shadowOf(dialog).getTitle().toString());
    Splash infinity=activity();show(infinity,true,412,915);assertTrue(tag(infinity,"experience-card-infinity").performClick());Intent next=Shadows.shadowOf(infinity).getNextStartedActivity();assertNotNull(next);assertEquals("com.projectinfinity.kodi.Main",next.getComponent().getClassName());
    Splash cobra=activity();show(cobra,true,412,915);assertTrue(tag(cobra,"experience-card-cobra").performClick());Intent live=Shadows.shadowOf(cobra).getNextStartedActivity();assertNotNull(live);assertEquals("com.projectinfinity.kodi.InfinityLiveActivity",live.getComponent().getClassName());assertEquals("cobra",live.getStringExtra("infinity_live_profile"));
  }
  @Test public void cobraGearExposesThemeRecoveryWithoutEnteringCobra()throws Exception{
    Splash a=activity();show(a,true,412,915);View gear=tag(a,"experience-settings-cobra");assertNotNull(gear);assertTrue(gear.performClick());
    AlertDialog recovery=ShadowAlertDialog.getLatestAlertDialog();assertNotNull(recovery);assertEquals("Cobra recovery",Shadows.shadowOf(recovery).getTitle().toString());
    assertTrue(texts(recovery.getListView()).contains("Restore Built-in Theme"));
  }

  @Test public void corruptThemeFallsBackWithoutChangingLegacyChooser()throws Exception{
    Splash a=activity();File file=themeFile(a);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());try(FileOutputStream out=new FileOutputStream(file)){out.write("{not json".getBytes("UTF-8"));}chooser.invoke(a);layout(a,412,915);List<String> copy=texts(a.getWindow().getDecorView());assertNull(tag(a,"experience-themed-root"));assertTrue(contains(copy,"INFINITY 2-IN-1"));assertTrue(contains(copy,"Two separate environments"));
  }
  @Test @Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w320dp-h720dp-port-mdpi") public void narrowDisplayStacksCardsAndKeepsControlsReachable()throws Exception{
    Splash a=activity();show(a,true,320,720);View infinity=tag(a,"experience-card-infinity"),cobra=tag(a,"experience-card-cobra");assertNotNull(infinity);assertNotNull(cobra);assertTrue("stacked",cobra.getTop()>=infinity.getBottom());assertTrue(infinity.getHeight()>=180);assertTrue(cobra.getHeight()>=180);assertNotNull(tag(a,"experience-settings-infinity"));assertNotNull(tag(a,"experience-settings-cobra"));shot(a,"experience-cover-320x720");
  }
  @Test @Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w960dp-h540dp-land-mdpi") public void landscapeKeepsBalancedSideBySideCards()throws Exception{
    Splash a=activity();show(a,true,960,540);View infinity=tag(a,"experience-card-infinity"),cobra=tag(a,"experience-card-cobra");assertNotNull(infinity);assertNotNull(cobra);assertEquals("same row",infinity.getTop(),cobra.getTop());assertTrue(cobra.getLeft()>infinity.getLeft());assertTrue(infinity.getWidth()>300&&cobra.getWidth()>300);shot(a,"experience-landscape-960x540");
  }
  @Test public void oversizedThemeFallsBackInsteadOfReadingUnboundedData()throws Exception{
    Splash a=activity();File file=themeFile(a);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());byte[] large=new byte[65537];java.util.Arrays.fill(large,(byte)' ');try(FileOutputStream out=new FileOutputStream(file)){out.write(large);}chooser.invoke(a);assertNull(tag(a,"experience-themed-root"));
  }
}
