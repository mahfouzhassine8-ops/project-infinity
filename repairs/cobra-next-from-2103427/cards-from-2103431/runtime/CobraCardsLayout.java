package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Outline;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Looper;
import android.os.Build;
import android.view.WindowInsets;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.TextUtils;
import android.text.method.TransformationMethod;
import android.text.style.ForegroundColorSpan;
import android.text.style.StyleSpan;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import android.widget.FrameLayout;
import android.widget.GridView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;
import java.util.Map;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;
import java.util.WeakHashMap;

/** Cards-only presentation around accepted native views. No player, provider,
 * preference, control-listener or persistence operation is owned here. */
public final class CobraCardsLayout {
  private static final WeakHashMap<Activity,WeakReference<State>> OWNERS=new WeakHashMap<>();
  private static final WeakHashMap<View,Boolean> SHEET_REVEALS=new WeakHashMap<>();
  private static final int CYAN=0xff20cee9, WHITE=0xfff0f3f7, MUTED=0xffafc1d8;
  private static final Typeface NORMAL=Typeface.create("sans-serif",Typeface.NORMAL);
  private static final Typeface BOLD=Typeface.create("sans-serif",Typeface.BOLD);
  private static final Typeface HEADER_FACE=Build.VERSION.SDK_INT>=28?Typeface.create(NORMAL,500,false):Typeface.create("sans-serif-medium",Typeface.NORMAL);
  private static final Class<?>[] NONE=new Class<?>[0];
  private CobraCardsLayout(){}

  private static void mainThread(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("Cards layout requires main thread");}
  private static boolean cards(Activity a){return a!=null && "cards".equals(CobraArrange.ownedField(a,"mCobraGuideStyle")) && !Boolean.TRUE.equals(CobraArrange.ownedField(a,"mCobraProActive"));}
  private static Object read(Activity a,String name){return CobraArrange.ownedField(a,name);}
  private static Field field(Class<?> type,String name){try{Field f=type.getDeclaredField(name);f.setAccessible(true);return f;}catch(ReflectiveOperationException e){throw new IllegalStateException("Cards layout field: "+name,e);}}
  private static Object value(Object target,String name){try{return field(target.getClass(),name).get(target);}catch(IllegalAccessException e){throw new IllegalStateException(e);}}
  private static int integer(Object target,String name){return ((Number)value(target,name)).intValue();}
  private static void integer(Object target,String name,int number){try{field(target.getClass(),name).setInt(target,number);}catch(IllegalAccessException e){throw new IllegalStateException(e);}}
  private static void detach(View view){if(view.getParent() instanceof ViewGroup)((ViewGroup)view.getParent()).removeView(view);}
  private static void text(TextView view,CharSequence next){if(!TextUtils.equals(view.getText(),next))view.setText(next);}
  private static State existing(Activity a){WeakReference<State> ref=OWNERS.get(a);return ref==null?null:ref.get();}
  private static State state(Activity a){
    if(!cards(a))return null;
    View shell=(View)read(a,"mCobraGuideShell");
    if(shell==null || read(a,"mCobraGuideDetails")==null || read(a,"mCobraModeToolbar")==null)return null;
    State prior=existing(a);
    if(prior!=null && prior.shell==shell)return prior;
    if(prior!=null)prior.restore();
    State next=new State(a,shell);OWNERS.put(a,new WeakReference<>(next));return next;
  }

  /** Hook before shell/restyle native code. Restoration happens before another
   * mode applies its own styling; repeated Cards refresh retains its own state. */
  public static void beforeShell(Activity owner){
    mainThread();State prior=existing(owner);
    if(prior!=null && (!cards(owner) || read(owner,"mCobraGuideShell")!=prior.shell)){
      prior.restore();OWNERS.remove(owner);
    }
  }

  /** A fullscreen Cards menu belongs to the visible player, including while
   * Multi-View deliberately retains its GONE grid underneath that player.
   * Other modes and menu kinds retain their original native host selection. */
  public static FrameLayout frontPlayerSheetHost(Activity owner,String kind){
    if(!"player-settings".equals(kind) || !cards(owner)
        || Boolean.TRUE.equals(read(owner,"mCobraProSportsActive")))return null;
    android.content.res.Configuration configuration=owner.getResources().getConfiguration();
    if(Math.min(configuration.screenWidthDp,configuration.screenHeightDp)>=600)return null;
    mainThread();Object current=read(owner,"mPlayerOverlay");
    if(!(current instanceof FrameLayout))return null;
    FrameLayout player=(FrameLayout)current;
    return player.isAttachedToWindow() && player.isShown()?player:null;
  }

  /** Alpha zero can persist until the animator's first frame. A second layout
   * callback in that interval must not cancel and restart the same reveal.
   * Native geometry validation still runs on every callback, and the original
   * animation/opacity remain the sole presentation owner. */
  public static boolean beginFrontCardsSheetReveal(Activity owner,View panel){
    if(!cards(owner) || Boolean.TRUE.equals(read(owner,"mCobraProSportsActive")))return true;
    Object kind=read(owner,"mCobraSheetKind");
    if(!"player-settings".equals(kind) && !"visual-settings".equals(kind))return true;
    android.content.res.Configuration configuration=owner.getResources().getConfiguration();
    if(Math.min(configuration.screenWidthDp,configuration.screenHeightDp)>=600)return true;
    mainThread();
    if(panel==null || panel!=read(owner,"mCobraSheetPanel"))return true;
    return SHEET_REVEALS.put(panel,Boolean.TRUE)==null;
  }

  /** Hook after native visual-layout overrides. Mutates the EXISTING rect arrays
   * because native cobraLayoutGuide already holds their references in [[I. */
  public static void layout(Activity owner,Object model){
    mainThread();if(!cards(owner) || model==null)return;
    int width=integer(model,"width"),height=integer(model,"height");if(width<=0 || height<=0)return;
    float unit=width/941f,font=Math.max(1f,Math.min(2f,owner.getResources().getConfiguration().fontScale));
    DensityProfile densityProfile=new DensityProfile(width,height,owner.getResources().getConfiguration().fontScale);
    CobraCardsReuse.beforeLayout(owner,width,height,densityProfile.columns);
    if(densityProfile.expanded){expandedBoxes(model,width,height,font,densityProfile);return;}
    int columns=width<280?1:width>height && width>=1100?3:2;
    float header=Math.min(height*.22f,Math.max(1,104*unit*font));
    float rowTop=header+12*unit, toolbar=Math.max(48,122*unit*Math.min(1.25f,font));
    float cell=(width-32*unit-16*unit*(columns-1))/columns;
    float firstCard=Math.max(72,250*cell/448f);
    float reserve=Math.min(height*.48f,toolbar+22*unit+firstCard);
    float rowHeight=Math.min(362*unit*(1+(font-1)*.5f),Math.max(64,height-rowTop-18*unit-reserve));
    rowHeight=Math.min(rowHeight,Math.max(1,height-rowTop-toolbar-18*unit-36));
    int rowY=Math.round(rowTop),rowH=Math.max(1,Math.round(rowHeight));
    int browserY=Math.min(height-1,Math.round(rowTop+rowHeight+18*unit));
    box(model,"toolbar",0,0,width,Math.max(1,Math.round(header)));
    box(model,"rail",0,0,0,0);box(model,"directory",0,0,0,0);box(model,"footer",0,0,0,0);
    box(model,"video",Math.round(14*unit),rowY,Math.max(1,Math.round(476*unit)),rowH);
    box(model,"details",Math.round(497*unit),rowY,Math.max(1,width-Math.round(513*unit)),rowH);
    box(model,"browser",0,browserY,width,Math.max(1,height-browserY));
    integer(model,"columns",columns);
  }
  /** Profile selection uses the real usable logical window in dp. A narrow
   * dimension preserves the entire433 cover/phone path, including landscape. */
  static final class DensityProfile {
    final boolean expanded;final int columns;final float unit;
    DensityProfile(int width,int height,float font){
      expanded=Math.min(width,height)>=600;
      if(expanded){
        float minimum=160*Math.max(1,font);
        columns=Math.max(1,Math.min(4,(int)((width-24)/(minimum+8))));
        unit=.62f;
      }else{columns=width<280?1:width>height && width>=1100?3:2;unit=width/941f;}
    }
  }
  static boolean expanded(Activity a){
    if(!cards(a))return false;Object model=read(a,"mCobraModeLayout");
    return model!=null && Math.min(integer(model,"width"),integer(model,"height"))>=600;
  }
  private static void expandedBoxes(Object model,int width,int height,float font,DensityProfile profile){
    float u=profile.unit,header=Math.min(height*.22f,104*u*font),top=header+12*u;
    float videoWidth=width*.5f-21*u,bar=Math.max(48,122*u*Math.min(1.25f,font));
    float reserve=bar+22*u+Math.max(112,160+(font-1)*96);
    float h=Math.min(Math.min(362*u,videoWidth*9/16+24*u),Math.max(96,height-top-reserve-18*u));
    int y=Math.round(top),rowHeight=Math.max(1,Math.round(h));
    box(model,"toolbar",0,0,width,Math.max(1,Math.round(header)));
    box(model,"rail",0,0,0,0);box(model,"directory",0,0,0,0);box(model,"footer",0,0,0,0);
    box(model,"video",Math.round(14*u),y,Math.round(videoWidth),rowHeight);
    int detailX=Math.round(width*.5f+6*u);
    box(model,"details",detailX,y,width-detailX-Math.round(14*u),rowHeight);
    int browserY=Math.min(height-1,Math.round(top+h+18*u));
    box(model,"browser",0,browserY,width,Math.max(1,height-browserY));integer(model,"columns",profile.columns);
  }
  private static void box(Object model,String name,int x,int y,int width,int height){
    int[] rect=(int[])value(model,name);
    if(rect.length!=4)throw new IllegalStateException("Cards rect ownership: "+name);
    rect[0]=x;rect[1]=y;rect[2]=width;rect[3]=height;
  }

  /** Hook LAST at render/restyle returns, after native vtheme.tree. */
  public static void afterRender(Activity owner){
    mainThread();if(!cards(owner)){beforeShell(owner);return;}
    if(read(owner,"mCobraModeLayout")==null)return;State s=state(owner);if(s==null)return;
    s.apply();s.metadata();
  }
  /** POST-native cobraRefreshModeDetails hook: never replaces native sideeffects.
   * Returns true only when the actual Cards views are ready for formatting. */
  public static boolean refreshDetails(Activity owner){
    mainThread();if(!cards(owner))return false;
    if(read(owner,"mCobraModeLayout")==null)return false;State s=existing(owner);if(s==null)return false;
    s.captureNativeMetadata();s.apply();s.metadata();return true;
  }

  /** LAST post-native effects hook. Reuses the native status label/slot; the
   * native player state and binding remain the sole playback truth. */
  public static void refreshPreview(Activity owner){
    mainThread();if(!cards(owner)){beforeShell(owner);return;}
    if(read(owner,"mCobraModeLayout")==null)return;State s=existing(owner);if(s==null)return;
    s.refreshPreview();
  }

  /** Optional native cobraAmbientSurface prefix. Every parameter is computed by
   * its original caller; all other views/modes execute the unchanged body. */
  public static boolean ambientSurface(Activity owner,View view,int tint,int mode,int radius,boolean night){
    mainThread();if(!cards(owner) || view==null)return false;
    State s=existing(owner);if(s==null || s.restoring || read(owner,"mCobraGuideShell")!=s.shell)return false;
    AmbientPanel panel=view==s.toolbar?s.toolbarAmbient:view==s.details?s.detailsAmbient:null;
    if(panel==null)return false;s.rebasePublishedNativeStyles();
    return panel.apply(tint,mode,radius,night,owner.getResources().getDisplayMetrics().density);
  }

  private static final class Slot {
    final View view;final ViewGroup parent;final int index;final ViewGroup.LayoutParams params;
    Slot(View v){view=v;parent=(ViewGroup)v.getParent();index=parent.indexOfChild(v);params=v.getLayoutParams();}
    void restore(){detach(view);parent.addView(view,Math.min(index,parent.getChildCount()),params);}
  }
  private static final class Snapshot {
    final View view;Drawable background;final Drawable foreground;final int foregroundGravity;final ViewGroup.LayoutParams params;
    int left,top,right,bottom;final int visibility;float elevation;final float alpha;final ViewOutlineProvider outline;final boolean clip;
    final boolean group,clipChildren,clipPadding;final int orientation,linearGravity;
    final boolean isText;float textSize,letterSpacing;final float lineExtra,lineMultiplier;final int maxLines,minLines,gravity;
    final boolean fontPadding;final Drawable[] compounds;final int compoundPadding;Typeface typeface;android.content.res.ColorStateList textColors;
    final TextUtils.TruncateAt ellipsize;final TransformationMethod transformation;
    final boolean nativeIcon;final CharSequence originalText;
    final Drawable barDrawable;final android.content.res.ColorStateList barTint,barBackgroundTint;
    final int gridColumns,gridHorizontal,gridVertical;
    Snapshot(View v){
      view=v;background=v.getBackground();foreground=Build.VERSION.SDK_INT>=23?v.getForeground():null;foregroundGravity=Build.VERSION.SDK_INT>=23?v.getForegroundGravity():0;params=v.getLayoutParams();left=v.getPaddingLeft();top=v.getPaddingTop();right=v.getPaddingRight();bottom=v.getPaddingBottom();visibility=v.getVisibility();
      elevation=v.getElevation();alpha=v.getAlpha();outline=v.getOutlineProvider();clip=v.getClipToOutline();
      group=v instanceof ViewGroup;clipChildren=group && ((ViewGroup)v).getClipChildren();clipPadding=group && ((ViewGroup)v).getClipToPadding();
      orientation=v instanceof LinearLayout?((LinearLayout)v).getOrientation():-1;linearGravity=v instanceof LinearLayout?((LinearLayout)v).getGravity():0;
      isText=v instanceof TextView;TextView t=isText?(TextView)v:null;
      textSize=t==null?0:t.getTextSize();letterSpacing=t==null?0:t.getLetterSpacing();lineExtra=t==null?0:t.getLineSpacingExtra();lineMultiplier=t==null?1:t.getLineSpacingMultiplier();
      maxLines=t==null?0:t.getMaxLines();minLines=t==null?0:t.getMinLines();gravity=t==null?0:t.getGravity();fontPadding=t!=null && t.getIncludeFontPadding();
      originalText=t==null?null:t.getText();compounds=t==null?null:t.getCompoundDrawablesRelative();compoundPadding=t==null?0:t.getCompoundDrawablePadding();
      ProgressBar bar=v instanceof ProgressBar?(ProgressBar)v:null;barDrawable=bar==null?null:bar.getProgressDrawable();barTint=bar==null?null:bar.getProgressTintList();barBackgroundTint=bar==null?null:bar.getProgressBackgroundTintList();
      GridView grid=v instanceof GridView?(GridView)v:null;gridColumns=grid==null?0:grid.getNumColumns();gridHorizontal=grid==null?0:grid.getHorizontalSpacing();gridVertical=grid==null?0:grid.getVerticalSpacing();
      typeface=t==null?null:t.getTypeface();textColors=t==null?null:t.getTextColors();ellipsize=t==null?null:t.getEllipsize();transformation=t==null?null:t.getTransformationMethod();
      nativeIcon=v.getClass().getName().endsWith("$CobraIconButton");
    }
    /** Only properties the native renderer restores/applies on publication.
     * Parent/LP/clip/lines/selection and all other Cards-owned state stay original. */
    void publishedNativeStyle(){
      background=view.getBackground();left=view.getPaddingLeft();top=view.getPaddingTop();right=view.getPaddingRight();bottom=view.getPaddingBottom();elevation=view.getElevation();
      if(isText){TextView text=(TextView)view;textSize=text.getTextSize();letterSpacing=text.getLetterSpacing();typeface=text.getTypeface();textColors=text.getTextColors();}
    }
    void restore(){
      view.setBackground(background);if(Build.VERSION.SDK_INT>=23){view.setForeground(foreground);view.setForegroundGravity(foregroundGravity);}view.setPadding(left,top,right,bottom);view.setElevation(elevation);view.setAlpha(alpha);view.setOutlineProvider(outline);view.setClipToOutline(clip);
      if(params!=null)view.setLayoutParams(params);view.setVisibility(visibility);
      if(group){((ViewGroup)view).setClipChildren(clipChildren);((ViewGroup)view).setClipToPadding(clipPadding);}
      if(orientation>=0){((LinearLayout)view).setOrientation(orientation);((LinearLayout)view).setGravity(linearGravity);}
      if(isText){TextView t=(TextView)view;t.setTypeface(typeface);t.setTextSize(TypedValue.COMPLEX_UNIT_PX,textSize);t.setTextColor(textColors);t.setIncludeFontPadding(fontPadding);t.setLetterSpacing(letterSpacing);t.setLineSpacing(lineExtra,lineMultiplier);t.setMaxLines(maxLines);t.setMinLines(minLines);t.setEllipsize(ellipsize);t.setGravity(gravity);t.setTransformationMethod(transformation);t.setCompoundDrawablesRelative(compounds[0],compounds[1],compounds[2],compounds[3]);t.setCompoundDrawablePadding(compoundPadding);text(t,originalText);}
      if(view instanceof ProgressBar){ProgressBar bar=(ProgressBar)view;bar.setProgressDrawable(barDrawable);bar.setProgressTintList(barTint);bar.setProgressBackgroundTintList(barBackgroundTint);}
      if(view instanceof GridView){GridView grid=(GridView)view;grid.setNumColumns(gridColumns);grid.setHorizontalSpacing(gridHorizontal);grid.setVerticalSpacing(gridVertical);}
    }
  }

  private static final class State implements View.OnAttachStateChangeListener,View.OnLayoutChangeListener {
    final WeakReference<Activity> owner;final View shell;final LinearLayout toolbar,details,browser;
    final View preview,texture;final ViewGroup.LayoutParams textureParams;ViewGroup.LayoutParams ownedTextureParams;final TextView eyebrow,title,time,description,remaining;
    final ProgressBar progress;final FrameLayout frame;
    final ArrayList<Slot> originalDetails=new ArrayList<>();
    final IdentityHashMap<View,Snapshot> shared=new IdentityHashMap<>(),header=new IdentityHashMap<>(),browserHeader=new IdentityHashMap<>();
    final Snapshot stage;final View stageView;Object nativeRenderer,nativeTheme;Field nativeActiveField,nativeBindingsField;final AmbientPanel toolbarAmbient,detailsAmbient;
    PreviewBadge badge;
    View headerFirst,headerLast,browserFirst,browserSpacer;float scale=1,font=1;boolean restoring,hasNativeMetadata;
    final PanelSurface headerSurface=new PanelSurface(24,0),detailSurface=new PanelSurface(24,12),previewSurface=new PanelSurface(24,0),filterSurface=new PanelSurface(24,0);
    final ProgressSurface progressSurface=new ProgressSurface();
    CharSequence nativeEyebrow,nativeTitle,nativeTime,nativeDescription,nativeSub;
    int nativeProgressVisibility=View.GONE;
    Class<?> channelClass,programmeClass;Class<?>[] channelArgs;
    Field programmeStart,programmeStop;
    long start=Long.MIN_VALUE,stop=Long.MIN_VALUE,remainingMinutes=Long.MIN_VALUE;String locale="",zone="",endDatePrefix="",startDatePrefix="",scheduleSource="",scheduleText="",eyebrowSource="",countLocale="";
    CharSequence eyebrowText;SpannableString countText;int shownCount=-1;
    State(Activity a,View nativeShell){
      owner=new WeakReference<>(a);shell=nativeShell;toolbar=(LinearLayout)read(a,"mCobraModeToolbar");details=(LinearLayout)read(a,"mCobraGuideDetails");browser=(LinearLayout)read(a,"mCobraGuideBrowser");preview=(View)read(a,"mCobraGuideVideo");texture=(View)read(a,"mCobraPreviewTexture");textureParams=texture==null?null:texture.getLayoutParams();
      eyebrow=(TextView)read(a,"mCobraModeEyebrow");title=(TextView)read(a,"mCobraGuideNowLabel");time=(TextView)read(a,"mCobraGuideNextLabel");description=(TextView)read(a,"mCobraModeDescription");progress=(ProgressBar)read(a,"mCobraGuideProgress");
      toolbarAmbient=new AmbientPanel(a,toolbar,headerSurface);detailsAmbient=new AmbientPanel(a,details,detailSurface);
      stageView=(View)read(a,"mStage");stage=stageView==null?null:new Snapshot(stageView);
      for(View v:new View[]{shell,toolbar,details,browser,preview,eyebrow,title,time,description,progress})if(v!=null)shared.put(v,new Snapshot(v));
      for(int i=0;i<details.getChildCount();i++)originalDetails.add(new Slot(details.getChildAt(i)));
      nativeEyebrow=eyebrow.getText();nativeTitle=title.getText();nativeTime=time.getText();nativeDescription=description.getText();nativeProgressVisibility=progress.getVisibility();hasNativeMetadata=true;
      details.removeAllViews();frame=new FrameLayout(a);frame.setClipChildren(true);frame.setClipToPadding(true);
      details.addView(frame,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT));
      remaining=new TextView(a);remaining.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
      for(View v:new View[]{eyebrow,time,title,progress,remaining,description}){detach(v);frame.addView(v,new FrameLayout.LayoutParams(1,1));}
      captureRendererGeneration(a);shell.addOnAttachStateChangeListener(this);details.addOnLayoutChangeListener(this);
    }
    void captureRendererGeneration(Activity a){
      nativeRenderer=read(a,"mVisualTheme");if(nativeRenderer==null)return;
      nativeActiveField=field(nativeRenderer.getClass(),"active");nativeBindingsField=field(nativeRenderer.getClass(),"bindings");
      try{nativeTheme=nativeActiveField.get(null);}catch(IllegalAccessException e){throw new IllegalStateException(e);}
    }
    void rebasePublishedNativeStyles(){
      Activity a=owner.get();if(a==null || restoring)return;Object renderer=read(a,"mVisualTheme");if(renderer==null)return;
      if(nativeActiveField==null || renderer.getClass()!=nativeActiveField.getDeclaringClass()){nativeActiveField=field(renderer.getClass(),"active");nativeBindingsField=field(renderer.getClass(),"bindings");}
      try{
        Object theme=nativeActiveField.get(null);if(renderer==nativeRenderer && theme==nativeTheme)return;
        // publish/refreshClients executes atomically on the UI thread. Its
        // current native binding-owned properties are authoritative, not the
        // constructor snapshot from before that publication.
        Map<?,?> bindings=(Map<?,?>)nativeBindingsField.get(renderer);
        rebaseStyles(shared,bindings);rebaseStyles(header,bindings);rebaseStyles(browserHeader,bindings);
        if(stage!=null && bindings.containsKey(stage.view))stage.publishedNativeStyle();
        if(badge!=null){if(bindings.containsKey(badge.originalLabel.view))badge.originalLabel.publishedNativeStyle();if(badge.originalContainer!=null && bindings.containsKey(badge.originalContainer.view))badge.originalContainer.publishedNativeStyle();}
        nativeRenderer=renderer;nativeTheme=theme;
      }catch(IllegalAccessException e){throw new IllegalStateException("Cards native publication",e);}
    }
    void rebaseStyles(IdentityHashMap<View,Snapshot> snapshots,Map<?,?> bindings){for(Snapshot snapshot:snapshots.values())if(bindings.containsKey(snapshot.view))snapshot.publishedNativeStyle();}
    Snapshot snapshot(IdentityHashMap<View,Snapshot> snapshots,View view){Snapshot old=snapshots.get(view);if(old==null){old=new Snapshot(view);snapshots.put(view,old);}return old;}
    void restoreSnapshots(IdentityHashMap<View,Snapshot> snapshots){for(Snapshot s:snapshots.values())s.restore();snapshots.clear();}
    void restoreBrowser(){if(browserSpacer!=null){detach(browserSpacer);browserSpacer=null;}restoreSnapshots(browserHeader);}
    void restoreStage(){
      rebasePublishedNativeStyles();
      // Native clearStage writes its own padding BEFORE detaching the guide.
      // Never overwrite that newer destination layout during this callback.
      Activity a=owner.get();
      if(stage!=null && a!=null && read(a,"mStage")==stageView && stageView.getPaddingLeft()==0 && stageView.getPaddingTop()==0 && stageView.getPaddingRight()==0 && stageView.getPaddingBottom()==0)
        stageView.setPadding(stage.left,stage.top,stage.right,stage.bottom);
    }
    void restore(){
      if(restoring)return;rebasePublishedNativeStyles();restoring=true;
      shell.removeOnAttachStateChangeListener(this);details.removeOnLayoutChangeListener(this);restoreStage();if(badge!=null){badge.restore();badge=null;}
      if(texture!=null && texture.getParent()==preview && texture.getLayoutParams()==ownedTextureParams && textureParams!=null)texture.setLayoutParams(textureParams);ownedTextureParams=null;
      for(Slot slot:originalDetails)slot.restore();detach(frame);
      toolbarAmbient.restore();detailsAmbient.restore();restoreSnapshots(header);restoreBrowser();restoreSnapshots(shared);
      text(eyebrow,nativeEyebrow);text(title,nativeTitle);text(time,nativeTime);text(description,nativeDescription);progress.setVisibility(nativeProgressVisibility);
      Activity a=owner.get();if(a!=null && nativeSub!=null){Object sub=read(a,"mCobraModeSub");if(sub instanceof TextView)text((TextView)sub,nativeSub);}
    }
    void apply(){
      Activity a=owner.get();if(a==null || !cards(a) || restoring)return;rebasePublishedNativeStyles();
      Object model=read(a,"mCobraModeLayout");if(model==null)return;
      scale=(shell.getWidth()>0?shell.getWidth():integer(model,"width")*a.getResources().getDisplayMetrics().density)/941f;
      font=Math.max(1f,Math.min(2f,a.getResources().getConfiguration().fontScale));
      physicalLayout(a,model);
      if(stageView!=null && read(a,"mStage")==stageView && (stageView.getPaddingLeft()!=0 || stageView.getPaddingTop()!=0 || stageView.getPaddingRight()!=0 || stageView.getPaddingBottom()!=0))stageView.setPadding(0,0,0,0);
      if(shell.getBackground()==null || !(shell.getBackground() instanceof android.graphics.drawable.ColorDrawable) || ((android.graphics.drawable.ColorDrawable)shell.getBackground()).getColor()!=0xff000000)shell.setBackgroundColor(0xff000000);
      if(browser.getBackground()==null || !(browser.getBackground() instanceof android.graphics.drawable.ColorDrawable) || ((android.graphics.drawable.ColorDrawable)browser.getBackground()).getColor()!=0xff000000)browser.setBackgroundColor(0xff000000);if(browser.getPaddingLeft()!=0 || browser.getPaddingTop()!=0 || browser.getPaddingRight()!=0 || browser.getPaddingBottom()!=0)browser.setPadding(0,0,0,0);
      if(toolbar.getPaddingLeft()!=0 || toolbar.getPaddingTop()!=0 || toolbar.getPaddingRight()!=0 || toolbar.getPaddingBottom()!=0)toolbar.setPadding(0,0,0,0);if(toolbar.getGravity()!=Gravity.CENTER_VERTICAL)toolbar.setGravity(Gravity.CENTER_VERTICAL);headerSurface.scale=scale;if(toolbar.getBackground()!=headerSurface && !toolbarAmbient.valid())toolbar.setBackground(headerSurface);
      if(details.getPaddingLeft()!=0 || details.getPaddingTop()!=0 || details.getPaddingRight()!=0 || details.getPaddingBottom()!=0)details.setPadding(0,0,0,0);detailSurface.scale=scale;if(details.getBackground()!=detailSurface && !detailsAmbient.valid())details.setBackground(detailSurface);
      previewSurface.scale=scale;if(preview.getBackground()!=previewSurface)preview.setBackground(previewSurface);if(preview.getOutlineProvider()!=ViewOutlineProvider.BACKGROUND)preview.setOutlineProvider(ViewOutlineProvider.BACKGROUND);if(!preview.getClipToOutline())preview.setClipToOutline(true);if(preview.getPaddingLeft()!=0 || preview.getPaddingTop()!=0 || preview.getPaddingRight()!=0 || preview.getPaddingBottom()!=0)preview.setPadding(0,0,0,0);textureInset();
      styleHeader(a);styleBrowser(a);styleDetails();
    }
    void textureInset(){
      // Inset the original video only. Native controls/status/PiP use the full
      // host coordinate plane and must not inherit video padding or clipping.
      if(texture==null || texture.getParent()!=preview)return;
      int left=px(10),top=px(14),right=px(10),bottom=px(10);ViewGroup.LayoutParams old=texture.getLayoutParams();
      if(old instanceof FrameLayout.LayoutParams){FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)old;if(p.width==ViewGroup.LayoutParams.MATCH_PARENT && p.height==ViewGroup.LayoutParams.MATCH_PARENT && p.leftMargin==left && p.topMargin==top && p.rightMargin==right && p.bottomMargin==bottom){ownedTextureParams=p;return;}}
      FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT);p.leftMargin=left;p.topMargin=top;p.rightMargin=right;p.bottomMargin=bottom;texture.setLayoutParams(p);ownedTextureParams=p;
    }
    void physicalLayout(Activity a,Object model){
      if(shell.getWidth()<=0 || shell.getHeight()<=0)return;
      int insetLeft=0,insetTop=0,insetRight=0,insetBottom=0;
      if(Build.VERSION.SDK_INT>=23){WindowInsets insets=shell.getRootWindowInsets();if(insets!=null){int[] location=new int[2];shell.getLocationInWindow(location);View decor=a.getWindow().getDecorView();insetLeft=Math.max(0,insets.getSystemWindowInsetLeft()-location[0]);insetTop=Math.max(0,insets.getSystemWindowInsetTop()-location[1]);insetRight=Math.max(0,location[0]+shell.getWidth()-decor.getWidth()+insets.getSystemWindowInsetRight());insetBottom=Math.max(0,location[1]+shell.getHeight()-decor.getHeight()+insets.getSystemWindowInsetBottom());}}
      float density=a.getResources().getDisplayMetrics().density;
      int width=Math.max(1,shell.getWidth()-insetLeft-insetRight),height=Math.max(1,shell.getHeight()-insetTop-insetBottom);
      int working=Math.round(integer(model,"height")*density);if(height-working>density)height=Math.min(height,working);
      if(expanded(a)){
        scale=density*.62f;float headerHeight=Math.min(height*.22f,104*scale*font),top=headerHeight+12*scale;
        float videoWidth=width*.5f-21*scale,bar=Math.max(48*density,122*scale*Math.min(1.25f,font));
        float reserve=bar+22*scale+Math.max(112*density,(160+(font-1)*96)*density);
        float h=Math.min(Math.min(362*scale,videoWidth*9/16+24*scale),Math.max(96*density,height-top-reserve-18*scale));
        int y=Math.round(top),rowHeight=Math.max(1,Math.round(h)),detailX=Math.round(width*.5f+6*scale);
        int browserY=Math.min(height-1,Math.round(top+h+18*scale));
        physical(toolbar,insetLeft,insetTop,width,Math.round(headerHeight));
        physical(preview,insetLeft+Math.round(14*scale),insetTop+y,Math.round(videoWidth),rowHeight);
        physical(details,insetLeft+detailX,insetTop+y,width-detailX-Math.round(14*scale),rowHeight);
        physical(browser,insetLeft,insetTop+browserY,width,height-browserY);return;
      }
      scale=width/941f;float headerHeight=Math.min(height*.22f,Math.max(1,104*scale*font)),rowTop=headerHeight+12*scale;
      float barHeight=Math.max(48*density,122*scale*Math.min(1.25f,font));int columns=integer(model,"columns");
      float cell=(width-32*scale-16*scale*(columns-1))/columns,firstCard=Math.max(72*density,250*cell/448f);
      float reserve=Math.min(height*.48f,barHeight+22*scale+firstCard);
      float rowHeight=Math.min(362*scale*(1+(font-1)*.5f),Math.max(64*density,height-rowTop-18*scale-reserve));rowHeight=Math.min(rowHeight,Math.max(1,height-rowTop-barHeight-18*scale-36*density));
      int y=Math.round(rowTop),h=Math.max(1,Math.round(rowHeight)),browserTop=Math.min(height-1,Math.round(rowTop+rowHeight+18*scale));
      physical(toolbar,insetLeft,insetTop,width,Math.round(headerHeight));physical(preview,insetLeft+Math.round(14*scale),insetTop+y,Math.round(476*scale),h);
      physical(details,insetLeft+Math.round(497*scale),insetTop+y,width-Math.round(513*scale),h);physical(browser,insetLeft,insetTop+browserTop,width,height-browserTop);
    }
    void physical(View view,int x,int y,int width,int height){
      ViewGroup.LayoutParams old=view.getLayoutParams();if(old instanceof FrameLayout.LayoutParams){FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)old;if(p.width==width && p.height==height && p.leftMargin==x && p.topMargin==y && p.rightMargin==0 && p.bottomMargin==0)return;}
      FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.max(1,width),Math.max(1,height));p.leftMargin=x;p.topMargin=y;view.setLayoutParams(p);
    }
    void refreshPreview(){
      Activity a=owner.get();if(a==null || restoring)return;rebasePublishedNativeStyles();
      View host=(View)read(a,"mCobraPreviewHost");
      if(host!=preview){if(badge!=null){badge.restore();badge=null;}return;}
      View label=host.findViewWithTag("cobra_preview_label");
      if(!(label instanceof TextView)){if(badge!=null){badge.restore();badge=null;}return;}
      if(badge==null || badge.label!=label){if(badge!=null)badge.restore();badge=new PreviewBadge(this,(TextView)label);}
      badge.refresh();
    }
    void styleHeader(Activity a){
      if(toolbar.getChildCount()<4)return;
      View first=toolbar.getChildAt(0),last=toolbar.getChildAt(toolbar.getChildCount()-1);
      if(first!=headerFirst || last!=headerLast){restoreSnapshots(header);headerFirst=first;headerLast=last;}
      for(int i=0;i<toolbar.getChildCount();i++)snapshot(header,toolbar.getChildAt(i));
      View labelBox=toolbar.getChildAt(1),visuals=toolbar.getChildAt(2),views=toolbar.getChildAt(3);
      styleIcon(first,header,1);styleIcon(visuals,header,2);styleIcon(views,header,3);
      linear(first,96,90,0,16,22);linear(labelBox,0,104*font,1,0,0);linear(visuals,96,90,0,0,28);linear(views,96,90,0,0,20);
      TextView name=(TextView)read(a,"mCobraModeTitle"),sub=(TextView)read(a,"mCobraModeSub");
      snapshot(header,name);if(!header.containsKey(sub))nativeSub=sub.getText();snapshot(header,sub);snapshot(header,labelBox);
      labelBox.setPadding(0,0,0,0);if(labelBox instanceof LinearLayout)((LinearLayout)labelBox).setGravity(Gravity.CENTER_VERTICAL);
      style(name,HEADER_FACE,WHITE,42,1);name.setLetterSpacing(.0325f);text(name,"Cobra");
      style(sub,NORMAL,MUTED,17,1);sub.setLetterSpacing(.12f);
      headerCount(a,sub);
    }
    void headerCount(Activity a,TextView sub){
      Object channels=read(a,"mChannels");int count=channels instanceof List?((List<?>)channels).size():0;
      String currentLocale=Locale.getDefault().toLanguageTag();
      if(countText==null || count!=shownCount || !currentLocale.equals(countLocale)){
        String label="CARDS    |    "+String.format(Locale.getDefault(),"%,d",count)+" CHANNELS";
        countText=new SpannableString(label);countText.setSpan(new ForegroundColorSpan(CYAN),0,5,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);countText.setSpan(new StyleSpan(Typeface.BOLD),0,5,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);shownCount=count;countLocale=currentLocale;
      }
      text(sub,countText);
    }
    void styleBrowser(Activity a){
      if(browser.getChildCount()==0)return;
      View first=browser.getChildAt(0);
      if(!(first instanceof LinearLayout) || ((LinearLayout)first).getChildCount()<3)return;
      if(first!=browserFirst){restoreBrowser();browserFirst=first;}
      LinearLayout row=(LinearLayout)first;snapshot(browserHeader,row);
      filterSurface.scale=scale;filterSurface.divider=true;if(row.getBackground()!=filterSurface)row.setBackground(filterSurface);if(row.getGravity()!=Gravity.CENTER_VERTICAL)row.setGravity(Gravity.CENTER_VERTICAL);if(row.getPaddingLeft()!=px(20) || row.getPaddingTop()!=px(20) || row.getPaddingRight()!=px(16) || row.getPaddingBottom()!=px(20))row.setPadding(px(20),px(20),px(16),px(20));
      ViewGroup.LayoutParams oldRow=row.getLayoutParams();int rowHeight=px(122*Math.min(1.25f,font)),edge=px(16);
      if(!(oldRow instanceof LinearLayout.LayoutParams) || oldRow.width!=ViewGroup.LayoutParams.MATCH_PARENT || oldRow.height!=rowHeight || ((LinearLayout.LayoutParams)oldRow).leftMargin!=edge || ((LinearLayout.LayoutParams)oldRow).rightMargin!=edge){LinearLayout.LayoutParams root=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,rowHeight);root.leftMargin=edge;root.rightMargin=edge;row.setLayoutParams(root);}
      View selector=row.getChildAt(0),source=row.getChildAt(row.getChildCount()-2),search=row.getChildAt(row.getChildCount()-1);
      snapshot(browserHeader,selector);snapshot(browserHeader,source);snapshot(browserHeader,search);
      if(row.getChildCount()==3){View blank=new View(a);blank.setTag("cobra_cards_toolbar_spacer");blank.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);row.addView(blank,1,new LinearLayout.LayoutParams(0,1,1));browserSpacer=blank;}
      styleIcon(selector,browserHeader,4);
      if(selector instanceof TextView){TextView label=(TextView)selector;style(label,BOLD,WHITE,24,1,true);label.setGravity(Gravity.CENTER_VERTICAL|Gravity.LEFT);label.setPadding(px(88),0,px(42),0);String value=label.getText().toString().replace(" / Channel wall"," / Channel Wall").replace("  \u25be","");text(label,value);}
      linear(selector,434,82,0,0,0);styleIcon(source,browserHeader,5);styleIcon(search,browserHeader,6);linear(source,94,82,0,0,18);linear(search,94,82,0,0,0);
      for(int i=1;i<browser.getChildCount();i++)if(browser.getChildAt(i) instanceof GridView){
        GridView grid=(GridView)browser.getChildAt(i);snapshot(browserHeader,grid);int columns=integer(read(a,"mCobraModeLayout"),"columns");
        if(grid.getNumColumns()!=columns)grid.setNumColumns(columns);CobraCardsReuse.columnsApplied(a,grid);if(grid.getHorizontalSpacing()!=px(16))grid.setHorizontalSpacing(px(16));if(grid.getVerticalSpacing()!=px(24))grid.setVerticalSpacing(px(24));
        if(grid.getPaddingLeft()!=px(16) || grid.getPaddingTop()!=px(22) || grid.getPaddingRight()!=px(16) || grid.getPaddingBottom()!=px(24))grid.setPadding(px(16),px(22),px(16),px(24));
      }
    }
    void styleIcon(View view,IdentityHashMap<View,Snapshot> snapshots,int kind){
      Snapshot capture=snapshot(snapshots,view);
      // Native CobraIconButton draws a fallback even for an empty glyph. Keep
      // its metadata/callbacks and cover its drawing with an opaque foreground.
      // API21/22 retain the original native glyph with the Cards panel surface.
      boolean foreground=capture.nativeIcon && Build.VERSION.SDK_INT>=23;
      Drawable current=foreground?view.getForeground():view.getBackground();
      if(!(current instanceof ButtonSurface) || ((ButtonSurface)current).kind!=kind){ButtonSurface shape=new ButtonSurface(kind);shape.scale=scale;shape.drawIcon=!capture.nativeIcon || foreground;if(foreground)view.setForeground(shape);else view.setBackground(shape);}
      else if(((ButtonSurface)current).scale!=scale){((ButtonSurface)current).scale=scale;view.invalidate();}
      if(foreground && view.getBackground()!=null)view.setBackground(null);
      if(kind!=4 && (view.getPaddingLeft()!=0 || view.getPaddingTop()!=0 || view.getPaddingRight()!=0 || view.getPaddingBottom()!=0))view.setPadding(0,0,0,0);
    }
    void style(TextView view,Typeface face,int color,float size,int lines){style(view,face,color,size,lines,false);}
    void style(TextView view,Typeface face,int color,float size,int lines,boolean preservePadding){
      if(view.getTypeface()!=face)view.setTypeface(face);if(view.getTextColors().isStateful() || view.getCurrentTextColor()!=color)view.setTextColor(color);float pixels=size*scale*font;if(view.getTextSize()!=pixels)view.setTextSize(TypedValue.COMPLEX_UNIT_PX,pixels);
      if(view.getIncludeFontPadding())view.setIncludeFontPadding(false);if(!preservePadding && (view.getPaddingLeft()!=0 || view.getPaddingTop()!=0 || view.getPaddingRight()!=0 || view.getPaddingBottom()!=0))view.setPadding(0,0,0,0);if(view.getLetterSpacing()!=0)view.setLetterSpacing(0);if(view.getMaxLines()!=lines)view.setMaxLines(lines);if(view.getEllipsize()!=TextUtils.TruncateAt.END)view.setEllipsize(TextUtils.TruncateAt.END);if(view.getGravity()!=(Gravity.TOP|Gravity.LEFT))view.setGravity(Gravity.TOP|Gravity.LEFT);if(view.getLineSpacingExtra()!=0 || view.getLineSpacingMultiplier()!=1.06f)view.setLineSpacing(0,1.06f);
    }
    void styleDetails(){
      rebasePublishedNativeStyles();
      style(eyebrow,NORMAL,MUTED,18,1);style(time,NORMAL,MUTED,22,1);style(title,BOLD,WHITE,29,1);style(description,NORMAL,MUTED,21,5);style(remaining,NORMAL,MUTED,16,1);remaining.setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);
      if(progress.getPaddingLeft()!=0 || progress.getPaddingTop()!=0 || progress.getPaddingRight()!=0 || progress.getPaddingBottom()!=0)progress.setPadding(0,0,0,0);if(progress.getProgressTintList()!=null)progress.setProgressTintList(null);if(progress.getProgressBackgroundTintList()!=null)progress.setProgressBackgroundTintList(null);if(progress.getProgressDrawable()!=progressSurface)progress.setProgressDrawable(progressSurface);int max=progress.getMax();progressSurface.setLevel(max<=0?0:(int)Math.max(0,Math.min(10000,Math.round(progress.getProgress()*10000d/max))));
      float timeY=32+22*font+20,titleY=timeY+26*font+8,progressY=titleY+36*font+26,descriptionY=progressY+47;
      float width=details.getWidth()>0?details.getWidth()/scale:428;
      place(eyebrow,24,32,width-48,22*font);place(time,24,timeY,width-48,26*font);place(title,24,titleY,width-48,36*font);
      place(progress,24,progressY,Math.max(24,width-142),10);place(remaining,width-104,progressY-5,80,26*font);
      float height=details.getHeight()>0?details.getHeight()/scale:362;
      place(description,24,descriptionY,width-48,Math.max(1,height-descriptionY-20));int descriptionVisibility=!TextUtils.isEmpty(nativeDescription) && height-descriptionY-20>=21*font?View.VISIBLE:View.GONE;if(description.getVisibility()!=descriptionVisibility)description.setVisibility(descriptionVisibility);
    }
    void captureNativeMetadata(){
      nativeEyebrow=eyebrow.getText();nativeTitle=title.getText();nativeTime=time.getText();nativeDescription=description.getText();nativeProgressVisibility=progress.getVisibility();hasNativeMetadata=true;
      Activity a=owner.get();if(a!=null){Object sub=read(a,"mCobraModeSub");if(sub instanceof TextView)nativeSub=((TextView)sub).getText();}
    }
    void metadata(){
      Activity a=owner.get();if(a==null || !cards(a) || !hasNativeMetadata)return;
      String label=nativeEyebrow==null?"":nativeEyebrow.toString();int slash=label.indexOf("  /  ");
      if(slash>0){if(!label.equals(eyebrowSource)){String heading=label.substring(0,slash),channel=label.substring(slash+5);String line=heading+"   |   "+channel;SpannableString span=new SpannableString(line);span.setSpan(new ForegroundColorSpan(CYAN),0,heading.length(),Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);span.setSpan(new StyleSpan(Typeface.BOLD),0,heading.length(),Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);eyebrowSource=label;eyebrowText=span;}text(eyebrow,eyebrowText);}
      Object channel=read(a,"mGuidePreviewChannel"),programme=null;
      if(channel!=null){
        if(channelClass!=channel.getClass()){channelClass=channel.getClass();channelArgs=new Class<?>[]{channelClass};}
        if(channel==read(a,"mCobraInspectedChannel"))programme=read(a,"mCobraInspectedProgram");
        if(programme==null)programme=CobraArrange.ownedCall(a,"cobraCurrentProgram",channelArgs,channel);
      }
      if(programme==null){remaining.setVisibility(View.GONE);return;}
      if(programmeClass!=programme.getClass()){programmeClass=programme.getClass();programmeStart=field(programmeClass,"start");programmeStop=field(programmeClass,"stop");}
      long first,last;
      try{first=programmeStart.getLong(programme);last=programmeStop.getLong(programme);}catch(IllegalAccessException e){throw new IllegalStateException(e);}
      String currentLocale=Locale.getDefault().toLanguageTag(),currentZone=TimeZone.getDefault().getID();
      if(first!=start || last!=stop || !currentLocale.equals(locale) || !currentZone.equals(zone)){
        start=first;stop=last;locale=currentLocale;zone=currentZone;SimpleDateFormat date=new SimpleDateFormat("EEE MMM d • ",Locale.US);startDatePrefix=date.format(new Date(first));endDatePrefix=date.format(new Date(last));scheduleSource="";
      }
      String original=nativeTime==null?"":nativeTime.toString();
      if(!original.equals(scheduleSource)){String schedule=original;int newline=schedule.indexOf('\n');if(newline>=0)schedule=schedule.substring(0,newline);if(startDatePrefix.equals(endDatePrefix)){String repeated=" – "+endDatePrefix;int at=schedule.indexOf(repeated);if(at>=0)schedule=schedule.substring(0,at)+" – "+schedule.substring(at+repeated.length());}scheduleText=schedule;scheduleSource=original;}
      text(time,scheduleText);
      long clock=System.currentTimeMillis();boolean live=first<=clock && clock<last && last>first && nativeProgressVisibility==View.VISIBLE;
      remaining.setVisibility(live?View.VISIBLE:View.GONE);if(live){long minutes=Math.max(0,(last-clock+59999)/60000);if(minutes!=remainingMinutes){text(remaining,minutes+" min left");remainingMinutes=minutes;}}
    }
    int px(float number){return Math.max(1,Math.round(number*scale));}
    void linear(View view,float width,float height,float weight,float left,float right){
      int w=width==0?0:px(width),h=px(height),l=left==0?0:px(left),r=right==0?0:px(right);ViewGroup.LayoutParams old=view.getLayoutParams();
      if(old instanceof LinearLayout.LayoutParams){LinearLayout.LayoutParams p=(LinearLayout.LayoutParams)old;if(p.width==w && p.height==h && p.leftMargin==l && p.rightMargin==r && p.topMargin==0 && p.bottomMargin==0 && p.weight==weight && p.gravity==Gravity.CENTER_VERTICAL)return;}
      LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h,weight);p.leftMargin=l;p.rightMargin=r;p.gravity=Gravity.CENTER_VERTICAL;view.setLayoutParams(p);
    }
    void place(View view,float x,float y,float width,float height){
      int w=px(width),h=px(height),l=Math.round(x*scale),t=Math.round(y*scale);ViewGroup.LayoutParams old=view.getLayoutParams();
      if(old instanceof FrameLayout.LayoutParams){FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)old;if(p.width==w && p.height==h && p.leftMargin==l && p.topMargin==t && p.rightMargin==0 && p.bottomMargin==0 && p.gravity==(Gravity.TOP|Gravity.LEFT))return;}
      FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(w,h,Gravity.TOP|Gravity.LEFT);p.leftMargin=l;p.topMargin=t;view.setLayoutParams(p);
    }
    public void onLayoutChange(View view,int left,int top,int right,int bottom,int oldLeft,int oldTop,int oldRight,int oldBottom){
      Activity a=owner.get();if(!restoring && a!=null && cards(a) && (right-left!=oldRight-oldLeft || bottom-top!=oldBottom-oldTop))styleDetails();
    }
    public void onViewAttachedToWindow(View view){rebasePublishedNativeStyles();Activity a=owner.get();if(a!=null && cards(a) && read(a,"mCobraGuideShell")==shell && stageView!=null && read(a,"mStage")==stageView)stageView.setPadding(0,0,0,0);}
    public void onViewDetachedFromWindow(View view){restoreStage();}
  }

  /** One bounded native wrapper per owned panel. Types, alpha, orientation,
   * radius and stroke match accepted cobraAmbientSurface exactly. */
  private static final class AmbientPanel {
    final View view;final PanelSurface panel;final Map<View,Drawable> base,applied;
    final boolean hadBase,hadApplied;final Drawable originalBase,originalApplied;
    LayerDrawable wrapper;int tint,mode,radius,densityBits;boolean night,handled;
    @SuppressWarnings("unchecked") AmbientPanel(Activity a,View view,PanelSurface panel){
      this.view=view;this.panel=panel;base=(Map<View,Drawable>)read(a,"mCobraAmbientSurfaceBase");applied=(Map<View,Drawable>)read(a,"mCobraAmbientSurfaceApplied");
      hadBase=base.containsKey(view);hadApplied=applied.containsKey(view);originalBase=base.get(view);originalApplied=applied.get(view);
    }
    boolean valid(){return wrapper!=null && view.getBackground()==wrapper && base.get(view)==panel && applied.get(view)==wrapper;}
    boolean apply(int nextTint,int nextMode,int nextRadius,boolean nextNight,float density){
      Drawable current=view.getBackground();if(current!=panel && !valid())return false;
      handled=true;
      if(nextMode==0 && !nextNight){if(current!=panel)view.setBackground(panel);base.remove(view);applied.remove(view);return true;}
      int bits=Float.floatToIntBits(density);
      if(wrapper==null || tint!=nextTint || mode!=nextMode || radius!=nextRadius || night!=nextNight || densityBits!=bits){
        int lineAlpha=nextNight?230:nextMode==2?245:150,fillAlpha=nextNight?218:nextMode==2?30:13;
        int lineColor=Color.argb(lineAlpha,Color.red(nextTint),Color.green(nextTint),Color.blue(nextTint));
        int fillColor=nextNight?Color.argb(fillAlpha,0,0,0):Color.argb(fillAlpha,Color.red(nextTint),Color.green(nextTint),Color.blue(nextTint));
        GradientDrawable gradient=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{fillColor,0,0});gradient.setCornerRadius(Math.max(1,Math.round(nextRadius*density)));
        GradientDrawable stroke=new GradientDrawable();stroke.setColor(0);stroke.setCornerRadius(Math.max(1,Math.round(nextRadius*density)));stroke.setStroke(Math.max(1,Math.round((nextMode!=2 && !nextNight?1:2)*density)),lineColor);
        wrapper=new LayerDrawable(new Drawable[]{panel,gradient,stroke});if(Build.VERSION.SDK_INT>=23)wrapper.setPaddingMode(LayerDrawable.PADDING_MODE_STACK);
        tint=nextTint;mode=nextMode;radius=nextRadius;night=nextNight;densityBits=bits;
      }
      base.put(view,panel);applied.put(view,wrapper);if(view.getBackground()!=wrapper)view.setBackground(wrapper);return true;
    }
    void restore(){
      // Restore only mappings still owned by us, never a newer native writer.
      if(handled && (valid() || !base.containsKey(view) && !applied.containsKey(view))){
        if(hadBase)base.put(view,originalBase);else base.remove(view);
        if(hadApplied)applied.put(view,originalApplied);else applied.remove(view);
      }
      wrapper=null;
    }
  }

  /** Owns presentation only. The original native legacy label and StatusSlot
   * remain in place, with their native listeners, pulse state and accessibility. */
  private static final class PreviewBadge implements View.OnLayoutChangeListener {
    final State owner;final TextView label;final View container,pulse;final Snapshot originalLabel,originalContainer;
    final LiveSurface background=new LiveSurface();final LiveDot dot=new LiveDot();
    final Class<?>[] playerArgs;final Method visibleStatus,smallPip;final Object six;
    Class<?> bindingClass,vitalsClass;Field bindingChannel,bindingClosed,bindingVitals,vitalsLive;
    CharSequence nativeText;int pulseVisibility;boolean active,drawableOwned;
    PreviewBadge(State state,TextView view){
      owner=state;label=view;
      if(view.getParent()==state.preview){container=view;pulse=null;}
      else if(view.getParent() instanceof FrameLayout && ((View)view.getParent()).getParent()==state.preview && "cobra_pulse_slot".equals(((View)view.getParent()).getTag())){
        container=(View)view.getParent();
        if(value(container,"legacy")!=view)throw new IllegalStateException("Cards preview status ownership");
        pulse=(View)value(container,"pulse");
      }else throw new IllegalStateException("Cards preview status hierarchy");
      if(!(container.getLayoutParams() instanceof FrameLayout.LayoutParams))throw new IllegalStateException("Cards preview status geometry");
      originalLabel=new Snapshot(view);originalContainer=container==view?null:new Snapshot(container);
      nativeText=label.getText();pulseVisibility=pulse==null?View.GONE:pulse.getVisibility();
      Activity a=state.owner.get();
      try{
        playerArgs=new Class<?>[]{Class.forName("androidx.media3.exoplayer.ExoPlayer",false,a.getClassLoader())};
        Class<?> effects=Class.forName("com.projectinfinity.kodi.CobraPresentationEffects",false,a.getClassLoader());
        visibleStatus=effects.getDeclaredMethod("visibleStatus",CharSequence.class);visibleStatus.setAccessible(true);
        six=read(a,"mCobraSix");smallPip=six.getClass().getDeclaredMethod("smallPreviewPip");smallPip.setAccessible(true);
      }catch(ReflectiveOperationException e){throw new IllegalStateException("Cards native preview status API",e);}
      container.addOnLayoutChangeListener(this);
    }
    String status(Object state){try{return (String)visibleStatus.invoke(null,state);}catch(IllegalAccessException|InvocationTargetException e){throw new IllegalStateException("Cards native visible status",e);}}
    boolean liveBinding(Activity a,Object player,Object channel){
      Object bindings=read(a,"mCobraPlayerBindings"),binding=bindings instanceof Map?((Map<?,?>)bindings).get(player):null;
      if(binding==null || !Boolean.TRUE.equals(CobraArrange.ownedCall(a,"isCobraAsyncAlive",NONE)))return false;
      if(bindingClass!=binding.getClass()){bindingClass=binding.getClass();bindingChannel=field(bindingClass,"channel");bindingClosed=field(bindingClass,"closed");bindingVitals=field(bindingClass,"vitals");}
      try{
        if(bindingClosed.getBoolean(binding))return false;
        Object bound=bindingChannel.get(binding),vitals=bindingVitals.get(binding);if(bound==null || vitals==null)return false;
        if(vitalsClass!=vitals.getClass()){vitalsClass=vitals.getClass();vitalsLive=field(vitalsClass,"live");}
        if(!vitalsLive.getBoolean(vitals))return false;
        if(owner.channelClass!=channel.getClass()){owner.channelClass=channel.getClass();owner.channelArgs=new Class<?>[]{owner.channelClass};}
        Object key=CobraArrange.ownedCall(a,"cobraChannelKey",owner.channelArgs,channel);
        return key!=null && key.equals(read(a,"mCobraPreviewSessionKey")) && key.equals(CobraArrange.ownedCall(a,"cobraChannelKey",owner.channelArgs,bound));
      }catch(IllegalAccessException e){throw new IllegalStateException("Cards native live binding",e);}
    }
    void refresh(){
      Activity a=owner.owner.get();if(a==null)return;
      Object player=read(a,"mCobraPreviewPlayer"),channel=read(a,"mGuidePreviewChannel");
      String state=(String)CobraArrange.ownedCall(a,"cobraPlayerState",playerArgs,player);
      // Save each genuine post-effects publication, not our prior LIVE label.
      CharSequence published=label.getText();nativeText=active && TextUtils.equals(published,"LIVE")?status(state):published;
      if(pulse!=null && read(a,"mCobraEffects")!=null)pulseVisibility=pulse.getVisibility();
      boolean show=cards(a) && player!=null && channel!=null && "LIVE".equals(state)
          && read(a,"mPlayerOverlay")==null && read(a,"mMultiOverlay")==null
          && !Boolean.TRUE.equals(read(a,"mInPictureInPicture")) && !Boolean.TRUE.equals(read(a,"mBackgroundStopped"))
          && liveBinding(a,player,channel);
      if(!show){if(active)release();return;}
      active=true;background.scale=owner.scale;
      if(label.getBackground()!=background)label.setBackground(background);
      if(label.getTypeface()!=BOLD)label.setTypeface(BOLD);if(label.getCurrentTextColor()!=WHITE)label.setTextColor(WHITE);
      float textSize=17*owner.scale*owner.font;if(label.getTextSize()!=textSize)label.setTextSize(TypedValue.COMPLEX_UNIT_PX,textSize);
      if(label.getIncludeFontPadding())label.setIncludeFontPadding(false);if(label.getGravity()!=(Gravity.CENTER_VERTICAL|Gravity.LEFT))label.setGravity(Gravity.CENTER_VERTICAL|Gravity.LEFT);
      if(label.getMaxLines()!=1)label.setMaxLines(1);if(label.getLetterSpacing()!=0)label.setLetterSpacing(0);label.setEllipsize(null);
      int padding=owner.px(14),diameter=owner.px(14),gap=owner.px(11);dot.setBounds(0,0,diameter,diameter);
      if(label.getPaddingLeft()!=padding || label.getPaddingTop()!=0 || label.getPaddingRight()!=padding || label.getPaddingBottom()!=0)label.setPadding(padding,0,padding,0);
      if(!drawableOwned){label.setCompoundDrawablesRelative(dot,null,null,null);drawableOwned=true;}
      if(label.getCompoundDrawablePadding()!=gap)label.setCompoundDrawablePadding(gap);
      text(label,"LIVE");if(label.getAlpha()!=1)label.setAlpha(1);if(label.getVisibility()!=View.VISIBLE)label.setVisibility(View.VISIBLE);
      if(pulse!=null && pulse.getVisibility()!=View.GONE)pulse.setVisibility(View.GONE);
      int bottom=owner.px(26);View controls=owner.preview.findViewWithTag("cobra_preview_controls");
      if(controls!=null && controls.getVisibility()==View.VISIBLE){int height=controls.getHeight();if(height<=0 && controls.getLayoutParams()!=null)height=Math.max(0,controls.getLayoutParams().height);bottom=Math.max(bottom,height+owner.px(6));}
      int width=owner.px(89*owner.font),height=owner.px(38*owner.font),left=owner.px(27);
      FrameLayout.LayoutParams old=(FrameLayout.LayoutParams)container.getLayoutParams();
      if(old.width!=width || old.height!=height || old.gravity!=(Gravity.BOTTOM|Gravity.LEFT) || old.leftMargin!=left || old.bottomMargin!=bottom || old.topMargin!=0 || old.rightMargin!=0){
        FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(width,height,Gravity.BOTTOM|Gravity.LEFT);p.leftMargin=left;p.bottomMargin=bottom;container.setLayoutParams(p);
      }
    }
    void release(){
      originalLabel.restore();if(originalContainer!=null)originalContainer.restore();text(label,nativeText);
      // Match native StatusSlot.show semantics for the current publication.
      int visibility=pulse!=null && pulseVisibility==View.VISIBLE?View.INVISIBLE:TextUtils.isEmpty(status(nativeText))?View.GONE:View.VISIBLE;
      label.setVisibility(visibility);if(pulse!=null)pulse.setVisibility(pulseVisibility);active=false;drawableOwned=false;
    }
    void restore(){if(active)release();container.removeOnLayoutChangeListener(this);}
    public void onLayoutChange(View view,int l,int t,int r,int b,int ol,int ot,int or,int ob){
      // Moving StatusSlot leaves its child's local bounds unchanged; invoke the
      // EXISTING avoidance routine for its new actual ancestor position too.
      try{smallPip.invoke(six);}catch(IllegalAccessException|InvocationTargetException e){throw new IllegalStateException("Cards native PiP avoidance",e);}
    }
  }
  private static final class LiveSurface extends Drawable {
    final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);final RectF box=new RectF();float scale=1;
    LiveSurface(){paint.setColor(0xee000000);}
    @Override public void draw(Canvas canvas){box.set(getBounds());canvas.drawRoundRect(box,10*scale,10*scale,paint);}
    @Override public void setAlpha(int alpha){paint.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){paint.setColorFilter(filter);invalidateSelf();}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
  private static final class LiveDot extends Drawable {
    final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    LiveDot(){paint.setColor(CYAN);}
    @Override public void draw(Canvas canvas){Rect b=getBounds();canvas.drawCircle(b.exactCenterX(),b.exactCenterY(),Math.min(b.width(),b.height())/2f,paint);}
    @Override public void setAlpha(int alpha){paint.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){paint.setColorFilter(filter);invalidateSelf();}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }

  private static class PanelSurface extends Drawable {
    final Paint fill=new Paint(Paint.ANTI_ALIAS_FLAG),line=new Paint(Paint.ANTI_ALIAS_FLAG);final RectF box=new RectF();
    final float radius,topInset;float scale=1;boolean divider;
    PanelSurface(float radius,float top){this.radius=radius;topInset=top;line.setStyle(Paint.Style.STROKE);}
    @Override protected void onBoundsChange(Rect bounds){fill.setShader(new LinearGradient(bounds.left,bounds.top,bounds.right,bounds.bottom,new int[]{0xff00090d,0xff000203,0xff001016},new float[]{0,.6f,1},Shader.TileMode.CLAMP));}
    @Override public void draw(Canvas canvas){Rect b=getBounds();box.set(b.left+.75f*scale,b.top+topInset*scale+.75f*scale,b.right-.75f*scale,b.bottom-.75f*scale);canvas.drawRoundRect(box,radius*scale,radius*scale,fill);line.setColor(0xff08667e);line.setStrokeWidth(Math.max(1,1.4f*scale));canvas.drawRoundRect(box,radius*scale,radius*scale,line);if(divider){line.setColor(0xff173b49);line.setStrokeWidth(Math.max(1,scale));float x=b.left+491*scale;canvas.drawLine(x,b.top+32*scale,x,b.top+94*scale,line);}}
    @Override public void getOutline(Outline out){Rect b=getBounds();out.setRoundRect(b.left,b.top+Math.round(topInset*scale),b.right,b.bottom,radius*scale);}
    @Override public void setAlpha(int alpha){fill.setAlpha(alpha);line.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
  private static final class ButtonSurface extends PanelSurface {
    final int kind;boolean drawIcon=true;final Paint icon=new Paint(Paint.ANTI_ALIAS_FLAG);final Path shape=new Path();boolean focused,pressed;
    ButtonSurface(int kind){super(20,0);this.kind=kind;icon.setStyle(Paint.Style.STROKE);icon.setStrokeCap(Paint.Cap.ROUND);icon.setStrokeJoin(Paint.Join.ROUND);}
    @Override public boolean isStateful(){return true;}
    @Override protected boolean onStateChange(int[] states){boolean f=false,p=false;for(int state:states){f|=state==android.R.attr.state_focused;p|=state==android.R.attr.state_pressed;}if(f==focused && p==pressed)return false;focused=f;pressed=p;invalidateSelf();return true;}
    @Override public void draw(Canvas canvas){
      super.draw(canvas);if(!drawIcon)return;Rect r=getBounds();float x=r.exactCenterX(),y=r.exactCenterY(),s=scale;icon.setColor(kind==3 || kind==4?CYAN:WHITE);icon.setStrokeWidth(Math.max(1,4*s));
      if(kind==1 || kind==5){for(int i=0;i<3;i++){float length=(kind==5?34-i*8:38)*s;canvas.drawLine(x-19*s,y+(i-1)*15*s,x-19*s+length,y+(i-1)*15*s,icon);}}
      else if(kind==2){canvas.drawCircle(x,y,11*s,icon);for(int i=0;i<8;i++){double angle=i*Math.PI/4;float dx=(float)Math.cos(angle),dy=(float)Math.sin(angle);canvas.drawLine(x+dx*20*s,y+dy*20*s,x+dx*27*s,y+dy*27*s,icon);}shape.reset();shape.moveTo(x+17*s,y+22*s);shape.lineTo(x+24*s,y+29*s);shape.lineTo(x+32*s,y+19*s);canvas.drawPath(shape,icon);}
      else if(kind==3){for(int row=0;row<2;row++)for(int col=0;col<2;col++){float left=x+(col==0?-20:4)*s,top=y+(row==0?-20:4)*s;canvas.drawRoundRect(left,top,left+16*s,top+16*s,3*s,3*s,icon);}}
      else if(kind==4){x=r.left+43*s;shape.reset();for(int i=0;i<10;i++){double angle=-Math.PI/2+i*Math.PI/5;float radius=(i%2==0?20:9)*s;float px=x+(float)Math.cos(angle)*radius,py=y+(float)Math.sin(angle)*radius;if(i==0)shape.moveTo(px,py);else shape.lineTo(px,py);}shape.close();canvas.drawPath(shape,icon);icon.setColor(WHITE);icon.setStyle(Paint.Style.FILL);shape.reset();shape.moveTo(r.right-40*s,y-4*s);shape.lineTo(r.right-26*s,y-4*s);shape.lineTo(r.right-33*s,y+6*s);shape.close();canvas.drawPath(shape,icon);icon.setStyle(Paint.Style.STROKE);}
      else if(kind==6){canvas.drawCircle(x-3*s,y-4*s,15*s,icon);canvas.drawLine(x+8*s,y+7*s,x+21*s,y+21*s,icon);}
      if(focused || pressed){icon.setColor(CYAN);icon.setStrokeWidth(Math.max(1,2*scale));box.inset(3*scale,3*scale);canvas.drawRoundRect(box,18*scale,18*scale,icon);}
    }
  }
  private static final class ProgressSurface extends Drawable {
    final Paint track=new Paint(Paint.ANTI_ALIAS_FLAG),fill=new Paint(Paint.ANTI_ALIAS_FLAG);final RectF all=new RectF(),part=new RectF();
    ProgressSurface(){track.setColor(0xff2d4051);fill.setColor(0xff29c9ea);}
    @Override public void draw(Canvas canvas){all.set(getBounds());float radius=all.height()/2;canvas.drawRoundRect(all,radius,radius,track);if(getLevel()>0){part.set(all);part.right=part.left+part.width()*getLevel()/10000f;canvas.drawRoundRect(part,radius,radius,fill);}}
    @Override protected boolean onLevelChange(int level){invalidateSelf();return true;}
    @Override public void setAlpha(int alpha){track.setAlpha(alpha);fill.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
}
