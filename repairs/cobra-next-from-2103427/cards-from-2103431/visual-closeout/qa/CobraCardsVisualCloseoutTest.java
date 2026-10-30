package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.text.Layout;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.shadows.ShadowActivity;

/** Four selected closeout cases. Native builders, adapter/card, EPG and source
 * methods execute. Only preview/QuickPeek terminals are recorded; projection
 * instrumentation delegates to the exact original method. No decoder/workers. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCardsVisualCloseoutTest.Terminals.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraCardsVisualCloseoutTest {
  static int guideProjections,currentProjections;
  static final List<Object> previews=new ArrayList<>(),peeks=new ArrayList<>();
  static final String LIVE_TITLE="Evening reports and regional analysis";
  static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
  static void set(Object o,String n,Object v)throws Exception{CobraCardsLayoutTest.set(o,n,v);}
  static Object call(Object o,String n,Object...a)throws Exception{return CobraCardsLayoutTest.call(o,n,a);}
  static Object create(String n,Object...a)throws Exception{return CobraCardsLayoutTest.construct(n,a);}
  static Path output(){return Paths.get(System.getProperty("cards.closeout.output"));}
  static void write(String name,JSONObject report)throws Exception{Files.createDirectories(output());Files.write(output().resolve(name+".json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}
  static Rect rect(View v){int[] p=new int[2];v.getLocationOnScreen(p);return new Rect(p[0],p[1],p[0]+v.getWidth(),p[1]+v.getHeight());}
  static JSONArray rectJson(View v){Rect b=rect(v);return new JSONArray(new int[]{b.left,b.top,b.right,b.bottom});}
  static List<View> descendants(View root){List<View> result=new ArrayList<>();result.add(root);if(root instanceof ViewGroup){ViewGroup g=(ViewGroup)root;for(int i=0;i<g.getChildCount();i++)result.addAll(descendants(g.getChildAt(i)));}return result;}
  static View more(View card){View result=null;for(View v:descendants(card))if(v.getClass().getName().endsWith("CobraCardsTiles$MoreView")){assertNull(result);result=v;}assertNotNull("actual Cards More target",result);return result;}
  static TextView brand(CobraCardsLayoutTest.Fixture f)throws Exception{for(View v:descendants((View)get(f.a,"mCobraModeToolbar")))if(v instanceof TextView&&((TextView)v).getText().toString().equals("Cobra"))return (TextView)v;throw new AssertionError("Native header brand missing");}
  static void header(CobraCardsLayoutTest.Fixture f)throws Exception{TextView title=brand(f);int expected=Integer.getInteger("cards.closeout.header.weight",-1);assertTrue("Root's reference-calibrated header weight must be recorded",expected>0);assertEquals("Only reference-calibrated Cards brand face",expected,title.getTypeface().getWeight());}
  @Before public void controlledNativeSetup()throws Exception{
    assertTrue("Explicit authorized closeout candidate phase",Boolean.getBoolean("cards.closeout.candidate"));
    new CobraCardsLayoutTest().frames();previews.clear();peeks.clear();guideProjections=0;currentProjections=0;
    write("native-phase-setup",CobraCardsLayoutTest.nativeWarmThemeSetup());
  }
  @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
  public static class Terminals extends ShadowActivity {
    @RealObject InfinityLiveActivity owner;
    @Implementation protected void selectGuidePreview(Object channel){previews.add(channel);}
    @Implementation protected void cobraShowQuickPeek(Object channel,Object anchor){peeks.add(channel);}
    @Implementation protected ArrayList<?> cobraGuideChannels(){guideProjections++;return Shadow.directlyOn(owner,InfinityLiveActivity.class,"cobraGuideChannels");}
    @Implementation protected ArrayList<?> cobraChannelsForCurrentView(){currentProjections++;return Shadow.directlyOn(owner,InfinityLiveActivity.class,"cobraChannelsForCurrentView");}
  }
  /** Observes the real adapter's local lookup work; every operation delegates. */
  static final class CountedAdapter extends BaseAdapter {
    final android.widget.ListAdapter original;int items,views;final List<Integer> positions=new ArrayList<>();
    CountedAdapter(android.widget.ListAdapter value){original=value;}
    public int getCount(){return original.getCount();}public Object getItem(int p){items++;positions.add(p);return original.getItem(p);}public long getItemId(int p){return original.getItemId(p);}
    public boolean hasStableIds(){return original.hasStableIds();}public int getItemViewType(int p){return original.getItemViewType(p);}public int getViewTypeCount(){return original.getViewTypeCount();}
    public boolean areAllItemsEnabled(){return original.areAllItemsEnabled();}public boolean isEnabled(int p){return original.isEnabled(p);}
    public View getView(int p,View old,ViewGroup parent){views++;return original.getView(p,old,parent);}
  }
  static final class Rows {
    final CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards");
    final GridView grid=(GridView)get(f.a,"mCobraGuideList");final android.widget.ListAdapter original=grid.getAdapter();
    final List<Object> items=(List<Object>)get(original,"channels");final Map<String,ArrayList<Object>> programs;
    Rows()throws Exception{
      programs=(Map<String,ArrayList<Object>>)get(((Map)get(f.a,"mCobraEpg")).get("qa"),"programs");
      for(int i=0;i<4;i++){
        Object channel=create("Channel","qa:"+i,i%2==0?"World Documentary HD":"Regional News HD","World | News","epg"+i,"","https://example.invalid/video/"+i,"qa",Collections.emptyMap());
        f.channels.set(i,channel);items.set(i,channel);
      }
      programs.put("epg0",new ArrayList<Object>());programme(1,LIVE_TITLE);programme(2,"News");programme(3,"News");
      set(f.a,"mGuidePreviewChannel",items.get(1));((BaseAdapter)original).notifyDataSetChanged();call(f.a,"cobraRefreshModeDetails");f.frames();
      assertEquals(2,grid.getNumColumns());assertTrue(grid.getChildCount()>=4);assertEquals(941,f.a.getWindow().getDecorView().getWidth());
      assertNull(get(f.a,"mPlayer"));assertNull(get(f.a,"mCobraPreviewPlayer"));
    }
    void programme(int position,String title)throws Exception{
      Object p=create("GuideProgram");set(p,"channel","epg"+position);set(p,"title",title);set(p,"description","Synthetic reference-length programme");long now=System.currentTimeMillis();set(p,"start",now-3600000L);set(p,"stop",now+3600000L);ArrayList<Object> list=new ArrayList<>();list.add(p);programs.put("epg"+position,list);
    }
    View card(int adapterPosition){int local=adapterPosition-grid.getFirstVisiblePosition();assertTrue(local>=0&&local<grid.getChildCount());return grid.getChildAt(local);}
    void publish()throws Exception{((BaseAdapter)original).notifyDataSetChanged();call(f.a,"cobraRefreshModeDetails");f.frames();}
  }
  static void visibleTextFits(TextView text){
    assertEquals(View.VISIBLE,text.getVisibility());assertNotNull(text.getLayout());Layout layout=text.getLayout();int lines=Math.min(layout.getLineCount(),text.getMaxLines());assertTrue(lines>0);
    assertTrue("actual allowed text lines fit native TextView",layout.getLineBottom(lines-1)<=text.getHeight()-text.getCompoundPaddingTop()-text.getCompoundPaddingBottom());
  }
  static JSONObject row(View left,View right)throws Exception{
    assertEquals("peers share top",left.getTop(),right.getTop());assertEquals("peers share measured height",left.getHeight(),right.getHeight());assertEquals(left.getBottom(),right.getBottom());
    JSONObject report=new JSONObject().put("left",rectJson(left)).put("right",rectJson(right));JSONArray content=new JSONArray();
    for(View card:new View[]{left,right}){
      TextView category=(TextView)get(card,"category"),title=(TextView)get(card,"title"),now=(TextView)get(card,"now"),time=(TextView)get(card,"time");ProgressBar progress=(ProgressBar)get(card,"progress");
      visibleTextFits(category);visibleTextFits(title);visibleTextFits(now);Rect area=rect(card),body=rect(now);
      assertTrue("programme/status box stays inside card",area.contains(body));assertTrue("native channel title above programme",rect(title).bottom<=body.top);
      View corner=more(card);for(View text:new View[]{category,title,now})assertFalse("More excludes text touch targets",Rect.intersects(rect(corner),rect(text)));
      JSONObject cell=new JSONObject().put("native_tag",card.getTag()).put("category",rectJson(category)).put("title",rectJson(title)).put("programme",rectJson(now)).put("programme_text",now.getText()).put("programme_lines",now.getLayout().getLineCount()).put("time",rectJson(time)).put("time_visible",time.getVisibility()).put("progress",rectJson(progress)).put("progress_visible",progress.getVisibility()).put("more",rectJson(corner));content.put(cell);
      if(progress.getVisibility()==View.VISIBLE){visibleTextFits(time);assertTrue("programme above LIVE footer",body.bottom<=rect(time).top);assertTrue("progress below footer",rect(time).bottom<=rect(progress).top);assertTrue("progress remains inside card",area.contains(rect(progress)));}
    }
    return report.put("actual_content_and_footer",content);
  }
  @Test public void nativeWrappedMissingScheduleAndLivePeersShareMeasuredRows()throws Exception{
    Rows r=new Rows();header(r.f);Object missing=r.items.get(0);assertNull(call(r.f.a,"cobraCurrentProgram",missing));String status=String.valueOf(call(r.f.a,"cobraGuideStatus",missing));TextView label=(TextView)get(r.card(0),"now");assertEquals("actual native status, no fabricated text",status,label.getText().toString());assertTrue("reference-like genuine missing status wraps",label.getLayout().getLineCount()>=2);assertEquals(0,label.getLayout().getEllipsisCount(label.getLayout().getLineCount()-1));
    View first=r.card(0),peer=r.card(1);JSONObject report=row(first,peer);assertTrue("next row starts below taller pair",r.card(2).getTop()>=first.getBottom()+r.grid.getVerticalSpacing());assertTrue("wrapped row grows beyond short row",first.getHeight()>r.card(2).getHeight());
    assertEquals(View.GONE,((View)get(first,"progress")).getVisibility());assertEquals(View.VISIBLE,((View)get(peer,"progress")).getVisibility());
    report.put("native_status",status).put("native_live_title",((TextView)get(peer,"now")).getText()).put("next_pair",row(r.card(2),r.card(3))).put("geometry",r.f.geometry()).put("header_weight",brand(r.f).getTypeface().getWeight()).put("private_reference_png_in_repository",false);write("native-mixed-paired-rows",report);r.f.image("native-mixed-reference-length-rows");
  }
  @Test public void nativeRowRecyclingAndContentChangesPreserveAnchors()throws Exception{
    Rows r=new Rows();int tall=r.card(0).getHeight();r.programme(3,LIVE_TITLE);View recycled=r.original.getView(2,null,r.grid),peer=r.original.getView(3,null,r.grid);assertEquals("short text uses actual next-row LIVE peer extent",recycled.getLayoutParams().height,peer.getLayoutParams().height);assertTrue(recycled.getLayoutParams().height>r.card(2).getHeight());assertSame(recycled,r.original.getView(0,recycled,r.grid));assertEquals("cobra-channel:qa:0",recycled.getTag());assertEquals(String.valueOf(call(r.f.a,"cobraGuideStatus",r.items.get(0))),((TextView)get(recycled,"now")).getText().toString());assertEquals(View.GONE,((View)get(recycled,"progress")).getVisibility());assertSame(recycled,r.original.getView(1,recycled,r.grid));assertEquals("cobra-channel:qa:1",recycled.getTag());assertEquals(View.VISIBLE,((View)get(recycled,"progress")).getVisibility());r.programme(0,"News");r.programme(1,"News");r.publish();int shortHeight=r.card(0).getHeight();assertTrue("same real adapter shrinks after text shortens",shortHeight<tall);row(r.card(0),r.card(1));
    r.grid.setSelection(8);r.f.layout();r.grid.scrollListBy(17);r.f.layout();int first=r.grid.getFirstVisiblePosition(),top=r.grid.getChildAt(0).getTop();assertTrue("nonzero native scroll anchor",first>0);View retained=r.grid.getChildAt(0);assertTrue(retained.requestFocus());View focus=r.grid.findFocus();assertNotNull(focus);Object selected=r.original.getItem(first);set(r.f.a,"mGuidePreviewChannel",selected);
    CountedAdapter counted=new CountedAdapter(r.original);r.grid.setAdapter(counted);r.grid.setSelection(first);r.f.layout();r.grid.scrollListBy(r.grid.getChildAt(0).getTop()-top);r.f.layout();retained=r.grid.getChildAt(0);assertTrue(retained.requestFocus());focus=r.grid.findFocus();first=r.grid.getFirstVisiblePosition();top=retained.getTop();
    int beforeViews=counted.views;counted.items=0;counted.positions.clear();guideProjections=0;currentProjections=0;View rebound=counted.getView(first,retained,r.grid);assertSame("native recycling retains actual card",retained,rebound);
    int initialLookups=counted.items;List<Integer> initialPositions=new ArrayList<>(counted.positions);int rowStart=(first/r.grid.getNumColumns())*r.grid.getNumColumns();assertTrue("identity validation plus bounded row peers",initialLookups<=r.grid.getNumColumns()+1);for(int position:initialPositions)assertTrue("no off-row/inventory lookup",position>=rowStart&&position<Math.min(rowStart+r.grid.getNumColumns(),counted.getCount()));assertEquals("no Home/current-view projection during card bind",0,currentProjections);assertEquals("no repeated guide projection during card bind",0,guideProjections);
    r.programme(first,LIVE_TITLE);int oldHeight=retained.getHeight();call(retained,"bind",selected,first);r.f.frames();assertSame(retained,r.grid.getChildAt(0));assertSame(focus,r.grid.findFocus());assertEquals(first,r.grid.getFirstVisiblePosition());assertEquals(top,r.grid.getChildAt(0).getTop());assertTrue(retained.isSelected());assertEquals(LIVE_TITLE,((TextView)get(retained,"now")).getText().toString());assertTrue(retained.getHeight()>oldHeight);
    write("native-recycle-content-anchor",new JSONObject().put("before_shortening_height",tall).put("short_height",shortHeight).put("first_visible",first).put("first_top",top).put("retained_focus_identity",System.identityHashCode(focus)).put("single_bind_getItem_calls",initialLookups).put("single_bind_getItem_positions",new JSONArray(initialPositions)).put("total_followup_getItem_calls",counted.items).put("native_getView_calls",counted.views-beforeViews).put("guide_projection_calls",guideProjections).put("current_projection_calls",currentProjections).put("actual_card_tag",retained.getTag()));
  }
  static void press(CobraCardsLayoutTest.Fixture f,View target)throws Exception{
    Rect visible=new Rect();assertTrue("actual target visible before press",target.getGlobalVisibleRect(visible));assertTrue(visible.width()>8&&visible.height()>8);View root=f.a.getWindow().getDecorView();int[] origin=new int[2];root.getLocationOnScreen(origin);long down=SystemClock.uptimeMillis();
    for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}){if(action==MotionEvent.ACTION_UP)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,visible.exactCenterX()-origin[0],visible.exactCenterY()-origin[1],0);e.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);try{assertTrue(root.dispatchTouchEvent(e));}finally{e.recycle();}}
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));
  }
  @Test public void nativeMoreAndRowTargetsKeepTheirCurrentChannelAfterGrowth()throws Exception{
    Rows r=new Rows();Object expected=r.items.get(1);View current=r.card(1);row(r.card(0),current);press(r.f,more(current));View sheet=(View)get(r.f.a,"mCobraActionSheet");assertNotNull("real native More menu",sheet);assertTrue(sheet.isAttachedToWindow());boolean named=false,heading=false;for(View v:descendants(sheet))if(v instanceof TextView){String t=((TextView)v).getText().toString();named|=t.contains(String.valueOf(get(expected,"name")));heading|=t.equals("Channel actions");}assertTrue(named&&heading);assertTrue(previews.isEmpty());assertTrue(peeks.isEmpty());assertTrue((Boolean)call(r.f.a,"closeCobraActionSheet"));r.f.frames();
    current=r.card(1);press(r.f,(View)get(current,"now"));assertEquals("one native row press",1,previews.size());assertSame("actual current bound channel",expected,previews.get(0));assertTrue(peeks.isEmpty());write("grown-row-real-target-dispatch",new JSONObject().put("actual_pointer_presses",2).put("native_more_bound_channel",get(expected,"id")).put("row_terminal_bound_channel",get(previews.get(0),"id")).put("native_menu_body","EXECUTED_UNCHANGED").put("decoder","NOT_EXECUTED"));
  }
  static Object styleSubset(Object value)throws Exception{
    if(value instanceof JSONObject){JSONObject source=(JSONObject)value,result=new JSONObject();for(Iterator<String> keys=source.keys();keys.hasNext();){String key=keys.next();if(!key.equals("text"))result.put(key,styleSubset(source.get(key)));}return result;}
    if(value instanceof JSONArray){JSONArray source=(JSONArray)value,result=new JSONArray();for(int i=0;i<source.length();i++)result.put(styleSubset(source.get(i)));return result;}
    return value;
  }
  @Test public void cardsHeaderAndRowsLeaveFourNativeModesUnchanged()throws Exception{
    List<String> errors=new ArrayList<>();for(String mode:CobraCardsLayoutTest.MODES){Rows r=new Rows();header(r.f);Object preview=get(r.f.a,"mCobraGuideVideo"),texture=get(r.f.a,"mCobraPreviewTexture");r.f.mode(mode);for(String shared:CobraCardsLayoutTest.SHARED)CobraCardsLayoutTest.noOwnedCardsForeground((View)get(r.f.a,shared));assertSame(preview,get(r.f.a,"mCobraGuideVideo"));assertSame(texture,get(r.f.a,"mCobraPreviewTexture"));
      // The preserved reference fixture has identical synthetic inventory; use
      // its untouched metadata before comparing all shared native properties.
      CobraCardsLayoutTest.Fixture clean=new CobraCardsLayoutTest.Fixture("cards");header(clean);clean.mode(mode);JSONObject actual=clean.shared(),expected=CobraCardsLayoutTest.baseline(mode),mixed=r.f.shared();JSONArray ignored=new JSONArray(),mixedIgnored=new JSONArray();for(String field:CobraCardsLayoutTest.SHARED){CobraCardsLayoutTest.normalizeNamedGone(expected.getJSONObject(field),actual.getJSONObject(field),mode+"."+field,false,false,ignored);CobraCardsLayoutTest.normalizeNamedGone(CobraCardsLayoutTest.baseline(mode).getJSONObject(field),mixed.getJSONObject(field),mode+"."+field,false,false,mixedIgnored);}String difference=CobraCardsLayoutTest.diff(expected,actual,mode);if(difference!=null)errors.add(difference);String mixedDifference=CobraCardsLayoutTest.diff(styleSubset(expected),styleSubset(mixed),mode+".mixed_native_style_and_hierarchy");if(mixedDifference!=null)errors.add(mixedDifference);assertTrue("current mixed-data programme preserved",((TextView)get(r.f.a,"mCobraGuideNowLabel")).getText().toString().contains(LIVE_TITLE));write("restored-native-"+mode,new JSONObject().put("shared",actual).put("approved_gone_geometry_only",ignored).put("mixed_row_shared",mixed).put("mixed_style_comparison","ALL_PROPERTIES_EXCEPT_DYNAMIC_TEXT_VALUES; native geometry exceptions remain exact previously approved subset").put("mixed_approved_gone_geometry_only",mixedIgnored));}
    assertEquals("all four existing native modes preserve approved shared properties",Collections.emptyList(),errors);
  }
}
