// @replace cobraResolveEpg
  private String cobraResolveEpg(Channel channel) {
    if (channel == null) return "";
    CobraEpgData data = mCobraEpg.get(sourceIdForChannel(channel));
    if (data == null) return "";
    // These map lookups are O(1). Never memoize by stream ID alone: metadata can change.
    String epg = CobraGuideMath.id(channel.epgId);
    if (!epg.isEmpty() && data.programs.containsKey(epg)) return epg;
    String alias = data.aliases.get(CobraGuideMath.alias(epg));
    if (alias == null) alias = data.aliases.get(CobraGuideMath.alias(channel.name));
    if (alias != null && !alias.isEmpty() && data.programs.containsKey(alias)) return alias;
    return data.programs.containsKey("@stream:" + channel.id) ? "@stream:" + channel.id : "";
  }
// @replace cobraPrograms
  private ArrayList<GuideProgram> cobraPrograms(Channel channel) {
    if (channel == null) return null;
    CobraEpgData data = mCobraEpg.get(sourceIdForChannel(channel));
    if (data == null) return null;
    ArrayList<GuideProgram> primary = data.programs.get(cobraResolveEpg(channel));
    ArrayList<GuideProgram> fallback = data.programs.get("@stream:" + channel.id);
    if (primary == null) return fallback;
    if (fallback == null || primary == fallback) return primary;
    return cobraMergeProgrammeRanges(primary, fallback);
  }
// @replace cobraCurrentProgram
  private GuideProgram cobraCurrentProgram(Channel channel) {
    return cobraProgrammeAt(channel, System.currentTimeMillis());
  }
// @replace programFor
  private ProgramPair programFor(Channel channel) {
    GuideProgram now = cobraCurrentProgram(channel), next = cobraNextProgram(channel);
    if (now == null && next == null) return null;
    ProgramPair pair = new ProgramPair();
    if (now != null) pair.now = now.title;
    if (next != null) { pair.next = next.title; pair.nextStart = next.start; }
    return pair;
  }
// @replace guideTitleAt
  private String guideTitleAt(Channel channel, long instant) {
    GuideProgram program = cobraProgrammeAt(channel, instant);
    return program == null ? cobraGuideStatus(channel) : program.title;
  }
// @replace cobraLibrariesEqual
  private boolean cobraLibrariesEqual(List<Channel> current, List<Channel> next) {
    if (current == null || next == null || current.size() != next.size()) return false;
    for (int i = 0; i < current.size(); i++) {
      Channel a = current.get(i), b = next.get(i);
      if (!java.util.Objects.equals(a.id, b.id) || !java.util.Objects.equals(a.primaryUrl, b.primaryUrl)
          || !java.util.Objects.equals(a.name, b.name) || !java.util.Objects.equals(a.epgId, b.epgId)
          || !java.util.Objects.equals(a.group, b.group) || !java.util.Objects.equals(a.icon, b.icon)
          || !java.util.Objects.equals(a.fallbackUrl, b.fallbackUrl)
          || !java.util.Objects.equals(a.headers, b.headers)) return false;
    }
    return true;
  }
// @replace cobraMergeEpg
  private void cobraMergeEpg(CobraEpgData into, CobraEpgData incoming) {
    // Earlier configured feeds own overlapping intervals, not the entire channel.
    ArrayList<String> keys = new ArrayList<>(incoming.programs.keySet());
    Collections.sort(keys);
    for (String key : keys) {
      ArrayList<GuideProgram> first = into.programs.get(key);
      if (first == null && into.programs.size() >= 20000) { into.truncated = true; continue; }
      into.programs.put(key, first == null ? new ArrayList<>(incoming.programs.get(key))
          : cobraMergeProgrammeRanges(first, incoming.programs.get(key)));
    }
    ArrayList<String> aliases = new ArrayList<>(incoming.aliases.keySet());
    Collections.sort(aliases);
    for (String key : aliases) {
      String value = incoming.aliases.get(key), previous = into.aliases.get(key);
      if (!into.aliases.containsKey(key)) {
        if (into.aliases.size() < 100000) into.aliases.put(key, value);
        else into.truncated = true;
      } else if (!java.util.Objects.equals(previous, value)) into.aliases.put(key, "");
    }
    into.truncated |= incoming.truncated;
    into.coverageEnd = -1L;
    cobraBoundMergedGuide(into);
  }
// @replace cobraRefreshGuide
  private void cobraRefreshGuide(Channel channel) {
    if (channel == null || !isCobraAsyncAlive()) return;
    String id = sourceIdForChannel(channel);
    if (mCobraEpgRequest.containsKey(id)) { toast("Guide refresh is already running"); return; }
    for (LiveSource source : mSources) if (source.id.equals(id) && mFeatures.sourceEnabled(id)) {
      // Bypass freshness, not recovery. Keep both successful timestamps and disk snapshots.
      mCobraForceEpg.add(id);
      mCobraForceEpg.add("@short:" + channel.id);
      mCobraShortEpgStatus.remove(channel.id);
      loadGuideAsync(source);
      cobraRequestShortEpg(channel);
      toast("Refreshing programme guide");
      return;
    }
    toast("Guide source is not enabled");
  }
// @replace loadGuideAsync
  private void loadGuideAsync(LiveSource source) {
    if (source == null || !isCobraAsyncAlive() || !mFeatures.sourceEnabled(source.id)) return;
    final String identity = cobraEpgIdentity(source);
    if (identity.equals(mCobraEpgRequest.get(source.id))) return;
    final boolean force = mCobraForceEpg.remove(source.id);
    CobraEpgData current = mCobraEpg.get(source.id);
    long now = System.currentTimeMillis();
    boolean same = current != null && identity.equals(current.identity);
    if (!force && same && cobraEpgFresh(current, now)) return;
    Long attempt = mCobraEpgLastAttempt.get(source.id + "|" + identity);
    long retry = same && !cobraEpgHasCoverage(current, now) ? 15L * 60000L : 60000L;
    if (!force && attempt != null && now - attempt >= 0 && now - attempt < retry) return;
    mCobraEpgLastAttempt.put(source.id + "|" + identity, now);
    mCobraEpgRequest.put(source.id, identity);
    final long generation = cobraNextEpgGeneration(source.id);
    mCobraEpgStatus.put(source.id, same ? "Updating saved guide…" : "Loading guide…");
    final ArrayList<String> urls = cobraEpgUrls(source);
    if (!submitCobraIo(() -> {
      CobraEpgData saved = cobraReadEpgCache(source.id, identity);
      if (saved != null) publishCobraUi(() -> {
        if (cobraEpgGenerationCurrent(source.id, generation) && cobraEpgRequestCurrent(source, identity))
          cobraInstallEpg(source.id, saved, "Saved guide");
      });
      if (!force && saved != null && cobraEpgFresh(saved, System.currentTimeMillis())) {
        publishCobraUi(() -> {
          if (!cobraEpgGenerationCurrent(source.id, generation)) return;
          boolean valid = cobraEpgRequestCurrent(source, identity);
          if (identity.equals(mCobraEpgRequest.get(source.id))) mCobraEpgRequest.remove(source.id);
          if (valid) { mCobraEpgStatus.put(source.id, saved.truncated ? "Guide ready • partial source" : "Guide ready"); cobraRefreshProgrammeLabels(); }
        });
        return;
      }
      CobraEpgData fresh = new CobraEpgData();
      fresh.identity = identity; fresh.requestGeneration = generation;
      String error = urls.isEmpty() ? "No guide source configured" : "Guide unavailable";
      boolean fetchedAny = false;
      int failedFeeds = 0;
      for (String url : urls) {
        if (!isCobraAsyncAlive() || Thread.currentThread().isInterrupted()
            || !cobraEpgGenerationCurrent(source.id, generation)) return;
        try { cobraMergeEpg(fresh, cobraDownloadEpg(url)); fetchedAny = true; }
        catch (Exception failure) { error = cobraGuideFailure(failure); failedFeeds++; }
      }
      final boolean ok = fetchedAny && !fresh.programs.isEmpty();
      final String resultStatus = ok
          ? (!cobraEpgHasCoverage(fresh, System.currentTimeMillis()) ? "Guide received • no current or upcoming timed coverage"
             : fresh.truncated || failedFeeds > 0 ? "Guide ready • partial source" : "Guide ready")
          : fetchedAny ? "Provider returned no programme schedule" : error;
      fresh.fetched = System.currentTimeMillis();
      // Identity-specific filenames plus generation-guarded serialized writes protect disk and UI.
      if (ok) cobraWriteEpgCache(source.id, fresh);
      publishCobraUi(() -> {
        if (!cobraEpgGenerationCurrent(source.id, generation)) return;
        boolean valid = cobraEpgRequestCurrent(source, identity);
        if (identity.equals(mCobraEpgRequest.get(source.id))) mCobraEpgRequest.remove(source.id);
        if (!valid) return;
        if (ok) cobraInstallEpg(source.id, fresh, resultStatus);
        else {
          CobraEpgData retained = mCobraEpg.get(source.id);
          boolean cached = retained != null && identity.equals(retained.identity);
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
// @replace cobraEpgUrls
  private ArrayList<String> cobraEpgUrls(LiveSource source) {
    ArrayList<String> urls = new ArrayList<>();
    cobraAddGuideUrls(urls, mPrefs.getString("cobra_custom_epg:" + source.id, ""), null, false);
    try {
      cobraAddGuideUrls(urls, "xtream".equals(source.type) ? xtreamEpgUrl(source) : source.epgUrl, null, false);
      if ("m3u".equals(source.type)) {
        cobraAddGuideUrls(urls, mPrefs.getString("cobra_epg_discovered|" + source.id, ""), source.playlistUrl, true);
        Uri playlist = Uri.parse(source.playlistUrl);
        String path = playlist.getPath();
        if (path != null && path.endsWith("/get.php")) {
          String u = playlist.getQueryParameter("username"), p = playlist.getQueryParameter("password");
          if (u != null && p != null) cobraAddGuideUrls(urls, playlist.buildUpon()
              .path(path.substring(0, path.length() - 7) + "xmltv.php").clearQuery()
              .appendQueryParameter("username", u).appendQueryParameter("password", p).build().toString(), null, false);
        }
      }
    } catch (Exception ignored) { /* Never discover feeds by probing other providers. */ }
    return urls;
  }
// @replace cobraDiscoverPlaylistGuide
  private void cobraDiscoverPlaylistGuide(LiveSource source, String playlist) {
    if (source == null || playlist == null) return;
    int newline = playlist.indexOf('\n');
    String header = playlist.substring(0, Math.min(playlist.length(), newline < 0 ? 4096 : Math.min(4096, newline)));
    if (!header.replace("\uFEFF", "").trim().toUpperCase(Locale.ROOT).startsWith("#EXTM3U")) return;
    Matcher match = Pattern.compile("(?:x-tvg-url|url-tvg|tvg-url)\\s*=\\s*[\"']([^\"']+)[\"']", Pattern.CASE_INSENSITIVE).matcher(header);
    ArrayList<String> urls = new ArrayList<>();
    while (match.find()) cobraAddGuideUrls(urls, match.group(1), source.playlistUrl, true);
    // Also clear an obsolete advertised guide after a successfully parsed replacement playlist.
    StringBuilder value = new StringBuilder();
    for (String url : urls) { if (value.length() > 0) value.append('\n'); value.append(url); }
    mPrefs.edit().putString("cobra_epg_discovered|" + source.id, value.toString()).apply();
  }
// @append
  private GuideProgram cobraProgrammeAt(Channel channel, long instant) {
    if (channel == null) return null;
    CobraEpgData data = mCobraEpg.get(sourceIdForChannel(channel));
    if (data == null) return null;
    ArrayList<GuideProgram> primary = data.programs.get(cobraResolveEpg(channel));
    GuideProgram match = cobraFindProgrammeAt(primary, instant);
    // Key existence is not time coverage. Unknown-duration entries never claim to be live.
    return match != null ? match : cobraFindProgrammeAt(data.programs.get("@stream:" + channel.id), instant);
  }
  private GuideProgram cobraFindProgrammeAt(List<GuideProgram> programs, long instant) {
    if (programs != null) for (GuideProgram p : programs) {
      if (p.start > instant) break;
      if (p.stop > instant) return p;
    }
    return null;
  }
  private ArrayList<GuideProgram> cobraMergeProgrammeRanges(List<GuideProgram> primary, List<GuideProgram> fallback) {
    ArrayList<GuideProgram> result = new ArrayList<>(primary);
    java.util.TreeMap<Long, Long> covered = new java.util.TreeMap<>();
    Set<String> seen = new HashSet<>();
    for (GuideProgram p : primary) {
      seen.add(p.start + "|" + p.stop + "|" + p.title);
      cobraCoverRange(covered, p.start, p.stop);
    }
    for (GuideProgram p : fallback) {
      String key = p.start + "|" + p.stop + "|" + p.title;
      if (!seen.add(key)) continue;
      Map.Entry<Long, Long> overlap = p.stop > p.start ? covered.lowerEntry(p.stop) : null;
      if (overlap != null && overlap.getValue() > p.start) continue;
      result.add(p); cobraCoverRange(covered, p.start, p.stop);
    }
    Collections.sort(result, (a, b) -> Long.compare(a.start, b.start));
    return result;
  }
  private void cobraCoverRange(java.util.TreeMap<Long, Long> ranges, long start, long stop) {
    if (stop <= start) return;
    Map.Entry<Long, Long> floor = ranges.floorEntry(start);
    if (floor != null && floor.getValue() >= start) {
      start = floor.getKey(); stop = Math.max(stop, floor.getValue()); ranges.remove(start);
    }
    Map.Entry<Long, Long> next = ranges.ceilingEntry(start);
    while (next != null && next.getKey() <= stop) {
      stop = Math.max(stop, next.getValue()); ranges.remove(next.getKey()); next = ranges.ceilingEntry(start);
    }
    ranges.put(start, stop);
  }
  private void cobraBoundMergedGuide(CobraEpgData data) {
    int total = 0; for (ArrayList<GuideProgram> list : data.programs.values()) total += list.size();
    if (total <= 400000) return;
    data.truncated = true;
    long now = System.currentTimeMillis();
    ArrayList<String> keys = new ArrayList<>(data.programs.keySet()); Collections.sort(keys);
    Map<String, ArrayList<GuideProgram>> bounded = new HashMap<>();
    // Reserve Now/Next for every retained channel before using optional history budget.
    int kept = 0;
    for (String key : keys) {
      ArrayList<GuideProgram> list = data.programs.get(key), output = new ArrayList<>();
      GuideProgram current = null, next = null;
      for (GuideProgram p : list) {
        if (p.start <= now && p.stop > now && current == null) current = p;
        if (p.start > now && (next == null || p.start < next.start)) next = p;
      }
      if (current != null) output.add(current);
      if (next != null) output.add(next);
      bounded.put(key, output); kept += output.size();
    }
    for (String key : keys) {
      ArrayList<GuideProgram> output = bounded.get(key);
      Set<GuideProgram> seen = new HashSet<>(output);
      for (GuideProgram p : data.programs.get(key)) {
        if (kept >= 400000) break;
        if (seen.add(p)) { output.add(p); kept++; }
      }
      Collections.sort(output, (a, b) -> Long.compare(a.start, b.start));
    }
    data.programs.clear(); data.programs.putAll(bounded);
  }
  private boolean cobraEpgHasCoverage(CobraEpgData data, long now) {
    if (data.coverageEnd < 0) {
      long end = 0;
      for (Map.Entry<String, ArrayList<GuideProgram>> entry : data.programs.entrySet()) {
        if (entry.getKey().startsWith("@stream:")) continue;
        for (GuideProgram p : entry.getValue()) if (p.stop > p.start) end = Math.max(end, p.stop);
      }
      data.coverageEnd = end;
    }
    return data.coverageEnd > now;
  }
  private boolean cobraEpgFresh(CobraEpgData data, long now) {
    long age = now - data.fetched;
    return age >= 0 && age < COBRA_GUIDE_TTL_MS && cobraEpgHasCoverage(data, now);
  }
  private void cobraAddGuideUrls(ArrayList<String> urls, String raw, String base, boolean multiple) {
    if (raw == null || raw.length() > 65536) return;
    String[] values = multiple ? raw.split("[,\\r\\n]", 65) : new String[]{raw};
    for (int index = 0; index < Math.min(64, values.length); index++) {
      String value = values[index];
      if (urls.size() >= 16) return;
      value = value.trim(); if (value.isEmpty() || value.length() > 8192) continue;
      try {
        URL url = base == null ? new URL(value) : new URL(new URL(base), value);
        if (!("http".equals(url.getProtocol()) || "https".equals(url.getProtocol())) || url.getHost().isEmpty()) continue;
        String normalized = url.toExternalForm(); if (!urls.contains(normalized)) urls.add(normalized);
      } catch (java.net.MalformedURLException ignored) { }
    }
  }
  private long cobraNextEpgGeneration(String key) {
    long generation = mCobraEpgSequence.incrementAndGet();
    mCobraEpgGenerations.put(key, generation); return generation;
  }
  private boolean cobraEpgGenerationCurrent(String key, long generation) {
    return Long.valueOf(generation).equals(mCobraEpgGenerations.get(key));
  }
  private File cobraEpgSnapshotFile(String sourceId, String identity) {
    String prefix = sourceId.startsWith("@short:") ? "cobra-epg-short-v3-" : "cobra-epg-v3-";
    return new File(getFilesDir(), prefix + cobraDigest(sourceId).substring(0, 24)
        + "-" + cobraDigest(identity).substring(0, 24) + ".bin");
  }
  private void cobraPruneSourceGuideSnapshots(String sourceId, File keep) {
    String prefix = "cobra-epg-v3-" + cobraDigest(sourceId).substring(0, 24) + "-";
    File[] entries = getFilesDir().listFiles((dir, name) -> name.startsWith(prefix) && name.endsWith(".bin"));
    if (entries == null || entries.length <= 4) return;
    java.util.Arrays.sort(entries, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
    int kept = 1;
    for (File file : entries) if (!file.equals(keep)) {
      if (kept++ >= 4) new android.util.AtomicFile(file).delete();
    }
  }
  private boolean cobraGuidePresentationActive() {
    return isCobraAsyncAlive() && !mBackgroundStopped
        && (mCobraPreviewPlayer != null || mPlayer != null || !mCobraTiles.isEmpty()
            || (mCobraGuideShell != null && mCobraGuideShell.isShown()));
  }
  private boolean cobraProgrammeHasEnd(GuideProgram program) { return program.stop > program.start; }
  private boolean cobraProgrammeInSchedule(GuideProgram program, long cutoff) {
    return program.stop > cutoff || (program.stop == -1L && program.start > cutoff);
  }
  private String cobraProgrammeTimeLabel(GuideProgram program) {
    return formatTime(program.start) + (cobraProgrammeHasEnd(program) ? " – " + formatTime(program.stop) : " • End time unavailable");
  }
