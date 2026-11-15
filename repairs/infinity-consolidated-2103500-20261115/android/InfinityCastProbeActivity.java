package com.projectinfinity.kodi;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import org.json.JSONObject;

/** Separate CI package, real pinned SDK. No receiver, media or Kodi shutdown. */
public final class InfinityCastProbeActivity extends Activity implements InfinityCastSession.View {
    private static final java.util.concurrent.atomic.AtomicBoolean admitted=new java.util.concurrent.atomic.AtomicBoolean();
    private final Handler ui=new Handler(Looper.getMainLooper());
    private InfinityCastSession cast;
    private long deadline;
    private int pulses,checks;
    private boolean finished;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        // SDK resource attachment may recreate the disposable Activity. Keep
        // one process-owned check and never launch a second native capture.
        if(!admitted.compareAndSet(false,true))return;
        deadline=SystemClock.uptimeMillis()+30000;
        cast=InfinityCastSession.get(this);
        cast.attach(this);
        pulse();
    }
    private Object field(String name) throws Exception {
        java.lang.reflect.Field f=InfinityCastSession.class.getDeclaredField(name);
        f.setAccessible(true);return f.get(cast);
    }
    private void field(String name,boolean value) throws Exception {
        java.lang.reflect.Field f=InfinityCastSession.class.getDeclaredField(name);
        f.setAccessible(true);f.setBoolean(cast,value);
    }
    private void require(boolean value,String message) {
        if(!value)throw new IllegalStateException(message);
        checks++;
    }
    private long[] sdkCallback() throws Exception {
        // Inspect the actual private pinned SDK record by callback identity,
        // not obfuscated class/field names or the application's boolean alone.
        // MediaRouter1.3.0 CallbackRecord has one int flags and one long time.
        Object router=field("router"),callback=field("routes");
        long[] found=null;
        for(java.lang.reflect.Field listField:router.getClass().getDeclaredFields()) {
            if(java.lang.reflect.Modifier.isStatic(listField.getModifiers()) ||
                    !java.util.List.class.isAssignableFrom(listField.getType()))continue;
            listField.setAccessible(true);Object records=listField.get(router);
            if(records==null)continue;
            for(Object record:(java.util.List<?>)records) {
                if(record==null)continue;
                boolean ours=false;Long flags=null,time=null;int ints=0,longs=0;
                for(java.lang.reflect.Field f:record.getClass().getDeclaredFields()) {
                    if(java.lang.reflect.Modifier.isStatic(f.getModifiers()))continue;
                    f.setAccessible(true);
                    if(f.getType()==int.class){flags=(long)f.getInt(record);ints++;}
                    else if(f.getType()==long.class){time=f.getLong(record);longs++;}
                    else if(f.get(record)==callback)ours=true;
                }
                if(ours) {
                    if(found!=null || ints!=1 || longs!=1)throw new IllegalStateException("ambiguous pinned SDK record");
                    found=new long[]{flags,time};
                }
            }
        }
        return found;
    }
    private void pulse() {
        if(finished)return;
        pulses++;
        try {
            if((Boolean)field("initialized") && pulses>=10 && !cast.phone.busy()) {
                require((Boolean)field("discovering"),"visible picker not registered");
                long[] active=sdkCallback();
                // PERFORM_ACTIVE_SCAN is1 in the hash-pinned1.3.0 SDK.
                require(active!=null && (active[0]&1)!=0,"actual SDK request is not active");
                if(SystemClock.elapsedRealtime()<=active[1]){ui.postDelayed(this::pulse,2);return;}
                cast.pickerVisibility(this,true);
                require(sdkCallback()[1]==active[1],"repeated visible event renews scan deadline");
                cast.pickerVisibility(this,false);
                require(!(Boolean)field("discovering"),"background retains discovery callback");
                require(sdkCallback()==null,"actual SDK retains background callback");
                cast.pickerVisibility(this,true);
                require((Boolean)field("discovering"),"foreground did not resume discovery");
                // Isolated controller state checks only; these do NOT simulate
                // a receiver connection, transfer, native release or playback.
                for(String state:new String[]{"selecting","transferStarted","handedOff","returning","cleanupPending"}) {
                    cast.pickerVisibility(this,false);field(state,true);
                    cast.pickerVisibility(this,true);
                    require(!(Boolean)field("discovering"),"discovery admitted during "+state);
                    field(state,false);cast.pickerVisibility(this,true);
                    require((Boolean)field("discovering"),"picker did not recover after "+state);
                }
                InfinityCastSession.View other=()->{};
                cast.pickerVisibility(other,false);
                require((Boolean)field("discovering"),"another view stopped this picker");
                cast.detach(other);
                require((Boolean)field("discovering") && sdkCallback()!=null,"stale detach stopped current picker");
                cast.detach(this);
                require(!(Boolean)field("discovering"),"dismiss retained discovery callback");
                require(sdkCallback()==null,"actual SDK retains dismissed callback");
                require(!(Boolean)field("listening"),"idle dismissed picker retained session callback");
                result(true,"SDK_picker_lifecycle_verified");return;
            }
        } catch(Exception | LinkageError error) {
            result(false,"probe_"+error.getClass().getSimpleName());return;
        }
        if(SystemClock.uptimeMillis()>deadline){result(false,"SDK_initialization_deadline");return;}
        ui.postDelayed(this::pulse,100);
    }
    private void result(boolean passed,String reason) {
        if(finished)return;finished=true;
        try {
            if(cast!=null)cast.detach(this);
            JSONObject report=new JSONObject().put("pass",passed).put("reason",reason)
                .put("API",android.os.Build.VERSION.SDK_INT).put("checks",checks).put("main_thread_pulses",pulses)
                .put("scope","real SDK initialization and discovery registration lifecycle; no receiver fixture")
                .put("SDK_active_scan_flag_verified",passed).put("SDK_request_timestamp_not_renewed",passed)
                .put("active_scan_expiry","30s_PINNED_SDK_SOURCE_CONTRACT_NOT_TIMED_ON_ANDROID")
                .put("wifi_receiver_discovery","NOT_TESTED").put("physical_TV_playback","NOT_TESTED")
                .put("media_delivery","UNCHANGED_NOT_RERUN").put("Kodi_shutdown","NOT_RUN")
                .put("native_observer_correction","NOT_INCLUDED_IN_THIS_PROBE").put("owner_installer",false);
            android.util.Log.i("InfinityCastProbe",report.toString());
        } catch(Exception ignored) {}
    }
    @Override public void changed() {}
}
