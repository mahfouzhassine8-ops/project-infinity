package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Bundle;
import android.os.Looper;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.time.Duration;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual production helpers and Android native drawing; no device/playback claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,
    qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205PresentationEffectsTest {
  ActivityController<Activity> controller;
  Activity activity;
  FrameLayout root;
  CobraPresentationEffects effects;
  @Before public void before(){
    controller=Robolectric.buildActivity(Activity.class).setup();activity=controller.get();
    root=new FrameLayout(activity);activity.setContentView(root);controller.visible();
    effects=new CobraPresentationEffects(activity);layout(412,915);
  }
  @After public void after(){effects.close();controller.destroy();}
  void layout(int width,int height){
    root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
    root.layout(0,0,width,height);
  }
  Bitmap draw(View view){Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));return bitmap;}
  void evidence(Bitmap bitmap,String name)throws Exception{
    File folder=new File(System.getProperty("cobra.evidence","."));assertTrue(folder.isDirectory()||folder.mkdirs());
    try(FileOutputStream out=new FileOutputStream(new File(folder,"presentation-205-"+name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}
  }
  @Test public void newPreferencesDefaultOffAndDoNotAlterLegacyPreferenceValues(){
    SharedPreferences prefs=activity.getSharedPreferences("presentation-defaults",0);prefs.edit().clear().putString("cobra_appearance_mode","oled").commit();
    assertEquals(0,CobraPresentationEffects.ambientMode(prefs));assertFalse(prefs.getBoolean(CobraPresentationEffects.NIGHT,false));
    assertEquals(3500L,CobraPresentationEffects.chromeDelay(false));assertEquals(2100L,CobraPresentationEffects.chromeDelay(true));
    assertEquals("oled",prefs.getString("cobra_appearance_mode",""));
    prefs.edit().putString(CobraPresentationEffects.AMBIENT,"untrusted-mode").commit();assertEquals(0,CobraPresentationEffects.ambientMode(prefs));
  }
  @Test public void offPreservesEveryPaletteRoleAndSelectedModesOnlyTintAllowedRoles(){
    String[] roles={"background","text","muted","accent","accent_soft","focus","line","panel","panel2","rail","error","video"};
    for(String role:roles)assertEquals(role,0x99152743,CobraPresentationEffects.ambientColor(role,0x99152743,0,Color.RED));
    for(String role:new String[]{"background","text","muted","error","video"})for(int mode:new int[]{1,2})
      assertEquals(role,0x99152743,CobraPresentationEffects.ambientColor(role,0x99152743,mode,Color.RED));
    assertNotEquals(CobraPresentationEffects.ambientColor("focus",0xff162d49,1,Color.RED),CobraPresentationEffects.ambientColor("focus",0xff162d49,2,Color.RED));
    assertEquals(0x99,Color.alpha(CobraPresentationEffects.ambientColor("panel",0x99152743,2,Color.RED)));
  }
  @Test public void backdropOffRetainsExactOriginalAndNeverRecolorsVideoOwner()throws Exception{
    View background=new View(activity);background.setTag("cobra-browse-background");background.setBackgroundColor(Color.BLACK);root.addView(background,new FrameLayout.LayoutParams(-1,-1));
    View video=new View(activity);video.setTag("video");video.setBackgroundColor(0xff20aa70);root.addView(video,new FrameLayout.LayoutParams(180,120));layout(412,915);
    Drawable original=background.getBackground(),videoOriginal=video.getBackground();Bitmap baseline=draw(root);
    effects.backdrop(background,Color.BLACK,Color.BLUE,0);assertSame(original,background.getBackground());assertTrue(baseline.sameAs(draw(root)));
    effects.backdrop(video,Color.BLACK,Color.RED,2);assertSame(videoOriginal,video.getBackground());
    effects.backdrop(background,Color.BLACK,Color.BLUE,2);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(240));layout(412,915);
    Bitmap ambient=draw(root);assertEquals(0xff20aa70,ambient.getPixel(60,60));assertNotEquals(baseline.getPixel(350,40),ambient.getPixel(350,40));
    evidence(ambient,"ambient-video-protected");effects.backdrop(background,Color.BLACK,Color.BLUE,0);
    assertSame(original,background.getBackground());assertTrue(baseline.sameAs(draw(root)));
  }
  @Test public void contextTintUsesSuppliedMetadataAndHandlesMalformedColor(){
    assertEquals(0xffedaa31,CobraPresentationEffects.contextTint("#EDAA31"));
    assertEquals(0xff62aaff,CobraPresentationEffects.contextTint("not-a-color"));
    assertNotEquals(CobraPresentationEffects.ambientColor("accent",0xff62aaff,2,Color.RED),CobraPresentationEffects.ambientColor("accent",0xff62aaff,2,Color.GREEN));
  }
  @Test public void ambientLayersOverOriginalArtworkAndOffRestoresExactPixels()throws Exception{
    Bitmap artwork=Bitmap.createBitmap(32,32,Bitmap.Config.ARGB_8888);
    for(int x=0;x<32;x++)for(int y=0;y<32;y++)artwork.setPixel(x,y,(x/8+y/8)%2==0?0xffab7021:0xff284625);
    Bitmap originalPixels=artwork.copy(Bitmap.Config.ARGB_8888,false);
    View background=new View(activity);background.setTag("cobra-browse-background");
    BitmapDrawable original=new BitmapDrawable(activity.getResources(),artwork);background.setBackground(original);
    root.addView(background,new FrameLayout.LayoutParams(-1,-1));layout(412,915);Bitmap baseline=draw(root),subtle=null;
    for(int mode:new int[]{CobraPresentationEffects.SUBTLE,CobraPresentationEffects.IMMERSIVE}){
      effects.backdrop(background,Color.BLACK,Color.BLUE,mode);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(240));layout(412,915);
      assertTrue(background.getBackground() instanceof LayerDrawable);LayerDrawable layers=(LayerDrawable)background.getBackground();
      assertEquals(2,layers.getNumberOfLayers());assertSame(original,layers.getDrawable(0));assertEquals(255,original.getAlpha());assertTrue(artwork.sameAs(originalPixels));
      Bitmap rendered=draw(root);assertFalse(baseline.sameAs(rendered));assertNotEquals(rendered.getPixel(20,30),rendered.getPixel(150,30));
      if(subtle==null)subtle=rendered;else assertFalse(subtle.sameAs(rendered));evidence(rendered,"ambient-art-"+mode);
    }
    effects.backdrop(background,Color.BLACK,Color.BLUE,CobraPresentationEffects.OFF);assertSame(original,background.getBackground());assertTrue(baseline.sameAs(draw(root)));
  }
  @Test public void ambientAdoptsNewThemeArtworkWithoutRestoringOldThemeAndNullRestoresNull(){
    View background=new View(activity);background.setTag("cobra-browse-background");root.addView(background);
    effects.backdrop(background,Color.BLACK,Color.BLUE,2);effects.backdrop(background,Color.BLACK,Color.BLUE,0);assertNull(background.getBackground());
    background.setBackgroundColor(Color.RED);effects.backdrop(background,Color.BLACK,Color.BLUE,2);
    Drawable replacement=new ColorDrawable(Color.GREEN);background.setBackground(replacement);effects.backdrop(background,Color.BLACK,Color.BLUE,2);
    assertSame(replacement,((LayerDrawable)background.getBackground()).getDrawable(0));effects.backdrop(background,Color.BLACK,Color.BLUE,0);assertSame(replacement,background.getBackground());
  }
  @Test public void closeRestoresOwnedBackdropWithoutUndoingNewExternalThemePaint(){
    View background=new View(activity);background.setTag("cobra-browse-background");background.setBackgroundColor(Color.BLACK);root.addView(background);
    effects.backdrop(background,Color.BLACK,Color.BLUE,2);background.setBackgroundColor(Color.MAGENTA);Drawable later=background.getBackground();
    effects.close();assertSame(later,background.getBackground());
  }
  @Test public void explicitEntryTokenIsConsumedAndPersistedAcrossRecreation(){
    assertFalse(effects.consumeEntry(new Intent()));Intent first=new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"one-explicit-choice");
    assertTrue(effects.consumeEntry(first));assertFalse(first.hasExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN));assertFalse(effects.consumeEntry(first));
    Bundle saved=new Bundle();effects.save(saved);CobraPresentationEffects recreated=new CobraPresentationEffects(activity);recreated.restore(saved);
    assertFalse(recreated.consumeEntry(new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"one-explicit-choice")));
    assertTrue(recreated.consumeEntry(new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"second-explicit-choice")));recreated.close();
  }
  @Test public void malformedOversizedEntryTokenNeverTriggersWelcome(){
    String token=new String(new char[200]).replace('\0','a');Intent intent=new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,token);
    assertFalse(effects.consumeEntry(intent));assertFalse(intent.hasExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN));
  }
  @Test public void greetingIsLiteralBoundedAndDoesNotSplitUnicode(){
    assertEquals("Welcome back",CobraPresentationEffects.boundedGreeting(" \n "));
    assertEquals("<b>Hassine</b>",CobraPresentationEffects.boundedGreeting("<b>Hassine</b>"));
    String emoji=new String(Character.toChars(0x1f60a)),longText="";for(int i=0;i<130;i++)longText+=emoji;
    String bounded=CobraPresentationEffects.boundedGreeting(longText);assertEquals(120,bounded.codePointCount(0,bounded.length()));assertEquals(240,bounded.length());
  }
  @Test public void welcomeRevealsBesideEmblemWithoutTakingFocusAndExpiresBy2200ms()throws Exception{
    effects.showWelcome(root,"Welcome back, Hassine",false,false);layout(412,915);
    View welcome=root.findViewWithTag("cobra_personalized_welcome");TextView text=root.findViewWithTag("cobra_welcome_text");
    assertNotNull(welcome);assertFalse(welcome.isFocusable());assertFalse(welcome.isClickable());assertFalse(text.isFocusable());assertFalse(text.isClickable());
    assertEquals(0f,text.getTranslationX(),0f);assertEquals(0f,text.getTranslationY(),0f);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(300));assertEquals(1f,text.getAlpha(),.001f);evidence(draw(root),"welcome-light");
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(1900));assertFalse(effects.welcomeVisible());assertNull(root.findViewWithTag("cobra_personalized_welcome"));
  }
  @Test public void welcomeRtlLargeFontFitsAndBackgroundDoesNotReplayIt()throws Exception{
    android.content.res.Configuration configuration=new android.content.res.Configuration(activity.getResources().getConfiguration());configuration.fontScale=2f;activity.getResources().updateConfiguration(configuration,activity.getResources().getDisplayMetrics());
    layout(320,480);effects.showWelcome(root,"مرحبا بعودتك حسّين إلى كوبرا",true,true);layout(320,480);
    LinearLayout row=root.findViewWithTag("cobra_personalized_welcome");TextView text=root.findViewWithTag("cobra_welcome_text");
    assertSame(text,row.getChildAt(0));assertTrue(text.getLeft()<row.getChildAt(1).getLeft());
    assertTrue(text.getLayout().getHeight()<=text.getHeight());assertTrue(row.getHeight()<480);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(300));layout(320,480);
    assertEquals(1f,text.getAlpha(),.001f);evidence(draw(root),"welcome-rtl-font200");
    effects.setForeground(false);assertFalse(effects.welcomeVisible());effects.setForeground(true);assertFalse(effects.welcomeVisible());
  }
  @Test public void pulseStatePriorityUsesObservedTroubleAndNeverInventsLive(){
    assertEquals(CobraPresentationEffects.PulseState.NONE,CobraPresentationEffects.pulseState(false,true,true,true,true,true,true,true));
    assertEquals(CobraPresentationEffects.PulseState.NETWORK,CobraPresentationEffects.pulseState(true,true,true,true,true,true,true,true));
    assertEquals(CobraPresentationEffects.PulseState.RECOVERING,CobraPresentationEffects.pulseState(true,false,true,true,true,true,true,true));
    assertEquals(CobraPresentationEffects.PulseState.NORMAL,CobraPresentationEffects.pulseState(true,false,false,false,false,false,false,false));
  }
  @Test public void pulsePixelsShowEveryApprovedStateOnLightAndDark()throws Exception{
    for(int canvas:new int[]{Color.WHITE,Color.BLACK}){
      FrameLayout samples=new FrameLayout(activity);samples.setBackgroundColor(canvas);int x=0;
      for(CobraPresentationEffects.PulseState state:CobraPresentationEffects.PulseState.values()){
        if(state==CobraPresentationEffects.PulseState.NONE)continue;
        CobraPresentationEffects.PulseView pulse=new CobraPresentationEffects.PulseView(activity);pulse.allowMotion(false);pulse.state(state);
        FrameLayout.LayoutParams position=new FrameLayout.LayoutParams(44,44);position.leftMargin=x;position.topMargin=8;samples.addView(pulse,position);x+=48;
      }
      samples.measure(View.MeasureSpec.makeMeasureSpec(x,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(60,View.MeasureSpec.EXACTLY));samples.layout(0,0,x,60);
      Bitmap rendered=draw(samples);int index=0;
      for(CobraPresentationEffects.PulseState state:CobraPresentationEffects.PulseState.values()){
        if(state==CobraPresentationEffects.PulseState.NONE)continue;int ink=0;
        for(int px=index*48;px<index*48+44;px++)for(int py=8;py<52;py++){
          int color=rendered.getPixel(px,py);int maximum=Math.max(Color.red(color),Math.max(Color.green(color),Color.blue(color))),minimum=Math.min(Color.red(color),Math.min(Color.green(color),Color.blue(color)));
          if(state==CobraPresentationEffects.PulseState.LIVE?maximum-minimum<25&&maximum>130&&maximum<(canvas==Color.WHITE?250:256):maximum-minimum>15)ink++;
        }
        assertTrue(state+" visible on "+canvas,ink>12);index++;
      }
      evidence(rendered,canvas==Color.WHITE?"pulse-light":"pulse-dark");
    }
  }
  @Test public void pulseNormalHasNoLoopAndBufferAnimationStopsWhenHiddenOrDetached(){
    CobraPresentationEffects.PulseView pulse=new CobraPresentationEffects.PulseView(activity);root.addView(pulse,new FrameLayout.LayoutParams(44,44));layout(412,915);
    pulse.state(CobraPresentationEffects.PulseState.NORMAL);assertFalse(pulse.animating());
    pulse.state(CobraPresentationEffects.PulseState.BUFFERING);assertTrue(pulse.animating());
    pulse.setVisibility(View.GONE);assertFalse(pulse.animating());pulse.setVisibility(View.VISIBLE);assertTrue(pulse.animating());
    pulse.allowMotion(false);assertFalse(pulse.animating());pulse.allowMotion(true);root.removeView(pulse);assertFalse(pulse.animating());
  }
  @Test public void pulseRetainsExistingStatusTagAndEmptyStateWithoutExtraControl(){
    TextView legacy=new TextView(activity);legacy.setTag("player_state");legacy.setText("Select a channel");View slot=effects.status(legacy);root.addView(slot,new FrameLayout.LayoutParams(82,30));layout(412,915);
    effects.updateStatus(root,CobraPresentationEffects.PulseState.NONE,true);assertSame(legacy,root.findViewWithTag("player_state"));assertEquals(View.VISIBLE,legacy.getVisibility());
    effects.updateStatus(root,CobraPresentationEffects.PulseState.BUFFERING,true);assertEquals(View.INVISIBLE,legacy.getVisibility());assertEquals("Buffering",slot.getContentDescription());
    assertFalse(slot.isClickable());assertFalse(slot.isFocusable());effects.updateStatus(root,CobraPresentationEffects.PulseState.BUFFERING,false);
    assertEquals(View.VISIBLE,legacy.getVisibility());assertEquals(View.GONE,root.findViewWithTag("cobra_pulse_emblem").getVisibility());
  }
}
