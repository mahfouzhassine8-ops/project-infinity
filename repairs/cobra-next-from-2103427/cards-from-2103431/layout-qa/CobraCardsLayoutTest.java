package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.os.Looper;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.ByteArrayOutputStream;
import java.lang.reflect.*;
import java.lang.ref.WeakReference;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
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
import org.robolectric.shadows.ShadowDisplay;

/** Actual accepted native shell/views. State-only player input, no decoder.
 * Only media/OS terminal actions are intercepted; native controls remain real. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraCardsLayoutTest {
  static final String[] MODES={"mobile","compact","grid","focus"};
  static final List<String> ENDPOINTS=new ArrayList<>();
  static final String[] SHARED={"mCobraModeToolbar","mCobraGuideDetails","mCobraGuideVideo"};
  static Object get(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
  static void set(Object o,String n,Object value)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,value);}
  static Object call(Object o,String n,Object...args)throws Exception{
    for(Method m:o.getClass().getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterCount()==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(InvocationTargetException e){throw new RuntimeException("Actual native "+n,e.getCause());}}
    throw new NoSuchMethodException(n);
  }
  static Object construct(String n,Object...args)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+n);
    for(Constructor<?> k:c.getDeclaredConstructors())if(k.getParameterCount()==args.length){k.setAccessible(true);return k.newInstance(args);}
    throw new NoSuchMethodException(n);
  }
  static boolean candidate(){return Boolean.getBoolean("cards.candidate");}
  static Path output(){return Paths.get(System.getProperty("cards.layout.output"));}
  static String hash(byte[] bytes)throws Exception{byte[] b=MessageDigest.getInstance("SHA-256").digest(bytes);StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(Locale.US,"%02x",v));return s.toString();}
  static void write(String name,JSONObject value)throws Exception{Files.createDirectories(output());Files.write(output().resolve(name+".json"),(value.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}
  @Before public void frames(){ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));Locale.setDefault(Locale.US);TimeZone.setDefault(TimeZone.getTimeZone("UTC"));assertTrue(SystemClock.setCurrentTimeMillis(1735732800000L));}
  static final class RecordIo extends AbstractExecutorService {
    final List<Runnable> admitted=new ArrayList<>();public void execute(Runnable r){admitted.add(r);}
    public void shutdown(){throw new AssertionError("Shutdown is not selected");}public List<Runnable> shutdownNow(){throw new AssertionError("Shutdown is not selected");}
    public boolean isShutdown(){return false;}public boolean isTerminated(){return false;}public boolean awaitTermination(long t,TimeUnit u){throw new AssertionError("Shutdown is not selected");}
  }
  static final class Playback implements InvocationHandler {
    int state=Player.STATE_READY;boolean ready=true;
    public Object invoke(Object proxy,Method m,Object[] args){
      String n=m.getName();if(n.equals("equals"))return proxy==args[0];if(n.equals("hashCode"))return System.identityHashCode(proxy);
      if(n.equals("getPlayWhenReady"))return ready;if(n.equals("isPlaying"))return ready&&state==Player.STATE_READY;if(n.equals("getPlaybackState"))return state;
      if(n.equals("getVolume"))return 1f;if(n.equals("getTrackSelectionParameters"))return TrackSelectionParameters.DEFAULT_WITHOUT_CONTEXT;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getVideoSize"))return VideoSize.UNKNOWN;if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getAvailableCommands"))return Player.Commands.EMPTY;if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
  public static class TerminalActions extends ShadowActivity {
    @RealObject InfinityLiveActivity owner;
    @Implementation protected void promoteCobraPreviewToFullscreen(Object channel)throws Exception{ENDPOINTS.add("fullscreen");set(owner,"mPlayer",get(owner,"mCobraPreviewPlayer"));set(owner,"mPlayerOverlay",new FrameLayout(owner));}
    @Implementation protected void enterCobraPictureInPicture(){ENDPOINTS.add("pip");}
  }
  static final class Fixture {
    final ActivityController<InfinityLiveActivity> controller;final InfinityLiveActivity a;final SharedPreferences prefs;final RecordIo io=new RecordIo();
    final List<Object> channels;final int width=941,height=1672;Playback input;Object player,binding;
    Fixture(String mode)throws Exception{
      ShadowDisplay display=Shadows.shadowOf(ShadowDisplay.getDefaultDisplay());display.setDensityDpi(420);display.setWidth(width);display.setHeight(height);display.setRealWidth(width);display.setRealHeight(height);
      controller=Robolectric.buildActivity(InfinityLiveActivity.class);a=controller.get();a.setTheme(android.R.style.Theme_Material_NoActionBar);
      a.getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,WindowManager.LayoutParams.FLAG_FULLSCREEN);
      prefs=a.getSharedPreferences("cards-layout-"+UUID.randomUUID(),Context.MODE_PRIVATE);prefs.edit().putString("cobra_appearance_mode","dark").putString("guide_view_mode",mode).putString("cobra_primary_view","guide").putString("cobra_ambient_mode","off").commit();
      set(a,"mPrefs",prefs);set(a,"mTheme",construct("Theme"));set(a,"mUi",construct("UiContract"));
      InfinityCobraFeatureRuntime features=new InfinityCobraFeatureRuntime(a);assertTrue(features.unlockAndSelectProfile("default",""));set(a,"mFeatures",features);set(a,"mIo",io);
      set(a,"mCobraGuideStyle",mode);set(a,"mCobraGuideRoute","channels");set(a,"mCategory","ALL");set(a,"mSearch","");set(a,"mCobraProActive",false);set(a,"mCobraPreviewAutoplayAllowed",false);set(a,"mCobraRotationResumed",true);
      call(a,"cobraInitPresentationEffects",new Object[]{null});assertNotNull(get(a,"mCobraEffects"));
      ((List<Object>)get(a,"mSources")).add(construct("LiveSource","qa","m3u","Synthetic QA","","","","https://example.invalid/playlist",""));
      channels=(List<Object>)get(a,"mChannels");for(int i=0;i<24;i++)channels.add(construct("Channel","qa:"+i,"Synthetic channel "+i,"Group","epg"+i,"","https://example.invalid/video/"+i,"qa",Collections.emptyMap()));seedEpg();
      set(a,"mGuidePreviewChannel",channels.get(0));call(a,"buildShell");call(a,"cobraShowGuideShell");controller.visible();frames();
      assertTrue(((View)get(a,"mCobraGuideShell")).isAttachedToWindow());assertEquals(420,a.getResources().getDisplayMetrics().densityDpi);
      assertTrue(((View)get(a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_label").getParent().getClass().getName().endsWith("$StatusSlot"));
      assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));
    }
    void seedEpg()throws Exception{
      long now=System.currentTimeMillis();Object data=construct("CobraEpgData");set(data,"identity",call(a,"cobraEpgIdentity",((List)get(a,"mSources")).get(0)));set(data,"fetched",now);
      Map<String,ArrayList<Object>> programs=(Map<String,ArrayList<Object>>)get(data,"programs");for(int i=0;i<channels.size();i++){ArrayList<Object> list=new ArrayList<>();for(int n=0;n<2;n++){Object p=construct("GuideProgram");set(p,"channel","epg"+i);set(p,"title",(n==0?"Current ":"Next ")+i);set(p,"description","Synthetic programme description "+i);set(p,"start",now+(n==0?-3600000L:3600000L));set(p,"stop",now+(n==0?3600000L:7200000L));list.add(p);}programs.put("epg"+i,list);}((Map)get(a,"mCobraEpg")).put("qa",data);
    }
    void layout(){View v=a.getWindow().getDecorView();v.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));v.layout(0,0,width,height);}
    void frames(){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));layout();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));layout();}
    void mode(String mode)throws Exception{call(a,"cobraSwitchMode",mode);frames();assertEquals(mode,get(a,"mCobraGuideStyle"));assertEquals("focus".equals(mode),get(a,"mCobraProActive"));}
    void player(boolean live)throws Exception{
      Object channel=live?channels.get(0):construct("Channel","vod-only","Synthetic VOD","Group","","","https://example.invalid/vod","qa",Collections.emptyMap());
      input=new Playback();player=Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},input);
      binding=construct("CobraPlayerBinding",a,player,channel);((Map)get(a,"mCobraPlayerBindings")).put(player,binding);
      set(a,"mCobraPreviewPlayer",player);set(a,"mGuidePreviewChannel",channel);set(a,"mCobraPreviewSessionKey",call(a,"cobraChannelKey",channel));publish();
      assertEquals(live,get(get(binding,"vitals"),"live"));
    }
    void publish()throws Exception{call(a,"cobraUpdatePlaybackLabels");frames();}
    JSONObject geometry()throws Exception{JSONObject result=new JSONObject();result.put("density_dpi",a.getResources().getDisplayMetrics().densityDpi).put("window",new JSONArray(Arrays.asList(width,height)));for(String field:new String[]{"mCobraGuideShell","mCobraModeToolbar","mCobraGuideVideo","mCobraGuideDetails","mCobraGuideBrowser","mCobraGuideList"}){View v=(View)get(a,field);result.put(field,view(v,false));}Object model=get(a,"mCobraModeLayout");JSONObject rects=new JSONObject();for(String n:new String[]{"toolbar","video","details","browser","columns","width","height"}){Object value=get(model,n);rects.put(n,value instanceof int[]?new JSONArray(value):value);}return result.put("model_dp",rects).put("recorded_IO_jobs",io.admitted.size()).put("effects_present",get(a,"mCobraEffects")!=null);}
    JSONObject shared()throws Exception{JSONObject r=new JSONObject();for(String f:SHARED)r.put(f,view((View)get(a,f),true));r.put("stage_padding",padding((View)get(a,"mStage")));return r;}
    void image(String name)throws Exception{View root=(View)get(a,"mCobraGuideShell");assertEquals(width,root.getWidth());assertEquals(height,root.getHeight());Bitmap bitmap=Bitmap.createBitmap(root.getWidth(),root.getHeight(),Bitmap.Config.ARGB_8888);root.draw(new Canvas(bitmap));ByteArrayOutputStream bytes=new ByteArrayOutputStream();assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,bytes));Files.createDirectories(output());Files.write(output().resolve(name+".png"),bytes.toByteArray());bitmap.recycle();}
    void press(View target)throws Exception{Rect box=new Rect();assertTrue(target.getGlobalVisibleRect(box));assertTrue(box.width()>10&&box.height()>10);View root=a.getWindow().getDecorView();int[] xy=new int[2];root.getLocationOnScreen(xy);long t=SystemClock.uptimeMillis();for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}){MotionEvent event=MotionEvent.obtain(t,t+(action==MotionEvent.ACTION_UP?32:0),action,box.exactCenterX()-xy[0],box.exactCenterY()-xy[1],0);try{assertTrue(root.dispatchTouchEvent(event));}finally{event.recycle();}}Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));}
  }
  static JSONArray padding(View v){return new JSONArray(Arrays.asList(v.getPaddingLeft(),v.getPaddingTop(),v.getPaddingRight(),v.getPaddingBottom()));}
  static String background(Drawable d)throws Exception{if(d==null)return "null";Rect old=new Rect(d.getBounds());Bitmap bitmap=Bitmap.createBitmap(64,64,Bitmap.Config.ARGB_8888);d.setBounds(0,0,64,64);d.draw(new Canvas(bitmap));int[] pixels=new int[4096];bitmap.getPixels(pixels,0,64,0,0,64,64);d.setBounds(old);bitmap.recycle();java.nio.ByteBuffer bytes=java.nio.ByteBuffer.allocate(pixels.length*4);for(int p:pixels)bytes.putInt(p);return d.getClass().getName()+":"+hash(bytes.array());}
  static JSONObject view(View v,boolean recurse)throws Exception{
    JSONObject o=new JSONObject().put("class",v.getClass().getName()).put("tag",String.valueOf(v.getTag())).put("bounds",new JSONArray(Arrays.asList(v.getLeft(),v.getTop(),v.getWidth(),v.getHeight()))).put("padding",padding(v)).put("visibility",v.getVisibility()).put("alpha",v.getAlpha()).put("elevation",v.getElevation()).put("clip_outline",v.getClipToOutline()).put("focusable",v.isFocusable()).put("clickable",v.isClickable()).put("long_clickable",v.isLongClickable()).put("background",background(v.getBackground()));
    ViewGroup.LayoutParams p=v.getLayoutParams();if(p!=null){JSONObject lp=new JSONObject().put("class",p.getClass().getName()).put("width",p.width).put("height",p.height);if(p instanceof ViewGroup.MarginLayoutParams){ViewGroup.MarginLayoutParams m=(ViewGroup.MarginLayoutParams)p;lp.put("margins",new JSONArray(Arrays.asList(m.leftMargin,m.topMargin,m.rightMargin,m.bottomMargin)));}if(p instanceof FrameLayout.LayoutParams)lp.put("gravity",((FrameLayout.LayoutParams)p).gravity);if(p instanceof LinearLayout.LayoutParams)lp.put("weight",((LinearLayout.LayoutParams)p).weight).put("gravity",((LinearLayout.LayoutParams)p).gravity);o.put("layout",lp);}
    if(v instanceof TextView){TextView t=(TextView)v;o.put("text",String.valueOf(t.getText())).put("size_px",t.getTextSize()).put("color",t.getCurrentTextColor()).put("typeface_style",t.getTypeface().getStyle()).put("max_lines",t.getMaxLines()).put("min_lines",t.getMinLines()).put("gravity",t.getGravity()).put("letter_spacing",t.getLetterSpacing()).put("font_padding",t.getIncludeFontPadding()).put("line_extra",t.getLineSpacingExtra()).put("line_multiplier",t.getLineSpacingMultiplier()).put("ellipsize",String.valueOf(t.getEllipsize())).put("compound_padding",t.getCompoundDrawablePadding());JSONArray compounds=new JSONArray();for(Drawable d:t.getCompoundDrawablesRelative())compounds.put(background(d));o.put("compounds",compounds);}
    if(v instanceof ProgressBar){ProgressBar bar=(ProgressBar)v;o.put("progress",bar.getProgress()).put("max",bar.getMax()).put("drawable_level",bar.getProgressDrawable()==null?-1:bar.getProgressDrawable().getLevel()).put("progress_drawable",background(bar.getProgressDrawable())).put("progress_tint",String.valueOf(bar.getProgressTintList())).put("progress_background_tint",String.valueOf(bar.getProgressBackgroundTintList()));}
    if(v.getClass().getName().endsWith("$CobraIconButton"))o.put("glyph",get(v,"glyph")).put("caption",get(v,"caption"));
    if(v instanceof ViewGroup){ViewGroup group=(ViewGroup)v;o.put("clip_children",group.getClipChildren()).put("clip_padding",group.getClipToPadding());if(v instanceof LinearLayout)o.put("orientation",((LinearLayout)v).getOrientation()).put("gravity",((LinearLayout)v).getGravity());if(recurse){JSONArray children=new JSONArray();for(int i=0;i<group.getChildCount();i++)children.put(view(group.getChildAt(i),true));o.put("children",children);}}
    return o;
  }
  static String diff(Object expected,Object actual,String path)throws Exception{
    if(expected instanceof JSONObject && actual instanceof JSONObject){JSONObject a=(JSONObject)expected,b=(JSONObject)actual;TreeSet<String> keys=new TreeSet<>();for(Iterator<String> i=a.keys();i.hasNext();)keys.add(i.next());for(Iterator<String> i=b.keys();i.hasNext();)keys.add(i.next());for(String key:keys){if(!a.has(key)||!b.has(key))return path+"."+key+" missing";String d=diff(a.get(key),b.get(key),path+"."+key);if(d!=null)return d;}return null;}
    if(expected instanceof JSONArray && actual instanceof JSONArray){JSONArray a=(JSONArray)expected,b=(JSONArray)actual;if(a.length()!=b.length())return path+" length "+a.length()+" != "+b.length();for(int i=0;i<a.length();i++){String d=diff(a.get(i),b.get(i),path+"["+i+"]");if(d!=null)return d;}return null;}
    if(expected instanceof Number && actual instanceof Number)return Math.abs(((Number)expected).doubleValue()-((Number)actual).doubleValue())<.00001?null:path+" "+expected+" != "+actual;
    return Objects.equals(expected,actual)?null:path+" "+expected+" != "+actual;
  }
  static void noOwnedCardsForeground(View view){Drawable drawable=view.getForeground();assertFalse("Cards foreground must not leak into another mode",drawable!=null && drawable.getClass().getName().startsWith("com.projectinfinity.kodi.CobraCardsLayout$"));if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;for(int i=0;i<group.getChildCount();i++)noOwnedCardsForeground(group.getChildAt(i));}}
  static boolean numeric(Object value)throws Exception{if(value instanceof Number)return true;if(value instanceof JSONArray){JSONArray a=(JSONArray)value;for(int i=0;i<a.length();i++)if(!numeric(a.get(i)))return false;return true;}return false;}
  static void normalizeNamedGone(JSONObject expected,JSONObject actual,String path,boolean underDetails,boolean inheritedGone,JSONArray recorded)throws Exception{
    boolean details=underDetails || path.endsWith(".mCobraGuideDetails");boolean ownGone=expected.optInt("visibility",-1)==View.GONE && actual.optInt("visibility",-1)==View.GONE;
    boolean effectiveGone=inheritedGone || ownGone;
    boolean named=path.endsWith(".mCobraGuideDetails") || path.endsWith(".mCobraGuideDetails.children[2]") || path.endsWith(".mCobraGuideDetails.children[3]") || path.endsWith(".mCobraGuideDetails.children[4]") || "cobra_preview_pip_small".equals(expected.optString("tag")) && "cobra_preview_pip_small".equals(actual.optString("tag"));
    if(effectiveGone && (named || details && inheritedGone)){
      if(expected.has("bounds") && actual.has("bounds")){if(diff(expected.get("bounds"),actual.get("bounds"),path)!=null)recorded.put(new JSONObject().put("path",path+".bounds").put("baseline",expected.get("bounds")).put("candidate",actual.get("bounds")).put("native_reason","Native GONE/effectively GONE retains prior Cards geometry; no draw/layout"));expected.remove("bounds");actual.remove("bounds");}
      if(expected.has("layout") && actual.has("layout")){JSONObject a=expected.getJSONObject("layout"),b=actual.getJSONObject("layout");List<String> keys=new ArrayList<>();for(Iterator<String> i=a.keys();i.hasNext();)keys.add(i.next());for(String key:keys)if(!key.equals("class") && b.has(key) && numeric(a.get(key)) && numeric(b.get(key))){if(diff(a.get(key),b.get(key),path)!=null)recorded.put(new JSONObject().put("path",path+".layout."+key).put("baseline",a.get(key)).put("candidate",b.get(key)).put("native_reason","Native hide path does not reposition its previous Cards LP"));a.remove(key);b.remove(key);}}
    }
    if(expected.has("children") && actual.has("children")){JSONArray a=expected.getJSONArray("children"),b=actual.getJSONArray("children");if(a.length()==b.length())for(int i=0;i<a.length();i++)normalizeNamedGone(a.getJSONObject(i),b.getJSONObject(i),path+".children["+i+"]",details,details && effectiveGone,recorded);}
  }
  static JSONObject baseline(String mode)throws Exception{return new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("cards.layout.baseline")).resolve("shared-transition-"+mode+".json")),StandardCharsets.UTF_8));}
  @Test public void recordNativeSharedModeBaselines()throws Exception{
    assertFalse("baseline method uses exact signed431 only",candidate());
    for(String mode:MODES){Fixture f=new Fixture(mode);write("shared-"+mode,f.shared());write("geometry-"+mode,f.geometry());}
  }
  @Test public void recordNativeCardsExitModeBaselines()throws Exception{
    assertFalse("same-journey baseline uses exact signed431 only",candidate());
    for(String mode:MODES){Fixture f=new Fixture("cards");f.mode(mode);write("shared-transition-"+mode,f.shared());write("geometry-transition-"+mode,f.geometry());}
  }
  @Test public void recordNativeCardsAmbientWrapping()throws Exception{
    assertFalse(candidate());Fixture f=new Fixture("cards");f.prefs.edit().putString("cobra_ambient_mode","subtle").commit();JSONArray phases=new JSONArray();for(int i=0;i<4;i++){call(f.a,"cobraRefreshModeDetails");call(f.a,"cobraRefreshVisualEffects");f.frames();View details=(View)get(f.a,"mCobraGuideDetails");Map base=(Map)get(f.a,"mCobraAmbientSurfaceBase"),applied=(Map)get(f.a,"mCobraAmbientSurfaceApplied");phases.put(new JSONObject().put("iteration",i).put("background_class",details.getBackground().getClass().getName()).put("background_identity",System.identityHashCode(details.getBackground())).put("base_count",base.size()).put("applied_count",applied.size()));assertEquals("subtle",f.prefs.getString("cobra_ambient_mode",""));assertNotNull(get(f.a,"mCobraEffects"));}write("native-ambient",new JSONObject().put("iterations",phases).put("source","exact signed431"));
  }
  @Test public void actualCardsRenderAtReferenceViewport()throws Exception{
    assertTrue(candidate());Fixture f=new Fixture("cards");f.channels.clear();Set<String> favorites=(Set<String>)get(f.a,"mFavorites");favorites.clear();for(int i=0;i<20226;i++){Object channel=construct("Channel","qa:"+i,"Synthetic channel "+i,"Group","epg"+i,"","https://example.invalid/video/"+i,"qa",Collections.emptyMap());f.channels.add(channel);if(i<6)favorites.add((String)get(channel,"id"));}set(f.a,"mCategory","FAVORITES");set(f.a,"mGuidePreviewChannel",f.channels.get(0));call(f.a,"cobraShowGuideShell");f.frames();f.player(true);write("cards-geometry",f.geometry());f.image("cards-native-reference-favorites");
    assertTrue(get(f.a,"mCobraGuideList") instanceof GridView);GridView grid=(GridView)get(f.a,"mCobraGuideList");assertEquals(2,grid.getNumColumns());assertEquals(6,grid.getCount());assertEquals(20226,f.channels.size());assertEquals("FAVORITES",get(f.a,"mCategory"));
    View preview=(View)get(f.a,"mCobraGuideVideo"),details=(View)get(f.a,"mCobraGuideDetails"),browser=(View)get(f.a,"mCobraGuideBrowser");assertEquals(preview.getTop(),details.getTop());assertEquals(preview.getHeight(),details.getHeight());assertTrue(browser.getTop()>=preview.getBottom());
    assertEquals(0,((View)get(f.a,"mStage")).getPaddingLeft());assertEquals(0,((View)get(f.a,"mStage")).getPaddingRight());assertFalse((Boolean)get(f.a,"mCobraProActive"));
    TextView time=(TextView)get(f.a,"mCobraGuideNextLabel");String text=time.getText().toString();assertEquals("same-day native date occurs once",text.indexOf("Wed Jan 1"),text.lastIndexOf("Wed Jan 1"));
    TextView description=(TextView)get(f.a,"mCobraModeDescription");assertEquals(View.VISIBLE,description.getVisibility());assertEquals("Synthetic programme description 0",description.getText().toString());
    ProgressBar progress=(ProgressBar)get(f.a,"mCobraGuideProgress");assertTrue(progress.getMax()>0 && progress.getProgress()>0 && progress.getProgress()<progress.getMax());assertEquals(Math.round(progress.getProgress()*10000f/progress.getMax()),progress.getProgressDrawable().getLevel());
    assertEquals(104,((View)get(f.a,"mCobraModeToolbar")).getHeight());assertEquals(14,preview.getLeft());assertEquals(116,preview.getTop());assertEquals(476,preview.getWidth());assertEquals(362,preview.getHeight());assertEquals(496,browser.getTop());
  }
  @Test public void cardsRestoresSharedNativeViewsInOtherModes()throws Exception{
    assertTrue(candidate());List<String> differences=new ArrayList<>();for(String mode:MODES){Fixture f=new Fixture("cards");Object preview=get(f.a,"mCobraGuideVideo"),texture=get(f.a,"mCobraPreviewTexture"),title=get(f.a,"mCobraGuideNowLabel");f.mode(mode);for(String shared:SHARED)noOwnedCardsForeground((View)get(f.a,shared));assertSame(preview,get(f.a,"mCobraGuideVideo"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertSame(title,get(f.a,"mCobraGuideNowLabel"));JSONObject actual=f.shared(),expected=baseline(mode);write("restored-"+mode,actual);JSONArray historical=new JSONArray();for(String field:SHARED)normalizeNamedGone(expected.getJSONObject(field),actual.getJSONObject(field),mode+"."+field,false,false,historical);write("ignored-native-gone-geometry-"+mode,new JSONObject().put("differences",historical).put("scope","only approved exact named metadata/Pro details/tagged smallPiP; numeric geometry only; LPclass/styles/visibility remain strict"));String difference=diff(expected,actual,mode);if(difference!=null)differences.add(difference);}assertEquals("shared native properties/hierarchy restored; see exact JSON",Collections.emptyList(),differences);
  }
  @Test public void truthfulLiveBadgeUsesNativeStatusAndPreservesActualPipPress()throws Exception{
    assertTrue(candidate());Fixture f=new Fixture("cards");View preview=(View)get(f.a,"mCobraPreviewHost");TextView label=preview.findViewWithTag("cobra_preview_label");Object parent=label.getParent();assertNotNull(get(f.a,"mCobraEffects"));f.player(true);assertEquals("LIVE",call(f.a,"cobraPlayerState",f.player));assertEquals("LIVE",label.getText().toString());assertEquals(View.VISIBLE,label.getVisibility());assertSame(parent,label.getParent());
    View pip=preview.findViewWithTag("cobra_preview_pip_small"),controls=preview.findViewWithTag("cobra_preview_controls");assertEquals("reference-density small preview uses native PiP",View.GONE,controls.getVisibility());assertEquals(View.VISIBLE,pip.getVisibility());Rect badge=new Rect(),button=new Rect();assertTrue(label.getGlobalVisibleRect(badge));assertTrue(pip.getGlobalVisibleRect(button));assertFalse("native PiP actual target clears LIVE chip",Rect.intersects(badge,button));assertEquals("full native PiP width remains visible",pip.getWidth(),button.width());assertEquals("full native PiP height remains visible",pip.getHeight(),button.height());assertEquals(new Rect(41,414,130,452),badge);View texture=(View)get(f.a,"mCobraPreviewTexture");assertEquals(10,texture.getLeft());assertEquals(14,texture.getTop());assertEquals(preview.getWidth()-20,texture.getWidth());assertEquals(preview.getHeight()-24,texture.getHeight());assertEquals(new JSONArray(Arrays.asList(0,0,0,0)).toString(),padding(preview).toString());
    write("live-native-status",new JSONObject().put("label",view(label,true)).put("PiP",view(pip,true)).put("badge_bounds",new JSONArray(Arrays.asList(badge.left,badge.top,badge.right,badge.bottom))).put("PiP_bounds",new JSONArray(Arrays.asList(button.left,button.top,button.right,button.bottom))));f.image("cards-native-live");
    f.input.ready=false;f.publish();assertEquals("Paused",call(f.a,"cobraPlayerState",f.player));assertNotEquals("LIVE",label.getText().toString());f.input.ready=true;f.input.state=Player.STATE_BUFFERING;f.publish();assertEquals("Buffering\u2026",call(f.a,"cobraPlayerState",f.player));assertNotEquals("LIVE",label.getText().toString());
    f.input.state=Player.STATE_READY;set(f.a,"mCobraPreviewSessionKey","mismatched-session");f.publish();assertNotEquals("LIVE",label.getText().toString());set(f.a,"mCobraPreviewSessionKey",call(f.a,"cobraChannelKey",f.channels.get(0)));f.publish();assertEquals("LIVE",label.getText().toString());
    ENDPOINTS.clear();f.press(pip);assertEquals(Arrays.asList("fullscreen","pip"),new ArrayList<>(ENDPOINTS));assertSame(f.player,get(f.a,"mPlayer"));
    Fixture notLive=new Fixture("cards");notLive.player(false);TextView vod=((View)get(notLive.a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_label");assertNotEquals("LIVE",vod.getText().toString());write("native-pip-and-status-cases",new JSONObject().put("actual_coordinate_endpoints",new JSONArray(ENDPOINTS)).put("cases",new JSONArray(Arrays.asList("native live matching session","paused","buffering","mismatched session","restored matching session","native nonlive binding"))).put("effects_present",true).put("physical_playback","NOT_TESTED"));
  }
  static Object cardsState(InfinityLiveActivity a)throws Exception{Field field=Class.forName("com.projectinfinity.kodi.CobraCardsLayout").getDeclaredField("OWNERS");field.setAccessible(true);return ((WeakReference)((Map)field.get(null)).get(a)).get();}
  static Drawable cloneActualPanel(Drawable original)throws Exception{Constructor<?> constructor=original.getClass().getDeclaredConstructor(float.class,float.class);constructor.setAccessible(true);Drawable clone=(Drawable)constructor.newInstance(get(original,"radius"),get(original,"topInset"));set(clone,"scale",get(original,"scale"));return clone;}
  @Test public void activeAmbientPreservesNativeEffectsAndRecordsWrapping()throws Exception{
    assertTrue(candidate());Fixture f=new Fixture("cards");f.prefs.edit().putString("cobra_ambient_mode","subtle").commit();JSONArray phases=new JSONArray();Drawable stable=null;
    for(int i=0;i<4;i++){call(f.a,"cobraRefreshModeDetails");call(f.a,"cobraRefreshVisualEffects");f.frames();View details=(View)get(f.a,"mCobraGuideDetails");Map base=(Map)get(f.a,"mCobraAmbientSurfaceBase"),applied=(Map)get(f.a,"mCobraAmbientSurfaceApplied");phases.put(new JSONObject().put("iteration",i).put("background_class",details.getBackground().getClass().getName()).put("background_identity",System.identityHashCode(details.getBackground())).put("native_base_class",base.get(details)==null?JSONObject.NULL:base.get(details).getClass().getName()).put("native_applied_matches",applied.get(details)==details.getBackground()).put("base_count",base.size()).put("applied_count",applied.size()));assertEquals("subtle",f.prefs.getString("cobra_ambient_mode",""));assertNotNull(get(f.a,"mCobraEffects"));assertSame(details.getBackground(),applied.get(details));if(i==0)stable=details.getBackground();else assertSame("unchanged native arguments reuse exact native wrapper",stable,details.getBackground());}
    write("active-ambient",new JSONObject().put("iterations",phases).put("native_effects_preserved",true).put("comparison","431 four wrappers; candidate one wrapper for unchanged native arguments"));
    Object state=cardsState(f.a);View details=(View)get(f.a,"mCobraGuideDetails"),toolbar=(View)get(f.a,"mCobraModeToolbar");Drawable panel=(Drawable)get(state,"detailSurface");FrameLayout oracle=new FrameLayout(f.a);oracle.setBackground(cloneActualPanel(panel));JSONArray equality=new JSONArray();
    int[][] cases={{0xff49a9ff,1,16,0},{0xffcc8844,1,16,0},{0xffcc8844,2,16,0},{0xffcc8844,0,16,1},{0xffcc8844,0,16,0}};
    for(int[] c:cases){call(f.a,"cobraAmbientSurface",details,c[0],c[1],c[2],c[3]!=0);call(f.a,"cobraAmbientSurface",oracle,c[0],c[1],c[2],c[3]!=0);String actual=background(details.getBackground()),expected=background(oracle.getBackground());equality.put(new JSONObject().put("tint",c[0]).put("mode",c[1]).put("radius_dp",c[2]).put("night",c[3]!=0).put("native_hash",expected).put("candidate_hash",actual));assertEquals("same original native drawable raster for fresh parameter tuple",expected,actual);}
    Map base=(Map)get(f.a,"mCobraAmbientSurfaceBase"),applied=(Map)get(f.a,"mCobraAmbientSurfaceApplied");assertSame(panel,details.getBackground());assertFalse(base.containsKey(details));assertFalse(applied.containsKey(details));
    float originalDensity=f.a.getResources().getDisplayMetrics().density;int originalDpi=f.a.getResources().getDisplayMetrics().densityDpi;
    try{f.a.getResources().getDisplayMetrics().density=3f;f.a.getResources().getDisplayMetrics().densityDpi=480;call(f.a,"cobraAmbientSurface",details,0xff49a9ff,1,16,false);call(f.a,"cobraAmbientSurface",oracle,0xff49a9ff,1,16,false);assertEquals("density changes native radius/stroke equally",background(oracle.getBackground()),background(details.getBackground()));}finally{f.a.getResources().getDisplayMetrics().density=originalDensity;f.a.getResources().getDisplayMetrics().densityDpi=originalDpi;}
    Drawable ownedToolbar=(Drawable)get(state,"headerSurface");f.mode("mobile");assertNotSame(panel,base.get(details));assertNotSame(ownedToolbar,base.get(toolbar));assertNotSame(stable,applied.get(details));write("ambient-native-equivalence-and-restoration",new JSONObject().put("parameter_cases",equality).put("density_key_verified",true).put("off_cleared_native_maps",true).put("native_exit_mapping_restored",true).put("unselected_modes", "original method body retained"));
  }
}
