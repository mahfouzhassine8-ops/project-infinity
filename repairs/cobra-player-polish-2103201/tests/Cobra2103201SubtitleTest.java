package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import androidx.media3.common.*;
import androidx.media3.common.text.Cue;
import androidx.media3.common.text.CueGroup;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real Android sheets and caption adapter with controlled Media3 track/cue inputs.
 * Does not establish provider subtitle availability, subtitle decoding or physical rendering. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103201SubtitleTest {
  CobraNavigationUiTest ui;InfinityLiveActivity a;PlayerDouble fake;Object binding,channel;Locale previousLocale;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}

  static class PlayerDouble implements InvocationHandler {
    final ExoPlayer player;TrackSelectionParameters params;Tracks tracks=Tracks.EMPTY;int parameterWrites;
    PlayerDouble(Context context){params=new TrackSelectionParameters.Builder(context).build();player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);}
    public Object invoke(Object p,Method method,Object[] args){String n=method.getName();
      if(n.equals("toString"))return "Controlled subtitle player";if(n.equals("hashCode"))return System.identityHashCode(p);if(n.equals("equals"))return p==args[0];
      if(n.equals("getTrackSelectionParameters"))return params;if(n.equals("getCurrentTracks"))return tracks;
      if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;
      if(n.equals("setTrackSelectionParameters")){params=(TrackSelectionParameters)args[0];parameterWrites++;return null;}
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return true;
      Class<?> type=method.getReturnType();if(type==boolean.class)return false;if(type==int.class)return 0;if(type==long.class)return 0L;if(type==float.class)return 0f;if(type==double.class)return 0d;return null;
    }
  }

  static Tracks.Group group(String id,String mime,String language,boolean supported,boolean selected){
    Format format=new Format.Builder().setId(id).setSampleMimeType(mime).setLanguage(language).build();
    return new Tracks.Group(new TrackGroup(id,format),false,new int[]{supported?C.FORMAT_HANDLED:C.FORMAT_UNSUPPORTED_TYPE},new boolean[]{selected});
  }
  void tracks(Tracks.Group...groups){fake.tracks=new Tracks(Arrays.asList(groups));}
  View root(){return a.getWindow().getDecorView();}
  View tag(String tag){return root().findViewWithTag(tag);}
  TextView text(View v,String value){
    if(v instanceof TextView&&value.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){TextView found=text(((ViewGroup)v).getChildAt(i),value);if(found!=null)return found;}
    return null;
  }
  void open()throws Exception{call(a,"showTrackChooser");ui.measure(a,412,915);assertEquals("tracks",get(a,"mCobraSheetKind"));}
  void cue()throws Exception{call(binding,"onCues",new CueGroup(Collections.singletonList(new Cue.Builder().setText("Visible supplied caption").build()),0L));}
  View captions()throws Exception{return (View)get(binding,"captions");}
  @Before @SuppressWarnings("unchecked") public void before()throws Exception{
    previousLocale=Locale.getDefault();Locale.setDefault(Locale.US);CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);call(a,"cobraOpenLiveTv");ui.measure(a,412,915);
    channel=((List<?>)get(a,"mChannels")).get(0);fake=new PlayerDouble(a);
    binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,fake.player,channel);
    ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(fake.player,binding);
    put(a,"mPlayer",fake.player);put(a,"mPlaying",channel);
    FrameLayout overlay=new FrameLayout(a);((FrameLayout)root()).addView(overlay,new FrameLayout.LayoutParams(-1,-1));put(a,"mPlayerOverlay",overlay);
    android.view.TextureView texture=new android.view.TextureView(a);overlay.addView(texture,new FrameLayout.LayoutParams(-1,-1));
    call(a,"cobraAttachVideo",fake.player,texture);ui.measure(a,412,915);
  }
  @After public void after()throws Exception{if(a!=null)ui.clean(a);CobraVisualRenderer.clients.clear();if(previousLocale!=null)Locale.setDefault(previousLocale);}

  @Test public void audioOnlyShowsMissingSubtitlesAndNeverClaimsOffSelectedWhenNotDisabled()throws Exception{
    tracks(group("audio","audio/mp4a-latm","und",true,true));open();
    assertNotNull(text(root(),"No subtitle tracks available in this stream."));
    assertNotNull(text(root(),"Audio track 1"));assertNull(text(root(),"und"));
    assertFalse(tag("cobra-track-off").isSelected());assertTrue(tag("cobra-track:0:0").isSelected());
    Cobra2103201MenuPolishTest.capture(a,ui,"cobra201-audio-only-412x915",412,915);
  }

  @Test public void savedEnglishRemainsPreferenceWhenNoTextIsSupplied()throws Exception{
    String key=(String)call(a,"cobraPreferenceKey",channel);Object p=call(a,"cobraReadPreferences",key);put(p,"subtitles","en");
    assertEquals(true,call(a,"cobraSavePreferences",channel,key,p,false));
    assertEquals(Collections.singletonList("en"),fake.params.preferredTextLanguages);assertFalse(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    call(a,"cobraShowChannelPreferences",channel);ui.measure(a,412,915);
    assertNotNull(text(root(),"Preferred subtitles"));assertNotNull(text(root(),"English • when available"));
    tracks(group("audio","audio/mp4a-latm","und",true,true));open();
    assertNotNull(text(root(),"No subtitle tracks available in this stream."));assertNull(text(root(),"English"));
  }

  @Test public void currentEnglishSelectsActualTextGroupWithoutOverwritingSavedDefault()throws Exception{
    String key=(String)call(a,"cobraPreferenceKey",channel);Object saved=call(a,"cobraReadPreferences",key);put(saved,"subtitles","off");call(a,"cobraSavePreferences",channel,key,saved,false);
    Tracks.Group text=group("english","text/vtt","en",true,false);tracks(text);open();assertTrue(tag("cobra-track-off").isSelected());
    assertNotNull(text(root(),"English"));assertTrue(tag("cobra-track:0:0").performClick());
    assertFalse(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    assertTrue(fake.params.overrides.containsKey(text.getMediaTrackGroup()));
    assertEquals("off",new JSONObject(((SharedPreferences)get(a,"mPrefs")).getString(key,"")).getString("subtitles"));
    cue();assertEquals(View.VISIBLE,captions().getVisibility());
  }

  @Test public void fullscreenOffClearsDisplayedCaptionImmediatelyWithoutWaitingForNewCue()throws Exception{
    tracks(group("english","text/vtt","en",true,true));cue();assertEquals(View.VISIBLE,captions().getVisibility());open();
    assertTrue(tag("cobra-track-off").performClick());assertTrue(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    assertEquals(View.GONE,captions().getVisibility());open();assertTrue(tag("cobra-track-off").isSelected());
  }

  @Test public void delayedTrackDiscoveryRefreshesExistingSheetAndKeepsFocus()throws Exception{
    tracks(group("audio","audio/mp4a-latm","und",true,true));open();View sheet=tag("cobra_themed_sheet");View off=tag("cobra-track-off");
    // Exercise focus navigation, not a touch-mode row that intentionally cannot take focus.
    // This public Android operation exits touch mode without changing the control's flags.
    System.out.println("Subtitle focus setup: touch="+off.isInTouchMode()+", focusable="+off.isFocusable()+", focusableInTouch="+off.isFocusableInTouchMode());
    assertTrue("Off row must accept focus navigation before track discovery",off.requestFocusFromTouch());
    assertFalse("Focus restoration is tested outside touch mode",off.isInTouchMode());
    assertTrue("Initial focus must be established before rows change",off.hasFocus());
    tracks(group("audio","audio/mp4a-latm","und",true,true),group("english","text/vtt","en",true,true));
    call(binding,"onTracksChanged",fake.tracks);ui.measure(a,412,915);
    assertSame(sheet,tag("cobra_themed_sheet"));assertNull(text(root(),"No subtitle tracks available in this stream."));
    assertNotNull("Discovered English track must be visible",text(root(),"English"));
    assertTrue("Selected English state must match the current track",tag("cobra-track:1:0").isSelected());
    assertTrue("The same Off action must retain focus after row replacement",tag("cobra-track-off").hasFocus());
    Cobra2103201MenuPolishTest.capture(a,ui,"cobra201-english-track-412x915",412,915);
  }

  @Test public void unsupportedSubtitlesAreExplainedButNeverSelectable()throws Exception{
    tracks(group("unsupported","text/vtt","en",false,false),group("audio","audio/mp4a-latm","en",true,true));open();
    assertNotNull(text(root(),"Subtitle tracks are present but unsupported on this player."));assertNull(tag("cobra-track:0:0"));assertNotNull(tag("cobra-track:1:0"));
  }

  @Test public void staleRemovedTrackRowCannotSelectOrCloseReplacementSheet()throws Exception{
    tracks(group("english","text/vtt","en",true,false));open();View old=tag("cobra-track:0:0");int writes=fake.parameterWrites;
    tracks(group("spanish","text/vtt","es",true,false));call(binding,"onTracksChanged",fake.tracks);View sheet=tag("cobra_themed_sheet");
    old.performClick();assertSame(sheet,tag("cobra_themed_sheet"));assertEquals(writes,fake.parameterWrites);
    call(a,"cobraShowChannelPreferences",channel);sheet=tag("cobra_themed_sheet");old.performClick();assertSame(sheet,tag("cobra_themed_sheet"));
  }

  @Test public void staleSessionAndClosedSheetCallbacksDoNothing()throws Exception{
    tracks(group("english","text/vtt","en",true,false));open();View row=tag("cobra-track:0:0");int writes=fake.parameterWrites;
    put(a,"mPlayer",new PlayerDouble(a).player);row.performClick();assertEquals(writes,fake.parameterWrites);
    call(a,"closeCobraActionSheet");call(binding,"onTracksChanged",fake.tracks);assertNull(get(a,"mCobraTrackSheetPlayer"));assertNull(get(a,"mCobraTrackSheetRows"));assertNull(tag("cobra_themed_sheet"));
  }

  @Test public void previewToggleUsesExistingSelectionAndClearsCueAfterFullscreenHandoff()throws Exception{
    tracks(group("english","text/vtt","en",true,true));cue();assertEquals(View.VISIBLE,captions().getVisibility());
    // Same production binding/session transferred to the preview ownership slot.
    put(a,"mPlayer",null);put(a,"mCobraPreviewPlayer",fake.player);call(a,"toggleCobraPreviewCaptions");
    assertTrue(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertEquals(View.GONE,captions().getVisibility());
    call(a,"toggleCobraPreviewCaptions");assertFalse(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertTrue(fake.params.selectUndeterminedTextLanguage);
    cue();assertEquals(View.VISIBLE,captions().getVisibility());
  }

  @Test public void externalDisableCallbackImmediatelyClearsCueAndUpdatesOpenChooser()throws Exception{
    tracks(group("english","text/vtt","en",true,true));cue();open();
    fake.params=fake.params.buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_TEXT,true).build();
    call(binding,"onTrackSelectionParametersChanged",fake.params);
    assertEquals(View.GONE,captions().getVisibility());assertTrue(tag("cobra-track-off").isSelected());assertFalse(tag("cobra-track:0:0").isSelected());
  }

  @Test public void previewWithoutCurrentSessionCannotAlterReplacementOrCreateRequestedState()throws Exception{
    put(a,"mPlayer",null);put(a,"mCobraPreviewPlayer",null);call(a,"toggleCobraPreviewCaptions");assertEquals(0,fake.parameterWrites);
    PlayerDouble next=new PlayerDouble(a);put(a,"mCobraPreviewPlayer",next.player);call(a,"toggleCobraPreviewCaptions");assertEquals(0,next.parameterWrites);
  }

  @Test public void realFullscreenReturnNewPreviewHostAndStopRefreshSubtitleButtonWithoutTrackEvents()throws Exception{
    tracks(group("english","text/vtt","en",true,true));
    View originalHost=(View)get(a,"mCobraPreviewHost");
    View originalButton=originalHost.findViewWithTag("cobra_preview_captions");assertFalse(originalButton.isSelected());
    int writes=fake.parameterWrites;
    call(a,"closeFullscreenToCobraView");ui.measure(a,412,915);
    assertSame(fake.player,get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayer"));
    assertTrue(((View)get(a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_captions").isSelected());
    assertEquals(writes,fake.parameterWrites);
    // Shell recreation can construct a host after tracks are already selected.
    put(a,"mCobraPreviewHost",null);
    View rebuilt=(View)call(a,"cobraPreviewPanel",channel,false);
    View rebuiltButton=rebuilt.findViewWithTag("cobra_preview_captions");assertTrue(rebuiltButton.isSelected());
    assertEquals("Turn subtitles off",rebuiltButton.getContentDescription());
    call(a,"stopCobraPreviewPlayerOnly");assertFalse(rebuiltButton.isSelected());
    assertEquals("Turn subtitles on when available",rebuiltButton.getContentDescription());
  }

  @Test public void explicitPreviewOnSelectsPreferredSupportedTrackAndPreservesValidSessionOverride()throws Exception{
    String key=(String)call(a,"cobraPreferenceKey",channel);Object saved=call(a,"cobraReadPreferences",key);put(saved,"subtitles","en");call(a,"cobraSavePreferences",channel,key,saved,false);
    String stored=((SharedPreferences)get(a,"mPrefs")).getString(key,"");
    Tracks.Group spanish=group("es","text/vtt","es",true,false),english=group("en","text/vtt","en",true,false);
    tracks(spanish,english);fake.params=fake.params.buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_TEXT,true).build();
    put(a,"mPlayer",null);put(a,"mCobraPreviewPlayer",fake.player);call(a,"toggleCobraPreviewCaptions");
    assertTrue(fake.params.overrides.containsKey(english.getMediaTrackGroup()));assertFalse(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    assertEquals(stored,((SharedPreferences)get(a,"mPrefs")).getString(key,""));
    // A valid explicit current-session choice takes priority over the saved language.
    fake.params=fake.params.buildUpon().setOverrideForType(new TrackSelectionOverride(spanish.getMediaTrackGroup(),0)).setTrackTypeDisabled(C.TRACK_TYPE_TEXT,true).build();
    call(a,"toggleCobraPreviewCaptions");assertTrue(fake.params.overrides.containsKey(spanish.getMediaTrackGroup()));
    assertEquals(stored,((SharedPreferences)get(a,"mPrefs")).getString(key,""));
  }

  @Test public void previewOnBeforeDiscoverySelectsNondefaultEnglishOnceAndOffCancelsPendingChoice()throws Exception{
    put(a,"mPlayer",null);put(a,"mCobraPreviewPlayer",fake.player);call(a,"toggleCobraPreviewCaptions");
    assertTrue(fake.params.selectUndeterminedTextLanguage);assertTrue(fake.params.overrides.isEmpty());
    Tracks.Group english=group("english","text/vtt","en",true,false);tracks(english);call(binding,"onTracksChanged",fake.tracks);
    assertTrue("Enabling text alone cannot select an ordinary language-tagged nondefault track",fake.params.overrides.containsKey(english.getMediaTrackGroup()));
    int writes=fake.parameterWrites;call(binding,"onTracksChanged",fake.tracks);assertEquals("No repeated selection loop",writes,fake.parameterWrites);
    call(a,"toggleCobraPreviewCaptions");assertTrue(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertTrue(fake.params.overrides.isEmpty());
    writes=fake.parameterWrites;call(binding,"onTracksChanged",fake.tracks);assertEquals("Off cannot be undone by later discovery",writes,fake.parameterWrites);
  }
}
