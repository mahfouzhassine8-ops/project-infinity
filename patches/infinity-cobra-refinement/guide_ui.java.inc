// STATE
  private FrameLayout mRefGuideCanvas;
  private FrameLayout mRefPreviewHost;
  private TextureView mRefPreviewTexture;
  private LinearLayout mRefGuideBody;
  private LinearLayout mRefGuideInfo;
  private android.widget.BaseAdapter mRefGuideAdapter;
  private boolean mRefGuideCategories = false;
  private String mRefGuideSource = "";
  private String mRefGuideMode = "grid";
  private long mRefGuideWindow = 0L;
  private int mRefGuideWidth = -1;
  private int mRefGuideHeight = -1;
  private final Runnable mRefGuideTick = new Runnable() {
    public void run() {
      if (!isCobraAsyncAlive()) return;
      refreshCobraGuidePresentation();
      mMain.postDelayed(this, 30000L);
    }
  };

// METHODS
  private ArrayList<Channel> cobraRefGuideChannels() {
    ArrayList<Channel> result = new ArrayList<>();
    boolean recent = "RECENT".equals(mCategory);
    List<Channel> source = recent ? filteredChannels(false, true) : mChannels;
    for (Channel c : source) {
      String sid = sourceIdForChannel(c);
      if (isCobraHidden(c) || mFeatures.looksAdult(c.group) || mFeatures.looksAdult(c.name)) continue;
      if (!sid.isEmpty() && !mFeatures.sourceEnabled(sid)) continue;
      if (!mRefGuideSource.isEmpty() && !sid.equals(mRefGuideSource)) continue;
      if ("FAVORITES".equals(mCategory) && !mFavorites.contains(c.id)) continue;
      if (mCategory.startsWith("MY:") && !mCategory.substring(3).equals(cobraCustomGroup(c))) continue;
      if (!mCategory.startsWith("MY:") && !"ALL".equals(mCategory) && !"RECENT".equals(mCategory)
          && !"FAVORITES".equals(mCategory) && !mCategory.equals(c.group)) continue;
      if (!mSearch.trim().isEmpty() && !c.name.toLowerCase(Locale.ROOT).contains(mSearch.trim().toLowerCase(Locale.ROOT))) continue;
      result.add(c);
    }
    return result;
  }

  private void cobraRefGuideShell(String mode, boolean categories) {
    mRefGuideMode = mode; mRefGuideCategories = categories;
    mCobraInternalScreen = "root";
    ArrayList<Channel> all = new ArrayList<>();
    for (Channel c : mChannels) if (!isCobraHidden(c) && !mFeatures.looksAdult(c.group)
        && !mFeatures.looksAdult(c.name) && mFeatures.sourceEnabled(sourceIdForChannel(c))) all.add(c);
    ensureCobraPreviewSelection(all);
    if (mRefGuideCanvas == null || mRefGuideCanvas.getParent() != mStage) {
      clearStage("COBRA · LIVE TV");
      mRefGuideCanvas = new FrameLayout(this);
      mRefPreviewHost = cobraPreviewPanel(mGuidePreviewChannel, true);
      mRefPreviewTexture = mCobraPreviewTexture;
      mRefGuideInfo = new LinearLayout(this); mRefGuideInfo.setOrientation(LinearLayout.VERTICAL);
      TextView title = cobraRefinedText("", 16, true); title.setTag("ref_guide_title");
      TextView now = cobraRefinedText("", 13, false); now.setTag("ref_guide_now");
      TextView next = cobraRefinedText("", 12, false); next.setTag("ref_guide_next");
      for (TextView line : new TextView[]{title, now, next}) {
        line.setMaxLines(1); line.setEllipsize(android.text.TextUtils.TruncateAt.END);
        mRefGuideInfo.addView(line, new LinearLayout.LayoutParams(-1, dp(25)));
      }
      mRefGuideInfo.setPadding(dp(8), dp(5), dp(8), dp(5));
      mRefGuideInfo.setOnClickListener(v -> { if (mGuidePreviewChannel != null) showProgramGuide(mGuidePreviewChannel); });
      mRefGuideBody = new LinearLayout(this); mRefGuideBody.setOrientation(LinearLayout.VERTICAL);
      mRefGuideCanvas.addView(mRefPreviewHost);
      mRefGuideCanvas.addView(mRefGuideInfo);
      mRefGuideCanvas.addView(mRefGuideBody);
      mStage.addView(mRefGuideCanvas, new LinearLayout.LayoutParams(-1, 0, 1));
      mRefGuideWidth = -1; mRefGuideHeight = -1;
      mRefGuideCanvas.addOnLayoutChangeListener((v, l, t, r, b, ol, ot, or, ob) -> {
        if (r-l != mRefGuideWidth || b-t != mRefGuideHeight) {
          mRefGuideWidth = r-l; mRefGuideHeight = b-t;
          layoutCobraRefGuide();
          renderCobraRefGuideBody();
        }
      });
    }
    // Reuse the same preview View AND TextureView, including after fullscreen hand-back.
    mCobraPreviewHost = mRefPreviewHost; mCobraPreviewTexture = mRefPreviewTexture;
    if (mCobraTransferPlayer != null && mGuidePreviewChannel != null
        && cobraChannelKey(mGuidePreviewChannel).equals(mCobraTransferKey)) {
      ExoPlayer player = mCobraTransferPlayer;
      mCobraTransferPlayer = null; mCobraTransferKey = "";
      mCobraPreviewPlayer = player; mCobraPreviewSessionKey = cobraChannelKey(mGuidePreviewChannel);
      player.setVideoTextureView(mRefPreviewTexture); player.setVolume(mCobraPreviewMuted ? 0f : 1f);
      updateCobraPreviewPlayPause();
    }
    mHeader.setText("☰  COBRA · " + ("grid".equals(mode) ? "LIVE TV" : mode.toUpperCase(Locale.ROOT)));
    mHeader.setTypeface(Typeface.SANS_SERIF, Typeface.BOLD); mHeader.setTextSize(18);
    mHeader.getLayoutParams().height = dp(48); mHeader.requestLayout();
    mStatus.getLayoutParams().height = dp(28); mStatus.requestLayout();
    mStatus.setTypeface(Typeface.SANS_SERIF); mStatus.setTextSize(11);
    if (mRefGuideWindow == 0) mRefGuideWindow = System.currentTimeMillis() / 1800000L * 1800000L;
    layoutCobraRefGuide(); renderCobraRefGuideBody(); refreshCobraGuidePresentation();
    requestCobraShortGuide(mGuidePreviewChannel);
    mMain.removeCallbacks(mRefGuideTick); mMain.postDelayed(mRefGuideTick, 30000L);
  }

  private void layoutCobraRefGuide() {
    if (mRefGuideCanvas == null || mRefGuideCanvas.getWidth() <= 0 || mRefGuideCanvas.getHeight() <= 0) return;
    int w = mRefGuideCanvas.getWidth(), h = mRefGuideCanvas.getHeight();
    boolean side = w > h * 1.35f && w >= dp(600);
    int gap = dp(8), info = dp(84);
    if (side) {
      int pw = Math.max(dp(220), Math.min(w * 2 / 5, w - dp(320)));
      int ph = Math.min(h - info, Math.round(pw * 9f / 16f));
      mRefPreviewHost.setLayoutParams(new FrameLayout.LayoutParams(pw, Math.max(dp(96), ph), Gravity.TOP | Gravity.LEFT));
      FrameLayout.LayoutParams ip = new FrameLayout.LayoutParams(pw, info); ip.topMargin = Math.max(dp(96), ph);
      mRefGuideInfo.setLayoutParams(ip);
      FrameLayout.LayoutParams bp = new FrameLayout.LayoutParams(w - pw - gap, -1); bp.leftMargin = pw + gap;
      mRefGuideBody.setLayoutParams(bp);
    } else {
      int ideal = "compact".equals(mRefGuideMode) ? dp(128) : Math.round(w * 9f / 16f);
      int ph = Math.min(ideal, Math.max(dp(96), h - info - dp(160)));
      if ("focus".equals(mRefGuideMode)) ph = Math.min(Math.round(h * .43f), Math.max(dp(120), h - info - dp(160)));
      mRefPreviewHost.setLayoutParams(new FrameLayout.LayoutParams(-1, ph));
      FrameLayout.LayoutParams ip = new FrameLayout.LayoutParams(-1, info); ip.topMargin = ph;
      mRefGuideInfo.setLayoutParams(ip);
      FrameLayout.LayoutParams bp = new FrameLayout.LayoutParams(-1, Math.max(dp(96), h - ph - info - gap)); bp.topMargin = ph + info + gap;
      mRefGuideBody.setLayoutParams(bp);
    }
  }

  private void showCobraTvHub() { cobraRefGuideShell("mobile".equals(cobraPrimaryView()) ? "mobile" : cobraGuideViewMode(), true); }
  private void showGuideGrid() { cobraRefGuideShell("grid", false); }
  private void showGuideCompact() { cobraRefGuideShell("compact", false); }
  private void showGuideCards() { cobraRefGuideShell("cards", false); }
  private void showGuideFocus() { cobraRefGuideShell("focus", false); }
  private void showCobraMobileView() { cobraRefGuideShell("mobile", false); }

  private void selectCobraCategory(String value) {
    mCategory = value; mRefGuideCategories = false;
    mCobraInternalScreen = "root";
    if (mRefGuideCanvas != null && mRefGuideCanvas.getParent() == mStage) renderCobraRefGuideBody();
    else showCobraPrimaryView();
  }

  private boolean cobraRefGuideBack() {
    if (mRefGuideCanvas == null || mRefGuideCanvas.getParent() != mStage) return false;
    if (!mRefGuideCategories) { mRefGuideCategories = true; renderCobraRefGuideBody(); return true; }
    if (!mRefGuideSource.isEmpty()) { mRefGuideSource = ""; renderCobraRefGuideBody(); return true; }
    return false;
  }

  private void renderCobraRefGuideBody() {
    if (mRefGuideBody == null || mRefGuideCanvas == null || mRefGuideCanvas.getParent() != mStage) return;
    mRefGuideBody.removeAllViews(); mRefGuideAdapter = null;
    LinearLayout top = new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL);
    Button up = cobraRefinedButton(mRefGuideCategories ? "Live TV" : "‹ Categories");
    up.setOnClickListener(v -> { if (mRefGuideCategories) mRefGuideSource = ""; mRefGuideCategories = true; renderCobraRefGuideBody(); });
    top.addView(up, new LinearLayout.LayoutParams(0, dp(48), 1));
    TextView group = cobraRefinedText(mRefGuideCategories ? (mRefGuideSource.isEmpty() ? "Browse" : "Categories") : mCategory, 12, true);
    group.setMaxLines(1); group.setEllipsize(android.text.TextUtils.TruncateAt.END);
    top.addView(group, new LinearLayout.LayoutParams(0, dp(48), 1));
    Button search = cobraRefinedButton("Search");
    search.setOnClickListener(v -> {
      EditText field = new EditText(this); field.setSingleLine(true); field.setText(mSearch); field.setHint("Find a channel");
      new AlertDialog.Builder(this).setTitle("Search Live TV").setView(field).setPositiveButton("Search", (d, x) -> {
        mSearch = field.getText().toString(); mCategory = "ALL"; mRefGuideCategories = false; renderCobraRefGuideBody();
      }).setNegativeButton("Clear", (d, x) -> { mSearch = ""; renderCobraRefGuideBody(); }).show();
    });
    top.addView(search, new LinearLayout.LayoutParams(dp(74), dp(48)));
    mRefGuideBody.addView(top, new LinearLayout.LayoutParams(-1, dp(48)));
    if (mRefGuideCategories) { renderCobraRefCategories(); return; }
    final ArrayList<Channel> channels = cobraRefGuideChannels();
    final boolean timeline = "grid".equals(mRefGuideMode) && !isPortrait() && cobraWidthDp() >= 600;
    if (timeline) {
      LinearLayout times = new LinearLayout(this); times.setGravity(Gravity.CENTER_VERTICAL);
      Button before = cobraRefinedButton("‹"); before.setContentDescription("Earlier programmes");
      Button now = cobraRefinedButton("Now"); Button after = cobraRefinedButton("›"); after.setContentDescription("Later programmes");
      before.setOnClickListener(v -> { mRefGuideWindow = Math.max(System.currentTimeMillis() - 7L * 86400000L, mRefGuideWindow - 5400000L); renderCobraRefGuideBody(); });
      after.setOnClickListener(v -> { mRefGuideWindow = Math.min(System.currentTimeMillis() + 7L * 86400000L, mRefGuideWindow + 5400000L); renderCobraRefGuideBody(); });
      now.setOnClickListener(v -> { mRefGuideWindow = System.currentTimeMillis() / 1800000L * 1800000L; renderCobraRefGuideBody(); });
      times.addView(before, new LinearLayout.LayoutParams(dp(48), dp(48)));
      times.addView(now, new LinearLayout.LayoutParams(dp(52), dp(48)));
      TextView label = cobraRefinedText(new SimpleDateFormat("EEE h:mm a", Locale.US).format(new Date(mRefGuideWindow)) + " – "
          + new SimpleDateFormat("h:mm a", Locale.US).format(new Date(mRefGuideWindow + 5400000L)), 11, false);
      times.addView(label, new LinearLayout.LayoutParams(0, dp(48), 1)); times.addView(after, new LinearLayout.LayoutParams(dp(48), dp(48)));
      mRefGuideBody.addView(times, new LinearLayout.LayoutParams(-1, dp(48)));
    }
    android.widget.BaseAdapter adapter = new android.widget.BaseAdapter() {
      public int getCount() { return channels.size(); }
      public Object getItem(int i) { return channels.get(i); }
      public long getItemId(int i) { return channels.get(i).id.hashCode(); }
      public View getView(int i, View old, android.view.ViewGroup parent) {
        Channel channel = channels.get(i);
        if (timeline) return cobraRefTimelineRow(channel, parent.getWidth());
        TextView row = old instanceof TextView ? (TextView) old : cobraRefinedText("", 14, false);
        ProgramPair pair = programFor(channel);
        boolean active = mGuidePreviewChannel != null && channel.id.equals(mGuidePreviewChannel.id);
        String current = pair == null || pair.now.isEmpty() ? cobraGuideStatus(channel) : pair.now;
        String label = (active ? "▶  " : "") + channel.name;
        if ("compact".equals(mRefGuideMode)) label += "\n" + current;
        else label += "\nNow  ·  " + current + (pair != null && !pair.next.isEmpty() ? "\nNext  ·  " + pair.next : "");
        row.setText(label); row.setTextSize("compact".equals(mRefGuideMode) ? 12 : 14);
        row.setMaxLines("compact".equals(mRefGuideMode) ? 2 : 3); row.setEllipsize(android.text.TextUtils.TruncateAt.END);
        row.setPadding(dp(12), dp(6), dp(12), dp(6)); row.setGravity(Gravity.CENTER_VERTICAL);
        row.setBackground(focusSurface(cobraThemeColor(active ? "focus" : "panel", active ? mTheme.focus : mTheme.panel), cobraThemeColor("focus", mTheme.focus), 10));
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp("compact".equals(mRefGuideMode) ? 56 : 88)));
        row.setFocusable(!cobraTouchFirstDevice()); row.setOnClickListener(v -> selectGuidePreview(channel));
        row.setOnLongClickListener(v -> { showCobraChannelActions(channel); return true; }); return row;
      }
    };
    mRefGuideAdapter = adapter;
    if ("cards".equals(mRefGuideMode) || "focus".equals(mRefGuideMode)) {
      android.widget.GridView grid = new android.widget.GridView(this);
      int available = mRefGuideBody.getWidth() > 0 ? Math.round(mRefGuideBody.getWidth() / getResources().getDisplayMetrics().density) : cobraWidthDp();
      grid.setNumColumns(Math.max(1, Math.min(4, available / 180))); grid.setHorizontalSpacing(dp(6)); grid.setVerticalSpacing(dp(6));
      grid.setAdapter(adapter); mRefGuideBody.addView(grid, new LinearLayout.LayoutParams(-1, 0, 1));
    } else {
      android.widget.ListView list = new android.widget.ListView(this); list.setDivider(null); list.setDividerHeight(dp(3));
      list.setSelector(android.R.color.transparent); list.setFastScrollEnabled(channels.size() > 100); list.setAdapter(adapter);
      mRefGuideBody.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
    }
    if (channels.isEmpty()) cobraSheetNote(mRefGuideBody, "No channels match. Choose another category or clear Search.");
  }

  private void renderCobraRefCategories() {
    ArrayList<String> labels = new ArrayList<>(), values = new ArrayList<>();
    Collections.addAll(labels, "Favorites", "Recently Played", "All Channels");
    Collections.addAll(values, "FAVORITES", "RECENT", "ALL");
    if (mRefGuideSource.isEmpty() && mSources.size() > 1) for (LiveSource source : mSources) if (mFeatures.sourceEnabled(source.id)) {
      labels.add(source.name + "  ›"); values.add("SOURCE:" + source.id);
    }
    Set<String> groups = new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
    for (Channel c : mChannels) if (!isCobraHidden(c) && !mFeatures.looksAdult(c.group) && !mFeatures.looksAdult(c.name)
        && mFeatures.sourceEnabled(sourceIdForChannel(c)) && (mRefGuideSource.isEmpty() || mRefGuideSource.equals(sourceIdForChannel(c)))) groups.add(c.group);
    for (String group : groups) { labels.add(group + "  ›"); values.add(group); }
    for (String group : cobraCustomGroups()) { labels.add("My group · " + group); values.add("MY:" + group); }
    android.widget.ListView list = new android.widget.ListView(this); list.setDivider(null);
    list.setAdapter(new android.widget.BaseAdapter() {
      public int getCount() { return labels.size(); }
      public Object getItem(int i) { return values.get(i); }
      public long getItemId(int i) { return i; }
      public View getView(int i, View old, android.view.ViewGroup parent) {
        TextView row = old instanceof TextView ? (TextView) old : cobraRefinedText("", 14, false);
        row.setText(labels.get(i)); row.setPadding(dp(14), 0, dp(14), 0); row.setGravity(Gravity.CENTER_VERTICAL);
        row.setBackground(focusSurface(cobraThemeColor("panel", mTheme.panel), cobraThemeColor("focus", mTheme.focus), 10));
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(52)));
        String value = values.get(i); row.setOnClickListener(v -> {
          if (value.startsWith("SOURCE:")) { mRefGuideSource = value.substring(7); renderCobraRefGuideBody(); }
          else { mSearch = ""; selectCobraCategory(value); }
        }); return row;
      }
    });
    mRefGuideBody.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private View cobraRefTimelineRow(Channel channel, int available) {
    LinearLayout row = new LinearLayout(this);
    row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(66)));
    int cw = dp(112), width = Math.max(dp(80), available - cw);
    TextView name = cobraRefinedText(channel.name, 12, true); name.setMaxLines(2); name.setPadding(dp(8), dp(4), dp(8), dp(4));
    name.setBackgroundColor(cobraThemeColor("panel", mTheme.panel)); name.setOnClickListener(v -> selectGuidePreview(channel));
    name.setOnLongClickListener(v -> { showCobraChannelActions(channel); return true; });
    row.addView(name, new LinearLayout.LayoutParams(cw, -1));
    FrameLayout band = new FrameLayout(this); band.setClipChildren(true);
    band.setBackgroundColor(cobraThemeColor("panel2", mTheme.panel2));
    row.addView(band, new LinearLayout.LayoutParams(0, -1, 1));
    long end = mRefGuideWindow + 5400000L, clock = System.currentTimeMillis(); boolean found = false;
    for (GuideProgram p : cobraGuidePrograms(channel)) {
      if (p.stop <= mRefGuideWindow || p.start >= end) continue;
      found = true;
      int left = Math.round((Math.max(p.start, mRefGuideWindow) - mRefGuideWindow) * width / 5400000f);
      int right = Math.round((Math.min(p.stop, end) - mRefGuideWindow) * width / 5400000f);
      TextView block = cobraRefinedText(p.title, 12, false); block.setMaxLines(2); block.setEllipsize(android.text.TextUtils.TruncateAt.END);
      block.setGravity(Gravity.CENTER_VERTICAL); block.setPadding(dp(8), dp(5), dp(8), dp(5));
      boolean current = p.start <= clock && clock < p.stop;
      block.setBackground(focusSurface(cobraThemeColor(current ? "focus" : "panel", current ? mTheme.focus : mTheme.panel), cobraThemeColor("focus", mTheme.focus), 6));
      block.setOnClickListener(v -> { if (p.start <= System.currentTimeMillis() && System.currentTimeMillis() < p.stop) selectGuidePreview(channel); else showProgramActions(channel, p); });
      block.setOnLongClickListener(v -> { showProgramActions(channel, p); return true; });
      FrameLayout.LayoutParams bp = new FrameLayout.LayoutParams(Math.max(1, right-left-dp(2)), -1); bp.leftMargin = left;
      band.addView(block, bp);
    }
    if (!found) {
      TextView empty = cobraRefinedText(cobraGuideStatus(channel), 12, false); empty.setOnClickListener(v -> selectGuidePreview(channel));
      band.addView(empty, new FrameLayout.LayoutParams(-1, -1));
    }
    if (clock >= mRefGuideWindow && clock < end) {
      View marker = new View(this); marker.setBackgroundColor(cobraThemeColor("accent", mTheme.accent));
      FrameLayout.LayoutParams mp = new FrameLayout.LayoutParams(dp(2), -1); mp.leftMargin = Math.round((clock-mRefGuideWindow) * width / 5400000f);
      marker.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO); band.addView(marker, mp);
    }
    return row;
  }

  private void refreshCobraGuidePresentation() {
    if (!isCobraAsyncAlive()) return;
    if (mRefGuideAdapter != null) mRefGuideAdapter.notifyDataSetChanged();
    Channel channel = mGuidePreviewChannel;
    ProgramPair pair = channel == null ? null : programFor(channel);
    if (mRefGuideInfo != null) {
      ((TextView) mRefGuideInfo.findViewWithTag("ref_guide_title")).setText(channel == null ? "Choose a channel" : channel.name);
      ((TextView) mRefGuideInfo.findViewWithTag("ref_guide_now")).setText("Now  ·  " + (pair == null || pair.now.isEmpty() ? cobraGuideStatus(channel) : pair.now));
      ((TextView) mRefGuideInfo.findViewWithTag("ref_guide_next")).setText(pair == null || pair.next.isEmpty() ? "Tap for schedule and guide status" : "Next  ·  " + pair.next);
    }
    if (mPlayerOverlay != null && mPlaying != null) {
      View now = mPlayerOverlay.findViewWithTag("ref_player_now"), next = mPlayerOverlay.findViewWithTag("ref_player_next");
      if (now instanceof TextView) ((TextView) now).setText(cobraPlayerNow(mPlaying));
      if (next instanceof TextView) ((TextView) next).setText(cobraPlayerNext(mPlaying));
    }
  }
