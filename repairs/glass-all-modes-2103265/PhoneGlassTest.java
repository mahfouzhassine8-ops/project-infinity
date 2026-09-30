package com.projectinfinity.kodi;
import android.app.Activity;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import java.lang.reflect.*;
import java.io.*;
import java.util.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class PhoneGlassTest {
  static Object call(Object o,String name,Object... args)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass())for(Method m:c.getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(InvocationTargetException e){throw new RuntimeException(name,e.getCause());}}
    throw new NoSuchMethodException(name);
  }
  static Field field(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f;}
  static void put(Object o,String name,Object value)throws Exception{field(o,name).set(o,value);}
  static Object get(Object o,String name)throws Exception{return field(o,name).get(o);}
  static Object load(InfinityLiveActivity a,String name)throws Exception{Class<?> c=Class.forName(InfinityLiveActivity.class.getName()+"$"+name);Method m=c.getDeclaredMethod("load",Context.class);m.setAccessible(true);return m.invoke(null,a);}
  static void layout(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  static Bitmap render(View v){Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));return b;}
  static void save(View v,String name)throws Exception{File d=new File(System.getProperty("glass.phone.evidence","build/phone-glass"));d.mkdirs();Bitmap b=render(v);try(FileOutputStream f=new FileOutputStream(new File(d,name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,f));}b.recycle();}
  InfinityLiveActivity activity(boolean light,int w,int h)throws Exception{
    RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-mdpi");
    InfinityLiveActivity a=Robolectric.buildActivity(InfinityLiveActivity.class).get();
    SharedPreferences p=a.getSharedPreferences("phone-glass-tests",0);p.edit().clear().putString("cobra_appearance_mode",light?"light":"oled").apply();put(a,"mPrefs",p);
    put(a,"mTheme",load(a,"Theme"));put(a,"mUi",load(a,"UiContract"));put(a,"mFeatures",new InfinityCobraFeatureRuntime(a));
    put(a,"mVisualTheme",new CobraVisualRenderer(a).mode(light?"light":"oled"));
    LinearLayout root=new LinearLayout(a);root.setOrientation(1);LinearLayout stage=new LinearLayout(a);stage.setOrientation(1);root.addView(stage,new LinearLayout.LayoutParams(-1,-1));
    TextView header=new TextView(a),status=new TextView(a);stage.addView(header);stage.addView(status);put(a,"mRoot",root);put(a,"mStage",stage);put(a,"mHeader",header);put(a,"mStatus",status);a.setContentView(root);layout(root,w,h);return a;
  }
  @Before public void stableRenderer(){CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();}
  @After public void clearRenderer(){CobraVisualRenderer.active=CobraVisualTheme.builtin();}
  @Test public void liveTextSurvivesTheActualSharedThemeTreeAndRefresh()throws Exception{
    for(boolean light:new boolean[]{false,true})for(float font:new float[]{1,2}){
      ProVisualTest.Scene s=new ProVisualTest.Scene(light,0,412,915,font);
      CobraVisualTheme theme=CobraVisualTheme.builtin();theme.data.put("styles",new JSONObject().put("all.text",new JSONObject().put("padding_dp",32).put("text_size_sp",48).put("text","#000000")).put("all.panel",new JSONObject().put("fill","#ffffff").put("padding_dp",20)));
      CobraVisualRenderer.active=theme;CobraVisualRenderer r=new CobraVisualRenderer(s.activity).mode(light?"light":"oled");
      int w=s.hero.live.getWidth(),h=s.hero.live.getHeight();r.tree(s.hero,"guide.details");r.refresh();ProVisualTest.layout(s.root,412,915);
      assertEquals("LIVE",s.hero.live.getText().toString());assertEquals(w,s.hero.live.getWidth());assertEquals(h,s.hero.live.getHeight());assertEquals(0,s.hero.live.getPaddingLeft());
      Bitmap b=render(s.hero.live);int red=0;for(int y=0;y<b.getHeight();y++)for(int x=0;x<b.getWidth();x++){int c=b.getPixel(x,y);if(Color.red(c)>180&&Color.red(c)>Color.green(c)*1.25)red++;}assertTrue("LIVE must visibly draw red glyphs after production styling",red>15);b.recycle();save(s.hero.live,"live-"+light+"-font"+font);s.close();CobraVisualRenderer.active=CobraVisualTheme.builtin();
    }
  }
  @Test public void allFourActualGuideShellsRenderGlassWithoutAPlayer()throws Exception{
    for(boolean light:new boolean[]{false,true})for(String mode:new String[]{"mobile","grid","compact","cards"})for(int[] size:new int[][]{{412,915},{320,640},{1024,600}}){
      InfinityLiveActivity a=activity(light,size[0],size[1]);put(a,"mCobraGuideStyle",mode);put(a,"mCobraPreviewAutoplayAllowed",false);
      Class<?> channelClass=Class.forName(InfinityLiveActivity.class.getName()+"$Channel");Constructor<?> channelCtor=channelClass.getDeclaredConstructor(String.class,String.class,String.class,String.class,String.class,String.class,String.class,Map.class);channelCtor.setAccessible(true);
      ArrayList fixtureChannels=(ArrayList)get(a,"mChannels");
      for(int i=0;i<6;i++)fixtureChannels.add(channelCtor.newInstance("fixture:"+i,"Channel "+(i+1),"Test group","","","https://fixture.invalid/test.ts","",new HashMap<String,String>()));
      put(a,"mGuidePreviewChannel",fixtureChannels.get(0));put(a,"mCobraGuideRoute","channels");
      call(a,"cobraShowGuideShell");View root=(View)get(a,"mRoot");layout(root,size[0],size[1]);((View)get(a,"mCobraGuideBrowser")).animate().cancel();((View)get(a,"mCobraGuideBrowser")).setAlpha(1f);
      assertTrue(((View)get(a,"mCobraModeToolbar")).getBackground() instanceof CobraVisualRenderer.Glass);
      assertTrue(((View)get(a,"mCobraGuideDetails")).getBackground() instanceof CobraVisualRenderer.Glass);
      assertNotNull(get(a,"mCobraGuideList"));assertEquals(6,((AbsListView)get(a,"mCobraGuideList")).getAdapter().getCount());
      assertNull(get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayer"));
      save(root,mode+"-"+(light?"light":"oled")+"-"+size[0]+"x"+size[1]);((android.os.Handler)get(a,"mMain")).removeCallbacksAndMessages(null);a.finish();
    }
  }
  @Test public void actualDrawerAndChooserKeepTheirDestinationsAndFiveLayouts()throws Exception{
    for(boolean light:new boolean[]{false,true}){
      InfinityLiveActivity a=activity(light,412,915);call(a,"toggleCobraDrawer");View decor=a.getWindow().getDecorView();View drawer=decor.findViewWithTag("cobra_experience_drawer");assertNotNull(drawer);layout(drawer,412,915);View panel=((ViewGroup)drawer).getChildAt(0);panel.animate().cancel();panel.setTranslationX(0);panel.setAlpha(1);
      for(String destination:new String[]{"SEARCH","TV","MOVIES","SHOWS","RECORDINGS","MY LIST","SETTINGS"}){View row=drawer.findViewWithTag("cobra-destination:"+destination);assertNotNull(destination,row);assertTrue(row.getBackground() instanceof CobraVisualRenderer.Glass);}
      assertNotNull(drawer.findViewWithTag("cobra-drawer-view"));assertNotNull(drawer.findViewWithTag("cobra_drawer_power"));save(drawer,"drawer-"+light);assertEquals(true,call(a,"closeCobraExperienceDrawer"));assertNull(decor.findViewWithTag("cobra_experience_drawer"));
      call(a,"cobraPremiumViewMenu");View chooser=(View)get(a,"mCobraActionSheet");layout(chooser,412,915);View chooserPanel=((ViewGroup)chooser).getChildAt(0);chooserPanel.animate().cancel();chooserPanel.setAlpha(1);chooserPanel.setTranslationY(0);chooserPanel.setScaleX(1);chooserPanel.setScaleY(1);for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){View card=decor.findViewWithTag("cobra-view-mode:"+mode);assertNotNull(mode,card);assertTrue(card.getBackground() instanceof CobraVisualRenderer.Glass);assertEquals(mode.equals("mobile"),card.isSelected());}
      save(chooser,"chooser-"+light);call(a,"closeCobraActionSheet");a.finish();
    }
  }
  @Test public void stateTransitionsKeepHitGeometryAndProduceVisibleSelection()throws Exception{
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();Button b=new Button(a);b.setBackground(CobraVisualRenderer.phoneGlass(a,false,14,true));a.setContentView(b);layout(b,200,56);b.setFocusable(false);b.clearFocus();b.getBackground().jumpToCurrentState();Bitmap normal=render(b);
    b.setSelected(true);b.getBackground().jumpToCurrentState();Bitmap selected=render(b);assertNotEquals(normal.getPixel(8,8),selected.getPixel(8,8));assertEquals(200,b.getWidth());assertEquals(56,b.getHeight());assertEquals(0,b.getTranslationX(),0);assertEquals(1,b.getScaleX(),0);normal.recycle();selected.recycle();
    b.setVisibility(View.GONE);assertFalse(b.getBackground().isVisible());
  }
}
