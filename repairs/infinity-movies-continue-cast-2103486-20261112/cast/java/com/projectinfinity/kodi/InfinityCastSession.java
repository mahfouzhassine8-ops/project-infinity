package com.projectinfinity.kodi;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.os.SystemClock;
import androidx.mediarouter.media.MediaRouteSelector;
import androidx.mediarouter.media.MediaRouter;
import com.google.android.gms.cast.CastMediaControlIntent;
import com.google.android.gms.cast.CastDevice;
import com.google.android.gms.cast.MediaInfo;
import com.google.android.gms.cast.MediaLoadRequestData;
import com.google.android.gms.cast.MediaMetadata;
import com.google.android.gms.cast.MediaSeekOptions;
import com.google.android.gms.cast.MediaStatus;
import com.google.android.gms.cast.framework.CastContext;
import com.google.android.gms.cast.framework.CastSession;
import com.google.android.gms.cast.framework.SessionManagerListener;
import com.google.android.gms.cast.framework.media.RemoteMediaClient;
import org.json.JSONObject;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** One explicit Infinity Cast session in :kodi; never initialized at startup. */
final class InfinityCastSession implements SessionManagerListener<CastSession> {
    interface View { void changed(); }
    private static InfinityCastSession instance;
    static InfinityCastSession get(Context context) {
        if(instance==null)instance=new InfinityCastSession(context.getApplicationContext());
        return instance;
    }
    final Handler ui=new Handler(Looper.getMainLooper());
    final InfinityCastGateway phone=new InfinityCastGateway();
    private final Context context;
    private WeakReference<View> view=new WeakReference<>(null);
    private final ExecutorService initialization=Executors.newSingleThreadExecutor(r->{
        Thread t=new Thread(r,"InfinityCastInitialization");t.setDaemon(true);return t;});
    private boolean initializing,initialized,discovering,initializationAttempted;
    private CastContext sdk;
    private MediaRouter router;
    private MediaRouteSelector selector;
    private CastSession session;
    private RemoteMediaClient remote;
    private InfinityCastChannel channel;
    private JSONObject source;
    private String mime,token="",mediaToken="";
    private InfinityCastSource privateSource;
    private InfinityCastRelay relay;
    private boolean phoneClockReady;
    private boolean handedOff,everPlayed,finished,returning,aborting,transferStarted,ticking,leaving,selecting;
    private boolean phoneWasPaused,mayHavePaused,restoreInFlight;
    private long lastPosition,lastDuration,epoch,nextNativePoll,returnDeadline,returnEpoch;
    String message="Preparing Infinity Cast…";
    final List<MediaRouter.RouteInfo> devices=new ArrayList<>();
    private final MediaRouter.Callback routes=new MediaRouter.Callback() {
        @Override public void onRouteAdded(MediaRouter r,MediaRouter.RouteInfo info){updateDevices();}
        @Override public void onRouteRemoved(MediaRouter r,MediaRouter.RouteInfo info){updateDevices();}
        @Override public void onRouteChanged(MediaRouter r,MediaRouter.RouteInfo info){updateDevices();}
    };
    private final RemoteMediaClient.Callback mediaEvents=new RemoteMediaClient.Callback() {
        @Override public void onStatusUpdated(){status();}
        @Override public void onMetadataUpdated(){status();}
    };
    private InfinityCastSession(Context context){this.context=context;}
    void attach(View value) {
        view=new WeakReference<>(value);
        if(!initialized && !initializationAttempted)initialize();
        else if(initialized){discover();if(!transferStarted && !handedOff && !phone.busy())capture();}
        changed();
    }
    void detach(View value) {
        if(view.get()==value)view.clear();
        stopDiscovery();
        if(transferStarted && !handedOff && !returning){message="Cast connection cancelled.";abortTransfer();}
        // The process-owned session keeps no Activity/View reference.
    }
    private void changed(){View target=view.get();if(target!=null)target.changed();}
    private void initialize() {
        initializing=true;initializationAttempted=true;message="Preparing Cast support…";changed();
        final long generation=++epoch;
        initialization.execute(()->{
            try {
                InfinityCastResources.install(context);
                ui.post(()->initializeSdk());
            } catch(Exception | LinkageError error) {
                ui.post(()->unavailable("The Cast component could not initialize. Phone playback is unchanged."));
            }
        });
        ui.postDelayed(()->{
            if(initializing && generation==epoch){message="Cast initialization has not completed. Phone playback is unchanged.";changed();}
        },12000);
    }
    private void initializeSdk() {
        try {
            // The official asynchronous API still requires its entry call on
            // Android's main thread. Only resource verification runs off-thread.
            CastContext.getSharedInstance(context,initialization)
                    .addOnSuccessListener(value->ui.post(()->{
                        sdk=value;initializing=false;initialized=true;
                        sdk.getSessionManager().addSessionManagerListener(this,CastSession.class);
                        router=MediaRouter.getInstance(context);
                        selector=new MediaRouteSelector.Builder().addControlCategory(
                            CastMediaControlIntent.categoryForCast(CastMediaControlIntent.DEFAULT_MEDIA_RECEIVER_APPLICATION_ID)).build();
                        session=sdk.getSessionManager().getCurrentCastSession();
                        if(view.get()!=null)discover();capture();
                    }))
                    .addOnFailureListener(error->ui.post(()->unavailable("Cast is unavailable on this device. Phone playback is unchanged.")));
        } catch(Exception | LinkageError error) {unavailable("The Cast component could not initialize. Phone playback is unchanged.");}
    }
    private void unavailable(String reason){initializing=false;message=reason;changed();}
    private void discover() {
        if(router==null || selector==null || discovering)return;
        discovering=true;router.addCallback(selector,routes,MediaRouter.CALLBACK_FLAG_REQUEST_DISCOVERY);updateDevices();
    }
    private void stopDiscovery(){if(router!=null && discovering)router.removeCallback(routes);discovering=false;}
    private void updateDevices() {
        devices.clear();
        if(router!=null)for(MediaRouter.RouteInfo route:router.getRoutes())
            if(route.isEnabled() && !route.isDefault() && route.matchesSelector(selector))devices.add(route);
        changed();
    }
    private void capture() {
        token=UUID.randomUUID().toString().replace("-","");
        final String expected=token;
        phone.request("capture",token,0,value->{
            if(!expected.equals(token))return;
            if(!ok(value)){unavailable("No supported active video is available. Phone playback is unchanged.");return;}
            source=value;privateSource=InfinityCastSource.parse(value.optString("file"));mime=null;
            if(privateSource==null || !value.optBoolean("can_pause") || !value.optBoolean("can_seek")) {
                privateSource=null;message="This stream uses unsupported transport or adaptive media handling. Phone playback is unchanged.";
            } else message="Choose a Cast device.";
            changed();
        });
    }
    boolean connected(){return session!=null && session.isConnected();}
    boolean casting(){return handedOff && connected();}
    boolean hasRetainedPhone(){return handedOff || mayHavePaused;}
    boolean playing(){return remote!=null && ownsMedia() && remote.getPlayerState()==MediaStatus.PLAYER_STATE_PLAYING;}
    boolean seekable(){return remote!=null && ownsMedia() && remote.getMediaStatus()!=null &&
        remote.getMediaStatus().isMediaCommandSupported(MediaStatus.COMMAND_SEEK);}
    String title(){return source==null?"Infinity Cast":source.optString("title","Infinity Cast");}
    long position(){return lastPosition;}
    long duration(){return lastDuration;}
    void choose(int index) {
        if(transferStarted || handedOff || index<0 || index>=devices.size() || privateSource==null || phone.busy() || source==null)return;
        aborting=returning=false;selecting=true;message="Connecting to "+devices.get(index).getName()+"…";changed();
        final long generation=++epoch;
        devices.get(index).select();
        if(connected())connectedSession(session);
        ui.postDelayed(()->{
            if(generation==epoch && !handedOff && !aborting){message="The receiver did not become ready. Phone playback is unchanged.";abortTransfer();}
        },20000);
    }
    private boolean ok(JSONObject value){return value!=null && "ok".equals(value.optString("status"));}
    private void connectedSession(CastSession value) {
        if(!selecting || transferStarted || aborting || source==null || privateSource==null)return;
        transferStarted=true;phoneClockReady=false;
        session=value;remote=value.getRemoteMediaClient();
        CastDevice device=value.getCastDevice();
        if(remote==null || device==null || !device.hasCapability(CastDevice.CAPABILITY_VIDEO_OUT) ||
            device.getInetAddress()==null || device.getInetAddress().isLoopbackAddress()) {
            unavailable("This receiver has no supported local video transport. Phone playback is unchanged.");abortTransfer();return;
        }
        remote.registerCallback(mediaEvents);
        final String expected=token;
        phone.request("snapshot",token,0,current->{
            if(!expected.equals(token) || session!=value)return;
            if(!ok(current)){abortTransfer();return;}
            source=current;privateSource=InfinityCastSource.parse(current.optString("file"));
            if(aborting || privateSource==null){abortTransfer();return;}
            phoneWasPaused=current.optBoolean("paused");mayHavePaused=false;
            try {
                if(channel!=null)channel.close();
                channel=new InfinityCastChannel(token,current.getString("file_sha256"),current.getString("origin_sha256"));
                publish();InfinityCastRpc.channel(channel.name,false);
                message="Checking supported media; phone playback continues.";changed();
                relay=InfinityCastRelay.start(device.getInetAddress(),privateSource,(owner,type,failure)->ui.post(()->{
                    if(!expected.equals(token) || session!=value || !transferStarted || aborting) {owner.close();return;}
                    if(failure!=null || type==null || owner.closed()){message="This stream cannot be relayed with the supported media transport. Phone playback continues.";abortTransfer();return;}
                    relay=owner;mime=type;loadReceiver(expected,value,owner);
                }));
                if(!ticking){ticking=true;tick();}
            } catch(Exception | LinkageError unavailable){message="The Cast media transport could not start. Phone playback is unchanged.";abortTransfer();}
        });
    }
    private void loadReceiver(String expected,CastSession value,InfinityCastRelay owner) {
        if(!expected.equals(token) || session!=value || owner!=relay || owner.closed() || aborting)return;
        try {
            mediaToken=UUID.randomUUID().toString().replace("-","");
            MediaMetadata metadata=new MediaMetadata("episode".equals(source.optString("kind"))?
                MediaMetadata.MEDIA_TYPE_TV_SHOW:"movie".equals(source.optString("kind"))?
                MediaMetadata.MEDIA_TYPE_MOVIE:MediaMetadata.MEDIA_TYPE_GENERIC);
            metadata.putString(MediaMetadata.KEY_TITLE,InfinityCastSource.receiverTitle(title()));
            if("episode".equals(source.optString("kind"))) {
                if(source.optInt("season",-1)>=0)metadata.putInt(MediaMetadata.KEY_SEASON_NUMBER,source.optInt("season"));
                if(source.optInt("episode",-1)>=0)metadata.putInt(MediaMetadata.KEY_EPISODE_NUMBER,source.optInt("episode"));
            }
            // The receiver receives only our temporary, peer-bound endpoint.
            // Original provider URL/query/headers remain private on this phone.
            MediaInfo.Builder info=new MediaInfo.Builder(owner.address()).setContentType(mime)
                .setStreamType(MediaInfo.STREAM_TYPE_BUFFERED).setMetadata(metadata)
                .setCustomData(new JSONObject().put("infinity_transaction",mediaToken));
            if(source.optLong("duration_ms")>0)info.setStreamDuration(source.optLong("duration_ms"));
            message="Preparing the receiver; phone playback continues.";changed();
            final String expectedMedia=mediaToken;
            remote.load(new MediaLoadRequestData.Builder().setMediaInfo(info.build()).setAutoplay(false)
                .setCurrentTime(source.optLong("position_ms")).build()).setResultCallback(result->{
                    if(!expected.equals(token) || !expectedMedia.equals(mediaToken) || aborting)return;
                    if(!result.getStatus().isSuccess()){message="The receiver could not load this media. Phone playback is unchanged.";abortTransfer();}
                    else waitForReady(SystemClock.uptimeMillis()+8000,expected);
                });
        } catch(Exception unavailable){message="The receiver handoff could not be prepared. Phone playback is unchanged.";abortTransfer();}
    }
    private void waitForReady(long deadline,String expected) {
        if(!expected.equals(token) || aborting || returning || handedOff)return;
        if(!connected() || !ownsMedia()){if(SystemClock.uptimeMillis()>deadline){abortTransfer();return;}}
        else if(remote.getPlayerState()==MediaStatus.PLAYER_STATE_PAUSED && channel!=null && channel.acknowledged()) {
            pausePhone();return;
        }
        if(SystemClock.uptimeMillis()>deadline){message="The playback observer or receiver is not ready. Phone playback is unchanged.";abortTransfer();return;}
        ui.postDelayed(()->waitForReady(deadline,expected),100);
    }
    private void pausePhone() {
        final String expected=token;
        phone.request("snapshot",token,0,value->{
            if(!expected.equals(token))return;
            if(!ok(value) || aborting){abortTransfer();return;}
            source=value;phoneWasPaused=value.optBoolean("paused");
            commitPause(expected);
        });
    }
    private void commitPause(String expected) {
        if(!expected.equals(token) || aborting)return;
        mayHavePaused=true;
        message="Transferring playback…";changed();
        phone.request("pause",token,0,new InfinityCastGateway.Result(){
            @Override public void done(JSONObject value) {
                if(!expected.equals(token))return;
                if(!ok(value)){aborting=true;restorePhone(false);return;}
                source=value;
                if(aborting){restorePhone(false);return;}
                confirmPaused(SystemClock.uptimeMillis()+2500,expected);
            }
            @Override public void pendingCommit(){if(expected.equals(token)){message="Phone handoff is pending; the receiver remains paused.";aborting=true;changed();}}
        });
    }
    private void confirmPaused(long deadline,String expected) {
        if(!expected.equals(token))return;
        if(SystemClock.uptimeMillis()>deadline){aborting=true;restorePhone(false);return;}
        if(phone.busy()){ui.postDelayed(()->confirmPaused(deadline,expected),50);return;}
        phone.request("snapshot",token,0,value->{
            if(!expected.equals(token))return;
            if(!ok(value) || SystemClock.uptimeMillis()>deadline){aborting=true;restorePhone(false);return;}
            if(!value.optBoolean("paused")){ui.postDelayed(()->confirmPaused(deadline,expected),50);return;}
            source=value;
            if(aborting){restorePhone(false);return;}
            final String expectedMedia=mediaToken;
            final RemoteMediaClient receiver=remote;
            if(receiver==null || !ownsMedia()){aborting=true;restorePhone(false);return;}
            receiver.seek(new MediaSeekOptions.Builder().setPosition(value.optLong("position_ms")).build()).setResultCallback(result->{
                if(!expected.equals(token) || !expectedMedia.equals(mediaToken) || aborting)return;
                if(!result.getStatus().isSuccess()){aborting=true;restorePhone(false);return;}
                handedOff=true;receiver.play().setResultCallback(play->{
                    if(!expected.equals(token) || !expectedMedia.equals(mediaToken) || returning)return;
                    if(!play.getStatus().isSuccess()){aborting=true;restorePhone(false);}
                });
                ui.postDelayed(()->{
                    if(expected.equals(token) && expectedMedia.equals(mediaToken) && handedOff && !everPlayed && !returning){
                        message="Receiver playback did not start. Returning to the existing phone player.";
                        aborting=true;restorePhone(false);
                    }
                },8000);
                message="Connected";publish();changed();
            });
        });
    }
    private boolean ownsMedia() {
        if(remote==null || remote.getMediaInfo()==null)return false;
        JSONObject data=remote.getMediaInfo().getCustomData();
        return data!=null && mediaToken.equals(data.optString("infinity_transaction"));
    }
    private void status() {
        if(remote==null)return;
        if(ownsMedia()) {
            MediaStatus status=remote.getMediaStatus();
            if(status!=null) {
                if(status.getPlayerState()==MediaStatus.PLAYER_STATE_PLAYING)everPlayed=true;
                long p=remote.getApproximateStreamPosition(),d=remote.getStreamDuration();
                if(d>0 && d<30L*24*3600*1000)lastDuration=d;
                if(p>=0 && p<30L*24*3600*1000)lastPosition=p;
                finished=everPlayed && status.getPlayerState()==MediaStatus.PLAYER_STATE_IDLE &&
                    status.getIdleReason()==MediaStatus.IDLE_REASON_FINISHED;
                if(finished && lastDuration>0)lastPosition=lastDuration;
                if(!returning && status.getPlayerState()==MediaStatus.PLAYER_STATE_IDLE && status.getIdleReason()==MediaStatus.IDLE_REASON_ERROR) {
                    message="Receiver playback failed. Returning to the existing phone player.";aborting=true;restorePhone(false);
                }
            }
        } else if(handedOff)message="The receiver is playing different content. Return to phone playback.";
        publish();changed();
    }
    private void publish() {
        if(channel==null || source==null)return;
        try {
            channel.publish(new JSONObject().put("schema",1).put("controller","InfinityCastV1")
                .put("pid",Process.myPid()).put("session",token).put("at_ms",SystemClock.uptimeMillis())
                .put("file_sha256",source.getString("file_sha256")).put("origin_sha256",source.getString("origin_sha256"))
                .put("connected",connected()).put("owned",handedOff)
                .put("media_matches",ownsMedia())
                .put("ever_played",everPlayed).put("completed",finished)
                .put("position",lastPosition/1000.0).put("duration",lastDuration/1000.0));
        } catch(Exception ignored) {}
    }
    private void tick() {
        if(channel==null){ticking=false;return;}
        status();
        if((handedOff || transferStarted) && !returning && !aborting && !phone.busy() && SystemClock.uptimeMillis()>nextNativePoll) {
            nextNativePoll=SystemClock.uptimeMillis()+1500;
            phone.request("snapshot",token,0,value->{
                if(aborting && !mayHavePaused && !handedOff){leaveReceiver(ownsMedia());return;}
                if(!ok(value)){message="Phone playback changed or is closing; Cast ownership was released.";leaveReceiver(true);}
                else if(!value.optBoolean("paused") && handedOff && !returning){
                    message="Phone playback resumed; the Cast session was released.";phoneClockReady=true;leaveReceiver(true);
                }
            });
        }
        ui.postDelayed(this::tick,500);
    }
    void toggle() {
        if(!casting() || !ownsMedia())return;
        if(playing())remote.pause();else if(!finished)remote.play();
    }
    void seek(long value) {
        if(!casting() || !seekable() || value<0 || value>lastDuration)return;
        remote.seek(new MediaSeekOptions.Builder().setPosition(value).build());
    }
    void returnToPhone(){
        if(returning)return;
        if(!handedOff && !mayHavePaused){abortTransfer();return;}
        returnDeadline=0;returning=true;++returnEpoch;restorePhone(handedOff);
    }
    private void restorePhone(boolean useRemotePosition) {restorePhone(useRemotePosition,token);}
    private void restorePhone(boolean useRemotePosition,String expected) {
        if(!expected.equals(token) || restoreInFlight)return;
        if(!returning){returning=true;++returnEpoch;}
        if(source==null){leaveReceiver(false);return;}
        if(returnDeadline==0)returnDeadline=SystemClock.uptimeMillis()+8000;
        if(SystemClock.uptimeMillis()>returnDeadline){
            message="Phone return has not completed; receiver state was retained. You can retry Return to Phone.";
            returning=false;returnDeadline=0;changed();return;
        }
        if(phone.busy()){ui.postDelayed(()->restorePhone(useRemotePosition,expected),100);return;}
        final boolean pauseAfter=useRemotePosition?(!playing() || finished):phoneWasPaused;
        if(remote!=null && ownsMedia())remote.pause();
        message="Returning to the existing phone player…";changed();
        long position=useRemotePosition?Math.max(0,lastPosition):source.optLong("position_ms");
        long duration=source.optLong("duration_ms");
        if(duration>0)position=Math.min(position,Math.max(0,duration-1));
        final long target=position;
        final long returningOperation=returnEpoch;
        restoreInFlight=true;
        phone.request("seek",token,target,value->{
            if(!expected.equals(token) || returningOperation!=returnEpoch)return;
            if(!ok(value)){message="The original phone item is no longer available; no other playback was changed.";leaveReceiver(false);return;}
            phone.request(pauseAfter?"pause":"resume",token,0,resumed->{
                if(!expected.equals(token) || returningOperation!=returnEpoch)return;
                if(ok(resumed)){confirmReturn(target,pauseAfter,expected,returningOperation);}
                else {message="Phone playback has not resumed. Receiver state was retained.";restoreInFlight=false;returning=false;changed();}
            });
        });
    }
    private void confirmReturn(long position,boolean paused,String expected,long returningOperation) {
        if(!expected.equals(token) || returningOperation!=returnEpoch)return;
        if(SystemClock.uptimeMillis()>returnDeadline){
            message="Phone return is not confirmed. Receiver state was retained.";restoreInFlight=false;returning=false;returnDeadline=0;changed();return;
        }
        if(phone.busy()){ui.postDelayed(()->confirmReturn(position,paused,expected,returningOperation),100);return;}
        phone.request("snapshot",token,0,value->{
            if(!expected.equals(token) || returningOperation!=returnEpoch)return;
            if(!ok(value)){message="The original phone item changed; no other playback was controlled.";leaveReceiver(true);return;}
            long distance=Math.abs(value.optLong("position_ms")-position);
            if(value.optBoolean("paused")==paused && distance<2500){
                mayHavePaused=false;phoneClockReady=true;leaveReceiver(true);message="Returned to phone playback.";changed();
            } else ui.postDelayed(()->confirmReturn(position,paused,expected,returningOperation),100);
        });
    }
    private void abortTransfer() {
        aborting=true;++epoch;
        if(handedOff || mayHavePaused){restorePhone(handedOff);return;}
        if(!phone.busy())leaveReceiver(ownsMedia());
        else phone.cancel();
        changed();
    }
    private void leaveReceiver(boolean stopOwnedMedia) {
        if(leaving)return;leaving=true;
        boolean own=ownsMedia();
        boolean releaseClock=!handedOff || phoneClockReady;
        if(remote!=null)remote.unregisterCallback(mediaEvents);
        boolean end=session!=null;
        handedOff=false;everPlayed=false;finished=false;returning=false;transferStarted=false;selecting=false;
        returnDeadline=0;mayHavePaused=false;restoreInFlight=false;
        if(channel!=null) {
            if(releaseClock)InfinityCastRpc.channel(channel.name,true);
            channel.close();channel=null;
        }
        if(relay!=null){relay.close();relay=null;}
        remote=null;session=null;phoneClockReady=false;
        if(sdk!=null && end)sdk.getSessionManager().endCurrentSession(stopOwnedMedia && own);
        if(!phone.busy() && !token.isEmpty())phone.request("release",token,0,value->{
            if(ok(value) && view.get()!=null && !phone.busy() && !handedOff && !transferStarted)capture();
        });
        leaving=false;
        changed();
    }
    @Override public void onSessionStarted(CastSession s,String id){connectedSession(s);}
    @Override public void onSessionResumed(CastSession s,boolean suspended){if(!handedOff)connectedSession(s);}
    @Override public void onSessionStartFailed(CastSession s,int error){if(session!=null && s!=session)return;unavailable("Cast connection failed. Phone playback is unchanged.");abortTransfer();}
    @Override public void onSessionResumeFailed(CastSession s,int error){onSessionStartFailed(s,error);}
    @Override public void onSessionEnded(CastSession s,int error){if(leaving || s!=session)return;if(relay!=null){relay.close();relay=null;}if(handedOff){message="Cast disconnected. Return to phone playback.";returning=false;}else if(transferStarted)abortTransfer();else session=null;changed();}
    @Override public void onSessionSuspended(CastSession s,int reason){message="Cast connection interrupted. Return to phone playback.";changed();}
    @Override public void onSessionStarting(CastSession s){if(!handedOff)session=s;}
    @Override public void onSessionResuming(CastSession s,String id){}
    @Override public void onSessionEnding(CastSession s){}
}
