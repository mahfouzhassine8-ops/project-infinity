package com.projectinfinity.kodi;
import android.app.*;
import android.content.*;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraVisualLayoutTest {
  final CobraVisualRuntimeTest helper=new CobraVisualRuntimeTest();
  @Before public void before()throws Exception{helper.setup();}
  @After public void after(){helper.cleanup();}
  JSONObject node(String slot,int x,int y,int w,int h)throws Exception{return new JSONObject().put("id",slot).put("type","slot").put("slot",slot).put("rect",new JSONArray(Arrays.asList(x,y,w,h)));}
  JSONObject scene()throws Exception{return new JSONObject().put("width",412).put("height",915).put("nodes",new JSONArray()
      .put(node("enter.infinity",20,250,372,64)).put(node("settings.infinity",20,320,372,52))
      .put(node("enter.cobra",20,500,372,64)).put(node("settings.cobra",20,570,372,52)));}
  JSONObject themedScene(JSONObject scene)throws Exception{JSONObject root=helper.root("scene");root.getJSONObject("base").put("scenes",new JSONObject().put("chooser",scene));return root;}
  JSONObject guide()throws Exception{JSONObject r=new JSONObject();r.put("toolbar",new JSONArray(Arrays.asList(0,0,1,.06)));r.put("video",new JSONArray(Arrays.asList(0,.07,1,.22)));r.put("details",new JSONArray(Arrays.asList(0,.30,1,.12)));r.put("browser",new JSONArray(Arrays.asList(0,.43,1,.57)));for(String n:new String[]{"rail","directory","footer"})r.put(n,new JSONArray(Arrays.asList(0,0,0,0)));return new JSONObject().put("regions",r);}
  @Test public void scenesRejectMissingAndUnknownActionsBeforeActivation()throws Exception{
    JSONObject missing=scene();missing.getJSONArray("nodes").remove(0);helper.rejects(()->helper.install(themedScene(missing)));
    JSONObject unknown=scene();unknown.getJSONArray("nodes").getJSONObject(0).put("slot","launch.arbitrary");helper.rejects(()->helper.install(themedScene(unknown)));
    assertEquals("builtin",CobraVisualTheme.load(helper.context).id);
  }
  @Test public void scenesRejectOverlappingActionsAndExecutableNodes()throws Exception{
    JSONObject overlap=scene();overlap.getJSONArray("nodes").getJSONObject(1).put("rect",new JSONArray(Arrays.asList(20,250,372,64)));helper.rejects(()->helper.install(themedScene(overlap)));
    JSONObject script=scene();script.getJSONArray("nodes").put(new JSONObject().put("id","script").put("type","script").put("rect",new JSONArray(Arrays.asList(0,0,1,1))).put("label","run"));helper.rejects(()->helper.install(themedScene(script)));
  }
  @Test public void nativeChooserLaunchAndSettingsSlotsRemainRealControls()throws Exception{
    helper.activate(helper.install(themedScene(scene())));ExperienceChooserUiTest old=new ExperienceChooserUiTest();ExperienceChooserUiTest.reflect();Splash a=old.activity();
    try{old.show(a,false,412,915);assertNotNull(a.getWindow().getDecorView().findViewWithTag("visual-scene:chooser"));View launch=old.tag(a,"experience-card-cobra"),settings=old.tag(a,"experience-settings-cobra");assertTrue(launch.isFocusable());assertTrue(launch.getHeight()>=44);assertTrue(settings.isClickable());assertTrue(settings.performClick());assertNotNull(org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog());org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog().dismiss();assertTrue(launch.performClick());Intent intent=Shadows.shadowOf(a).getNextStartedActivity();assertNotNull(intent);assertEquals("com.projectinfinity.kodi.InfinityLiveActivity",intent.getComponent().getClassName());old.shot(a,"visual-native-chooser-scene");}finally{old.closeWindows();}
  }
  @Test public void tooSmallSceneFallsBackBeforeNativeControlsAreReparented()throws Exception{
    JSONObject narrow=scene();narrow.put("width",1536);helper.activate(helper.install(themedScene(narrow)));ExperienceChooserUiTest old=new ExperienceChooserUiTest();ExperienceChooserUiTest.reflect();Splash a=old.activity();
    try{old.show(a,false,412,915);assertNull(a.getWindow().getDecorView().findViewWithTag("visual-scene:chooser"));assertNotNull(old.tag(a,"experience-card-infinity"));assertNotNull(old.tag(a,"experience-settings-cobra"));}finally{old.closeWindows();}
  }
  @Test public void guideRegionOverrideIsAtomicAndRejectsUnsafeGeometry()throws Exception{
    int[][] boxes=new int[7][4];assertTrue(CobraVisualGeometry.guide(guide(),boxes,412,915,1));int[][] before=new int[7][];for(int i=0;i<7;i++)before[i]=boxes[i].clone();JSONObject bad=guide();bad.getJSONObject("regions").put("browser",new JSONArray(Arrays.asList(0,.07,1,.60)));assertFalse(CobraVisualGeometry.guide(bad,boxes,412,915,1));for(int i=0;i<7;i++)assertArrayEquals(before[i],boxes[i]);assertFalse(CobraVisualGeometry.guide(guide(),boxes,100,100,2));for(int i=0;i<7;i++)assertArrayEquals(before[i],boxes[i]);
  }
  @Test public void actualFiveViewGeometryCanChangeWithoutNewVideoView()throws Exception{
    JSONObject root=helper.root("geometry");root.getJSONObject("base").put("guide_layouts",new JSONObject().put("grid",guide()));helper.activate(helper.install(root));CobraNavigationUiTest old=new CobraNavigationUiTest();old.clock();InfinityLiveActivity a=old.fixture(24);
    try{CobraNavigationUiTest.call(a,"cobraOpenLiveTv");old.measure(a,412,915);Object texture=CobraNavigationUiTest.get(a,"mCobraPreviewTexture"),shell=CobraNavigationUiTest.get(a,"mCobraGuideShell");CobraNavigationUiTest.call(a,"cobraLayoutGuide");old.measure(a,412,915);assertSame(texture,CobraNavigationUiTest.get(a,"mCobraPreviewTexture"));assertSame(shell,CobraNavigationUiTest.get(a,"mCobraGuideShell"));Object policy=CobraNavigationUiTest.get(a,"mCobraModeLayout");int[] video=(int[])CobraNavigationUiTest.get(policy,"video");assertEquals(Math.round((Integer)CobraNavigationUiTest.get(policy,"height")*.22f),video[3]);old.guide(a);}finally{old.clean(a);}
  }
  @Test public void extendedStylesPreserveParametersWeightAndRestore()throws Exception{
    JSONObject root=helper.root("styles");root.getJSONObject("base").put("styles",new JSONObject().put("drawer.item.tv",new JSONObject().put("width_dp",180).put("height_dp",60).put("margin_top_dp",9).put("padding_left_dp",17).put("weight",2).put("alpha",.8).put("gravity","left")));
    helper.activate(helper.install(root));LinearLayout parent=new LinearLayout(helper.context);Button button=new Button(helper.context);LinearLayout.LayoutParams original=new LinearLayout.LayoutParams(120,50,1);original.leftMargin=7;parent.addView(button,original);int[] clicks={0};button.setOnClickListener(v->clicks[0]++);CobraVisualRenderer renderer=new CobraVisualRenderer(helper.context);renderer.paint(button,"drawer.item.tv");LinearLayout.LayoutParams changed=(LinearLayout.LayoutParams)button.getLayoutParams();assertNotSame(original,changed);assertEquals(120,original.width);assertEquals(180,changed.width);assertEquals(9,changed.topMargin);assertEquals(7,changed.leftMargin);assertEquals(2,changed.weight,0);assertTrue(button.performClick());assertEquals(1,clicks[0]);helper.activate(CobraVisualTheme.builtin());LinearLayout.LayoutParams restored=(LinearLayout.LayoutParams)button.getLayoutParams();assertEquals(120,restored.width);assertEquals(50,restored.height);assertEquals(1,restored.weight,0);assertSame(parent,button.getParent());
  }
  @Test public void extendedStylesRejectUnsupportedValues()throws Exception{
    for(JSONObject bad:Arrays.asList(new JSONObject().put("orientation","delete"),new JSONObject().put("height_dp",-1.5),new JSONObject().put("alpha",2),new JSONObject().put("margin_top_dp",9000),new JSONObject().put("onClick","evil"))){JSONObject root=helper.root("bad-style");root.getJSONObject("base").put("styles",new JSONObject().put("drawer.panel",bad));helper.rejects(()->helper.install(root));}
  }
  @Test public void chooserRetainsTheRunElevenTextPaddingRepair()throws Exception{
    ExperienceChooserUiTest old=new ExperienceChooserUiTest();Splash a=old.activity();try{java.lang.reflect.Method text=Splash.class.getDeclaredMethod("chooserStyledText",String.class,int.class,float.class,boolean.class,int.class);text.setAccessible(true);TextView view=(TextView)text.invoke(a,"INFINITY",Color.WHITE,23f,true,Gravity.CENTER);assertEquals(0,view.getPaddingLeft());assertEquals(0,view.getPaddingRight());assertEquals(0,view.getPaddingTop());assertEquals(0,view.getPaddingBottom());}finally{old.closeWindows();}
  }
  @Test public void paletteAndLayoutSceneVariantsResolveIndependently()throws Exception{
    JSONObject data=themedScene(scene()),cover=scene();cover.put("height",1600);data.put("variants",new JSONObject().put("cover",new JSONObject().put("scenes",new JSONObject().put("chooser",cover))).put("oled",new JSONObject().put("colors",new JSONObject().put("palette.text","#FFFFFF"))));CobraVisualTheme theme=helper.install(data);assertEquals(1600,((JSONObject)theme.value("scenes","chooser","oled","cover")).getInt("height"));assertEquals(915,((JSONObject)theme.value("scenes","chooser","light","landscape")).getInt("height"));
  }
}
