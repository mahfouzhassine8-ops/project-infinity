package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Bitmap;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ImageView;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.WeakHashMap;

/** Admission and UI ownership only. Reuse the shipped downloader, executor,
 * connection/read limits and bounded bitmap cache. No new worker or polling. */
public final class CobraLogoRequests {
  private static final WeakHashMap<Activity,WeakReference<CobraLogoRequests>> OWNERS=new WeakHashMap<>();
  private final WeakReference<Activity> owner;
  private final Handler main=new Handler(Looper.getMainLooper());
  private final WeakHashMap<ImageView,Binding> bindings=new WeakHashMap<>();
  private final WeakHashMap<ImageView,String> waiting=new WeakHashMap<>();
  private final HashMap<String,Flight> active=new HashMap<>(); // <=4 existing-executor jobs
  private boolean posted;
  private final Runnable pumpTask=()->{posted=false;pump();};
  private CobraLogoRequests(Activity a){owner=new WeakReference<>(a);}
  private static CobraLogoRequests get(Activity a){
    WeakReference<CobraLogoRequests> ref=OWNERS.get(a);CobraLogoRequests c=ref==null?null:ref.get();
    if(c==null){c=new CobraLogoRequests(a);OWNERS.put(a,new WeakReference<>(c));}return c;
  }
  private Object field(String name){return CobraArrange.ownedField(owner.get(),name);}
  private Object call(String name,Class<?>[] types,Object...args){return CobraArrange.ownedCall(owner.get(),name,types,args);}
  private boolean alive(){Activity a=owner.get();return a!=null && Boolean.TRUE.equals(call("isCobraAsyncAlive",new Class<?>[0]));}
  @SuppressWarnings("unchecked") private Map<String,Bitmap> cache(){return (Map<String,Bitmap>)field("mCobraSportsLogos");}
  private final class Binding implements View.OnAttachStateChangeListener {
    String url;Binding(String u){url=u;}
    public void onViewAttachedToWindow(View v){schedule();}
    public void onViewDetachedFromWindow(View v){waiting.remove(v);bindings.remove(v);v.removeOnAttachStateChangeListener(this);}
  }
  private static final class Flight {
    final ImageView origin;Flight(ImageView v){origin=v;}
  }
  public static void request(Activity a,String url,ImageView view){
    if(url==null || url.isEmpty() || view==null)return;
    CobraLogoRequests c=get(a);if(!c.alive())return;
    Binding b=c.bindings.get(view);if(b==null){b=c.new Binding(url);c.bindings.put(view,b);view.addOnAttachStateChangeListener(b);}else b.url=url;
    Bitmap bitmap=c.cache().get(url);
    if(bitmap!=null){c.waiting.remove(view);view.setImageBitmap(bitmap);return;}
    c.waiting.put(view,url);c.schedule();
  }
  public static void deliver(Activity a,String url,Bitmap bitmap,ImageView original){
    CobraLogoRequests c=get(a);if(!c.alive() || bitmap==null)return;
    c.cache().put(url,bitmap); // same existing LRU48; no second bitmap cache
    for(ImageView view:new ArrayList<>(c.waiting.keySet())){
      Binding b=c.bindings.get(view);
      if(b!=null && url.equals(b.url) && url.equals(c.waiting.get(view))){
        c.waiting.remove(view);if(view.isAttachedToWindow())view.setImageBitmap(bitmap);
      }
    }
  }
  private void schedule(){if(!posted){posted=true;main.post(pumpTask);}}
  private void pump(){
    if(!alive()){waiting.clear();return;}
    for(ImageView view:new ArrayList<>(waiting.keySet())){
      if(active.size()>=4)break;
      Binding binding=bindings.get(view);String url=waiting.get(view);
      if(binding==null || url==null || !url.equals(binding.url)){waiting.remove(view);continue;}
      if(!view.isAttachedToWindow() || active.containsKey(url))continue;
      Bitmap bitmap=cache().get(url);if(bitmap!=null){waiting.remove(view);view.setImageBitmap(bitmap);continue;}
      Flight flight=new Flight(view);active.put(url,flight);
      Runnable job=()->{
        try{ImageView origin=flight.origin;if(owner.get()!=null && origin!=null && alive())
          call("lambda$cobraSportsLoadLogo$482$com-projectinfinity-kodi-InfinityLiveActivity",new Class<?>[]{String.class,ImageView.class},url,origin);
        }finally{main.post(()->finish(url,flight));}
      };
      boolean submitted=false;
      try{submitted=Boolean.TRUE.equals(call("submitCobraIo",new Class<?>[]{Runnable.class},job));}
      finally{if(!submitted)active.remove(url);}
      if(!submitted){waiting.clear();return;}
    }
  }
  private void finish(String url,Flight flight){
    if(active.get(url)!=flight)return;active.remove(url);
    // Success publication was posted before this completion on the same main
    // queue. Remove failed waiters too: do not create a retry/polling loop.
    for(ImageView view:new ArrayList<>(waiting.keySet()))if(url.equals(waiting.get(view)))waiting.remove(view);
    if(!waiting.isEmpty())schedule();
  }
}
