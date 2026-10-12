package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ListView;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.File;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Original source only: no candidate controller, no changed Groups runtime. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraGroupsBaselineTest {
  CobraNavigationUiTest fixture;
  void settle(InfinityLiveActivity activity,boolean framework) throws Exception {
    if(framework)fixture.frames(12);else fixture.measure(activity,412,915);
    assertEquals(412,activity.getWindow().getDecorView().getWidth());
    assertEquals(915,activity.getWindow().getDecorView().getHeight());
  }
  View button(View view) {
    if(view instanceof Button)return view;
    if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){
      View result=button(((ViewGroup)view).getChildAt(i));if(result!=null)return result;
    }
    return null;
  }
  void click(InfinityLiveActivity activity,View target,boolean framework) throws Exception {
    assertNotNull(target);assertTrue(target.isAttachedToWindow());assertTrue(target.isShown());assertTrue(target.performClick());settle(activity,framework);
  }
  @Test public void groupsRendersWithFrameworkTraversalWithoutRuntimeModification() throws Exception {
    JSONArray cases=new JSONArray();
    for(boolean framework:new boolean[]{false,true}) {
      RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");fixture=new CobraNavigationUiTest();fixture.clock();
      InfinityLiveActivity activity=fixture.fixture(8);
      try {
        Shadows.shadowOf(activity.getWindowManager().getDefaultDisplay()).setWidth(412);
        Shadows.shadowOf(activity.getWindowManager().getDefaultDisplay()).setHeight(915);
        WindowManager.LayoutParams params=activity.getWindow().getAttributes();params.width=412;params.height=915;activity.getWindow().setAttributes(params);
        ((SharedPreferences)get(activity,"mPrefs")).edit().putString("guide_view_mode","mobile").commit();
        put(activity,"mCobraGuideStyle","mobile");call(activity,"cobraShowGuideShell");settle(activity,framework);
        Object channel=((List)get(activity,"mChannels")).get(0);
        CobraProHandoffTest.Stub playback=new CobraProHandoffTest.Stub();
        ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},playback);
        put(activity,"mGuidePreviewChannel",channel);put(activity,"mCobraPreviewPlayer",player);
        put(activity,"mCobraPreviewSessionKey",call(activity,"cobraChannelKey",channel));put(activity,"mCobraPreviewMuted",false);
        call(activity,"promoteCobraPreviewToFullscreen",channel);settle(activity,framework);
        click(activity,fixture.description((View)get(activity,"mPlayerChrome"),"Channels"),framework);
        click(activity,activity.getWindow().getDecorView().findViewWithTag("cobra_player_tab_CATEGORIES"),framework);
        ListView list=(ListView)get(activity,"mCobraPlayerDrawerList");int group=-1;
        for(int i=0;i<list.getCount();i++)if("Documentaries".equals(list.getItemAtPosition(i)))group=i;
        assertTrue(group>=0);list.setSelectionFromTop(group,0);settle(activity,framework);
        click(activity,button(list.getChildAt(group-list.getFirstVisiblePosition())),framework);
        assertEquals("GROUP:Documentaries",get(activity,"mCobraDrawerFilter"));
        list.setSelectionFromTop(1,0);list.requestLayout();settle(activity,framework);fixture.frames(12);settle(activity,framework);
        JSONObject result=new JSONObject().put("traversal",framework?"framework":"historical_manual")
            .put("count",list.getCount()).put("children",list.getChildCount())
            .put("first",list.getFirstVisiblePosition()).put("last",list.getLastVisiblePosition())
            .put("width",list.getWidth()).put("height",list.getHeight()).put("layoutRequested",list.isLayoutRequested());
        cases.put(result);
        File dir=new File(System.getProperty("cobra.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
        Files.write(new File(dir,"GROUPS-BASELINE-COMPARISON.json").toPath(),new JSONObject().put("cases",cases).toString(2).getBytes(StandardCharsets.UTF_8));
        if(framework){assertEquals(4,list.getCount());assertTrue("Actual baseline group rows must render",list.getChildCount()>0);assertTrue(list.getFirstVisiblePosition()<=1&&list.getLastVisiblePosition()>=1);View row=button(list.getChildAt(1-list.getFirstVisiblePosition()));assertNotNull(row);assertTrue(row.isShown());assertTrue(row.isClickable());}
      } finally {call(activity,"closePlayer");fixture.clean(activity);}
    }
  }
}
