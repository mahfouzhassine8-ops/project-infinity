package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;

/** Actual rebuilt classes/views/handlers. Player proxies only record session
 * calls; no streaming, decoder, platform PiP or physical Fold claim is made. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w480dp-h900dp-port-mdpi",instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraArrangeIntegrationTest {
  static Object get(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
  static void set(Object o,String n,Object v)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
  static Object call(Object o,String n,Object...args)throws Exception{
    for(Method m:o.getClass().getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterCount()==args.length){m.setAccessible(true);return m.invoke(o,args);}
    throw new NoSuchMethodException(n);
  }
  static Object construct(String name,Object...args)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+name);
    for(Constructor<?> ctor:c.getDeclaredConstructors())if(ctor.getParameterCount()==args.length){ctor.setAccessible(true);return ctor.newInstance(args);}
    throw new NoSuchMethodException(name);
  }
  static final class PlayerState implements InvocationHandler {
    float volume;boolean paused;int state=3;final List<String> writes=new ArrayList<>();Object proxy;
    PlayerState(int i)throws Exception{
      volume=i==1?0.37f:0;paused=i%2==0;
      Class<?> type=Class.forName("androidx.media3.exoplayer.ExoPlayer");
      proxy=Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},this);
    }
    public Object invoke(Object p,Method m,Object[] args){
      String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(p);
      if(n.equals("equals"))return p==args[0];if(n.equals("toString"))return "inert-player";
      if(n.equals("getPlaybackState"))return state;if(n.equals("getVolume"))return volume;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return !paused;
      if(n.startsWith("set")||n.startsWith("seek")||Arrays.asList("prepare","play","pause","stop","release").contains(n))writes.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;
      if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  static void measure(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  static final class Fixture {
    InfinityLiveActivity a;FrameLayout root,canvas;SharedPreferences prefs;
    final List<Object> tiles=new ArrayList<>();final List<PlayerState> players=new ArrayList<>();
    Fixture(int count,String mode,int w,int h)throws Exception{
      RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-"+(w>=h?"land":"port")+"-mdpi");
      ActivityController<InfinityLiveActivity> controller=Robolectric.buildActivity(InfinityLiveActivity.class);a=controller.get();
      a.setTheme(android.R.style.Theme_Material_NoActionBar);
      prefs=a.getSharedPreferences("cobra-arrange-"+UUID.randomUUID(),Context.MODE_PRIVATE);
      prefs.edit().putString("cobra_appearance_mode","dark").commit();set(a,"mPrefs",prefs);
      set(a,"mTheme",construct("Theme"));set(a,"mUi",construct("UiContract"));
      mode(mode);
      root=new FrameLayout(a);canvas=new FrameLayout(a);root.addView(canvas,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);
      set(a,"mMultiOverlay",root);set(a,"mCobraMultiCanvas",canvas);set(a,"mMultiChrome",new LinearLayout(a));
      Map entries=(Map)get(get(a,"mCobraTiles"),"entries");
      for(int i=0;i<count;i++){
        Object channel=construct("Channel","id"+i,"Channel "+i,"Group","epg"+i,"","https://example.invalid/"+i,"source",Collections.emptyMap());
        Object tile=construct("CobraVideoTile",a,channel);PlayerState player=new PlayerState(i);set(tile,"player",player.proxy);
        tiles.add(tile);players.add(player);entries.put("id"+i,tile);canvas.addView((View)get(tile,"view"));
      }
      call(a,"cobraSyncMultiArrays");set(a,"mAudioTile",Math.min(1,count-1));
      controller.visible();Shadows.shadowOf(Looper.getMainLooper()).idle();resize(w,h); // app onCreate, services and engine never invoked
    }
    void mode(String mode)throws Exception{set(a,"mCobraGuideStyle",mode);set(a,"mCobraProActive",mode.equals("focus"));}
    void resize(int w,int h)throws Exception{measure(root,w,h);call(a,"cobraLayoutMultiTiles");measure(root,w,h);}
    List<String> keys()throws Exception{return new ArrayList<>(((Map<String,Object>)get(get(a,"mCobraTiles"),"entries")).keySet());}
    View view(int original)throws Exception{return (View)get(tiles.get(original),"view");}
    void select(String id)throws Exception{
      call(a,"cobraShowMultiLayoutChooser");View sheet=(View)get(a,"mCobraActionSheet");
      View item=sheet.findViewWithTag("cobra_arrangement_"+id);assertNotNull(id,item);assertTrue(item.performClick());
      measure(root,root.getWidth(),root.getHeight());
    }
    void unchanged()throws Exception{
      for(int i=0;i<players.size();i++){assertSame(players.get(i).proxy,get(tiles.get(i),"player"));assertTrue(players.get(i).writes.toString(),players.get(i).writes.isEmpty());
        assertEquals(i==1?0.37f:0,players.get(i).volume,0);assertEquals(i%2==0,players.get(i).paused);}
      String audible=keys().get((Integer)get(a,"mAudioTile"));assertEquals("id1",audible);
    }
  }
  static void touch(View v,int action,float globalX,float globalY,long start,long time){
    int[] at=new int[2];v.getLocationOnScreen(at);
    MotionEvent e=MotionEvent.obtain(start,time,action,globalX,globalY,0);e.offsetLocation(-at[0],-at[1]);
    v.dispatchTouchEvent(e);e.recycle();
  }
  static float[] center(View v){int[] at=new int[2];v.getLocationOnScreen(at);return new float[]{at[0]+v.getWidth()/2f,at[1]+v.getHeight()/2f};}
  static long hold(View v,float[] point){long t=SystemClock.uptimeMillis();touch(v,0,point[0],point[1],t,t);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(550));return t;}

  @Test public void allElevenActualPickerOptionsBindAndKeepSessionsInAllFiveModes()throws Exception{
    assertEquals(11,CobraLayoutCatalog.all().length);
    for(String mode:new String[]{"mobile","compact","cards","grid","focus"})for(int count=2;count<=4;count++){
      Fixture f=new Fixture(count,mode,600,900);
      for(String id:CobraLayoutCatalog.forCount(count)){
        f.select(id);
        for(int[] size:new int[][]{{480,900},{1800,1500},{1500,1800},{360,480}}){
          f.resize(size[0],size[1]);int area=0;
          for(int i=0;i<count;i++){FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)f.view(i).getLayoutParams();
            assertTrue(mode+id,p.width>0&&p.height>0&&p.leftMargin>=0&&p.topMargin>=0);
            assertTrue(p.leftMargin+p.width<=size[0]);assertTrue(p.topMargin+p.height<=size[1]);area+=p.width*p.height;}
          assertTrue(area>0);f.unchanged();
        }
      }
      assertEquals(0,CobraLayoutCatalog.forCount(1).length);assertEquals(0,CobraLayoutCatalog.forCount(5).length);
    }
  }
  @Test public void dragSwapChangesOrderButNoPlayerOrAudioState()throws Exception{
    Fixture f=new Fixture(3,"cards",900,600);f.select("columns3");
    View source=f.view(2);float[] from=center(source),to=center(f.view(0));long t=hold(source,from);
    touch(source,2,to[0],to[1],t,t+600);touch(source,1,to[0],to[1],t,t+650);
    assertEquals(Arrays.asList("id2","id1","id0"),f.keys());f.unchanged();
  }
  @Test public void dragPromotesToMainUsingExistingSessions()throws Exception{
    Fixture f=new Fixture(3,"focus",900,600);f.select("columns3");View source=f.view(2);float[] from=center(source);long t=hold(source,from);
    int[] at=new int[2];f.canvas.getLocationOnScreen(at);float x=at[0]+450,y=at[1]+18;
    touch(source,2,x,y,t,t+600);touch(source,1,x,y,t,t+650);
    assertEquals(Arrays.asList("id2","id0","id1"),f.keys());
    assertEquals("main2",f.prefs.getString("cobra_multiview_arrangement.default.3",""));f.unchanged();
  }
  @Test public void cancellationOutsideResizeAndStaleSessionNeverCommit()throws Exception{
    for(String reason:new String[]{"cancel","outside","resize","stale","stopped","pointer"}){
      Fixture f=new Fixture(3,"compact",900,600);f.select("columns3");View source=f.view(2);float[] from=center(source),to=center(f.view(0));long t=hold(source,from);
      touch(source,2,to[0],to[1],t,t+600);
      if(reason.equals("cancel"))touch(source,3,to[0],to[1],t,t+620);
      if(reason.equals("outside")){to[0]=-100;to[1]=-100;}
      if(reason.equals("resize"))f.resize(480,900);
      if(reason.equals("stale"))set(f.tiles.get(0),"player",new PlayerState(0).proxy);
      if(reason.equals("stopped"))f.players.get(0).state=1;
      if(reason.equals("pointer"))touch(source,MotionEvent.ACTION_POINTER_DOWN,to[0],to[1],t,t+620);
      touch(source,1,to[0],to[1],t,t+650);
      assertEquals(reason,Arrays.asList("id0","id1","id2"),f.keys());
      for(PlayerState p:f.players)assertTrue(p.writes.isEmpty());
    }
  }
  @Test public void stationaryHoldPreservesOriginalMenuAndRemoteMoveUsesSameSwap()throws Exception{
    Fixture f=new Fixture(3,"mobile",900,600);View source=f.view(2);float[] from=center(source);long t=hold(source,from);
    touch(source,1,from[0],from[1],t,t+600);
    View sheet=(View)get(f.a,"mCobraActionSheet");assertNotNull(sheet);
    View move=sheet.findViewWithTag("cobra_move_screen");assertNotNull(move);assertTrue(move.performClick());
    sheet=(View)get(f.a,"mCobraActionSheet");assertTrue(sheet.findViewWithTag("cobra_swap_1").performClick());
    assertEquals(Arrays.asList("id2","id1","id0"),f.keys());f.unchanged();
  }
  @Test public void moreMovesOnlyItselfAndProOrderRestoresOnRetainedPreview()throws Exception{
    Fixture f=new Fixture(2,"mobile",480,900);
    LinearLayout row=new LinearLayout(f.a);ArrayList<View> original=new ArrayList<>();
    for(String tag:new String[]{"pause","favorite","captions","mute","cobra_preview_options_anchor","fullscreen","pip"}){
      View v=new View(f.a);v.setTag(tag);row.addView(v,new LinearLayout.LayoutParams(20,20));original.add(v);}
    CobraPresentation.moreLast(f.a,row);assertSame(original.get(4),row.getChildAt(6));
    f.mode("focus");CobraPresentation.moreLast(f.a,row);
    for(int i=0;i<original.size();i++)assertSame(original.get(i),row.getChildAt(i));
    f.mode("grid");CobraPresentation.moreLast(f.a,row);assertSame(original.get(4),row.getChildAt(6));
    assertEquals(7,row.getChildCount());
  }
  @Test public void identicalGeometryDoesNotRequestLayoutButResizeStillApplies(){
    Context c=RuntimeEnvironment.getApplication();
    class Counter extends View {int calls;Counter(){super(c);}public void setLayoutParams(ViewGroup.LayoutParams p){super.setLayoutParams(p);calls++;}}
    Counter v=new Counter();CobraPresentation.position(v,4,8,600,900);int first=v.calls;
    for(int i=0;i<100;i++)CobraPresentation.position(v,4,8,600,900);
    assertEquals(first,v.calls);CobraPresentation.position(v,4,8,900,600);assertEquals(first+1,v.calls);
    FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)v.getLayoutParams();assertEquals(900,p.width);assertEquals(600,p.height);
  }
  @Test public void actualPreviewReuseKeepsCallbacksAndRestoresProOrder()throws Exception{
    Fixture f=new Fixture(2,"mobile",480,900);Object channel=get(f.tiles.get(0),"channel");
    FrameLayout preview=(FrameLayout)call(f.a,"cobraPreviewPanel",channel,false);
    LinearLayout controls=preview.findViewWithTag("cobra_preview_controls");
    View more=controls.findViewWithTag("cobra_preview_options_anchor");assertNotNull(more);
    ArrayList<View> others=new ArrayList<>();for(int i=0;i<controls.getChildCount();i++)if(controls.getChildAt(i)!=more)others.add(controls.getChildAt(i));
    for(String mode:new String[]{"compact","cards","grid","focus","mobile"}){
      f.mode(mode);assertSame(preview,call(f.a,"cobraPreviewPanel",channel,false));
      assertSame(more,controls.getChildAt(mode.equals("focus")?4:controls.getChildCount()-1));
      ArrayList<View> now=new ArrayList<>();for(int i=0;i<controls.getChildCount();i++)if(controls.getChildAt(i)!=more)now.add(controls.getChildAt(i));
      assertEquals(others,now);assertTrue(more.hasOnClickListeners());
    }
  }
  @Test public void obsoleteRemoteChoiceCannotArrangeReplacementSession()throws Exception{
    Fixture f=new Fixture(3,"cards",900,600);call(f.a,"showCobraMultiTileActions",2);
    View sheet=(View)get(f.a,"mCobraActionSheet");sheet.findViewWithTag("cobra_move_screen").performClick();
    sheet=(View)get(f.a,"mCobraActionSheet");View swap=sheet.findViewWithTag("cobra_swap_1");
    set(f.tiles.get(0),"player",new PlayerState(0).proxy);swap.performClick();
    assertEquals(Arrays.asList("id0","id1","id2"),f.keys());
    call(f.a,"cobraShowMultiLayoutChooser");sheet=(View)get(f.a,"mCobraActionSheet");View option=sheet.findViewWithTag("cobra_arrangement_columns3");
    set(f.tiles.get(1),"player",new PlayerState(1).proxy);option.performClick();
    assertEquals("",f.prefs.getString("cobra_multiview_arrangement.default.3",""));
  }
  @Test public void detachedOldChoiceCannotCloseNewMenuAndOnePlayerIsUnchanged()throws Exception{
    Fixture f=new Fixture(3,"cards",900,600);call(f.a,"cobraShowMultiLayoutChooser");
    View old=(View)get(f.a,"mCobraActionSheet");View choice=old.findViewWithTag("cobra_arrangement_columns3");
    call(f.a,"showCobraMultiTileActions",1);Object current=get(f.a,"mCobraActionSheet");assertNotSame(old,current);
    choice.performClick();assertSame(current,get(f.a,"mCobraActionSheet"));
    assertEquals("",f.prefs.getString("cobra_multiview_arrangement.default.3",""));
    Fixture single=new Fixture(1,"mobile",480,900);call(single.a,"showCobraMultiTileActions",0);
    assertNull(((View)get(single.a,"mCobraActionSheet")).findViewWithTag("cobra_move_screen"));
  }
  @Test public void tapThresholdBackAndTinyWindowHaveSafeOutcomes()throws Exception{
    Fixture f=new Fixture(3,"cards",900,600);f.select("columns3");View source=f.view(2);float[] from=center(source),to=center(f.view(0));
    long t=SystemClock.uptimeMillis();touch(source,0,from[0],from[1],t,t);touch(source,2,to[0],to[1],t,t+10);touch(source,1,to[0],to[1],t,t+30);
    assertEquals(Arrays.asList("id0","id1","id2"),f.keys());f.unchanged();
    t=hold(source,from);touch(source,2,to[0],to[1],t,t+600);f.a.onBackPressed();touch(source,1,to[0],to[1],t,t+650);
    assertEquals(Arrays.asList("id0","id1","id2"),f.keys());f.unchanged();
    Fixture tiny=new Fixture(2,"mobile",150,140);tiny.select("equal2");source=tiny.view(1);from=center(source);to=center(tiny.view(0));t=hold(source,from);
    touch(source,2,to[0],to[1],t,t+600);touch(source,1,to[0],to[1],t,t+650);
    assertEquals(Arrays.asList("id1","id0"),tiny.keys());tiny.unchanged();
  }
  @Test public void existingProSportsAndOtherModeStripsKeepTheirExactOrder()throws Exception{
    Fixture f=new Fixture(2,"focus",480,900);Object six=get(f.a,"mCobraSix");
    Object features=Class.forName("com.projectinfinity.kodi.InfinityCobraFeatureRuntime").getConstructor(Context.class).newInstance(f.a);set(f.a,"mFeatures",features);
    Object channel=get(f.tiles.get(0),"channel");set(f.a,"mPlaying",channel);set(f.a,"mPlayerOverlay",f.root);
    for(String mode:new String[]{"focus","mobile","compact","cards","grid"})for(boolean sports:new boolean[]{true,false}){
      f.mode(mode);set(six,"fullContextOverlay",f.root);set(six,"fullContextKey",call(f.a,"cobraChannelKey",channel));
      set(six,"fullContextProfile",call(features,"activeProfileId"));set(six,"fullContextSports",sports);
      LinearLayout row=new LinearLayout(f.a);for(String label:new String[]{"Channels","Display","Multi-View","More"}){View v=new View(f.a);v.setTag(label);row.addView(v);}
      View result=(View)call(six,"controls",row,480);
      assertEquals(mode.equals("focus"),result instanceof android.widget.HorizontalScrollView);
      ArrayList<String> expected=new ArrayList<>(Arrays.asList("Channels","Display","Multi-View","cobra_fullscreen_pip"));
      if(mode.equals("focus")&&sports)expected.add("cobra_fullscreen_sports_stats");expected.add("More");
      ArrayList<String> actual=new ArrayList<>();for(int i=0;i<row.getChildCount();i++)actual.add(String.valueOf(row.getChildAt(i).getTag()));
      assertEquals(mode+" sports="+sports,expected,actual);
    }
    f.unchanged();
  }
  @Test public void everyPanePairSwapsAcrossAllFiveModesAndCounts()throws Exception{
    for(String mode:new String[]{"mobile","compact","cards","grid","focus"})for(int count=2;count<=4;count++){
      Fixture f=new Fixture(count,mode,900,600);f.select(count==2?"equal2":count==3?"columns3":"grid4");
      for(int a=0;a<count;a++)for(int b=a+1;b<count;b++){
        ArrayList<String> expected=new ArrayList<>(f.keys());Collections.swap(expected,expected.indexOf("id"+a),expected.indexOf("id"+b));
        View source=f.view(a);float[] from=center(source),to=center(f.view(b));long t=hold(source,from);
        touch(source,2,to[0],to[1],t,t+600);touch(source,1,to[0],to[1],t,t+650);measure(f.root,900,600);
        assertEquals(mode+" "+a+"->"+b,expected,f.keys());f.unchanged();
        for(Object tile:f.tiles)assertSame(f.canvas,((View)get(tile,"view")).getParent());
      }
    }
  }
  @Test public void profileSpecificChoiceRestoresAndProfileChangeCancelsDrag()throws Exception{
    Fixture f=new Fixture(3,"cards",900,600);
    Object features=Class.forName("com.projectinfinity.kodi.InfinityCobraFeatureRuntime").getConstructor(Context.class).newInstance(f.a);set(f.a,"mFeatures",features);
    String original=(String)call(features,"activeProfileId");f.select("columns3");
    View source=f.view(2);float[] from=center(source),to=center(f.view(0));long t=hold(source,from);touch(source,2,to[0],to[1],t,t+600);
    String other=(String)call(features,"createProfile","Other","",false);assertTrue((Boolean)call(features,"unlockAndSelectProfile",other,""));
    touch(source,1,to[0],to[1],t,t+650);assertEquals(Arrays.asList("id0","id1","id2"),f.keys());f.unchanged();
    int[] originalRect={4,5,6,7};assertSame(originalRect,CobraArrange.rect(f.a,originalRect,0,3,900,600,-1,false));
    assertTrue((Boolean)call(features,"unlockAndSelectProfile",original,""));
    assertArrayEquals(new int[]{0,0,300,600},CobraArrange.rect(f.a,originalRect,0,3,900,600,-1,false));
  }
}
