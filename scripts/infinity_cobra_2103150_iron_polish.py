#!/usr/bin/env python3
"""Cobra 2103150 iron/polish pass.

Android presentation-shell only. This pass keeps the locked 2103149 native
engine bytes untouched while addressing device-test findings:
- warm-start live-library cache with background refresh
- virtualized 12k-channel browsing instead of eager Button trees
- restored Mobile destination
- orientation-specific TV Grid / Compact / Cards / Focus layouts
- in-place preview selection for lower touch latency
- uninterrupted preview <-> fullscreen handoff on the same live session
- dark, compact video chrome with aspect control always reachable
"""
from __future__ import annotations

import argparse
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def method_end(text: str, start: int) -> int:
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError("method opening brace missing")
    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if c == "\n": line_comment = False
            i += 1; continue
        if block_comment:
            if c == "*" and n == "/": block_comment = False; i += 2; continue
            i += 1; continue
        if quote is not None:
            if escape: escape = False
            elif c == "\\": escape = True
            elif c == quote: quote = None
            i += 1; continue
        if c == "/" and n == "/": line_comment = True; i += 2; continue
        if c == "/" and n == "*": block_comment = True; i += 2; continue
        if c in ('"', "'"): quote = c; i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i + 1
        i += 1
    raise RuntimeError("method closing brace missing")


def span(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    if start < 0:
        raise RuntimeError("missing method: " + signature.strip())
    if text.find(signature, start + 1) >= 0:
        raise RuntimeError("duplicate method: " + signature.strip())
    return start, method_end(text, start)


def replace_method(text: str, signature: str, replacement: str) -> str:
    a, b = span(text, signature)
    return text[:a] + replacement.rstrip() + "\n" + text[b:]


def inject_after_signature(text: str, signature: str, addition: str) -> str:
    a, b = span(text, signature)
    block = text[a:b]
    brace = block.find("{")
    block = block[:brace + 1] + "\n" + addition.rstrip() + "\n" + block[brace + 1:]
    return text[:a] + block + text[b:]


def patch(java: str) -> str:
    state_anchor = '  private boolean mCobraDrawerShifted = false;\n'
    if java.count(state_anchor) != 1:
        raise RuntimeError("2103149 state anchor missing")
    java = java.replace(
        state_anchor,
        state_anchor
        + '  private static final String COBRA_LIBRARY_CACHE_FILE = "cobra-live-library-v1.json";\n'
        + '  private ExoPlayer mCobraTransferPlayer;\n'
        + '  private String mCobraTransferKey = "";\n',
        1,
    )

    action = r'''  private Button action(String value) {
    Button button = new Button(this);
    button.setText(value);
    button.setTextColor(cobraThemeColor("text", mTheme.text));
    button.setTextSize(13);
    button.setAllCaps(false);
    button.setGravity(Gravity.CENTER);
    boolean dpad = getPackageManager().hasSystemFeature("android.software.leanback");
    button.setFocusable(dpad && (mUi == null || mUi.dpadFocusEnabled));
    button.setFocusableInTouchMode(false);
    int target = mTheme == null ? 52 : mTheme.touchTarget;
    if (mUi != null) target = Math.max(target, mUi.minimumTargetDp);
    button.setMinHeight(dp(target));
    button.setMinWidth(dp(target));
    button.setStateListAnimator(null);
    button.setHapticFeedbackEnabled(true);
    button.setSoundEffectsEnabled(true);
    button.setPadding(dp(10), dp(6), dp(10), dp(6));
    button.setBackground(focusSurface(
        cobraThemeColor("panel", mTheme.panel),
        cobraThemeColor("focus", mTheme.focus), 14));
    return button;
  }'''
    java = replace_method(java, "  private Button action(String value) {", action)

    cache_and_loader = r'''  private File cobraLibraryCacheFile() {
    return new File(getFilesDir(), COBRA_LIBRARY_CACHE_FILE);
  }

  private String cobraSourceFingerprint(List<LiveSource> enabled) {
    StringBuilder material = new StringBuilder();
    for (LiveSource source : enabled) {
      material.append(source.id).append('|').append(source.type).append('|')
          .append(source.server).append('|').append(source.username).append('|')
          .append(source.password).append('|').append(source.playlistUrl).append('|')
          .append(source.epgUrl).append('|').append(mFeatures.sourceEnabled(source.id)).append('\n');
    }
    try {
      byte[] digest = java.security.MessageDigest.getInstance("SHA-256")
          .digest(material.toString().getBytes(StandardCharsets.UTF_8));
      StringBuilder out = new StringBuilder();
      for (byte b : digest) out.append(String.format(Locale.US, "%02x", b & 0xff));
      return out.toString();
    } catch (Exception ignored) {
      return Integer.toHexString(material.toString().hashCode());
    }
  }

  private boolean restoreCobraLibraryCache(ArrayList<LiveSource> enabled) {
    File file = cobraLibraryCacheFile();
    if (!file.isFile() || file.length() <= 0 || file.length() > 32L * 1024L * 1024L) return false;
    try {
      JSONObject root = new JSONObject(readText(new java.io.FileInputStream(file)));
      if (root.optInt("schema", 0) != 1) return false;
      if (!cobraSourceFingerprint(enabled).equals(root.optString("source_fingerprint", ""))) return false;
      JSONArray rows = root.optJSONArray("channels");
      if (rows == null || rows.length() == 0 || rows.length() > MAX_CHANNELS) return false;
      ArrayList<Channel> restored = new ArrayList<>();
      for (int i = 0; i < rows.length(); i++) {
        JSONObject row = rows.optJSONObject(i); if (row == null) continue;
        String primary = row.optString("primary_url", "");
        if (primary.isEmpty()) continue;
        HashMap<String, String> headers = new HashMap<>();
        JSONObject encodedHeaders = row.optJSONObject("headers");
        if (encodedHeaders != null) {
          JSONArray names = encodedHeaders.names();
          if (names != null) for (int h = 0; h < names.length(); h++) {
            String name = names.optString(h, "");
            if (!name.isEmpty()) headers.put(name, encodedHeaders.optString(name, ""));
          }
        }
        restored.add(new Channel(
            row.optString("id", ""), row.optString("name", "Live channel"),
            row.optString("group", "Other"), row.optString("epg_id", ""),
            row.optString("icon", ""), primary, row.optString("fallback_url", ""), headers));
      }
      if (restored.isEmpty()) return false;
      mChannels.clear(); mChannels.addAll(restored);
      String active = mPrefs.getString(ACTIVE_SOURCE, "");
      mActiveSource = null;
      for (LiveSource source : enabled) if (source.id.equals(active)) { mActiveSource = source; break; }
      if (mActiveSource == null && !enabled.isEmpty()) mActiveSource = enabled.get(0);
      status(restored.size() + " channels • saved library • refreshing quietly");
      showCobraPrimaryView();
      return true;
    } catch (Exception ignored) {
      return false;
    }
  }

  private void saveCobraLibraryCache(ArrayList<LiveSource> enabled, ArrayList<Channel> channels) {
    if (channels == null || channels.isEmpty()) return;
    try {
      JSONObject root = new JSONObject();
      root.put("schema", 1);
      root.put("saved_at", System.currentTimeMillis());
      root.put("source_fingerprint", cobraSourceFingerprint(enabled));
      JSONArray rows = new JSONArray();
      int limit = Math.min(MAX_CHANNELS, channels.size());
      for (int i = 0; i < limit; i++) {
        Channel channel = channels.get(i);
        JSONObject row = new JSONObject();
        row.put("id", channel.id); row.put("name", channel.name); row.put("group", channel.group);
        row.put("epg_id", channel.epgId); row.put("icon", channel.icon);
        row.put("primary_url", channel.primaryUrl); row.put("fallback_url", channel.fallbackUrl);
        JSONObject headers = new JSONObject();
        if (channel.headers != null) for (Map.Entry<String, String> entry : channel.headers.entrySet())
          headers.put(entry.getKey(), entry.getValue());
        row.put("headers", headers); rows.put(row);
      }
      root.put("channels", rows);
      byte[] data = root.toString().getBytes(StandardCharsets.UTF_8);
      if (data.length > 32 * 1024 * 1024) return;
      File file = cobraLibraryCacheFile();
      File tmp = new File(file.getParentFile(), file.getName() + ".tmp");
      try (java.io.FileOutputStream out = new java.io.FileOutputStream(tmp)) {
        out.write(data); out.getFD().sync();
      }
      if (file.exists() && !file.delete()) { tmp.delete(); return; }
      if (!tmp.renameTo(file)) tmp.delete();
    } catch (Exception ignored) {}
  }

  private boolean cobraLibrariesEqual(List<Channel> current, List<Channel> next) {
    if (current == null || next == null || current.size() != next.size()) return false;
    for (int i = 0; i < current.size(); i++) {
      Channel a = current.get(i), b = next.get(i);
      if (!a.id.equals(b.id) || !a.primaryUrl.equals(b.primaryUrl)) return false;
    }
    return true;
  }

  private void loadAllEnabledSources(boolean showBusy) {
    if (mSources.isEmpty()) { showWelcome(); return; }
    final ArrayList<LiveSource> enabled = new ArrayList<>();
    for (LiveSource source : mSources) if (mFeatures.sourceEnabled(source.id)) enabled.add(source);
    if (enabled.isEmpty()) { status("No sources enabled"); showSources(); return; }

    boolean warm = !mChannels.isEmpty();
    if (!warm) warm = restoreCobraLibraryCache(enabled);
    if (showBusy && !warm) {
      clearStage("COBRA • LIVE TV");
      status("Loading enabled TV sources…");
      mStage.addView(text("BUILDING YOUR LIVE LIBRARY…", cobraThemeColor("muted", mTheme.muted),
          16, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1));
    } else if (warm) {
      status(mChannels.size() + " channels • refreshing in background");
    }

    final boolean hadWarmLibrary = warm;
    final ArrayList<Channel> previous = new ArrayList<>(mChannels);
    if (!submitCobraIo(() -> {
      ArrayList<Channel> merged = new ArrayList<>();
      ArrayList<String> failures = new ArrayList<>();
      for (LiveSource source : enabled) {
        try {
          LoadResult result = loadSource(source, false);
          merged.addAll(result.channels);
        } catch (LiveException error) {
          failures.add(source.name + ": " + error.userMessage);
          for (Channel cached : previous)
            if (cached.id != null && cached.id.startsWith(source.id + ":")) merged.add(cached);
        }
      }
      final ArrayList<Channel> resolved = merged;
      publishCobraUi(() -> {
        if (resolved.isEmpty()) {
          if (hadWarmLibrary && !mChannels.isEmpty()) {
            status(mChannels.size() + " channels • using saved library • refresh unavailable");
            return;
          }
          clearStage("COBRA • SOURCE ERROR");
          status("No enabled source could load");
          String message = failures.isEmpty() ? "No playable channels were returned."
              : android.text.TextUtils.join("\n\n", failures);
          mStage.addView(text(message, cobraThemeColor("text", mTheme.text), 15, Gravity.CENTER),
              new LinearLayout.LayoutParams(-1, 0, 1));
          return;
        }
        boolean changed = !cobraLibrariesEqual(mChannels, resolved);
        mChannels.clear(); mChannels.addAll(resolved);
        if (mActiveSource == null || !mFeatures.sourceEnabled(mActiveSource.id)) mActiveSource = enabled.get(0);
        if (!hadWarmLibrary) { mCategory = "ALL"; mSearch = ""; }
        String suffix = failures.isEmpty() ? "ready" : (failures.size() + " source refresh unavailable");
        status(resolved.size() + " channels • " + enabled.size() + " enabled source"
            + (enabled.size() == 1 ? "" : "s") + " • " + suffix);
        if ((!hadWarmLibrary || changed) && mPlayerOverlay == null && mMultiOverlay == null)
          showCobraPrimaryView();
        final ArrayList<Channel> persist = new ArrayList<>(resolved);
        submitCobraIo(() -> saveCobraLibraryCache(enabled, persist));
        for (LiveSource source : enabled) loadGuideAsync(source);
        mFeatures.writeHealth("live", mActiveSource == null ? "" : mActiveSource.id,
            "", "ready", failures.isEmpty() ? "" : failures.get(0), 0, 0, -1, "idle", "loading");
      });
    })) {
      if (!warm) toast("Cobra is closing; source refresh was skipped");
    }
  }'''
    java = replace_method(java, "  private void loadAllEnabledSources(boolean showBusy) {", cache_and_loader)

    a, b = span(java, "  private void toggleCobraDrawer() {")
    drawer = java[a:b]
    tv_anchor = '    addCobraDrawerAction(menu, "TV", v -> {\n'
    if drawer.count(tv_anchor) != 1:
        raise RuntimeError("final drawer TV anchor missing")
    mobile_entry = r'''    addCobraDrawerAction(menu, "MOBILE", v -> {
      mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "mobile").apply();
      mCobraInternalScreen = "root";
      showCobraMobileView();
    });
'''
    drawer = drawer.replace(tv_anchor, mobile_entry + tv_anchor, 1)
    java = java[:a] + drawer + java[b:]

    preview = r'''  private Button cobraVideoButton(String label, String description) {
    Button button = action(label);
    button.setContentDescription(description);
    button.setTextColor(Color.WHITE);
    button.setTextSize(13);
    button.setAllCaps(false);
    button.setMinWidth(0); button.setMinimumWidth(0);
    button.setMinHeight(dp(44));
    button.setPadding(dp(6), dp(4), dp(6), dp(4));
    button.setBackground(surface(Color.argb(220, 12, 18, 26), 17,
        Color.argb(78, 255, 255, 255), 1));
    return button;
  }

  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {
    stopCobraPreview();
    FrameLayout host = new FrameLayout(this);
    mCobraPreviewHost = host;
    host.setTag("cobra_preview_host");
    host.setBackground(surface(Color.BLACK, 22, Color.rgb(34, 44, 56), 1));
    host.setClickable(true);

    mCobraPreviewTexture = new TextureView(this);
    host.addView(mCobraPreviewTexture, new FrameLayout.LayoutParams(-1, -1));

    TextView badge = text(channel == null ? "SELECT A CHANNEL" : "LIVE  •  " + channel.name,
        Color.WHITE, 11, Gravity.RIGHT | Gravity.CENTER_VERTICAL);
    badge.setTag("cobra_preview_label");
    badge.setPadding(dp(10), dp(3), dp(10), dp(3));
    badge.setBackground(surface(Color.argb(180, 3, 7, 12), 13,
        Color.argb(60, 255, 255, 255), 1));
    FrameLayout.LayoutParams badgeP = new FrameLayout.LayoutParams(-2, dp(32), Gravity.TOP | Gravity.RIGHT);
    badgeP.setMargins(dp(10), dp(10), dp(10), 0);
    host.addView(badge, badgeP);

    if (channel != null) {
      LinearLayout controls = new LinearLayout(this);
      controls.setGravity(Gravity.CENTER);
      controls.setPadding(dp(8), dp(5), dp(8), dp(5));
      controls.setBackgroundColor(Color.argb(188, 3, 7, 12));
      Button fullscreen = cobraVideoButton("⛶", "Fullscreen");
      Button favorite = cobraVideoButton(mFavorites.contains(channel.id) ? "♥" : "♡", "Favorite");
      favorite.setTag("cobra_preview_favorite");
      Button schedule = cobraVideoButton("◷", "Schedule recording");
      Button captions = cobraVideoButton("CC", "Closed captions");
      Button volume = cobraVideoButton(mCobraPreviewMuted ? "MUTE" : "VOL", "Volume");
      Button more = cobraVideoButton("⋮", "More channel actions");
      fullscreen.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel; if (active != null) promoteCobraPreviewToFullscreen(active);
      });
      favorite.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel; if (active == null) return;
        toggleFavorite(active); favorite.setText(mFavorites.contains(active.id) ? "♥" : "♡");
      });
      schedule.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel; if (active != null) showCobraScheduleRecording(active);
      });
      captions.setOnClickListener(v -> toggleCobraPreviewCaptions());
      volume.setOnClickListener(v -> { toggleCobraPreviewMute(); volume.setText(mCobraPreviewMuted ? "MUTE" : "VOL"); });
      more.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel; if (active != null) showCobraChannelActions(active);
      });
      for (Button button : new Button[]{fullscreen, favorite, schedule, captions, volume, more})
        controls.addView(button, new LinearLayout.LayoutParams(0, dp(44), 1));
      host.addView(controls, new FrameLayout.LayoutParams(-1, dp(54), Gravity.BOTTOM));
    }

    host.setOnClickListener(v -> {
      Channel active = mGuidePreviewChannel; if (active != null) promoteCobraPreviewToFullscreen(active);
    });
    if (channel != null) host.post(() -> {
      String key = cobraChannelKey(channel);
      if (mCobraTransferPlayer != null && key.equals(mCobraTransferKey)) {
        ExoPlayer transfer = mCobraTransferPlayer;
        mCobraTransferPlayer = null; mCobraTransferKey = "";
        mCobraPreviewPlayer = transfer;
        try { transfer.setVideoTextureView(mCobraPreviewTexture); } catch (Exception ignored) {}
        transfer.setVolume(mCobraPreviewMuted ? 0f : 1f);
        setCobraPreviewLabel("LIVE PREVIEW  •  " + channel.name + "  •  TAP VIDEO FOR FULLSCREEN");
        updateCobraPreviewDetails();
      } else {
        releaseCobraTransferPlayer();
        startCobraPreview(channel);
      }
    });
    return host;
  }'''
    java = replace_method(java, "  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {", preview)

    details = r'''  private View cobraPreviewDetails(Channel channel) {
    LinearLayout info = new LinearLayout(this);
    info.setOrientation(LinearLayout.VERTICAL);
    info.setPadding(dp(4), dp(6), dp(4), dp(6));
    LinearLayout titleRow = new LinearLayout(this);
    titleRow.setGravity(Gravity.CENTER_VERTICAL);
    TextView title = text(channel == null ? "Choose a channel" : channel.name,
        cobraThemeColor("text", mTheme.text), 17, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    title.setTag("cobra_preview_detail_title"); title.setTypeface(null, Typeface.BOLD);
    Button epg = action("EPG");
    epg.setTag("cobra_preview_epg");
    epg.setOnClickListener(v -> {
      Channel active = mGuidePreviewChannel; if (active != null) showProgramGuide(active);
    });
    titleRow.addView(title, new LinearLayout.LayoutParams(0, dp(44), 1));
    titleRow.addView(epg, new LinearLayout.LayoutParams(dp(92), dp(42)));
    info.addView(titleRow, new LinearLayout.LayoutParams(-1, dp(46)));
    TextView summary = text("", cobraThemeColor("muted", mTheme.muted), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    summary.setTag("cobra_preview_detail_summary");
    info.addView(summary, new LinearLayout.LayoutParams(-1, dp(34)));
    updateCobraPreviewDetails();
    return info;
  }

  private void updateCobraPreviewDetails() {
    if (mStage == null) return;
    Channel channel = mGuidePreviewChannel;
    View titleView = mStage.findViewWithTag("cobra_preview_detail_title");
    View summaryView = mStage.findViewWithTag("cobra_preview_detail_summary");
    if (titleView instanceof TextView)
      ((TextView) titleView).setText(channel == null ? "Choose a channel" : channel.name);
    if (summaryView instanceof TextView) {
      if (channel == null) ((TextView) summaryView).setText("Select a channel to begin");
      else {
        ProgramPair pair = programFor(channel);
        String value = pair != null && pair.now != null && !pair.now.isEmpty()
            ? "NOW  •  " + pair.now : providerBadge(channel) + "  •  " + channel.group;
        ((TextView) summaryView).setText(value);
      }
    }
    if (mCobraPreviewHost != null) {
      View favorite = mCobraPreviewHost.findViewWithTag("cobra_preview_favorite");
      if (favorite instanceof Button && channel != null)
        ((Button) favorite).setText(mFavorites.contains(channel.id) ? "♥" : "♡");
    }
  }

  private void releaseCobraTransferPlayer() {
    ExoPlayer player = mCobraTransferPlayer;
    mCobraTransferPlayer = null; mCobraTransferKey = "";
    if (player == null) return;
    try { player.stop(); } catch (Exception ignored) {}
    try { player.release(); } catch (Exception ignored) {}
  }'''
    java = replace_method(java, "  private View cobraPreviewDetails(Channel channel) {", details)

    select = r'''  private void selectGuidePreview(Channel channel) {
    String key = cobraChannelKey(channel);
    if (key.equals(mGuidePreviewKey) && mGuidePreviewChannel != null
        && mGuidePreviewArmed && mUi.guideSecondActivationFullscreen) {
      promoteCobraPreviewToFullscreen(channel);
      return;
    }
    mGuidePreviewChannel = channel;
    mGuidePreviewKey = key;
    mGuidePreviewArmed = true;
    if (!mUi.guideFirstActivationPreview) { promoteCobraPreviewToFullscreen(channel); return; }
    if (mCobraPreviewHost != null && mCobraPreviewTexture != null) {
      setCobraPreviewLabel("CONNECTING  •  " + channel.name);
      startCobraPreview(channel);
      updateCobraPreviewDetails();
      return;
    }
    showCobraPrimaryView();
  }'''
    java = replace_method(java, "  private void selectGuidePreview(Channel channel) {", select)

    handoff = r'''  private void promoteCobraPreviewToFullscreen(Channel channel) {
    if (channel == null) return;
    String key = cobraChannelKey(channel);
    ExoPlayer session = key.equals(mGuidePreviewKey) ? mCobraPreviewPlayer : null;
    if (session == null) { stopCobraPreview(); playChannel(channel); return; }

    mCobraPreviewPlayer = null;
    try { if (mCobraPreviewTexture != null) session.clearVideoTextureView(mCobraPreviewTexture); }
    catch (Exception ignored) {}
    mCobraPreviewTexture = null; mCobraPreviewHost = null;
    releaseMulti();
    if (mPlayerOverlay != null) closePlayer();
    mPlaying = channel; mPlayingIndex = mChannels.indexOf(channel); mTriedFallback = false;
    addRecent(channel);
    openPlayerOverlay(channel);
    mPlayer = session;
    try { session.setVideoTextureView(mPlayerTexture); } catch (Exception ignored) {}
    session.setVolume(1f);
    TextView state = mPlayerOverlay == null ? null
        : (TextView) mPlayerOverlay.findViewWithTag("player_state");
    if (state != null) state.setText("LIVE");
    final ExoPlayer active = session;
    active.addListener(new Player.Listener() {
      @Override public void onPlaybackStateChanged(int playbackState) {
        if (mPlayer != active || state == null) return;
        if (playbackState == Player.STATE_BUFFERING) state.setText("BUFFERING");
        else if (playbackState == Player.STATE_READY) state.setText("LIVE");
        else if (playbackState == Player.STATE_ENDED) state.setText("ENDED");
      }
      @Override public void onPlayerError(PlaybackException error) {
        if (mPlayer != active || mPlaying == null) return;
        if (!mTriedFallback && mPlaying.fallbackUrl != null && !mPlaying.fallbackUrl.isEmpty()) {
          mTriedFallback = true; mPlaybackRetryCount++;
          if (state != null) state.setText("RETRYING STREAM");
          active.setMediaItem(mediaItem(mPlaying.fallbackUrl)); active.prepare(); active.play();
          return;
        }
        if (state != null) state.setText("STREAM ERROR");
        showPlayerError(error);
      }
    });
    if (mPlayerTexture != null) mPlayerTexture.post(() -> applyCobraAspectTransform());
  }

  private void closeFullscreenToCobraView() {
    Channel playing = mPlaying;
    if (mPlayer != null && playing != null && mGuidePreviewChannel != null
        && cobraChannelKey(playing).equals(cobraChannelKey(mGuidePreviewChannel))) {
      ExoPlayer session = mPlayer; mPlayer = null;
      try { if (mPlayerTexture != null) session.clearVideoTextureView(mPlayerTexture); }
      catch (Exception ignored) {}
      if (mPlayerOverlay != null) try {
        ((FrameLayout) getWindow().getDecorView()).removeView(mPlayerOverlay);
      } catch (Exception ignored) {}
      mPlayerOverlay = null; mPlayerTexture = null; mPlayerChrome = null;
      mPlaying = null; mPlayingIndex = -1;
      mCobraTransferPlayer = session; mCobraTransferKey = cobraChannelKey(playing);
      showCobraPrimaryView();
      if (mCobraTransferPlayer != null) releaseCobraTransferPlayer();
      return;
    }
    closePlayer();
    if (mGuidePreviewChannel != null) showCobraPrimaryView();
  }'''
    java = replace_method(java, "  private void promoteCobraPreviewToFullscreen(Channel channel) {", handoff)
    if java.count("  private void closeFullscreenToCobraView() {") != 2:
        raise RuntimeError("fullscreen handoff duplicate expectation failed")
    first = java.find("  private void closeFullscreenToCobraView() {")
    second = java.find("  private void closeFullscreenToCobraView() {", first + 1)
    end = method_end(java, second)
    java = java[:second] + java[end:]

    virtual_helpers = r'''  private boolean cobraTouchFirstDevice() {
    return !getPackageManager().hasSystemFeature("android.software.leanback");
  }

  private int cobraWidthDp() {
    return Math.round(getResources().getDisplayMetrics().widthPixels /
        getResources().getDisplayMetrics().density);
  }

  private int cobraHeightDp() {
    return Math.round(getResources().getDisplayMetrics().heightPixels /
        getResources().getDisplayMetrics().density);
  }

  private android.widget.BaseAdapter cobraChannelAdapter(
      final ArrayList<Channel> channels, final String style) {
    return new android.widget.BaseAdapter() {
      @Override public int getCount() { return channels.size(); }
      @Override public Channel getItem(int position) { return channels.get(position); }
      @Override public long getItemId(int position) { return position; }
      @Override public View getView(int position, View convertView, android.view.ViewGroup parent) {
        Button row = convertView instanceof Button ? (Button) convertView : action("");
        Channel channel = channels.get(position);
        ProgramPair pair = programFor(channel);
        String now = pair != null && pair.now != null && !pair.now.isEmpty() ? pair.now : "No guide data";
        String next = pair != null && pair.next != null && !pair.next.isEmpty() ? pair.next : "—";
        int height; float textSize;
        if ("compact".equals(style)) {
          height = 48; textSize = 12f;
          row.setText(String.format(Locale.US, "%03d  %s  •  %s", position + 1, channel.name, now));
        } else if ("cards".equals(style)) {
          height = isPortrait() ? 116 : 104; textSize = 14f;
          row.setText(channel.name + "\nNOW  •  " + now + "\nNEXT  •  " + next);
        } else if ("focus".equals(style)) {
          height = isPortrait() ? 92 : 78; textSize = 13f;
          row.setText(channel.name + "\n" + now);
        } else if ("grid_portrait".equals(style)) {
          height = 74; textSize = 13f;
          row.setText(channel.name + "\nNOW  •  " + now + "     NEXT  •  " + next);
        } else {
          height = Math.max(66, mUi.mobileChannelRowHeightDp); textSize = 13f;
          row.setText(channel.name + "\n" + mobileGuideSummary(channel));
        }
        row.setTextSize(textSize); row.setAllCaps(false);
        row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
        row.setPadding(dp("cards".equals(style) ? 16 : 12), dp(6), dp(12), dp(6));
        row.setFocusable(!cobraTouchFirstDevice()); row.setFocusableInTouchMode(false);
        row.setBackground(focusSurface(cobraThemeColor("panel", mTheme.panel),
            cobraThemeColor("focus", mTheme.focus), "cards".equals(style) ? 18 : 13));
        row.setOnClickListener(v -> selectGuidePreview(channel));
        row.setOnLongClickListener(v -> { showCobraChannelActions(channel); return true; });
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(height)));
        return row;
      }
    };
  }

  private android.widget.ListView cobraChannelList(ArrayList<Channel> channels, String style) {
    android.widget.ListView list = new android.widget.ListView(this);
    list.setAdapter(cobraChannelAdapter(channels, style));
    list.setDividerHeight(dp(3)); list.setSelector(android.R.color.transparent);
    list.setClipToPadding(false); list.setPadding(0, dp(3), 0, dp(8));
    list.setFastScrollEnabled(channels.size() > 180); list.setSmoothScrollbarEnabled(true);
    list.setScrollingCacheEnabled(true);
    return list;
  }

  private android.widget.GridView cobraChannelGrid(
      ArrayList<Channel> channels, String style, int columns) {
    android.widget.GridView grid = new android.widget.GridView(this);
    grid.setNumColumns(Math.max(1, columns));
    grid.setHorizontalSpacing(dp(8)); grid.setVerticalSpacing(dp(8));
    grid.setStretchMode(android.widget.GridView.STRETCH_COLUMN_WIDTH);
    grid.setAdapter(cobraChannelAdapter(channels, style));
    grid.setSelector(android.R.color.transparent); grid.setClipToPadding(false);
    grid.setPadding(dp(3), dp(3), dp(3), dp(8));
    grid.setFastScrollEnabled(channels.size() > 180); grid.setScrollingCacheEnabled(true);
    return grid;
  }

  private android.widget.BaseAdapter cobraTimelineAdapter(
      final ArrayList<Channel> channels, final long slot,
      final int channelWidthDp, final int programWidthDp) {
    return new android.widget.BaseAdapter() {
      @Override public int getCount() { return channels.size(); }
      @Override public Channel getItem(int position) { return channels.get(position); }
      @Override public long getItemId(int position) { return position; }
      @Override public View getView(int position, View convertView, android.view.ViewGroup parent) {
        LinearLayout row = convertView instanceof LinearLayout ? (LinearLayout) convertView : new LinearLayout(InfinityLiveActivity.this);
        if (row.getChildCount() != 4) {
          row.removeAllViews(); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL);
          for (int i = 0; i < 4; i++) row.addView(action(""));
        }
        Channel channel = channels.get(position);
        for (int i = 0; i < 4; i++) {
          Button cell = (Button) row.getChildAt(i);
          cell.setAllCaps(false); cell.setTextSize(i == 0 ? 12 : 11);
          cell.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL); cell.setFocusable(!cobraTouchFirstDevice());
          if (i == 0) cell.setText(String.format(Locale.US, "%03d  %s", position + 1, channel.name));
          else cell.setText(guideTitleAt(channel, slot + (i - 1) * 1800000L));
          cell.setOnClickListener(v -> selectGuidePreview(channel));
          cell.setOnLongClickListener(v -> { showCobraChannelActions(channel); return true; });
          cell.setLayoutParams(new LinearLayout.LayoutParams(dp(i == 0 ? channelWidthDp : programWidthDp),
              dp(mUi.guideRowHeightDp)));
        }
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(
            dp(channelWidthDp + programWidthDp * 3), dp(mUi.guideRowHeightDp + 2)));
        return row;
      }
    };
  }

  private LinearLayout cobraModeToolbar(String title) {
    LinearLayout bar = new LinearLayout(this); bar.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("‹  CATEGORIES"); categories.setOnClickListener(v -> showCobraTvHub());
    TextView label = text(title, cobraThemeColor("accent_soft", mTheme.accentSoft), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL); label.setTypeface(null, Typeface.BOLD);
    int categoryWidth = Math.min(148, Math.max(112, cobraWidthDp() / 3));
    bar.addView(categories, new LinearLayout.LayoutParams(dp(categoryWidth), dp(50)));
    bar.addView(label, new LinearLayout.LayoutParams(0, dp(50), 1));
    return bar;
  }

  private int cobraPreviewHeight(boolean compact) {
    int screen = cobraHeightDp();
    if (isPortrait()) return compact ? Math.max(118, Math.min(150, screen / 6))
        : Math.max(190, Math.min(270, screen / 3));
    return compact ? 108 : Math.max(138, Math.min(190, screen / 3));
  }

  private void showCobraMobileView() {
    stopCobraPreview();
    clearStage("COBRA • MOBILE");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "mobile").apply();
    mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView();
    ensureCobraPreviewSelection(visible);

    LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
    if (mUi.mobilePreviewFirst) {
      root.addView(cobraPreviewPanel(mGuidePreviewChannel, false),
          new LinearLayout.LayoutParams(-1, dp(cobraPreviewHeight(false))));
      root.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(82)));
    }
    LinearLayout tools = new LinearLayout(this); tools.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("CATEGORIES"); Button search = action("SEARCH"); Button tv = action("TV GUIDE");
    categories.setOnClickListener(v -> showCobraTvHub());
    search.setOnClickListener(v -> { stopCobraPreview(); mCobraInternalScreen = "internal"; showSearch(); });
    tv.setOnClickListener(v -> { mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply(); showGuide(); });
    tools.addView(categories, new LinearLayout.LayoutParams(0, dp(52), 1.15f));
    tools.addView(search, new LinearLayout.LayoutParams(0, dp(52), .85f));
    tools.addView(tv, new LinearLayout.LayoutParams(0, dp(52), 1f));
    root.addView(tools, new LinearLayout.LayoutParams(-1, dp(55)));
    TextView heading = text("CHANNELS  •  " + visible.size(), cobraThemeColor("muted", mTheme.muted), 11,
        Gravity.LEFT | Gravity.CENTER_VERTICAL); heading.setLetterSpacing(.10f);
    root.addView(heading, new LinearLayout.LayoutParams(-1, dp(34)));
    if (visible.isEmpty()) root.addView(text("No channels in this view", cobraThemeColor("muted", mTheme.muted),
        15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1));
    else root.addView(cobraChannelList(visible, "mobile"), new LinearLayout.LayoutParams(-1, 0, 1));
    mStage.addView(root, new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    java = replace_method(java, "  private void showCobraMobileView() {", virtual_helpers)

    grid = r'''  private void showGuideGrid() {
    stopCobraPreview(); clearStage("COBRA • TV GRID");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply(); mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView(); ensureCobraPreviewSelection(visible);
    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(cobraPreviewHeight(false))));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(82)));
    }
    mStage.addView(cobraModeToolbar("TV GRID  •  " + visible.size() + " CHANNELS"),
        new LinearLayout.LayoutParams(-1, dp(52)));
    if (visible.isEmpty()) { mStage.addView(text("No channels in this view", cobraThemeColor("muted", mTheme.muted),
        15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1)); return; }
    if (isPortrait()) {
      mStage.addView(cobraChannelList(visible, "grid_portrait"), new LinearLayout.LayoutParams(-1, 0, 1));
      return;
    }
    long now = System.currentTimeMillis(); long slot = now - (now % 1800000L);
    int width = cobraWidthDp(); int channelWidth = Math.max(132, Math.min(178, width / 5));
    int programWidth = Math.max(142, (width - channelWidth - 38) / 3);
    LinearLayout header = new LinearLayout(this); header.setGravity(Gravity.CENTER_VERTICAL);
    header.setBackground(surface(cobraThemeColor("panel", mTheme.panel), 12,
        cobraThemeColor("line", mTheme.line), 1));
    header.addView(text("CHANNEL", cobraThemeColor("muted", mTheme.muted), 11, Gravity.LEFT | Gravity.CENTER_VERTICAL),
        new LinearLayout.LayoutParams(dp(channelWidth), dp(mUi.guideHeaderHeightDp)));
    SimpleDateFormat clock = new SimpleDateFormat("h:mm a", Locale.US);
    for (int i = 0; i < 3; i++) header.addView(text((i == 0 ? "NOW  •  " : "") +
        clock.format(new Date(slot + i * 1800000L)), i == 0 ? cobraThemeColor("accent_soft", mTheme.accentSoft)
            : cobraThemeColor("muted", mTheme.muted), 11, Gravity.CENTER),
        new LinearLayout.LayoutParams(dp(programWidth), dp(mUi.guideHeaderHeightDp)));
    mStage.addView(header, new LinearLayout.LayoutParams(-1, dp(mUi.guideHeaderHeightDp)));
    android.widget.ListView timeline = new android.widget.ListView(this);
    timeline.setAdapter(cobraTimelineAdapter(visible, slot, channelWidth, programWidth));
    timeline.setDividerHeight(dp(2)); timeline.setSelector(android.R.color.transparent);
    timeline.setFastScrollEnabled(visible.size() > 180); timeline.setScrollingCacheEnabled(true);
    mStage.addView(timeline, new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    java = replace_method(java, "  private void showGuideGrid() {", grid)

    compact = r'''  private void showGuideCompact() {
    stopCobraPreview(); clearStage("COBRA • COMPACT");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply(); mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView(); ensureCobraPreviewSelection(visible);
    if (mUi.guidePreviewPlayer) mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
        new LinearLayout.LayoutParams(-1, dp(cobraPreviewHeight(true))));
    mStage.addView(cobraModeToolbar("COMPACT  •  FAST BROWSE  •  " + visible.size()),
        new LinearLayout.LayoutParams(-1, dp(52)));
    if (visible.isEmpty()) mStage.addView(text("No channels in this view", cobraThemeColor("muted", mTheme.muted),
        15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1));
    else mStage.addView(cobraChannelList(visible, "compact"), new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    java = replace_method(java, "  private void showGuideCompact() {", compact)

    cards = r'''  private void showGuideCards() {
    stopCobraPreview(); clearStage("COBRA • CARDS");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply(); mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView(); ensureCobraPreviewSelection(visible);
    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(cobraPreviewHeight(false))));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(82)));
    }
    mStage.addView(cobraModeToolbar("CARDS  •  TOUCH BROWSE  •  " + visible.size()),
        new LinearLayout.LayoutParams(-1, dp(52)));
    int width = cobraWidthDp(); int columns = isPortrait() ? (width >= 380 ? 2 : 1) : (width >= 1000 ? 4 : 3);
    if (visible.isEmpty()) mStage.addView(text("No channels in this view", cobraThemeColor("muted", mTheme.muted),
        15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1));
    else mStage.addView(cobraChannelGrid(visible, "cards", columns), new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    java = replace_method(java, "  private void showGuideCards() {", cards)

    focus = r'''  private void showGuideFocus() {
    stopCobraPreview(); clearStage("COBRA • FOCUS");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply(); mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView(); ensureCobraPreviewSelection(visible);
    mStage.addView(cobraModeToolbar("FOCUS  •  CINEMATIC BROWSE  •  " + visible.size()),
        new LinearLayout.LayoutParams(-1, dp(52)));
    if (visible.isEmpty()) { mStage.addView(text("No channels in this view", cobraThemeColor("muted", mTheme.muted),
        15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1)); return; }
    if (isPortrait()) {
      if (mUi.guidePreviewPlayer) {
        mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
            new LinearLayout.LayoutParams(-1, dp(Math.max(215, Math.min(300, cobraHeightDp() / 3)))));
        mStage.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(84)));
      }
      int columns = cobraWidthDp() >= 350 ? 2 : 1;
      mStage.addView(cobraChannelGrid(visible, "focus", columns), new LinearLayout.LayoutParams(-1, 0, 1));
      return;
    }
    LinearLayout split = new LinearLayout(this); split.setOrientation(LinearLayout.HORIZONTAL);
    LinearLayout hero = new LinearLayout(this); hero.setOrientation(LinearLayout.VERTICAL);
    if (mUi.guidePreviewPlayer) {
      hero.addView(cobraPreviewPanel(mGuidePreviewChannel, true), new LinearLayout.LayoutParams(-1, 0, 1));
      hero.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(86)));
    }
    split.addView(hero, new LinearLayout.LayoutParams(0, -1, 1.75f));
    LinearLayout.LayoutParams rail = new LinearLayout.LayoutParams(0, -1, 1f); rail.leftMargin = dp(10);
    split.addView(cobraChannelList(visible, "focus"), rail);
    mStage.addView(split, new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    java = replace_method(java, "  private void showGuideFocus() {", focus)

    player_overlay = r'''  private void openPlayerOverlay(Channel channel) {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mPlayerOverlay = new FrameLayout(this); mPlayerOverlay.setBackgroundColor(Color.BLACK);
    mPlayerOverlay.setFocusable(true); mPlayerOverlay.setFocusableInTouchMode(true);
    mPlayerTexture = new TextureView(this); mAspectMode = mPrefs.getInt(COBRA_ASPECT_MODE, 0);
    mPlayerOverlay.addView(mPlayerTexture, new FrameLayout.LayoutParams(-1, -1));

    mPlayerChrome = new LinearLayout(this); mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(8), dp(5), dp(8), dp(6));
    mPlayerChrome.setBackgroundColor(Color.argb(214, 3, 7, 12));

    LinearLayout infoRow = new LinearLayout(this); infoRow.setGravity(Gravity.CENTER_VERTICAL);
    TextView info = text(channel.name + "\n" + providerBadge(channel) + "  •  " + channel.group,
        Color.WHITE, isPortrait() ? 13 : 15, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    info.setTypeface(null, Typeface.BOLD);
    Button aspect = cobraVideoButton("▣", "Aspect / Display");
    aspect.setOnClickListener(v -> showCobraAspectPicker());
    TextView state = text("CONNECTING", Color.WHITE, 11, Gravity.RIGHT | Gravity.CENTER_VERTICAL);
    state.setTag("player_state"); state.setBackgroundColor(Color.TRANSPARENT);
    infoRow.addView(info, new LinearLayout.LayoutParams(0, dp(48), 1));
    infoRow.addView(aspect, new LinearLayout.LayoutParams(dp(52), dp(42)));
    infoRow.addView(state, new LinearLayout.LayoutParams(dp(104), dp(42)));
    mPlayerChrome.addView(infoRow, new LinearLayout.LayoutParams(-1, dp(50)));

    LinearLayout controls = new LinearLayout(this); controls.setGravity(Gravity.CENTER);
    Button prev = cobraVideoButton("◀", "Previous channel");
    Button favorite = cobraVideoButton("★", "Favorite");
    Button guide = cobraVideoButton("▤", "Return to Cobra view");
    Button record = cobraVideoButton("●", "Record");
    Button multi = cobraVideoButton("▦", "Multi-View");
    Button next = cobraVideoButton("▶", "Next channel");
    Button settings = cobraVideoButton("⚙", "Player settings");
    prev.setOnClickListener(v -> stepChannel(-1)); favorite.setOnClickListener(v -> toggleFavorite(channel));
    guide.setOnClickListener(v -> closeFullscreenToCobraView()); record.setOnClickListener(v -> toggleRecording(channel));
    multi.setOnClickListener(v -> beginMultiView()); next.setOnClickListener(v -> stepChannel(1));
    settings.setOnClickListener(v -> showPlayerSettingsDrawer());
    for (Button button : mUi.orderPlayerActions(prev, favorite, guide, record, multi, next, settings)) {
      button.setMinWidth(0); button.setMinimumWidth(0);
      controls.addView(button, new LinearLayout.LayoutParams(0, dp(46), 1));
    }
    mPlayerChrome.addView(controls, new LinearLayout.LayoutParams(-1, dp(50)));

    FrameLayout.LayoutParams chromeParams = new FrameLayout.LayoutParams(-1, dp(108), Gravity.BOTTOM);
    mPlayerOverlay.addView(mPlayerChrome, chromeParams);
    mPlayerOverlay.setOnClickListener(v -> { if (!closePlayerSettingsDrawer()) togglePlayerChrome(); });
    mPlayerOverlay.setOnKeyListener((v, keyCode, event) -> {
      if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
      if (keyCode == KeyEvent.KEYCODE_DPAD_UP || keyCode == KeyEvent.KEYCODE_DPAD_DOWN
          || keyCode == KeyEvent.KEYCODE_DPAD_CENTER) showPlayerChromeTemporarily();
      return false;
    });
    decor.addView(mPlayerOverlay, new FrameLayout.LayoutParams(-1, -1));
    controls.requestFocus(); scheduleChromeHide();
    mFeatures.writeHealth("player", sourceIdForChannel(channel), channel.id,
        "connecting", "", mPlaybackRetryCount, 0, -1,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }'''
    java = replace_method(java, "  private void openPlayerOverlay(Channel channel) {", player_overlay)
    java = inject_after_signature(java, "  protected void onDestroy() {", "    releaseCobraTransferPlayer();")
    return java


def verify(java: str) -> None:
    required = (
        'COBRA_LIBRARY_CACHE_FILE = "cobra-live-library-v1.json"',
        'restoreCobraLibraryCache(enabled)', 'saveCobraLibraryCache(enabled, persist)',
        'saved library • refreshing quietly', 'refreshing in background',
        'addCobraDrawerAction(menu, "MOBILE"',
        'android.widget.BaseAdapter cobraChannelAdapter', 'android.widget.ListView cobraChannelList',
        'android.widget.GridView cobraChannelGrid', 'cobraTimelineAdapter(',
        'COBRA • MOBILE', 'COBRA • TV GRID', 'COBRA • COMPACT', 'COBRA • CARDS', 'COBRA • FOCUS',
        'if (isPortrait())', 'CINEMATIC BROWSE', 'FAST BROWSE', 'TOUCH BROWSE',
        'mCobraTransferPlayer', 'session.setVideoTextureView(mPlayerTexture)',
        'transfer.setVideoTextureView(mCobraPreviewTexture)',
        'setTag("cobra_preview_detail_title")', 'updateCobraPreviewDetails()',
        'cobraVideoButton("▣", "Aspect / Display")',
        'new FrameLayout.LayoutParams(-1, dp(108), Gravity.BOTTOM)',
        'mUi.orderPlayerActions(prev, favorite, guide, record, multi, next, settings)',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("2103150 iron-polish contract missing: " + token)
    if java.count('BUILDING YOUR LIVE LIBRARY…') != 1:
        raise RuntimeError("Cold-start building state should exist exactly once")
    if java.count("  private void closeFullscreenToCobraView() {") != 1:
        raise RuntimeError("Fullscreen handoff method duplicated")
    if java.count("  private void showCobraMobileView() {") != 1:
        raise RuntimeError("Mobile renderer duplicated")
    if java.count("  private void showGuideFocus() {") != 1:
        raise RuntimeError("Focus renderer duplicated")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra 2103150 warm-cache + virtualized modes + seamless video polish applied")


if __name__ == "__main__":
    main()
