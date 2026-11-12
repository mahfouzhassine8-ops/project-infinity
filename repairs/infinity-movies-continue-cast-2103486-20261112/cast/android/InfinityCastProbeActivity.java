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
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        oldResource=getResources().getIdentifier("tag_accessibility_pane_title","id","com.projectinfinity.kodi");
        if(oldResource==0){result(false,"baseline_resource_missing");return;}
        if(getResources().getIdentifier("cast_device_chooser_title","string","com.projectinfinity.cast.resources")!=0){
            result(false,"Cast_resource_loaded_before_request");return;}
        deadline=SystemClock.uptimeMillis()+20000;
        cast=InfinityCastSession.get(this);cast.attach(this);
        pulse();
    }
    private void pulse() {
        if(finished)return;pulses++;
        try {
            java.lang.reflect.Field field=InfinityCastSession.class.getDeclaredField("initialized");field.setAccessible(true);
            if(field.getBoolean(cast)) {
                int same=getResources().getIdentifier("tag_accessibility_pane_title","id","com.projectinfinity.kodi");
                int added=getResources().getIdentifier("cast_device_chooser_title","string","com.projectinfinity.cast.resources");
                if(same!=oldResource || (added>>>24)!=128){result(false,"resource_isolation_failed");return;}
                android.view.View view=new android.view.View(this);
                androidx.core.view.ViewCompat.setAccessibilityPaneTitle(view,"Cast probe");
                if(!"Cast probe".contentEquals(androidx.core.view.ViewCompat.getAccessibilityPaneTitle(view))){
                    result(false,"existing_core_tag_contract_failed");return;}
                // Require repeated main-thread callbacks, not just a class load.
                if(pulses>=10){result(true,"SDK_initialized_resources_isolated_original_Core_API_usable");return;}
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
                .put("full_Infinity_playback","NOT_TESTED").put("receiver_transfer","NOT_TESTED")
                .put("shutdown","NOT_SELECTED").put("owner_APK",false);
            android.util.Log.i("InfinityCastProbe",value.toString());
        } catch(Exception ignored) {}
        if(cast!=null)cast.detach(this);
    }
    @Override public void changed() {}
}
