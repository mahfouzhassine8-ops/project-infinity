package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Compact-card layout with controlled capacity. Existing 207 tests retain
 * ownership/silence checks; these screenshots are fixtures, not live phone video. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208QuickPeekLayoutTest {
  Cobra2103205SessionUiTest f;View anchor;Cobra2103205SessionUiTest.CounterPlayer main;
  @Before public void before()throws Exception{
    f=new Cobra2103205SessionUiTest();f.before();main=f.main();
    FrameLayout overlay=(FrameLayout)CobraNavigationUiTest.get(f.a,"mPlayerOverlay");
    anchor=new View(f.a);FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(160,48);pos.leftMargin=28;pos.topMargin=570;overlay.addView(anchor,pos);f.layout();
    CobraNavigationUiTest.put(f.a,"mRecordingSession","controlled-capacity-guard");main.commands.clear();
  }
  @After public void after()throws Exception{if(f!=null){CobraNavigationUiTest.put(f.a,"mRecordingSession","");f.after();}}
  void open()throws Exception{f.call("cobraShowQuickPeek",f.second,anchor);f.layout();}
  @Test public void cardUsesInvokedAnchorAndOneCompactActionRow()throws Exception{
    open();assertSame(anchor,CobraNavigationUiTest.get(f.a,"mCobraSheetAnchor"));
    ViewGroup actions=(ViewGroup)f.tag("cobra_quick_peek_actions");assertEquals(3,actions.getChildCount());
    for(String tag:new String[]{"cobra-quick-peek-play","cobra-quick-peek-favorite","cobra-quick-peek-actions"})
      assertSame(actions,f.tag(tag).getParent());
    assertEquals(208,f.call("cobraSheetWidth","quick-peek"));assertTrue(main.commands.isEmpty());
  }
  @Test public void cardDoesNotDimPlayerAndFitsSafeWindow()throws Exception{
    open();FrameLayout scrim=(FrameLayout)CobraNavigationUiTest.get(f.a,"mCobraActionSheet");
    assertEquals(Color.TRANSPARENT,((ColorDrawable)scrim.getBackground()).getColor());
    View panel=f.tag("cobra_sheet_panel");assertTrue(panel.getWidth()<=208);assertTrue(panel.getLeft()>=0);assertTrue(panel.getTop()>=0);
    assertTrue(panel.getRight()<=scrim.getWidth());assertTrue(panel.getBottom()<=scrim.getHeight());assertTrue(main.commands.isEmpty());
  }
  @Test public void portraitPreviewMockHasNoOversizedRowsOrCodecCopy()throws Exception{
    open();f.tag("cobra_quick_peek_video").setVisibility(View.VISIBLE);((TextView)f.tag("cobra_quick_peek_state")).setText("Live preview · muted");f.layout();
    View panel=f.tag("cobra_sheet_panel");assertEquals(104,f.tag("cobra_quick_peek_video").getLayoutParams().height);
    assertTrue(panel.getHeight()>panel.getWidth());assertTrue(panel.getHeight()<500);
    Cobra2103201MenuPolishTest.capture(f.a,f.ui,"cobra208-quick-peek-portrait-layout-fixture",412,915);
  }
  @Test public void favoriteAndExistingChannelActionsRemainAccessible()throws Exception{
    open();View favorite=f.tag("cobra-quick-peek-favorite");boolean before=favorite.isSelected();favorite.performClick();
    assertEquals(!before,favorite.isSelected());assertTrue(main.commands.isEmpty());
    f.tag("cobra-quick-peek-actions").performClick();assertEquals("channel",CobraNavigationUiTest.get(f.a,"mCobraSheetKind"));
    assertNotNull(f.tag("cobra-channel-preferences"));assertNull(CobraNavigationUiTest.get(f.a,"mCobraQuickPeekChannel"));
  }
  @Test public void edgePlacementKeepsCompactCardNearInvokingRow(){
    int[] safe={8,8,312,700},pane={0,0,320,720};
    for(int[] row:new int[][]{{8,8,150,56},{160,650,310,698},{10,330,160,378}}){
      int[] p=InfinityLiveActivity.CobraSheetGeometry.place(safe,pane,row,208,290,6);
      assertEquals(208,p[2]);assertTrue(p[0]>=8&&p[0]+p[2]<=312);assertTrue(p[1]>=8&&p[1]+p[3]<=700);
      assertTrue(p[1]>=row[3]||p[1]+p[3]<=row[1]);
    }
  }
  @Test public void visualMenuWidthIsSeparateFromPeekAndLegacySheets()throws Exception{
    assertEquals(288,f.call("cobraSheetWidth","visual-settings"));assertEquals(208,f.call("cobraSheetWidth","quick-peek"));
    assertEquals(440,f.call("cobraSheetWidth","tracks"));
  }
}
