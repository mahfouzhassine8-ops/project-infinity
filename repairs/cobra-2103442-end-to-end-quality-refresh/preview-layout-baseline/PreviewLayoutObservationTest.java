package com.projectinfinity.kodi;

import android.view.View;
import android.widget.FrameLayout;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

/** Follow-up to real accepted442 layout warnings; no shutdown or new player. */
public class PreviewLayoutObservationTest extends ProApprovedLayoutTest {
 static String placement(FrameLayout.LayoutParams p){return p.width+","+p.height+","+p.gravity+","+p.leftMargin+","+p.topMargin+","+p.rightMargin+","+p.bottomMargin;}
 @Test public void unchangedPreviewPlacementRequestsLayout()throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("grid",1080,2520,320,"dark");
  FrameLayout root=(FrameLayout)get(f.a,"mCobraPreviewHost");
  View controls=root.findViewWithTag("cobra_preview_controls"),pip=root.findViewWithTag("cobra_preview_pip_small");
  assertNotNull(pip);controls.setVisibility(View.GONE);Object six=get(f.a,"mCobraSix");
  call(six,"smallPreviewPip");frames();assertEquals(View.VISIBLE,pip.getVisibility());
  String original=placement((FrameLayout.LayoutParams)pip.getLayoutParams());int requested=0;
  for(int i=0;i<32;i++){
   pip.measure(View.MeasureSpec.makeMeasureSpec(pip.getWidth(),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(pip.getHeight(),View.MeasureSpec.EXACTLY));
   pip.layout(pip.getLeft(),pip.getTop(),pip.getRight(),pip.getBottom());
   assertFalse("Clear actual view layout request before observation",pip.isLayoutRequested());
   call(six,"smallPreviewPip");if(pip.isLayoutRequested())requested++;
   assertEquals(original,placement((FrameLayout.LayoutParams)pip.getLayoutParams()));
   assertSame(pip,root.findViewWithTag("cobra_preview_pip_small"));
  }
  save("PREVIEW-SAME-BOUNDS-LAYOUT",new JSONObject().put("calls",32).put("layout_requests",requested).put("unchanged_placement",original).put("owner","CobraSix.smallPreviewPip; exact accepted442 method in signed443"));
 }
}
