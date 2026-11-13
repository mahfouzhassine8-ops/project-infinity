package com.projectinfinity.kodi;
import android.content.Context;import android.os.*;import androidx.mediarouter.media.*;import com.google.android.gms.cast.framework.*;import com.google.android.gms.cast.framework.media.*;
public final class SessionContractTest {
 static int checks;static void check(boolean ok,String m){checks++;if(!ok)throw new AssertionError(m);}
 static void field(Object o,String n,Object v)throws Exception {java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
 static InfinityCastSession setup(long connection,long relay,long load)throws Exception {
  Handler.reset();RemoteMediaClient.loadDelay=load;RemoteMediaClient.dropLoad=false;RemoteMediaClient.dropSeek=false;RemoteMediaClient.loadCode=0;InfinityCastRelay.delay=relay;InfinityCastRelay.stall=false;
  java.lang.reflect.Field i=InfinityCastSession.class.getDeclaredField("instance");i.setAccessible(true);i.set(null,null);
  InfinityCastSession c=InfinityCastSession.get(new Context());CastContext sdk=new CastContext();CastSession session=new CastSession();
  field(c,"initialized",true);field(c,"sdk",sdk);field(c,"router",MediaRouter.instance);field(c,"selector",new MediaRouteSelector.Builder().build());
  MediaRouter.instance.list.clear();MediaRouter.RouteInfo route=new MediaRouter.RouteInfo();route.select=()->new Handler(Looper.getMainLooper()).postDelayed(()->{sdk.manager.current=session;c.onSessionStarting(session);c.onSessionStarted(session,"fixture");},connection);MediaRouter.instance.list.add(route);
  c.attach(()->{});Handler.advance(1);c.choose(0);return c;
 }
 public static void main(String[] args)throws Exception {
  InfinityCastSession quick=setup(1000,1000,1000);Handler.advance(5000);check(quick.casting(),"quick real controller handoff");quick.returnToPhone();Handler.advance(6000);check(!quick.phone.paused&&!quick.hasRetainedPhone(),"phone restored and lease retired");
  InfinityCastSession slow=setup(12000,5000,6000);Handler.advance(24000);check(slow.casting(),"successful connected source+load must not be aborted by expired connection-only timer");
  System.out.println("PASS_ACTUAL_CAST_CONTROLLER_CONTRACT checks="+checks+"; deterministic SDK/native backends; no receiver claim");
 }
}
