package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** 2103159 presentation-only acceptance for the Cobra drawer/settings/power cleanup. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103159UiTest {
  final CobraNavigationUiTest ui=new CobraNavigationUiTest();
  @Before public void clock(){ui.clock();}
  static String norm(CharSequence value){return value==null?"":value.toString().trim().replaceAll("\\s+"," ");}
  static View exact(View root,String wanted){
    if(root instanceof TextView&&norm(((TextView)root).getText()).equals(wanted))return root;
    if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++){View found=exact(((ViewGroup)root).getChildAt(i),wanted);if(found!=null)return found;}
    return null;
  }
  static View contains(View root,String wanted){
    if(root instanceof TextView&&norm(((TextView)root).getText()).toUpperCase(Locale.US).contains(wanted.toUpperCase(Locale.US)))return root;
    if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++){View found=contains(((ViewGroup)root).getChildAt(i),wanted);if(found!=null)return found;}
    return null;
  }
  static View clickableAncestor(View child,View boundary){
    View current=child;
    while(current!=null&&current!=boundary){if(current.isClickable())return current;android.view.ViewParent parent=current.getParent();current=parent instanceof View?(View)parent:null;}
    return null;
  }
  void shot(InfinityLiveActivity a,String name)throws Exception{
    View view=a.getWindow().getDecorView();Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));
    File root=new File(System.getProperty("cobra.evidence"));assertTrue(root.isDirectory()||root.mkdirs());
    try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();
  }
  @Test(timeout=90000) public void drawerHasPowerOnlyAndHealthLivesInSettings()throws Exception{
    InfinityLiveActivity a=ui.fixture(64);try{
      CobraNavigationUiTest.call(a,"toggleCobraDrawer");ui.measure(a,412,915);View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(drawer);
      assertNotNull(exact(drawer,"View"));assertNotNull(exact(drawer,"Settings"));assertNotNull(exact(drawer,"Power"));
      assertNull("Health Center must not remain a main-drawer destination",contains(drawer,"Health Center"));
      assertNull("Direct Infinity drawer handoff must be removed",exact(drawer,"∞ Infinity"));shot(a,"cobra-2103159-drawer-clean");
      View settings=clickableAncestor(exact(drawer,"Settings"),drawer);assertNotNull(settings);assertTrue(settings.performClick());ui.measure(a,412,915);
      View health=contains(a.getWindow().getDecorView(),"Health Center");
      assertNotNull("Health Center must be available from Cobra Settings",health);
      View healthButton=clickableAncestor(health,a.getWindow().getDecorView());assertNotNull("Health Center must have a real click action",healthButton);
      healthButton.requestRectangleOnScreen(new Rect(0,0,healthButton.getWidth(),healthButton.getHeight()),true);ui.measure(a,412,915);
      Rect visible=new Rect();assertTrue("Health Center must be scroll-reachable",healthButton.getGlobalVisibleRect(visible));assertTrue(visible.height()>0);shot(a,"cobra-2103159-settings-health");
      assertTrue(healthButton.performClick());ui.measure(a,412,915);
      View healthSheet=(View)CobraNavigationUiTest.get(a,"mCobraActionSheet");assertNotNull("Settings button must open Health Center",healthSheet);
      assertEquals("health-center",CobraNavigationUiTest.get(a,"mCobraSheetKind"));assertNotNull(healthSheet.findViewWithTag("cobra-health-summary"));shot(a,"cobra-2103159-health-from-settings");
    }finally{ui.clean(a);}
  }
  @Test(timeout=90000) public void powerIsTheSingleHandoffAndExitLabelIsPlain()throws Exception{
    InfinityLiveActivity a=ui.fixture(32);try{
      CobraNavigationUiTest.call(a,"showCobraPowerMenu");ui.measure(a,412,915);View sheet=a.getWindow().getDecorView().findViewWithTag("cobra_power_menu");assertNotNull(sheet);
      assertNotNull(contains(sheet,"Switch to Infinity"));assertNotNull(contains(sheet,"Exit"));assertNotNull(exact(sheet,"Cancel"));assertNull(contains(sheet,"Exit Infinity"));shot(a,"cobra-2103159-power");
    }finally{ui.clean(a);}
  }
}
