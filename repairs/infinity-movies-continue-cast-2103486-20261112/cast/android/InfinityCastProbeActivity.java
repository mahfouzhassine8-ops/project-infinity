package com.projectinfinity.kodi;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import org.json.JSONObject;

/** CI-only separate-package probe. Never included in the combined installer. */
public final class InfinityCastProbeActivity extends Activity implements InfinityCastSession.View {
    private final Handler ui=new Handler(Looper.getMainLooper());
    private long deadline;
    private int pulses;
    private boolean finished;
    private InfinityCastSession cast;
    private int oldResource;
    private int activityResourceAfter,applicationResourceAfter,applicationCastResource,activityCastResource;
    private boolean explicitSelectionGuard,privateResource;
    private volatile JSONObject relayResult;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        oldResource=getResources().getIdentifier("tag_accessibility_pane_title","id","com.projectinfinity.kodi");
        if(oldResource==0){result(false,"baseline_resource_missing");return;}
        if(getResources().getIdentifier("cast_device_chooser_title","string","com.projectinfinity.cast.resources")!=0){
            result(false,"Cast_resource_loaded_before_request");return;}
        deadline=SystemClock.uptimeMillis()+20000;
        Thread relayProbe=new Thread(()->relayResult=InfinityCastRelayAndroidTest.run(),"CIOnlyCastRelayProbe");
        relayProbe.setDaemon(true);relayProbe.start();
        cast=InfinityCastSession.get(this);cast.attach(this);
        try {
            java.lang.reflect.Field source=InfinityCastSession.class.getDeclaredField("source");source.setAccessible(true);
            java.lang.reflect.Field transport=InfinityCastSession.class.getDeclaredField("privateSource");transport.setAccessible(true);
            source.set(cast,new JSONObject());transport.set(cast,InfinityCastSource.parse("https://example.invalid/public.mp4"));
            // SDK classes are intentionally private/optimized. The production
            // controller is compiled with them; a separately compiled CI probe
            // must inspect its actual parameter type, not import an old name.
            java.lang.reflect.Method connect=null;
            for(java.lang.reflect.Method method:InfinityCastSession.class.getDeclaredMethods())
                if(method.getName().equals("connectedSession") && method.getParameterTypes().length==1)connect=method;
            if(connect==null)throw new NoSuchMethodException("connectedSession");
            connect.setAccessible(true);connect.invoke(cast,new Object[]{null});
            java.lang.reflect.Field started=InfinityCastSession.class.getDeclaredField("transferStarted");started.setAccessible(true);
            explicitSelectionGuard=!started.getBoolean(cast);source.set(cast,null);transport.set(cast,null);
            Class<?> suffix=Class.forName("assets.infinity.cast.privatehttp.okhttp3.internal.publicsuffix.PublicSuffixDatabase");
            try(java.io.InputStream data=suffix.getResourceAsStream("publicsuffixes.gz")){privateResource=data!=null && data.read()==31 && data.read()==139;}
            if(!explicitSelectionGuard || !privateResource){result(false,"private_transport_or_explicit_selection_guard_failed");return;}
        }catch(Exception | LinkageError failure){result(false,"private_runtime_guard_"+failure.getClass().getSimpleName());return;}
        pulse();
    }
    private void pulse() {
        if(finished)return;pulses++;
        try {
            java.lang.reflect.Field field=InfinityCastSession.class.getDeclaredField("initialized");field.setAccessible(true);
            if(field.getBoolean(cast)) {
                activityResourceAfter=getResources().getIdentifier("tag_accessibility_pane_title","id","com.projectinfinity.kodi");
                applicationResourceAfter=getApplicationContext().getResources().getIdentifier("tag_accessibility_pane_title","id","com.projectinfinity.kodi");
                applicationCastResource=getApplicationContext().getResources().getIdentifier("cast_device_chooser_title","string","com.projectinfinity.cast.resources");
                activityCastResource=getResources().getIdentifier("cast_device_chooser_title","string","com.projectinfinity.cast.resources");
                // Production installs the provider on the SDK's Application
                // context. A separate Activity Resources instance need not
                // gain the new package. Its original identifiers must survive.
                if(activityResourceAfter!=oldResource || applicationResourceAfter!=oldResource ||
                    (applicationCastResource>>>24)!=128){result(false,"resource_isolation_failed");return;}
                if(getApplicationContext().getResources().getString(applicationCastResource).isEmpty()){
                    result(false,"SDK_string_unreadable");return;}
                int originalSymbol=Class.forName("androidx.core.R$id").getField("tag_accessibility_pane_title").getInt(null);
                if(originalSymbol!=oldResource){result(false,"original_Core_resource_symbol_changed");return;}
                android.view.View view=new android.view.View(this);
                androidx.core.view.ViewCompat.setAccessibilityPaneTitle(view,"Cast probe");
                if(!"Cast probe".contentEquals(androidx.core.view.ViewCompat.getAccessibilityPaneTitle(view))){
                    result(false,"existing_core_tag_contract_failed");return;}
                // Require repeated main-thread callbacks, not just a class load.
                if(relayResult!=null && !relayResult.optBoolean("pass")){result(false,"relay_probe_failed");return;}
                if(pulses>=10 && relayResult!=null){result(true,"SDK_resources_existing_API_and_local_relay_verified");return;}
            }
        } catch(Exception | LinkageError failure){result(false,failure.getClass().getSimpleName());return;}
        if(SystemClock.uptimeMillis()>deadline){result(false,"SDK_initialization_deadline");return;}
        ui.postDelayed(this::pulse,100);
    }
    private void result(boolean passed,String reason) {
        if(finished)return;finished=true;
        try {
            JSONObject value=new JSONObject().put("schema",1).put("pass",passed).put("reason",reason)
                .put("main_thread_pulses",pulses).put("API",android.os.Build.VERSION.SDK_INT)
                .put("original_resource_id",oldResource).put("Activity_original_after",activityResourceAfter)
                .put("Application_original_after",applicationResourceAfter).put("Application_Cast_id",applicationCastResource)
                .put("Activity_Cast_id",activityCastResource)
                .put("relay",relayResult==null?JSONObject.NULL:relayResult)
                .put("explicit_receiver_selection_required",explicitSelectionGuard).put("private_HTTP_resource_readable",privateResource)
                .put("full_Infinity_playback","NOT_TESTED").put("receiver_transfer","NOT_TESTED")
                .put("shutdown","NOT_SELECTED").put("owner_APK",false);
            android.util.Log.i("InfinityCastProbe",value.toString());
        } catch(Exception ignored) {}
        if(cast!=null)cast.detach(this);
    }
    @Override public void changed() {}
}
