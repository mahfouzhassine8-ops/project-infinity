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
    private boolean initializing,initialized,discovering,initializationAttempted,listening;
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
    private String receiverName="",selectedDeviceId="";
    private boolean cleanupPending;
    private final Runnable ticker=this::tick;
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
        else if(initialized){listen();discover();if(!cleanupPending && !returning && !selecting && !transferStarted && !handedOff && !phone.busy())capture();}
        changed();
    }
    void detach(View value) {
        if(view.get()==value)view.clear();
        stopDiscovery();
        // Close Controls dismisses presentation only; transfer/session owns its bounded cleanup.
        if(!selecting && !transferStarted && !handedOff && !cleanupPending && !token.isEmpty())leaveReceiver(false);
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
                        listen();
                        router=MediaRouter.getInstance(context);
                        selector=new MediaRouteSelector.Builder().addControlCategory(
                            CastMediaControlIntent.categoryForCast(CastMediaControlIntent.DEFAULT_MEDIA_RECEIVER_APPLICATION_ID)).build();
                        if(view.get()!=null){discover();capture();}
                    }))
                    .addOnFailureListener(error->ui.post(()->unavailable("Cast is unavailable on this device. Phone playback is unchanged.")));
        } catch(Exception | LinkageError error) {unavailable("The Cast component could not initialize. Phone playback is unchanged.");}
    }
    private void unavailable(String reason){initializing=false;if(!initialized)initializationAttempted=false;message=reason;changed();}
    private void listen(){if(sdk!=null && !listening){sdk.getSessionManager().addSessionManagerListener(this,CastSession.class);listening=true;}}
    private void unlisten(){if(sdk!=null && listening){sdk.getSessionManager().removeSessionManagerListener(this,CastSession.class);listening=false;}}
    private void discover() {
        if(router==null || selector==null || discovering)return;
        discovering=true;router.addCallback(selector,routes,MediaRouter.CALLBACK_FLAG_REQUEST_DISCOVERY);updateDevices();
    }
    private void stopDiscovery(){if(router!=null && discovering)router.removeCallback(routes);discovering=false;}
    private void updateDevices() {
        devices.clear();
        if(router!=null)for(MediaRouter.RouteInfo route:router.getRoutes())
            if(route.isEnabled() && !route.isDefault() && route.matchesSelector(selector)) {
                CastDevice device=CastDevice.getFromBundle(route.getExtras());
                if(device!=null && device.hasCapability(CastDevice.CAPABILITY_VIDEO_OUT))devices.add(route);
            }
        changed();
    }
    private void capture() {
        token=UUID.randomUUID().toString().replace("-","");
        final String expected=token;
        phone.request("capture",token,0,value->{
            if(!expected.equals(token))return;
            if(!ok(value)){unavailable("No supported active video is available. Phone playback is unchanged.");return;}
            source=value;privateSource=readSource(value);mime=null;
            if(privateSource==null || !value.optBoolean("can_pause") || !value.optBoolean("can_seek")) {
                privateSource=null;message=value.optBoolean("cast_drm")?"This source requires DRM; Cast cannot transfer it. Phone playback continues.":"This source does not expose a supported seekable HTTP video transport. Phone playback is unchanged.";
            } else message="Choose a Cast device.";
            changed();
        });
    }
    boolean connected(){return session!=null && session.isConnected();}
    boolean casting(){return handedOff && everPlayed && connected();}
    boolean transferring(){return selecting || transferStarted || returning || cleanupPending;}
    boolean canDisconnect(){return transferring() || connected() || hasRetainedPhone();}
    String receiverName(){return receiverName;}
    boolean hasRetainedPhone(){return handedOff || mayHavePaused;}
    boolean playing(){return remote!=null && ownsMedia() && remote.getPlayerState()==MediaStatus.PLAYER_STATE_PLAYING;}
    boolean seekable(){return remote!=null && ownsMedia() && remote.getMediaStatus()!=null &&
        remote.getMediaStatus().isMediaCommandSupported(MediaStatus.COMMAND_SEEK);}
    String title(){return source==null?"Infinity Cast":source.optString("title","Infinity Cast");}
    long position(){return lastPosition;}
    long duration(){return lastDuration;}
    void choose(int index) {
        if(cleanupPending || selecting || transferStarted || handedOff || index<0 || index>=devices.size() || phone.busy())return;
        if(privateSource==null || source==null){final String routeId=devices.get(index).getId();captureThenChoose(routeId);return;}
        aborting=returning=false;selecting=true;everPlayed=finished=false;receiverName=devices.get(index).getName();
        message="Connecting to "+receiverName+"…";InfinityCastDiagnostics.event("session","connecting",0);changed();
        CastDevice chosen=CastDevice.getFromBundle(devices.get(index).getExtras());
        if(chosen==null || !chosen.hasCapability(CastDevice.CAPABILITY_VIDEO_OUT)){selecting=false;message="That receiver does not support video.";changed();return;}
        selectedDeviceId=chosen.getDeviceId();
        final long generation=++epoch;devices.get(index).select();
        CastSession existing=sdk==null?null:sdk.getSessionManager().getCurrentCastSession();
        if(existing!=null && existing.isConnected() && existing.getCastDevice()!=null && selectedDeviceId.equals(existing.getCastDevice().getDeviceId()))connectedSession(existing);
        ui.postDelayed(()->{
            if(generation==epoch && !handedOff && !aborting){message="The receiver did not become ready. Phone playback is unchanged.";abortTransfer();}
        },20000);
    }
    private InfinityCastSource readSource(JSONObject value) {
        if(!value.optBoolean("cast_headers_supported",true))return null;
        return InfinityCastSource.parse(value.optString("file"),value.optString("cast_manifest_headers"),
            value.optString("cast_stream_headers"),value.optBoolean("cast_drm"));
    }
    private void captureThenChoose(String routeId) {
        token=UUID.randomUUID().toString().replace("-","");final String expected=token;
        phone.request("capture",token,0,value->{
            if(!expected.equals(token) || cleanupPending)return;
            if(!ok(value)){message="No supported active video is available. Phone playback is unchanged.";changed();return;}
            source=value;privateSource=readSource(value);
            if(privateSource==null || !value.optBoolean("can_pause") || !value.optBoolean("can_seek")){privateSource=null;message=value.optBoolean("cast_drm")?"This source requires DRM; Cast cannot transfer it. Phone playback continues.":"Unsupported current video transport. Phone playback is unchanged.";changed();return;}
            for(int i=0;i<devices.size();i++)if(routeId.equals(devices.get(i).getId())){choose(i);return;}
            message="That receiver is no longer available.";changed();
        });
    }
    private boolean ok(JSONObject value){return value!=null && "ok".equals(value.optString("status"));}
    private void connectedSession(CastSession value) {
        if(!selecting || transferStarted || aborting || source==null || privateSource==null)return;
        if(value==null || value.getCastDevice()==null || !selectedDeviceId.equals(value.getCastDevice().getDeviceId()))return;
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
            source=current;privateSource=readSource(current);
            if(aborting || privateSource==null){abortTransfer();return;}
            phoneWasPaused=current.optBoolean("paused");mayHavePaused=false;
            try {
                if(channel!=null)channel.close();
                channel=new InfinityCastChannel(token,current.getString("file_sha256"),current.getString("origin_sha256"));
                publish();phone.request("channel",token,0,registered->{if(!ok(registered))InfinityCastDiagnostics.event("observer","registration_unavailable",0);});
                message="Checking supported media; phone playback continues.";changed();
                relay=InfinityCastRelay.start(device.getInetAddress(),privateSource,(owner,type,failure)->ui.post(()->{
                    if(!expected.equals(token) || session!=value || !transferStarted || aborting) {owner.close();return;}
                    if(failure!=null || type==null || owner.closed()){message=mediaFailure(failure);abortTransfer();return;}
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
            if(owner.hlsVideoFormat()!=null)info.setHlsVideoSegmentFormat(owner.hlsVideoFormat());
            if(owner.hlsAudioFormat()!=null)info.setHlsSegmentFormat(owner.hlsAudioFormat());
            message="Preparing the receiver; phone playback continues.";changed();
            final String expectedMedia=mediaToken;
            remote.load(new MediaLoadRequestData.Builder().setMediaInfo(info.build()).setAutoplay(false)
                .setCurrentTime(source.optLong("position_ms")).build()).setResultCallback(result->{
                    if(!expected.equals(token) || !expectedMedia.equals(mediaToken) || aborting)return;
                    if(!result.getStatus().isSuccess()){InfinityCastDiagnostics.event("media_load","rejected",result.getStatus().getStatusCode());message="The TV rejected the media load (code "+result.getStatus().getStatusCode()+"). Phone playback continues.";abortTransfer();}
                    else waitForReady(SystemClock.uptimeMillis()+20000,expected);
                });
        } catch(Exception unavailable){message="The receiver handoff could not be prepared. Phone playback is unchanged.";abortTransfer();}
    }
    private void waitForReady(long deadline,String expected) {
        if(!expected.equals(token) || aborting || returning || handedOff)return;
        if(!connected() || !ownsMedia()){if(SystemClock.uptimeMillis()>deadline){abortTransfer();return;}}
        else if(remote.getPlayerState()==MediaStatus.PLAYER_STATE_PAUSED && !phone.busy()) {
            pausePhone();return;
        }
        if(SystemClock.uptimeMillis()>deadline){message="The TV did not finish preparing this movie. Phone playback is unchanged.";abortTransfer();return;}
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
                message="Starting movie on the TV…";publish();changed();
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
                if(status.getPlayerState()==MediaStatus.PLAYER_STATE_PLAYING && handedOff) {
                    if(!everPlayed)InfinityCastDiagnostics.event("receiver","playing_confirmed",0);
                    everPlayed=true;if(!returning)message="Now Casting";
                }
                long p=remote.getApproximateStreamPosition(),d=remote.getStreamDuration();
                if(d>0 && d<30L*24*3600*1000)lastDuration=d;
                if(p>=0 && p<30L*24*3600*1000)lastPosition=p;
                finished=everPlayed && status.getPlayerState()==MediaStatus.PLAYER_STATE_IDLE &&
                    status.getIdleReason()==MediaStatus.IDLE_REASON_FINISHED;
                if(finished && lastDuration>0)lastPosition=lastDuration;
                if(!returning && status.getPlayerState()==MediaStatus.PLAYER_STATE_IDLE && status.getIdleReason()==MediaStatus.IDLE_REASON_ERROR) {
                    InfinityCastDiagnostics.event("receiver","media_idle_error",status.getIdleReason());
                    message=relay!=null && !relay.failure().isEmpty()?mediaFailure(relay.failure()):"TV playback failed. Returning to phone playback.";aborting=true;restorePhone(false);
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
                .put("connected",connected()).put("owned",handedOff && channel.acknowledged())
                .put("media_matches",ownsMedia())
                .put("ever_played",everPlayed).put("completed",finished)
                .put("position",lastPosition/1000.0).put("duration",lastDuration/1000.0));
        } catch(Exception ignored) {}
    }
    private void tick() {
        if(channel==null || cleanupPending){ticking=false;return;}
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
        if(channel!=null && !cleanupPending)ui.postDelayed(ticker,500);else ticking=false;
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
            message="Phone return could not be confirmed. Cast was disconnected; the existing phone player remains available.";
            leaveReceiver(true);return;
        }
        if(phone.busy()){ui.postDelayed(()->restorePhone(useRemotePosition,expected),100);return;}
        final boolean pauseAfter=useRemotePosition?finished:phoneWasPaused;
        if(connected() && remote!=null && ownsMedia())try{remote.pause();}catch(RuntimeException ignored){}
        message="Returning to the existing phone player…";changed();
        long position=useRemotePosition?Math.max(0,lastPosition):source.optLong("position_ms");
        long duration=source.optLong("duration_ms");
        if(duration>0)position=Math.min(position,Math.max(0,duration-1));
        final long target=position;
        final long returningOperation=returnEpoch;
        restoreInFlight=true;
        phone.request("seek",token,target,value->{
            if(!expected.equals(token) || returningOperation!=returnEpoch)return;
            if(!ok(value)){message="The original phone item is no longer available; no other playback was changed.";phoneClockReady=true;leaveReceiver(true);return;}
            phone.request(pauseAfter?"pause":"resume",token,0,resumed->{
                if(!expected.equals(token) || returningOperation!=returnEpoch)return;
                if(ok(resumed)){confirmReturn(target,pauseAfter,expected,returningOperation);}
                else {message="The phone could not resume automatically. Cast was disconnected; use the existing phone controls.";restoreInFlight=false;leaveReceiver(true);}
            });
        });
    }
    private void confirmReturn(long position,boolean paused,String expected,long returningOperation) {
        if(!expected.equals(token) || returningOperation!=returnEpoch)return;
        if(SystemClock.uptimeMillis()>returnDeadline){
            message="Phone playback is not confirmed. Cast was disconnected; use the existing phone controls.";restoreInFlight=false;leaveReceiver(true);return;
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
    private String mediaFailure(String reason) {
        if(reason==null)return "Media preparation failed. Phone playback continues.";
        if(reason.equals("drm_or_unsupported_encryption"))return "This source uses DRM or unsupported encryption; Cast cannot transfer it. Phone playback continues.";
        if(reason.startsWith("source_http_"))return "The media source refused Cast delivery (HTTP "+reason.substring(12)+"). Phone playback continues.";
        if(reason.startsWith("unsupported_") || reason.startsWith("invalid_"))return "This source uses an unsupported media or manifest feature. Phone playback continues.";
        return "The media relay could not reach or prepare this source. Phone playback continues.";
    }
    private void abortTransfer() {
        if(cleanupPending)return;
        aborting=true;++epoch;
        if(handedOff || mayHavePaused){restorePhone(everPlayed);return;}
        // Cancellation waits for an already committed native outcome. It never
        // abandons a late pause/seek or issues commands against another item.
        if(phone.busy())phone.cancel();
        leaveReceiver(ownsMedia());
    }
    private void leaveReceiver(boolean stopOwnedMedia) {
        if(cleanupPending)return;cleanupPending=true;leaving=true;++epoch;
        final String expected=token;boolean own=ownsMedia();
        boolean ownedSession=selecting || transferStarted || handedOff;
        if(remote!=null){try{remote.unregisterCallback(mediaEvents);if(stopOwnedMedia && own && connected())remote.stop();}catch(RuntimeException ignored){}}
        if(relay!=null){relay.close();relay=null;}
        ui.removeCallbacksAndMessages(null);ticking=false;
        // Explicitly release the RAM-only recorder channel on every exit. The
        // ordinary recorder keeps its last real sample; no records are forged.
        if(channel!=null){channel.close();channel=null;}
        if(sdk!=null && session!=null && ownedSession)try{sdk.getSessionManager().endCurrentSession(false);}catch(RuntimeException ignored){}
        remote=null;session=null;stopDiscovery();unlisten();
        phone.afterIdle(()->releaseNative(expected));
        changed();
    }
    private void releaseNative(String expected) {
        if(!cleanupPending || !expected.equals(token))return;
        if(mayHavePaused && !phoneClockReady) {
            // A late committed pause must be reconciled before dropping token
            // ownership. Native item binding protects all other playback.
            phone.request(!everPlayed && phoneWasPaused?"pause":"resume",expected,0,result->{
                phoneClockReady=true;releaseNative(expected);
            });return;
        }
        phone.request("release",expected,0,result->{
            InfinityCastDiagnostics.event("cleanup",ok(result)?"native_released":"native_release_refused",0);
            handedOff=everPlayed=finished=returning=transferStarted=selecting=false;
            returnDeadline=0;mayHavePaused=restoreInFlight=false;phoneClockReady=false;
            cleanupPending=leaving=aborting=false;privateSource=null;token="";mediaToken="";
            InfinityCastDiagnostics.event("cleanup","session_released",0);
            if(view.get()!=null){listen();discover();}changed();
        });
    }
    @Override public void onSessionStarted(CastSession s,String id){connectedSession(s);}
    @Override public void onSessionResumed(CastSession s,boolean suspended){if(!handedOff)connectedSession(s);}
    @Override public void onSessionStartFailed(CastSession s,int error){if(session!=null && s!=session)return;unavailable("Cast connection failed. Phone playback is unchanged.");abortTransfer();}
    @Override public void onSessionResumeFailed(CastSession s,int error){onSessionStartFailed(s,error);}
    @Override public void onSessionEnded(CastSession s,int error){
        if(leaving || s!=session)return;InfinityCastDiagnostics.event("session","ended",error);
        if(relay!=null){relay.close();relay=null;}
        if(handedOff || mayHavePaused){message="TV disconnected. Returning to phone playback…";returning=false;restorePhone(everPlayed);}
        else abortTransfer();
    }
    @Override public void onSessionSuspended(CastSession s,int reason){if(s!=session || cleanupPending)return;InfinityCastDiagnostics.event("session","suspended",reason);message="TV connection interrupted. Returning to phone playback…";abortTransfer();}
    @Override public void onSessionStarting(CastSession s){if(!handedOff)session=s;}
    @Override public void onSessionResuming(CastSession s,String id){}
    @Override public void onSessionEnding(CastSession s){}
}
