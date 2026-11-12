package com.projectinfinity.kodi;

import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;

/** One asynchronous native command. No blocking UI/JNI wait or blind retry. */
final class InfinityCastGateway {
    interface Result {
        void done(JSONObject result);
        default void pendingCommit() {}
    }
    private final Handler handler=new Handler(Looper.getMainLooper());
    private Pending pending;
    private static final class Pending {
        long id,deadline;
        boolean warned;
        Result result;
    }
    boolean busy() { return pending!=null; }
    static JSONObject error(String reason) {
        JSONObject value=new JSONObject();
        try { value.put("status","error").put("reason",reason); } catch(Exception ignored) {}
        return value;
    }
    void request(String operation,String token,long position,Result result) {
        if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("Cast command thread");
        if(pending!=null){ result.done(error("native_busy"));return; }
        final long id;
        try {
            id=InfinityCastNative.request(operation,token,position);
        } catch(LinkageError | RuntimeException failure) {
            result.done(error("matching_native_component_unavailable"));return;
        }
        if(id==0){result.done(error("native_unavailable"));return;}
        Pending next=new Pending();next.id=id;next.deadline=SystemClock.uptimeMillis()+3500;
        next.result=result;pending=next;poll(next);
    }
    private void poll(Pending request) {
        if(pending!=request)return;
        JSONObject completed=null;
        boolean warn=false;
        try {
            byte[] data=InfinityCastNative.poll(request.id);
            if(data!=null) {
                pending=null;
                completed=data.length>131072?error("native_result_limit"):
                    new JSONObject(new String(data,StandardCharsets.UTF_8));
            } else if(SystemClock.uptimeMillis()>request.deadline && !request.warned) {
                request.warned=true;
                if(InfinityCastNative.cancel(request.id)) {
                    pending=null;completed=error("cancelled_before_commit");
                } else warn=true;
                // Do not pretend an already committed operation was undone.
                // Keep this ONE bounded native request owned until its actual
                // outcome arrives; do not launch replacement worker threads.
            }
        } catch(Exception | LinkageError failure) {
            pending=null;completed=error("native_result_unavailable");
        }
        // Callback exceptions cannot be mistaken for a second native outcome.
        if(completed!=null){request.result.done(completed);return;}
        if(warn)request.result.pendingCommit();
        handler.postDelayed(()->poll(request),request.warned?250:16);
    }
    void cancel() {
        Pending request=pending;if(request==null)return;
        try {
            if(InfinityCastNative.cancel(request.id)) {
                pending=null;request.result.done(error("cancelled_before_commit"));
            } else if(!request.warned) { request.warned=true;request.result.pendingCommit(); }
        } catch(LinkageError ignored) {}
    }
}
