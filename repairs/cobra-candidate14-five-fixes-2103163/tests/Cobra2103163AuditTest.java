package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.media.session.*;
import android.media.session.MediaController;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ServiceController;
import static org.junit.Assert.*;

/** Actual production UI/session code with a controllable ExoPlayer, not a decoder/device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103163AuditTest {
  final CobraNavigationUiTest ui=new CobraNavigationUiTest();
  InfinityLiveActivity a;Context app;ServiceController<InfinityExtendedBackgroundService> service;
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  @Before public void setup()throws Exception{
    ui.clock();app=RuntimeEnvironment.getApplication();
    app.getSharedPreferences("infinity_runtime",Context.MODE_PRIVATE).edit().clear().commit();
    Shadows.shadowOf((Application)app).grantPermissions(android.Manifest.permission.POST_NOTIFICATIONS,android.Manifest.permission.WAKE_LOCK);
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    a=ui.fixture(1);
  }
  @After public void cleanup()throws Exception{
    InfinityExtendedBackgroundService.stopMiniPlayback(app);
    if(service!=null)service.destroy();
    ui.clean(a);CobraVisualRenderer.clients.clear();
  }
  static final class ControlledPlayer implements InvocationHandler {
    int state=Player.STATE_READY;boolean playing=true;float volume=1;
    final ArrayList<String> commands=new ArrayList<>();final ArrayList<Player.Listener> listeners=new ArrayList<>();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},this);
    public Object invoke(Object p,Method m,Object[] args){
      String n=m.getName();
      if(n.equals("equals"))return p==args[0];if(n.equals("hashCode"))return System.identityHashCode(p);
      if(n.equals("getApplicationLooper"))return Looper.getMainLooper();if(n.equals("getPlaybackState"))return state;
      if(n.equals("getPlayWhenReady"))return playing;if(n.equals("isPlaying"))return playing&&state==Player.STATE_READY;
      if(n.equals("getVolume"))return volume;if(n.equals("getCurrentPosition"))return 1234L;
      if(n.equals("getVideoSize"))return androidx.media3.common.VideoSize.UNKNOWN;
      if(n.equals("addListener"))listeners.add((Player.Listener)args[0]);if(n.equals("removeListener"))listeners.remove(args[0]);
      if(n.equals("pause")){commands.add(n);playing=false;}if(n.equals("play")){commands.add(n);playing=true;}
      if(n.equals("prepare")||n.equals("release")||n.equals("stop")||n.equals("setMediaItem")||n.equals("setVideoTextureView")||n.equals("clearVideoTextureView")||n.equals("setWakeMode"))commands.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  ControlledPlayer mini(boolean enabled)throws Exception{
    call(a,"cobraShowGuideShell");ui.measure(a,800,600);
    ControlledPlayer p=new ControlledPlayer();put(a,"mCobraPreviewPlayer",p.player);put(a,"mCobraHealthForeground",true);
    ((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",enabled).commit();return p;
  }
  Intent begin(ControlledPlayer p)throws Exception{
    assertTrue((Boolean)call(a,"cobraBeginMiniBackgroundPlayback"));
    Intent intent=Shadows.shadowOf((Application)app).getNextStartedService();
    assertNotNull("Native foreground service must be requested",intent);assertTrue(intent.getAction().endsWith("MINI_BACKGROUND_START"));return intent;
  }
  InfinityExtendedBackgroundService promote(Intent intent){
    service=Robolectric.buildService(InfinityExtendedBackgroundService.class).create();
    InfinityExtendedBackgroundService s=service.get();s.onStartCommand(intent,0,1);return s;
  }
  @Test public void disabledBackgroundDoesNotRequestAService()throws Exception{ControlledPlayer p=mini(false);assertFalse((Boolean)call(a,"cobraBeginMiniBackgroundPlayback"));assertNull(Shadows.shadowOf((Application)app).getNextStartedService());assertTrue(p.commands.isEmpty());}
  @Test public void pausedPreviewDoesNotStartBackgroundPlayback()throws Exception{ControlledPlayer p=mini(true);p.playing=false;assertFalse((Boolean)call(a,"cobraBeginMiniBackgroundPlayback"));assertTrue(p.commands.isEmpty());}
  @Test public void fullscreenCannotAcquireMiniAudioLease()throws Exception{ControlledPlayer p=mini(true);put(a,"mPlayerOverlay",new FrameLayout(a));assertFalse((Boolean)call(a,"cobraBeginMiniBackgroundPlayback"));assertFalse(InfinityExtendedBackgroundService.keepsMiniPlayback(p.player));}
  @Test public void multiviewCannotAcquireMiniAudioLease()throws Exception{ControlledPlayer p=mini(true);put(a,"mMultiOverlay",new FrameLayout(a));assertFalse((Boolean)call(a,"cobraBeginMiniBackgroundPlayback"));}
  @Test public void stoppedActivityDoesNotStartANewForegroundService()throws Exception{ControlledPlayer p=mini(true);call(a,"onStop");assertNull(Shadows.shadowOf((Application)app).getNextStartedService());assertFalse(p.playing);}
  @Test public void pendingStartIsNotReportedAsRunning()throws Exception{ControlledPlayer p=mini(true);begin(p);assertTrue(InfinityExtendedBackgroundService.keepsMiniPlayback(p.player));assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertFalse(p.commands.contains("prepare"));}
  @Test public void rapidReturnCancelsPendingMediaPromotion()throws Exception{ControlledPlayer p=mini(true);Intent intent=begin(p);call(a,"cobraEndMiniBackgroundPlayback");promote(intent);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue(p.playing);assertNull(get(service.get(),"mediaSession"));}
  @Test public void promotedSessionUsesTheExactExistingPlayer()throws Exception{ControlledPlayer p=mini(true);promote(begin(p));assertTrue(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue(InfinityExtendedBackgroundService.keepsMiniPlayback(p.player));assertFalse(p.commands.contains("prepare"));assertFalse(p.commands.contains("setMediaItem"));assertFalse(p.commands.contains("release"));}
  @Test public void nativeControlsPauseAndPlayTheSameStream()throws Exception{
    ControlledPlayer p=mini(true);InfinityExtendedBackgroundService s=promote(begin(p));
    MediaSession session=(MediaSession)get(s,"mediaSession");assertNotNull(session);
    // Robolectric's MediaSession binder is a no-op. Execute the exact callback registered by production.
    MediaSession.Callback callback=(MediaSession.Callback)get(s,"mediaCallback");assertNotNull(callback);
    callback.onPause();ui.frames(2);assertFalse(p.playing);assertEquals(PlaybackState.STATE_PAUSED,InfinityExtendedBackgroundService.nativeState(p.player));
    Notification paused=(Notification)call(s,"buildNotification");assertEquals("Cobra • Paused",paused.extras.getCharSequence(Notification.EXTRA_TEXT));
    callback.onPlay();ui.frames(2);assertTrue(p.playing);assertEquals(PlaybackState.STATE_PLAYING,InfinityExtendedBackgroundService.nativeState(p.player));
    assertFalse(p.commands.contains("prepare"));assertFalse(p.commands.contains("setMediaItem"));
  }
  @Test public void nativeStopRemovesSessionAndDoesNotAutoplayOnReturn()throws Exception{
    ControlledPlayer p=mini(true);InfinityExtendedBackgroundService s=promote(begin(p));MediaSession session=(MediaSession)get(s,"mediaSession");
    ((MediaSession.Callback)get(s,"mediaCallback")).onStop();ui.frames(2);
    assertFalse(p.playing);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(s,"mediaSession"));
    call(a,"resumeCobraAfterBackground");assertFalse("Explicit stop must not resume itself",p.playing);
  }
  @Test public void returnReattachesVideoWithoutRestartOrRelease()throws Exception{ControlledPlayer p=mini(true);promote(begin(p));p.commands.clear();call(a,"cobraEndMiniBackgroundPlayback");assertTrue(p.commands.contains("setVideoTextureView"));assertFalse(p.commands.contains("pause"));assertFalse(p.commands.contains("prepare"));assertFalse(p.commands.contains("release"));assertFalse(InfinityExtendedBackgroundService.keepsMiniPlayback(p.player));}
  @Test public void playbackStatesAreTruthfulNotHardcodedPlaying(){ControlledPlayer p=new ControlledPlayer();assertEquals(PlaybackState.STATE_PLAYING,InfinityExtendedBackgroundService.nativeState(p.player));p.playing=false;assertEquals(PlaybackState.STATE_PAUSED,InfinityExtendedBackgroundService.nativeState(p.player));p.playing=true;p.state=Player.STATE_BUFFERING;assertEquals(PlaybackState.STATE_BUFFERING,InfinityExtendedBackgroundService.nativeState(p.player));p.state=Player.STATE_ENDED;assertEquals(PlaybackState.STATE_STOPPED,InfinityExtendedBackgroundService.nativeState(p.player));}
  @Test public void backgroundSettingHasAnActualOnOffSwitch()throws Exception{call(a,"showCobraBackgroundModePicker");ui.measure(a,800,600);Switch toggle=(Switch)a.getWindow().getDecorView().findViewWithTag("cobra-mini-background-switch");assertNotNull(toggle);assertFalse(toggle.isChecked());toggle.setChecked(true);assertTrue((Boolean)call(a,"cobraMiniBackgroundEnabled"));toggle.setChecked(false);assertFalse((Boolean)call(a,"cobraMiniBackgroundEnabled"));}
  @Test @SuppressWarnings("unchecked") public void fullscreenGroupsIncludeArabicBeyondOldCapAndNormalizeCachedNames()throws Exception{
    List<Object> all=(List<Object>)get(a,"mChannels");Object sample=all.get(0);all.clear();for(int i=0;i<12010;i++)all.add(sample);
    all.add(CobraNavigationUiTest.construct("Channel","fixture:arabic","Channel A"," Arabic\u00a0 ","","","https://example.invalid/a","",Collections.emptyMap()));
    all.add(CobraNavigationUiTest.construct("Channel","fixture:arabic2","Channel B","arabic","","","https://example.invalid/b","",Collections.emptyMap()));
    ListView list=new ListView(a);put(a,"mCobraPlayerDrawerList",list);call(a,"cobraRenderPlayerDrawer","CATEGORIES");
    ListAdapter adapter=list.getAdapter();boolean found=false;for(int i=0;i<adapter.getCount();i++)if("Arabic".equals(adapter.getItem(i)))found=true;assertTrue(found);
    call(a,"cobraRenderPlayerDrawer","GROUP:Arabic");assertEquals(2,list.getAdapter().getCount());
  }
  @Test public void groupSelectionIgnoresHarmlessCaseAndWhitespace()throws Exception{assertTrue((Boolean)call(a,"cobraGroupMatches","Arabic"," arabic\u00a0 "));assertFalse((Boolean)call(a,"cobraGroupMatches","Arabic","French"));}
  @Test public void filesAppPickerUsesGetContentWithoutPretendingPersistentGrants()throws Exception{
    call(a,"cobraLaunchFilePicker",991,"application/zip",new String[]{"application/zip","application/octet-stream"},false,true);
    Intent outer=Shadows.shadowOf(a).getNextStartedActivityForResult().intent;assertEquals(Intent.ACTION_CHOOSER,outer.getAction());
    Intent inner=outer.getParcelableExtra(Intent.EXTRA_INTENT);assertEquals(Intent.ACTION_GET_CONTENT,inner.getAction());assertNull(inner.getPackage());assertEquals("*/*",inner.getType());assertEquals(0,inner.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
  }
  @Test public void systemPickerRetainsPersistableReadPath()throws Exception{call(a,"cobraLaunchFilePicker",992,"*/*",new String[]{"video/*"},true,false);Intent i=Shadows.shadowOf(a).getNextStartedActivityForResult().intent;assertEquals(Intent.ACTION_OPEN_DOCUMENT,i.getAction());assertTrue((i.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)!=0);}
  JSONObject node(String slot,int x,int y,int w,int h)throws Exception{return new JSONObject().put("id",slot).put("type","slot").put("slot",slot).put("rect",new JSONArray(Arrays.asList(x,y,w,h)));}
  @Test public void themedChooserFitsInnerDisplayAndRetainsNativeButtonsOnResize()throws Exception{
    JSONObject scene=new JSONObject().put("width",1000).put("height",720).put("nodes",new JSONArray().put(node("enter.infinity",80,310,340,80)).put(node("settings.infinity",80,410,340,80)).put(node("enter.cobra",580,310,340,80)).put(node("settings.cobra",580,410,340,80)));
    Map<String,View> slots=new LinkedHashMap<>();final int[] clicks={0};for(String key:CobraVisualScene.CHOOSER_SLOTS){TextView t=new TextView(a);t.setText(key);t.setClickable(true);t.setOnClickListener(v->clicks[0]++);slots.put(key,t);}
    View root=CobraVisualScene.build(a,new CobraVisualRenderer(a),scene,slots,1000);assertNotNull(root);
    for(int[] size:new int[][]{{1000,500},{800,600},{1100,620}}){root.measure(View.MeasureSpec.makeMeasureSpec(size[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(size[1],View.MeasureSpec.EXACTLY));root.layout(0,0,size[0],size[1]);FrameLayout canvas=(FrameLayout)((ScrollView)root).getChildAt(0);assertTrue(canvas.getHeight()<=size[1]);for(View v:slots.values()){assertTrue(v.getWidth()>=44);assertTrue(v.getHeight()>=44);assertTrue(v.getBottom()<=size[1]);assertTrue(v.performClick());}}
    assertEquals(12,clicks[0]);
  }
  @Test public void moreSheetIsCenteredAndBoundedInPortraitAndLandscape()throws Exception{
    for(int[] size:new int[][]{{412,915},{900,460},{720,540}}){
      FrameLayout overlay=new FrameLayout(a);a.setContentView(overlay);put(a,"mPlayerOverlay",overlay);ui.measure(a,size[0],size[1]);
      call(a,"showPlayerSettingsDrawer");for(int frame=0;frame<6;frame++){overlay.measure(View.MeasureSpec.makeMeasureSpec(size[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(size[1],View.MeasureSpec.EXACTLY));overlay.layout(0,0,size[0],size[1]);}View panel=overlay.findViewWithTag("cobra_sheet_panel");assertNotNull(panel);
      assertEquals(size[0]/2f,(panel.getLeft()+panel.getRight())/2f,2f);assertTrue("panel top="+panel.getTop()+" height="+panel.getHeight()+" viewport="+size[1],panel.getTop()>=0);assertTrue("panel bottom="+panel.getBottom()+" viewport="+size[1],panel.getBottom()<=size[1]-64);
      call(a,"closeCobraActionSheet");
    }
  }
  @Test public void deniedPromotionPausesAndRemovesPendingLease()throws Exception{
    ControlledPlayer p=mini(true);Intent intent=begin(p);Shadows.shadowOf((Application)app).denyPermissions(android.Manifest.permission.POST_NOTIFICATIONS);
    promote(intent);assertFalse(p.playing);assertFalse(InfinityExtendedBackgroundService.keepsMiniPlayback(p.player));assertNull(get(service.get(),"mediaSession"));
  }
  @Test public void audioFocusLossStopsOnlyTheLeasedPreview()throws Exception{
    ControlledPlayer p=mini(true);InfinityExtendedBackgroundService s=promote(begin(p));
    ((android.media.AudioManager.OnAudioFocusChangeListener)get(s,"focusChange")).onAudioFocusChange(android.media.AudioManager.AUDIOFOCUS_LOSS);
    assertFalse(p.playing);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertFalse(p.commands.contains("release"));
  }
  @Test public void endedPlaybackRemovesPlayingNotification()throws Exception{
    ControlledPlayer p=mini(true);InfinityExtendedBackgroundService s=promote(begin(p));p.state=Player.STATE_ENDED;
    ((Player.Listener)get(s,"listener")).onEvents(p.player,null);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(s,"mediaSession"));
  }
  @Test @SuppressWarnings("unchecked") public void parserRetainsArabicAfterTwelveThousandEntries()throws Exception{
    StringBuilder playlist=new StringBuilder("#EXTM3U\n");for(int i=0;i<12005;i++)playlist.append("#EXTINF:-1 group-title=\"News\",Channel ").append(i).append("\nhttps://example.invalid/").append(i).append("\n");
    playlist.append("#EXTINF:-1 group-title=\"Arabic\",Arabic TV\nhttps://example.invalid/arabic\n");
    Object source=CobraNavigationUiTest.construct("LiveSource","fixture","m3u","Fixture","","","","https://example.invalid/list.m3u","");
    List<Object> channels=(List<Object>)call(a,"parseM3u",source,playlist.toString());assertEquals(12006,channels.size());assertEquals("Arabic",get(channels.get(12005),"group"));
  }

  @Test public void staleMediaCallbackCannotStopANewerLease()throws Exception{
    ControlledPlayer first=mini(true);InfinityExtendedBackgroundService owner=promote(begin(first));MediaSession.Callback stale=(MediaSession.Callback)get(owner,"mediaCallback");
    call(a,"cobraEndMiniBackgroundPlayback");ControlledPlayer next=mini(true);Intent intent=begin(next);owner.onStartCommand(intent,0,2);stale.onStop();assertTrue(next.playing);assertTrue(InfinityExtendedBackgroundService.keepsMiniPlayback(next.player));
  }
  @Test public void staleFocusCallbackCannotPauseANewerLease()throws Exception{
    ControlledPlayer first=mini(true);InfinityExtendedBackgroundService owner=promote(begin(first));android.media.AudioManager.OnAudioFocusChangeListener stale=(android.media.AudioManager.OnAudioFocusChangeListener)get(owner,"focusChange");
    call(a,"cobraEndMiniBackgroundPlayback");ControlledPlayer next=mini(true);owner.onStartCommand(begin(next),0,2);stale.onAudioFocusChange(android.media.AudioManager.AUDIOFOCUS_LOSS);assertTrue(next.playing);assertTrue(InfinityExtendedBackgroundService.keepsMiniPlayback(next.player));
  }
  @Test public void taskRemovalEndsAudioWithoutRestartingAStream()throws Exception{
    ControlledPlayer p=mini(true);InfinityExtendedBackgroundService owner=promote(begin(p));owner.onTaskRemoved(new Intent());assertFalse(p.playing);assertFalse(InfinityExtendedBackgroundService.keepsMiniPlayback(p.player));assertNull(get(owner,"mediaSession"));assertFalse(p.commands.contains("prepare"));
  }
  @Test public void nativePauseTimesOutWithoutLeavingAFakePlayingSession()throws Exception{
    ControlledPlayer p=mini(true);InfinityExtendedBackgroundService owner=promote(begin(p));((MediaSession.Callback)get(owner,"mediaCallback")).onPause();((Runnable)get(owner,"pausedTimeout")).run();assertFalse(p.playing);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(owner,"mediaSession"));
  }
  @Test @SuppressWarnings("unchecked") public void mainGuideUsesTheSameNormalizedArabicSelection()throws Exception{
    List<Object> channels=(List<Object>)get(a,"mChannels");channels.clear();channels.add(CobraNavigationUiTest.construct("Channel","fixture:a","Arabic TV"," arabic\u00a0 ","","","https://example.invalid/a","",Collections.emptyMap()));put(a,"mCategory","Arabic");assertEquals(1,((List<?>)call(a,"filteredChannels",false,false)).size());
  }
  @Test @SuppressWarnings("unchecked") public void sourceDisabledGroupsStayHiddenFromBothDirectories()throws Exception{
    List<Object> channels=(List<Object>)get(a,"mChannels");channels.clear();Object channel=CobraNavigationUiTest.construct("Channel","fixture:a","Arabic TV","Arabic","","","https://example.invalid/a","",Collections.emptyMap());channels.add(channel);
    String source=(String)call(a,"sourceIdForChannel",channel);((InfinityCobraFeatureRuntime)get(a,"mFeatures")).setSourceMeta(source,false,"#FF4059","");assertTrue(((Map<?,?>)call(a,"cobraProviderGroups",false)).isEmpty());assertTrue(((Map<?,?>)call(a,"cobraProviderGroups",true)).isEmpty());
  }
}
