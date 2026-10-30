package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Application;
import android.content.SharedPreferences;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowChoreographer;
import org.robolectric.shadows.ShadowSystemClock;

/** Real native shell/layout/render/projection and profile API; no core stubs. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
  qualifiers="w941dp-h1672dp-port-mdpi",instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraCardsReuseNativeTest {
  @Before public void pausedFrames(){ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));}
  static Object get(Object o,String n)throws Exception{return CobraSettingsReturnBaselineTest.get(o,n);}
  static void set(Object o,String n,Object v)throws Exception{CobraSettingsReturnBaselineTest.set(o,n,v);}
  static Object call(Object o,String n,Object...a)throws Exception{return CobraSettingsReturnBaselineTest.call(o,n,a);}
  static Object construct(String n,Object...a)throws Exception{return CobraSettingsReturnBaselineTest.construct(n,a);}
  static CobraSettingsReturnBaselineTest.Fixture fixture(int count)throws Exception{return new CobraSettingsReturnBaselineTest.Fixture(true,count);}
  static GridView grid(CobraSettingsReturnBaselineTest.Fixture f)throws Exception{return (GridView)get(f.a,"mCobraGuideList");}
  static Object state(Activity a)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.CobraCardsReuse");Method m=c.getDeclaredMethod("existing",Activity.class);m.setAccessible(true);return m.invoke(null,a);
  }
  static boolean tryReuse(Activity a)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.CobraCardsReuse");return (Boolean)c.getMethod("tryReuse",Activity.class).invoke(null,a);
  }
  static void helper(String name,Activity a)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.CobraCardsReuse");c.getMethod(name,Activity.class).invoke(null,a);
  }
  static void write(String name,JSONObject report)throws Exception{
    Path out=Paths.get(System.getProperty("reuse.output"));Files.createDirectories(out);
    Files.write(out.resolve(name+".json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
    System.out.println("COBRA_CARDS_REUSE="+name+" "+report.getString("status"));
  }
  static List<Object> adapterItems(GridView g){List<Object> items=new ArrayList<>();for(int i=0;i<g.getCount();i++)items.add(g.getAdapter().getItem(i));return items;}
  static void sameItems(List<Object> before,GridView after){assertEquals(before.size(),after.getCount());for(int i=0;i<before.size();i++)assertSame("Original Channel reference "+i,before.get(i),after.getAdapter().getItem(i));}
  static void shellReturn(CobraSettingsReturnBaselineTest.Fixture f)throws Exception{call(f.a,"cobraShowGuideShell");f.layout();}
  static JSONObject retainedCardDiagnostic(CobraSettingsReturnBaselineTest.Fixture f,View card,Object selected)throws Exception{
    Class<?> tiles=Class.forName("com.projectinfinity.kodi.CobraCardsTiles");Method method=tiles.getDeclaredMethod("holder",LinearLayout.class);method.setAccessible(true);
    Object holder=method.invoke(null,card),bound=get(holder,"bound"),preview=get(f.a,"mGuidePreviewChannel");GridView grid=grid(f);View focus=grid.findFocus();
    JSONObject metrics=new JSONObject();for(String field:new String[]{"adapterPosition","measuredRow","measuredWidth","configuredHeight","measuredFont","configuredWidth","configuredFont","requiredNowHeight","contentGeneration","configuredContentGeneration","configuring","rowSyncPending","selectionAfterResize","hasLive","start","stop"})metrics.put(field,get(holder,field));
    Object boundAdapter=((java.lang.ref.WeakReference<?>)get(holder,"boundAdapter")).get(),measuredAdapter=((java.lang.ref.WeakReference<?>)get(holder,"measuredAdapter")).get();
    metrics.put("measuredLabels",new JSONArray((String[])get(holder,"measuredLabels"))).put("measuredTextHeights",new JSONArray((int[])get(holder,"measuredTextHeights")));
    ViewGroup.LayoutParams params=card.getLayoutParams();Object programme=call(f.a,"cobraCurrentProgram",selected);android.graphics.drawable.Drawable surface=card.getBackground();
    return new JSONObject().put("card_identity",System.identityHashCode(card)).put("card_class",card.getClass().getName()).put("tag",card.getTag())
      .put("bound_channel_id",bound==null?JSONObject.NULL:get(bound,"id")).put("selected_variable_id",get(selected,"id")).put("preview_channel_id",preview==null?JSONObject.NULL:get(preview,"id"))
      .put("native_selected_variable",call(f.a,"cobraModeSelected",selected)).put("native_selected_bound",bound==null?JSONObject.NULL:call(f.a,"cobraModeSelected",bound)).put("view_selected",card.isSelected())
      .put("view_focused",card.isFocused()).put("view_has_focus",card.hasFocus()).put("focus_identity",focus==null?JSONObject.NULL:System.identityHashCode(focus)).put("focus_tag",focus==null?JSONObject.NULL:focus.getTag())
      .put("surface_class",surface.getClass().getName()).put("surface_selected",get(surface,"selected")).put("surface_focused",get(surface,"focus")).put("drawable_state",new JSONArray(card.getDrawableState()))
      .put("native_current_programme",programme==null?JSONObject.NULL:get(programme,"title")).put("actual_now_text",String.valueOf(((TextView)get(card,"now")).getText())).put("actual_time_text",String.valueOf(((TextView)get(card,"time")).getText())).put("actual_accessibility",String.valueOf(card.getContentDescription()))
      .put("actual_size",new JSONArray(new int[]{card.getWidth(),card.getHeight()})).put("layout_params_size",params==null?JSONObject.NULL:new JSONArray(new int[]{params.width,params.height}))
      .put("card_layout_requested",card.isLayoutRequested()).put("grid_layout_requested",grid.isLayoutRequested()).put("card_attached",card.isAttachedToWindow()).put("card_parent_is_current_grid",card.getParent()==grid)
      .put("first_visible",grid.getFirstVisiblePosition()).put("first_child_top",grid.getChildAt(0).getTop()).put("grid_selected_position",grid.getSelectedItemPosition()).put("card_adapter_position",grid.getPositionForView(card))
      .put("native_adapter_class",grid.getAdapter().getClass().getName()).put("native_adapter_identity",System.identityHashCode(grid.getAdapter())).put("bound_adapter_identity",boundAdapter==null?JSONObject.NULL:System.identityHashCode(boundAdapter)).put("measured_adapter_identity",measuredAdapter==null?JSONObject.NULL:System.identityHashCode(measuredAdapter))
      .put("holder",metrics);
  }

  @Test public void actualAccepted431ReturnBaseline()throws Exception{
    CobraSettingsReturnBaselineTest.Fixture f=fixture(240);GridView before=grid(f);List<Object> refs=adapterItems(before);
    before.setSelection(80);f.layout();assertEquals(80,before.getFirstVisiblePosition());f.observeBrowser();
    JSONObject initial=f.snapshot();shellReturn(f);GridView after=grid(f);
    assertNotSame(before,after);assertTrue(f.addedGrids>0);sameItems(refs,after);
    write("ACCEPTED431-RETURN",new JSONObject().put("status","OBSERVED_ORIGINAL_NATIVE_GRID_RECONSTRUCTION")
      .put("before",initial).put("after",f.snapshot()).put("source","9ccc4c362a65118eeba38a8e7e4b0de5723c69af")
      .put("latency_or_frames","NOT_MEASURED").put("shutdown","NOT_RUN"));
  }

  @Test public void nativeReusePreservesScrollSelectionAndCurrentProgramme()throws Exception{
    CobraSettingsReturnBaselineTest.Fixture f=fixture(240);GridView before=grid(f);assertNotNull(state(f.a));
    before.setSelection(80);f.layout();assertEquals(80,before.getFirstVisiblePosition());before.scrollListBy(17);f.layout();
    int first=before.getFirstVisiblePosition(),top=before.getChildAt(0).getTop();View child=before.getChildAt(0);
    boolean focused=child.requestFocus();View oldFocus=before.findFocus();assertTrue("Actual native focus request must succeed",focused);assertNotNull("Actual focused native view required",oldFocus);Object adapter=before.getAdapter();List<Object> refs=adapterItems(before);
    Object selected=before.getAdapter().getItem(first);set(f.a,"mGuidePreviewChannel",selected);
    List<int[]> cardLayouts=new ArrayList<>(),gridLayouts=new ArrayList<>();
    View.OnLayoutChangeListener cardObserver=(v,l,t,r,b,ol,ot,or,ob)->cardLayouts.add(new int[]{l,t,r,b,ol,ot,or,ob,v.isSelected()?1:0});
    View.OnLayoutChangeListener gridObserver=(v,l,t,r,b,ol,ot,or,ob)->gridLayouts.add(new int[]{l,t,r,b,ol,ot,or,ob});
    child.addOnLayoutChangeListener(cardObserver);before.addOnLayoutChangeListener(gridObserver);
    JSONObject beforeClock=retainedCardDiagnostic(f,child,selected);
    // Advance the actual controlled Android clock without dispatching worker bodies.
    ShadowSystemClock.advanceBy(Duration.ofMinutes(61));
    Object current=call(f.a,"cobraCurrentProgram",selected);assertNotNull(current);assertTrue(String.valueOf(get(current,"title")).startsWith("Next "));
    JSONObject beforeReturn=retainedCardDiagnostic(f,child,selected);
    f.observeBrowser();call(f.a,"cobraShowGuideShell");JSONObject synchronousReturn=retainedCardDiagnostic(f,child,selected);f.layout();
    assertSame(before,grid(f));assertSame(adapter,grid(f).getAdapter());sameItems(refs,grid(f));
    assertEquals(first,before.getFirstVisiblePosition());assertEquals(top,before.getChildAt(0).getTop());
    assertSame(child,before.getChildAt(0));assertSame("Actual native focus identity retained",oldFocus,before.findFocus());
    JSONObject afterReturn=retainedCardDiagnostic(f,child,selected);child.removeOnLayoutChangeListener(cardObserver);before.removeOnLayoutChangeListener(gridObserver);
    write("REUSE-PREASSERT-DIAGNOSTIC",new JSONObject().put("status","OBSERVED_BEFORE_UNCHANGED_STRICT_SELECTION_ASSERTION")
      .put("before_clock_advance",beforeClock).put("after_clock_before_return",beforeReturn).put("synchronous_shell_return",synchronousReturn).put("after_return_layout_before_assert",afterReturn)
      .put("expected_current_programme",get(current,"title")).put("captured_first_visible",first).put("captured_first_top",top).put("original_native_adapter_identity",System.identityHashCode(adapter))
      .put("card_layout_change_events",new JSONArray(cardLayouts)).put("grid_layout_change_events",new JSONArray(gridLayouts))
      .put("layout_observation_limit","Additive OnLayoutChangeListener observes bounds changes or layout-required callbacks; it does not intercept every GridView layoutChildren/setupChild invocation")
      .put("strict_selectedflag_assertion","UNCHANGED").put("production_or_global_state_mutation","NONE_BY_DIAGNOSTIC"));
    assertTrue("Original native bind refreshes selection",child.isSelected());
    assertTrue("Original native bind refreshes current EPG/accessibility",String.valueOf(child.getContentDescription()).contains(String.valueOf(get(current,"title"))));
    assertEquals(0,f.addedGrids);assertEquals(0,f.removedGrids);assertNull(get(f.a,"mPlayer"));assertNull(get(f.a,"mCobraPreviewPlayer"));
    write("RETAINED-RETURN",new JSONObject().put("status","PASS_REAL_NATIVE_GRID_ADAPTER_CHANNEL_SCROLL_FOCUS_AND_EPG_REUSE")
      .put("first_visible",first).put("first_child_top",top).put("focus_requested",focused)
      .put("focused_view_identity_before",System.identityHashCode(oldFocus)).put("focused_view_identity_after",System.identityHashCode(before.findFocus())).put("after",f.snapshot())
      .put("provider_workers_executed",false).put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN"));
  }

  @Test public void nativeImmediateSecondRenderPreservesPendingPosition()throws Exception{
    CobraSettingsReturnBaselineTest.Fixture f=fixture(240);GridView initial=grid(f);initial.setSelection(80);f.layout();assertEquals(80,initial.getFirstVisiblePosition());
    // Real publication also tests equal-content replacement: it must invalidate.
    call(f.a,"applyLoadResult",construct("LoadResult",new ArrayList<Object>(f.channels)));
    f.observeBrowser();call(f.a,"cobraRenderGuideBrowser");GridView pending=grid(f);assertNotSame(initial,pending);
    assertNotNull(state(f.a));int childrenBeforeLayout=pending.getChildCount();
    call(f.a,"cobraRenderGuideBrowser");assertSame(pending,grid(f));f.layout();
    assertEquals(80,pending.getFirstVisiblePosition());assertEquals(1,f.addedGrids);assertEquals(1,f.removedGrids);
    List<Object> refs=new ArrayList<Object>(f.channels);sameItems(refs,pending);
    write("PENDING-RESTORATION",new JSONObject().put("status","PASS_ACTUAL_NEW_GRID_PENDING80_RETAINED_ON_SECOND_NATIVE_RENDER")
      .put("children_before_first_layout",childrenBeforeLayout).put("after",f.snapshot()).put("shutdown","NOT_RUN"));
  }

  @Test public void nativeSelectiveCollectionsAndFreshDirectory()throws Exception{
    CobraSettingsReturnBaselineTest.Fixture f=fixture(24);GridView all=grid(f);f.observeBrowser();
    call(f.a,"addRecent",f.channels.get(2));shellReturn(f);assertSame("Recent-only change keeps ALL grid",all,grid(f));
    call(f.a,"toggleFavorite",f.channels.get(1));shellReturn(f);assertSame("Favorite-only change keeps ALL grid",all,grid(f));
    set(f.a,"mCategory","RECENT");call(f.a,"cobraRenderGuideBrowser");f.layout();GridView recents=grid(f);
    assertEquals(1,recents.getCount());call(f.a,"addRecent",f.channels.get(3));shellReturn(f);
    assertNotSame(recents,grid(f));assertEquals("qa:3",get(grid(f).getAdapter().getItem(0),"id"));assertEquals(2,grid(f).getCount());
    set(f.a,"mCategory","FAVORITES");call(f.a,"cobraRenderGuideBrowser");f.layout();assertEquals(1,grid(f).getCount());GridView favorites=grid(f);
    call(f.a,"toggleFavorite",f.channels.get(4));shellReturn(f);assertNotSame(favorites,grid(f));assertEquals(2,grid(f).getCount());
    // Group/source directory pages use the original complete count renderer.
    set(f.a,"mCobraGuideRoute","categories");call(f.a,"cobraRenderGuideBrowser");f.layout();assertNull(state(f.a));
    LinearLayout browser=(LinearLayout)get(f.a,"mCobraGuideBrowser");ListView directory=null;
    for(int i=0;i<browser.getChildCount();i++)if(browser.getChildAt(i) instanceof ListView)directory=(ListView)browser.getChildAt(i);
    assertNotNull("Original directory built",directory);Object adapter=directory.getAdapter();
    List<?> values=(List<?>)get(adapter,"val$values"),counts=(List<?>)get(adapter,"val$counts");
    assertEquals("2",counts.get(values.indexOf("RECENT")));assertEquals("2",counts.get(values.indexOf("FAVORITES")));
    write("SELECTIVE-COLLECTIONS",new JSONObject().put("status","PASS_ACTUAL_COLLECTION_MUTATORS_CONTEXT_SELECTIVITY_AND_NATIVE_DIRECTORY_COUNTS")
      .put("recent_count",counts.get(values.indexOf("RECENT"))).put("favorite_count",counts.get(values.indexOf("FAVORITES")))
      .put("shutdown","NOT_RUN"));
  }

  @Test public void nativePolicyTypesAndContextInvalidation()throws Exception{
    JSONArray rows=new JSONArray();
    for(String scenario:new String[]{"profiles-type","source-meta-type","profile-policy","hidden","custom-group","source-publication","equal-quiet-publication"}){
      CobraSettingsReturnBaselineTest.Fixture f=fixture(24);GridView before=grid(f);Object features=get(f.a,"mFeatures");
      SharedPreferences policy=(SharedPreferences)get(features,"prefs");
      String originalProfiles=policy.getString("profiles","[]"),originalSourceMeta=policy.getString("source_meta","{}");
      if(scenario.equals("profiles-type"))policy.edit().putInt("profiles",7).commit();
      if(scenario.equals("source-meta-type"))policy.edit().putInt("source_meta",7).commit();
      if(scenario.equals("profile-policy")){
        String id=(String)call(features,"createProfile","Restricted test","",true);assertFalse(id.isEmpty());assertTrue((Boolean)call(features,"unlockAndSelectProfile",id,""));call(f.a,"reloadProfileCollections");
      }
      if(scenario.equals("hidden"))call(f.a,"hideCobraChannel",f.channels.get(2));
      if(scenario.equals("custom-group")){
        EditText input=new EditText(f.a);input.setText("Cache group");call(f.a,"lambda$showCobraAddToGroup$74$com-projectinfinity-kodi-InfinityLiveActivity",input,f.channels.get(2),null,0);
        set(f.a,"mCategory","MY:Cache group");call(f.a,"cobraRenderGuideBrowser");f.layout();before=grid(f);input.setText("");
        call(f.a,"lambda$showCobraAddToGroup$74$com-projectinfinity-kodi-InfinityLiveActivity",input,f.channels.get(2),null,0);
      }
      if(scenario.equals("source-publication"))call(f.a,"persistSources");
      if(scenario.equals("equal-quiet-publication"))call(f.a,"lambda$loadAllEnabledSources$54$com-projectinfinity-kodi-InfinityLiveActivity",new ArrayList<Object>(f.channels),true,new ArrayList<Object>(),new ArrayList<Object>((List<?>)get(f.a,"mSources")));
      shellReturn(f);
      if(scenario.equals("custom-group"))assertNull("Empty native result has no retained grid",get(f.a,"mCobraGuideList"));
      else{
        assertNotSame(scenario+" must use fresh native projection",before,grid(f));
        if(scenario.equals("hidden"))assertEquals(23,grid(f).getCount());
        if(scenario.equals("profile-policy"))assertEquals(23,grid(f).getCount());
        if(scenario.endsWith("-type"))assertEquals("Original policy fallback stays usable",24,grid(f).getCount());
      }
      rows.put(new JSONObject().put("scenario",scenario).put("status","PASS_ORIGINAL_NATIVE_PROJECTION_AND_ERROR_SEMANTICS"));
      if(scenario.equals("profiles-type"))policy.edit().putString("profiles",originalProfiles).commit();
      if(scenario.equals("source-meta-type"))policy.edit().putString("source_meta",originalSourceMeta).commit();
    }
    write("CONTEXT-INVALIDATION",new JSONObject().put("status","PASS_NATIVE_POLICY_TYPE_PROFILE_HIDDEN_CUSTOM_SOURCE_PUBLICATION_CASES").put("cases",rows).put("shutdown","NOT_RUN"));
  }

  @Test public void revisionHooksAllowBackgroundAndModeExitDisposes()throws Exception{
    CobraSettingsReturnBaselineTest.Fixture f=fixture(24);assertNotNull(state(f.a));final AtomicReference<Throwable> error=new AtomicReference<>();
    Thread thread=new Thread(()->{try{
      for(String event:new String[]{"inventory","sources","favorites","collections","hidden","custom"})helper(event,f.a);
      Class<?> c=Class.forName("com.projectinfinity.kodi.CobraCardsReuse");c.getMethod("recent",Activity.class,Object.class).invoke(null,f.a,f.channels.get(0));
    }catch(Throwable t){error.set(t);}},"selected-revision-hook-QA");thread.start();thread.join(3000);assertFalse(thread.isAlive());assertNull(error.get());
    assertFalse("Dirty inventory rejects fast path",tryReuse(f.a));shellReturn(f);
    set(f.a,"mCobraGuideStyle","mobile");call(f.a,"cobraShowGuideShell");f.layout();assertNull(state(f.a));assertFalse(tryReuse(f.a));
    assertTrue(get(f.a,"mCobraGuideList") instanceof ListView);
    write("THREAD-AND-EXIT",new JSONObject().put("status","PASS_REVISION_ONLY_BACKGROUND_HOOKS_AND_NATIVE_MODE_EXIT")
      .put("runtime_worker_added",false).put("shutdown","NOT_RUN"));
  }
}
