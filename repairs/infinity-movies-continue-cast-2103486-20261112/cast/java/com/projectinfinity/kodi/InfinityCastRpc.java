package com.projectinfinity.kodi;

import android.os.Handler;
import android.os.Looper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Only theme reads and the authenticated CC channel-registration command.
 * Playback mutations use the cancellable, item-bound native interface instead.
 */
final class InfinityCastRpc {
    private static final ThreadPoolExecutor executor=new ThreadPoolExecutor(1,1,30,TimeUnit.SECONDS,
        new ArrayBlockingQueue<>(1),r->{Thread t=new Thread(r,"InfinityCastRegistration");t.setDaemon(true);return t;},
        new ThreadPoolExecutor.AbortPolicy());
    static { executor.allowCoreThreadTimeOut(true); }
    interface Reply { void ready(JSONObject value); }
    static void send(String method,JSONObject parameters,Reply reply) {
        Handler ui=new Handler(Looper.getMainLooper());
        try {
            executor.execute(()->{
                JSONObject value=null;
                try {
                    JSONObject request=new JSONObject().put("jsonrpc","2.0").put("id",1)
                        .put("method",method).put("params",parameters);
                    String response=new XBMCJsonRPC().request_string(request.toString());
                    if(response!=null && response.length()<32768)value=new JSONObject(response);
                } catch(Exception | LinkageError ignored) {}
                final JSONObject result=value;
                if(reply!=null)ui.post(()->reply.ready(result));
            });
        } catch(RuntimeException full) { if(reply!=null)ui.post(()->reply.ready(null)); }
    }
    static void channel(String name,boolean clear) {
        if(name==null || !name.matches("infinity-cast-[1-9][0-9]*-[a-f0-9]{32}"))return;
        try {
            JSONArray args=new JSONArray().put("cast-channel").put(name);
            if(clear)args.put("clear");
            send("Addons.ExecuteAddon",new JSONObject().put("addonid","script.infinity.commandcenter")
                 .put("params",args).put("wait",false),null);
        } catch(Exception ignored) {}
    }
}
