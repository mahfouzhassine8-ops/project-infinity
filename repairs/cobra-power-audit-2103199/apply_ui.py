"""Surgical repairs to existing Cobra presentation and active subtitle controls.

Pure source transform. The orchestration owns the protected receipt, rollback,
combined source write, packaging and signer; this module never writes the input.
"""


def replace_once(text: str, before: str, after: str) -> str:
    count = text.count(before)
    if count != 1:
        raise ValueError(f"UI repair anchor expected once, found {count}: {before[:100]!r}")
    return text.replace(before, after, 1)


def transform(text: str) -> str:
    # A paired remote/keyboard can drive the existing buttons on a Fold or
    # phone too. Retain the existing contract flag and touch-mode exclusion.
    text = replace_once(text,
        '''    boolean dpad = getPackageManager().hasSystemFeature("android.software.leanback");
    button.setFocusable(dpad && (mUi == null || mUi.dpadFocusEnabled));''',
        '''    button.setFocusable(mUi == null || mUi.dpadFocusEnabled);''')
    # The sheet already forces dark text/icons over video. Only its raised detail
    # rows were incorrectly taking their fill from the LIGHT browsing palette.
    anchor = '  private LinearLayout cobraDetailRow(String icon,String title,String detail,String tag,boolean selected,Runnable action){'
    helper = '''  private android.graphics.drawable.Drawable cobraSheetDetailSurface(int radius){
    if(!cobraSheetIsDark()||cobraModeDark())return cobraModeSurface(radius,true);
    int accent=cobraModeColor("accent");
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_focused},surface(vtheme().color("cobra.cobraModeSurface.colors.1",0xff263d51),radius,accent,2));
    states.addState(new int[]{android.R.attr.state_selected},surface(vtheme().color("cobra.cobraModeSurface.colors.3",0xff1d3549),radius,cobraAlpha(accent,135),1));
    states.addState(new int[]{},surface(vtheme().color("cobra.cobraModeColorBuiltin.colors.11",0xff1a2430),radius,vtheme().color("cobra.cobraModeSurface.colors.6",Color.TRANSPARENT),0));
    return new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(vtheme().color("cobra.cobraModeSurface.colors.7",0x24ffffff)),states,surface(vtheme().color("cobra.cobraModeSurface.colors.9",Color.WHITE),radius,vtheme().color("cobra.cobraModeSurface.colors.10",Color.TRANSPARENT),0));
  }

'''
    text = replace_once(text, anchor, helper + anchor)
    text = replace_once(
        text,
        'row.setMinimumHeight(dp(vtheme().dimension("cobra.cobraDetailRow.dimensions.5",58)));row.setBackground(cobraModeSurface(14,true));',
        'row.setMinimumHeight(dp(vtheme().dimension("cobra.cobraDetailRow.dimensions.5",58)));row.setBackground(cobraSheetDetailSurface(14));',
    )

    # Focus takes ownership from an in-flight list-entry animation. Restore every
    # entry-only property and remove its sticky per-view stagger before animating.
    text = replace_once(
        text,
        '''      v.animate().cancel();
      v.animate().scaleX(focused?1.018f:1f).scaleY(focused?1.018f:1f)''',
        '''      v.animate().cancel();v.setTranslationX(0f);v.setTranslationY(0f);
      v.animate().setStartDelay(0L).scaleX(focused?1.018f:1f).scaleY(focused?1.018f:1f)''',
    )
    text = replace_once(
        text,
        '      View child=group.getChildAt(i);if(child==null)continue;\n      child.animate().cancel();child.setAlpha(0f);',
        '      View child=group.getChildAt(i);if(child==null||child.hasFocus())continue;\n      child.animate().cancel();child.setAlpha(0f);',
    )

    # Keep the existing profile list and actions, but permit short viewports and
    # large profile sets to reach the final row through touch or D-pad scrolling.
    before = '''    mStage.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void createProfileDialog()'''
    after = '''    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(list);
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void createProfileDialog()'''
    text = replace_once(text, before, after)

    # Saved channel defaults still initialize each session. An explicit existing
    # track/CC action overrides only the active Media3 session; cue visibility
    # must follow that session's actual text-track state, not its old default.
    text = replace_once(
        text,
        'captions.cues("off".equals(vitals.preferences.subtitles)?Collections.emptyList():group.cues);',
        'captions.cues(player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_TEXT)?Collections.emptyList():group.cues);',
    )

    # Restrict the escape repair to seven human-visible text statements. Do not
    # touch regexes, JSON escaping, playlist lines or HTTP protocol framing.
    display_anchors = (
        'labels[i] = channel.name +',
        '(pair != null && !pair.next.isEmpty() ? "\\\\nNEXT',
        'Button row = action(vtheme().copy("cobra.showRecordings.copy.1",',
        'Button row = action(vtheme().copy("cobra.showRecordings.copy.3",',
        'Button row = action(item.title +',
        'Button row = action(vtheme().copy("cobra.showContinueWatching.copy.1",',
        'clearStage("COBRA • AMBIENT");',
    )
    lines = text.splitlines(keepends=True)
    for anchor in display_anchors:
        found = [i for i, line in enumerate(lines) if anchor in line]
        if len(found) != 1:
            raise ValueError(f"Display escape anchor expected once, found {len(found)}: {anchor!r}")
        i = found[0]
        if "\\\\n" not in lines[i]:
            raise ValueError(f"Display escape already changed or missing: {anchor!r}")
        lines[i] = lines[i].replace("\\\\n", "\\n")
    text = "".join(lines)

    # Source A's delayed success/failure must never paint source B's Settings.
    # Cache storage remains keyed to the source whose request was performed.
    text = replace_once(
        text,
        '''    if (source == null || !"xtream".equals(source.type)) return;
    submitCobraIo(() -> {''',
        '''    if (source == null || !"xtream".equals(source.type)) return;
    final long subscriptionTicket=mCobraNavigation.current();
    submitCobraIo(() -> {''',
    )
    before = '''        publishCobraUi(() -> {
          View view = mStage == null ? null : mStage.findViewWithTag("cobra_subscription_status");
          if (view instanceof TextView) ((TextView) view).setText(label);
        });'''
    after = '''        publishCobraUi(() -> {
          if(mActiveSource==null||!source.id.equals(mActiveSource.id)||!mCobraNavigation.accepts(subscriptionTicket))return;
          View view = mStage == null ? null : mStage.findViewWithTag("cobra_subscription_status");
          if (view instanceof TextView) ((TextView) view).setText(label);
        });'''
    if text.count(before) != 2:
        raise ValueError("Subscription success/failure publication anchors changed")
    text = text.replace(before, after)

    # A geometry-only configuration change can remeasure the existing internal
    # content. Keep its list/scroll and pending navigation ticket intact instead
    # of replacing it with Live TV. Palette-changing configuration still follows
    # the existing rebuild path; do not invent a route-restoration architecture.
    text = replace_once(text, '  private String mCobraInternalScreen = "root";',
        '  private String mCobraInternalScreen = "root";\n  private String mCobraShellAppearance = "";')
    text = replace_once(text, '''  private void buildShell() {
    mCobraNavigation.advance();''', '''  private void buildShell() {
    mCobraShellAppearance=cobraEffectiveAppearanceMode();
    mCobraNavigation.advance();''')
    text = replace_once(text,
        '''    if("COBRA • SETTINGS".equals(mCobraStageTitle)){buildShell();showSettings();return;}''',
        '''    if("internal".equals(mCobraInternalScreen)&&mRoot!=null&&mStage!=null
        &&mCobraShellAppearance.equals(cobraEffectiveAppearanceMode())){
      closeCobraExperienceDrawer();closeCobraPowerMenu();
      if(mRail!=null&&mRail.getLayoutParams() instanceof LinearLayout.LayoutParams){
        LinearLayout.LayoutParams rail=(LinearLayout.LayoutParams)mRail.getLayoutParams();
        rail.width="drawer".equals(mUi.navigationMode)
            ?dp(isPortrait()?mUi.drawerPortraitWidthDp:mUi.drawerLandscapeWidthDp)
            :(isCompact()?dp(vtheme().dimension("cobra.buildShell.dimensions.5",104)):isMedium()?dp(vtheme().dimension("cobra.buildShell.dimensions.6",132)):dp(vtheme().dimension("cobra.buildShell.dimensions.7",156)));
        mRail.setLayoutParams(rail);
      }
      if(mHeader!=null){mHeader.setTextSize(isCompact()?19:25);vtheme().paint(mHeader,"screen.header");}
      mRoot.requestApplyInsets();mRoot.requestLayout();return;
    }
    if("COBRA • SETTINGS".equals(mCobraStageTitle)){buildShell();showSettings();return;}''')
    return text
