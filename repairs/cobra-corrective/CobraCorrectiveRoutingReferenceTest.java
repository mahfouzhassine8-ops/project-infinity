package com.projectinfinity.kodi;

import android.view.View;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Iterator;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Runs unchanged on approved source first, then compares the candidate to that artifact. */
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class CobraCorrectiveRoutingReferenceTest {
  static void mode(CobraProHandoffTest h,String name)throws Exception{
    call(h.a,"showCobraViewModeMenu");View card=((View)get(h.a,"mCobraActionSheet")).findViewWithTag("cobra-view-mode:"+name);
    assertNotNull(name,card);assertTrue(card.performClick());h.f.measure(h.a,412,915);
  }
  static void sports(CobraProHandoffTest h)throws Exception{
    mode(h,"focus");Object game=h.addLiveGameForChannel(0);View tab=((View)get(h.a,"mCobraGuideBrowser")).findViewWithTag("pro_filter_4");
    assertNotNull(tab);assertTrue(tab.performClick());h.sportsMini(0,game);h.f.measure(h.a,412,915);
  }
  static JSONObject state(CobraProHandoffTest h)throws Exception{
    InfinityLiveActivity a=h.a;View hero=(View)get(a,"mCobraProHeroUi"),shell=(View)get(a,"mCobraGuideShell");
    return new JSONObject().put("mode",get(a,"mCobraGuideStyle")).put("saved_mode",h.prefs.getString("guide_view_mode",""))
      .put("owner",call(a,"cobraDrawerOwner")).put("pro_active",get(a,"mCobraProActive")).put("sports_section",get(a,"mCobraProSportsActive"))
      .put("sports_hero",call(a,"cobraProSportsHeroActive")).put("hero_present",hero!=null).put("hero_attached",hero!=null&&hero.isAttachedToWindow())
      .put("shell_present",shell!=null).put("shell_attached",shell!=null&&shell.isAttachedToWindow()).put("stage_title",get(a,"mCobraStageTitle"))
      .put("preview_same",get(a,"mCobraPreviewPlayer")==h.player).put("fullscreen_same",get(a,"mPlayer")==h.player)
      .put("player_released",h.state.released).put("prepare_count",h.state.prepares).put("media_change_count",h.state.changes);
  }
  static void assertReference(String key,JSONObject actual)throws Exception{
    String path=System.getProperty("cobra.corrective.routingBaseline");assertNotNull("Candidate needs the approved routing reference path",path);
    JSONObject root=new JSONObject(new String(Files.readAllBytes(new File(path).toPath()),StandardCharsets.UTF_8));assertEquals(1,root.getInt("schema"));
    JSONObject expected=root.getJSONObject("contexts").getJSONObject(key);assertEquals(key+" field count",expected.length(),actual.length());
    for(Iterator<String> it=expected.keys();it.hasNext();){String field=it.next();assertEquals(key+"."+field,expected.get(field),actual.get(field));}
  }
  @Test public void approvedNavigationReferenceAndCandidateEquivalence()throws Exception{
    JSONObject contexts=new JSONObject();
    for(String key:new String[]{"stopped_pro_sports","return_mobile","return_compact","return_cards","return_grid"}){
      CobraProHandoffTest h=new CobraProHandoffTest();h.setup();h.prefs.edit().putBoolean("cobra_live_rewind_enabled",false).commit();
      put(get(h.a,"mCobraPlaybackPolicy"),"resumed",true);put(get(h.a,"mCobraPlaybackPolicy"),"started",true);
      org.robolectric.Shadows.shadowOf((android.media.AudioManager)h.a.getSystemService(android.content.Context.AUDIO_SERVICE)).setNextFocusRequestResponse(android.media.AudioManager.AUDIOFOCUS_REQUEST_GRANTED);
      try{sports(h);
        if(key.equals("stopped_pro_sports")){call(h.a,"stopCobraPreview");call(h.a,"showCobraPrimaryView");}
        else{mode(h,key.substring(7));h.freshPlayer();put(h.a,"mGuidePreviewChannel",h.channel(0));put(h.a,"mCobraPreviewPlayer",h.player);put(h.a,"mCobraPreviewSessionKey",call(h.a,"cobraChannelKey",h.channel(0)));put(h.a,"mCobraPreviewMuted",false);
          call(h.a,"promoteCobraPreviewToFullscreen",h.channel(0));h.f.measure(h.a,412,915);View back=h.f.description((View)get(h.a,"mPlayerChrome"),"Return to preview");assertNotNull(back);assertTrue(back.performClick());}
        h.f.measure(h.a,412,915);JSONObject result=state(h);if(System.getProperty("cobra.corrective.routingBaseline")!=null)assertReference(key,result);contexts.put(key,result);
      }finally{call(h.a,"closePlayer");call(h.a,"stopCobraPreview");h.cleanup();}
    }
    File dir=new File(System.getProperty("cobra.corrective.evidence","."));assertTrue(dir.isDirectory()||dir.mkdirs());
    try(Writer out=new FileWriter(new File(dir,"ROUTING-REFERENCE.json"))){out.write(new JSONObject().put("schema",1).put("contexts",contexts).toString(2));}
  }
}
