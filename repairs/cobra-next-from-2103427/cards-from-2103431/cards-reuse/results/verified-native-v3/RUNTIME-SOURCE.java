package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.GridView;
import android.widget.LinearLayout;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.WeakHashMap;

/** Reuses only the currently attached native Cards grid. No data/policy cache,
 * preferences write, worker, timer, player or lifecycle responsibility. */
public final class CobraCardsReuse {
  private static final WeakHashMap<Activity,WeakReference<State>> OWNERS=new WeakHashMap<>();
  private static final Map<String,Field> FIELDS=new HashMap<>();
  private static final Map<String,Method> METHODS=new HashMap<>();
  private static final Class<?>[] NONE=new Class<?>[0];
  private static final String NATIVE_CARD="com.projectinfinity.kodi.InfinityLiveActivity$CobraPosterChannelCard";
  private CobraCardsReuse(){}

  private static void main(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("Cards reuse requires main thread");}
  private static Field field(Object o,String name){
    String key=o.getClass().getName()+"#"+name;
    synchronized(FIELDS){Field f=FIELDS.get(key);if(f!=null)return f;
      try{f=o.getClass().getDeclaredField(name);f.setAccessible(true);FIELDS.put(key,f);return f;}
      catch(ReflectiveOperationException e){throw new IllegalStateException("Cards reuse field "+key,e);}}
  }
  private static Object read(Object o,String name){try{return field(o,name).get(o);}catch(IllegalAccessException e){throw new IllegalStateException(e);}}
  private static Object call(Object o,String name,Class<?>[] types,Object...args){
    String key=o.getClass().getName()+"#"+name+Arrays.toString(types);Method m;
    synchronized(METHODS){m=METHODS.get(key);if(m==null)try{m=o.getClass().getDeclaredMethod(name,types);m.setAccessible(true);METHODS.put(key,m);}catch(ReflectiveOperationException e){throw new IllegalStateException("Cards reuse method "+key,e);}}
    try{return m.invoke(o,args);}catch(InvocationTargetException e){Throwable cause=e.getCause();if(cause instanceof RuntimeException)throw (RuntimeException)cause;if(cause instanceof Error)throw (Error)cause;throw new IllegalStateException(cause);}catch(IllegalAccessException e){throw new IllegalStateException(e);}
  }
  private static int number(Object o,String name){return ((Number)read(o,name)).intValue();}
  private static String string(Object o,String name){return String.valueOf(read(o,name));}
  private static boolean cards(Activity a){return a!=null && "cards".equals(read(a,"mCobraGuideStyle")) && !Boolean.TRUE.equals(read(a,"mCobraProActive")) && !Boolean.TRUE.equals(read(a,"mCobraProSportsActive"));}
  private static State existing(Activity a){synchronized(OWNERS){WeakReference<State> ref=OWNERS.get(a);return ref==null?null:ref.get();}}
  private static Stamp stamp(Activity a){
    // This optional acceleration must not introduce a new preference-type
    // failure. An unsupported raw policy type simply requires native rendering,
    // which retains the existing policy/error behaviour without interpreting it.
    Object features=read(a,"mFeatures"),backing=read(features,"prefs");
    if(!(backing instanceof SharedPreferences))throw new IllegalStateException("Cards policy binding changed");
    SharedPreferences policy=(SharedPreferences)backing;String[] raw;
    try{raw=new String[]{policy.getString("active_profile","default"),policy.getString("profiles",""),policy.getString("source_meta","{}")};}
    catch(ClassCastException unsupportedPolicyType){return null;}
    return new Stamp(a,features,backing,raw);
  }
  private static boolean eligible(Activity a){
    if(!cards(a) || !"channels".equals(read(a,"mCobraGuideRoute")))return false;
    Object model=read(a,"mCobraModeLayout");if(model==null)return false;
    int[] directory=(int[])read(model,"directory"),browser=(int[])read(model,"browser");
    // Directory/group/source pages retain their original fresh count builder.
    if(directory[2]!=0 || directory[3]!=0 || browser[2]<=0 || browser[3]<=0)return false;
    return read(a,"mCobraGuideShell") instanceof ViewGroup && read(a,"mCobraGuideBrowser") instanceof LinearLayout
        && read(a,"mCobraGuideList") instanceof GridView && read(a,"mCobraGuideAdapter") instanceof BaseAdapter;
  }
  private static boolean tree(Activity a,State s){
    return eligible(a) && read(a,"mCobraGuideShell")==s.shell && read(a,"mCobraGuideBrowser")==s.browser
        && read(a,"mCobraGuideList")==s.grid && read(a,"mCobraGuideAdapter")==s.adapter
        && s.shell.isAttachedToWindow() && s.browser.isAttachedToWindow() && s.grid.isAttachedToWindow()
        && s.browser.getParent()==s.shell && s.grid.getParent()==s.browser && s.grid.getAdapter()==s.adapter
        && s.adapter.getCount()==s.count;
  }

  /** Called after existing Cards afterRender; captures fresh native membership
   * even before first layout, preserving any pending native scroll restoration. */
  public static void installed(Activity a){
    main();State prior=existing(a);
    if(!eligible(a)){if(prior!=null)prior.dispose();return;}
    ViewGroup shell=(ViewGroup)read(a,"mCobraGuideShell");LinearLayout browser=(LinearLayout)read(a,"mCobraGuideBrowser");
    GridView grid=(GridView)read(a,"mCobraGuideList");BaseAdapter adapter=(BaseAdapter)read(a,"mCobraGuideAdapter");
    if(!shell.isAttachedToWindow() || !browser.isAttachedToWindow() || !grid.isAttachedToWindow()
        || browser.getParent()!=shell || grid.getParent()!=browser || grid.getAdapter()!=adapter){if(prior!=null)prior.dispose();return;}
    if(prior!=null)prior.dispose();
    Stamp current=stamp(a);if(current==null)return;
    State next=new State(a,shell,browser,grid,adapter,current);
    synchronized(OWNERS){OWNERS.put(a,new WeakReference<>(next));}
    shell.addOnAttachStateChangeListener(next);browser.addOnAttachStateChangeListener(next);grid.addOnAttachStateChangeListener(next);
  }

  /** Only unchanged native membership/context may retain the current UI.
   * Never remember/reapply scroll here: a newly attached grid can have a valid
   * pending position before its first layout. The grid owns that state. */
  public static boolean tryReuse(Activity a){
    main();State s=existing(a);if(s==null)return false;
    if(!tree(a,s)){s.dispose();return false;}
    if(!string(a,"mCobraModePendingFocus").isEmpty())return false;
    Stamp fresh=stamp(a);if(fresh==null)return false;
    long favoriteVersion,recentVersion,customVersion;
    synchronized(s){
      if(s.disposed || s.inventory!=s.drawnInventory || s.sources!=s.drawnSources || s.collections!=s.drawnCollections
          || s.hidden!=s.drawnHidden || !s.stamp.same(fresh))return false;
      String category=string(a,"mCategory");
      if("FAVORITES".equals(category) && s.favorites!=s.drawnFavorites)return false;
      if("RECENT".equals(category) && s.recents!=s.drawnRecents)return false;
      if(category.startsWith("MY:") && s.custom!=s.drawnCustom)return false;
      favoriteVersion=s.favorites;recentVersion=s.recents;customVersion=s.custom;
    }
    int first=s.grid.getFirstVisiblePosition(),visible=s.grid.getChildCount();
    // No list reconstruction or notifyDataSetChanged: bind just the native
    // visible convertViews, retaining grid/adapter/child/selection identities.
    for(int i=0;i<visible;i++){
      View child=s.grid.getChildAt(i);
      if(first+i<0 || first+i>=s.adapter.getCount() || child==null
          || !child.getClass().getName().equals(NATIVE_CARD))return false;
    }
    for(int i=0;i<visible;i++){
      View child=s.grid.getChildAt(i);View rebound=s.adapter.getView(first+i,child,s.grid);
      if(rebound!=child)return false;
    }
    call(a,"cobraRefreshModeDetails",NONE);
    Object renderer=call(a,"vtheme",NONE);
    call(renderer,"tree",new Class<?>[]{View.class,String.class},s.browser,"guide.browser");
    int ambient=((Number)call(a,"cobraStaticAmbientMode",NONE)).intValue();
    boolean night=(Boolean)call(a,"cobraNightCinemaActive",NONE);
    call(a,"cobraRefreshGlassTree",new Class<?>[]{View.class,int.class,boolean.class},s.browser,ambient,night);
    CobraCardsLayout.afterRender(a);
    call(a,"cobraQueueVisibleGuides",NONE); // Existing request scheduler only.
    synchronized(s){s.drawnFavorites=favoriteVersion;s.drawnRecents=recentVersion;s.drawnCustom=customVersion;s.stamp=fresh;}
    return true;
  }

  public static void beforeShell(Activity a){main();State s=existing(a);if(s!=null && (!cards(a) || read(a,"mCobraGuideShell")!=s.shell))s.dispose();}
  public static void inventory(Activity a){State s=existing(a);if(s!=null)synchronized(s){s.inventory++;}}
  public static void sources(Activity a){State s=existing(a);if(s!=null)synchronized(s){s.sources++;}}
  public static void favorites(Activity a){State s=existing(a);if(s!=null)synchronized(s){s.favorites++;}}
  public static void collections(Activity a){State s=existing(a);if(s!=null)synchronized(s){s.collections++;}}
  public static void hidden(Activity a){State s=existing(a);if(s!=null)synchronized(s){s.hidden++;}}
  public static void custom(Activity a){State s=existing(a);if(s!=null)synchronized(s){s.custom++;}}
  public static void recent(Activity a,Object channel){
    // Publication hooks may be called off-main. Never inspect a mutable list,
    // view or preference here: the RECENT-only revision is conservative.
    State s=existing(a);if(s!=null)synchronized(s){s.recents++;}
  }

  private static final class State implements View.OnAttachStateChangeListener {
    final WeakReference<Activity> owner;final ViewGroup shell;final LinearLayout browser;final GridView grid;final BaseAdapter adapter;final int count;
    long inventory,sources,collections,hidden,favorites,recents,custom;
    final long drawnInventory=0,drawnSources=0,drawnCollections=0,drawnHidden=0;
    long drawnFavorites,drawnRecents,drawnCustom;Stamp stamp;boolean disposed;
    State(Activity a,ViewGroup shell,LinearLayout browser,GridView grid,BaseAdapter adapter,Stamp current){owner=new WeakReference<>(a);this.shell=shell;this.browser=browser;this.grid=grid;this.adapter=adapter;count=adapter.getCount();stamp=current;}
    public void onViewAttachedToWindow(View view){}
    public void onViewDetachedFromWindow(View view){dispose();}
    void dispose(){
      synchronized(this){if(disposed)return;disposed=true;}
      shell.removeOnAttachStateChangeListener(this);browser.removeOnAttachStateChangeListener(this);grid.removeOnAttachStateChangeListener(this);
      Activity a=owner.get();if(a!=null)synchronized(OWNERS){WeakReference<State> ref=OWNERS.get(a);if(ref!=null && ref.get()==this)OWNERS.remove(a);}
    }
  }

  /** A small current-context equality stamp; never an authorization result.
   * Native projection/auth runs unchanged whenever its raw inputs change. */
  private static final class Stamp {
    final Object prefs,features,featurePrefs,ui,theme,effective;
    final String[] text;final int[] geometry;
    Stamp(Activity a,Object currentFeatures,Object currentFeaturePrefs,String[] raw){
      prefs=read(a,"mPrefs");features=currentFeatures;featurePrefs=currentFeaturePrefs;
      ui=read(a,"mUi");theme=read(a,"mTheme");Object renderer=call(a,"vtheme",NONE);effective=call(renderer,"effective",NONE);
      Configuration config=a.getResources().getConfiguration();DisplayMetrics dm=a.getResources().getDisplayMetrics();
      text=new String[]{string(a,"mCobraGuideStyle"),string(a,"mCobraGuideRoute"),string(a,"mCobraGuideSource"),string(a,"mCategory"),string(a,"mSearch"),
          string(a,"mCobraListStateKey"),string(a,"mCobraFocusSchedule"),string(a,"mCobraModeGroupsExpanded"),
          raw[0],raw[1],raw[2],
          String.valueOf(read(ui,"sourceStamp")),String.valueOf(call(renderer,"palette",NONE)),config.toString(),
          String.valueOf(call(a,"cobraStaticAmbientMode",NONE)),String.valueOf(call(a,"cobraNightCinemaActive",NONE))};
      Object model=read(a,"mCobraModeLayout");ArrayList<Integer> values=new ArrayList<>();
      for(String name:new String[]{"toolbar","rail","directory","video","details","browser","footer"})for(int v:(int[])read(model,name))values.add(v);
      for(String name:new String[]{"width","height","columns","channelWidth"})values.add(number(model,name));
      values.add(Float.floatToIntBits(dm.density));values.add(Float.floatToIntBits(dm.scaledDensity));values.add(dm.densityDpi);
      geometry=new int[values.size()];for(int i=0;i<geometry.length;i++)geometry[i]=values.get(i);
    }
    boolean same(Stamp other){return prefs==other.prefs && features==other.features && featurePrefs==other.featurePrefs
        && ui==other.ui && theme==other.theme && effective==other.effective && Arrays.equals(text,other.text) && Arrays.equals(geometry,other.geometry);}
  }
}
