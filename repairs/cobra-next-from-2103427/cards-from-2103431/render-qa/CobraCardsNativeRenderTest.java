package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewConfiguration;
import android.widget.FrameLayout;
import android.widget.GridView;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.OutputStream;
import java.lang.reflect.*;
import java.lang.ref.WeakReference;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowActivity;
import org.robolectric.shadows.ShadowChoreographer;
import org.robolectric.shadows.ShadowSystem;

/** Actual accepted431 Activity/Card classes or the narrowly reviewed Card overlay.
 * Preview/QuickPeek terminal spies are used only for row-action dispatch tests.
 * More invokes its original native menu body. No decoder/provider/shutdown suite. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
  qualifiers="w359dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
  shadows={CobraCardsNativeRenderTest.RowTerminals.class})
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraCardsNativeRenderTest {
  static final List<Object> PREVIEWS=new ArrayList<>(),PEEKS=new ArrayList<>();
  static Object get(Object owner,String name)throws Exception{for(Class<?> type=owner.getClass();type!=null;type=type.getSuperclass())try{Field f=type.getDeclaredField(name);f.setAccessible(true);return f.get(owner);}catch(NoSuchFieldException absent){}throw new NoSuchFieldException(name);}
  static void set(Object owner,String name,Object value)throws Exception{Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
  static Object call(Object owner,String name,Object...args)throws Exception{
    for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){m.setAccessible(true);return m.invoke(owner,args);}
    throw new NoSuchMethodException(name);
  }
  static Object nested(String name,Object...args)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+name);
    for(Constructor<?> ctor:c.getDeclaredConstructors())if(ctor.getParameterCount()==args.length){ctor.setAccessible(true);return ctor.newInstance(args);}
    throw new NoSuchMethodException(name);
  }
  static void measure(View view,int width,int height){view.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));view.layout(0,0,width,height);}
  static boolean candidate(){return System.getProperty("cards.render.phase","").equals("CARDS_TILE_PROTOTYPE");}
  static void candidateOnly(){Assume.assumeTrue("Selected only for reviewed Cards prototype",candidate());}
  static Path output(){String value=System.getProperty("cards.render.output");assertNotNull("Explicit private artifact destination required",value);return Paths.get(value);}
  static void write(String name,JSONObject json)throws Exception{Files.createDirectories(output());Files.write(output().resolve(name+".json"),(json.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}
  static Rect box(View view){int[] point=new int[2];view.getLocationOnScreen(point);return new Rect(point[0],point[1],point[0]+view.getWidth(),point[1]+view.getHeight());}
  static Rect relative(View root,View child){Rect r=box(child),origin=box(root);r.offset(-origin.left,-origin.top);return r;}
  static JSONArray rectangle(Rect rect){return new JSONArray().put(rect.left).put(rect.top).put(rect.right).put(rect.bottom);}
  static void png(View view,String name)throws Exception{
    Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));
    Files.createDirectories(output());try(OutputStream stream=Files.newOutputStream(output().resolve(name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,stream));}finally{bitmap.recycle();}
  }
  static List<View> descendants(View root){List<View> out=new ArrayList<>();out.add(root);if(root instanceof ViewGroup){ViewGroup group=(ViewGroup)root;for(int i=0;i<group.getChildCount();i++)out.addAll(descendants(group.getChildAt(i)));}return out;}
  static View more(View card){View found=null;for(View view:descendants(card))if(view.getClass().getName().endsWith("CobraCardsTiles$MoreView")){assertNull(found);found=view;}assertNotNull(found);return found;}
  static ImageView logo(View card){for(View view:descendants(card))if(view.getClass().getName().endsWith("CobraCardsTiles$OwnedLogo"))return (ImageView)view;throw new AssertionError("Native Cards logo view missing");}
  static TextView fallback(View card,TextView nativeTitle,TextView nativeNow,TextView category,TextView time,String label){for(View v:descendants(card))if(v instanceof TextView&&v!=nativeTitle&&v!=nativeNow&&v!=category&&v!=time&&((TextView)v).getText().toString().equals(label))return (TextView)v;throw new AssertionError("Bound initials fallback missing");}
  @Before public void controlledHost(){
    String phase=System.getProperty("cards.render.phase","");assertTrue("Explicit Cards phase required",phase.equals("ACCEPTED431_BASELINE")||phase.equals("CARDS_TILE_PROTOTYPE"));
    ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));
    org.robolectric.shadows.ShadowDisplay display=Shadows.shadowOf(org.robolectric.shadows.ShadowDisplay.getDefaultDisplay());display.setWidth(941);display.setRealWidth(941);display.setHeight(1672);display.setRealHeight(1672);
    assertTrue(SystemClock.setCurrentTimeMillis(1793318400000L));Locale.setDefault(Locale.US);TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
    PREVIEWS.clear();PEEKS.clear();
  }
  @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
  public static class RowTerminals extends ShadowActivity {
    @Implementation protected void selectGuidePreview(Object channel){PREVIEWS.add(channel);}
    @Implementation protected void cobraShowQuickPeek(Object channel,Object anchor){PEEKS.add(channel);}
  }
  static final class RecordIo extends AbstractExecutorService {
    final List<Runnable> admitted=new ArrayList<>();
    public void execute(Runnable runnable){admitted.add(runnable);}
    public void shutdown(){throw new AssertionError("Shutdown is not selected");}
    public List<Runnable> shutdownNow(){throw new AssertionError("Shutdown is not selected");}
    public boolean isShutdown(){return false;}public boolean isTerminated(){return false;}
    public boolean awaitTermination(long time,TimeUnit unit){throw new AssertionError("Shutdown is not selected");}
  }
  static final class Fixture {
    final ActivityController<InfinityLiveActivity> controller=Robolectric.buildActivity(InfinityLiveActivity.class);
    final InfinityLiveActivity a=controller.get();
    final LinearLayout root,stage;final RecordIo io=new RecordIo();
    final List<Object> channels;
    final long now=ShadowSystem.currentTimeMillis();
    final Object epg;
    Fixture(int count,float font)throws Exception{
      a.setTheme(android.R.style.Theme_Material_NoActionBar);
      Configuration configuration=new Configuration(a.getResources().getConfiguration());configuration.fontScale=font;a.getResources().updateConfiguration(configuration,a.getResources().getDisplayMetrics());
      SharedPreferences prefs=a.getSharedPreferences("cards-render-"+UUID.randomUUID(),Context.MODE_PRIVATE);prefs.edit().putString("cobra_appearance_mode","dark").putString("guide_view_mode","cards").putString("cobra_primary_view","guide").commit();
      set(a,"mPrefs",prefs);set(a,"mTheme",nested("Theme"));set(a,"mUi",nested("UiContract"));InfinityCobraFeatureRuntime features=new InfinityCobraFeatureRuntime(a);assertTrue(features.unlockAndSelectProfile("default",""));set(a,"mFeatures",features);set(a,"mIo",io);
      set(a,"mCobraGuideStyle","cards");set(a,"mCobraGuideRoute","channels");set(a,"mCategory","ALL");set(a,"mSearch","");set(a,"mCobraGuideSource","");
      set(a,"mCobraPreviewAutoplayAllowed",false);set(a,"mCobraProActive",false);
      channels=(List<Object>)get(a,"mChannels");
      ((List<Object>)get(a,"mSources")).add(nested("LiveSource","qa","m3u","Synthetic QA","","","","https://example.invalid/playlist",""));
      epg=nested("CobraEpgData");set(epg,"identity",call(a,"cobraEpgIdentity",((List)get(a,"mSources")).get(0)));set(epg,"fetched",now);((Map<String,Object>)get(a,"mCobraEpg")).put("qa",epg);
      for(int i=0;i<count;i++){
        Object channel=channel("qa:"+i,i==0?"Alpha":"Synthetic channel "+i,"Synthetic group",i==0?"epg-a":"epg-"+i,"");channels.add(channel);
        if(i<6 && i!=2)programme(i==0?"epg-a":"epg-"+i,"Current programme "+i,now-900000L,now+1800000L);
      }
      set(a,"mGuidePreviewChannel",channels.get(Math.min(3,count-1)));
      call(a,"buildShell");call(a,"cobraShowGuideShell");root=(LinearLayout)get(a,"mRoot");stage=(LinearLayout)get(a,"mStage");controller.visible();
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));
      assertTrue(((View)get(a,"mCobraGuideShell")).isAttachedToWindow());assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));
    }
    Object channel(String id,String name,String group,String epgId,String icon)throws Exception{return nested("Channel",id,name,group,epgId,icon,"", "qa",Collections.emptyMap());}
    void programme(String id,String title,long start,long stop)throws Exception{
      Object programme=nested("GuideProgram");set(programme,"channel",id);set(programme,"title",title);set(programme,"description","Synthetic guide description");set(programme,"start",start);set(programme,"stop",stop);
      ArrayList<Object> programs=new ArrayList<>();programs.add(programme);((Map<String,ArrayList<Object>>)get(epg,"programs")).put(id,programs);
    }
    void shell(int width,int height)throws Exception{call(a,"cobraShowGuideShell");measure(a.getWindow().getDecorView(),width,height);measure(root,width,height);measure(root,width,height);}
    LinearLayout publishFirst(Object channel)throws Exception{
      GridView grid=(GridView)get(a,"mCobraGuideList");channels.set(0,channel);((List<Object>)get(grid.getAdapter(),"channels")).set(0,channel);((BaseAdapter)grid.getAdapter()).notifyDataSetChanged();for(int frame=0;frame<4;frame++)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));assertEquals("Host window must match physical fixture pixels before fresh target observation",941,root.getWidth());
      LinearLayout card=(LinearLayout)((GridView)get(a,"mCobraGuideList")).getChildAt(0);assertEquals("Published adapter identity", "cobra-channel:"+get(channel,"id"),card.getTag());return card;
    }
    LinearLayout standalone(Object channel,int width)throws Exception{
      GridView grid=new GridView(a);grid.setNumColumns(1);grid.setColumnWidth(width);grid.setStretchMode(GridView.NO_STRETCH);measure(grid,width,600);set(a,"mCobraGuideList",grid);
      Object model=nested("CobraModeLayout",Math.max(1,Math.round(width/a.getResources().getDisplayMetrics().density)),600);set(model,"columns",1);((int[])get(model,"browser"))[2]=Math.max(1,Math.round(width/a.getResources().getDisplayMetrics().density));set(a,"mCobraModeLayout",model);
      LinearLayout card=(LinearLayout)nested("CobraPosterChannelCard",a);call(card,"bind",channel,0);
      while(stage.getChildCount()>2)stage.removeViewAt(2);FrameLayout holder=new FrameLayout(a);holder.addView(card,new FrameLayout.LayoutParams(width,card.getLayoutParams().height));stage.addView(holder,new LinearLayout.LayoutParams(width,700));
      measure(root,width,900);measure(root,width,900);return card;
    }
  }
  @Test public void renderNativeCards941()throws Exception{
    Fixture f=new Fixture(20226,1);f.shell(941,1672);for(int frame=0;frame<24;frame++)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));assertEquals("Real host window width",941,f.root.getWidth());assertEquals("Real host window height",1672,f.root.getHeight());Object list=get(f.a,"mCobraGuideList");assertTrue(list instanceof GridView);
    GridView grid=(GridView)list;assertEquals(20226,grid.getAdapter().getCount());assertTrue(grid.getChildCount()>0);
    assertEquals("Actual native Cards adapter", "com.projectinfinity.kodi.InfinityLiveActivity$21",grid.getAdapter().getClass().getName());
    JSONObject report=new JSONObject().put("phase",System.getProperty("cards.render.phase")).put("viewport",new JSONArray(new int[]{941,1672}))
      .put("density_dpi",f.a.getResources().getDisplayMetrics().densityDpi).put("fontScale",1).put("inventory",20226).put("coordinate_space","NATIVE_APP_ROOT_LOCAL_PIXELS")
      .put("builder","ORIGINAL_NATIVE_cobraShowGuideShell").put("browser_alpha",((View)get(f.a,"mCobraGuideBrowser")).getAlpha()).put("frame_handoff","PAUSED_MANUAL_BOUNDED_24x16ms; no forced alpha").put("preview_video","NOT_PLAYED; DYNAMIC_REGION")
      .put("theme","CONTROLLED_BUILTIN_DARK; NOT_USER_DEVICE_THEME_IMPORT").put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN");
    JSONArray regions=new JSONArray();
    for(String name:new String[]{"mCobraModeToolbar","mCobraGuideVideo","mCobraGuideDetails","mCobraGuideBrowser"})regions.put(new JSONObject().put("native_field",name).put("bounds",rectangle(relative(f.root,(View)get(f.a,name)))));
    report.put("native_regions",regions);JSONArray cards=new JSONArray();
    for(int i=0;i<grid.getChildCount();i++){
      View card=grid.getChildAt(i);JSONObject row=new JSONObject().put("bounds",rectangle(relative(f.root,card))).put("selected",card.isSelected()).put("class",card.getClass().getName());JSONArray dynamic=new JSONArray();
      for(String name:new String[]{"category","title","now","time","progress"}){View v=(View)get(card,name);if(v.getVisibility()==View.VISIBLE)dynamic.put(new JSONObject().put("field",name).put("bounds",rectangle(relative(f.root,v))));}
      for(View v:descendants(card))if(v instanceof ImageView)dynamic.put(new JSONObject().put("field","provider_logo").put("bounds",rectangle(relative(f.root,v))));
      cards.put(row.put("dynamic_regions",dynamic));
    }
    report.put("cards",cards);JSONArray hierarchy=new JSONArray();
    for(View view:descendants(f.root)){
      JSONObject node=new JSONObject().put("class",view.getClass().getName()).put("bounds",rectangle(relative(f.root,view))).put("visibility",view.getVisibility()).put("selected",view.isSelected()).put("clickable",view.isClickable()).put("description",view.getContentDescription()==null?"":view.getContentDescription());
      if(view instanceof TextView)node.put("text",((TextView)view).getText()).put("text_size_px",((TextView)view).getTextSize());hierarchy.put(node);
    }
    report.put("actual_hierarchy",hierarchy).put("submitted_provider_IO_bodies_NOT_executed",f.io.admitted.size());png(f.root,"cards-941-native");write("CARDS-NATIVE-RENDER",report);
  }
  @Test public void nativeCardRecycleAndCurrentProgramme()throws Exception{
    candidateOnly();Fixture f=new Fixture(2,1);Object a=f.channel("qa:a","Alpha","QA | Group","epg-a","");Object b=f.channel("qa:b","Very long channel name that must ellipsize rather than collide with other Cards targets","QA | Other","missing","");
    ((List<Object>)get(f.a,"mChannels")).add(a);((List<Object>)get(f.a,"mChannels")).add(b);f.programme("epg-a","Current programme 0",f.now,f.now+1800000L);set(f.a,"mGuidePreviewChannel",a);LinearLayout card=f.standalone(a,448);
    assertTrue(card.hasOnClickListeners());assertTrue(card.isLongClickable());assertEquals("cobra-channel:qa:a",card.getTag());assertTrue(card.isSelected());
    assertEquals("QA | GROUP",((TextView)get(card,"category")).getText().toString());assertEquals("Current programme 0",((TextView)get(card,"now")).getText().toString());assertEquals(View.VISIBLE,((ProgressBar)get(card,"progress")).getVisibility());
    String schedule=((TextView)get(card,"time")).getText().toString();assertEquals("One native date prefix for same-day interval",1,schedule.length()-schedule.replace("•","").length());
    call(card,"bind",b,1);measure(f.root,448,900);assertEquals("cobra-channel:qa:b",card.getTag());assertFalse(card.isSelected());assertEquals(View.GONE,((ProgressBar)get(card,"progress")).getVisibility());
    assertEquals(call(f.a,"cobraGuideStatus",b),((TextView)get(card,"now")).getText().toString());set(f.a,"mGuidePreviewChannel",b);call(card,"refreshPlaying");assertTrue(card.isSelected());
    f.programme("missing","Expired programme",f.now-172800000L,f.now-86400000L);call(card,"refreshPlaying");assertEquals(View.GONE,((ProgressBar)get(card,"progress")).getVisibility());png(card,"tile-recycled-missing");
  }
  @Test public void nativeCardDimensionsAndCornerTouch()throws Exception{
    candidateOnly();JSONArray cases=new JSONArray();
    for(float font:new float[]{1,2})for(int width:new int[]{328,448}){
      Fixture f=new Fixture(1,font);Object channel=f.channel("qa:a","Alpha","QA | Group","epg-a","");((List<Object>)get(f.a,"mChannels")).add(channel);LinearLayout card=f.standalone(channel,width);
      View more=more(card);Rect corner=box(more);for(String key:new String[]{"category","title","now"})assertFalse("More pointer bounds cannot cover "+key,Rect.intersects(corner,box((View)get(card,key))));
      cases.put(new JSONObject().put("width",width).put("fontScale",font).put("card_bounds",rectangle(box(card))).put("more_bounds",rectangle(corner)));
    }
    Fixture real=new Fixture(2,1);real.shell(941,1672);for(int frame=0;frame<24;frame++)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));Object rebound=real.channel("qa:rebound","Rebound current channel","Synthetic group","missing","");LinearLayout first=real.publishFirst(rebound);
    View moreTarget=more(first);Rect corner=box(moreTarget),visibleCorner=new Rect();boolean visible=moreTarget.getGlobalVisibleRect(visibleCorner);final JSONArray received=new JSONArray();
    moreTarget.setOnTouchListener((view,event)->{try{received.put(new JSONObject().put("action",event.getActionMasked()).put("x",event.getX()).put("y",event.getY()).put("uptime",SystemClock.uptimeMillis()).put("event_time",event.getEventTime()).put("pressed_before_default",view.isPressed()).put("private_flags_before_default",get(view,"mPrivateFlags")).put("ignore_up",get(view,"mIgnoreNextUpEvent")).put("performed_long_press",get(view,"mHasPerformedLongPress")));}catch(Exception error){throw new AssertionError(error);}return false;});final JSONArray callbacks=new JSONArray();
    Object info=get(moreTarget,"mListenerInfo");View.OnClickListener original=(View.OnClickListener)get(info,"mOnClickListener");assertNotNull(original);
    moreTarget.setOnClickListener(view->{try{Object owner=((WeakReference<?>)get(original,"owner")).get();callbacks.put(new JSONObject().put("original_listener",original.getClass().getName()).put("owner_alive",owner!=null).put("bound_channel_nonnull",get(original,"bound")!=null).put("card_attached",((View)get(original,"card")).isAttachedToWindow()).put("native_mode",get(owner,"mCobraGuideStyle")).put("on_main_thread",Looper.myLooper()==Looper.getMainLooper()));}catch(Exception error){throw new AssertionError(error);}original.onClick(view);});
    JSONObject diagnostic=new JSONObject().put("old_card_attached",first.isAttachedToWindow()).put("more_attached",moreTarget.isAttachedToWindow()).put("more_clickable",moreTarget.isClickable()).put("more_enabled",moreTarget.isEnabled()).put("native_style",get(real.a,"mCobraGuideStyle"))
      .put("same_current_grid_child",((GridView)get(real.a,"mCobraGuideList")).getChildAt(0)==first).put("has_click_listener",moreTarget.hasOnClickListeners()).put("focusable",moreTarget.isFocusable()).put("focusable_touch_mode",moreTarget.isFocusableInTouchMode()).put("in_touch_mode",moreTarget.isInTouchMode()).put("has_focus",moreTarget.hasFocus()).put("browser_alpha",((View)get(real.a,"mCobraGuideBrowser")).getAlpha()).put("full_more_bounds",rectangle(corner)).put("global_visible_more",visible).put("visible_more_bounds",rectangle(visibleCorner));
    png(real.root,"before-corner-press");write("MORE-BEFORE",diagnostic);assertTrue("Current More must have visible native bounds before any press",visible&&visibleCorner.width()>8&&visibleCorner.height()>8);
    int[] origin=new int[2];real.root.getLocationOnScreen(origin);diagnostic.put("root_screen_origin",new JSONArray().put(origin[0]).put(origin[1])).put("root_translation_x",real.root.getTranslationX()).put("root_translation_y",real.root.getTranslationY()).put("root_scale_x",real.root.getScaleX()).put("root_scale_y",real.root.getScaleY()).put("frame_mode","PAUSED_MANUAL_BOUNDED_24x16ms_AFTER_NATIVE_SHELL");write("MORE-BEFORE",diagnostic);float x=visibleCorner.exactCenterX()-origin[0],y=visibleCorner.exactCenterY()-origin[1];long t=SystemClock.uptimeMillis();
    for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}){if(action==MotionEvent.ACTION_UP)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));MotionEvent e=MotionEvent.obtain(t,SystemClock.uptimeMillis(),action,x,y,0);e.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);try{boolean consumed=real.root.dispatchTouchEvent(e);diagnostic.put("dispatch_"+action,new JSONObject().put("consumed",consumed).put("received",received).put("pressed_after_default",moreTarget.isPressed()).put("private_flags_after_default",get(moreTarget,"mPrivateFlags")).put("root_bounds",rectangle(box(real.root))).put("more_bounds",rectangle(box(moreTarget))).put("still_current_card",((GridView)get(real.a,"mCobraGuideList")).getChildAt(0)==first));write("MORE-EVENT-"+action,diagnostic);}finally{e.recycle();}}
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));View sheet=(View)get(real.a,"mCobraActionSheet");
    diagnostic.put("received_more_actions",received).put("actual_original_click_callbacks",callbacks).put("more_pressed_after",moreTarget.isPressed()).put("has_focus_after",moreTarget.hasFocus()).put("card_attached_after",first.isAttachedToWindow()).put("menu_opened",sheet!=null).put("preview_terminal_count",PREVIEWS.size()).put("peek_terminal_count",PEEKS.size()).put("root_screen_origin",new JSONArray().put(origin[0]).put(origin[1])).put("coordinate_root_local",new JSONArray().put(x).put(y));write("MORE-AFTER",diagnostic);png(real.root,"after-corner-press");assertNotNull("Actual original native channel menu must open",sheet);assertTrue("Native menu attached",sheet.isAttachedToWindow());
    boolean nativeHeading=false,boundName=false;for(View v:descendants(sheet))if(v instanceof TextView){String text=((TextView)v).getText().toString();nativeHeading|=text.equals("Channel actions");boundName|=text.contains("Rebound current channel");}
    assertTrue("Original native menu heading",nativeHeading);assertTrue("Current bound channel named in native menu",boundName);assertTrue(PREVIEWS.isEmpty());assertTrue(PEEKS.isEmpty());
    png(real.root,"native-more-menu");
    Fixture row=new Fixture(2,1);row.shell(941,1672);for(int frame=0;frame<24;frame++)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));Object expected=row.channel("qa:rebound-row","Rebound row","Synthetic group","missing","");LinearLayout nativeRow=row.publishFirst(expected);
    View title=(View)get(nativeRow,"title");Rect titleBox=box(title);row.root.getLocationOnScreen(origin);x=titleBox.exactCenterX()-origin[0];y=titleBox.exactCenterY()-origin[1];t=SystemClock.uptimeMillis();
    for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}){if(action==MotionEvent.ACTION_UP)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));MotionEvent e=MotionEvent.obtain(t,SystemClock.uptimeMillis(),action,x,y,0);e.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);try{assertTrue(row.root.dispatchTouchEvent(e));}finally{e.recycle();}}
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));assertEquals(1,PREVIEWS.size());assertSame("Native click callback owns rebound channel",expected,PREVIEWS.get(0));
    final JSONArray longReceipts=new JSONArray();nativeRow.setOnTouchListener((view,event)->{try{longReceipts.put(new JSONObject().put("action",event.getActionMasked()).put("x",event.getX()).put("y",event.getY()).put("uptime",SystemClock.uptimeMillis()).put("pressed_before_default",view.isPressed()).put("attach_count",get(view,"mWindowAttachCount")));}catch(Exception error){throw new AssertionError(error);}return false;});
    Rect programmeBox=box((View)get(nativeRow,"now"));x=programmeBox.exactCenterX()-origin[0];y=programmeBox.exactCenterY()-origin[1];t=SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(t,t,MotionEvent.ACTION_DOWN,x,y,0);down.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);try{assertTrue(row.root.dispatchTouchEvent(down));}finally{down.recycle();}
    JSONArray hold=new JSONArray();int holdDuration=ViewConfiguration.getLongPressTimeout()+32;for(int elapsed=0;elapsed<holdDuration;elapsed+=16){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(Math.min(16,holdDuration-elapsed)));if(elapsed%96==0 || elapsed+16>=holdDuration)hold.put(new JSONObject().put("elapsed",SystemClock.uptimeMillis()-t).put("pressed",nativeRow.isPressed()).put("attach_count",get(nativeRow,"mWindowAttachCount")).put("attached",nativeRow.isAttachedToWindow()).put("same_current_card",((GridView)get(row.a,"mCobraGuideList")).getChildAt(0)==nativeRow).put("pending_longpress",get(nativeRow,"mPendingCheckForLongPress")!=null).put("performed_longpress",get(nativeRow,"mHasPerformedLongPress")).put("peeks",PEEKS.size()));}
    MotionEvent up=MotionEvent.obtain(t,SystemClock.uptimeMillis(),MotionEvent.ACTION_UP,x,y,0);up.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);try{row.root.dispatchTouchEvent(up);}finally{up.recycle();}write("NATIVE-ROW-LONGPRESS",new JSONObject().put("received",longReceipts).put("hold",hold).put("window_focus",nativeRow.hasWindowFocus()).put("touch_mode",nativeRow.isInTouchMode()).put("long_press_timeout",ViewConfiguration.getLongPressTimeout()).put("peeks",PEEKS.size()));
    assertEquals(1,PEEKS.size());assertSame("Native long-press callback owns rebound channel",expected,PEEKS.get(0));
    write("CARD-BOUND-TARGETS",new JSONObject().put("cases",cases).put("menu","ACTUAL_NATIVE_BODY; NOT_SHADOWED").put("native_click_longpress","ACTUAL_MOTIONEVENTS; ONLY_PREVIEW_AND_QUICKPEEK_TERMINALS_SPIED").put("physical_Fold","NOT_RUN"));
  }
  @Test public void nativeCardLogoRecycle()throws Exception{
    candidateOnly();Fixture f=new Fixture(1,1);String url="https://example.invalid/cards-qa-logo-a";
    Object a=f.channel("qa:a","A","QA","epg-a",url),b=f.channel("qa:b","B","QA","missing","");
    Bitmap bitmap=Bitmap.createBitmap(12,8,Bitmap.Config.ARGB_8888);bitmap.eraseColor(Color.CYAN);((Map<String,Bitmap>)get(f.a,"mCobraSportsLogos")).put(url,bitmap);
    LinearLayout card=f.standalone(a,448);ImageView image=logo(card);TextView empty=fallback(card,(TextView)get(card,"title"),(TextView)get(card,"now"),(TextView)get(card,"category"),(TextView)get(card,"time"),"A");assertEquals(View.GONE,empty.getVisibility());assertNotNull(image.getDrawable());call(card,"bind",b,1);assertEquals("B",empty.getText().toString());assertEquals(View.VISIBLE,empty.getVisibility());assertNull("Blank URI must clear recycled artwork",image.getDrawable());
    CobraLogoRequests.deliver(f.a,url,bitmap,image);assertNull("Late old-URI publication cannot fill rebound blank tile",image.getDrawable());
    ViewGroup parent=(ViewGroup)card.getParent();ViewGroup.LayoutParams params=card.getLayoutParams();parent.removeView(card);parent.addView(card,params);assertNull("Old attach binding cannot restore old artwork",image.getDrawable());
    call(card,"bind",a,0);assertNotNull("Legitimate cached same-URI image restores",image.getDrawable());
    write("CARD-LOGO-RECYCLE",new JSONObject().put("status","PASS_CONTROLLED_REAL_PRODUCTION_BINDING_AND_DELIVER_PATH").put("network","NOT_RUN; CACHE_AND_CONTROLLED_COMPLETION").put("physical_Fold","NOT_RUN"));
  }
}
