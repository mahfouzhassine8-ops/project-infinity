package com.projectinfinity.kodi;
import android.content.*;
import android.app.job.*;
import android.view.*;
import android.widget.*;
import android.graphics.*;
import java.util.*;
import java.io.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class ProTeams312Test {
 CobraNavigationUiTest f; InfinityLiveActivity a; CobraSportsPreferences choices; InfinityCobraFeatureRuntime runtime;
 @Before public void setup()throws Exception{f=new CobraNavigationUiTest();f.clock();a=f.fixture(8);choices=new CobraSportsPreferences(a);choices.prefs.edit().clear().putString("cobra_appearance_mode","dark").commit();put(a,"mPrefs",choices.prefs);runtime=(InfinityCobraFeatureRuntime)get(a,"mFeatures");a.getSharedPreferences(InfinityCobraFeatureRuntime.PREFS,0).edit().remove("reminders").commit();put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());}
 @After public void finish()throws Exception{f.clean(a);}
 Object game(String id,String away,String home,String state)throws Exception{Object g=SportsHubTest.game();put(g,"id",id);put(g,"away",SportsHubTest.team(away,"nfl|"+away,away,away,"17"));put(g,"home",SportsHubTest.team(home,"nfl|"+home,home,home,"24"));put(g,"state",state);put(g,"startMs",System.currentTimeMillis()+(state.equals("pre")?3600000L:-60000L));return g;}
 @SuppressWarnings("unchecked") void games(Object...values)throws Exception{((List<Object>)get(a,"mCobraSportsGames")).addAll(Arrays.asList(values));}
 void pro()throws Exception{choices.prefs.edit().putString("guide_view_mode","focus").commit();put(a,"mCobraGuideStyle","focus");call(a,"cobraShowGuideShell");f.measure(a,412,915);}
 String text(View view){String result=view instanceof TextView?((TextView)view).getText().toString():"";if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)result+="\n"+text(((ViewGroup)view).getChildAt(i));return result;}
 void save(String name)throws Exception{f.measure(a,412,915);View view=a.getWindow().getDecorView();Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));File file=new File(System.getProperty("cobra.evidence"),"teams/"+name+".png");file.getParentFile().mkdirs();try(FileOutputStream out=new FileOutputStream(file)){bitmap.compress(Bitmap.CompressFormat.PNG,100,out);}bitmap.recycle();}
 @Test public void priorityIsFavoriteThenPinnedThenFollowedInEverySportsList()throws Exception{
   Object ordinary=game("a","BUF","NYJ","in"),follow=game("b","CHI","GB","in"),pin=game("c","KC","ATL","in"),favorite=game("d","DET","MIN","in");
   choices.toggle(CobraSportsPreferences.FOLLOWS,"nfl|CHI");choices.toggle(CobraSportsPreferences.PINS,"nfl|KC");choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");games(ordinary,follow,pin,favorite);
   put(a,"mCobraProSportsSection","live");List<?> rows=(List<?>)call(a,"cobraProRowGames",false);assertEquals(Arrays.asList(favorite,pin,follow,ordinary),rows);
   put(a,"mCobraProSportsSection","myteams");assertEquals(Arrays.asList(favorite,pin,follow),call(a,"cobraProRowGames",false));
   assertSame(favorite,call(a,"cobraProPreferredSportsGame"));choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");assertSame(pin,call(a,"cobraProPreferredSportsGame"));
 }
 @Test public void preferencesPersistAndOriginalFollowsArePreserved(){choices.toggle(CobraSportsPreferences.FOLLOWS,"nfl|GB");choices.toggle(CobraSportsPreferences.PINS,"nfl|DET");choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");CobraSportsPreferences restored=new CobraSportsPreferences(a);assertEquals(0,restored.rank("nfl|DET"));assertEquals(2,restored.rank("nfl|GB"));restored.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");assertEquals(1,restored.rank("nfl|DET"));}
 @Test public void previewPriorityNeverOverridesManualSelectionOrRetunesOnRefresh()throws Exception{
   Object chosen=game("manual","BUF","NYJ","in"),favorite=game("fav","DET","GB","in");games(chosen,favorite);choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");pro();
   put(a,"mCobraProSportsGameId","manual");put(a,"mCobraProSportsManualSelection",true);Object texture=get(a,"mCobraPreviewTexture");call(a,"cobraProOnSportsDataChanged");assertSame(chosen,call(a,"cobraProCurrentSportsGame"));assertSame(texture,get(a,"mCobraPreviewTexture"));
   put(a,"mCobraProSportsManualSelection",false);assertSame(favorite,call(a,"cobraProCurrentSportsGame"));
 }
 @Test public void twoPinnedTeamsAndManualReminderShareOneAlarm()throws Exception{
   choices.toggle(CobraSportsPreferences.PINS,"nfl|DET");choices.toggle(CobraSportsPreferences.PINS,"nfl|GB");Object g=game("both","DET","GB","pre");games(g);call(a,"cobraSyncSportsReminders");assertEquals(1,runtime.reminders().length());
   call(a,"cobraSportsToggleGameReminder",g);assertEquals(1,runtime.reminders().length());JSONObject item=runtime.sportsReminder("nfl|both");assertTrue(item.optBoolean("automatic"));assertTrue(item.optBoolean("manual"));
   assertFalse(runtime.consumeSportsReminder("sports:nfl|both"));org.robolectric.shadows.ShadowSystemClock.advanceBy(java.time.Duration.ofMinutes(55));assertTrue(runtime.consumeSportsReminder("sports:nfl|both"));assertFalse(runtime.consumeSportsReminder("sports:nfl|both"));
 }
 @Test public void unpinKeepsIndependentReminderAndRemovalDoesNotRecreateIt()throws Exception{
   long start=System.currentTimeMillis()+3600000;choices.toggle(CobraSportsPreferences.PINS,"nfl|DET");runtime.sportsReminder("nfl|1","nfl|DET","nfl|GB","Lions @ Packers",start,true,true);
   choices.toggle(CobraSportsPreferences.PINS,"nfl|DET");runtime.reconcileSportsReminders();assertTrue(runtime.sportsReminder("nfl|1").optBoolean("manual"));assertFalse(runtime.sportsReminder("nfl|1").optBoolean("automatic"));
   runtime.sportsReminder("nfl|1","nfl|DET","nfl|GB","Lions @ Packers",start,false,false);assertNull(runtime.sportsReminder("nfl|1"));
 }
 @Test public void removingManualReminderLeavesAutomaticTeamReminder()throws Exception{
   Object g=game("one","DET","GB","pre");games(g);choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");call(a,"cobraSyncSportsReminders");call(a,"cobraSportsToggleGameReminder",g);call(a,"cobraSportsToggleGameReminder",g);
   JSONObject item=runtime.sportsReminder("nfl|one");assertTrue(item.optBoolean("automatic"));assertFalse(item.optBoolean("manual"));
 }
 @Test public void automaticRemindersUpdateAirtimeAndCancelFinishedGames()throws Exception{
   Object g=game("move","DET","GB","pre");games(g);choices.toggle(CobraSportsPreferences.PINS,"nfl|DET");call(a,"cobraSyncSportsReminders");long old=runtime.sportsReminder("nfl|move").optLong("when");
   put(g,"startMs",((Long)get(g,"startMs"))+3600000);call(a,"cobraSyncSportsReminders");assertEquals(old+3600000,runtime.sportsReminder("nfl|move").optLong("when"));put(g,"state","post");call(a,"cobraSyncSportsReminders");assertNull(runtime.sportsReminder("nfl|move"));
 }
 @Test public void backgroundScheduleIngestOnlyAddsChosenTeamsAndHonorsCancellation()throws Exception{
   choices.toggle(CobraSportsPreferences.PINS,"nfl|8");String date=new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm'Z'",Locale.US).format(new Date(System.currentTimeMillis()+86400000));
   JSONObject event=new JSONObject().put("id","88").put("name","Packers at Lions").put("date",date).put("status",new JSONObject().put("type",new JSONObject().put("state","pre"))).put("competitions",new JSONArray().put(new JSONObject().put("competitors",new JSONArray().put(new JSONObject().put("homeAway","home").put("team",new JSONObject().put("id","8"))).put(new JSONObject().put("homeAway","away").put("team",new JSONObject().put("id","9"))))));
   JSONObject root=new JSONObject().put("events",new JSONArray().put(event));CobraSportsReminderJob.ingest(a,"nfl",root);assertNotNull(runtime.sportsReminder("nfl|88"));event.getJSONObject("status").getJSONObject("type").put("name","STATUS_POSTPONED");CobraSportsReminderJob.ingest(a,"nfl",root);assertNull(runtime.sportsReminder("nfl|88"));
 }
 @Test public void backgroundJobIsOptInPersistentAndUsesNetworkConstraint(){CobraSportsReminderJob.schedule(a);JobScheduler s=(JobScheduler)a.getSystemService(Context.JOB_SCHEDULER_SERVICE);assertTrue(s.getAllPendingJobs().isEmpty());choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|8");CobraSportsReminderJob.schedule(a);JobInfo job=s.getAllPendingJobs().get(0);assertTrue(job.isPersisted());assertEquals(JobInfo.NETWORK_TYPE_ANY,job.getNetworkType());assertEquals(6*3600000L,job.getIntervalMillis());}
 @Test public void spoilerProtectionRedactsRowsHeroStatsAndAccessibility()throws Exception{
   Object g=game("hidden","DET","GB","in");put(g,"detail","Lions win 24-17");games(g);choices.protection(true);
   CobraProUi.SportsGame data=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",g);assertEquals("Scores hidden",data.score);assertFalse(data.status.contains("24"));
   CobraProUi.Program hero=(CobraProUi.Program)call(a,"cobraProSportsProgram",g);assertFalse(hero.sportsScore.contains("24"));assertFalse(hero.sportsMeta.contains("win"));
   CobraProUi.GameRow row=new CobraProUi.GameRow(a,false,()->{},()->{});row.bind(data,(v,u)->{});assertFalse(row.getContentDescription().toString().contains("24"));
   call(a,"showCobraSportsStats",g);assertEquals("sports-reveal-stats",get(a,"mCobraSheetKind"));assertFalse(text((View)get(a,"mCobraActionSheet")).contains("24"));
 }
 @Test public void revealingOneGameLeavesOthersProtectedAndToggleResetsReveals()throws Exception{
   Object first=game("first","DET","GB","in"),second=game("second","ATL","BUF","in");choices.protection(true);call(a,"cobraSportsReveal",first);
   assertTrue(((String)call(a,"cobraSportsScoreLine",first)).contains("24"));assertFalse(((String)call(a,"cobraSportsScoreLine",second)).contains("24"));choices.protection(false);choices.protection(true);assertEquals(true,call(a,"cobraSportsHidden",first));
 }
 @Test public void gameOptionsContainIndependentReminderTeamChoicesAndExistingRecording()throws Exception{
   Object game=game("upcoming","DET","GB","pre");call(a,"cobraProSportsOptions",game);String copy=text((View)get(a,"mCobraActionSheet"));assertTrue(copy.contains("Set a Reminder"));assertTrue(copy.contains("Record / Schedule from guide"));assertTrue(copy.contains("DET"));assertTrue(copy.contains("GB"));save("game-options");
 }
 @Test public void proPreviewMuteBadgeIsGoneInBothThemes()throws Exception{
   pro();CobraProUi.Hero hero=(CobraProUi.Hero)get(a,"mCobraProHeroUi");assertEquals(View.GONE,hero.muted.getVisibility());assertEquals(View.GONE,hero.muteIcon.getVisibility());hero.setState(CobraProUi.PREVIEW,null,false);assertEquals(View.GONE,hero.muted.getVisibility());assertEquals(View.GONE,hero.muteIcon.getVisibility());
 }
 @Test public void tickerRespectsProtectionAndPipWithoutChangingPlayers()throws Exception{
   Object g=game("ticker","DET","GB","in");games(g);pro();choices.prefs.edit().putBoolean(CobraSportsPreferences.TICKER,true).commit();FrameLayout host=new FrameLayout(a);put(a,"mPlayerOverlay",host);put(get(a,"mCobraPlaybackPolicy"),"resumed",true);choices.protection(true);call(a,"cobraRefreshScoreTicker");
   TextView ticker=(TextView)get(a,"mCobraScoreTicker");assertNotNull(ticker);assertFalse(ticker.getText().toString().contains("24"));assertNull(get(a,"mPlayer"));put(a,"mInPictureInPicture",true);call(a,"cobraRefreshScoreTicker");assertNull(get(a,"mCobraScoreTicker"));assertEquals(0,host.getChildCount());
 }
 @Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()throws Exception{
   games(game("live","DET","GB","in"));pro();f.drawer(a,"Sports");f.measure(a,412,915);assertTrue((Boolean)get(a,"mCobraProSportsActive"));assertEquals(true,call(a,"cobraSurfaceMatchesDrawerOwner"));
   call(a,"cobraProSportsTab",2);call(a,"cobraRenderGuideBrowser");assertEquals("upcoming",get(a,"mCobraProSportsSection"));call(a,"cobraProFilter",3);assertEquals("live",call(a,"cobraDrawerOwner"));
 }
 @Test public void renderNewControlsAcrossThemesAndSportsSettings()throws Exception{
   games(game("favorite","DET","GB","in"),game("pinned","KC","ATL","in"));choices.toggle(CobraSportsPreferences.FAVORITES,"nfl|DET");choices.toggle(CobraSportsPreferences.PINS,"nfl|KC");pro();call(a,"cobraProFilter",4);f.frames(30);save("favorite-and-pinned");choices.protection(true);call(a,"cobraSportsPresentationChanged");save("spoiler-protection");call(a,"showCobraSportsSettings");save("sports-settings");
 }
}
