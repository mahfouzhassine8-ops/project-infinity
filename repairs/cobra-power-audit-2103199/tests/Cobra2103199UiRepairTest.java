package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.media3.common.C;
import androidx.media3.common.text.Cue;
import androidx.media3.common.text.CueGroup;
import java.util.Collections;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Android view/animation/cue-adapter regressions with a controlled player.
 * No physical display, hardware decoder, subtitle transport or SystemUI claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103199UiRepairTest {
  CobraNavigationUiTest ui;
  InfinityLiveActivity a;

  static Object get(Object owner,String name)throws Exception{return CobraNavigationUiTest.get(owner,name);}
  static void put(Object owner,String name,Object value)throws Exception{CobraNavigationUiTest.put(owner,name,value);}
  static Object call(Object owner,String name,Object... values)throws Exception{return CobraNavigationUiTest.call(owner,name,values);}
  SharedPreferences prefs()throws Exception{return (SharedPreferences)get(a,"mPrefs");}
  TextView findText(View view,String value){
    if(view instanceof TextView&&value.contentEquals(((TextView)view).getText()))return (TextView)view;
    if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){
      TextView found=findText(((ViewGroup)view).getChildAt(i),value);if(found!=null)return found;
    }
    return null;
  }
  ScrollView scroll(View view){
    if(view instanceof ScrollView)return (ScrollView)view;
    if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){
      ScrollView found=scroll(((ViewGroup)view).getChildAt(i));if(found!=null)return found;
    }
    return null;
  }
  static double luminance(int color){
    double[] v={Color.red(color)/255d,Color.green(color)/255d,Color.blue(color)/255d};
    for(int i=0;i<3;i++)v[i]=v[i]<=.04045?v[i]/12.92:Math.pow((v[i]+.055)/1.055,2.4);
    return .2126*v[0]+.7152*v[1]+.0722*v[2];
  }
  static double contrast(int first,int second){double a=luminance(first),b=luminance(second);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);}
  static int renderedFill(Drawable drawable,int[] state){
    drawable.setState(state);drawable.jumpToCurrentState();drawable.setBounds(0,0,160,100);
    Bitmap image=Bitmap.createBitmap(160,100,Bitmap.Config.ARGB_8888);image.eraseColor(Color.MAGENTA);
    drawable.draw(new Canvas(image));int color=image.getPixel(80,50);image.recycle();return color;
  }

  static final class RulerCanvas extends Canvas {
    final java.util.ArrayList<String> labels=new java.util.ArrayList<>();
    final java.util.ArrayList<float[]> positions=new java.util.ArrayList<>();
    RulerCanvas(Bitmap bitmap){super(bitmap);}
    @Override public void drawText(String text,float x,float y,Paint paint){
      if(!"CHANNEL".equals(text)&&!text.isEmpty()){
        labels.add(text);positions.add(new float[]{x,y,paint.measureText(text),paint.getTextSize()});
      }
      super.drawText(text,x,y,paint);
    }
  }

  @Before public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);
  }
  @After public void after()throws Exception{
    if(a!=null)ui.clean(a);CobraVisualRenderer.clients.clear();
  }

  @Test public void fullscreenAndMultiDetailRowsHaveReadableActualSurfaceInEveryPalette()throws Exception{
    for(String appearance:new String[]{"light","dark","oled"})for(String context:new String[]{"browse","player","multi"}){
      prefs().edit().putString("cobra_appearance_mode",appearance).commit();
      put(a,"mPlayerOverlay","player".equals(context)?new FrameLayout(a):null);
      put(a,"mMultiOverlay","multi".equals(context)?new FrameLayout(a):null);
      LinearLayout row=(LinearLayout)call(a,"cobraDetailRow","settings","Readable title","Readable supporting text","contrast-fixture",false,(Runnable)()->{});
      TextView title=findText(row,"Readable title"),detail=findText(row,"Readable supporting text");
      assertNotNull(title);assertNotNull(detail);
      for(int[] state:new int[][]{{android.R.attr.state_enabled},{android.R.attr.state_enabled,android.R.attr.state_focused},{android.R.attr.state_enabled,android.R.attr.state_selected}}){
        int fill=renderedFill(row.getBackground(),state);
        assertTrue(appearance+"/"+context+" title actual contrast "+contrast(title.getCurrentTextColor(),fill),contrast(title.getCurrentTextColor(),fill)>=4.5);
        assertTrue(appearance+"/"+context+" detail actual contrast "+contrast(detail.getCurrentTextColor(),fill),contrast(detail.getCurrentTextColor(),fill)>=4.5);
      }
    }
    put(a,"mPlayerOverlay",null);put(a,"mMultiOverlay",null);
  }

  @Test public void focusInterruptingStaggeredEntryRestoresPositionWithoutInheritedDelay()throws Exception{
    call(a,"showSettings");ui.measure(a,412,915);
    ScrollView scroll=scroll((View)get(a,"mStage"));assertNotNull(scroll);
    LinearLayout list=(LinearLayout)scroll.getChildAt(0);Button target=null;
    for(int i=10;i<Math.min(14,list.getChildCount());i++)if(list.getChildAt(i) instanceof Button){target=(Button)list.getChildAt(i);break;}
    assertNotNull(target);assertNotNull(target.getOnFocusChangeListener());
    // Restart the existing entry callback, then inject a framework focus event
    // before this late-staggered row reaches its final translation/alpha.
    call(a,"cobraAnimateChildrenIn",list);ui.frames(1);
    assertTrue("Fixture must interrupt an unfinished translation",target.getTranslationY()>0f);
    target.getOnFocusChangeListener().onFocusChange(target,true);ui.frames(10);
    assertEquals(0f,target.getTranslationY(),.01f);assertEquals(0f,target.getTranslationX(),.01f);
    assertEquals(0L,target.animate().getStartDelay());assertEquals(1f,target.getAlpha(),.01f);
    assertEquals(1.018f,target.getScaleX(),.006f);
    target.getOnFocusChangeListener().onFocusChange(target,false);ui.frames(8);
    assertEquals(1f,target.getScaleX(),.006f);assertEquals(0f,target.getTranslationY(),.01f);
  }

  @Test public void lastProfileRemainsReachableInShortLandscapeViewport()throws Exception{
    JSONArray profiles=new JSONArray();
    for(int i=0;i<30;i++)profiles.put(new JSONObject().put("id","audit-"+i).put("name","Audit profile "+i).put("pin_hash","").put("adult_locked",false));
    a.getSharedPreferences(InfinityCobraFeatureRuntime.PREFS,Context.MODE_PRIVATE).edit().putString("profiles",profiles.toString()).putString("active_profile","audit-0").commit();
    RuntimeEnvironment.setQualifiers("w900dp-h420dp-land-mdpi");call(a,"showProfiles");ui.measure(a,900,420);
    ScrollView scroll=scroll((View)get(a,"mStage"));assertNotNull("Profiles require reachable scrolling",scroll);
    LinearLayout list=(LinearLayout)scroll.getChildAt(0);assertEquals(31,list.getChildCount());
    assertTrue(list.getHeight()>scroll.getHeight());scroll.setSmoothScrollingEnabled(false);scroll.fullScroll(View.FOCUS_DOWN);ui.measure(a,900,420);
    assertTrue("Bottom scroll must move content",scroll.getScrollY()>0);
    View last=list.getChildAt(30);Rect visible=new Rect();assertTrue("Last profile visible after scrolling",last.getGlobalVisibleRect(visible));
    assertTrue(visible.height()>0);assertTrue(last.isClickable());
    assertEquals("○  Audit profile 29",((TextView)last).getText().toString());
  }

  @Test public void explicitPreviewCaptionsOverrideOnlyActiveSessionAndKeepSavedOffDefault()throws Exception{
    call(a,"cobraOpenLiveTv");ui.measure(a,412,915);
    CobraHealthUiTest.PlayerDouble fake=new CobraHealthUiTest.PlayerDouble(a);
    CobraHealthUiTest health=new CobraHealthUiTest();
    Object binding=health.attach(a,fake);
    Object channel=((List<?>)get(a,"mChannels")).get(0);
    String key=(String)call(a,"cobraPreferenceKey",channel);Object saved=call(a,"cobraReadPreferences",key);put(saved,"subtitles","off");
    assertEquals(true,call(a,"cobraSavePreferences",channel,key,saved,false));
    assertTrue(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    CueGroup cues=new CueGroup(Collections.singletonList(new Cue.Builder().setText("Supplied stream caption").build()),0L);
    View overlay=(View)get(binding,"captions");call(binding,"onCues",cues);assertEquals(View.GONE,overlay.getVisibility());
    call(a,"toggleCobraPreviewCaptions");assertFalse(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    call(binding,"onCues",cues);assertEquals("Explicit active choice must render delivered cues",View.VISIBLE,overlay.getVisibility());
    assertEquals("off",new JSONObject(prefs().getString(key,"")).getString("subtitles"));
    call(a,"toggleCobraPreviewCaptions");call(binding,"onCues",cues);assertEquals(View.GONE,overlay.getVisibility());
    // Reapplying the saved preference uses the original session initializer.
    call(a,"cobraApplyChannelTracks",binding);assertTrue(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    assertEquals("off",get(call(a,"cobraReadPreferences",key),"subtitles"));
  }

  @Test public void staleSourceSubscriptionFailureCannotOverwriteDifferentCurrentSource()throws Exception{
    Object first=CobraNavigationUiTest.construct("LiveSource","source-a","xtream","A","invalid://local-fixture","fixture","fixture","","");
    Object second=CobraNavigationUiTest.construct("LiveSource","source-b","m3u","B","","","","","");
    put(a,"mActiveSource",first);call(a,"showSettings");
    CobraNavigationUiTest.PendingIo io=(CobraNavigationUiTest.PendingIo)get(a,"mIo");assertFalse(io.tasks.isEmpty());
    put(a,"mActiveSource",second);call(a,"showSettings");
    TextView label=(TextView)a.getWindow().getDecorView().findViewWithTag("cobra_subscription_status");
    String current=label.getText().toString();assertTrue(current.contains("Expiration not provided"));
    // The deliberately invalid scheme fails immediately without network access.
    // Execute A's already-captured task only after B's Settings has replaced it.
    io.drain();ui.frames(2);assertEquals(current,label.getText().toString());
    // A current-source request must still report its failure, not get dropped.
    put(a,"mActiveSource",first);call(a,"showSettings");io.drain();ui.frames(2);
    TextView currentA=(TextView)a.getWindow().getDecorView().findViewWithTag("cobra_subscription_status");
    assertEquals("SUBSCRIPTION • Status unavailable",currentA.getText().toString());
  }

  @Test public void geometryChangeKeepsMoviesPendingWorkAndRecordingsViewInsteadOfOpeningLive()throws Exception{
    call(a,"showMovies");Object root=get(a,"mRoot"),stage=get(a,"mStage");
    Object navigation=get(a,"mCobraNavigation");long epoch=((Number)call(navigation,"current")).longValue();
    RuntimeEnvironment.setQualifiers("w900dp-h420dp-land-mdpi");
    a.onConfigurationChanged(new Configuration(a.getResources().getConfiguration()));ui.measure(a,900,420);
    assertSame(root,get(a,"mRoot"));assertSame(stage,get(a,"mStage"));
    assertEquals("COBRA • MOVIES",get(a,"mCobraStageTitle"));
    assertEquals("Geometry must not invalidate the pending Movies response",epoch,((Number)call(navigation,"current")).longValue());
    ((CobraNavigationUiTest.PendingIo)get(a,"mIo")).drain();ui.frames(2);
    assertNotNull(findText((View)get(a,"mStage"),"No titles returned by enabled Xtream providers."));
    call(a,"showRecordings");LinearLayout recordingStage=(LinearLayout)get(a,"mStage");View content=recordingStage.getChildAt(2);
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");
    a.onConfigurationChanged(new Configuration(a.getResources().getConfiguration()));ui.measure(a,412,915);
    assertSame(recordingStage,get(a,"mStage"));assertSame(content,recordingStage.getChildAt(2));
    assertEquals("COBRA • RECORDINGS",get(a,"mCobraStageTitle"));
  }

  @Test public void phoneDpadCanFocusExistingSettingsActionsAndContractCanStillDisableFocus()throws Exception{
    assertFalse(a.getPackageManager().hasSystemFeature("android.software.leanback"));
    Object contract=get(a,"mUi");put(contract,"dpadFocusEnabled",true);
    call(a,"showSettings");ui.measure(a,412,915);
    View sources=a.getWindow().getDecorView().findViewWithTag("cobra_tv_sources");assertNotNull(sources);
    assertTrue("Existing settings must accept non-TV D-pad focus",sources.isFocusable());
    assertFalse("Touch focus behavior remains unchanged",sources.isFocusableInTouchMode());
    assertTrue(sources.requestFocusFromTouch());assertTrue(sources.hasFocus());
    assertTrue(sources.performClick());assertNotNull(findText((View)get(a,"mStage"),"+  ADD TV SOURCE"));
    put(contract,"dpadFocusEnabled",false);Button disabled=(Button)call(a,"action","Contract-disabled action");
    assertFalse(disabled.isFocusable());assertFalse(disabled.isFocusableInTouchMode());
  }

  @Test public void guideRulerKeepsReadableTimesWithinTheirActualLargeFontSlots()throws Exception{
    java.util.Calendar clock=java.util.Calendar.getInstance();clock.clear();clock.set(2026,java.util.Calendar.SEPTEMBER,20,10,0);
    long start=clock.getTimeInMillis();
    for(int[] fixture:new int[][]{{320,720,150},{960,540,100}}){
      int width=fixture[0],height=fixture[1];float fontScale=fixture[2]/100f;
      RuntimeEnvironment.setQualifiers("w"+width+"dp-h"+height+"dp-"+(width>height?"land":"port")+"-mdpi");
      Configuration config=new Configuration(a.getResources().getConfiguration());config.fontScale=fontScale;
      a.getResources().updateConfiguration(config,a.getResources().getDisplayMetrics());a.onConfigurationChanged(config);
      prefs().edit().putString("cobra_appearance_mode","oled").commit();call(a,"cobraOpenLiveTv");
      ui.measure(a,width,height);ui.frames(32);ui.measure(a,width,height);put(a,"mCobraGuideWindow",start);
      View ruler=(View)get(a,"mCobraGuideRuler");Object layout=get(a,"mCobraModeLayout");
      float channelWidth=((Number)get(layout,"channelWidth")).floatValue()*a.getResources().getDisplayMetrics().density;
      long span=((Number)get(layout,"timeSpan")).longValue();float slot=(ruler.getWidth()-channelWidth)*1800000f/span;
      assertTrue("Production ruler is measured",ruler.getWidth()>200&&ruler.getHeight()>0);
      Bitmap bitmap=Bitmap.createBitmap(ruler.getWidth(),ruler.getHeight(),Bitmap.Config.ARGB_8888);
      RulerCanvas canvas=new RulerCanvas(bitmap);ruler.draw(canvas);
      assertTrue("Actual onDraw must paint timeline labels",canvas.labels.size()>=2);
      for(int i=0;i<canvas.labels.size();i++){
        float[] position=canvas.positions.get(i);
        assertEquals("Actual paint follows accessibility font size",10f*fontScale,position[3],.05f);
        assertTrue("Rendered label must fit before next tick: "+canvas.labels.get(i),position[2]<=slot-10f+.1f);
        assertTrue("Rendered label must fit visible ruler: "+canvas.labels.get(i),position[0]+position[2]<=ruler.getWidth()-5f+.1f);
      }
      String full=(String)call(a,"formatTime",start);
      if(width==320){
        assertEquals(new java.text.SimpleDateFormat("h:mm a",java.util.Locale.US).format(new java.util.Date(start)),canvas.labels.get(0));
        assertFalse("Narrow labels retain the actual clock rather than clipping a date prefix",canvas.labels.get(0).equals(full));
      }else assertEquals("Normal wide ruler preserves the existing full date/time label",full,canvas.labels.get(0));
      // An extreme custom cell must still respect measured text bounds. This is
      // secondary to the actual production onDraw assertions above.
      Paint paint=(Paint)get(ruler,"paint");String tiny=(String)call(ruler,"labelFor",start,8f);
      assertTrue(paint.measureText(tiny)<=8.1f);assertEquals("",call(ruler,"labelFor",start,0f));
      ui.image(a,"tv-grid-ruler-repaired-"+width+"x"+height+"-font"+fixture[2]);bitmap.recycle();
    }
  }
}
