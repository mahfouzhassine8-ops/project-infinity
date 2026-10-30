package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.widget.*;
import java.lang.reflect.Method;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import org.robolectric.*;
import org.robolectric.annotation.*;

/** Observational protected432 binary control. No current-row height expectation,
 * app focusability change, global field reset or new production behavior. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCardsVisualCloseoutTest.Terminals.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraCardsSigned432SelectionControlTest {
  static Object get(Object owner,String name)throws Exception{return CobraCardsVisualCloseoutTest.get(owner,name);}
  static Object call(Object owner,String name,Object...args)throws Exception{return CobraCardsVisualCloseoutTest.call(owner,name,args);}
  static void set(Object owner,String name,Object value)throws Exception{CobraCardsVisualCloseoutTest.set(owner,name,value);}
  static String id(Object channel)throws Exception{return channel==null?"null":String.valueOf(get(channel,"id"));}
  @Before public void sameNativeWarmPhase()throws Exception{new CobraCardsLayoutTest().frames();CobraCardsVisualCloseoutTest.previews.clear();CobraCardsVisualCloseoutTest.peeks.clear();CobraCardsVisualCloseoutTest.write("protected432-native-phase",CobraCardsLayoutTest.nativeWarmThemeSetup());}
  @Test public void nativeSigned432SingleBindSelectionControl()throws Exception{
    CobraCardsVisualCloseoutTest.Rows r=new CobraCardsVisualCloseoutTest.Rows();
    // Replay v5 setup and recycling operations; all new-height expectations are
    // intentionally absent from this observation of the protected old binary.
    r.programme(3,CobraCardsVisualCloseoutTest.LIVE_TITLE);View recycled=r.original.getView(2,null,r.grid);r.original.getView(3,null,r.grid);r.original.getView(0,recycled,r.grid);r.original.getView(1,recycled,r.grid);r.programme(0,"News");r.programme(1,"News");r.publish();
    r.grid.setSelection(8);r.f.layout();r.grid.scrollListBy(17);r.f.layout();int first=r.grid.getFirstVisiblePosition(),top=r.grid.getChildAt(0).getTop();View retained=r.grid.getChildAt(0);boolean initialFocus=retained.requestFocusFromTouch();View focus=r.grid.findFocus();Object selected=r.original.getItem(first);set(r.f.a,"mGuidePreviewChannel",selected);
    CobraCardsVisualCloseoutTest.CountedAdapter counted=new CobraCardsVisualCloseoutTest.CountedAdapter(r.original);r.grid.setAdapter(counted);r.grid.setSelection(first);r.f.layout();r.grid.scrollListBy(r.grid.getChildAt(0).getTop()-top);r.f.layout();retained=r.grid.getChildAt(0);boolean replacementFocus=retained.requestFocusFromTouch();focus=r.grid.findFocus();first=r.grid.getFirstVisiblePosition();top=retained.getTop();counted.getView(first,retained,r.grid);
    r.programme(first,CobraCardsVisualCloseoutTest.LIVE_TITLE);int oldHeight=retained.getHeight();call(retained,"bind",selected,first);r.f.frames();
    Class<?> tiles=Class.forName("com.projectinfinity.kodi.CobraCardsTiles");Method holderMethod=tiles.getDeclaredMethod("holder",LinearLayout.class);holderMethod.setAccessible(true);Object holder=holderMethod.invoke(null,retained),bound=get(holder,"bound"),preview=get(r.f.a,"mGuidePreviewChannel");Drawable surface=retained.getBackground();int[] state=retained.getDrawableState();
    r.f.image("protected432-single-bind-selection-control");
    JSONObject report=new JSONObject().put("runtime","PROTECTED432_ACTUAL_OWNER_DEX_HOST_CONTROL").put("height_expectations","NONE").put("captured_first",first).put("actual_first",r.grid.getFirstVisiblePosition()).put("captured_top",top).put("actual_top",r.grid.getChildAt(0).getTop()).put("tag",retained.getTag()).put("bound_channel_id",id(bound)).put("selected_variable_id",id(selected)).put("preview_channel_id",id(preview)).put("native_selected_variable",call(r.f.a,"cobraModeSelected",selected)).put("native_selected_bound",call(r.f.a,"cobraModeSelected",bound)).put("view_selected",retained.isSelected()).put("view_focused",retained.isFocused()).put("view_has_focus",retained.hasFocus()).put("focus_identity_preserved",focus==r.grid.findFocus()).put("focus_class",r.grid.findFocus()==null?"null":r.grid.findFocus().getClass().getName()).put("focus_tag",r.grid.findFocus()==null?"null":String.valueOf(r.grid.findFocus().getTag())).put("initial_focus_request",initialFocus).put("replacement_focus_request",replacementFocus).put("drawable_state",new JSONArray(state)).put("surface_class",surface.getClass().getName()).put("surface_selected",get(surface,"selected")).put("surface_focused",get(surface,"focus")).put("surface_pressed",get(surface,"pressed")).put("old_height",oldHeight).put("new_height",retained.getHeight()).put("actual_text",((TextView)get(retained,"now")).getText()).put("no_app_or_global_flags_changed",true).put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN");
    CobraCardsVisualCloseoutTest.write("PROTECTED432-SINGLE-BIND-SELECTION",report);
  }
}
