package com.projectinfinity.kodi;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
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
    private final Object worker=new Object();
    private final LinkedHashMap<Integer,byte[]> fragments=new LinkedHashMap<>(4,0.75f,true);
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
        this.input=input;InfinityCastRemuxNative.load();handle=InfinityCastRemuxNative.open(input);
        if(handle==0)throw new IOException("mkv_native_context_unavailable");
    }
    void prepare() throws IOException {
        synchronized(worker){
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
        }
    }
    void requireReceiver(InfinityCastReceiverPolicy.Receiver receiver,InfinityCastHardwareVideo.Factory factory) throws IOException {
        synchronized(worker){check();if(inspectedVideo==null)throw new IOException("mkv_not_prepared");
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
                initialization=InfinityCastRemuxNative.init(handle);if(initialization==null||initialization.length<16||initialization.length>1048576)throw new IOException("cast_hw_output_init");fragments.clear();master=null;
                InfinityCastDiagnostics.event("hardware_video","h264_aac_ready",720);
            }
            // Unknown is an explicitly unverified existing direct attempt, never
            // advertised as supported. Existing transactional pause/return is unchanged.
        }
    }
    private IOException failure(IOException error){String reason=input.failure();return reason.isEmpty()?error:new IOException(reason);}
    private void check() throws IOException{if(cancelled || handle==0)throw new IOException("mkv_cancelled");}
    boolean hardwareVideo(){return hardwareVideo!=null;}
    long durationMs(){return starts==null?0:starts[starts.length-1]/1000;}
    byte[] playlist(String base) throws IOException {
        synchronized(worker){
            check();if(starts==null || codecs==null)throw new IOException("mkv_not_prepared");
            if(master==null){
                // Measured first-segment estimate for a single JIT rendition.
                // Use the existing cache: the receiver's next request reuses it.
                byte[] first=resource("0.m4s");long span=starts[1]-starts[0];
                long rate=((first.length+(long)initialization.length)*8000000L+span-1)/span;
                master=("#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-INDEPENDENT-SEGMENTS\n#EXT-X-STREAM-INF:BANDWIDTH="+rate+",CODECS=\""+codecs+"\"\n"+base+"/mkv/media.m3u8\n").getBytes(StandardCharsets.UTF_8);
                InfinityCastDiagnostics.event("mkv_manifest","explicit_codec_master",1);
            }
            return master;
        }
    }
    byte[] mediaPlaylist(String base) throws IOException {
        check();if(starts==null)throw new IOException("mkv_not_prepared");long largest=0;
        for(int n=1;n<starts.length;n++)largest=Math.max(largest,starts[n]-starts[n-1]);
        StringBuilder text=new StringBuilder("#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-TARGETDURATION:").append((largest+999999)/1000000).append("\n#EXT-X-MEDIA-SEQUENCE:0\n#EXT-X-INDEPENDENT-SEGMENTS\n#EXT-X-MAP:URI=\"").append(base).append("/mkv/init.mp4\"\n");
        for(int n=0;n<starts.length-1;n++)text.append("#EXTINF:").append(String.format(Locale.ROOT,"%.6f",(starts[n+1]-starts[n])/1000000.0)).append(",\n").append(base).append("/mkv/").append(n).append(".m4s\n");
        text.append("#EXT-X-ENDLIST\n");byte[] data=text.toString().getBytes(StandardCharsets.UTF_8);if(data.length>1048576)throw new IOException("mkv_playlist_limit");return data;
    }
    byte[] resource(String suffix) throws IOException {
        synchronized(worker){
            check();if(suffix.equals("init.mp4"))return initialization;
            if(!suffix.matches("[0-9]{1,4}\\.m4s"))throw new IOException("mkv_unknown_resource");
            int index=Integer.parseInt(suffix.substring(0,suffix.length()-4));if(starts==null || index>=starts.length-1)throw new IOException("mkv_segment_out_of_range");
            byte[] bytes=fragments.get(index);if(bytes!=null)return bytes;
            long readBudget=0;boolean budgetInstalled=false;long entered=System.nanoTime();
            InfinityCastDiagnostics.event("mkv_request","started",index);
            try{readBudget=InfinityCastRemuxNative.readBudget(handle,index);if(readBudget<33554432L || readBudget>134217728L)throw new IOException("mkv_source_budget_invalid");input.budget(readBudget);budgetInstalled=true;bytes=InfinityCastRemuxNative.segment(handle,index);check();if(bytes==null || bytes.length==0 || bytes.length>8388608)throw new IOException("mkv_fragment_limit");}
            catch(IOException error){
                IOException actual=budgetInstalled?failure(error):error;
                String nativeCode=error.getMessage(),code=actual.getMessage();
                boolean explicitCancel="mkv_cancelled".equals(nativeCode)||"cast_hw_video_cancelled".equals(nativeCode);
                InfinityCastDiagnostics.event("mkv_request",cancelled?(explicitCancel?"cancelled_after_close":"failed_during_close"):"generation_failed",index);
                InfinityCastDiagnostics.event("mkv_request","close_flag_observed",cancelled?1:0);
                // Preserve both observed outcomes; concurrent close proves no cause.
                if(nativeCode!=null&&nativeCode.matches("(?:mkv_|cast_hw_)[a-z0-9_]{1,55}"))InfinityCastDiagnostics.event("mkv_native_failure",nativeCode,index);
                if(code!=null&&code.matches("(?:mkv_|cast_hw_)[a-z0-9_]{1,55}"))InfinityCastDiagnostics.event("mkv_failure",code,index);
                throw actual;
            }
            finally{InfinityCastDiagnostics.event("mkv_request","elapsed_ms",(int)Math.min(Integer.MAX_VALUE,(System.nanoTime()-entered)/1000000));reportSource(index,readBudget,budgetInstalled);}
            while(fragments.size()>=2)fragments.remove(fragments.keySet().iterator().next());fragments.put(index,bytes);
            InfinityCastDiagnostics.event("mkv_fragment","copied",index);InfinityCastDiagnostics.event("mkv_request","generated_bytes",bytes.length);return bytes;
        }
    }
    /** Numeric-only, bounded best-effort outcome reporting; never masks the request failure. */
    private void reportSource(int index,long budget,boolean budgetInstalled){
        try{
            long[] nativeStats=InfinityCastRemuxNative.sourceStats(handle),origin=budgetInstalled?input.usage():new long[0];
            InfinityCastDiagnostics.event("mkv_source","fragment_index",index);
            InfinityCastDiagnostics.event("mkv_source","read_budget_bytes",(int)budget);
            if(origin.length==4){InfinityCastDiagnostics.event("mkv_source","bytes_consumed",(int)origin[0]);InfinityCastDiagnostics.event("mkv_source","seek_count",(int)Math.min(Integer.MAX_VALUE,origin[1]));InfinityCastDiagnostics.event("mkv_source","range_requests",(int)Math.min(Integer.MAX_VALUE,origin[2]));}
            if(budgetInstalled && nativeStats!=null && nativeStats.length==7 && nativeStats[0]==index){String[] phases={"aac_bytes","preroll_bytes","selected_bytes","lookahead_bytes"};for(int n=0;n<4;n++)InfinityCastDiagnostics.event("mkv_source",phases[n],(int)nativeStats[n+1]);}
            if(budgetInstalled && "mkv_source_read_limit".equals(input.failure()))InfinityCastDiagnostics.event("mkv_source","budget_exhausted",1);
        }catch(IOException|RuntimeException|OutOfMemoryError unavailable){/* Logging cannot change playback/cancellation outcomes. */}
    }
    /** Called immediately on cancel; never waits for the worker/native mutex. */
    void cancel(){cancelled=true;InfinityCastHardwareVideo hw=hardwareVideo;if(hw!=null)hw.cancel();long current=handle;if(current!=0)InfinityCastRemuxNative.cancel(current);}
    /** Relay invokes this only after every admitted probe/serve job retired. */
    @Override public void close(){
        cancel();synchronized(worker){if(hardwareVideo!=null){try{hardwareVideo.close();}catch(IOException unresolved){input.close();fragments.clear();initialization=null;master=null;throw new IllegalStateException("cast_hw_resources_not_retired",unresolved);}hardwareVideo=null;}long current=handle;handle=0;if(current!=0)InfinityCastRemuxNative.close(current);input.close();fragments.clear();initialization=null;starts=null;master=null;codecs=null;}
        InfinityCastDiagnostics.event("mkv_context","retired",InfinityCastRemuxNative.active());
    }
}
