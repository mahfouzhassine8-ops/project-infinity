package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Handler;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.ExecutorService;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import static org.junit.Assert.*;

/** Native Android view rendering against generated production Activity, with fake guide data.
 * Does not decode video, contact a provider, or substitute for a phone playback test.
 *
 * The visual fixtures intentionally keep their EPG population small. The previous version
 * created 216,000 GuideProgram objects through reflection (12,000 channels x 6 programmes x
 * three Activities) before rendering only a handful of visible rows. On GitHub-hosted runners
 * that caused the Robolectric native-graphics test to exceed the whole 35-minute job timeout.
 * A separate 12,000-channel test below still exercises the real production adapters and proves
 * that every mode remains virtualized without manufacturing off-screen programme objects.
 */
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=34, application=Application.class, manifest=Config.NONE,
        qualifiers="w960dp-h540dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraModesUiTest {
  static final Class<?> ACT=InfinityLiveActivity.class;
  static final String[] MODES={"mobile","grid","compact","cards","focus"};
  Object get(Object owner,String name)throws Exception {Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);}
  void put(Object owner,String name,Object value)throws Exception {Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
  Object call(Object owner,String name,Object... args)throws Exception {for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){m.setAccessible(true);try{return m.invoke(owner,args);}catch(InvocationTargetException e){throw new AssertionError(name,e.getCause());}}throw new NoSuchMethodException(name);}
  Class<?> nested(String name)throws Exception {return Class.forName(ACT.getName()+"$"+name);}
  Object construct(String name,Object... args)throws Exception {for(Constructor<?> c:nested(name).getDeclaredConstructors())if(c.getParameterCount()==args.length){c.setAccessible(true);return c.newInstance(args);}throw new NoSuchMethodException(name);}

  @SuppressWarnings("unchecked") InfinityLiveActivity fixture(int channelCount,int epgChannelCount)throws Exception {
    InfinityLiveActivity a=Robolectric.buildActivity(InfinityLiveActivity.class).get();
    a.setTheme(android.R.style.Theme_Material_NoActionBar);
    put(a,"mPrefs",a.getSharedPreferences("cobra_modes_fixture",Context.MODE_PRIVATE));
    put(a,"mTheme",construct("Theme"));put(a,"mUi",construct("UiContract"));
    put(a,"mFeatures",new InfinityCobraFeatureRuntime(a));put(a,"mCobraPreviewAutoplayAllowed",false);
    ArrayList<Object> channels=(ArrayList<Object>)get(a,"mChannels");
    Object epg=construct("CobraEpgData");Map<String,Object> programs=(Map<String,Object>)get(epg,"programs");
    String[] names={"Nature One","World News","Kids Planet","Cinema Plus","Sport Central","History Now","Discovery Lab","Travel Life"};
    String[] titles={"Wild coastlines","The evening report","A new adventure","The midnight train","Live championship","Cities of the past","How it works","A journey north"};
    long now=System.currentTimeMillis(),start=now-now%1800000L;
    int withGuide=Math.min(channelCount,Math.max(0,epgChannelCount));
    for(int i=0;i<channelCount;i++){
      String id="fixture:"+i,epgId="ch"+i,group=i%3==0?"Documentaries":i%3==1?"Entertainment":"News & Sport";
      Object channel=construct("Channel",id,names[i%8]+(i<8?"":" "+i),group,epgId,"","","",Collections.emptyMap());channels.add(channel);
      if(i<withGuide){
        ArrayList<Object> rows=new ArrayList<>();
        for(int j=0;j<6;j++){
          Object p=construct("GuideProgram");put(p,"channel",epgId);put(p,"start",start+(j-1)*1800000L);put(p,"stop",start+j*1800000L);put(p,"title",titles[(i+j)%8]);put(p,"description","Guide fixture for native view tests. Playback is not being simulated.");rows.add(p);
        }
        programs.put(epgId,rows);
      }
    }
    ((Map<String,Object>)get(a,"mCobraEpg")).put("",epg);put(a,"mGuidePreviewChannel",channels.get(0));
    ((Set<String>)get(a,"mFavorites")).add("fixture:0");if(channelCount>2)((Set<String>)get(a,"mFavorites")).add("fixture:2");
    ((List<String>)get(a,"mRecents")).add("fixture:0");if(channelCount>1)((List<String>)get(a,"mRecents")).add("fixture:1");
    call(a,"buildShell");return a;
  }

  void measure(InfinityLiveActivity a,int w,int h)throws Exception {
    View decor=a.getWindow().getDecorView();
    for(int i=0;i<3;i++){decor.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));decor.layout(0,0,w,h);call(a,"cobraLayoutGuide");}
    call(a,"cobraRenderGuideBrowser");decor.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));decor.layout(0,0,w,h);
  }
  int count(View view){int n=1;if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)n+=count(((ViewGroup)view).getChildAt(i));return n;}
  void image(InfinityLiveActivity a,String name)throws Exception {
    View root=(View)get(a,"mCobraGuideShell");assertTrue(root.getWidth()>0);assertTrue(root.getHeight()>0);
    Bitmap bitmap=Bitmap.createBitmap(root.getWidth(),root.getHeight(),Bitmap.Config.ARGB_8888);root.draw(new Canvas(bitmap));
    File dir=new File(System.getProperty("cobra.screenshots","build/cobra-mode-screenshots"));assertTrue(dir.isDirectory()||dir.mkdirs());try(FileOutputStream stream=new FileOutputStream(new File(dir,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,stream));}bitmap.recycle();
  }
  void clean(InfinityLiveActivity a)throws Exception {((Handler)get(a,"mMain")).removeCallbacksAndMessages(null);((ExecutorService)get(a,"mIo")).shutdownNow();a.finish();}

  @Test(timeout=600000) public void fiveModesRenderAndKeepOneVideoSurface()throws Exception {
    // 192 channels are plenty to exercise recycled rows, programme blocks and screenshots.
    // Only 64 need EPG because a phone/tablet viewport cannot display more at one time.
    for(int[] wh:new int[][]{{360,800},{960,540}}){
      RuntimeEnvironment.setQualifiers("w"+wh[0]+"dp-h"+wh[1]+"dp-"+(wh[0]>wh[1]?"land":"port")+"-mdpi");
      InfinityLiveActivity a=fixture(192,64);Object texture=null;Set<String> renderers=new HashSet<>();
      try {for(String mode:MODES){
        System.out.println("Rendering "+mode+" at "+wh[0]+"x"+wh[1]);
        call(a,"cobraSwitchMode",mode);measure(a,wh[0],wh[1]);Object current=get(a,"mCobraPreviewTexture");assertNotNull(current);if(texture==null)texture=current;else assertSame("Changing view mode must retain exact TextureView",texture,current);
        AbsListView list=(AbsListView)get(a,"mCobraGuideList");assertNotNull(mode+" list",list);assertTrue(mode+" visible browsing area",list.getHeight()>=48);assertEquals(192,list.getCount());assertTrue("production browser must remain virtualized",count((View)get(a,"mCobraGuideShell"))<1000);
        assertTrue(mode+" has rendered rows",list.getChildCount()>0);renderers.add(list.getChildAt(0).getClass().getSimpleName());
        if(mode.equals("grid"))assertNotNull(((View)get(a,"mCobraGuideShell")).findViewWithTag("cobra_tv_time_ruler"));
        image(a,mode+"-"+wh[0]+"x"+wh[1]+"-dark");
      }assertEquals("Five different production row renderers",5,renderers.size());
      call(a,"toggleCobraDrawer");View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(drawer);call(a,"closeCobraExperienceDrawer");
      call(a,"showCobraViewModeMenu");assertNotNull(get(a,"mCobraActionSheet"));call(a,"closeCobraActionSheet");
      } finally{clean(a);}
    }
  }

  @Test(timeout=360000) public void twelveThousandChannelsRemainVirtualized()throws Exception {
    RuntimeEnvironment.setQualifiers("w960dp-h540dp-land-mdpi");
    // This is the real 12k stress gate. Off-screen EPG objects are deliberately omitted: the
    // contract under test is adapter/list virtualization and view-tree size, not XMLTV parsing.
    InfinityLiveActivity a=fixture(12000,0);Object texture=null;
    try {
      for(String mode:MODES){
        System.out.println("12k virtualization: "+mode);
        call(a,"cobraSwitchMode",mode);measure(a,960,540);
        AbsListView list=(AbsListView)get(a,"mCobraGuideList");assertNotNull(list);assertEquals(12000,list.getCount());
        assertTrue(mode+" rendered children must be bounded",list.getChildCount()>0 && list.getChildCount()<100);
        assertTrue(mode+" complete view tree must stay bounded",count((View)get(a,"mCobraGuideShell"))<1000);
        Object current=get(a,"mCobraPreviewTexture");assertNotNull(current);if(texture==null)texture=current;else assertSame("12k mode switch must retain exact TextureView",texture,current);
      }
    } finally {clean(a);}
  }

  @Test(timeout=360000) public void lightAndLargeTextRemainBrowsable()throws Exception {
    RuntimeEnvironment.setQualifiers("w320dp-h720dp-port-mdpi");InfinityLiveActivity a=fixture(160,48);
    try {android.content.res.Configuration config=a.getResources().getConfiguration();config.fontScale=1.5f;a.getResources().updateConfiguration(config,a.getResources().getDisplayMetrics());
      SharedPreferences prefs=(SharedPreferences)get(a,"mPrefs");prefs.edit().putString("cobra_appearance_mode","light").commit();
      for(String mode:MODES){System.out.println("Large text: "+mode);call(a,"cobraSwitchMode",mode);measure(a,320,720);AbsListView list=(AbsListView)get(a,"mCobraGuideList");assertNotNull(list);assertTrue(mode+" large-text browser",list.getHeight()>48);image(a,mode+"-320x720-light-large-text");}
    }finally{clean(a);}
  }
}
