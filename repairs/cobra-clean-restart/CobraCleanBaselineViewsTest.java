package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.File;
import java.io.FileOutputStream;
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

/** Attached production hierarchy from the unmodified source. Not a device/decoder test. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraCleanBaselineViewsTest {
  private void collect(View v, JSONArray rows) throws Exception {
    if(v.getVisibility()!=View.VISIBLE)return;
    Rect r=new Rect();boolean visible=v.getGlobalVisibleRect(r);
    JSONObject row=new JSONObject().put("class",v.getClass().getName())
        .put("tag",String.valueOf(v.getTag())).put("description",String.valueOf(v.getContentDescription()))
        .put("clickable",v.isClickable()).put("enabled",v.isEnabled()).put("shown",v.isShown())
        .put("attached",v.isAttachedToWindow()).put("visibleRect",visible)
        .put("rect",new JSONArray(new int[]{r.left,r.top,r.right,r.bottom}));
    if(v instanceof android.widget.TextView)row.put("text",((android.widget.TextView)v).getText().toString());
    rows.put(row);
    if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)collect(((ViewGroup)v).getChildAt(i),rows);
  }
  @Test public void approvedViewsHaveRecordedWindowBoundsAndOriginalTouchRegions() throws Exception {
    File dir=new File(System.getProperty("cobra.clean.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
    for(int[] size:new int[][]{{412,915},{915,412},{720,840},{840,720},{280,280}}){
      String q="w"+size[0]+"dp-h"+size[1]+"dp-"+(size[0]>size[1]?"land":"port")+"-mdpi";
      RuntimeEnvironment.setQualifiers(q);
      CobraNavigationUiTest f=new CobraNavigationUiTest();f.clock();InfinityLiveActivity a=f.fixture(8);
      try {
        Shadows.shadowOf(a.getWindowManager().getDefaultDisplay()).setWidth(size[0]);
        Shadows.shadowOf(a.getWindowManager().getDefaultDisplay()).setHeight(size[1]);
        WindowManager.LayoutParams lp=a.getWindow().getAttributes();lp.width=size[0];lp.height=size[1];a.getWindow().setAttributes(lp);
        SharedPreferences prefs=(SharedPreferences)get(a,"mPrefs");prefs.edit().putString("guide_view_mode","focus").commit();
        put(a,"mCobraGuideStyle","focus");put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());
        call(a,"cobraShowGuideShell");f.measure(a,size[0],size[1]);
        Object ch=((List)get(a,"mChannels")).get(0);
        CobraProHandoffTest.Stub state=new CobraProHandoffTest.Stub();state.volume=0;
        ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},state);
        put(a,"mGuidePreviewChannel",ch);put(a,"mCobraPreviewPlayer",player);put(a,"mCobraPreviewSessionKey",call(a,"cobraChannelKey",ch));
        put(a,"mCobraPreviewMuted",true);put(a,"mCobraProPlaybackOwned",false);
        call(a,"cobraRefreshProHero");call(a,"cobraSetProState",CobraProUi.PREVIEW,false);
        f.measure(a,size[0],size[1]);
        View decor=a.getWindow().getDecorView();assertEquals(size[0],decor.getWidth());assertEquals(size[1],decor.getHeight());
        CobraProUi.Hero hero=(CobraProUi.Hero)get(a,"mCobraProHeroUi");assertNotNull(hero);assertTrue(hero.isAttachedToWindow());
        assertEquals(View.VISIBLE,hero.unmute.getVisibility());
        JSONArray nodes=new JSONArray();collect(decor,nodes);
        String name="approved-preview-"+size[0]+"x"+size[1];
        JSONObject result=new JSONObject().put("windowWidth",decor.getWidth()).put("windowHeight",decor.getHeight())
            .put("heroWidth",hero.getWidth()).put("heroHeight",hero.getHeight()).put("nodes",nodes);
        Files.write(new File(dir,name+".json").toPath(),result.toString(2).getBytes(StandardCharsets.UTF_8));
        Bitmap bitmap=Bitmap.createBitmap(decor.getWidth(),decor.getHeight(),Bitmap.Config.ARGB_8888);decor.draw(new Canvas(bitmap));
        try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}finally{bitmap.recycle();}
      } finally {f.clean(a);}
    }
  }
}
