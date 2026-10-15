// STATE
  private final Map<String, String> mGuideLoadState = new HashMap<>();
  private final Map<String, Long> mGuideLoadEpoch = new HashMap<>();
  private final Map<String, String> mGuideAliases = new HashMap<>();
  private final Set<String> mGuideInFlight = new HashSet<>();
  private final Set<String> mGuideShortInFlight = new HashSet<>();
  private final Map<String, Long> mGuideShortLast = new HashMap<>();

// METHODS
  private String cobraGuideSignature(LiveSource source) {
    return cobraDigest(source.toJson().toString() + "|" + mPrefs.getString("cobra_custom_epg:" + source.id, ""));
  }

  private String cobraDigest(String value) {
    try {
      byte[] hash = java.security.MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
      StringBuilder out = new StringBuilder();
      for (byte b : hash) out.append(String.format(Locale.US, "%02x", b & 255));
      return out.toString();
    } catch (Exception e) { throw new IllegalStateException(e); }
  }

  private String cobraGuideNormalize(String value) {
    return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
  }

  private void cobraGuideAlias(Map<String, String> aliases, String name, String id) {
    String key = cobraGuideNormalize(name);
    if (key.isEmpty() || id == null || id.isEmpty()) return;
    if (!aliases.containsKey(key)) aliases.put(key, id);
    else if (!id.equals(aliases.get(key))) aliases.put(key, ""); // Ambiguous names must never cross-map.
  }

  private Map<String, String> cobraParseGuideAliases(String xml) throws Exception {
    Map<String, String> aliases = new HashMap<>();
    XmlPullParser parser = Xml.newPullParser();
    parser.setInput(new java.io.StringReader(xml));
    String id = null;
    for (int event = parser.getEventType(); event != XmlPullParser.END_DOCUMENT; event = parser.next()) {
      if (event == XmlPullParser.START_TAG && "channel".equals(parser.getName())) {
        id = parser.getAttributeValue(null, "id");
        cobraGuideAlias(aliases, id, id);
      } else if (event == XmlPullParser.START_TAG && "display-name".equals(parser.getName()) && id != null) {
        cobraGuideAlias(aliases, parser.nextText(), id);
      } else if (event == XmlPullParser.END_TAG && "channel".equals(parser.getName())) id = null;
    }
    return aliases;
  }

  private boolean cobraGuideSourceCurrent(LiveSource source, String signature) {
    if (!isCobraAsyncAlive() || !mFeatures.sourceEnabled(source.id)) return false;
    for (LiveSource current : mSources)
      if (current.id.equals(source.id)) return signature.equals(cobraGuideSignature(current));
    return false;
  }

  private File cobraGuideCacheFile(LiveSource source) {
    return new File(getFilesDir(), "cobra-guide-" + cobraDigest(source.id) + ".json");
  }

  private JSONObject cobraGuideCache(LiveSource source, String signature,
      Map<String, ArrayList<GuideProgram>> data, Map<String, String> aliases) throws Exception {
    JSONObject root = new JSONObject();
    root.put("schema", 1).put("signature", signature).put("saved", System.currentTimeMillis());
    JSONObject rows = new JSONObject();
    for (Map.Entry<String, ArrayList<GuideProgram>> entry : data.entrySet()) {
      JSONArray list = new JSONArray();
      for (GuideProgram p : entry.getValue()) list.put(new JSONArray()
          .put(p.start).put(p.stop).put(p.title).put(p.description));
      rows.put(entry.getKey(), list);
    }
    root.put("programs", rows).put("aliases", new JSONObject(aliases));
    return root;
  }

  private void cobraPublishGuide(LiveSource source, String signature,
      Map<String, ArrayList<GuideProgram>> programs, Map<String, String> aliases, String state) {
    if (!cobraGuideSourceCurrent(source, signature)) return;
    String prefix = source.id + "|";
    ArrayList<String> old = new ArrayList<>();
    for (String key : mGuidePrograms.keySet()) if (key.startsWith(prefix)) old.add(key);
    for (String key : old) mGuidePrograms.remove(key);
    old.clear();
    for (String key : mGuideAliases.keySet()) if (key.startsWith(prefix)) old.add(key);
    for (String key : old) mGuideAliases.remove(key);
    for (Map.Entry<String, ArrayList<GuideProgram>> e : programs.entrySet()) {
      mGuidePrograms.put(prefix + e.getKey(), e.getValue());
      cobraGuideAlias(aliases, e.getKey(), e.getKey());
    }
    for (Map.Entry<String, String> e : aliases.entrySet()) mGuideAliases.put(prefix + e.getKey(), e.getValue());
    mGuideLoadState.put(source.id, state);
    refreshCobraGuidePresentation(); // Update adapters/labels; never rebuild the player or navigation.
  }

  private void loadGuideAsync(LiveSource source) {
    if (source == null || !isCobraAsyncAlive() || !mFeatures.sourceEnabled(source.id)) return;
    String signature = cobraGuideSignature(source);
    String flight = source.id + "|" + signature;
    if (!mGuideInFlight.add(flight)) return;
    long epoch = System.nanoTime();
    mGuideLoadEpoch.put(source.id, epoch);
    mGuideLoadState.put(source.id, "Updating guide");
    refreshCobraGuidePresentation();
    final String custom = mPrefs.getString("cobra_custom_epg:" + source.id, "");
    final String discovered = mPrefs.getString("cobra_discovered_epg:" + source.id, "");
    if (!submitCobraIo(() -> {
      boolean saved = false;
      try {
        File cache = cobraGuideCacheFile(source);
        if (cache.isFile() && cache.length() <= MAX_TEXT_BYTES) {
          JSONObject root = new JSONObject(readText(new java.io.FileInputStream(cache)));
          long age = System.currentTimeMillis() - root.optLong("saved", 0);
          if (root.optInt("schema") == 1 && signature.equals(root.optString("signature")) && age >= 0 && age < 8L * 86400000L) {
            Map<String, ArrayList<GuideProgram>> data = new HashMap<>();
            JSONObject rows = root.getJSONObject("programs");
            java.util.Iterator<String> keys = rows.keys();
            long now = System.currentTimeMillis();
            while (keys.hasNext()) {
              String key = keys.next(); JSONArray records = rows.getJSONArray(key);
              ArrayList<GuideProgram> list = new ArrayList<>();
              for (int i = 0; i < records.length(); i++) {
                JSONArray row = records.getJSONArray(i);
                GuideProgram p = new GuideProgram(); p.channel = key;
                p.start = row.getLong(0); p.stop = row.getLong(1); p.title = row.getString(2); p.description = row.optString(3);
                if (p.stop > p.start && p.stop > now - 86400000L) list.add(p);
              }
              if (!list.isEmpty()) data.put(key, list);
            }
            Map<String, String> aliases = new HashMap<>();
            JSONObject raw = root.optJSONObject("aliases");
            if (raw != null) { java.util.Iterator<String> a = raw.keys(); while (a.hasNext()) { String k = a.next(); aliases.put(k, raw.optString(k)); } }
            if (!data.isEmpty()) {
              saved = true;
              publishCobraUi(() -> {
                if (Long.valueOf(epoch).equals(mGuideLoadEpoch.get(source.id)))
                  cobraPublishGuide(source, signature, data, aliases, "Saved guide · updating");
              });
            }
          }
        }
      } catch (Exception ignored) { /* Corrupt cache is disposable; current memory remains usable. */ }
      Map<String, ArrayList<GuideProgram>> merged = new HashMap<>();
      Map<String, String> aliases = new HashMap<>();
      ArrayList<String> urls = new ArrayList<>();
      try {
        if (custom != null && !custom.trim().isEmpty()) urls.add(custom.trim());
        String base = "xtream".equals(source.type) ? xtreamEpgUrl(source) : source.epgUrl;
        if ((base == null || base.trim().isEmpty()) && !discovered.isEmpty()) base = discovered;
        if (base != null && !base.trim().isEmpty() && !urls.contains(base.trim())) urls.add(base.trim());
      } catch (Exception ignored) {}
      String failure = "";
      int completed = 0;
      for (String url : urls) {
        if (Thread.currentThread().isInterrupted() || !isCobraAsyncAlive()) break;
        try {
          String xml = httpGet(url);
          Map<String, ArrayList<GuideProgram>> data = parseXmlTvPrograms(xml);
          Map<String, String> names = cobraParseGuideAliases(xml);
          for (Map.Entry<String, ArrayList<GuideProgram>> e : data.entrySet()) if (!merged.containsKey(e.getKey())) merged.put(e.getKey(), e.getValue());
          for (Map.Entry<String, String> e : names.entrySet()) if (!aliases.containsKey(e.getKey())) aliases.put(e.getKey(), e.getValue());
          completed++;
        } catch (Exception error) { failure = error.getClass().getSimpleName(); }
      }
      String result = urls.isEmpty() ? "No guide source configured" : merged.isEmpty()
          ? (completed > 0 ? "Source returned no schedule" : "Guide unavailable · " + failure)
          : "Guide ready · " + merged.size() + " channel schedules";
      final String state = saved && merged.isEmpty() ? "Using saved guide · " + result : result;
      if (!merged.isEmpty()) {
        try {
          byte[] bytes = cobraGuideCache(source, signature, merged, aliases).toString().getBytes(StandardCharsets.UTF_8);
          if (bytes.length <= MAX_TEXT_BYTES) {
            android.util.AtomicFile file = new android.util.AtomicFile(cobraGuideCacheFile(source));
            java.io.FileOutputStream out = null;
            try { out = file.startWrite(); out.write(bytes); file.finishWrite(out); }
            catch (Exception e) { if (out != null) file.failWrite(out); }
          }
        } catch (Exception ignored) {}
      }
      publishCobraUi(() -> {
        mGuideInFlight.remove(flight);
        if (!Long.valueOf(epoch).equals(mGuideLoadEpoch.get(source.id)) || !cobraGuideSourceCurrent(source, signature)) return;
        if (!merged.isEmpty()) cobraPublishGuide(source, signature, merged, aliases, state);
        else { mGuideLoadState.put(source.id, state); refreshCobraGuidePresentation(); }
        requestCobraShortGuide(mGuidePreviewChannel);
      });
    })) mGuideInFlight.remove(flight);
  }

  private ArrayList<GuideProgram> cobraGuidePrograms(Channel channel) {
    if (channel == null) return new ArrayList<>();
    String prefix = sourceIdForChannel(channel) + "|";
    String id = channel.epgId == null ? "" : channel.epgId.trim();
    ArrayList<GuideProgram> rows = mGuidePrograms.get(prefix + id);
    if (rows != null && !rows.isEmpty()) return rows;
    String alias = mGuideAliases.get(prefix + cobraGuideNormalize(id));
    if (alias == null) alias = mGuideAliases.get(prefix + cobraGuideNormalize(channel.name));
    if (alias != null && !alias.isEmpty()) {
      rows = mGuidePrograms.get(prefix + alias);
      if (rows != null && !rows.isEmpty()) return rows;
    }
    rows = mGuidePrograms.get(prefix + "stream:" + channel.id);
    return rows == null ? new ArrayList<>() : rows;
  }

  private ProgramPair programFor(Channel channel) {
    if (channel == null) return null;
    long now = System.currentTimeMillis(); ProgramPair pair = new ProgramPair();
    for (GuideProgram p : cobraGuidePrograms(channel)) {
      if (p.start <= now && now < p.stop) { pair.now = p.title; }
      else if (p.start > now && (pair.nextStart == 0 || p.start < pair.nextStart)) { pair.next = p.title; pair.nextStart = p.start; }
    }
    return pair.now.isEmpty() && pair.next.isEmpty() ? null : pair;
  }

  private String cobraGuideStatus(Channel channel) {
    if (channel == null) return "Choose a channel";
    String state = mGuideLoadState.get(sourceIdForChannel(channel));
    return state == null ? "Guide not loaded" : state.startsWith("Guide ready") ? "No schedule mapped for this channel" : state;
  }

  private void requestCobraShortGuide(Channel channel) {
    if (channel == null || !cobraGuidePrograms(channel).isEmpty()) return;
    LiveSource source = sourceForChannel(channel);
    if (source == null || !"xtream".equals(source.type) || !mFeatures.sourceEnabled(source.id)) return;
    String key = channel.id; long now = System.currentTimeMillis();
    Long previous = mGuideShortLast.get(key);
    if ((previous != null && now - previous < 300000L) || !mGuideShortInFlight.add(key)) return;
    mGuideShortLast.put(key, now);
    String signature = cobraGuideSignature(source);
    if (!submitCobraIo(() -> {
      ArrayList<GuideProgram> rows = new ArrayList<>();
      try {
        String stream = key.substring((source.id + ":").length());
        if (!stream.matches("[0-9]+")) throw new IllegalArgumentException("Not a live stream");
        JSONObject root = new JSONObject(httpGet(xtreamUrl(source, "get_short_epg") + "&stream_id=" + enc(stream) + "&limit=8"));
        JSONArray records = root.optJSONArray("epg_listings");
        if (records != null) for (int i = 0; i < records.length(); i++) {
          JSONObject raw = records.getJSONObject(i); GuideProgram p = new GuideProgram(); p.channel = channel.epgId;
          p.start = raw.optLong("start_timestamp", 0) * 1000L;
          p.stop = raw.optLong("stop_timestamp", raw.optLong("end_timestamp", 0)) * 1000L;
          String title = raw.optString("title", "");
          try { p.title = new String(android.util.Base64.decode(title, android.util.Base64.DEFAULT), StandardCharsets.UTF_8); }
          catch (IllegalArgumentException e) { p.title = title; }
          if (p.start > 0 && p.stop > p.start && !p.title.trim().isEmpty()) rows.add(p);
        }
        rows.sort((a, b) -> Long.compare(a.start, b.start));
      } catch (Exception ignored) { /* Per-channel fallback is optional and bounded, not a retry loop. */ }
      publishCobraUi(() -> {
        mGuideShortInFlight.remove(key);
        if (!cobraGuideSourceCurrent(source, signature) || rows.isEmpty()) return;
        mGuidePrograms.put(source.id + "|stream:" + channel.id, rows);
        refreshCobraGuidePresentation();
      });
    })) mGuideShortInFlight.remove(key);
  }

  private Map<String, ArrayList<GuideProgram>> parseXmlTvPrograms(String xml) throws Exception {
    Map<String, ArrayList<GuideProgram>> result = new HashMap<>();
    XmlPullParser parser = Xml.newPullParser(); parser.setInput(new java.io.StringReader(xml));
    long now = System.currentTimeMillis(); long min = now - 8L * 86400000L, max = now + 8L * 86400000L;
    GuideProgram current = null; String textTag = ""; boolean validRoot = false; int count = 0;
    for (int event = parser.getEventType(); event != XmlPullParser.END_DOCUMENT; event = parser.next()) {
      if (Thread.currentThread().isInterrupted()) throw new java.io.InterruptedIOException("Guide cancelled");
      if (event == XmlPullParser.START_TAG) {
        String tag = parser.getName();
        if ("tv".equals(tag)) validRoot = true;
        if ("programme".equals(tag)) {
          current = new GuideProgram(); current.channel = parser.getAttributeValue(null, "channel");
          current.start = parseXmlTvTime(parser.getAttributeValue(null, "start")); current.stop = parseXmlTvTime(parser.getAttributeValue(null, "stop"));
        } else if (current != null && ("title".equals(tag) || "desc".equals(tag))) textTag = tag;
      } else if (event == XmlPullParser.TEXT && current != null) {
        if ("title".equals(textTag) && current.title.length() < 1024) current.title += parser.getText();
        else if ("desc".equals(textTag) && current.description.length() < 4096) current.description += parser.getText();
      } else if (event == XmlPullParser.END_TAG) {
        String tag = parser.getName();
        if ("title".equals(tag) || "desc".equals(tag)) textTag = "";
        if ("programme".equals(tag) && current != null) {
          if (current.channel != null && current.start > 0 && current.start <= max && (current.stop == 0 || current.stop >= min)) {
            current.channel = current.channel.trim(); current.title = current.title.trim();
            result.computeIfAbsent(current.channel, k -> new ArrayList<>()).add(current);
            if (++count > 200000) throw new java.io.IOException("Guide entry limit exceeded");
          }
          current = null; textTag = "";
        }
      }
    }
    if (!validRoot) throw new java.io.IOException("Not an XMLTV document");
    for (ArrayList<GuideProgram> list : result.values()) {
      list.sort((a, b) -> Long.compare(a.start, b.start));
      for (int i = 0; i + 1 < list.size(); i++) if (list.get(i).stop <= list.get(i).start) list.get(i).stop = list.get(i + 1).start;
      list.removeIf(p -> p.stop <= p.start || p.title.isEmpty());
    }
    result.entrySet().removeIf(e -> e.getValue().isEmpty());
    return result;
  }

  private void showProgramGuide(Channel channel) {
    requestCobraShortGuide(channel);
    ArrayList<GuideProgram> programs = cobraGuidePrograms(channel);
    LinearLayout sheet = cobraOpenRefinedSheet(channel.name + " · Schedule", false);
    if (sheet == null) return;
    if (programs.isEmpty()) { cobraSheetNote(sheet, cobraGuideStatus(channel)); return; }
    android.widget.ListView list = new android.widget.ListView(this); list.setDivider(null);
    list.setAdapter(new android.widget.BaseAdapter() {
      public int getCount() { return programs.size(); }
      public Object getItem(int i) { return programs.get(i); }
      public long getItemId(int i) { return programs.get(i).start; }
      public View getView(int i, View old, android.view.ViewGroup parent) {
        TextView row = old instanceof TextView ? (TextView) old : cobraRefinedText("", 14, false);
        GuideProgram p = programs.get(i); row.setText(formatTime(p.start) + "\n" + p.title);
        row.setPadding(dp(14), dp(8), dp(14), dp(8)); row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(64)));
        row.setOnClickListener(v -> { closeCobraRefinedSheet(); showProgramActions(channel, p); }); return row;
      }
    });
    sheet.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
    long now = System.currentTimeMillis();
    for (int i = 0; i < programs.size(); i++) if (programs.get(i).stop > now) { list.setSelection(i); break; }
  }
