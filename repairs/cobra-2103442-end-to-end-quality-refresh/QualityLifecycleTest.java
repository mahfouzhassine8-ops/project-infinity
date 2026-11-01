package com.projectinfinity.kodi;
import android.view.*;
import android.widget.*;
import java.util.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.robolectric.RuntimeEnvironment;

/** Native generation/publication and responsive state, no shutdown or external provider. */
public class QualityLifecycleTest extends ProApprovedLayoutTest {
 @Test public void generationErrorsAndFreshPublication()throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("cards",1080,2520,480,"dark");Object player=f.player,texture=get(f.a,"mCobraPreviewTexture");
  Object source=((List)get(f.a,"mSources")).get(0),original=((Map)get(f.a,"mCobraEpg")).get("qa");String identity=(String)call(f.a,"cobraEpgIdentity",source);
  Map requests=(Map)get(f.a,"mCobraEpgRequest");requests.put("qa",identity);
  long stale=(Long)call(f.a,"cobraNextEpgGeneration","qa"),current=(Long)call(f.a,"cobraNextEpgGeneration","qa");
  Object replacement=CobraCardsLayoutTest.construct("CobraEpgData");put(replacement,"identity",identity);put(replacement,"fetched",4102444800000L);
  Map programs=(Map)get(replacement,"programs");ArrayList<Object> full=new ArrayList<>(),shortGuide=new ArrayList<>();
  full.add(QualityRefreshTest.program("Replacement first",4102444800000L,4102448400000L));shortGuide.add(QualityRefreshTest.program("Fallback",4102452000000L,4102455600000L));
  programs.put("epg0",full);programs.put("@stream:qa:0",shortGuide);
  String ready="lambda$loadGuideAsync$61$com-projectinfinity-kodi-InfinityLiveActivity",done="lambda$loadGuideAsync$62$com-projectinfinity-kodi-InfinityLiveActivity";
  call(f.a,ready,source,stale,identity,replacement);assertSame(original,((Map)get(f.a,"mCobraEpg")).get("qa"));
  call(f.a,done,source,stale,identity,replacement);assertEquals(identity,requests.get("qa"));
  call(f.a,ready,source,current,identity,replacement);assertSame(replacement,((Map)get(f.a,"mCobraEpg")).get("qa"));
  Object next=call(f.a,"cobraNextProgram",f.channels.get(0));assertSame(full.get(0),next);
  put(full.get(0),"title","Fresh title without replacing list");assertEquals("Fresh title without replacing list",get(call(f.a,"cobraNextProgram",f.channels.get(0)),"title"));
  call(f.a,done,source,current,identity,replacement);assertFalse(requests.containsKey("qa"));
  assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));
  save("QUALITY-GENERATION-PUBLICATION",new JSONObject().put("stale_publication_ignored",true).put("stale_completion_keeps_new_request",true).put("current_publication_and_same_size_edit",true).put("player_surface_retained",true));
 }
 @Test public void fontScaleAndProSportsIsolation()throws Exception {
  JSONArray cases=new JSONArray();CobraCardsLayoutTest.Fixture f=pro(new int[]{1080,2520,480},"dark");Object player=f.player;
  for(int[] pane:new int[][]{{1080,2520,480},{1600,1800,240}})for(float font:new float[]{1f,1.4f,2f}){
   resize(f,pane);RuntimeEnvironment.setFontScale(font);
   for(String theme:new String[]{"light","dark","oled"})for(String mode:new String[]{"mobile","compact","grid","cards","focus"}){
    f.prefs.edit().putString("cobra_appearance_mode",theme).commit();f.mode(mode);call(f.a,"cobraRestyleGuide");call(f.a,"cobraLayoutGuide");frames();
    AbsListView rows=list(f);assertTrue(mode+" accessible guide",rows.isShown()&&rows.getWidth()>0&&rows.getHeight()>0&&rows.getChildCount()>0);
    View toolbar=(View)get(f.a,"mCobraModeToolbar");assertTrue(toolbar.isShown());assertSame(player,get(f.a,"mCobraPreviewPlayer"));
    cases.put(new JSONObject().put("pane",new JSONArray(pane)).put("font",font).put("theme",theme).put("mode",mode).put("rows",bounds(rows).toShortString()).put("visible",rows.getChildCount()));
   }
   f.mode("focus");put(f.a,"mCobraProSportsActive",true);call(f.a,"cobraLayoutGuide");frames();originalGeometry(f);put(f.a,"mCobraProSportsActive",false);
  }
  RuntimeEnvironment.setFontScale(1f);
  save("QUALITY-FONT-SPORTS",new JSONObject().put("cases",cases).put("count",cases.length()).put("Pro_Sports_geometry","ORIGINAL_POLICY").put("real_sports_network","NOT_EXERCISED"));
 }
}
