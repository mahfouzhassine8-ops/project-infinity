  /** Six-change controller. Existing routing/audio/lifecycle owners remain authoritative. */
  private final CobraSix mCobraSix = new CobraSix();
  private final class CobraSix {
    // Change 1: a synchronous, channel-bound override, never a global tuning policy.
    private Channel audioTarget;
    private Boolean audioMuted;
    // Change 2: only the new mini-player button owns this return receipt.
    private ExoPlayer miniPipPlayer;
    private String miniPipMode, miniPipProfile;
    private boolean miniPipEntered;
    private View themedHeader;
    private android.graphics.drawable.Drawable originalHeader;
    private int headerStamp=Integer.MIN_VALUE;
    private View statsOwner;
    private FrameLayout fullContextOverlay;
    private String fullContextKey="",fullContextProfile="";
    private boolean fullContextSports;

    void recordFullContext(boolean sports) {
      fullContextOverlay=mPlayerOverlay;fullContextSports=sports;
      fullContextKey=mPlaying==null?"":cobraChannelKey(mPlaying);
      fullContextProfile=mFeatures.activeProfileId();
    }
    void modeChanged() {
      fullContextOverlay=null;
      if(miniPipPlayer!=null && !java.util.Objects.equals(miniPipMode,mCobraGuideStyle))clearMiniPip();
      if(!sports() && statsOwner!=null && statsOwner==mCobraActionSheet)closeCobraActionSheet();
      if(mPlayerOverlay!=null && mPlayerChrome!=null && mPlayerChrome.findViewWithTag("cobra_fullscreen_controls")!=null)cobraBuildPlayerChrome();
      headerTheme();
    }
    void headerTheme() {
      if(!pro() || mCobraModeToolbar==null) {
        // The original non-Pro restyler owns that toolbar after a mode change.
        themedHeader=null;originalHeader=null;headerStamp=Integer.MIN_VALUE;return;
      }
      if(themedHeader!=mCobraModeToolbar) {
        themedHeader=mCobraModeToolbar;originalHeader=themedHeader.getBackground();headerStamp=Integer.MIN_VALUE;
      }
      int ink=cobraModeColor("text"),muted=cobraModeColor("muted");
      int stamp=java.util.Objects.hash(cobraEffectiveAppearanceMode(),cobraStaticAmbientMode(),mCobraAmbientTint,cobraNightCinemaActive(),ink,muted);
      if(headerStamp!=stamp){themedHeader.setBackground(cobraPhoneGlass(!cobraModeDark(),14,false));headerStamp=stamp;}
      if(mCobraModeTitle instanceof CobraProUi.Ink)((CobraProUi.Ink)mCobraModeTitle).ink(ink);
      if(mCobraModeSub instanceof CobraProUi.Ink)((CobraProUi.Ink)mCobraModeSub).ink(muted);
    }
    boolean phone() { return cobraTouchFirstDevice(); }
    boolean pro() { return phone() && mCobraProActive && "focus".equals(mCobraGuideStyle); }
    boolean sports() {
      if (!pro()) return false;
      if (mPlayerOverlay == null) return cobraProSportsHeroActive();
      if (fullContextOverlay != mPlayerOverlay) recordFullContext(cobraProSportsHeroActive());
      return fullContextSports && mPlaying!=null && fullContextKey.equals(cobraChannelKey(mPlaying))
          && fullContextProfile.equals(mFeatures.activeProfileId());
    }
    boolean channels() {
      return phone() && mPlayerOverlay != null && mCobraPlayerDrawer != null && mPlayer != null;
    }
    void tune(Channel target, Runnable action) {
      if (!phone() || mPlayer == null || target == null) { action.run(); return; }
      Channel previousTarget = audioTarget; Boolean previousMute = audioMuted;
      audioTarget = target; audioMuted = cobraMediaAudioState(mPlayer).userMuted;
      try {
        // A promoted preview is already constructed; seed its user intent before hand-off.
        if (mCobraPreviewPlayer != null && cobraChannelKey(target).equals(mCobraPreviewSessionKey)) {
          seed(mCobraPreviewPlayer, target, mPlayerTexture);
          mCobraPreviewMuted = audioMuted;
        }
        action.run();
        if(mPlayerOverlay!=null && mPlaying==target)recordFullContext(false);
      } finally { audioTarget = previousTarget; audioMuted = previousMute; }
    }
    void sportsTune(CobraSportsGame game,Channel channel) {
      CobraSportsGame current=game==null?null:cobraSportsGame(game.id);
      if(current==null || !current.live() || channel==null || !cobraChannelAllowed(channel)) {
        cobraPlaySportsBroadcast(game,channel);return;
      }
      tune(channel, () -> cobraPlaySportsBroadcast(game,channel));
      if(mPlayerOverlay!=null && mPlaying==channel) {
        recordFullContext(pro());cobraBuildPlayerChrome();
      }
    }
    void seed(ExoPlayer player, Channel channel, TextureView texture) {
      if (audioMuted == null || audioTarget != channel || texture != mPlayerTexture || player == null) return;
      CobraMediaAudioState state = cobraMediaAudioState(player);
      state.observe(CobraCallAudioPolicy.callMode(cobraAudioMode()));
      if (audioMuted) { state.mute(); player.setVolume(0f); }
      else state.unmute();
    }

    void fullPip() {
      if (!phone() || Build.VERSION.SDK_INT < 26) { toast("Picture-in-Picture is unavailable on this device"); return; }
      if (!cobraWantsFullscreenPip()) { toast("PiP is unavailable for the current playback state or channel setting"); return; }
      enterCobraPictureInPicture();
    }
    void miniPip() {
      if (!phone() || Build.VERSION.SDK_INT < 26 || mPlayerOverlay != null || mMultiOverlay != null
          || mCobraPreviewPlayer == null || mGuidePreviewChannel == null) return;
      ExoPlayer session = mCobraPreviewPlayer;
      if (!cobraPlaybackRequested(session) || !cobraChannelPipEnabled(mGuidePreviewChannel)) {
        toast("PiP is unavailable for the current playback state or channel setting"); return;
      }
      miniPipPlayer = session; miniPipMode = mCobraGuideStyle;
      miniPipProfile = mFeatures.activeProfileId(); miniPipEntered = false;
      promoteCobraPreviewToFullscreen(mGuidePreviewChannel);
      if (mPlayer != session || mPlayerOverlay == null) { clearMiniPip(); return; }
      enterCobraPictureInPicture();
    }
    void clearMiniPip() { miniPipPlayer = null; miniPipMode = null; miniPipProfile = null; miniPipEntered = false; }
    void pipChanged(boolean entered) {
      if (miniPipPlayer == null) return;
      if (entered) miniPipEntered = true;
      else mMain.post(() -> restoreMiniPip(false));
    }
    void restoreMiniPip(boolean failed) {
      if (miniPipPlayer == null || isCobraInPictureInPicture()) return;
      if (!failed && (!miniPipEntered || !mCobraPlaybackPolicy.resumed)) return;
      boolean current = mPlayer == miniPipPlayer && mPlayerOverlay != null && mMultiOverlay == null
          && java.util.Objects.equals(miniPipMode, mCobraGuideStyle)
          && java.util.Objects.equals(miniPipProfile, mFeatures.activeProfileId());
      clearMiniPip();
      if (current) closeFullscreenToCobraView();
    }
    void previewButton(LinearLayout bar, FrameLayout host) {
      if (!phone()) return;
      CobraIconButton pip = cobraIcon("pip", "Picture-in-Picture", true, v -> miniPip());
      pip.setTag("cobra_preview_pip");
      // Append; the six existing callback positions and their order are unchanged.
      bar.addView(pip, new LinearLayout.LayoutParams(0, dp(48), 1));
      CobraIconButton small = cobraIcon("pip", "Picture-in-Picture", true, v -> miniPip());
      small.setTag("cobra_preview_pip_small");small.setVisibility(View.GONE);
      host.addView(small,new FrameLayout.LayoutParams(dp(48),dp(48),Gravity.BOTTOM|Gravity.LEFT));
      host.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->smallPreviewPip());
      View label=host.findViewWithTag("cobra_preview_label");if(label!=null)label.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->smallPreviewPip());
    }
    void smallPreviewPip() {
      if(mCobraPreviewHost==null)return;
      View small=mCobraPreviewHost.findViewWithTag("cobra_preview_pip_small");
      View bar=mCobraPreviewHost.findViewWithTag("cobra_preview_controls");
      if(small==null || bar==null)return;
      if(!phone() || pro() || bar.getVisibility()==View.VISIBLE){small.setVisibility(View.GONE);return;}
      int w=mCobraPreviewHost.getWidth(),h=mCobraPreviewHost.getHeight(),gap=dp(2);
      View status=mCobraPreviewHost.findViewWithTag("cobra_preview_label");
      android.graphics.Rect blocked=new android.graphics.Rect();
      if(status!=null && status.getAlpha()>0f && status.getVisibility()==View.VISIBLE){
        blocked.set(0,0,status.getWidth(),status.getHeight());mCobraPreviewHost.offsetDescendantRectToMyCoords(status,blocked);
      }
      for(int size:new int[]{48,40,32}){
        int side=dp(size);
        for(int y:new int[]{h-side-gap,gap,blocked.bottom+gap})for(int x:new int[]{gap,w-side-gap,(w-side)/2}){
          android.graphics.Rect box=new android.graphics.Rect(x,y,x+side,y+side);
          if(x<gap || y<gap || box.right>w-gap || box.bottom>h-gap || android.graphics.Rect.intersects(box,blocked))continue;
          FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(side,side,Gravity.TOP|Gravity.LEFT);lp.leftMargin=x;lp.topMargin=y;
          small.setLayoutParams(lp);small.setVisibility(View.VISIBLE);return;
        }
      }
      // Fail the geometry gate rather than conceal an approved label or control.
      small.setVisibility(View.GONE);
    }

    // Changes 3/4: decorate only the newly built fullscreen controls for the current mode.
    View controls(LinearLayout tools, int availableWidth) {
      if (!phone()) return tools;
      tools.setTag("cobra_fullscreen_controls");
      CobraIconButton pip = cobraIcon("pip", "PiP", true, v -> fullPip());
      pip.caption("PiP"); pip.setTag("cobra_fullscreen_pip");
      tools.addView(pip, 3, new LinearLayout.LayoutParams(0, dp(52), 1));
      if (!pro()) return tools;
      if (sports()) {
        CobraIconButton stats = cobraIcon("stats", "Stats", true, v -> {
          if (!sports()) return;
          CobraSportsGame game = currentGame(); if (game != null) showCobraSportsStats(game);
        });
        stats.caption("Stats"); stats.setTag("cobra_fullscreen_sports_stats");
        tools.addView(stats, 4, new LinearLayout.LayoutParams(0, dp(52), 1));
      }
      android.widget.HorizontalScrollView scroll = new android.widget.HorizontalScrollView(InfinityLiveActivity.this);
      scroll.setTag("cobra_pro_fullscreen_scroll"); scroll.setHorizontalScrollBarEnabled(false);
      scroll.setFillViewport(false); scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
      int cell = Math.max(dp(72), availableWidth / 4);
      for (int i = 0; i < tools.getChildCount(); i++) tools.getChildAt(i).setLayoutParams(new LinearLayout.LayoutParams(cell, dp(52)));
      scroll.addView(tools, new FrameLayout.LayoutParams(-2, -1));
      return scroll;
    }
    CobraSportsGame currentGame() {
      if (!sports()) return null;
      if (mPlayerOverlay != null && mPlaying != null
          && mCobraProSportsPlaybackChannelKey.equals(cobraChannelKey(mPlaying))) {
        CobraSportsGame game = cobraSportsGame(mCobraProSportsPlaybackGameId);
        if (game != null) return game;
      }
      return cobraProCurrentSportsGame();
    }
    boolean drawStats(CobraIconButton button, android.graphics.Canvas canvas, float cx, float cy) {
      if (!"cobra_fullscreen_sports_stats".equals(button.getTag())) return false;
      // Exactly the mini-player renderer, not the shared health/theme glyph.
      CobraProUi.icon(canvas, button.paint, "stats", cx-dp(12), cy-dp(12), dp(24), button.ink);
      button.paint.reset(); button.paint.setAntiAlias(true); button.paint.setColor(button.ink);
      button.paint.setTextSize(dp(10)); button.paint.setTextAlign(android.graphics.Paint.Align.CENTER);
      canvas.drawText(button.caption, cx, button.getHeight()-dp(5), button.paint); return true;
    }

    // Change 5: capture the initiating fullscreen drawer, not a later/stale mode preference.
    boolean watchFromChannels(CobraSportsGame game) {
      if (!channels() || !"SPORTS".equals(mCobraDrawerFilter)) return false;
      final ExoPlayer origin = mPlayer;
      final FrameLayout overlay = mPlayerOverlay;
      final View drawer = mCobraPlayerDrawer;
      final String profile = mFeatures.activeProfileId();
      final boolean proChooser = pro();
      cobraSportsResolveAsync(game, matches -> {
        if (mPlayer != origin || mPlayerOverlay != overlay || mCobraPlayerDrawer != drawer
            || !profile.equals(mFeatures.activeProfileId()) || !"SPORTS".equals(mCobraDrawerFilter)
            || proChooser != pro()) return;
        if (matches.isEmpty()) { toast("No matching channel found in your current providers"); return; }
        if (cobraSportsUniqueStrong(matches)) {
          sportsTune(game,matches.get(0).channel); return;
        }
        if (proChooser) broadcastChooser(game, matches, origin, overlay, profile);
        else {
          // Preserve the existing non-Pro selection presentation, including its original limit.
          LinearLayout rows = cobraOpenSheet("Watch on", cobraSportsMatchup(game)+" • choose a broadcast", "sports-watch");
          for (int i=0;i<Math.min(8,matches.size());i++) {
            CobraSportsMatch match = matches.get(i);
            String confidence = match.score>=70?"Strong match":match.score>=55?"Good match":"Possible match";
            rows.addView(cobraSheetRow("play",match.channel.name,confidence+(match.evidence.isEmpty()?"":" • "+match.evidence),false,cobraSheetIsDark(),
                () -> sportsTune(game,match.channel)));
          }
        }
      });
      return true;
    }
    void broadcastChooser(CobraSportsGame game, ArrayList<CobraSportsMatch> matches,
                          ExoPlayer origin, FrameLayout overlay, String profile) {
      if (!pro() || mPlayerOverlay != overlay || mPlayer != origin) return;
      closeCobraPlayerDrawer();
      final android.widget.ListView list = new android.widget.ListView(InfinityLiveActivity.this);
      list.setTag("cobra_pro_broadcast_choices"); list.setDivider(null);
      list.setVerticalScrollBarEnabled(true); list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
      final View[] owner = new View[1];
      list.setAdapter(new android.widget.BaseAdapter() {
        public int getCount() { return matches.size(); }
        public Object getItem(int position) { return matches.get(position); }
        public long getItemId(int position) { return position; }
        public View getView(int position, View recycled, android.view.ViewGroup parent) {
          CobraSportsMatch match = matches.get(position);
          Button row = new Button(InfinityLiveActivity.this);
          row.setAllCaps(false); row.setSingleLine(true); row.setEllipsize(android.text.TextUtils.TruncateAt.END);
          row.setText(match.channel.name); row.setContentDescription(match.channel.name);
          row.setGravity(Gravity.START|Gravity.CENTER_VERTICAL); row.setTextSize(14);
          row.setTextColor(Color.WHITE); row.setPadding(dp(12),0,dp(12),0);
          row.setBackground(cobraPressSurface(true)); row.setMinHeight(0); row.setMinimumHeight(0);
          row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(48)));
          row.setTag("cobra_pro_broadcast_"+position);
          row.setOnClickListener(v -> {
            if (!pro() || mCobraActionSheet != owner[0] || mPlayerOverlay != overlay || mPlayer != origin
                || !profile.equals(mFeatures.activeProfileId())) return;
            sportsTune(game,match.channel);
          });
          return row;
        }
      });
      owner[0] = panel("Watch on", "sports-watch", list, matches.size());
    }

    // A new, bounded foreground panel. It uses the original Back/Close owner and no global layout hook.
    View panel(String title, String kind, View body, int choices) {
      closeCobraActionSheet();
      final FrameLayout parent = mPlayerOverlay != null ? mPlayerOverlay : (FrameLayout)getWindow().getDecorView();
      mCobraSheetPreviousFocus = getCurrentFocus(); mCobraSheetKind = kind;
      final LinearLayout box = new LinearLayout(InfinityLiveActivity.this);box.setOrientation(LinearLayout.VERTICAL);
      box.setClickable(true);box.setTag("cobra_sheet_panel");
      box.setBackground(cobraPanelSurface(0xee080b11,18,0xff344359));
      final LinearLayout header = new LinearLayout(InfinityLiveActivity.this);header.setGravity(Gravity.CENTER_VERTICAL);
      TextView heading = cobraText(title,Color.WHITE,18);heading.setSingleLine(true);heading.setEllipsize(android.text.TextUtils.TruncateAt.END);
      heading.setPadding(dp(12),0,0,0);header.addView(heading,new LinearLayout.LayoutParams(0,-1,1));
      CobraIconButton close = cobraIcon("close","Close menu",true,v -> closeCobraActionSheet());
      header.addView(close,new LinearLayout.LayoutParams(dp(48),-1));box.addView(header,new LinearLayout.LayoutParams(-1,dp(48)));
      box.addView(body,new LinearLayout.LayoutParams(-1,0,1));
      FrameLayout scrim = new FrameLayout(InfinityLiveActivity.this) {
        @Override protected void onMeasure(int ws,int hs) {
          int w=View.MeasureSpec.getSize(ws),h=View.MeasureSpec.getSize(hs);
          int[] safe = safeInsets(this,w,h);int aw=Math.max(1,w-safe[0]-safe[2]),ah=Math.max(1,h-safe[1]-safe[3]);
          int width=Math.min(aw,dp(440)),height;
          int headerHeight=dp(48);
          if(choices>0) {
            int visible=Math.min(choices,4);
            headerHeight=Math.min(headerHeight,Math.max(dp(32),ah-visible*dp(48)));
            height=Math.min(ah,headerHeight+Math.min(choices,8)*dp(48));
          } else height=Math.min(ah,dp(600));
          header.getLayoutParams().height=headerHeight;
          FrameLayout.LayoutParams lp=(FrameLayout.LayoutParams)box.getLayoutParams();
          lp.width=width;lp.height=height;lp.gravity=Gravity.TOP|Gravity.LEFT;
          lp.leftMargin=safe[0]+aw-width;lp.topMargin=safe[1]+Math.max(0,(ah-height)/2);
          box.setLayoutParams(lp);super.onMeasure(ws,hs);
        }
      };
      scrim.setTag(choices>0?"cobra_pro_broadcast_panel":"cobra_pro_stats_panel");
      scrim.setBackgroundColor(0x33000000);scrim.setClickable(true);scrim.setOnClickListener(v -> closeCobraActionSheet());
      scrim.addView(box,new FrameLayout.LayoutParams(-1,-1));
      mCobraActionSheet=scrim;mCobraSheetPanel=box;
      parent.addView(scrim,new FrameLayout.LayoutParams(-1,-1));scrim.bringToFront();close.requestFocus();
      return scrim;
    }
    int[] safeInsets(View view,int w,int h) {
      int[] out={0,0,0,0};
      if(Build.VERSION.SDK_INT<23 || view.getRootWindowInsets()==null)return out;
      android.view.WindowInsets in=view.getRootWindowInsets();int[] here=new int[2],root=new int[2];
      view.getLocationInWindow(here);view.getRootView().getLocationInWindow(root);
      int l=in.getSystemWindowInsetLeft(),t=in.getSystemWindowInsetTop(),r=in.getSystemWindowInsetRight(),b=in.getSystemWindowInsetBottom();
      if(Build.VERSION.SDK_INT>=28 && in.getDisplayCutout()!=null){android.view.DisplayCutout c=in.getDisplayCutout();l=Math.max(l,c.getSafeInsetLeft());t=Math.max(t,c.getSafeInsetTop());r=Math.max(r,c.getSafeInsetRight());b=Math.max(b,c.getSafeInsetBottom());}
      out[0]=Math.max(0,root[0]+l-here[0]);out[1]=Math.max(0,root[1]+t-here[1]);
      out[2]=Math.max(0,here[0]+w-(root[0]+view.getRootView().getWidth()-r));
      out[3]=Math.max(0,here[1]+h-(root[1]+view.getRootView().getHeight()-b));return out;
    }

    boolean stats(CobraSportsGame game) {
      if (!sports() || game == null || cobraSportsHidden(game)) return false;
      final LinearLayout rows;
      final View owner;
      if(mPlayerOverlay==null) {
        // Keep the approved mini-player dialog, including its theme and scroll/close behavior.
        rows=cobraOpenSheet("Stats • "+cobraSportsMatchup(game),"Loading game statistics…","sports-stats");owner=mCobraActionSheet;
      } else {
        rows=new LinearLayout(InfinityLiveActivity.this);rows.setOrientation(LinearLayout.VERTICAL);rows.setPadding(dp(12),dp(8),dp(12),dp(12));
        android.widget.ScrollView scroll=new android.widget.ScrollView(InfinityLiveActivity.this);scroll.setFillViewport(false);scroll.addView(rows,new FrameLayout.LayoutParams(-1,-2));
        owner=panel("Stats", "sports-stats",scroll,0);
      }
      statsOwner=owner;
      team(rows,game.away,"Away");team(rows,game.home,"Home");
      cobraInfoText(rows,"Venue • "+(game.venue.isEmpty()?"Unavailable":game.venue));
      cobraInfoText(rows,"Kickoff • "+(game.timeConfirmed?cobraSportsClock(game.startMs):"Time TBA"));
      cobraInfoText(rows,cobraSportsScoreLine(game));cobraInfoText(rows,cobraSportsMeta(game));
      final LinearLayout details=new LinearLayout(InfinityLiveActivity.this);details.setOrientation(LinearLayout.VERTICAL);rows.addView(details,new LinearLayout.LayoutParams(-1,-2));
      cobraInfoText(details,"Loading game statistics…");
      final String profile=mFeatures.activeProfileId();
      submitCobraIo(() -> {
        try {
          final CobraSportsSummary summary=mCobraSportsRepository.summary(game);
          publishCobraUi(() -> {
            if(mCobraActionSheet!=owner || !sports() || !profile.equals(mFeatures.activeProfileId()) || cobraSportsHidden(game))return;
            details.removeAllViews();
            for(String line:summary.lines)cobraInfoText(details,line);
          });
        } catch(Exception failure) {
          publishCobraUi(() -> {
            if(mCobraActionSheet!=owner || !sports() || !profile.equals(mFeatures.activeProfileId()) || cobraSportsHidden(game))return;
            details.removeAllViews();cobraInfoText(details,"Statistics are unavailable right now.");
          });
        }
      });return true;
    }
    void team(LinearLayout rows,CobraSportsTeam team,String side) {
      if(team==null){cobraInfoText(rows,side+" team • Unavailable");return;}
      LinearLayout row=new LinearLayout(InfinityLiveActivity.this);row.setGravity(Gravity.CENTER_VERTICAL);
      android.widget.ImageView logo=new android.widget.ImageView(InfinityLiveActivity.this);logo.setContentDescription(team.name+" logo");logo.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
      row.addView(logo,new LinearLayout.LayoutParams(dp(48),dp(48)));cobraSportsLoadLogo(team.logo,logo);
      TextView text=cobraText(side+" • "+team.name,cobraSheetIsDark()?Color.WHITE:cobraModeColor("text"),16);text.setMaxLines(2);text.setPadding(dp(10),0,0,0);
      row.addView(text,new LinearLayout.LayoutParams(0,-2,1));rows.addView(row,new LinearLayout.LayoutParams(-1,-2));
    }
  }
