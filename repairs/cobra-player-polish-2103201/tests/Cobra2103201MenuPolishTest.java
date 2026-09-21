package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Matrix;
import android.graphics.RectF;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.TextureView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real existing menu/button actions and TextureView geometry; no physical GPU claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w1600dp-h900dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103201MenuPolishTest {
  Cobra2103199DisplayRegressionTest fixture;
  Cobra2103199DisplayRegressionTest.Controlled controlled;
  InfinityLiveActivity a;
  TextureView texture;
  @Before public void before()throws Exception {
    fixture=new Cobra2103199DisplayRegressionTest();fixture.before();a=fixture.a;
    controlled=fixture.new Controlled();texture=fixture.texture(1600,900);
    fixture.bind(controlled,fixture.channel(0),texture,true);
    call("cobraBuildPlayerChrome");fixture.ui.measure(a,1600,900);
  }
  @After public void after()throws Exception {if(fixture!=null)fixture.after();}
  Object call(String n,Object...args)throws Exception{return CobraNavigationUiTest.call(a,n,args);}
  View root(){return a.getWindow().getDecorView();}
  int count(View v,String label){
    int result=v instanceof TextView&&label.contentEquals(((TextView)v).getText())?1:0;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)result+=count(g.getChildAt(i),label);}
    return result;
  }
  View tagged(String tag){return root().findViewWithTag(tag);}
  static void capture(InfinityLiveActivity a,CobraNavigationUiTest ui,String name,int width,int height)throws Exception {
    ui.frames(40);ui.measure(a,width,height);
    View view=a.getWindow().getDecorView();
    assertEquals(width,view.getWidth());assertEquals(height,view.getHeight());
    File dir=new File(System.getProperty("cobra.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
    Bitmap image=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);
    view.draw(new Canvas(image));
    try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,out));}
    image.recycle();
  }
  @Test public void optionsKeepUniqueFunctionsAndRemoveOnlyRepeatedAspectRoute()throws Exception {
    View options=tagged("cobra_player_options_anchor");assertNotNull(options);assertTrue(options.performClick());
    fixture.ui.measure(a,1600,900);
    for(String label:new String[]{"Channel playback","Health Center","Record now","Audio & subtitles","Cast / Route","Manage sources","Close player"})assertEquals(label,1,count(root(),label));
    assertEquals(0,count(root(),"Aspect / Display"));
    assertNotNull(tagged("cobra_player_aspect_anchor"));
    assertFalse(controlled.writes.contains("release"));assertFalse(controlled.writes.contains("prepare"));
    capture(a,fixture.ui,"cobra201-options-1600x900",1600,900);
  }
  @Test public void dedicatedAspectButtonStillChangesActualVideoRectangle()throws Exception {
    View display=tagged("cobra_player_aspect_anchor");assertNotNull(display);assertTrue(display.performClick());
    fixture.ui.measure(a,1600,900);
    assertEquals("channel-aspect",CobraNavigationUiTest.get(a,"mCobraSheetKind"));
    assertNotNull(tagged("cobra-channel-aspect:12"));
    View fourThree=tagged("cobra-channel-aspect:3");assertNotNull(fourThree);assertTrue(fourThree.performClick());
    RectF mapped=new RectF(0,0,texture.getWidth(),texture.getHeight());texture.getTransform(new Matrix()).mapRect(mapped);
    assertEquals(4f/3f,mapped.width()/mapped.height(),.001f);
    assertEquals(texture.getWidth()/2f,mapped.centerX(),.02f);assertEquals(texture.getHeight()/2f,mapped.centerY(),.02f);
    assertSame(controlled.player,CobraNavigationUiTest.get(a,"mPlayer"));
    assertFalse(controlled.writes.contains("seekTo"));assertFalse(controlled.writes.contains("release"));
  }
  @Test public void channelPreferencesRemainDistinctAndReachableAfterCleanup()throws Exception {
    assertTrue(tagged("cobra_player_options_anchor").performClick());fixture.ui.measure(a,1600,900);
    View channel=tagged("cobra-player-channel-preferences");assertNotNull(channel);assertTrue(channel.performClick());
    fixture.ui.measure(a,1600,900);
    assertEquals(1,count(root(),"Preferred subtitles"));assertEquals(0,count(root(),"Subtitles"));
    for(String tag:new String[]{"cobra-channel-aspect","cobra-channel-audio","cobra-channel-subtitles","cobra-channel-fallback","cobra-channel-recovery","cobra-channel-reset"})assertNotNull(tag,tagged(tag));
    capture(a,fixture.ui,"cobra201-channel-preferences-1600x900",1600,900);
    View subtitles=tagged("cobra-channel-subtitles");assertTrue(subtitles.performClick());fixture.ui.measure(a,1600,900);
    for(String value:new String[]{"inherit","off","auto","en"})assertNotNull(value,tagged("cobra-channel-language:"+value));
  }
}
