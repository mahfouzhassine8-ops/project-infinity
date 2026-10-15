"""Pure, narrowly scoped Fold fitting and existing-motion lifecycle repair.

The caller owns source receipts and writes. No decoder, surface, transport or
mode 0-11 policy is replaced here.
"""


def once(source, old, new):
    count = source.count(old)
    if count != 1:
        raise ValueError(f"Fold/motion anchor expected once, got {count}: {old[:100]!r}")
    return source.replace(old, new, 1)


MOTION_HELPERS = r'''
  private boolean cobraMotionEnabled(){
    return Build.VERSION.SDK_INT<26||android.animation.ValueAnimator.areAnimatorsEnabled();
  }

  private void cobraResetMotion(View view){
    if(view==null)return;
    view.animate().withEndAction(null).withStartAction(null).cancel();
    view.animate().setStartDelay(0L);
    view.setAlpha(1f);view.setTranslationX(0f);view.setTranslationY(0f);
    view.setScaleX(1f);view.setScaleY(1f);
  }

  private boolean cobraChromeCanHide(View chrome){
    return chrome!=null&&chrome==mPlayerChrome&&chrome.getVisibility()==View.VISIBLE
        &&!mCobraTimeshiftDragging&&!mCobraPlayerLocked&&!mInPictureInPicture
        &&mCobraActionSheet==null&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null;
  }

  private void cobraAnimatePlayerChromeIn(View chrome){
    cobraResetMotion(chrome);
    if(chrome==null||!cobraMotionEnabled()||mCobraTimeshiftDragging)return;
    // The touch targets stay in place, including a finger already on the timeline.
    chrome.setAlpha(0f);
    chrome.animate().alpha(1f).setDuration(150L)
        .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
  }
'''


def transform(source):
    source = once(source, '    static final float MAX_CROP=1.06f;\n', '')
    source = once(source, '''      // Fold Adaptive is conservative: preserve the entire frame on extreme/narrow
      // windows, and use only a tiny center crop on near-matching large viewports.
      float mismatch=Math.max(source/view,view/source);
      boolean roomy=Math.min(viewportWidth,viewportHeight)>=600;
      if(roomy&&mismatch<=1.18f){
        float z=Math.min(MAX_CROP,Math.max(1f/sx,1f/sy));sx*=z;sy*=z;
      }''', '''      // Always fit the complete frame to this measured video pane. Its dimensions
      // already follow inner/cover, rotation, multi-window and open player drawers.
      // A different source/display ratio requires bars; never add arbitrary crop.''')

    source = once(source,
        '    if(mPlayerChrome.getVisibility()==View.VISIBLE){mMain.removeCallbacks(mHideChrome);mPlayerChrome.setVisibility(View.GONE);}',
        '    if(mPlayerChrome.getVisibility()==View.VISIBLE){mMain.removeCallbacks(mHideChrome);cobraResetMotion(mPlayerChrome);mPlayerChrome.setVisibility(View.GONE);}')
    source = once(source,
        '    mPlayerChrome.animate().cancel();if(mPlayerChrome.getVisibility()!=View.VISIBLE){mPlayerChrome.setAlpha(0f);mPlayerChrome.setVisibility(View.VISIBLE);mPlayerChrome.animate().alpha(1f).setDuration(120).start();}else mPlayerChrome.setAlpha(1f);scheduleChromeHide();',
        '''    final LinearLayout chrome=mPlayerChrome;boolean hidden=chrome.getVisibility()!=View.VISIBLE;
    cobraResetMotion(chrome);chrome.setVisibility(View.VISIBLE);
    if(hidden&&cobraMotionEnabled()&&!mCobraTimeshiftDragging){chrome.setAlpha(0f);chrome.animate().alpha(1f).setDuration(120L).start();}
    scheduleChromeHide();''')
    source = once(source,
        '    if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE&&!this.mCobraTimeshiftDragging){final LinearLayout target=mPlayerChrome;target.animate().cancel();target.animate().alpha(0f).setDuration(150).withEndAction(()->{if(target==mPlayerChrome&&!this.mCobraTimeshiftDragging)target.setVisibility(View.GONE);}).start();}',
        '''    if(!cobraChromeCanHide(mPlayerChrome))return;
    final LinearLayout target=mPlayerChrome;cobraResetMotion(target);
    if(!cobraMotionEnabled()){target.setVisibility(View.GONE);return;}
    target.animate().alpha(0f).setDuration(150L).withEndAction(()->{
      if(target!=mPlayerChrome)return;
      if(cobraChromeCanHide(target))target.setVisibility(View.GONE);
      cobraResetMotion(target);
    }).start();''')
    source = once(source,
        '    if(mPlayerChrome!=null)mPlayerOverlay.removeView(mPlayerChrome);',
        '    if(mPlayerChrome!=null){cobraResetMotion(mPlayerChrome);mPlayerOverlay.removeView(mPlayerChrome);}')
    source = once(source,
        '    if(visible){chrome.setAlpha(0f);chrome.setTranslationY(dp(8));chrome.animate().alpha(1f).translationY(0f).setDuration(150L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();}',
        '    if(chrome.getVisibility()==View.VISIBLE)cobraAnimatePlayerChromeIn(chrome);')
    source = once(source,
        '    mPlayerChrome = null;',
        '    cobraResetMotion(mPlayerChrome);mPlayerChrome = null;')

    source = once(source,
        'CobraIconButton button=new CobraIconButton(glyph,description,dark);button.setOnClickListener(click);return button;',
        'CobraIconButton button=new CobraIconButton(glyph,description,dark);button.setOnClickListener(click);cobraPolishFocusable(button);return button;')
    source = once(source,
        '    void icon(String value){glyph=value;invalidate();}',
        '''    @Override public void setEnabled(boolean enabled){
      float alpha=getAlpha();super.setEnabled(enabled);
      // Runtime availability owns disabled dimming, even if focus remains held.
      if(!enabled){cobraResetMotion(this);setAlpha(alpha);}
    }
    void icon(String value){glyph=value;invalidate();}''')
    source = once(source,
        '      v.animate().cancel();v.setTranslationX(0f);v.setTranslationY(0f);',
        '''      float stateAlpha=v.getAlpha();cobraResetMotion(v);
      if(!v.isEnabled()){v.setAlpha(stateAlpha);return;}
      if(!cobraMotionEnabled()){v.setScaleX(focused?1.018f:1f);v.setScaleY(focused?1.018f:1f);v.setAlpha(focused?1f:.97f);return;}''')
    source = once(source,
        '    if(group==null)return;\n    int count=Math.min(group.getChildCount(),14);',
        '''    if(group==null||!group.isAttachedToWindow())return;
    if(!cobraMotionEnabled()){for(int i=0;i<group.getChildCount();i++){View child=group.getChildAt(i);if(child!=null&&!child.hasFocus())cobraResetMotion(child);}return;}
    int count=Math.min(group.getChildCount(),14);''')
    source = once(source,
        '      child.animate().cancel();child.setAlpha(0f);child.setTranslationY(dp(8));child.setScaleX(.992f);child.setScaleY(.992f);',
        '      cobraResetMotion(child);child.setAlpha(0f);child.setTranslationY(dp(8));child.setScaleX(.992f);child.setScaleY(.992f);')
    source = once(source,
        '    if(view==null)return;view.animate().cancel();view.setAlpha(0f);view.setScaleX(.985f);view.setScaleY(.985f);',
        '''    if(view==null||!view.isAttachedToWindow())return;cobraResetMotion(view);
    if(!cobraMotionEnabled())return;
    view.setAlpha(0f);view.setScaleX(.985f);view.setScaleY(.985f);''')
    source = once(source,
        'panel.post(()->cobraAnimatePanelIn(panel,!isPortrait()));',
        'panel.post(()->{if(panel==mCobraPlayerDrawer&&panel.isAttachedToWindow())cobraAnimatePanelIn(panel,!isPortrait());});')
    source = once(source,
        '    if(mCobraPlayerDrawer==null)return false;if(mCobraPlayerDrawer.getParent() instanceof android.view.ViewGroup)',
        '    if(mCobraPlayerDrawer==null)return false;cobraResetMotion(mCobraPlayerDrawer);if(mCobraPlayerDrawer.getParent() instanceof android.view.ViewGroup)')
    source = once(source,
        '    mCobraSheetLayoutListener=null;mCobraSheetAnchor=null;mCobraSheetPane=null;mCobraSheetPanel=null;mCobraSheetHeightLimit=Integer.MAX_VALUE;',
        '    cobraResetMotion(mCobraSheetPanel);mCobraSheetLayoutListener=null;mCobraSheetAnchor=null;mCobraSheetPane=null;mCobraSheetPanel=null;mCobraSheetHeightLimit=Integer.MAX_VALUE;')
    source = once(source,
        '      panel.setScaleX(.985f);panel.setScaleY(.985f);panel.setTranslationX(dp(8));',
        '''      cobraResetMotion(panel);
      if(!cobraMotionEnabled())return;
      panel.setAlpha(0f);panel.setScaleX(.985f);panel.setScaleY(.985f);panel.setTranslationX(dp(8));''')
    source = once(source,
        '  private static final class CobraMotionSpec {',
        MOTION_HELPERS + '\n  private static final class CobraMotionSpec {')
    return source
