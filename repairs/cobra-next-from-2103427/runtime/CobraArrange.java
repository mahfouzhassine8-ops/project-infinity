package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.os.Handler;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

/** UI-only adapter around the shipped Cobra tile store. Never calls a player API
 * that changes playback, constructs a session, tunes, seeks or transfers audio.
 * All reflection targets are pinned, Cobra-owned existing fields/methods and
 * exercised against the actual rebuilt production DEX before release.
 */
public final class CobraArrange {
  private static final WeakHashMap<Activity,WeakReference<CobraArrange>> OWNERS=new WeakHashMap<>();
  private final WeakReference<Activity> owner;
  private final Map<String,Field> fields=new HashMap<>();
  private final Map<String,Method> methods=new HashMap<>();
  private final IdentityHashMap<View,Touch> listeners=new IdentityHashMap<>();
  private final Handler handler=new Handler(Looper.getMainLooper());
  private FrameLayout attached;
  private Gesture gesture;
  private Preview preview;
  private final View.OnAttachStateChangeListener attachment=new View.OnAttachStateChangeListener(){
    public void onViewAttachedToWindow(View v){}
    public void onViewDetachedFromWindow(View v){cancel();clearTouches();v.removeOnAttachStateChangeListener(this);attached=null;}
  };

  public CobraArrange(Activity activity){owner=new WeakReference<>(activity);}
  private static CobraArrange get(Activity a){
    if(!a.getClass().getName().equals("com.projectinfinity.kodi.InfinityLiveActivity"))
      throw new IllegalArgumentException("Cobra owner required");
    synchronized(OWNERS){
      WeakReference<CobraArrange> reference=OWNERS.get(a);CobraArrange value=reference==null?null:reference.get();
      if(value==null){value=new CobraArrange(a);OWNERS.put(a,new WeakReference<>(value));}return value;
    }
  }
  private Activity activity(){Activity a=owner.get();if(a==null)throw new IllegalStateException("Cobra owner retired");return a;}
  private Field field(Object object,String name){
    String key=object.getClass().getName()+"#"+name;Field f=fields.get(key);
    if(f==null)try{f=object.getClass().getDeclaredField(name);f.setAccessible(true);fields.put(key,f);}
    catch(ReflectiveOperationException e){throw new IllegalStateException("Cobra field binding: "+name,e);}return f;
  }
  private Object read(Object o,String name){try{return field(o,name).get(o);}catch(IllegalAccessException e){throw new IllegalStateException(e);}}
  private Object read(String name){return read(activity(),name);}
  private void write(String name,Object value){try{field(activity(),name).set(activity(),value);}catch(IllegalAccessException e){throw new IllegalStateException(e);}}
  private Object call(Object object,String name,Class<?>[] types,Object...args){
    String key=object.getClass().getName()+"#"+name+Arrays.toString(types);Method m=methods.get(key);
    if(m==null)try{
      try{m=object.getClass().getDeclaredMethod(name,types);}
      catch(NoSuchMethodException inherited){m=object.getClass().getMethod(name,types);}
      m.setAccessible(true);methods.put(key,m);}
    catch(ReflectiveOperationException e){throw new IllegalStateException("Cobra method binding: "+name,e);}
    try{return m.invoke(object,args);}catch(ReflectiveOperationException e){throw new IllegalStateException("Cobra method failed: "+name,e);}
  }
  private Object call(String name){return call(activity(),name,new Class<?>[0]);}
  @SuppressWarnings("unchecked") private LinkedHashMap<String,Object> entries(){return (LinkedHashMap<String,Object>)read(read("mCobraTiles"),"entries");}
  private String profile(){Object features=read("mFeatures");return features==null?"default":String.valueOf(call(features,"activeProfileId",new Class<?>[0]));}
  private String pref(int n){return "cobra_multiview_arrangement."+profile()+"."+n;}
  private SharedPreferences prefs(){return (SharedPreferences)read("mPrefs");}
  private String chosen(int n){SharedPreferences p=prefs();String id=p==null?"":p.getString(pref(n),"");return CobraLayoutCatalog.valid(id,n)?id:"";}
  private int dp(int n){return Math.max(1,Math.round(n*activity().getResources().getDisplayMetrics().density));}

  public static boolean isPro(Activity a){CobraArrange c=get(a);return Boolean.TRUE.equals(c.read("mCobraProActive")) && "focus".equals(c.read("mCobraGuideStyle"));}
  public static int[] rect(Activity a,int[] original,int index,int count,int w,int h,int enlarged,boolean fill){
    if(enlarged>=0 || count<2 || count>4)return original;
    CobraArrange c=get(a);String id=c.chosen(count);
    return id.isEmpty()?original:CobraLayoutCatalog.rect(id,index,count,w,h,c.dp(8));
  }
  public static void afterLayout(Activity a){get(a).after();}
  public static boolean cancelActive(Activity a){CobraArrange c=get(a);boolean active=c.gesture!=null;c.cancel();return active;}
  public static void addLayouts(Activity a,LinearLayout rows){
    CobraArrange c=get(a);Snapshot offered=c.snapshot();if(offered==null)return;int n=offered.keys.size();
    for(final String id:CobraLayoutCatalog.forCount(n))
      c.row(rows,"multi",CobraLayoutCatalog.label(id),id.equals(c.chosen(n))?"Selected":null,
          "cobra_arrangement_"+id,()->{if(c.menuStillCurrent(offered))c.select(id);});
  }
  public static void addActions(Activity a,LinearLayout rows,String key){
    CobraArrange c=get(a);Snapshot offered=c.snapshot();if(rows==null || offered==null || !offered.keys.contains(key))return;
    c.row(rows,"multi","Move Screen",null,"cobra_move_screen",()->{if(c.menuStillCurrent(offered))c.moves(key);});
    c.row(rows,"multi","Arrange Screen",null,"cobra_arrange_screen",()->{if(c.menuStillCurrent(offered))c.arrangements();});
  }
  private void row(LinearLayout rows,String icon,String title,String detail,String tag,Runnable action){
    if(rows.findViewWithTag(tag)!=null)return;
    View view=(View)call(activity(),"cobraSheetRow",new Class<?>[]{String.class,String.class,String.class,boolean.class,boolean.class,Runnable.class},
        icon,title,detail,false,Boolean.TRUE.equals(call("cobraSheetIsDark")),action);
    final Object menu=read("mCobraActionSheet");
    // Preserve native close-then-action semantics, but validate ownership before
    // closing. A queued click from a detached old menu cannot close a newer one.
    view.setOnClickListener(v->{if(menu!=null && read("mCobraActionSheet")==menu){call("closeCobraActionSheet");action.run();}});
    view.setTag(tag);rows.addView(view);
  }
  private LinearLayout sheet(String title){return (LinearLayout)call(activity(),"cobraOpenSheet",new Class<?>[]{String.class,String.class,String.class},title,null,"multi-arrange");}
  private void moves(final String key){
    LinearLayout rows=sheet("Move Screen");
    final Snapshot offered=snapshot();if(offered==null)return;
    int index=0;for(final String target:new ArrayList<>(entries().keySet())){
      final int number=++index;if(target.equals(key))continue;
      row(rows,"multi","Swap with screen "+number,null,"cobra_swap_"+number,()->{
        Snapshot s=snapshot();if(menuStillCurrent(offered) && s!=null && s.keys.contains(key)&&s.keys.contains(target)){
          call("closeCobraActionSheet");reorder(s,key,target,null,false);}
      });
    }
  }
  private void arrangements(){LinearLayout rows=sheet("Multi-View layout");addLayouts(activity(),rows);}
  private void select(String id){
    Snapshot s=snapshot();if(s==null || !CobraLayoutCatalog.valid(id,s.keys.size()))return;
    call("closeCobraActionSheet");commitLayout(id);write("mCobraMultiEnlargedKey","");
    call("cobraLayoutMultiTiles");call("showMultiChromeTemporarily");
  }
  private void commitLayout(String id){SharedPreferences p=prefs();if(p!=null)p.edit().putString(pref(CobraLayoutCatalog.count(id)),id).apply();}

  private final class Snapshot {
    final FrameLayout canvas;final int width,height,x,y,density;
    final String profile,mode,layout;final boolean full;
    final Object modeOwner,uiOwner,modal;
    final Rect area;
    final ArrayList<String> keys;final ArrayList<Object> tiles=new ArrayList<>(),players=new ArrayList<>(),bindings=new ArrayList<>(),textures=new ArrayList<>();
    final ArrayList<View> views=new ArrayList<>();final ArrayList<Rect> boxes=new ArrayList<>();
    Snapshot(){
      canvas=(FrameLayout)read("mCobraMultiCanvas");width=canvas==null?0:canvas.getWidth();height=canvas==null?0:canvas.getHeight();
      int[] at=new int[2];if(canvas!=null)canvas.getLocationOnScreen(at);x=at[0];y=at[1];
      density=Float.floatToIntBits(activity().getResources().getDisplayMetrics().density);
      profile=profile();mode=String.valueOf(read("mCobraGuideStyle"))+read("mCobraProActive")+read("mCobraMultiEnlargedKey");
      modeOwner=read("mCobraModeLayout");uiOwner=read("mUi");modal=read("mCobraActionSheet");
      full=Boolean.TRUE.equals(read("mCobraMultiFullscreenActive")) || Boolean.TRUE.equals(read("mCobraPlayerLocked"));keys=new ArrayList<>(entries().keySet());layout=chosen(keys.size());
      int[] insets=Boolean.TRUE.equals(call("cobraMultiFillScreen"))?(int[])call("cobraMultiSafeInsets"):new int[4];
      area=new Rect(insets[0],insets[1],Math.max(insets[0]+1,width-insets[2]),Math.max(insets[1]+1,height-insets[3]));
      Map<?,?> owners=(Map<?,?>)read("mCobraPlayerBindings");
      for(String key:keys){Object tile=entries().get(key),player=read(tile,"player");
        tiles.add(tile);players.add(player);Object binding=owners.get(player);bindings.add(binding);textures.add(binding==null?read(tile,"texture"):read(binding,"texture"));
        View view=(View)read(tile,"view");views.add(view);
        ViewGroup.LayoutParams raw=view.getLayoutParams();
        if(raw instanceof FrameLayout.LayoutParams){FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)raw;boxes.add(new Rect(p.leftMargin,p.topMargin,p.leftMargin+p.width,p.topMargin+p.height));}
        else boxes.add(new Rect(view.getLeft(),view.getTop(),view.getRight(),view.getBottom()));
      }
    }
    boolean alive(){
      if(canvas==null || width<1 || height<1 || full || keys.size()<2 || keys.size()>4 || activity().isFinishing() || activity().isDestroyed() ||
          Boolean.TRUE.equals(read("mBackgroundStopped")) || Boolean.TRUE.equals(read("mInPictureInPicture")))return false;
      for(int i=0;i<keys.size();i++){
        Object player=players.get(i);
        if(player==null || (bindings.get(i)!=null && Boolean.TRUE.equals(read(bindings.get(i),"closed"))))return false;
        int state=((Number)call(player,"getPlaybackState",new Class<?>[0])).intValue();
        if(state==1 || state==4)return false;
      }
      return true;
    }
    boolean same(Snapshot b){return sameState(b) && modal==b.modal;}
    boolean sameState(Snapshot b){return b!=null && canvas==b.canvas && width==b.width && height==b.height && x==b.x && y==b.y && density==b.density &&
        profile.equals(b.profile) && mode.equals(b.mode) && layout.equals(b.layout) && full==b.full && keys.equals(b.keys) &&
        modeOwner==b.modeOwner && uiOwner==b.uiOwner && area.equals(b.area) && boxes.equals(b.boxes) &&
        sameObjects(tiles,b.tiles) && sameObjects(players,b.players) && sameObjects(bindings,b.bindings) && sameObjects(textures,b.textures);}
  }
  private static boolean sameObjects(List<?> a,List<?> b){if(a.size()!=b.size())return false;for(int i=0;i<a.size();i++)if(a.get(i)!=b.get(i))return false;return true;}
  private Snapshot snapshot(){Snapshot s=new Snapshot();return s.alive()?s:null;}
  private boolean menuStillCurrent(Snapshot offered){
    // Native sheet rows close their sheet before invoking the callback. Only
    // that expected modal removal is allowed; session/profile/bounds must match.
    Snapshot current=snapshot();return offered.sameState(current) && current.modal==null;
  }

  private void reorder(Snapshot s,String source,String target,String layout,boolean promote){
    Snapshot now=snapshot();if(!s.same(now) || !s.keys.contains(source))return;
    ArrayList<String> keys=new ArrayList<>(s.keys);int from=keys.indexOf(source);
    if(promote){keys.remove(from);keys.add(0,source);}
    else if(layout!=null && layout.startsWith("pip-")){keys.remove(from);keys.add(source);}
    else{int to=keys.indexOf(target);if(to<0 || to==from)return;keys.set(from,target);keys.set(to,source);}
    int audio=(Integer)read("mAudioTile");String audioKey=audio>=0&&audio<s.keys.size()?s.keys.get(audio):null;
    String enlarged=String.valueOf(read("mCobraMultiEnlargedKey"));
    LinkedHashMap<String,Object> previous=entries(), ordered=new LinkedHashMap<>();
    for(String key:keys)ordered.put(key,previous.get(key));
    previous.clear();previous.putAll(ordered); // same tile/player objects, never reconcile/retune
    call("cobraSyncMultiArrays");if(audioKey!=null)write("mAudioTile",keys.indexOf(audioKey));
    if(layout!=null){commitLayout(layout);write("mCobraMultiEnlargedKey","");}
    else if(enlarged.equals(source))write("mCobraMultiEnlargedKey",target);
    else if(enlarged.equals(target))write("mCobraMultiEnlargedKey",source);
    call("cobraLayoutMultiTiles");call("showMultiChromeTemporarily");
    s.views.get(from).requestFocus();
  }

  private void after(){
    FrameLayout canvas=(FrameLayout)read("mCobraMultiCanvas");
    if(attached!=canvas){cancel();clearTouches();if(attached!=null)attached.removeOnAttachStateChangeListener(attachment);
      attached=canvas;if(canvas!=null)canvas.addOnAttachStateChangeListener(attachment);}
    if(canvas==null)return;
    if(gesture!=null && !gesture.start.same(snapshot()))cancel();
    IdentityHashMap<View,Boolean> live=new IdentityHashMap<>();
    ArrayList<View> ordered=new ArrayList<>();
    for(Map.Entry<String,Object> entry:entries().entrySet()){
      View view=(View)read(entry.getValue(),"view");live.put(view,true);ordered.add(view);
      if(!listeners.containsKey(view)){Touch touch=new Touch(entry.getKey());listeners.put(view,touch);view.setOnTouchListener(touch);}
    }
    for(View view:new ArrayList<>(listeners.keySet()))if(!live.containsKey(view)){view.setOnTouchListener(null);listeners.remove(view);}
    // Overlay main panes must draw below their secondary panes even after a
    // session swap; touching child order never detaches a Surface/TextureView.
    if(!ordered.isEmpty()){ArrayList<View> current=new ArrayList<>();
      for(int i=0;i<canvas.getChildCount();i++)if(live.containsKey(canvas.getChildAt(i)))current.add(canvas.getChildAt(i));
      if(!current.equals(ordered))for(View view:ordered)view.bringToFront();
    }
  }
  private void clearTouches(){for(View view:listeners.keySet())view.setOnTouchListener(null);listeners.clear();}
  private void cancel(){
    if(gesture!=null){handler.removeCallbacks(gesture.arm);gesture.touch.view.setPressed(false);
      if(gesture.touch.view.getParent()!=null)gesture.touch.view.getParent().requestDisallowInterceptTouchEvent(false);}
    gesture=null;if(preview!=null && attached!=null)attached.getOverlay().remove(preview);preview=null;
  }

  private final class Touch implements View.OnTouchListener {
    final String key;View view;Touch(String key){this.key=key;}
    public boolean onTouch(View v,MotionEvent event){
      view=v;int action=event.getActionMasked();
      if(action==MotionEvent.ACTION_DOWN){cancel();Snapshot s=snapshot();
        if(s==null || !v.isShown())return false;
        gesture=new Gesture(this,s,event.getRawX()-s.x,event.getRawY()-s.y,event.getPointerId(0),event.getEventTime());
        v.setPressed(true);handler.postDelayed(gesture.arm,ViewConfiguration.getLongPressTimeout());return true;}
      Gesture g=gesture;if(g==null || g.touch!=this)return true;
      if(action==MotionEvent.ACTION_CANCEL || action==MotionEvent.ACTION_POINTER_DOWN || event.getPointerCount()!=1 || event.getPointerId(0)!=g.pointer){cancel();return true;}
      Snapshot current=snapshot();if(!g.start.same(current)){cancel();return true;}
      float x=event.getRawX()-g.start.x,y=event.getRawY()-g.start.y;
      if(event.getEventTime()-g.downTime>=ViewConfiguration.getLongPressTimeout())g.held=true;
      float distance=(float)Math.hypot(x-g.downX,y-g.downY);
      if(action==MotionEvent.ACTION_MOVE){
        if(!g.held && distance>g.slop)g.earlyMovement=true;
        if(g.held && !g.earlyMovement && distance>g.slop){g.drag=true;v.setPressed(false);
          if(v.getParent()!=null)v.getParent().requestDisallowInterceptTouchEvent(true);
          g.update(x,y);if(preview==null){preview=new Preview(g);attached.getOverlay().add(preview);}preview.invalidateSelf();}
        return true;
      }
      if(action==MotionEvent.ACTION_UP){
        g.update(x,y);boolean drag=g.drag,hold=g.held,tap=!g.earlyMovement&&distance<=g.slop;
        cancel();
        if(drag){if(g.target!=null)reorder(g.start,key,g.target,g.layout,g.promote);}
        else if(hold && tap)v.performLongClick();
        else if(tap)v.performClick();
      }
      return true;
    }
  }
  private final class Gesture {
    final Touch touch;final Snapshot start;final float downX,downY;final int pointer,slop;final long downTime;
    boolean held,drag,earlyMovement,promote;String target,layout;
    final Runnable arm=()->{if(gesture==this)held=true;};
    Gesture(Touch t,Snapshot s,float x,float y,int pointer,long downTime){touch=t;start=s;downX=x;downY=y;this.pointer=pointer;this.downTime=downTime;slop=ViewConfiguration.get(activity()).getScaledTouchSlop();}
    void update(float x,float y){
      target=null;layout=null;promote=false;if(x<0||y<0||x>=start.width||y>=start.height)return;
      float rawX=x,rawY=y;x-=start.area.left;y-=start.area.top;
      int w=start.area.width(),h=start.area.height(),n=start.keys.size(),band=Math.min(dp(48),h/6),half=Math.min(dp(110),w/3);
      if(x<0||y<0||x>=w||y>=h)return;
      boolean targets=w>=dp(180)&&h>=dp(160);
      if(targets && x>=w/2-half && x<=w/2+half && y<band){layout=n==2?"pip-br":n==3?"main2":"main3";promote=true;target=touch.key;return;}
      if(targets && y>=h-band && x>=w/2-half && x<=w/2+half){layout=n==2?"equal2":n==3?"overlay2":"overlay3";promote=true;target=touch.key;return;}
      if(targets && y>=h-band && x<band && n>=3){layout=n==3?"columns3":"grid4";promote=true;target=touch.key;return;}
      if(targets && n==2 && (x<band||x>=w-band) && (y<band||y>=h-band)){
        layout="pip-"+(y<h/2?"t":"b")+(x<w/2?"l":"r");
        // Dropped pane becomes the small overlay; the other remains main.
        target=start.keys.get(1-start.keys.indexOf(touch.key));promote=false;return;
      }
      for(int i=start.boxes.size()-1;i>=0;i--)if(start.boxes.get(i).contains((int)rawX,(int)rawY)){
        String key=start.keys.get(i);if(!key.equals(touch.key))target=key;return;
      }
    }
  }
  private final class Preview extends Drawable {
    final Gesture g;final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);final int accent,panel;
    Preview(Gesture g){this.g=g;setBounds(0,0,g.start.width,g.start.height);
      accent=((Number)call(activity(),"cobraThemeColor",new Class<?>[]{String.class,int.class},"accent",0xff28b7d4)).intValue();
      panel=((Number)call(activity(),"cobraThemeColor",new Class<?>[]{String.class,int.class},"panel",0xff16191e)).intValue();}
    public void draw(Canvas canvas){
      paint.setColor(0xccffffff);paint.setStrokeWidth(dp(2));paint.setStyle(Paint.Style.STROKE);
      for(Rect box:g.start.boxes)canvas.drawRect(box,paint);
      int w=g.start.area.width(),h=g.start.area.height(),band=Math.min(dp(48),h/6),half=Math.min(dp(110),w/3);
      canvas.save();canvas.translate(g.start.area.left,g.start.area.top);
      if(w>=dp(180)&&h>=dp(160)){
        paint.setStyle(Paint.Style.FILL);paint.setColor((panel&0x00ffffff)|0xcc000000);
        canvas.drawRect(w/2-half,0,w/2+half,band,paint);canvas.drawRect(w/2-half,h-band,w/2+half,h,paint);
        paint.setColor(0xffffffff);paint.setTextSize(dp(12));paint.setTextAlign(Paint.Align.CENTER);
        canvas.drawText("Make main",w/2,band*0.65f,paint);
        canvas.drawText(g.start.keys.size()==2?"50/50":"Main + overlays",w/2,h-band*0.35f,paint);
        paint.setColor((panel&0x00ffffff)|0xcc000000);
        if(g.start.keys.size()>=3){canvas.drawRect(0,h-band,band,h,paint);
          paint.setColor(0xffffffff);canvas.drawText(g.start.keys.size()==3?"Columns":"Grid",band/2,h-band*0.35f,paint);}
        else for(int corner=0;corner<4;corner++){
          int left=corner%2==0?0:w-band,top=corner<2?0:h-band;
          paint.setColor((panel&0x00ffffff)|0xcc000000);canvas.drawRect(left,top,left+band,top+band,paint);
          paint.setColor(0xffffffff);canvas.drawText("PiP",left+band/2,top+band*0.65f,paint);
        }
      }
      canvas.restore();
      if(g.target!=null){
        ArrayList<String> order=new ArrayList<>(g.start.keys);int from=order.indexOf(g.touch.key);
        if(g.promote){order.remove(from);order.add(0,g.touch.key);}
        else if(g.layout!=null && g.layout.startsWith("pip-")){order.remove(from);order.add(g.touch.key);}
        else{int to=order.indexOf(g.target);order.set(from,g.target);order.set(to,g.touch.key);}
        for(int i=0;i<order.size();i++){
          Rect box;
          if(g.layout==null)box=g.start.boxes.get(i);
          else{int[] r=CobraLayoutCatalog.rect(g.layout,i,order.size(),w,h,dp(8));box=new Rect(r[0]+g.start.area.left,r[1]+g.start.area.top,r[0]+r[2]+g.start.area.left,r[1]+r[3]+g.start.area.top);}
          paint.setStyle(Paint.Style.FILL);paint.setColor((accent&0x00ffffff)|0x55000000);canvas.drawRect(box,paint);
          paint.setStyle(Paint.Style.STROKE);paint.setColor(0xffffffff);canvas.drawRect(box,paint);
          paint.setStyle(Paint.Style.FILL);paint.setTextSize(dp(16));paint.setTextAlign(Paint.Align.CENTER);
          canvas.drawText("Screen "+(g.start.keys.indexOf(order.get(i))+1),box.centerX(),box.centerY(),paint);
        }
      }
    }
    public void setAlpha(int alpha){paint.setAlpha(alpha);}
    public void setColorFilter(ColorFilter filter){paint.setColorFilter(filter);}
    public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
}
