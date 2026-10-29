package com.projectinfinity.kodi;

import android.content.res.AssetManager;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.AdaptiveIconDrawable;
import android.graphics.drawable.Drawable;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.ResourcesMode;

/** Actual API35 framework inflation of compiled resources, no app classes.
 * APK paths are source-bound inputs; optional negative is signed430 failure.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,manifest=Config.NONE)
@ResourcesMode(ResourcesMode.Mode.BINARY)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class InfinityLauncherResourceInflationTest {
  private static final int[] IDS={0x7f080000,0x7f080001};
  private static final int[] DENSITIES={0,420};
  private static Path output()throws Exception {
    Path p=Paths.get(System.getProperty("icon.output", "target/icon-inflation"));Files.createDirectories(p);return p;
  }
  private static String required(String name){
    String v=System.getProperty(name);assertNotNull("Source-bound APK property required: "+name,v);
    assertTrue("APK input must exist: "+name,Files.isRegularFile(Paths.get(v)));return v;
  }
  private static AssetManager assets(String apk)throws Exception {
    AssetManager a=new AssetManager();Method add=AssetManager.class.getDeclaredMethod("addAssetPath",String.class);
    add.setAccessible(true);int cookie=(Integer)add.invoke(a,apk);assertTrue("Host APK AssetManager loader must succeed",cookie>0);return a;
  }
  private static Resources resources(AssetManager assets,boolean night){
    Configuration c=new Configuration(Resources.getSystem().getConfiguration());
    c.uiMode=Configuration.UI_MODE_TYPE_NORMAL|(night?Configuration.UI_MODE_NIGHT_YES:Configuration.UI_MODE_NIGHT_NO);
    DisplayMetrics dm=new DisplayMetrics();dm.setTo(Resources.getSystem().getDisplayMetrics());return new Resources(assets,dm,c);
  }
  private static Drawable drawable(Resources r,int id,int density){return density==0?r.getDrawable(id,null):r.getDrawableForDensity(id,density,null);}
  private static Bitmap render(Drawable d,String label)throws Exception {
    assertNotNull(label,d);assertTrue("Actual adaptive drawable required: "+label,d instanceof AdaptiveIconDrawable);
    Bitmap b=Bitmap.createBitmap(192,192,Bitmap.Config.ARGB_8888);d.setBounds(0,0,192,192);d.draw(new Canvas(b));
    try(OutputStream out=Files.newOutputStream(output().resolve(label+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}
    System.out.println("ICON_INFLATION "+label+" class="+d.getClass().getName()+" intrinsic="+d.getIntrinsicWidth()+"x"+d.getIntrinsicHeight());return b;
  }
  private static int[] pixels(Bitmap b){int[] p=new int[192*192];b.getPixels(p,0,192,0,0,192,192);return p;}
  private static void lightColors(Bitmap image){
    int white=0,dark=0,cyan=0,visible=0;
    for(int c:pixels(image)){
      int a=c>>>24,r=(c>>>16)&255,g=(c>>>8)&255,b=c&255;if(a<200)continue;visible++;
      if(r>=240&&g>=240&&b>=240)white++;if(r<=32&&g<=32&&b<=32)dark++;
      if(g>80&&b>80&&g>r*1.7&&b>r*1.7)cyan++;
    }
    assertTrue("White background visible",white>visible/2);assertTrue("Original black emblem visible",dark>200);assertEquals("No cyan emblem in light variant",0,cyan);
  }
  private static boolean containsZeroResource(Throwable e){
    for(Throwable t=e;t!=null;t=t.getCause())if(String.valueOf(t.getMessage()).contains("Resource ID #0x0"))return true;return false;
  }
  @Test public void actualCompiledLauncherResourcesInflateAcrossThemesAndDensityOverride()throws Exception {
    render(Resources.getSystem().getDrawable(android.R.drawable.sym_def_app_icon,null),"framework-control");
    Map<String,int[]> original=new HashMap<>();String baseline=required("icon.baseline.apk"),candidate=required("icon.candidate.apk");
    for(String apk:new String[]{baseline,candidate}){
      boolean isBaseline=apk.equals(baseline);String version=isBaseline?"baseline":"candidate";AssetManager a=assets(apk);
      try{
        for(boolean night:new boolean[]{false,true})for(int density:DENSITIES){
          Resources r=resources(a,night);
          for(int id:IDS){
            String suffix=(night?"night":"day")+"-"+Integer.toHexString(id)+"-density"+density;TypedValue value=new TypedValue();r.getValue(id,value,true);
            System.out.println("ICON_VALUE "+version+"-"+suffix+" "+value);
            String expected=night||isBaseline?(id==IDS[0]?"res/IG.xml":"res/6H.xml"):"res/infinity_launcher_light_v33.xml";
            assertEquals("Selected compiled resource path",expected,String.valueOf(value.string));Bitmap b=render(drawable(r,id,density),version+"-"+suffix);
            if(isBaseline)original.put(suffix,pixels(b));else if(night)assertArrayEquals("Dark mode exact rendered original",original.get(suffix),pixels(b));else lightColors(b);
          }
        }
      }finally{a.close();}
    }
    String negative=System.getProperty("icon.negative.apk");
    if(negative!=null){
      assertTrue(Files.isRegularFile(Paths.get(negative)));AssetManager a=assets(negative);
      try{
        Resources r=resources(a,false);
        try{drawable(r,IDS[0],420);fail("Signed430 negative must reproduce nonzero-density ResourceID0 failure");}
        catch(Resources.NotFoundException expected){
          assertTrue("Specific ResourceID0 cause required",containsZeroResource(expected));
          try(PrintWriter out=new PrintWriter(Files.newBufferedWriter(output().resolve("SIGNED430-EXPECTED-FAILURE.txt")))){expected.printStackTrace(out);}
          System.out.println("ICON_SIGNED430_NEGATIVE reproduced ResourceID0 at density420");
        }
      }finally{a.close();}
    }else System.out.println("ICON_SIGNED430_NEGATIVE NOT_SELECTED_NO_INPUT");
  }
}
