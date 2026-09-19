  }
  private String cobraSmartBufferMode(){return CobraBufferPolicy.mode(mPrefs.getString(COBRA_SMART_BUFFER,"auto"));}
  private boolean cobraLocalTimeshiftEnabled(){return mPrefs.getBoolean(COBRA_LOCAL_TIMESHIFT,false);}
  private String cobraLocalTimeshiftLabel(){return cobraLocalTimeshiftEnabled()?"ON":"OFF";}
  private boolean cobraPlaybackDiagnosticsEnabled(){return mPrefs.getBoolean(COBRA_PLAYBACK_DIAGNOSTICS,false);}
  private boolean cobraIsHls(String url){return url!=null&&url.toLowerCase(Locale.US).contains(".m3u8");}
  private Channel cobraTimeshiftSessionChannel(Channel channel,String requested){
    if(channel==null||!cobraLiveRewindEnabled()||!cobraLocalTimeshiftEnabled()||!cobraLiveChannel(channel)||mCobraProviderCatchupActive||requested==null||!requested.equals(channel.primaryUrl))return channel;
    String hls=cobraIsHls(channel.primaryUrl)?channel.primaryUrl:cobraIsHls(channel.fallbackUrl)?channel.fallbackUrl:"";if(hls.isEmpty())return channel;String fallback=hls.equals(channel.primaryUrl)?channel.fallbackUrl:channel.primaryUrl;
    return new Channel(channel.id,channel.name,channel.group,channel.epgId,channel.icon,hls,fallback,channel.headers,channel.catchup,channel.catchupDays,channel.providerStreamId,channel.containerExtension,channel.catchupTimezone);
  }
  private void showCobraBufferingTimeshiftPicker(){
    LinearLayout rows=cobraOpenSheet("Live TV Buffering & Timeshift","Local timeshift keeps a bounded HLS window on this device; smart buffering controls forward reserve.","buffer-timeshift");boolean dark=cobraSheetIsDark();
    rows.addView(cobraSheetRow("recent","Local timeshift",cobraLocalTimeshiftEnabled()?"On • up to about 2 minutes / 160 MB":"Off",false,dark,()->{boolean next=!cobraLocalTimeshiftEnabled();SharedPreferences.Editor edit=mPrefs.edit().putBoolean(COBRA_LOCAL_TIMESHIFT,next);if(next)edit.putBoolean(COBRA_LIVE_REWIND_ENABLED,true);edit.apply();toast("Local timeshift • "+cobraLocalTimeshiftLabel()+" • applies next tune");showCobraBufferingTimeshiftPicker();}));
    rows.addView(cobraSheetRow("health","Smart buffering • Auto","auto".equals(cobraSmartBufferMode())?"Selected • Media3 default single-view buffering":"Media3 default single-view buffering",false,dark,()->{mPrefs.edit().putString(COBRA_SMART_BUFFER,"auto").apply();showCobraBufferingTimeshiftPicker();}));
    rows.addView(cobraSheetRow("health","Smart buffering • Resilient","resilient".equals(cobraSmartBufferMode())?"Selected • 20 s minimum • up to 90 s • 8 s refill":"20 s minimum • up to 90 s • 8 s refill after a stall",false,dark,()->{mPrefs.edit().putString(COBRA_SMART_BUFFER,"resilient").apply();showCobraBufferingTimeshiftPicker();}));
    cobraInfoText(rows,"No second player or duplicate provider stream is created. Local timeshift extends only simple HLS live playlists; unsupported/encrypted playlist formats fall back safely to the provider window.");
  }

  private static final class CobraHlsSegment {final long sequence,durationMs;final String uri;CobraHlsSegment(long s,long d,String u){sequence=s;durationMs=d;uri=u;}}
  private final class CobraTimeshiftStore {
    final File root;final Map<String,java.util.TreeMap<Long,CobraHlsSegment>> windows=new HashMap<>();final Map<String,ArrayList<File>> filesByUri=new HashMap<>();final Set<String> segmentUris=new HashSet<>();long bytes;boolean closed,extended;
    CobraTimeshiftStore(String channel){root=new File(getCacheDir(),"cobra-timeshift-"+Integer.toHexString(channel.hashCode())+"-"+Long.toHexString(android.os.SystemClock.elapsedRealtimeNanos()));root.mkdirs();}
    synchronized long retainedMs(){long best=0;for(java.util.TreeMap<Long,CobraHlsSegment> w:windows.values()){long total=0;for(CobraHlsSegment s:w.values())total+=s.durationMs;best=Math.max(best,total);}return best;}
    synchronized long retainedBytes(){return bytes;}
    boolean playlist(Uri uri){String p=uri==null?null:uri.getPath();return p!=null&&p.toLowerCase(Locale.US).contains(".m3u8");}
    synchronized boolean cacheable(Uri uri){return uri!=null&&segmentUris.contains(uri.toString());}
    String absolute(Uri base,String value){try{return new java.net.URI(base.toString()).resolve(value).toString();}catch(Exception ignored){return value;}}
    synchronized byte[] rewrite(Uri uri,byte[] raw){
      if(closed||raw==null)return raw;String text=new String(raw,StandardCharsets.UTF_8);if(!text.startsWith("#EXTM3U")||text.contains("#EXT-X-ENDLIST"))return raw;
      boolean simple=CobraTimeshiftPolicy.extendable(text);String[] lines=text.replace("\r","").split("\n");long baseSeq=0;ArrayList<String> global=new ArrayList<>();
      for(String line:lines){if(line.startsWith("#EXT-X-MEDIA-SEQUENCE:"))try{baseSeq=Long.parseLong(line.substring(line.indexOf(':')+1).trim());}catch(Exception ignored){}else if(line.startsWith("#EXT-X-VERSION:")||line.startsWith("#EXT-X-TARGETDURATION:")||line.startsWith("#EXT-X-INDEPENDENT-SEGMENTS"))if(!global.contains(line))global.add(line);}
      java.util.TreeMap<Long,CobraHlsSegment> window=windows.get(uri.toString());if(window==null){window=new java.util.TreeMap<>();windows.put(uri.toString(),window);}long seq=baseSeq;long duration=-1;
      for(String line:lines){String t=line.trim();if(t.startsWith("#EXTINF:")){try{String v=t.substring(8);int comma=v.indexOf(',');if(comma>=0)v=v.substring(0,comma);duration=Math.max(1L,Math.round(Double.parseDouble(v)*1000d));}catch(Exception ignored){duration=-1;}}else if(!t.isEmpty()&&!t.startsWith("#")&&duration>0){String absolute=absolute(uri,t);window.put(seq,new CobraHlsSegment(seq,duration,absolute));segmentUris.add(absolute);seq++;duration=-1;}}
      long total=0;for(CobraHlsSegment s:window.descendingMap().values()){total+=s.durationMs;if(total>CobraTimeshiftPolicy.WINDOW_MS){window.headMap(s.sequence,false).clear();break;}}
      if(window.size()<2||!simple)return raw;extended=true;StringBuilder out=new StringBuilder("#EXTM3U\n");for(String g:global)out.append(g).append('\n');out.append("#EXT-X-MEDIA-SEQUENCE:").append(window.firstKey()).append('\n');for(CobraHlsSegment s:window.values())out.append("#EXTINF:").append(String.format(Locale.US,"%.3f",s.durationMs/1000d)).append(",\n").append(s.uri).append('\n');return out.toString().getBytes(StandardCharsets.UTF_8);
    }
    synchronized String key(androidx.media3.datasource.DataSpec spec){String value=spec.uri+"|"+spec.position+"|"+spec.length;try{byte[] h=java.security.MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));StringBuilder b=new StringBuilder();for(byte v:h)b.append(String.format(Locale.US,"%02x",v&255));return b.toString();}catch(Exception ignored){return Integer.toHexString(value.hashCode());}}
    synchronized File cached(androidx.media3.datasource.DataSpec spec){File f=new File(root,key(spec)+".seg");return f.isFile()?f:null;}
