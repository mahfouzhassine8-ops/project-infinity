"""Surgical display-state repairs over the preserved Cobra 2103197 Activity.

The existing thirteen display modes and their geometry policies remain unchanged.
Only fix stale state ownership, inconsistent Custom defaults, and missing observations.
"""

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one exact anchor, got {count}')
    return text.replace(old, new, 1)


HELPERS = r'''
  private int cobraBindingAspect(CobraPlayerBinding binding){
    // The channel/session owns its selection. A cached prior fullscreen channel must
    // never overwrite it when a new video size, drawer resize or Fold reflow arrives.
    int mode=binding.player==mPlayer?cobraChannelAspect(binding.channel):0;
    if(binding.vitals.live&&binding.vitals.preferences.aspect>=0)mode=binding.vitals.preferences.aspect;
    return mode;
  }

  private Object cobraDisplayNumber(float value){
    return Float.isNaN(value)||Float.isInfinite(value)?JSONObject.NULL:Float.valueOf(value);
  }

  private void cobraFitCaptions(CobraPlayerBinding binding){
    TextureView texture=binding.texture;View captions=binding.captions;
    if(texture==null||captions==null||texture.getWidth()<=0||texture.getHeight()<=0
        ||captions.getParent()!=texture.getParent()||!(texture.getParent() instanceof FrameLayout))return;
    FrameLayout parent=(FrameLayout)texture.getParent();
    int left=texture.getLeft()-parent.getPaddingLeft(),top=texture.getTop()-parent.getPaddingTop();
    android.view.ViewGroup.LayoutParams current=captions.getLayoutParams();
    FrameLayout.LayoutParams old=current instanceof FrameLayout.LayoutParams?(FrameLayout.LayoutParams)current:null;
    int gravity=Gravity.TOP|Gravity.LEFT;
    if(old==null||old.width!=texture.getWidth()||old.height!=texture.getHeight()
        ||old.leftMargin!=left||old.topMargin!=top||old.gravity!=gravity){
      FrameLayout.LayoutParams next=new FrameLayout.LayoutParams(texture.getWidth(),texture.getHeight(),gravity);
      next.leftMargin=left;next.topMargin=top;captions.setLayoutParams(next);
    }
    // A TextureView layout callback precedes its caption sibling's layout. The
    // parent can still lay that sibling with its old measured size and clear the
    // request raised by setLayoutParams. Recheck after this traversal, when a
    // fresh request cannot be consumed by that old sibling layout.
    if(captions.getVisibility()!=View.GONE&&(captions.getMeasuredWidth()!=texture.getWidth()
        ||captions.getMeasuredHeight()!=texture.getHeight()||captions.getWidth()!=texture.getWidth()
        ||captions.getHeight()!=texture.getHeight()||captions.getLeft()!=texture.getLeft()
        ||captions.getTop()!=texture.getTop())){
      captions.post(()->{
        if(!binding.current()||binding.texture!=texture||binding.captions!=captions
            ||texture.getParent()!=parent||captions.getParent()!=parent)return;
        if(captions.getVisibility()!=View.GONE&&(captions.getMeasuredWidth()!=texture.getWidth()
            ||captions.getMeasuredHeight()!=texture.getHeight()||captions.getWidth()!=texture.getWidth()
            ||captions.getHeight()!=texture.getHeight()||captions.getLeft()!=texture.getLeft()
            ||captions.getTop()!=texture.getTop()))captions.requestLayout();
      });
    }
  }

  private JSONObject cobraDisplayGeometry(CobraPlayerBinding binding)throws Exception{
    JSONObject geometry=new JSONObject();
    int selected=cobraBindingAspect(binding);
    geometry.put("selected_mode",selected);
    geometry.put("effective_mode",mInPictureInPicture?0:selected);
    geometry.put("global_default_mode",mPrefs.getInt(COBRA_ASPECT_MODE,0));
    geometry.put("channel_override_mode",binding.vitals.live?binding.vitals.preferences.aspect:-1);
    geometry.put("picture_in_picture",mInPictureInPicture);
    geometry.put("configuration_orientation",getResources().getConfiguration().orientation);
    geometry.put("density",cobraDisplayNumber(getResources().getDisplayMetrics().density));
    geometry.put("observation","texture_matrix_not_rendered_frame");
    geometry.put("physical_device_verified",false);
    VideoSize size=binding.player.getVideoSize();
    geometry.put("source_width",size.width);geometry.put("source_height",size.height);
    geometry.put("source_pixel_ratio",cobraDisplayNumber(size.pixelWidthHeightRatio));
    TextureView texture=binding.texture;
    geometry.put("texture_attached",texture!=null&&texture.isAttachedToWindow());
    if(texture==null)return geometry;
    int width=texture.getWidth(),height=texture.getHeight();
    geometry.put("viewport_width",width);geometry.put("viewport_height",height);
    geometry.put("surface_available",texture.isAvailable());
    geometry.put("view_scale_x",cobraDisplayNumber(texture.getScaleX()));
    geometry.put("view_scale_y",cobraDisplayNumber(texture.getScaleY()));
    geometry.put("view_translation_x",cobraDisplayNumber(texture.getTranslationX()));
    geometry.put("view_translation_y",cobraDisplayNumber(texture.getTranslationY()));
    int[] location=new int[2];texture.getLocationInWindow(location);
    geometry.put("viewport_window_x",location[0]);geometry.put("viewport_window_y",location[1]);
    android.graphics.Matrix matrix=texture.getTransform(new android.graphics.Matrix());
    float[] values=new float[9];matrix.getValues(values);JSONArray transform=new JSONArray();
    for(float value:values)transform.put(cobraDisplayNumber(value));geometry.put("texture_matrix",transform);
    android.graphics.RectF content=new android.graphics.RectF(0,0,width,height);matrix.mapRect(content);
    JSONArray bounds=new JSONArray();for(float value:new float[]{content.left,content.top,content.right,content.bottom})bounds.put(cobraDisplayNumber(value));
    geometry.put("transformed_bounds",bounds);
    JSONArray cropped=new JSONArray();for(float value:new float[]{Math.max(0,-content.left),Math.max(0,-content.top),Math.max(0,content.right-width),Math.max(0,content.bottom-height)})cropped.put(cobraDisplayNumber(value));
    geometry.put("cropped_edges_pixels",cropped);
    JSONArray bars=new JSONArray();for(float value:new float[]{Math.max(0,content.left),Math.max(0,content.top),Math.max(0,width-content.right),Math.max(0,height-content.bottom)})bars.put(cobraDisplayNumber(value));
    geometry.put("uncovered_edges_pixels",bars);
    android.view.WindowInsets insets=Build.VERSION.SDK_INT>=23?texture.getRootWindowInsets():null;
    if(insets!=null){
      int left,top,right,bottom;
      if(Build.VERSION.SDK_INT>=30){android.graphics.Insets safe=insets.getInsets(android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.displayCutout());left=safe.left;top=safe.top;right=safe.right;bottom=safe.bottom;}
      else{left=insets.getSystemWindowInsetLeft();top=insets.getSystemWindowInsetTop();right=insets.getSystemWindowInsetRight();bottom=insets.getSystemWindowInsetBottom();
        if(Build.VERSION.SDK_INT>=28&&insets.getDisplayCutout()!=null){android.view.DisplayCutout cut=insets.getDisplayCutout();left=Math.max(left,cut.getSafeInsetLeft());top=Math.max(top,cut.getSafeInsetTop());right=Math.max(right,cut.getSafeInsetRight());bottom=Math.max(bottom,cut.getSafeInsetBottom());}}
      JSONArray safe=new JSONArray();for(int value:new int[]{left,top,right,bottom})safe.put(value);geometry.put("window_safe_insets",safe);
    }
    return geometry;
  }
'''


def transform(text: str) -> str:
    text = once(text,
        '    Channel target=mPlaying;cobraRememberChannelTransition(target);',
        '    Channel target=mPlaying;mAspectMode=cobraChannelAspect(target);cobraRememberChannelTransition(target);',
        'Refresh fullscreen aspect on channel retune')
    text = once(text,
        '''  private void applyCobraAspectTransform() {
    cobraFitVideo(mPlayerTexture,mPlayer,mInPictureInPicture?0:mAspectMode);
  }''',
        '''  private void applyCobraAspectTransform() {
    CobraPlayerBinding binding=mCobraPlayerBindings.get(mPlayer);
    if(binding!=null)cobraFitBinding(binding);
    else cobraFitVideo(mPlayerTexture,mPlayer,mInPictureInPicture?0:mAspectMode);
  }''', 'Use the current playback binding for fullscreen reflow')
    text = once(text,
        '''  private void cobraFitBinding(CobraPlayerBinding binding) {
    int mode=binding.player==mPlayer?mAspectMode:0;
    if(binding.vitals.live&&binding.vitals.preferences.aspect>=0)mode=binding.vitals.preferences.aspect;
    cobraFitVideo(binding.texture,binding.player,mInPictureInPicture?0:mode);
  }''',
        '''  private void cobraFitBinding(CobraPlayerBinding binding) {
    int mode=cobraBindingAspect(binding);
    if(binding.player==mPlayer)mAspectMode=mode;
    cobraFitVideo(binding.texture,binding.player,mInPictureInPicture?0:mode);
    cobraFitCaptions(binding);
  }''', 'Single aspect owner across layout and video-size callbacks')
    text = once(text, 'mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f)',
                'mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1f)', 'Custom width matches displayed 100% default')
    text = once(text, 'mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f)',
                'mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,1f)', 'Custom height matches displayed 100% default')
    text = once(text,
        'row.put("channel_preference_scope",s.live?"profile_and_source_and_channel":"not_live_channel");sessions.put(row);',
        'row.put("channel_preference_scope",s.live?"profile_and_source_and_channel":"not_live_channel");row.put("display_geometry",cobraDisplayGeometry(b));sessions.put(row);',
        'Observe the actual TextureView transform in existing diagnostics')
    if 'private int cobraBindingAspect(' in text:
        raise RuntimeError('Display helper already present')
    at = text.rfind('}')
    if at < 0:
        raise RuntimeError('Missing Activity closing brace')
    return text[:at]+HELPERS+'\n'+text[at:]
