package com.projectinfinity.kodi;
import android.content.Context;import android.os.*;import androidx.mediarouter.media.*;import com.google.android.gms.cast.framework.*;import com.google.android.gms.cast.framework.media.*;
public final class SessionContractTest {
 static CastSession last;static int checks;static void check(boolean ok,String m){checks++;if(!ok)throw new AssertionError(m);}
 static void field(Object o,String n,Object v)throws Exception {java.lang.reflect.Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
 static InfinityCastSession setup(long connection,long relay,long load)throws Exception {
  Handler.reset();RemoteMediaClient.loadDelay=load;RemoteMediaClient.dropLoad=false;RemoteMediaClient.dropSeek=false;RemoteMediaClient.loadCode=0;InfinityCastRelay.delay=relay;InfinityCastRelay.stall=false;
  java.lang.reflect.Field i=InfinityCastSession.class.getDeclaredField("instance");i.setAccessible(true);i.set(null,null);
  InfinityCastSession c=InfinityCastSession.get(new Context());CastContext sdk=new CastContext();CastSession session=last=new CastSession();
  field(c,"initialized",true);field(c,"sdk",sdk);field(c,"router",MediaRouter.instance);field(c,"selector",new MediaRouteSelector.Builder().build());
  MediaRouter.instance.list.clear();MediaRouter.RouteInfo route=new MediaRouter.RouteInfo();route.select=()->new Handler(Looper.getMainLooper()).postDelayed(()->{sdk.manager.current=session;c.onSessionStarting(session);c.onSessionStarted(session,"fixture");},connection);MediaRouter.instance.list.add(route);
  c.attach(()->{});Handler.advance(1);c.choose(0);return c;
 }
 public static void main(String[] args)throws Exception {
  InfinityCastSession quick=setup(1000,1000,1000);Handler.advance(5000);check(quick.casting(),"quick real controller handoff");quick.returnToPhone();Handler.advance(6000);check(!quick.phone.paused&&!quick.hasRetainedPhone(),"phone restored and lease retired");
  InfinityCastSession slow=setup(12000,5000,6000);Handler.advance(24000);check(slow.casting(),"successful connected source+load must not be aborted by expired connection-only timer");
  check(slow.phone.paused,"successful Cast owns the paused phone player");slow.returnToPhone();Handler.advance(25000);check(!slow.phone.paused&&slow.phone.releases==1,"return after delayed transfer releases native ownership");
  InfinityCastSession noConnect=setup(30000,0,0);Handler.advance(21000);check(!noConnect.transferring()&&noConnect.phone.releases==1,"connection timeout bounded with lease release");
  InfinityCastSession noSource=setup(1000,0,0);InfinityCastRelay.stall=true;Handler.advance(22000);check(!noSource.transferring()&&InfinityCastRelay.latest.closed,"source preparation timeout closes owned relay");
  InfinityCastSession noLoad=setup(1000,1000,0);RemoteMediaClient.dropLoad=true;Handler.advance(23000);check(!noLoad.transferring()&&!noLoad.phone.paused&&InfinityCastRelay.latest.closed,"missing SDK load callback cannot hang or pause phone");
  InfinityCastSession noSeek=setup(1000,1000,1000);RemoteMediaClient.dropSeek=true;Handler.advance(12000);check(!noSeek.transferring()&&!noSeek.phone.paused&&noSeek.phone.releases==1,"missing receiver seek callback restores phone and releases lease");check(noSeek.message.contains("playback position"),"seek failure reason survives successful phone restoration");
  InfinityCastSession rejected=setup(1000,1000,1000);RemoteMediaClient.loadCode=2100;Handler.advance(4000);check(!rejected.transferring()&&!rejected.phone.paused,"receiver load rejection preserves phone");check(rejected.message.contains("2100"),"receiver status code preserved in visible failure");
  InfinityCastSession cancel=setup(1000,1000,8000);Handler.advance(3000);RemoteMediaClient pending=last.client;cancel.returnToPhone();Handler.advance(15000);check(pending.plays==0&&cancel.phone.releases==1&&!cancel.phone.paused,"late SDK load completion after cancel cannot start playback or retain owner");
  InfinityCastSession remoteError=setup(1000,1000,1000);Handler.advance(4000);last.client.status.state=1;last.client.status.idle=2;last.client.fire();Handler.advance(5000);check(!remoteError.phone.paused&&!remoteError.transferring(),"receiver media error restores existing phone player");check(remoteError.message.contains("TV playback failed")&&remoteError.message.contains("Returned"),"media failure remains visible after cleanup");
  System.out.println("PASS_ACTUAL_CAST_CONTROLLER_CONTRACT checks="+checks+"; deterministic SDK/native backends; no receiver claim");
 }
}
