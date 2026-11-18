package com.projectinfinity.kodi;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.concurrent.*;
import org.json.JSONArray;
import org.json.JSONObject;

/** One verified indexed MKV, stream-copied just in time; no file or database. */
final class InfinityCastRemux implements AutoCloseable {
    interface Input extends AutoCloseable {
        int read(byte[] target,int size) throws IOException;
        long seek(long offset,int whence) throws IOException;
        String failure();
        void budget(long bytes);
        default long[] usage(){return new long[0];}
        @Override void close();
    }
    private final Input input;
    private volatile Thread owner;
    private final ThreadPoolExecutor executor=new ThreadPoolExecutor(1,1,0,TimeUnit.SECONDS,new ArrayBlockingQueue<>(4),r->{Thread t=new Thread(r,"InfinityCastCodecOwner");t.setDaemon(true);owner=t;return t;});
    private final InfinityCastResource.Store fragments=new InfinityCastResource.Store();
    private final java.util.ArrayList<InfinityCastResource.Lease> warmed=new java.util.ArrayList<>();
    private final java.util.ArrayList<Integer> warmIndices=new java.util.ArrayList<>();
    private int warmFirst=-1,warmLast=-1;private boolean warming;
    private void releaseWarm(){for(InfinityCastResource.Lease lease:warmed)lease.close();warmed.clear();warmIndices.clear();warmFirst=warmLast=-1;}
    private InfinityCastResource.Lease admitted(InfinityCastResource r,int index)throws IOException {InfinityCastResource.Lease lease=fragments.pin(r);return lease;}
    private final LinkedHashMap<Integer,String> representations=new LinkedHashMap<>();
    private static final class Ticket<T> implements Callable<T> {
        final Callable<T> task;T result;boolean abandoned;
        Ticket(Callable<T> task){this.task=task;}
        private static void release(Object value){if(value instanceof InfinityCastResource.Lease)((InfinityCastResource.Lease)value).close();}
        public T call()throws Exception {T value=task.call();synchronized(this){if(abandoned)release(value);else result=value;}return value;}
        synchronized T claim(T value){result=null;return value;}
        synchronized void abandon(){abandoned=true;release(result);result=null;}
    }
    private <T> T owned(Callable<T> task)throws IOException {
        if(Thread.currentThread()==owner){try{return task.call();}catch(IOException e){throw e;}catch(Exception e){throw new IOException("mkv_owner_failure");}}
        Ticket<T> ticket=new Ticket<>(task);Future<T> future;try{synchronized(this){if(retirement!=null)throw new RejectedExecutionException();future=executor.submit(ticket);}}catch(RejectedExecutionException busy){throw new IOException("mkv_owner_busy");}
        try{return ticket.claim(future.get(20,TimeUnit.SECONDS));}catch(InterruptedException e){Thread.currentThread().interrupt();ticket.abandon();cancel();future.cancel(false);executor.remove((Runnable)future);throw new IOException("mkv_cancelled");}
        catch(TimeoutException e){ticket.abandon();cancel();future.cancel(false);executor.remove((Runnable)future);throw new IOException("mkv_owner_deadline");}
        catch(CancellationException e){ticket.abandon();throw new IOException("mkv_cancelled");}
        catch(ExecutionException e){ticket.abandon();Throwable cause=e.getCause();if(cause instanceof IOException)throw (IOException)cause;if(cause instanceof OutOfMemoryError)throw new IOException("mkv_memory_limit");throw new IOException("mkv_owner_failure");}
    }
    private volatile long handle;
    private volatile boolean cancelled;
    private long[] starts;
    private byte[] initialization;
    private String video,audio;
    private String codecs;
    private InfinityCastReceiverPolicy.Media inspectedVideo;
    private volatile InfinityCastHardwareVideo hardwareVideo;
    private byte[] master;
    InfinityCastRemux(Input input) throws IOException {
        this.input=input;
        try{owned(()->{InfinityCastRemuxNative.load();handle=InfinityCastRemuxNative.open(input);if(handle==0)throw new IOException("mkv_native_context_unavailable");if(cancelled){InfinityCastRemuxNative.close(handle);handle=0;throw new IOException("mkv_cancelled");}return null;});}catch(IOException failure){try{closeAsync(()->{});}catch(RuntimeException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    void prepare() throws IOException {
        owned(()->{
            check();
            try{
                input.budget(16L*1024*1024);
                String raw=InfinityCastRemuxNative.inspect(handle);if(raw==null || raw.length()>262144)throw new IOException("mkv_inspection_limit");
                JSONObject metadata=new JSONObject(raw);video=metadata.optString("video","unknown");audio=metadata.optString("audio","unknown");
                InfinityCastDiagnostics.event("mkv_video",video,0);InfinityCastDiagnostics.event("mkv_audio",audio,0);
                if(!"ok".equals(metadata.optString("status"))){
                    String error=metadata.optString("reason","mkv_inspection_failed");
                    if(error.equals("mkv_unsupported_video_codec"))error="mkv_unsupported_video_"+video;
                    if(error.equals("mkv_unsupported_audio_codec"))error="mkv_unsupported_audio_"+audio;
                    throw new IOException(error);
                }
                inspectedVideo=new InfinityCastReceiverPolicy.Media(video,metadata.optInt("video_profile",-1),metadata.optInt("video_level",-1),metadata.optInt("width",0),metadata.optInt("height",0),metadata.optLong("fps_num",0),metadata.optLong("fps_den",0),metadata.optInt("color_transfer",0));
                JSONArray times=metadata.getJSONArray("starts_us");if(times.length()<2 || times.length()>8193)throw new IOException("mkv_seek_index_limit");
                starts=new long[times.length()];for(int n=0;n<starts.length;n++){starts[n]=times.getLong(n);if(starts[n]<0 || (n>0 && starts[n]<=starts[n-1]))throw new IOException("mkv_invalid_seek_index");}
                if(starts[0]!=0 || starts[starts.length-1]!=metadata.getLong("duration_us"))throw new IOException("mkv_unverified_timeline");
                initialization=InfinityCastRemuxNative.init(handle);if(initialization==null || initialization.length<16 || initialization.length>1048576)throw new IOException("mkv_init_limit");
                codecs=metadata.optString("codecs","");
                if(!codecs.matches("(avc1\\.[0-9A-F]{6}|hev1\\.[ABC]?[0-9]+\\.[0-9A-F]+\\.[LH][0-9]+(?:\\.[0-9A-F]{2}){0,6})(?:,(?:mp4a\\.(?:40\\.[0-9]+|69|6B)|ac-3|ec-3))?"))throw new IOException("mkv_invalid_codec_description");
                if("hevc".equals(video)){String descriptor=codecs.split(",")[0];String[] fields=descriptor.split("\\.");InfinityCastDiagnostics.event("mkv_video_profile","hevc",Integer.parseInt(fields[1].replaceAll("[ABC]","")));InfinityCastDiagnostics.event("mkv_video_level",fields[3].startsWith("H")?"high_tier":"main_tier",Integer.parseInt(fields[3].substring(1)));}
                if("hevc".equals(video)){InfinityCastDiagnostics.event("mkv_csd","private_bytes",metadata.optInt("video_csd_bytes",-1));InfinityCastDiagnostics.event("mkv_csd","arrays",metadata.optInt("video_csd_arrays",-1));InfinityCastDiagnostics.event("mkv_csd","nal_length_bytes",metadata.optInt("video_nal_length_bytes",-1));}
                check();InfinityCastDiagnostics.event("mkv_inspection","stream_copy_ready",starts.length-1);
            }catch(IOException e){throw failure(e);}catch(Exception e){throw new IOException("mkv_inspection_failed");}
            return null;
        });
    }
    void requireReceiver(InfinityCastReceiverPolicy.Receiver receiver,InfinityCastHardwareVideo.Factory factory) throws IOException {
        owned(()->{check();if(inspectedVideo==null)throw new IOException("mkv_not_prepared");
            InfinityCastReceiverPolicy.Choice choice=InfinityCastReceiverPolicy.choose(receiver,inspectedVideo);
            InfinityCastDiagnostics.event("receiver_policy",choice.reason,choice.path.ordinal());
            if(choice.path==InfinityCastReceiverPolicy.Path.HARDWARE_AVC_720_REQUIRED){
                if(factory==null)throw new IOException("receiver_requires_hardware_avc_720");
                hardwareVideo=factory.create();check();long readBudget=0;boolean budgetInstalled=false;
                JSONObject output;
                try{readBudget=InfinityCastRemuxNative.readBudget(handle,0);if(readBudget<33554432L || readBudget>134217728L)throw new IOException("mkv_source_budget_invalid");input.budget(readBudget);budgetInstalled=true;output=new JSONObject(InfinityCastRemuxNative.configureVideo(handle,hardwareVideo));}
                catch(IOException error){throw budgetInstalled?failure(error):error;}catch(Exception invalid){throw new IOException("cast_hw_output_description");}
                finally{reportSource(0,readBudget,budgetInstalled);}
                video=output.optString("video");audio=output.optString("audio");codecs=output.optString("codecs");
                if(!"h264".equals(video)||!codecs.matches("avc1\\.[0-9A-F]{6}(?:,mp4a\\.40\\.[0-9]+)?"))throw new IOException("cast_hw_output_codec");
                initialization=InfinityCastRemuxNative.init(handle);if(initialization==null||initialization.length<16||initialization.length>1048576)throw new IOException("cast_hw_output_init");master=null;
                InfinityCastDiagnostics.event("hardware_video","h264_aac_ready",720);
            }
            // Unknown is an explicitly unverified existing direct attempt, never
            // advertised as supported. Existing transactional pause/return is unchanged.
            return null;
        });
    }
    private IOException failure(IOException error){String reason=input.failure();return reason.isEmpty()?error:new IOException(reason);}
    private void check() throws IOException{if(cancelled || handle==0)throw new IOException("mkv_cancelled");}
    boolean hardwareVideo(){return hardwareVideo!=null;}
    long durationMs(){return starts==null?0:starts[starts.length-1]/1000;}
    byte[] playlist(String base) throws IOException {
        return owned(()->{
            check();if(starts==null || codecs==null)throw new IOException("mkv_not_prepared");
            if(master==null){
                // Measured first-segment estimate for a single JIT rendition.
                // Use the existing cache: the receiver's next request reuses it.
                long length;try(InfinityCastResource.Lease first=resourceView("0.m4s")){length=first.length();}long span=starts[1]-starts[0];
                long rate=((length+(long)initialization.length)*8000000L+span-1)/span;
                master=("#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-INDEPENDENT-SEGMENTS\n#EXT-X-STREAM-INF:BANDWIDTH="+rate+",CODECS=\""+codecs+"\"\n"+base+"/mkv/media.m3u8\n").getBytes(StandardCharsets.UTF_8);
                InfinityCastDiagnostics.event("mkv_manifest","explicit_codec_master",1);
            }
            return master;
        });
    }
    byte[] mediaPlaylist(String base) throws IOException {
        check();if(starts==null)throw new IOException("mkv_not_prepared");long largest=0;
        for(int n=1;n<starts.length;n++)largest=Math.max(largest,starts[n]-starts[n-1]);
        StringBuilder text=new StringBuilder("#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-TARGETDURATION:").append((largest+999999)/1000000).append("\n#EXT-X-MEDIA-SEQUENCE:0\n#EXT-X-INDEPENDENT-SEGMENTS\n#EXT-X-MAP:URI=\"").append(base).append("/mkv/init.mp4\"\n");
        for(int n=0;n<starts.length-1;n++)text.append("#EXTINF:").append(String.format(Locale.ROOT,"%.6f",(starts[n+1]-starts[n])/1000000.0)).append(",\n").append(base).append("/mkv/").append(n).append(".m4s\n");
        text.append("#EXT-X-ENDLIST\n");byte[] data=text.toString().getBytes(StandardCharsets.UTF_8);if(data.length>1048576)throw new IOException("mkv_playlist_limit");return data;
    }
    // Legacy test callers retain their small-array interface; production streams a pinned lease.
    byte[] resource(String suffix) throws IOException {
        if(suffix.equals("init.mp4"))return owned(()->{check();return initialization;});
        try(InfinityCastResource.Lease data=resourceView(suffix)){return data.smallArray();}
    }
    InfinityCastResource.Lease resourceView(String suffix)throws IOException {
        return owned(()->{
            check();if(!suffix.matches("[0-9]{1,4}\\.m4s"))throw new IOException("mkv_unknown_resource");
            int index=Integer.parseInt(suffix.substring(0,suffix.length()-4));if(starts==null||index>=starts.length-1)throw new IOException("mkv_segment_out_of_range");
            InfinityCastResource ready=fragments.get(index);if(ready!=null&&ready.complete)return admitted(ready,index);
            InfinityCastResource producing=fragments.create(index);
            long readBudget=0;boolean budgetInstalled=false;long entered=System.nanoTime();
            InfinityCastDiagnostics.event("mkv_request","started",index);
            try{readBudget=InfinityCastRemuxNative.readBudget(handle,index);if(readBudget<33554432L || readBudget>134217728L)throw new IOException("mkv_source_budget_invalid");input.budget(readBudget);budgetInstalled=true;InfinityCastRemuxNative.segmentStream(handle,index,producing);check();producing.seal(true);String previous=representations.get(index);if(hardwareVideo==null&&previous!=null&&!previous.equals(producing.digest))throw new IOException("mkv_resource_representation_changed");representations.put(index,producing.digest);}
            catch(IOException error){
                IOException actual=budgetInstalled?failure(error):error;
                String nativeCode=error.getMessage(),code=actual.getMessage();
                boolean explicitCancel="mkv_cancelled".equals(nativeCode)||"cast_hw_video_cancelled".equals(nativeCode);
                InfinityCastDiagnostics.event("mkv_request",cancelled?(explicitCancel?"cancelled_after_close":"failed_during_close"):"generation_failed",index);
                InfinityCastDiagnostics.event("mkv_request","close_flag_observed",cancelled?1:0);
                // Preserve both observed outcomes; concurrent close proves no cause.
                if(nativeCode!=null&&nativeCode.matches("(?:mkv_|cast_hw_)[a-z0-9_]{1,55}"))InfinityCastDiagnostics.event("mkv_native_failure",nativeCode,index);
                if(code!=null&&code.matches("(?:mkv_|cast_hw_)[a-z0-9_]{1,55}"))InfinityCastDiagnostics.event("mkv_failure",code,index);
                producing.abort();throw actual;
            }catch(RuntimeException|OutOfMemoryError failure){producing.abort();throw new IOException("mkv_resource_storage_failed");}
            finally{InfinityCastDiagnostics.event("mkv_request","elapsed_ms",(int)Math.min(Integer.MAX_VALUE,(System.nanoTime()-entered)/1000000));reportSource(index,readBudget,budgetInstalled);}

            InfinityCastDiagnostics.event("mkv_fragment","copied",index);InfinityCastDiagnostics.event("mkv_request","generated_bytes",(int)producing.length);
            return admitted(producing,index);
        });
    }
    /** Readiness is around the actual transfer position; repeated/cache requests add no throughput coverage. */
    void consume(String suffix){try{int index=Integer.parseInt(suffix.substring(0,suffix.length()-4));owned(()->{if(!warming&&index>=warmFirst&&index<=warmLast){int at=warmIndices.indexOf(index);if(at>=0){warmed.remove(at).close();warmIndices.remove(at);}if(warmed.isEmpty())warmFirst=warmLast=-1;}return null;});}catch(IOException|RuntimeException ignored){/* Existing lease still retires in the serving finally block. */}}
    void warm(long positionMs)throws IOException {warm(positionMs,()->true);}
    void warm(long positionMs,java.util.function.BooleanSupplier current)throws IOException {owned(()->{
        check();if(!current.getAsBoolean())throw new IOException("mkv_prebuffer_superseded");long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(20);int index=0;while(index+1<starts.length-1&&starts[index+1]/1000<=positionMs)index++;
        releaseWarm();warming=true;warmFirst=index;long covered=0;
        try{for(int n=index;n<starts.length-1&&covered<8000000;n++){
            if(!current.getAsBoolean())throw new IOException("mkv_prebuffer_superseded");if(System.nanoTime()>deadline)throw new IOException("mkv_prebuffer_deadline");
            warmed.add(resourceView(n+".m4s"));warmIndices.add(n);warmLast=n;covered+=starts[n+1]-Math.max(starts[n],positionMs*1000);
        }
        if(!current.getAsBoolean())throw new IOException("mkv_prebuffer_superseded");if(System.nanoTime()>deadline)throw new IOException("mkv_prebuffer_deadline");
        if(hardwareVideo!=null)hardwareVideo.requireDelivery(starts[index],starts[warmLast+1],positionMs*1000,starts[starts.length-1]);
        }catch(IOException failure){releaseWarm();throw failure;}finally{warming=false;}
        InfinityCastDiagnostics.event("mkv_prebuffer","ready_ms",(int)(covered/1000));return null;
    });}
    /** Numeric-only, bounded best-effort outcome reporting; never masks the request failure. */
    private void reportSource(int index,long budget,boolean budgetInstalled){
        try{
            long[] nativeStats=InfinityCastRemuxNative.sourceStats(handle),origin=budgetInstalled?input.usage():new long[0];
            InfinityCastDiagnostics.event("mkv_source","fragment_index",index);
            InfinityCastDiagnostics.event("mkv_source","read_budget_bytes",(int)budget);
            if(origin.length>=4){InfinityCastDiagnostics.event("mkv_source","bytes_consumed",(int)origin[0]);InfinityCastDiagnostics.event("mkv_source","seek_count",(int)Math.min(Integer.MAX_VALUE,origin[1]));InfinityCastDiagnostics.event("mkv_source","range_requests",(int)Math.min(Integer.MAX_VALUE,origin[2]));}
            if(budgetInstalled && nativeStats!=null && nativeStats.length>=7 && nativeStats[0]==index){String[] phases={"aac_bytes","preroll_bytes","selected_bytes","lookahead_bytes"};for(int n=0;n<4;n++)InfinityCastDiagnostics.event("mkv_source",phases[n],(int)nativeStats[n+1]);}
            if(origin.length>=6){InfinityCastDiagnostics.event("mkv_source","cache_bytes",(int)origin[4]);InfinityCastDiagnostics.event("mkv_source","logical_bytes",(int)origin[5]);}
            if(nativeStats!=null&&nativeStats.length==17){String[] phases={"aac_ms","seek_ms","video_ms","mux_ms","total_ms","output_bytes","mux_payload_peak","planner_saturated","failed_mux_phase","failed_mux_result"};for(int n=0;n<10;n++)InfinityCastDiagnostics.event("mkv_profile",phases[n],(int)nativeStats[n+7]);}
            if(budgetInstalled && "mkv_source_read_limit".equals(input.failure()))InfinityCastDiagnostics.event("mkv_source","budget_exhausted",1);
        }catch(IOException|RuntimeException|OutOfMemoryError unavailable){/* Logging cannot change playback/cancellation outcomes. */}
    }
    /** Called immediately on cancel; never waits for the worker/native mutex. */
    void cancel(){cancelled=true;InfinityCastHardwareVideo hw=hardwareVideo;if(hw!=null)hw.cancel();long current=handle;if(current!=0)InfinityCastRemuxNative.cancel(current);}
    /** Relay invokes this only after every admitted probe/serve job retired. */
    private FutureTask<Void> retirement;
    private Void retireOwned()throws IOException {
        if(hardwareVideo!=null){try{hardwareVideo.close();}catch(IOException unresolved){input.close();throw new IOException("cast_hw_resources_not_retired",unresolved);}hardwareVideo=null;}
        long current=handle;handle=0;if(current!=0)InfinityCastRemuxNative.close(current);input.close();releaseWarm();fragments.close();representations.clear();initialization=null;starts=null;master=null;codecs=null;return null;
    }
    void closeAsync(Runnable completed){
        cancel();synchronized(this){
            if(retirement!=null)throw new IllegalStateException("mkv_retirement_already_admitted");
            // Stop admission, retire queued waiters and reserve the sole owner for
            // cleanup. The active operation observes the native/I/O cancel flag.
            for(Runnable queued:executor.getQueue().toArray(new Runnable[0]))if(executor.remove(queued)&&queued instanceof Future<?>)((Future<?>)queued).cancel(false);
            retirement=new FutureTask<Void>(this::retireOwned){@Override protected void done(){try{get();completed.run();}catch(Exception|LinkageError failure){InfinityCastDiagnostics.event("mkv_cleanup","retirement_failed",0);}}};
            executor.execute(retirement);executor.shutdown();
        }
    }
    @Override public void close(){
        synchronized(this){if(retirement==null)closeAsync(()->{});}
        // Bounded caller wait does not cancel or suppress eventual owner cleanup.
        try{retirement.get(20,TimeUnit.SECONDS);}catch(InterruptedException failure){Thread.currentThread().interrupt();throw new IllegalStateException("mkv_resources_not_retired",failure);}
        catch(ExecutionException|TimeoutException failure){throw new IllegalStateException("mkv_resources_not_retired",failure);}
    }
}
