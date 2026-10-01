package com.projectinfinity.kodi;
import android.app.Application;import android.graphics.*;import android.view.TextureView;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class) @Config(sdk=35,application=Application.class,manifest=Config.NONE)
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class AmbientVisibleCropTest {
 TextureView view(float sx,float sy){TextureView t=new TextureView(RuntimeEnvironment.getApplication());t.layout(0,0,400,200);Matrix m=new Matrix();m.setScale(sx,sy,200,100);t.setTransform(m);return t;}
 RectF region(TextureView t){RectF out=new RectF();CobraImmersiveAmbient.visibleSource(t,out,new Matrix(),new Matrix());return out;}
 @Test public void fillSamplesOnlyVisibleCenter(){assertEquals(new RectF(100,0,300,200),region(view(2,1)));}
 @Test public void fullscreenFitRetainsCompleteSource(){assertEquals(new RectF(0,0,400,200),region(view(1,.5f)));}
 @Test public void encodedBorderZoomMapsToVisibleSource(){RectF r=region(view(4f/3,4f/3));assertEquals(50,r.left,.001f);assertEquals(25,r.top,.001f);assertEquals(350,r.right,.001f);assertEquals(175,r.bottom,.001f);}
 @Test public void capturedPixelsExcludeCroppedEdgesAndReuseBuffers()throws Exception{
  TextureView t=new TextureView(RuntimeEnvironment.getApplication()){
   @Override public Bitmap getBitmap(Bitmap out){Canvas c=new Canvas(out);c.drawColor(Color.BLUE);Paint p=new Paint();p.setColor(Color.RED);c.drawRect(0,0,out.getWidth()/4,out.getHeight(),p);p.setColor(Color.GREEN);c.drawRect(out.getWidth()*3/4,0,out.getWidth(),out.getHeight(),p);return out;}
  };t.layout(0,0,400,200);Matrix transform=new Matrix();transform.setScale(2,1,200,100);t.setTransform(transform);
  CobraImmersiveAmbient engine=new CobraImmersiveAmbient(RuntimeEnvironment.getApplication());
  CobraNavigationUiTest.call(engine,"ensureBuffers",144,72);
  Bitmap first=(Bitmap)CobraNavigationUiTest.call(engine,"captureWatch",t,144,72);assertEquals(Color.BLUE,first.getPixel(5,30));assertEquals(Color.BLUE,first.getPixel(138,30));
  Object buffer=CobraNavigationUiTest.get(engine,"watchCapture");for(int i=0;i<20;i++)assertSame(first,CobraNavigationUiTest.call(engine,"captureWatch",t,144,72));assertSame(buffer,CobraNavigationUiTest.get(engine,"watchCapture"));
  assertEquals(region(view(2,1)),region(t));engine.release();
 }
}
