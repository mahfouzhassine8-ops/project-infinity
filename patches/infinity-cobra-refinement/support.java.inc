// STATE
  private ExoPlayer mRefUiOwner;
  private Player.Listener mRefUiListener;
  private boolean mRefDrawerDocked = false;

// METHODS
  private void cobraObserveFullscreen() {
    if (mRefUiOwner != null && mRefUiListener != null) {
      try { mRefUiOwner.removeListener(mRefUiListener); } catch (Exception ignored) {}
    }
    mRefUiOwner = mPlayer; mRefUiListener = null;
    if (mPlayer == null) return;
    final ExoPlayer owner = mPlayer;
    mRefUiListener = new Player.Listener() {
      @Override public void onPlaybackStateChanged(int state) {
        if (mPlayer == owner) cobraRefreshFullscreen();
      }
      @Override public void onIsPlayingChanged(boolean playing) {
        if (mPlayer == owner) cobraRefreshFullscreen();
      }
      @Override public void onVideoSizeChanged(VideoSize size) {
        if (mPlayer == owner) applyCobraAspectTransform();
      }
      @Override public void onPlayerError(PlaybackException error) {
        if (mPlayer == owner) cobraRefreshFullscreen();
      }
    };
    owner.addListener(mRefUiListener);
    cobraRefreshFullscreen();
  }

  private void cobraRefreshFullscreen() {
    if (!isCobraAsyncAlive() || mPlayerOverlay == null || mPlayer == null) return;
    updateCobraPlayerPlayPause();
    View state = mPlayerOverlay.findViewWithTag("player_state");
    if (state instanceof TextView) {
      String value = mPlayer.getPlayerError() != null ? "STREAM ERROR"
          : mPlayer.getPlaybackState() == Player.STATE_BUFFERING ? "BUFFERING"
          : mPlayer.getPlaybackState() == Player.STATE_READY ? (!mPlayer.getPlayWhenReady() ? "PAUSED" : mPlayingVodKey.isEmpty() ? "LIVE" : "PLAYING")
          : mPlayer.getPlaybackState() == Player.STATE_ENDED ? "ENDED" : "CONNECTING";
      ((TextView) state).setText(value);
    }
    View progress = mPlayerOverlay.findViewWithTag("ref_program_progress");
    if (progress instanceof android.widget.ProgressBar) {
      GuideProgram current = cobraCurrentProgram(mPlaying);
      progress.setVisibility(current == null ? View.GONE : View.VISIBLE);
      if (current != null) ((android.widget.ProgressBar) progress).setProgress((int) Math.max(0, Math.min(1000,
          (System.currentTimeMillis() - current.start) * 1000L / (current.stop - current.start))));
    }
    applyCobraAspectTransform();
  }

  private GuideProgram cobraCurrentProgram(Channel channel) {
    long now = System.currentTimeMillis();
    GuideProgram best = null;
    for (GuideProgram p : cobraGuidePrograms(channel)) if (p.start <= now && now < p.stop && (best == null || p.start >= best.start)) best = p;
    return best;
  }

  private String cobraPlayerNow(Channel channel) {
    ProgramPair pair = programFor(channel);
    return pair != null && !pair.now.isEmpty() ? pair.now : cobraGuideStatus(channel);
  }

  private String cobraPlayerNext(Channel channel) {
    ProgramPair pair = programFor(channel);
    GuideProgram current = cobraCurrentProgram(channel);
    String when = current == null ? "" : new SimpleDateFormat("h:mm a", Locale.getDefault()).format(new Date(current.start))
        + "–" + new SimpleDateFormat("h:mm a", Locale.getDefault()).format(new Date(current.stop))
        + " · " + Math.max(1, (current.stop - System.currentTimeMillis() + 59999L) / 60000L) + " min left";
    String next = pair == null || pair.next.isEmpty() ? "" : "Next · " + pair.next;
    return when.isEmpty() ? next : next.isEmpty() ? when : when + "  |  " + next;
  }

  private void dockCobraPlayerForSheet() {
    if (mPlayerTexture == null || mPlayerOverlay == null || mRefSheetPanel == null) return;
    int w = mPlayerOverlay.getWidth(), h = mPlayerOverlay.getHeight();
    if (w <= 0 || h <= 0) return;
    mRefDrawerDocked = true;
    if (mPlayerChrome != null) mPlayerChrome.setVisibility(View.GONE);
    FrameLayout.LayoutParams sheetP = (FrameLayout.LayoutParams) mRefSheetPanel.getLayoutParams();
    FrameLayout.LayoutParams video;
    if (h > w) {
      sheetP.height = Math.min(h * 57 / 100, h - dp(100));
      mRefSheetPanel.setLayoutParams(sheetP);
      video = new FrameLayout.LayoutParams(-1, Math.max(dp(96), h - sheetP.height - dp(32)), Gravity.TOP);
    } else {
      video = new FrameLayout.LayoutParams(Math.max(dp(120), w - sheetP.width - dp(30)), -1, Gravity.LEFT);
    }
    mPlayerTexture.setLayoutParams(video);
    mPlayerTexture.post(() -> applyCobraAspectTransform());
  }

  private String cobraRefinedDiagnostics() {
    StringBuilder out = new StringBuilder(mFeatures.healthSnapshot());
    out.append("\n\nGuide sources (identifiers redacted):\n");
    int i = 0;
    for (LiveSource source : mSources) {
      String state = mGuideLoadState.get(source.id);
      out.append("Source ").append(++i).append(": ").append(state == null ? "Not loaded" : state).append('\n');
    }
    try {
      File file = new File(getFilesDir(), "cobra-multiview-health.json");
      if (file.isFile() && file.length() < 65536) out.append("\nLast Multi-View snapshot:\n").append(readText(new java.io.FileInputStream(file)));
    } catch (Exception ignored) { out.append("\nNo Multi-View snapshot available."); }
    return out.toString();
  }

  private long parseXmlTvTime(String raw) {
    if (raw == null || raw.trim().isEmpty()) return 0L;
    String value = raw.trim();
    java.util.regex.Matcher match = java.util.regex.Pattern.compile("^(\\d{12}|\\d{14})(?:\\s*([+-]\\d{4}|Z))?$").matcher(value);
    if (!match.matches()) return 0L;
    String digits = match.group(1), offset = match.group(2);
    if (offset == null || "Z".equals(offset)) offset = "+0000";
    try {
      SimpleDateFormat format = new SimpleDateFormat(digits.length() == 14 ? "yyyyMMddHHmmss Z" : "yyyyMMddHHmm Z", Locale.US);
      format.setLenient(false); format.setTimeZone(TimeZone.getTimeZone("UTC"));
      return format.parse(digits + " " + offset).getTime();
    } catch (Exception ignored) { return 0L; }
  }

  private String cobraEpgTitle(String value) {
    if (value == null) return "";
    try {
      byte[] decoded = android.util.Base64.decode(value, android.util.Base64.DEFAULT);
      String text = new String(decoded, StandardCharsets.UTF_8);
      String canonical = android.util.Base64.encodeToString(decoded, android.util.Base64.NO_WRAP).replace("=", "");
      if (!canonical.equals(value.replaceAll("\\s", "").replace("=", "")) || text.indexOf('\uFFFD') >= 0) return value;
      for (int i = 0; i < text.length(); i++) if (Character.isISOControl(text.charAt(i)) && !Character.isWhitespace(text.charAt(i))) return value;
      return text;
    } catch (IllegalArgumentException ignored) { return value; }
  }
