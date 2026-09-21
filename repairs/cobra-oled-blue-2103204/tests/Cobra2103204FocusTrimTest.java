package com.projectinfinity.kodi;

import android.app.Application;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.RectF;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real production sheet and focused row drawing in reserved native-layout gutters.
 * This is Android/Robolectric evidence, not physical Fold or GPU verification.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w320dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103204FocusTrimTest {
  Cobra2103204PresentationTest f;
  @Before public void before()throws Exception{f=new Cobra2103204PresentationTest();f.before();}
  @After public void after(){
    Configuration c=new Configuration(RuntimeEnvironment.getApplication().getResources().getConfiguration());c.fontScale=1f;
    RuntimeEnvironment.getApplication().getResources().updateConfiguration(c,RuntimeEnvironment.getApplication().getResources().getDisplayMetrics());
    if(f!=null)f.after();
  }
  static Object call(Object owner,String name,Object...args)throws Exception{return CobraNavigationUiTest.call(owner,name,args);}
  static boolean blueRim(int color){
    // Reject the pale blue / dark blue focus fill. Count the saturated blue rim,
    // including opaque antialiasing pixels, rather than treating any blue as proof.
    return Color.alpha(color)>=180&&Color.blue(color)-Color.red(color)>80&&Color.blue(color)-Color.green(color)>40;
  }
  static int rimPixels(Bitmap pixels,int left,int right,int centerY){
    int count=0;for(int y=Math.max(0,centerY-4);y<Math.min(pixels.getHeight(),centerY+5);y++)
      for(int x=left;x<right;x++)if(blueRim(pixels.getPixel(x,y)))count++;
    return count;
  }
  static void textFits(View view,String context){
    assertNotNull(context+" copy view",view);
    if(view instanceof TextView){TextView text=(TextView)view;
      if(text.getText().length()>0){assertNotNull(context+" text layout",text.getLayout());
        int available=text.getHeight()-text.getTotalPaddingTop()-text.getTotalPaddingBottom();
        assertTrue(context+" text height: "+text.getText(),text.getLayout().getHeight()<=available+1);
      }
    }
    if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;for(int i=0;i<group.getChildCount();i++)textFits(group.getChildAt(i),context);}
  }

  @Test(timeout=180000) public void focusedRimsFitAndRenderInBothGuttersAtCoverAndWideFontScales()throws Exception{
    for(String mode:new String[]{"light","dark","oled"})for(int width:new int[]{320,440})for(float font:new float[]{1f,1.5f,2f}){
      InfinityLiveActivity a=f.activity(mode,width,915);
      String label=mode+" / "+width+"dp / font "+font;
      try{
        Configuration c=new Configuration(a.getResources().getConfiguration());c.fontScale=font;
        a.getResources().updateConfiguration(c,a.getResources().getDisplayMetrics());
        LinearLayout items=(LinearLayout)call(a,"cobraOpenSheet","Audio & subtitles","Existing focus feedback","focus-trim-fixture");
        View row=(View)call(a,"cobraDetailRow","cc","Preferred subtitles","Saved preference: English • when available","cobra204-focus-trim-row",true,(Runnable)()->{});
        items.addView(row);f.ui.measure(a,width,915);f.ui.frames(20);
        assertTrue(label+" natural focus entry",row.requestFocusFromTouch());f.ui.frames(20);
        assertTrue(label,row.hasFocus());assertEquals(label,1.018f,row.getScaleX(),.0001f);assertEquals(label,1.018f,row.getScaleY(),.0001f);
        assertEquals(label,4,items.getPaddingLeft());assertEquals(label,4,items.getPaddingRight());
        assertEquals(label,3,items.getPaddingTop());assertEquals(label,3,items.getPaddingBottom());
        assertFalse(label+" row may draw within its reserved gutter",items.getClipToPadding());
        assertTrue(label+" outer child clipping remains protected",items.getClipChildren());
        RectF mapped=new RectF(0,0,row.getWidth(),row.getHeight());row.getMatrix().mapRect(mapped);
        mapped.offset(row.getLeft(),row.getTop());
        assertTrue(label+" full transformed row stays inside items: "+mapped,mapped.left>=0&&mapped.top>=0&&mapped.right<=items.getWidth()&&mapped.bottom<=items.getHeight());
        // Heading/detail copy must fit. The checkmark is a decorative glyph with
        // separate fixed icon geometry; its font metrics are not visible-ink bounds.
        textFits(Cobra2103204PresentationTest.text(row,"Preferred subtitles"),label);
        textFits(Cobra2103204PresentationTest.text(row,"Saved preference: English • when available"),label);
        Bitmap pixels=Bitmap.createBitmap(items.getWidth(),items.getHeight(),Bitmap.Config.ARGB_8888);
        try{
          items.draw(new Canvas(pixels));int centerY=Math.round(mapped.centerY());
          assertTrue(label+" LEFT reserved gutter contains the drawn blue rim",rimPixels(pixels,0,items.getPaddingLeft(),centerY)>=4);
          assertTrue(label+" RIGHT reserved gutter contains the drawn blue rim",rimPixels(pixels,items.getWidth()-items.getPaddingRight(),items.getWidth(),centerY)>=4);
        }finally{pixels.recycle();}
        if(("light".equals(mode)&&width==320&&font==2f)||("dark".equals(mode)&&width==440&&font==1f)||("oled".equals(mode)&&width==320&&font==1.5f))
          f.shot(a,"focus-trim-"+mode+"-"+width+"x915-font"+Math.round(font*100),width,915);
      }finally{
        Configuration reset=new Configuration(a.getResources().getConfiguration());reset.fontScale=1f;
        a.getResources().updateConfiguration(reset,a.getResources().getDisplayMetrics());f.ui.clean(a);
      }
    }
  }
}
