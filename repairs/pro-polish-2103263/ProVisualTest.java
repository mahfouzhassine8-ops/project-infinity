package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import java.io.*;
import java.util.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class ProVisualTest {
  static final class Calls implements CobraProUi.Actions {int preview,unmute;final ArrayList<Integer> steps=new ArrayList<>(),controls=new ArrayList<>();public void preview(){preview++;}public void unmute(){unmute++;}public void step(int d){steps.add(d);}public void control(int i){controls.add(i);}}
  static CobraProUi.Program data(int index){CobraProUi.Program p=new CobraProUi.Program();String[] channels={"Nicktoons West","Cartoon Network","Disney Channel","ESPN","FOX 17","HGTV"};String[] shows={"SpongeBob SquarePants","Teen Titans Go!","Bluey","SportsCenter","Local News","House Hunters"};p.channel=channels[index%6];p.title=shows[index%6];p.schedule="1:20 PM – 1:46 PM  ·  18 min left";p.next="Next scheduled programme";p.progress=.31f;p.live=true;p.favorite=index==0;p.source=index==0?"FROM RECENTLY WATCHED":"FROM FAVORITES";return p;}
  static void layout(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  static double luminance(int color){double[] v={Color.red(color)/255d,Color.green(color)/255d,Color.blue(color)/255d};for(int i=0;i<3;i++)v[i]=v[i]<=.04045?v[i]/12.92:Math.pow((v[i]+.055)/1.055,2.4);return v[0]*.2126+v[1]*.7152+v[2]*.0722;}
  static FrameLayout.LayoutParams rect(int[] r){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.max(1,r[2]),Math.max(1,r[3]));p.leftMargin=r[0];p.topMargin=r[1];return p;}
  static class Scene {
    final ActivityController<Activity> ctl;final Activity activity;final FrameLayout root,video;final LinearLayout below,browser;final CobraProUi.Hero hero;final CobraProUi.Filters filters;final Calls calls=new Calls();final boolean light;final int width,height;
    Scene(boolean light,int state,int width,int height)throws Exception{
      RuntimeEnvironment.setQualifiers("w"+width+"dp-h"+height+"dp-mdpi");this.width=width;this.height=height;this.light=light;
      ctl=Robolectric.buildActivity(Activity.class).setup();activity=ctl.get();root=new FrameLayout(activity);root.setBackgroundColor(light?CobraProUi.PALE:Color.BLACK);activity.setContentView(root);
      int[][] r=CobraProUi.geometry(width,height,1,state);
      LinearLayout header=new LinearLayout(activity);header.setGravity(Gravity.CENTER_VERTICAL);CobraProUi.Action menu=new CobraProUi.Action(activity,"list","",false,light,()->{});menu.setContentDescription("Open Cobra navigation");header.addView(menu,new LinearLayout.LayoutParams(48,48));LinearLayout headerCopy=new LinearLayout(activity);headerCopy.setOrientation(1);headerCopy.setPadding(10,0,0,0);CobraProUi.Ink name=new CobraProUi.Ink(activity,light?CobraProUi.INK:Color.WHITE,22,true);name.text("Pro");headerCopy.addView(name);CobraProUi.Ink count=new CobraProUi.Ink(activity,light?CobraProUi.MUTED:0xffaacadd,10,false);count.text("COBRA LIVE  ·  TEST CHANNEL DATA");headerCopy.addView(count);header.addView(headerCopy,new LinearLayout.LayoutParams(0,-2,1));header.addView(new CobraProUi.Action(activity,"more","",false,light,()->{}),new LinearLayout.LayoutParams(48,48));header.addView(new CobraProUi.Action(activity,"groups","",false,light,()->{}),new LinearLayout.LayoutParams(48,48));root.addView(header,rect(r[0]));
      video=new FrameLayout(activity);video.setBackgroundColor(Color.BLACK);root.addView(video,rect(r[1]));ImageView frame=new ImageView(activity);frame.setScaleType(ImageView.ScaleType.CENTER_CROP);
      File fixture=new File(System.getProperty("pro.fixture",""));if(fixture.isFile()){byte[] bytes=java.nio.file.Files.readAllBytes(fixture.toPath());frame.setImageBitmap(BitmapFactory.decodeByteArray(bytes,0,bytes.length));}else frame.setBackgroundColor(0xff145270);video.addView(frame,new FrameLayout.LayoutParams(-1,-1));
      below=new LinearLayout(activity);below.setOrientation(1);below.setVisibility(state==2?View.VISIBLE:View.GONE);root.addView(below,rect(r[2]));
      hero=new CobraProUi.Hero(activity,light,calls,null);video.addView(hero,new FrameLayout.LayoutParams(-1,-1));hero.bind(data(0),0,6);hero.setState(state,below,false);hero.playback(state>0,state!=2,false,true);
      android.graphics.drawable.GradientDrawable border=new android.graphics.drawable.GradientDrawable();border.setColor(Color.BLACK);border.setCornerRadius(14);border.setStroke(1,CobraProUi.CYAN);video.setBackground(border);video.setClipToOutline(true);video.setElevation(3);
      browser=new LinearLayout(activity);browser.setOrientation(1);root.addView(browser,rect(r[3]));filters=new CobraProUi.Filters(activity,light,i->{});filters.selected(0);browser.addView(filters,new LinearLayout.LayoutParams(-1,-2));ListView list=new ListView(activity);list.setDividerHeight(0);list.setItemsCanFocus(true);list.setAdapter(new BaseAdapter(){public int getCount(){return 6;}public Object getItem(int i){return data(i);}public long getItemId(int i){return i;}public View getView(int i,View old,ViewGroup group){CobraProUi.ChannelRow row=new CobraProUi.ChannelRow(activity,light,()->{});row.bind(data(i),i,i==0,null);return row;}});browser.addView(list,new LinearLayout.LayoutParams(-1,0,1));layout(root,width,height);
    }
    void close(){ctl.pause().stop().destroy();}
  }
  @Test public void stateMovesTheSameMetadataViewAndNeverAddsASourceRail()throws Exception{
    Scene s=new Scene(true,0,412,915);assertSame(s.hero,s.hero.info.getParent());assertEquals(View.VISIBLE,s.hero.preview.getVisibility());assertEquals(View.GONE,s.hero.unmute.getVisibility());
    s.hero.setState(1,s.below,false);assertSame(s.hero,s.hero.info.getParent());assertEquals(View.GONE,s.hero.preview.getVisibility());assertEquals(View.VISIBLE,s.hero.unmute.getVisibility());
    s.below.setVisibility(View.VISIBLE);s.hero.setState(2,s.below,true);layout(s.root,412,915);Shadows.shadowOf(Looper.getMainLooper()).idle();assertSame(s.below,s.hero.info.getParent());assertEquals(1,s.below.getChildCount());for(CobraProUi.Action c:s.hero.player)assertEquals(View.VISIBLE,c.getVisibility());
    assertNull(s.root.findViewWithTag("source_thumbnail_rail"));assertTrue(s.hero.source.getText().toString().contains("RECENTLY WATCHED"));s.hero.setState(0,s.below,false);assertSame(s.hero,s.hero.info.getParent());s.close();
  }
  @Test public void previewUnmuteAndPlayerActionsAreDistinctCallbacks()throws Exception{
    Scene s=new Scene(true,0,412,915);s.hero.preview.performClick();assertEquals(1,s.calls.preview);assertEquals(0,s.calls.unmute);assertTrue(s.calls.controls.isEmpty());s.hero.setState(1,s.below,false);s.hero.unmute.performClick();assertEquals(1,s.calls.unmute);assertTrue(s.calls.controls.isEmpty());s.hero.setState(2,s.below,false);for(CobraProUi.Action b:s.hero.player)b.performClick();assertEquals(Arrays.asList(0,1,2,3,4,5),s.calls.controls);s.close();
  }
  @Test public void horizontalDragCancelsButtonClickAndChangesOnlyOneHero()throws Exception{
    Scene s=new Scene(true,0,412,915);long t=1000;float x=s.hero.preview.getX()+s.hero.preview.getWidth()/2f,y=s.hero.preview.getY()+24;
    for(int i=0;i<3;i++){int action=i==0?MotionEvent.ACTION_DOWN:i==1?MotionEvent.ACTION_MOVE:MotionEvent.ACTION_UP;MotionEvent e=MotionEvent.obtain(t,t+i*25,action,x-i*50,y,0);s.hero.dispatchTouchEvent(e);e.recycle();}
    assertEquals(Arrays.asList(1),s.calls.steps);assertEquals(0,s.calls.preview);assertEquals(0,s.calls.unmute);s.close();
  }
  @Test public void allFiveFiltersExistAndDispatchExactlyOnce()throws Exception{
    for(int w:new int[]{320,412,768}){RuntimeEnvironment.setQualifiers("w"+w+"dp-h915dp-mdpi");Activity a=Robolectric.buildActivity(Activity.class).setup().get();ArrayList<Integer> calls=new ArrayList<>();CobraProUi.Filters f=new CobraProUi.Filters(a,true,calls::add);a.setContentView(f);layout(f,w,CobraProUi.Filters.height(a,w));for(int i=0;i<5;i++){assertEquals(CobraProUi.Filters.LABELS[i],f.buttons[i].getContentDescription());assertTrue(f.buttons[i].getWidth()>=48);assertTrue(f.buttons[i].getHeight()>=48);f.buttons[i].performClick();}assertEquals(Arrays.asList(0,1,2,3,4),calls);}
  }
  @Test public void geometryKeepsAllRegionsInBoundsAndMetadataBelowVideo(){
    for(int[] size:new int[][]{{320,640},{412,915},{768,1024},{1024,600},{600,480}})for(int state=0;state<3;state++){
      int[][] r=CobraProUi.geometry(size[0],size[1],1,state);for(int[] b:r){assertTrue(Arrays.toString(b),b[0]>=0&&b[1]>=0&&b[0]+b[2]<=size[0]&&b[1]+b[3]<=size[1]);}
      assertTrue(r[3][3]>140);if(state==2)assertEquals(r[1][1]+r[1][3],r[2][1]);else assertEquals(0,r[2][3]);
      for(int i=0;i<4;i++)for(int j=i+1;j<4;j++){if(r[i][2]==0||r[j][2]==0)continue;assertFalse(Rect.intersects(new Rect(r[i][0],r[i][1],r[i][0]+r[i][2],r[i][1]+r[i][3]),new Rect(r[j][0],r[j][1],r[j][0]+r[j][2],r[j][1]+r[j][3])));}
    }
  }
  @Test public void missingGuideAndLogoStayTruthful()throws Exception{
    Scene s=new Scene(true,0,412,915);CobraProUi.Program p=data(0);p.title="Provider has no schedule for this channel";p.schedule="USA | Tubi";p.next="";p.progress=-1;p.logo="";s.hero.bind(p,0,1);assertEquals(p.title,s.hero.info.title.getText().toString());assertEquals(View.INVISIBLE,s.hero.info.progress.getVisibility());assertEquals(View.GONE,s.hero.right.getVisibility());s.close();
  }
  @Test public void lightThemeCannotTurnVideoOverlayTextBlack()throws Exception{
    Scene s=new Scene(true,0,412,915);s.hero.source.setTextColor(Color.BLACK);s.hero.info.title.setTextColor(Color.BLACK);assertEquals(Color.WHITE,s.hero.source.getCurrentTextColor());Bitmap badge=Bitmap.createBitmap(s.hero.live.getWidth(),s.hero.live.getHeight(),Bitmap.Config.ARGB_8888);s.hero.live.draw(new Canvas(badge));int white=0;for(int y=0;y<badge.getHeight();y++)for(int x=0;x<badge.getWidth();x++){int color=badge.getPixel(x,y);if(Color.red(color)>220&&Color.green(color)>220&&Color.blue(color)>220)white++;}assertTrue("LIVE text must actually render, not only exist in accessibility",white>5);badge.recycle();assertEquals(Color.WHITE,s.hero.info.title.getCurrentTextColor());s.hero.setState(2,s.below,false);assertEquals(CobraProUi.INK,s.hero.info.title.getCurrentTextColor());s.close();
  }
  @Test public void nativeScreenshotsAllStatesPhoneFoldAndLandscape()throws Exception{
    File out=new File(System.getProperty("pro.evidence","build/pro-evidence"));assertTrue(out.isDirectory()||out.mkdirs());
    for(boolean light:new boolean[]{true,false})for(int[] size:new int[][]{{412,915},{320,640},{768,1024},{1024,600}})for(int state=0;state<3;state++){
      Scene s=new Scene(light,state,size[0],size[1]);Bitmap b=Bitmap.createBitmap(size[0],size[1],Bitmap.Config.ARGB_8888);s.root.draw(new Canvas(b));try(FileOutputStream f=new FileOutputStream(new File(out,"pro-"+(light?"light":"oled")+"-"+state+"-"+size[0]+"x"+size[1]+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,f));}b.recycle();s.close();
    }
  }
  @Test public void filtersStayInOneScrollableRowAndSearchRemainsReachable()throws Exception{
    Scene s=new Scene(false,0,320,640);assertTrue(s.filters.strip.getWidth()>s.filters.getWidth());
    for(CobraProUi.Action a:s.filters.buttons){assertEquals(0,a.getTop());assertTrue(a.getWidth()>=78);}
    s.filters.scrollTo(s.filters.strip.getWidth(),0);assertTrue(s.filters.getScrollX()>0);
    assertTrue(s.filters.buttons[4].getRight()-s.filters.getScrollX()<=s.filters.getWidth());s.close();
  }
  @Test public void selectedDarkFilterActuallyRendersReadableWhiteText()throws Exception{
    Scene s=new Scene(false,0,412,915);CobraProUi.Action a=s.filters.buttons[0];Bitmap b=Bitmap.createBitmap(a.getWidth(),a.getHeight(),Bitmap.Config.ARGB_8888);a.draw(new Canvas(b));
    int bg=b.getPixel(8,8);assertTrue(Color.red(bg)<80&&Color.green(bg)<100&&Color.blue(bg)<110);int white=0;
    for(int y=40;y<b.getHeight()-4;y++)for(int x=0;x<b.getWidth();x++){int c=b.getPixel(x,y);if(Color.red(c)>220&&Color.green(c)>220&&Color.blue(c)>220)white++;}
    assertTrue("selected label must visibly render above its dark cyan wash",white>20);b.recycle();s.close();
  }
  @Test public void compactSourceBadgeAndTransportDoNotCoverProgrammeCopy()throws Exception{
    for(boolean light:new boolean[]{true,false}){Scene s=new Scene(light,0,412,915);CobraProUi.Program p=data(0);p.source="FROM CHANNELS";s.hero.bind(p,0,6);layout(s.root,412,915);
      assertTrue(s.hero.source.getWidth()<s.hero.getWidth()/2);assertTrue(s.hero.info.getBottom()<=s.hero.transport.getTop());assertTrue(s.hero.info.getTop()>s.hero.source.getBottom());
      Bitmap b=Bitmap.createBitmap(s.hero.transport.getWidth(),s.hero.transport.getHeight(),Bitmap.Config.ARGB_8888);s.hero.transport.draw(new Canvas(b));int c=b.getPixel(b.getWidth()/2,b.getHeight()/2);
      assertEquals(light,Color.red(c)>200&&Color.green(c)>200&&Color.blue(c)>200);assertEquals(light?CobraProUi.INK:Color.WHITE,s.hero.muted.getCurrentTextColor());b.recycle();
      Bitmap button=Bitmap.createBitmap(s.hero.preview.getWidth(),s.hero.preview.getHeight(),Bitmap.Config.ARGB_8888);s.hero.preview.draw(new Canvas(button));assertTrue("white Preview label needs readable fill contrast",1.05/(luminance(button.getPixel(40,8))+.05)>=4.5);button.recycle();
      s.hero.setState(2,s.below,false);if(light)assertTrue((luminance(CobraProUi.PALE)+.05)/(luminance(s.hero.info.eyebrow.getCurrentTextColor())+.05)>=4.5);s.close();}
  }
  @Test public void largeFontsKeepNavigationAndPlayerTargetsUsable()throws Exception{
    Scene s=new Scene(true,2,320,640);android.content.res.Configuration original=new android.content.res.Configuration(s.activity.getResources().getConfiguration());
    try{android.content.res.Configuration large=new android.content.res.Configuration(original);large.fontScale=2;s.activity.getResources().updateConfiguration(large,s.activity.getResources().getDisplayMetrics());
      layout(s.filters,304,CobraProUi.Filters.height(s.activity,304));assertTrue(s.filters.getHeight()>=86);for(CobraProUi.Action a:s.filters.buttons){assertTrue(a.getWidth()>=156);assertTrue(a.getHeight()>=48);}
      layout(s.hero,304,207);for(CobraProUi.Action a:s.hero.player){assertTrue(a.getWidth()>=48);assertTrue(a.getHeight()>=48);}assertEquals(Typeface.create("sans-serif-medium",Typeface.NORMAL),s.hero.info.title.getTypeface());
    }finally{s.activity.getResources().updateConfiguration(original,s.activity.getResources().getDisplayMetrics());s.close();}
  }
}
