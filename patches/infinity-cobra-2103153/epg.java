// COBRA-APPEND
  /** Disk-backed guide: importing a complete feed never builds a giant in-memory XML tree. */
  private static final class CobraEpgStore extends android.database.sqlite.SQLiteOpenHelper {
    private static CobraEpgStore instance;
    static synchronized android.database.sqlite.SQLiteDatabase database(Context context) {
      if (instance == null) instance = new CobraEpgStore(context.getApplicationContext());
      return instance.getWritableDatabase();
    }
    private CobraEpgStore(Context context) {
      super(context, "cobra-guide-v2.db", null, 1);
      setWriteAheadLoggingEnabled(true);
    }
    @Override public void onCreate(android.database.sqlite.SQLiteDatabase db) {
      db.execSQL("CREATE TABLE programmes(feed TEXT NOT NULL,id TEXT NOT NULL,start INTEGER NOT NULL,stop INTEGER NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,PRIMARY KEY(feed,id,start))");
      db.execSQL("CREATE TABLE aliases(feed TEXT NOT NULL,kind TEXT NOT NULL,value TEXT NOT NULL,id TEXT NOT NULL,PRIMARY KEY(feed,kind,value,id))");
      db.execSQL("CREATE TABLE feeds(feed TEXT PRIMARY KEY,updated INTEGER NOT NULL,records INTEGER NOT NULL)");
    }
    @Override public void onUpgrade(android.database.sqlite.SQLiteDatabase db, int oldVersion, int newVersion) {
      throw new IllegalStateException("Guide migration is required");
    }
  }
  private static final class CobraGuideWindow {
    final ArrayList<GuideProgram> programmes = new ArrayList<>();
    String message = "", fingerprint = "";
    long window, created;
    int epoch;
  }
  private final Map<String, String> mCobraEpgStatus = new HashMap<>();
  private final Set<String> mCobraEpgLoading = new HashSet<>();
  private final Set<String> mCobraEpgPending = new HashSet<>();
  private final Map<String, Long> mCobraShortAttempts = new HashMap<>();
  private final LinkedHashMap<String, CobraGuideWindow> mCobraGuideWindows =
      new LinkedHashMap<String, CobraGuideWindow>(128, .75f, true) {
        @Override protected boolean removeEldestEntry(Map.Entry<String, CobraGuideWindow> e) {
          return size() > 128;
        }
      };
  private final Map<String, String[]> mCobraGuideFingerprints = new HashMap<>();
  private int mCobraGuideEpoch;
  private final ExecutorService mCobraGuideReadIo = Executors.newFixedThreadPool(2);
  private boolean submitCobraGuideRead(Runnable task) {
    synchronized (mCobraAsyncLock) {
      if (!isCobraAsyncAlive() || mCobraGuideReadIo.isShutdown()) return false;
      try { mCobraGuideReadIo.execute(() -> { if (isCobraAsyncAlive() && !Thread.currentThread().isInterrupted()) task.run(); }); return true; }
      catch (java.util.concurrent.RejectedExecutionException error) { if (!isCobraAsyncAlive() || mCobraGuideReadIo.isShutdown()) return false; throw error; }
    }
  }

  private String cobraGuideFingerprint(LiveSource source) {
    if (source == null) return "";
    String config = source.toJson().toString() + "|" + mPrefs.getString("cobra_custom_epg:" + source.id, "")
        + "|" + mPrefs.getString("cobra_discovered_epg:" + source.id, "");
    synchronized (mCobraGuideFingerprints) {
      String[] cached = mCobraGuideFingerprints.get(source.id);
      if (cached != null && config.equals(cached[0])) return cached[1];
      try {
        byte[] digest = java.security.MessageDigest.getInstance("SHA-256")
            .digest(config.getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder(64);
        for (byte value : digest) {
          hex.append(Character.forDigit((value >>> 4) & 15, 16));
          hex.append(Character.forDigit(value & 15, 16));
        }
        String result = hex.toString();
        mCobraGuideFingerprints.put(source.id, new String[]{config, result});
        return result;
      } catch (Exception error) { throw new IllegalStateException("Guide identity unavailable", error); }
    }
  }
  private ArrayList<String> cobraGuideUrls(LiveSource source) {
    ArrayList<String> urls = new ArrayList<>();
    String primary = source.epgUrl;
    if ("xtream".equals(source.type)) try { primary = xtreamEpgUrl(source); } catch (Exception ignored) { primary = ""; }
    for (String raw : new String[]{primary,
        mPrefs.getString("cobra_discovered_epg:" + source.id, ""),
        mPrefs.getString("cobra_custom_epg:" + source.id, "")}) {
      String value = CobraCore.clean(raw);
      if ((value.startsWith("https://") || value.startsWith("http://")) && !urls.contains(value)) urls.add(value);
    }
    return urls;
  }
  private void captureCobraPlaylistGuide(LiveSource source, String playlist) {
    if (source == null || playlist == null) return;
    int end = playlist.indexOf('\n');
    String header = playlist.substring(0, Math.min(8192, end < 0 ? playlist.length() : end));
    Matcher match = Pattern.compile("(?:url-tvg|x-tvg-url|tvg-url)\\s*=\\s*['\"]([^'\"]+)['\"]", Pattern.CASE_INSENSITIVE).matcher(header);
    if (!match.find()) return;
    try {
      String target = new URL(new URL(source.playlistUrl), match.group(1).split(",")[0].trim()).toString();
      if (target.startsWith("https://") || target.startsWith("http://"))
        mPrefs.edit().putString("cobra_discovered_epg:" + source.id, target).apply();
    } catch (Exception ignored) { /* Invalid playlist metadata does not erase a user-specified guide. */ }
  }
  private File downloadCobraGuide(String target) throws Exception {
    File file = File.createTempFile("cobra-guide-", ".xml", getCacheDir());
    boolean complete = false;
    HttpURLConnection connection = null;
    try {
      for (int redirects = 0; redirects <= 5; redirects++) {
        URL url = new URL(target);
        if (!"http".equals(url.getProtocol()) && !"https".equals(url.getProtocol()))
          throw new java.io.IOException("Unsupported guide protocol");
        connection = (HttpURLConnection) url.openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(15000); connection.setReadTimeout(30000);
        connection.setRequestProperty("Accept-Encoding", "gzip");
        connection.setRequestProperty("User-Agent", "Infinity Cobra/3.0");
        int code = connection.getResponseCode();
        if (code >= 300 && code < 400) {
          String location = connection.getHeaderField("Location");
          if (location == null || redirects == 5) throw new java.io.IOException("Guide redirect failed");
          target = new URL(url, location).toString();
          connection.disconnect(); connection = null; continue;
        }
        if (code != 200) throw new java.io.IOException("Guide HTTP " + code);
        try (BufferedInputStream input = new BufferedInputStream(connection.getInputStream());
             java.io.FileOutputStream out = new java.io.FileOutputStream(file)) {
          input.mark(2); int a = input.read(), b = input.read(); input.reset();
          InputStream decoded = a == 31 && b == 139 ? new GZIPInputStream(input) : input;
          byte[] buffer = new byte[16384]; long total = 0; int count;
          while ((count = decoded.read(buffer)) != -1) {
            if (!isCobraAsyncAlive() || Thread.currentThread().isInterrupted()) throw new java.io.InterruptedIOException();
            total += count;
            if (total > 256L * 1024L * 1024L) throw new java.io.IOException("Guide exceeds safety limit");
            out.write(buffer, 0, count);
          }
        }
        complete = true; return file;
      }
      throw new java.io.IOException("Guide redirect failed");
    } finally {
      if (connection != null) connection.disconnect();
      if (!complete) file.delete();
    }
  }
  private int importCobraGuide(String feed, File file) throws Exception {
    android.database.sqlite.SQLiteDatabase db = CobraEpgStore.database(this);
    final int[] records = {0};
    long oldest = System.currentTimeMillis() - 86400000L, newest = oldest + 9L * 86400000L;
    db.beginTransactionNonExclusive();
    try {
      db.delete("programmes", "feed=?", new String[]{feed});
      db.delete("aliases", "feed=?", new String[]{feed});
      try (android.database.sqlite.SQLiteStatement row = db.compileStatement("INSERT OR REPLACE INTO programmes VALUES(?,?,?,?,?,?)");
           android.database.sqlite.SQLiteStatement alias = db.compileStatement("INSERT OR IGNORE INTO aliases VALUES(?,?,?,?)");
           InputStream input = new BufferedInputStream(new java.io.FileInputStream(file))) {
        CobraCore.parse(input, new CobraCore.Sink() {
          @Override public void channel(String id, String name) {
            if (id.isEmpty()) return;
            alias.clearBindings(); alias.bindString(1, feed); alias.bindString(2, "id");
            alias.bindString(3, CobraCore.alias(id)); alias.bindString(4, id); alias.executeInsert();
            if (!name.isEmpty()) {
              alias.clearBindings(); alias.bindString(1, feed); alias.bindString(2, "name");
              alias.bindString(3, CobraCore.alias(name)); alias.bindString(4, id); alias.executeInsert();
            }
          }
          @Override public void programme(CobraCore.Programme p) throws Exception {
            if (!isCobraAsyncAlive() || Thread.currentThread().isInterrupted()) throw new java.io.InterruptedIOException();
            if ((p.stop > 0 ? p.stop : p.start) < oldest || p.start > newest) return;
            row.clearBindings(); row.bindString(1, feed); row.bindString(2, p.id);
            row.bindLong(3, p.start); row.bindLong(4, p.stop); row.bindString(5, p.title);
            row.bindString(6, p.description); row.executeInsert(); records[0]++;
          }
        });
      }
      if (records[0] == 0) throw new java.io.IOException("No current guide records");
      // Missing stop times are inferred only from a real subsequent programme, never invented durations.
      db.execSQL("UPDATE programmes SET stop=COALESCE((SELECT MIN(p.start) FROM programmes p WHERE p.feed=programmes.feed AND p.id=programmes.id AND p.start>programmes.start),0) WHERE feed=? AND stop<=start", new Object[]{feed});
      android.content.ContentValues values = new android.content.ContentValues();
      values.put("feed", feed); values.put("updated", System.currentTimeMillis()); values.put("records", records[0]);
      db.insertWithOnConflict("feeds", null, values, android.database.sqlite.SQLiteDatabase.CONFLICT_REPLACE);
      if (!isCobraAsyncAlive()) throw new java.io.InterruptedIOException();
      db.setTransactionSuccessful();
      return records[0];
    } finally { db.endTransaction(); }
  }
  private String resolveCobraGuideId(android.database.sqlite.SQLiteDatabase db, String feed, Channel channel) {
    String epg = CobraCore.clean(channel.epgId);
    if (!epg.isEmpty()) {
      try (android.database.Cursor c = db.rawQuery("SELECT id FROM programmes WHERE feed=? AND id=? LIMIT 1", new String[]{feed, epg})) {
        if (c.moveToFirst()) return c.getString(0);
      }
    }
    for (String[] key : new String[][]{{"id", epg}, {"name", channel.name}}) {
      if (key[1] == null || key[1].isEmpty()) continue;
      try (android.database.Cursor c = db.rawQuery("SELECT DISTINCT id FROM aliases WHERE feed=? AND kind=? AND value=? LIMIT 2", new String[]{feed, key[0], CobraCore.alias(key[1])})) {
        if (c.getCount() == 1 && c.moveToFirst()) return c.getString(0);
      }
    }
    return "";
  }
  private void readCobraGuideFeed(android.database.sqlite.SQLiteDatabase db, String feed, Channel channel,
      long window, ArrayList<GuideProgram> result, boolean shortFeed) {
    String id = shortFeed ? channel.id : resolveCobraGuideId(db, feed, channel);
    if (id.isEmpty()) return;
    long now = System.currentTimeMillis();
    String[] args = {feed, id, Long.toString(now - 3600000L), Long.toString(now + 86400000L),
        Long.toString(window), Long.toString(window + 7200000L)};
    try (android.database.Cursor c = db.rawQuery("SELECT start,stop,title,description FROM programmes WHERE feed=? AND id=? AND ((stop>? AND start<?) OR (stop>? AND start<?)) ORDER BY start LIMIT 192", args)) {
      Set<Long> present = new HashSet<>(); for (GuideProgram p : result) present.add(p.start);
      while (c.moveToNext()) {
        long start = c.getLong(0), stop = c.getLong(1);
        if (stop <= start || !present.add(start)) continue;
        GuideProgram p = new GuideProgram(); p.channel = id; p.start = start; p.stop = stop;
        p.title = c.getString(2); p.description = c.getString(3); result.add(p);
      }
    }
  }
  private String decodeCobraEpgText(String raw) {
    String value = CobraCore.clean(raw);
    if (value.length() >= 4 && value.length() % 4 == 0 && value.matches("[A-Za-z0-9+/]*={0,2}")) {
      try {
        String decoded = new String(android.util.Base64.decode(value, android.util.Base64.DEFAULT), StandardCharsets.UTF_8);
        if (decoded.indexOf('\uFFFD') < 0 && !decoded.matches("(?s).*[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F].*")) return decoded.trim();
      } catch (IllegalArgumentException ignored) {}
    }
    return value;
  }
  private void fetchCobraShortGuide(LiveSource source, Channel channel, String feed) throws Exception {
    String id = channel.id.substring(Math.min(channel.id.length(), (source.id + ":").length()));
    if (!id.matches("\\d+")) return;
    String response = httpGet(xtreamUrl(source, "get_short_epg") + "&stream_id=" + enc(id) + "&limit=48");
    JSONArray list = new JSONObject(response).optJSONArray("epg_listings");
    if (list == null) return;
    ArrayList<CobraCore.Programme> programmes = new ArrayList<>();
    for (int i = 0; i < Math.min(192, list.length()); i++) {
      JSONObject item = list.optJSONObject(i); if (item == null) continue;
      long start = item.optLong("start_timestamp", 0), stop = item.optLong("stop_timestamp", item.optLong("end_timestamp", 0));
      if (start > 0 && start < 100000000000L) start *= 1000;
      if (stop > 0 && stop < 100000000000L) stop *= 1000;
      if (start <= 0 || stop <= start) continue; // Do not guess a provider timezone from a local date string.
      CobraCore.Programme p = new CobraCore.Programme(); p.start = start; p.stop = stop;
      p.title = decodeCobraEpgText(item.optString("title", ""));
      p.description = decodeCobraEpgText(item.optString("description", "")); programmes.add(p);
    }
    if (programmes.isEmpty()) return;
    android.database.sqlite.SQLiteDatabase db = CobraEpgStore.database(this);
    db.beginTransactionNonExclusive();
    try {
      db.delete("programmes", "feed=? AND id=?", new String[]{feed, channel.id});
      for (CobraCore.Programme p : programmes) {
        android.content.ContentValues values = new android.content.ContentValues();
        values.put("feed", feed); values.put("id", channel.id); values.put("start", p.start); values.put("stop", p.stop);
        values.put("title", p.title); values.put("description", p.description);
        db.insertWithOnConflict("programmes", null, values, android.database.sqlite.SQLiteDatabase.CONFLICT_REPLACE);
      }
      if (!isCobraAsyncAlive()) throw new java.io.InterruptedIOException();
      db.setTransactionSuccessful();
    } finally { db.endTransaction(); }
  }
  private void requestCobraGuideWindow(Channel channel, boolean explicit) {
    if (channel == null || !isCobraAsyncAlive()) return;
    LiveSource source = sourceForChannel(channel); if (source == null) return;
    String fingerprint = cobraGuideFingerprint(source);
    long window = cobraGuideWindowStart(), now = System.currentTimeMillis();
    CobraGuideWindow cached = mCobraGuideWindows.get(channel.id);
    boolean shortAllowed = explicit && "xtream".equals(source.type)
        && now - mCobraShortAttempts.getOrDefault(channel.id, 0L) > 900000L;
    if (!shortAllowed && cached != null && cached.epoch == mCobraGuideEpoch && cached.window == window
        && fingerprint.equals(cached.fingerprint) && now - cached.created < 300000L) return;
    if (mCobraEpgPending.size() >= 64 || !mCobraEpgPending.add(channel.id)) return;
    if (shortAllowed) mCobraShortAttempts.put(channel.id, now);
    ArrayList<String> urls = cobraGuideUrls(source); int epoch = mCobraGuideEpoch;
    if (!submitCobraGuideRead(() -> {
      CobraGuideWindow result = new CobraGuideWindow();
      result.window = window; result.fingerprint = fingerprint; result.epoch = epoch;
      result.created = System.currentTimeMillis();
      try {
        android.database.sqlite.SQLiteDatabase db = CobraEpgStore.database(this);
        for (int i = 0; i < urls.size(); i++) readCobraGuideFeed(db, fingerprint + ":" + i, channel, window, result.programmes, false);
        readCobraGuideFeed(db, fingerprint + ":short", channel, window, result.programmes, true);
        boolean current = false;
        for (GuideProgram p : result.programmes) if (CobraCore.current(p.start, p.stop, now)) current = true;
        if (!current && shortAllowed && isCobraAsyncAlive()) {
          try {
            fetchCobraShortGuide(source, channel, fingerprint + ":short");
            readCobraGuideFeed(db, fingerprint + ":short", channel, window, result.programmes, true);
          } catch (Exception error) { result.message = "Short guide unavailable"; }
        }
        Collections.sort(result.programmes, Comparator.comparingLong(p -> p.start));
        if (result.programmes.isEmpty() && result.message.isEmpty())
          result.message = urls.isEmpty() ? "No EPG source configured" : "No matching schedule in saved guide";
      } catch (Exception error) { result.message = "Saved guide unavailable"; }
      publishCobraUi(() -> {
        mCobraEpgPending.remove(channel.id);
        LiveSource active = sourceById(source.id);
        if (active == null || !mFeatures.sourceEnabled(source.id) || !fingerprint.equals(cobraGuideFingerprint(active))) return;
        if (epoch != mCobraGuideEpoch) { refreshCobraGuideViews(); return; }
        mCobraGuideWindows.put(channel.id, result); refreshCobraGuideViews();
      });
    })) mCobraEpgPending.remove(channel.id);
  }
  private ArrayList<GuideProgram> cobraSchedule(Channel channel) {
    if (channel == null) return new ArrayList<>();
    requestCobraGuideWindow(channel, false);
    CobraGuideWindow window = mCobraGuideWindows.get(channel.id);
    LiveSource source = sourceForChannel(channel);
    return window == null || source == null || !window.fingerprint.equals(cobraGuideFingerprint(source)) ? new ArrayList<>() : window.programmes;
  }
  private String cobraGuideMessage(Channel channel) {
    if (channel == null) return "Choose a channel";
    String sourceId = sourceIdForChannel(channel);
    CobraGuideWindow window = mCobraGuideWindows.get(channel.id);
    if (window != null && !window.programmes.isEmpty()) return "No programme for this time";
    if (mCobraEpgLoading.contains(sourceId)) return "Updating guide…";
    if (window == null) return "Loading saved guide…";
    String status = mCobraEpgStatus.get(sourceId);
    if (status != null && !status.startsWith("Guide ready")) return status;
    return window.message;
  }
  private String cobraGuideFailure(Exception error) {
    if (error instanceof java.net.SocketTimeoutException) return "Provider timed out";
    if (error instanceof java.net.UnknownHostException) return "Provider host unavailable";
    if (error instanceof javax.net.ssl.SSLException) return "Guide TLS connection failed";
    if (error instanceof org.xml.sax.SAXException) return "Invalid XMLTV data";
    String message=error.getMessage();
    if (message!=null && (message.matches("Guide HTTP [0-9]{3}") || "Guide exceeds safety limit".equals(message) || "No current guide records".equals(message))) return message;
    return "Guide download/import error ("+error.getClass().getSimpleName()+")";
  }
  private void pruneCobraGuideStore() {
    try {
      android.database.sqlite.SQLiteDatabase db = CobraEpgStore.database(this);
      long oldest = System.currentTimeMillis() - 9L * 86400000L;
      db.delete("programmes", "stop>0 AND stop<?", new String[]{Long.toString(oldest)});
      // Obsolete configurations are retained for rollback briefly, then removed transactionally.
      db.beginTransactionNonExclusive();
      try {
        db.execSQL("DELETE FROM programmes WHERE feed IN (SELECT feed FROM feeds WHERE updated<?)", new Object[]{oldest});
        db.execSQL("DELETE FROM aliases WHERE feed IN (SELECT feed FROM feeds WHERE updated<?)", new Object[]{oldest});
        db.delete("feeds", "updated<?", new String[]{Long.toString(oldest)});
        db.setTransactionSuccessful();
      } finally { db.endTransaction(); }
    } catch (Exception ignored) { /* Pruning failure must not discard usable programme data. */ }
  }

// COBRA-REPLACE loadGuideAsync
  private void loadGuideAsync(LiveSource source) {
    if (source == null || !isCobraAsyncAlive() || !mCobraEpgLoading.add(source.id)) return;
    String fingerprint = cobraGuideFingerprint(source);
    ArrayList<String> urls = cobraGuideUrls(source);
    if (urls.isEmpty()) {
      mCobraEpgLoading.remove(source.id); mCobraEpgStatus.put(source.id, "No EPG source configured");
      refreshCobraGuideViews(); return;
    }
    mCobraEpgStatus.put(source.id, "Updating guide…"); refreshCobraGuideViews();
    if (!submitCobraIo(() -> {
      int successes = 0, records = 0; String failure = "Guide unavailable";
      for (int i = 0; i < urls.size() && isCobraAsyncAlive(); i++) {
        File file = null;
        try { file = downloadCobraGuide(urls.get(i)); records += importCobraGuide(fingerprint + ":" + i, file); successes++; }
        catch (Exception error) { failure = cobraGuideFailure(error); }
        finally { if (file != null) file.delete(); }
      }
      final String status = successes > 0 ? "Guide ready • " + records + " programmes" + (successes < urls.size() ? " • partial refresh" : "")
          : "Refresh failed • " + failure;
      pruneCobraGuideStore();
      publishCobraUi(() -> {
        mCobraEpgLoading.remove(source.id);
        LiveSource active = sourceById(source.id);
        if (active == null || !fingerprint.equals(cobraGuideFingerprint(active))) return;
        mCobraEpgStatus.put(source.id, status); mCobraGuideEpoch++; refreshCobraGuideViews();
      });
    })) mCobraEpgLoading.remove(source.id);
  }

// COBRA-REPLACE programFor
  private ProgramPair programFor(Channel channel) {
    long now = System.currentTimeMillis(); ProgramPair pair = new ProgramPair();
    for (GuideProgram p : cobraSchedule(channel)) {
      if (CobraCore.current(p.start, p.stop, now)) pair.now = p.title;
      else if (p.start > now && (pair.nextStart == 0 || p.start < pair.nextStart)) {
        pair.next = p.title; pair.nextStart = p.start;
      }
    }
    return pair.now.isEmpty() && pair.next.isEmpty() ? null : pair;
  }

// COBRA-REPLACE parseXmlTvTime
  private long parseXmlTvTime(String value) { return CobraCore.time(value); }
