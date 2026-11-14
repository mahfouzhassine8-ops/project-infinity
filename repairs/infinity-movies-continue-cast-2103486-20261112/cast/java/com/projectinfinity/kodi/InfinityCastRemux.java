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
                JSONArray times=metadata.getJSONArray("starts_us");if(times.length()<2 || times.length()>8193)throw new IOException("mkv_seek_index_limit");
                starts=new long[times.length()];for(int n=0;n<starts.length;n++){starts[n]=times.getLong(n);if(starts[n]<0 || (n>0 && starts[n]<=starts[n-1]))throw new IOException("mkv_invalid_seek_index");}
                if(starts[0]!=0 || starts[starts.length-1]!=metadata.getLong("duration_us"))throw new IOException("mkv_unverified_timeline");
                initialization=InfinityCastRemuxNative.init(handle);if(initialization==null || initialization.length<16 || initialization.length>1048576)throw new IOException("mkv_init_limit");
                codecs=metadata.optString("codecs","");
                if(!codecs.matches("(avc1\\.[0-9A-F]{6}|hev1\\.[ABC]?[0-9]+\\.[0-9A-F]+\\.[LH][0-9]+(?:\\.[0-9A-F]{2}){0,6})(?:,(?:mp4a\\.(?:40\\.[0-9]+|69|6B)|ac-3|ec-3))?"))throw new IOException("mkv_invalid_codec_description");
                if("hevc".equals(video)){String descriptor=codecs.split(",")[0];String[] fields=descriptor.split("\\.");InfinityCastDiagnostics.event("mkv_video_profile","hevc",Integer.parseInt(fields[1].replaceAll("[ABC]","")));InfinityCastDiagnostics.event("mkv_video_level",fields[3].startsWith("H")?"high_tier":"main_tier",Integer.parseInt(fields[3].substring(1)));}
                check();InfinityCastDiagnostics.event("mkv_inspection","stream_copy_ready",starts.length-1);
            }catch(IOException e){throw failure(e);}catch(Exception e){throw new IOException("mkv_inspection_failed");}
        }
    }
    private IOException failure(IOException error){String reason=input.failure();return reason.isEmpty()?error:new IOException(reason);}
    private void check() throws IOException{if(cancelled || handle==0)throw new IOException("mkv_cancelled");}
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
            try{input.budget(32L*1024*1024);bytes=InfinityCastRemuxNative.segment(handle,index);check();if(bytes==null || bytes.length==0 || bytes.length>8388608)throw new IOException("mkv_fragment_limit");}
            catch(IOException error){throw failure(error);}
            while(fragments.size()>=2)fragments.remove(fragments.keySet().iterator().next());fragments.put(index,bytes);
            InfinityCastDiagnostics.event("mkv_fragment","copied",index);return bytes;
        }
    }
    /** Called immediately on cancel; never waits for the worker/native mutex. */
    void cancel(){cancelled=true;long current=handle;if(current!=0)InfinityCastRemuxNative.cancel(current);}
    /** Relay invokes this only after every admitted probe/serve job retired. */
    @Override public void close(){
        cancel();synchronized(worker){long current=handle;handle=0;if(current!=0)InfinityCastRemuxNative.close(current);input.close();fragments.clear();initialization=null;starts=null;master=null;codecs=null;}
        InfinityCastDiagnostics.event("mkv_context","retired",InfinityCastRemuxNative.active());
    }
}
