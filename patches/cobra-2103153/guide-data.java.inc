// @replace loadGuideAsync
  private void loadGuideAsync(LiveSource source) {
    if (source == null || !isCobraAsyncAlive() || !mFeatures.sourceEnabled(source.id)) return;
    final String identity = cobraEpgIdentity(source);
    if (identity.equals(mCobraEpgRequest.get(source.id))) return;
    CobraEpgData current = mCobraEpg.get(source.id);
    if (current != null && identity.equals(current.identity)
        && System.currentTimeMillis() - current.fetched < COBRA_GUIDE_TTL_MS) return;
    Long attempt=mCobraEpgLastAttempt.get(source.id+"|"+identity);
    if(attempt!=null&&System.currentTimeMillis()-attempt<60000L)return;
    mCobraEpgLastAttempt.put(source.id+"|"+identity,System.currentTimeMillis());
    mCobraEpgRequest.put(source.id, identity);
    mCobraEpgStatus.put(source.id, current == null ? "Loading guide…" : "Updating saved guide…");
    final ArrayList<String> urls = cobraEpgUrls(source);
    if (!submitCobraIo(() -> {
      CobraEpgData saved = cobraReadEpgCache(source.id, identity);
      if (saved != null) publishCobraUi(() -> {
        if (cobraEpgRequestCurrent(source, identity)) cobraInstallEpg(source.id, saved, "Saved guide");
      });
      if (saved != null && System.currentTimeMillis() - saved.fetched < COBRA_GUIDE_TTL_MS) {
        publishCobraUi(() -> {
          boolean valid=cobraEpgRequestCurrent(source,identity);
          if(identity.equals(mCobraEpgRequest.get(source.id)))mCobraEpgRequest.remove(source.id);
          if (valid) { mCobraEpgStatus.put(source.id, saved.truncated?"Guide ready • partial source":"Guide ready");
            cobraRefreshProgrammeLabels();
          }
        });
        return;
      }
      CobraEpgData fresh = new CobraEpgData();
      fresh.identity = identity;
      String error = urls.isEmpty() ? "No guide source configured" : "Guide unavailable";
      boolean fetchedAny = false;
      for (String url : urls) {
        if (!isCobraAsyncAlive() || Thread.currentThread().isInterrupted()) return;
        try {
          CobraEpgData incoming = cobraDownloadEpg(url);
          cobraMergeEpg(fresh, incoming);
          fetchedAny = true;
        } catch (Exception failure) {
          error = cobraGuideFailure(failure);
        }
      }
      final boolean ok = fetchedAny && !fresh.programs.isEmpty();
      final String resultStatus = ok ? (fresh.truncated ? "Guide ready • partial source" : "Guide ready")
          : fetchedAny ? "Provider returned no programme schedule" : error;
      fresh.fetched = System.currentTimeMillis();
      if (ok) cobraWriteEpgCache(source.id, fresh);
      publishCobraUi(() -> {
        boolean valid=cobraEpgRequestCurrent(source,identity);
        if(identity.equals(mCobraEpgRequest.get(source.id)))mCobraEpgRequest.remove(source.id);
        if (!valid) return;
        if (ok) cobraInstallEpg(source.id, fresh, resultStatus);
        else {
          boolean cached = mCobraEpg.containsKey(source.id);
          mCobraEpgStatus.put(source.id, cached ? "Saved guide • refresh unavailable" : resultStatus);
          cobraRefreshProgrammeLabels();
          if (mCobraGuideAdapter != null) mCobraGuideAdapter.notifyDataSetChanged();
          if (mGuidePreviewChannel != null) cobraRequestShortEpg(mGuidePreviewChannel);
        }
      });
    })) {
      mCobraEpgRequest.remove(source.id);
      mCobraEpgStatus.put(source.id, "Guide request cancelled");
    }
  }

// @replace programFor
  private ProgramPair programFor(Channel channel) {
    ArrayList<GuideProgram> programs = cobraPrograms(channel);
    if (programs == null || programs.isEmpty()) return null;
    long time = System.currentTimeMillis();
    ProgramPair pair = new ProgramPair();
    for (GuideProgram p : programs) {
      if (p.start <= time && p.stop > time) pair.now = p.title;
      else if (p.start > time) { pair.next = p.title; pair.nextStart = p.start; break; }
    }
    return pair;
  }

// @replace parseXmlTvTime
  private long parseXmlTvTime(String value) { return CobraGuideMath.parseTime(value); }

// @replace guideTitleAt
  private String guideTitleAt(Channel channel, long instant) {
    ArrayList<GuideProgram> programs = cobraPrograms(channel);
    if (programs != null) for (GuideProgram p : programs)
      if (p.start <= instant && p.stop > instant) return p.title;
    return cobraGuideStatus(channel);
  }

// @append
  private static final class CobraGuideMath {
    static final Pattern TIME = Pattern.compile("^(\\d{12}|\\d{14})(?:\\s*([+-]\\d{4}|Z))?$");
    static final ThreadLocal<SimpleDateFormat> CLOCK=new ThreadLocal<SimpleDateFormat>() {
      @Override protected SimpleDateFormat initialValue(){SimpleDateFormat f=new SimpleDateFormat("yyyyMMddHHmmss Z",Locale.US);f.setLenient(false);f.setTimeZone(TimeZone.getTimeZone("UTC"));return f;}
    };
    static String id(String value) {
      if (value == null) return "";
      String s = value.trim();
      return "null".equalsIgnoreCase(s) ? "" : s;
    }
    static String alias(String value) { return id(value).replaceAll("\\s+", " ").toLowerCase(Locale.ROOT); }
    static long parseTime(String value) {
      if (value == null) return 0;
      String s = value.trim();
      java.util.regex.Matcher m = TIME.matcher(s);
      if (!m.matches()) return 0;
      String digits = m.group(1); String zone = m.group(2);
      if (zone == null || "Z".equals(zone)) zone = "+0000";
      int zh = Integer.parseInt(zone.substring(1, 3)), zm = Integer.parseInt(zone.substring(3, 5));
      if (zh > 23 || zm > 59) return 0;
      if (digits.length() == 12) digits += "00";
      try {
        SimpleDateFormat f = CLOCK.get();
        java.text.ParsePosition pos = new java.text.ParsePosition(0);
        String input = digits + " " + zone;
        Date date = f.parse(input, pos);
        return date != null && pos.getIndex() == input.length() ? date.getTime() : 0;
      } catch (RuntimeException invalid) { return 0; }
    }
    static float progress(long start, long stop, long now) {
      if (stop <= start) return 0f;
      return (float)Math.max(0d, Math.min(1d, (double)(now - start) / (double)(stop - start)));
    }
    static float[] interval(long start, long stop, long window, long duration) {
      if (duration <= 0 || stop <= start || stop <= window || start >= window + duration) return null;
      return new float[]{(float)Math.max(0d, (double)(start - window) / duration),
          (float)Math.min(1d, (double)(stop - window) / duration)};
    }
    static void alias(Map<String,String> aliases, String name, String canonical) {
      String key = alias(name);
      if (key.isEmpty() || canonical == null || canonical.isEmpty() || (aliases.size()>=100000&&!aliases.containsKey(key))) return;
      String previous = aliases.get(key);
      // An ambiguous alias never chooses an arbitrary regional channel.
      if (previous == null) aliases.put(key, canonical);
      else if (!previous.equals(canonical)) aliases.put(key, "");
    }
  }

  private static final class CobraEpgData {
    String identity = "";
    long fetched = 0L;
    boolean truncated = false;
    final Map<String, ArrayList<GuideProgram>> programs = new HashMap<>();
    final Map<String, String> aliases = new HashMap<>();
  }

  private String cobraDigest(String text) {
    try {
      byte[] b = java.security.MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8));
      StringBuilder out = new StringBuilder();
      for (byte v : b) out.append(String.format(Locale.US, "%02x", v & 255));
      return out.toString();
    } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
  }

  private ArrayList<String> cobraEpgUrls(LiveSource source) {
    ArrayList<String> urls = new ArrayList<>();
    // A custom guide must be attempted even when the provider guide is absent or fails.
    String custom = mPrefs.getString("cobra_custom_epg:" + source.id, "");
    if (custom != null && !custom.trim().isEmpty()) urls.add(custom.trim());
    try {
      String normal = "xtream".equals(source.type) ? xtreamEpgUrl(source) : source.epgUrl;
      if (normal != null && !normal.trim().isEmpty() && !urls.contains(normal.trim())) urls.add(normal.trim());
      if ("m3u".equals(source.type)) {
        String detected = mPrefs.getString("cobra_epg_discovered|" + source.id, "");
        if (detected != null && !detected.isEmpty() && !urls.contains(detected)) urls.add(detected);
        Uri playlist = Uri.parse(source.playlistUrl);
        String path = playlist.getPath();
        if (path != null && path.endsWith("/get.php")) {
          String u = playlist.getQueryParameter("username"), p = playlist.getQueryParameter("password");
          if (u != null && p != null) {
            String epg = playlist.buildUpon().path(path.substring(0, path.length()-7)+"xmltv.php")
                .clearQuery().appendQueryParameter("username", u).appendQueryParameter("password", p).build().toString();
            if (!urls.contains(epg)) urls.add(epg);
          }
        }
      }
    } catch (Exception ignored) { /* no speculative requests to other providers */ }
    return urls;
  }

  private String cobraEpgIdentity(LiveSource source) {
    return cobraDigest(source.toJson().toString() + "\n" + cobraEpgUrls(source).toString());
  }

  private boolean cobraEpgRequestCurrent(LiveSource source, String identity) {
    if (!isCobraAsyncAlive() || !mFeatures.sourceEnabled(source.id)
        || !identity.equals(mCobraEpgRequest.get(source.id))) return false;
    for (LiveSource active : mSources)
      if (active.id.equals(source.id)) return identity.equals(cobraEpgIdentity(active));
    return false;
  }

  private void cobraDiscoverPlaylistGuide(LiveSource source, String playlist) {
    if (source == null || playlist == null) return;
    int newline = playlist.indexOf('\n');
    String header = playlist.substring(0, Math.min(playlist.length(), newline < 0 ? 4096 : Math.min(4096,newline)));
    Matcher match = Pattern.compile("(?:x-tvg-url|url-tvg|tvg-url)\\s*=\\s*[\"']([^\"']+)[\"']", Pattern.CASE_INSENSITIVE).matcher(header);
    if (!match.find()) return;
    String value = match.group(1).split(",", 2)[0].trim();
    try {
      URL resolved = new URL(new URL(source.playlistUrl), value);
      if (!"http".equals(resolved.getProtocol()) && !"https".equals(resolved.getProtocol())) return;
      mPrefs.edit().putString("cobra_epg_discovered|" + source.id, resolved.toString()).apply();
    } catch (Exception ignored) { }
  }

  private final class CobraBoundedGuideStream extends java.io.FilterInputStream {
    long remaining = 128L * 1024L * 1024L;
    CobraBoundedGuideStream(InputStream stream) { super(stream); }
    private void consume(int n) throws java.io.IOException {
      if (mCobraAsyncDestroyed || Thread.currentThread().isInterrupted()) throw new java.io.InterruptedIOException();
      if (n > 0 && (remaining -= n) < 0) throw new java.io.IOException("Guide size limit");
    }
    @Override public int read() throws java.io.IOException { int n=super.read(); consume(n<0?0:1); return n; }
    @Override public int read(byte[] b,int off,int len) throws java.io.IOException {
      int n=in.read(b,off,len); consume(n); return n;
    }
  }

  private CobraEpgData cobraDownloadEpg(String address) throws Exception {
    URL url = new URL(address);
    if (!"http".equals(url.getProtocol()) && !"https".equals(url.getProtocol()))
      throw new java.io.IOException("Unsupported guide protocol");
    HttpURLConnection c = (HttpURLConnection) url.openConnection();
    c.setConnectTimeout(15000); c.setReadTimeout(30000); c.setInstanceFollowRedirects(true);
    c.setRequestProperty("User-Agent", "Infinity Cobra/3.0");
    c.setRequestProperty("Accept-Encoding", "gzip");
    try {
      int code = c.getResponseCode();
      if (code < 200 || code >= 300) throw new LiveException("Guide HTTP " + code);
      try (BufferedInputStream raw = new BufferedInputStream(c.getInputStream())) {
        raw.mark(4); int a=raw.read(),b=raw.read(); raw.reset();
        // Covers .xml.gz sources without Content-Encoding as well as normal HTTP gzip.
        InputStream input = a==0x1f && b==0x8b ? new GZIPInputStream(raw) : raw;
        return cobraParseGuide(new CobraBoundedGuideStream(input));
      }
    } finally { c.disconnect(); }
  }

  private CobraEpgData cobraParseGuide(InputStream input) throws Exception {
    CobraEpgData data = new CobraEpgData();
    XmlPullParser parser = Xml.newPullParser();
    try { parser.setFeature("http://xmlpull.org/v1/doc/features.html#process-docdecl", false); }
    catch (org.xmlpull.v1.XmlPullParserException unsupported) { }
    parser.setInput(input, null);
    GuideProgram programme = null;
    String channel = "", reading = "";
    StringBuilder content = new StringBuilder();
    boolean tvRoot = false;
    int count = 0;
    Map<String,GuideProgram> requiredNow=new HashMap<>(),requiredNext=new HashMap<>();
    long now = System.currentTimeMillis(), min = now - 8L*86400000L, max = now + 8L*86400000L;
    for (int event=parser.getEventType(); event!=XmlPullParser.END_DOCUMENT; event=parser.next()) {
      if (mCobraAsyncDestroyed || Thread.currentThread().isInterrupted()) throw new java.io.InterruptedIOException();
      if (event == XmlPullParser.START_TAG) {
        String tag=parser.getName();
        if ("tv".equals(tag)) tvRoot=true;
        else if ("channel".equals(tag) && programme==null) {
          channel=cobraBoundedId(parser.getAttributeValue(null,"id"));
          CobraGuideMath.alias(data.aliases, channel, channel);
        } else if ("programme".equals(tag)) {
          programme=new GuideProgram(); programme.channel=cobraBoundedId(parser.getAttributeValue(null,"channel"));
          programme.start=parseXmlTvTime(parser.getAttributeValue(null,"start"));
          programme.stop=parseXmlTvTime(parser.getAttributeValue(null,"stop"));
        } else if ((programme!=null && ("title".equals(tag)||"desc".equals(tag)))
            || (!channel.isEmpty() && "display-name".equals(tag))) { reading=tag; content.setLength(0); }
      } else if (event==XmlPullParser.TEXT && !reading.isEmpty()) {
        if (content.length()<4096) content.append(parser.getText(),0,Math.min(parser.getText().length(),4096-content.length()));
      } else if (event==XmlPullParser.END_TAG) {
        String tag=parser.getName();
        if (tag.equals(reading)) {
          String text=content.toString().trim();
          if(text.length()>("desc".equals(tag)?2048:512))text=text.substring(0,"desc".equals(tag)?2048:512);
          if (programme!=null && "title".equals(tag) && programme.title.isEmpty()) programme.title=text;
          else if (programme!=null && "desc".equals(tag) && programme.description.isEmpty()) programme.description=text;
          else if ("display-name".equals(tag)) CobraGuideMath.alias(data.aliases,text,channel);
          reading="";
        }
        if ("programme".equals(tag) && programme!=null) {
          if (!programme.channel.isEmpty() && programme.start>0 && programme.stop>programme.start
              && programme.stop>=min && programme.start<=max) {
            // Reserve Now/Next for every channel even if the optional historical schedule hits its cap.
            if(requiredNow.containsKey(programme.channel)||requiredNow.size()<20000)
              if(programme.start<=now&&programme.stop>now)requiredNow.put(programme.channel,programme);
            if(requiredNext.containsKey(programme.channel)||requiredNext.size()<20000)
              if(programme.start>now&&(requiredNext.get(programme.channel)==null||programme.start<requiredNext.get(programme.channel).start))requiredNext.put(programme.channel,programme);
            if (count < 300000 && (data.programs.containsKey(programme.channel)||data.programs.size()<20000)) {
              ArrayList<GuideProgram> list=data.programs.get(programme.channel);
              if(list==null) { list=new ArrayList<>(); data.programs.put(programme.channel,list); }
              if(list.size()<1024) { list.add(programme); count++; } else data.truncated=true;
              CobraGuideMath.alias(data.aliases,programme.channel,programme.channel);
            } else data.truncated=true;
          }
          programme=null; reading="";
        } else if ("channel".equals(tag)) channel="";
      }
    }
    if (!tvRoot) throw new java.io.IOException("Response is not XMLTV");
    ArrayList<GuideProgram> essential=new ArrayList<>(requiredNow.values());essential.addAll(requiredNext.values());
    for(GuideProgram p:essential){ArrayList<GuideProgram> list=data.programs.get(p.channel);if(list==null){list=new ArrayList<>();data.programs.put(p.channel,list);}if(!list.contains(p))list.add(p);CobraGuideMath.alias(data.aliases,p.channel,p.channel);}
    for (ArrayList<GuideProgram> list:data.programs.values())
      Collections.sort(list,(a,b)->Long.compare(a.start,b.start));
    return data;
  }

  private void cobraMergeEpg(CobraEpgData into, CobraEpgData incoming) {
    for (Map.Entry<String,ArrayList<GuideProgram>> entry:incoming.programs.entrySet())
      if (!into.programs.containsKey(entry.getKey())) into.programs.put(entry.getKey(),entry.getValue());
    for (Map.Entry<String,String> entry:incoming.aliases.entrySet())
      if (!into.aliases.containsKey(entry.getKey())) into.aliases.put(entry.getKey(),entry.getValue());
    into.truncated |= incoming.truncated;
  }

  private File cobraEpgCacheFile(String sourceId) {
    return new File(getFilesDir(), (sourceId.startsWith("@short:")?"cobra-epg-short-v3-":"cobra-epg-v3-")+cobraDigest(sourceId).substring(0,24)+".bin");
  }

  private CobraEpgData cobraReadEpgCache(String sourceId,String identity) {
    android.util.AtomicFile file=new android.util.AtomicFile(cobraEpgCacheFile(sourceId));
    try (java.io.DataInputStream in=new java.io.DataInputStream(
        new GZIPInputStream(new BufferedInputStream(file.openRead())))) {
      if(in.readInt()!=0x43475033 || !identity.equals(in.readUTF())) return null;
      CobraEpgData data=new CobraEpgData(); data.identity=identity; data.fetched=in.readLong();data.truncated=in.readBoolean();
      if(data.fetched>System.currentTimeMillis()+60000 || System.currentTimeMillis()-data.fetched>8L*86400000L) return null;
      int aliasCount=in.readInt(); if(aliasCount<0||aliasCount>100000) return null;
      for(int i=0;i<aliasCount;i++) data.aliases.put(in.readUTF(),in.readUTF());
      int count=in.readInt(); if(count<0||count>400000) return null;
      for(int i=0;i<count;i++) {
        GuideProgram p=new GuideProgram(); p.channel=in.readUTF(); p.title=in.readUTF(); p.description=in.readUTF();
        p.start=in.readLong();p.stop=in.readLong();
        if(p.stop<=p.start) continue;
        ArrayList<GuideProgram> list=data.programs.get(p.channel);
        if(list==null){list=new ArrayList<>();data.programs.put(p.channel,list);}list.add(p);
      }
      for(ArrayList<GuideProgram> list:data.programs.values()) Collections.sort(list,(a,b)->Long.compare(a.start,b.start));
      return data;
    } catch(Exception ignored) { return null; }
  }

  private void cobraWriteEpgCache(String sourceId,CobraEpgData data) {
    android.util.AtomicFile file=new android.util.AtomicFile(cobraEpgCacheFile(sourceId));
    java.io.FileOutputStream stream=null;
    try {
      stream=file.startWrite();
      java.util.zip.GZIPOutputStream gzip=new java.util.zip.GZIPOutputStream(stream);
      java.io.DataOutputStream out=new java.io.DataOutputStream(gzip);
      out.writeInt(0x43475033);out.writeUTF(data.identity);out.writeLong(data.fetched);out.writeBoolean(data.truncated);
      out.writeInt(data.aliases.size());
      for(Map.Entry<String,String> e:data.aliases.entrySet()){out.writeUTF(e.getKey());out.writeUTF(e.getValue());}
      int count=0;for(ArrayList<GuideProgram> list:data.programs.values()) count+=list.size();out.writeInt(count);
      for(ArrayList<GuideProgram> list:data.programs.values()) for(GuideProgram p:list){
        out.writeUTF(p.channel);out.writeUTF(p.title);out.writeUTF(p.description);out.writeLong(p.start);out.writeLong(p.stop);
      }
      out.flush();gzip.finish();file.finishWrite(stream);stream=null;
      if(sourceId.startsWith("@short:"))cobraPruneShortGuideCache();
    } catch(Exception ignored) { if(stream!=null)file.failWrite(stream); }
  }

  private void cobraInstallEpg(String sourceId,CobraEpgData data,String statusText) {
    CobraEpgData previous=mCobraEpg.get(sourceId);
    if(previous!=null&&previous.identity.equals(data.identity))for(Map.Entry<String,ArrayList<GuideProgram>> e:previous.programs.entrySet())if(e.getKey().startsWith("@stream:"))data.programs.put(e.getKey(),e.getValue());
    mCobraEpg.put(sourceId,data);mCobraEpgStatus.put(sourceId,statusText);mCobraResolvedEpg.clear();
    // Preserve compatibility with schedule/reminder/catch-up consumers, without redrawing the player.
    String prefix=sourceId+"|";
    java.util.Iterator<String> keys=mGuidePrograms.keySet().iterator();
    while(keys.hasNext())if(keys.next().startsWith(prefix))keys.remove();
    for(Map.Entry<String,ArrayList<GuideProgram>> e:data.programs.entrySet())mGuidePrograms.put(prefix+e.getKey(),e.getValue());
    cobraRefreshProgrammeLabels();cobraQueueVisibleGuides();
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
    if(mCobraPlayerDrawerList!=null && mCobraPlayerDrawerList.getAdapter() instanceof android.widget.BaseAdapter)
      ((android.widget.BaseAdapter)mCobraPlayerDrawerList.getAdapter()).notifyDataSetChanged();
  }

  private String cobraResolveEpg(Channel channel) {
    if(channel==null)return "";
    String source=sourceIdForChannel(channel);CobraEpgData data=mCobraEpg.get(source);
    if(data==null)return "";
    String cached=mCobraResolvedEpg.get(channel.id);if(cached!=null)return cached;
    String epg=CobraGuideMath.id(channel.epgId),key="";
    if(data.programs.containsKey("@stream:"+channel.id))key="@stream:"+channel.id;
    else if(!epg.isEmpty()&&data.programs.containsKey(epg))key=epg;
    else {
      String alias=data.aliases.get(CobraGuideMath.alias(epg));
      if(alias==null||alias.isEmpty())alias=data.aliases.get(CobraGuideMath.alias(channel.name));
      if(alias!=null&&!alias.isEmpty()&&data.programs.containsKey(alias))key=alias;
    }
    mCobraResolvedEpg.put(channel.id,key);return key;
  }

  private ArrayList<GuideProgram> cobraPrograms(Channel channel) {
    if(channel==null)return null;
    CobraEpgData data=mCobraEpg.get(sourceIdForChannel(channel));
    return data==null?null:data.programs.get(cobraResolveEpg(channel));
  }

  private GuideProgram cobraCurrentProgram(Channel channel) {
    ArrayList<GuideProgram> programs=cobraPrograms(channel);long now=System.currentTimeMillis();
    if(programs!=null)for(GuideProgram p:programs){if(p.start>now)break;if(p.stop>now)return p;}
    return null;
  }

  private GuideProgram cobraNextProgram(Channel channel) {
    ArrayList<GuideProgram> programs=cobraPrograms(channel);long now=System.currentTimeMillis();
    if(programs!=null)for(GuideProgram p:programs)if(p.start>now)return p;
    return null;
  }

  private String cobraGuideStatus(Channel channel) {
    if(channel==null)return "Choose a channel";
    String source=sourceIdForChannel(channel);
    if(mCobraShortEpgBusy.contains(channel.id))return "Loading channel schedule…";
    String shortStatus=mCobraShortEpgStatus.get(channel.id);
    if(shortStatus!=null && cobraPrograms(channel)==null)return shortStatus;
    String state=mCobraEpgStatus.get(source);
    if(mCobraEpgRequest.containsKey(source)&&!mCobraEpg.containsKey(source))return "Loading guide…";
    if(!mCobraEpg.containsKey(source))return state==null?"Guide not loaded yet":state;
    if(cobraResolveEpg(channel).isEmpty())return "No matching programme ID";
    return "No programme scheduled for this time";
  }

  private String cobraGuideFailure(Exception e) {
    if(e instanceof LiveException && ((LiveException)e).userMessage.startsWith("Guide HTTP "))return ((LiveException)e).userMessage;
    if(e instanceof java.net.SocketTimeoutException)return "Guide server timed out";
    if(e instanceof java.net.UnknownHostException)return "Guide server not found";
    if(e instanceof javax.net.ssl.SSLException)return "Guide secure connection failed";
    if(e instanceof java.io.InterruptedIOException)return "Guide request cancelled";
    if(e instanceof org.xmlpull.v1.XmlPullParserException)return "Guide response is not valid XMLTV";
    return "Guide could not be read";
  }

  private String cobraDecodeEpgTitle(String encoded) {
    if(encoded==null)return "";
    String raw=encoded.trim();
    if(raw.length()<4 || raw.length()%4!=0 || !raw.matches("[A-Za-z0-9+/]+={0,2}"))return raw;
    try {
      byte[] bytes=android.util.Base64.decode(raw,android.util.Base64.DEFAULT);
      String decoded=new String(bytes,StandardCharsets.UTF_8);
      if(decoded.indexOf('\ufffd')>=0 || decoded.matches(".*[\\x00-\\x08\\x0E-\\x1F].*"))return raw;
      return decoded;
    }catch(IllegalArgumentException notBase64){return raw;}
  }

  private void cobraRequestShortEpg(Channel channel) {
    if(channel==null||!isCobraAsyncAlive()||mCobraShortEpgBusy.contains(channel.id)||mCobraShortEpgBusy.size()>=2)return;
    if(cobraCurrentProgram(channel)!=null && cobraNextProgram(channel)!=null)return;
    long now=System.currentTimeMillis();Long last=mCobraShortEpgAttempt.get(channel.id);
    if(last!=null&&now-last<15L*60000L)return;
    String sourceId=sourceIdForChannel(channel);LiveSource chosen=null;
    for(LiveSource s:mSources)if(s.id.equals(sourceId)&&"xtream".equals(s.type)){chosen=s;break;}
    if(chosen==null)return;
    final LiveSource source=chosen;final String identity=cobraEpgIdentity(source);
    final String stream=channel.id.substring(sourceId.length()+1);
    mCobraShortEpgBusy.add(channel.id);mCobraShortEpgAttempt.put(channel.id,now);
    if(!submitCobraIo(()->{
      ArrayList<GuideProgram> result=new ArrayList<>();String failure="Provider has no schedule for this channel";
      try {
        CobraEpgData cached=cobraReadEpgCache("@short:"+channel.id,identity);
        if(cached!=null&&System.currentTimeMillis()-cached.fetched<15L*60000L&&cached.programs.containsKey("@stream:"+channel.id))result.addAll(cached.programs.get("@stream:"+channel.id));
        if(result.isEmpty()) {
        JSONObject payload=new JSONObject(httpGet(xtreamUrl(source,"get_short_epg")+"&stream_id="+enc(stream)+"&limit=24"));
        JSONArray entries=payload.optJSONArray("epg_listings");
        if(entries!=null)for(int i=0;i<Math.min(48,entries.length());i++){
          JSONObject o=entries.optJSONObject(i);if(o==null)continue;
          GuideProgram p=new GuideProgram();p.channel="@stream:"+channel.id;
          p.title=cobraDecodeEpgTitle(o.optString("title",""));p.description=cobraDecodeEpgTitle(o.optString("description",""));
          p.start=o.optLong("start_timestamp",0)*1000L;p.stop=o.optLong("stop_timestamp",o.optLong("end_timestamp",0))*1000L;
          // Do not guess a provider's timezone from ambiguous wall-clock strings.
          if(p.start>0&&p.stop>p.start&&!p.title.isEmpty())result.add(p);
        }
        Collections.sort(result,(a,b)->Long.compare(a.start,b.start));
        if(!result.isEmpty()){CobraEpgData stored=new CobraEpgData();stored.identity=identity;stored.fetched=System.currentTimeMillis();stored.programs.put("@stream:"+channel.id,result);cobraWriteEpgCache("@short:"+channel.id,stored);}
        }
      }catch(Exception e){failure="Channel schedule unavailable";}
      final String state=failure;
      publishCobraUi(()->{
        mCobraShortEpgBusy.remove(channel.id);
        boolean current=false;for(LiveSource s:mSources)if(s.id.equals(source.id)&&identity.equals(cobraEpgIdentity(s)))current=true;
        if(!current||!mFeatures.sourceEnabled(source.id))return;
        if(!result.isEmpty()){
          CobraEpgData data=mCobraEpg.get(source.id);if(data==null){data=new CobraEpgData();data.identity=identity;mCobraEpg.put(source.id,data);}
          data.programs.put("@stream:"+channel.id,result);mCobraResolvedEpg.remove(channel.id);
          mGuidePrograms.put(source.id+"|@stream:"+channel.id,result);mCobraShortEpgStatus.remove(channel.id);
        }else mCobraShortEpgStatus.put(channel.id,state);
        cobraRefreshProgrammeLabels();cobraQueueVisibleGuides();if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
        if(mCobraPlayerDrawerList!=null&&mCobraPlayerDrawerList.getAdapter() instanceof android.widget.BaseAdapter)
          ((android.widget.BaseAdapter)mCobraPlayerDrawerList.getAdapter()).notifyDataSetChanged();
      });
    }))mCobraShortEpgBusy.remove(channel.id);
  }

  private String cobraBoundedId(String value) {String id=CobraGuideMath.id(value);return id.length()>512?"":id;}
  private void cobraPruneShortGuideCache() {
    long now=System.currentTimeMillis();if(now-mCobraLastCachePrune<60000)return;mCobraLastCachePrune=now;
    File[] files=getFilesDir().listFiles((dir,name)->name.startsWith("cobra-epg-short-v3-")&&name.endsWith(".bin"));if(files==null||files.length<=256)return;
    java.util.Arrays.sort(files,(a,b)->Long.compare(b.lastModified(),a.lastModified()));for(int i=256;i<files.length;i++)new android.util.AtomicFile(files[i]).delete();
  }
  private void cobraQueueVisibleGuides() {mMain.removeCallbacks(mCobraVisibleGuideFetch);if(isCobraAsyncAlive())mMain.postDelayed(mCobraVisibleGuideFetch,700L);}
  private void cobraFetchVisibleGuides() {
    if(!isCobraAsyncAlive()||mBackgroundStopped)return;
    android.widget.AbsListView list=mCobraPlayerDrawerList!=null?mCobraPlayerDrawerList:mCobraGuideList;
    if(list==null||!list.isShown()||list.getAdapter()==null)return;
    int start=Math.max(0,list.getFirstVisiblePosition()),end=Math.min(list.getAdapter().getCount(),Math.min(start+6,list.getLastVisiblePosition()+1));
    for(int i=start;i<end;i++){Object item=list.getAdapter().getItem(i);if(item instanceof Channel) {Channel c=(Channel)item;if(!mCobraEpgRequest.containsKey(sourceIdForChannel(c)))cobraRequestShortEpg(c);}}
  }
