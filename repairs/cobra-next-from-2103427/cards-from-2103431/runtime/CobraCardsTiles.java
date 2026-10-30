package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Outline;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.os.Looper;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.FrameLayout;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;
import java.util.WeakHashMap;

/** Cards-only tile presentation. Native row actions and provider jobs remain owned
 * by the accepted Cobra implementation. No artwork is embedded in this helper. */
public final class CobraCardsTiles {
  private static final WeakHashMap<LinearLayout,WeakReference<Holder>> HOLDERS=new WeakHashMap<>();
  private static final Class<?>[] LONG={long.class};
  private static final int CYAN=0xff20cee9, MUTED=0xffafc1d8, WHITE=0xfff0f3f7;
  private static final Typeface NORMAL=Typeface.create("sans-serif",Typeface.NORMAL);
  private static final Typeface BOLD=Typeface.create("sans-serif-medium",Typeface.NORMAL);
  private CobraCardsTiles(){}

  private static void mainThread(){
    if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("Cards UI requires main thread");
  }
  private static boolean cards(Activity a){return a!=null && "cards".equals(CobraArrange.ownedField(a,"mCobraGuideStyle"));}
  private static Holder holder(LinearLayout card){WeakReference<Holder> r=HOLDERS.get(card);return r==null?null:r.get();}
  public static void created(Activity a,LinearLayout card){
    mainThread();if(!cards(a) || holder(card)!=null)return;
    Holder h=new Holder(a,card);HOLDERS.put(card,new WeakReference<>(h));
  }
  /** Replaces only native CobraPosterChannelCard.bind; original row binding runs once. */
  public static void bind(Activity a,LinearLayout card,Object channel){
    mainThread();if(!cards(a))return;
    Holder h=holder(card);if(h==null){created(a,card);h=holder(card);}
    if(h!=null)h.bind(channel);
  }
  /** Replaces only native card refreshPlaying; off-hierarchy dot is not animated. */
  public static void refresh(Activity a,LinearLayout card){
    mainThread();if(!cards(a))return;Holder h=holder(card);
    if(h!=null && card.isAttachedToWindow())h.refresh();
  }
  private static Field field(Class<?> type,String name){
    try{Field f=type.getDeclaredField(name);f.setAccessible(true);return f;}
    catch(ReflectiveOperationException e){throw new IllegalStateException("Cards field: "+name,e);}
  }
  private static Object value(Field f,Object target){
    try{return f.get(target);}catch(IllegalAccessException e){throw new IllegalStateException("Cards field read",e);}
  }
  private static String string(Field f,Object target){Object x=value(f,target);return x==null?"":String.valueOf(x);}
  private static void detach(View view){if(view.getParent() instanceof ViewGroup)((ViewGroup)view.getParent()).removeView(view);}
  private static void text(TextView view,String value){if(!TextUtils.equals(view.getText(),value))view.setText(value);}

  private static final class Holder implements View.OnLayoutChangeListener,View.OnAttachStateChangeListener,View.OnClickListener {
    final WeakReference<Activity> owner;
    final LinearLayout card;
    final TextView category,title,now,time;
    final ProgressBar progress;
    final View hero,mark,playing;
    final FrameLayout body;
    final OwnedLogo logo;
    final TextView fallback,live;
    final View divider;
    final MoreView more;
    final CardSurface surface=new CardSurface();
    final RoundedProgress progressShape=new RoundedProgress();
    final LiveDot liveDot=new LiveDot();
    Class<?> channelType,programmeType,layoutType;
    Class<?>[] channelArgs,rowArgs;
    Field channelName,channelGroup,channelIcon,programmeStart,programmeStop,programmeTitle,layoutColumns,layoutBrowser;
    Object bound;
    String logoUrl="",name="",group="",dateLocale="",dateZone="",scheduleText="";
    long start=Long.MIN_VALUE,stop=Long.MIN_VALUE;
    SimpleDateFormat date;
    float configuredWidth=-1,configuredFont=-1,scale=1;
    boolean hasLive,configuring;

    Holder(Activity a,LinearLayout root){
      owner=new WeakReference<>(a);card=root;Class<?> nativeCard=root.getClass();
      category=(TextView)value(field(nativeCard,"category"),root);
      title=(TextView)value(field(nativeCard,"title"),root);
      now=(TextView)value(field(nativeCard,"now"),root);
      time=(TextView)value(field(nativeCard,"time"),root);
      progress=(ProgressBar)value(field(nativeCard,"progress"),root);
      hero=(View)value(field(nativeCard,"hero"),root);
      mark=(View)value(field(nativeCard,"mark"),root);
      playing=(View)value(field(nativeCard,"playing"),root);
      // The final native fields remain valid; only their Cards hierarchy changes.
      detach(category);detach(title);detach(now);detach(time);detach(progress);
      root.removeAllViews();root.setOrientation(LinearLayout.VERTICAL);root.setPadding(0,0,0,0);
      root.setClipToOutline(true);root.setBackground(surface);
      body=new FrameLayout(a);body.setClipChildren(true);body.setClipToPadding(true);
      root.addView(body,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT));
      fallback=new TextView(a);fallback.setTypeface(NORMAL);fallback.setTextColor(WHITE);fallback.setGravity(Gravity.CENTER);
      fallback.setIncludeFontPadding(false);fallback.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
      logo=new OwnedLogo(a,this);logo.setScaleType(ImageView.ScaleType.FIT_CENTER);
      logo.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
      divider=new View(a);divider.setBackgroundColor(0xff123642);
      live=new TextView(a);live.setText("LIVE");live.setTypeface(NORMAL);live.setTextColor(CYAN);
      live.setGravity(Gravity.CENTER_VERTICAL);live.setIncludeFontPadding(false);
      live.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
      more=new MoreView(a);more.setOnClickListener(this);more.setClickable(true);more.setFocusable(true);
      for(View child:new View[]{fallback,logo,divider,category,title,now,live,time,progress,more})
        body.addView(child,new FrameLayout.LayoutParams(1,1,Gravity.TOP|Gravity.LEFT));
      style(category,NORMAL,MUTED,1);style(title,BOLD,WHITE,1);
      style(now,NORMAL,MUTED,2);style(time,NORMAL,MUTED,1);
      now.setGravity(Gravity.TOP|Gravity.LEFT);
      progress.setPadding(0,0,0,0);progress.setMinimumHeight(0);progress.setIndeterminate(false);
      progress.setProgressTintList(null);progress.setProgressBackgroundTintList(null);progress.setProgressDrawable(progressShape);
      root.addOnLayoutChangeListener(this);root.addOnAttachStateChangeListener(this);
      resize(estimateWidth());
    }
    void style(TextView view,Typeface face,int color,int lines){
      view.setTypeface(face);view.setTextColor(color);view.setIncludeFontPadding(false);
      view.setSingleLine(lines==1);view.setMaxLines(lines);view.setEllipsize(TextUtils.TruncateAt.END);
      view.setGravity(Gravity.TOP|Gravity.LEFT);view.setPadding(0,0,0,0);view.setLineSpacing(0,1.06f);
    }
    void channelFields(Object channel){
      if(channel==null)throw new IllegalArgumentException("Cards channel required");
      if(channelType==channel.getClass())return;
      channelType=channel.getClass();channelName=field(channelType,"name");
      channelGroup=field(channelType,"group");channelIcon=field(channelType,"icon");
      channelArgs=new Class<?>[]{channelType};rowArgs=new Class<?>[]{View.class,channelType};
    }
    void bind(Object channel){
      Activity a=owner.get();if(a==null)return;channelFields(channel);bound=channel;
      CobraArrange.ownedCall(a,"cobraBindRow",rowArgs,card,channel);
      Object actualName=value(channelName,channel);name=actualName==null?"":String.valueOf(actualName);group=string(channelGroup,channel);
      text(title,name);text(category,group.toUpperCase(Locale.getDefault()));
      String initials=actualName==null?"TV":name.trim();int colon=initials.indexOf(':');
      if(colon>=0 && colon+1<initials.length())initials=initials.substring(colon+1).trim();
      text(fallback,initials.substring(0,Math.min(2,initials.length())).toUpperCase(Locale.getDefault()));
      more.setContentDescription(name.isEmpty()?"Channel actions":"Channel actions for "+name);
      String next=string(channelIcon,channel).trim();
      if(!next.equals(logoUrl)){
        CobraLogoRequests.clear(a,logo);logoUrl=next;logo.setImageDrawable(null);
        if(!next.isEmpty())CobraLogoRequests.request(a,next,logo);
      }else if(!next.isEmpty())CobraLogoRequests.request(a,next,logo);
      logoChanged();resize(estimateWidth());metadata(a);
    }
    void refresh(){
      Activity a=owner.get();if(a==null || bound==null || !cards(a))return;
      boolean selected=Boolean.TRUE.equals(CobraArrange.ownedCall(a,"cobraModeSelected",channelArgs,bound));
      if(card.isSelected()!=selected)card.setSelected(selected);
      metadata(a);resize(estimateWidth());
    }
    void metadata(Activity a){
      Object programme=CobraArrange.ownedCall(a,"cobraCurrentProgram",channelArgs,bound);
      String programmeLabel;
      if(programme==null){
        Object status=CobraArrange.ownedCall(a,"cobraGuideStatus",channelArgs,bound);
        programmeLabel=status==null?"":String.valueOf(status);
        hasLive=false;text(time,"");
      }else{
        if(programmeType!=programme.getClass()){
          programmeType=programme.getClass();programmeStart=field(programmeType,"start");
          programmeStop=field(programmeType,"stop");programmeTitle=field(programmeType,"title");
        }
        long first=((Number)value(programmeStart,programme)).longValue();
        long last=((Number)value(programmeStop,programme)).longValue();
        programmeLabel=string(programmeTitle,programme);
        long clock=System.currentTimeMillis();hasLive=first<=clock && clock<last && last>first;
        String locale=Locale.getDefault().toLanguageTag(),zone=TimeZone.getDefault().getID();
        if(first!=start || last!=stop || !locale.equals(dateLocale) || !zone.equals(dateZone)){
          dateLocale=locale;dateZone=zone;date=new SimpleDateFormat("yyyyMMdd",Locale.US);
          String left=String.valueOf(CobraArrange.ownedCall(a,"formatTime",LONG,first));
          String right=String.valueOf(CobraArrange.ownedCall(a,"formatTime",LONG,last));
          String firstDate=date.format(new Date(first)),lastDate=date.format(new Date(last));
          int separator=right.lastIndexOf('•');
          String stopText=firstDate.equals(lastDate) && separator>=0?right.substring(separator+1).trim():right;
          scheduleText=left+" – "+stopText;start=first;stop=last;
        }
        text(time,scheduleText);
        int maximum=progress.getMax();
        int value=hasLive?Math.round(Math.max(0,Math.min(1,(clock-first)/(float)(last-first)))*maximum):0;
        if(progress.getProgress()!=value)progress.setProgress(value);
      }
      text(now,programmeLabel);
      int visibility=hasLive?View.VISIBLE:View.GONE;
      if(live.getVisibility()!=visibility)live.setVisibility(visibility);
      if(time.getVisibility()!=visibility)time.setVisibility(visibility);
      if(progress.getVisibility()!=visibility)progress.setVisibility(visibility);
      String accessible=name+", "+programmeLabel+(card.isSelected()?", selected":"")+", tap to preview, hold for Quick Peek";
      if(!TextUtils.equals(card.getContentDescription(),accessible))card.setContentDescription(accessible);
    }
    void logoChanged(){
      boolean visible=!logoUrl.isEmpty() && logo.getDrawable()!=null;
      int image=visible?View.VISIBLE:View.INVISIBLE,empty=visible?View.GONE:View.VISIBLE;
      if(logo.getVisibility()!=image)logo.setVisibility(image);
      if(fallback.getVisibility()!=empty)fallback.setVisibility(empty);
    }
    int estimateWidth(){
      Activity a=owner.get();if(a==null)return card.getWidth();
      Object list=CobraArrange.ownedField(a,"mCobraGuideList");
      if(list instanceof GridView){
        GridView grid=(GridView)list;if(grid.getColumnWidth()>0)return grid.getColumnWidth();
        int columns=grid.getNumColumns();
        if(columns>0 && grid.getWidth()>0)return Math.max(1,(grid.getWidth()-grid.getPaddingLeft()-grid.getPaddingRight()
          -grid.getHorizontalSpacing()*(columns-1))/columns);
      }
      Object layout=CobraArrange.ownedField(a,"mCobraModeLayout");
      if(layout!=null){
        if(layoutType!=layout.getClass()){layoutType=layout.getClass();layoutColumns=field(layoutType,"columns");layoutBrowser=field(layoutType,"browser");}
        int columns=((Number)value(layoutColumns,layout)).intValue();int[] browser=(int[])value(layoutBrowser,layout);
        int width=Math.round(browser[2]*a.getResources().getDisplayMetrics().density);
        GridView grid=list instanceof GridView?(GridView)list:null;
        if(grid!=null){width-=grid.getPaddingLeft()+grid.getPaddingRight()+grid.getHorizontalSpacing()*Math.max(0,columns-1);}
        if(width>0 && columns>0)return Math.max(1,width/columns);
      }
      return card.getWidth();
    }
    void resize(int width){
      Activity a=owner.get();if(a==null || width<=0 || configuring)return;
      float font=a.getResources().getConfiguration().fontScale;if(!(font>0))font=1;
      float extra=Math.max(0,font-1)*128,refHeight=250+extra;
      int height=Math.max(1,Math.round(refHeight*width/448f));
      ViewGroup.LayoutParams parent=card.getLayoutParams();
      if(parent==null){card.setLayoutParams(new AbsListView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,height));}
      else if(parent.height!=height){parent.height=height;card.setLayoutParams(parent);}
      if(configuredWidth==width && configuredFont==font)return;
      configuring=true;
      try{
        configuredWidth=width;configuredFont=font;scale=width/448f;
        category.setTextSize(TypedValue.COMPLEX_UNIT_PX,17*scale*font);
        title.setTextSize(TypedValue.COMPLEX_UNIT_PX,24*scale*font);
        now.setTextSize(TypedValue.COMPLEX_UNIT_PX,21*scale*font);
        time.setTextSize(TypedValue.COMPLEX_UNIT_PX,19.5f*scale*font);
        fallback.setTextSize(TypedValue.COMPLEX_UNIT_PX,34*scale*font);
        live.setTextSize(TypedValue.COMPLEX_UNIT_PX,20.5f*scale*font);
        liveDot.setBounds(0,0,px(16),px(16));live.setCompoundDrawables(liveDot,null,null,null);live.setCompoundDrawablePadding(px(8));
        float flowFont=Math.max(1,font);
        float titleTop=32+20*flowFont+12,nowTop=titleTop+30*flowFont+14,footer=refHeight-52-26*font;
        place(logo,20,44,122,100);place(fallback,20,44,122,100);place(divider,145,34,1,104);
        place(category,164,32,448-164-80,20*font);
        place(title,164,titleTop,448-164-24,30*font);
        place(now,164,nowTop,448-164-24,52*font);
        float liveWidth=84*font,timeLeft=24+liveWidth+8;
        place(live,24,footer,liveWidth,26*font);place(time,timeLeft,footer+1,Math.max(24,448-timeLeft-24),26*font);
        place(progress,24,refHeight-38,448-48,10);
        // Keep the actual pointer target in the empty header corner. Expanding it
        // by display density would cover the native card-title/program targets.
        FrameLayout.LayoutParams moreParams=(FrameLayout.LayoutParams)more.getLayoutParams();
        moreParams.width=px(56);moreParams.height=px(44);
        moreParams.leftMargin=Math.max(0,width-px(12)-moreParams.width);moreParams.topMargin=px(14);more.setLayoutParams(moreParams);
        more.scale=scale;more.invalidate();
      }finally{configuring=false;}
    }
    int px(float value){return Math.max(1,Math.round(value*scale));}
    void place(View view,float left,float top,float width,float height){
      FrameLayout.LayoutParams params=(FrameLayout.LayoutParams)view.getLayoutParams();
      params.leftMargin=Math.round(left*scale);params.topMargin=Math.round(top*scale);
      params.width=Math.max(1,Math.round(width*scale));params.height=Math.max(1,Math.round(height*scale));view.setLayoutParams(params);
    }
    public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){if(r>l)resize(r-l);}
    public void onViewAttachedToWindow(View v){
      Activity a=owner.get();if(a!=null && cards(a) && bound!=null){refresh();if(!logoUrl.isEmpty())CobraLogoRequests.request(a,logoUrl,logo);}
    }
    public void onViewDetachedFromWindow(View v){}
    public void onClick(View v){
      mainThread();Activity a=owner.get();if(a==null || bound==null || !card.isAttachedToWindow() || !cards(a))return;
      CobraArrange.ownedCall(a,"showCobraChannelActions",channelArgs,bound);
    }
  }

  private static final class OwnedLogo extends ImageView {
    private final Holder holder;
    OwnedLogo(Activity a,Holder holder){super(a);this.holder=holder;}
    @Override public void setImageBitmap(Bitmap bitmap){super.setImageBitmap(bitmap);if(holder!=null)holder.logoChanged();}
    @Override public void setImageDrawable(Drawable drawable){super.setImageDrawable(drawable);if(holder!=null)holder.logoChanged();}
  }
  private static final class MoreView extends View {
    final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);float scale=1;
    MoreView(Activity a){super(a);setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);}
    @Override protected void drawableStateChanged(){super.drawableStateChanged();invalidate();}
    @Override protected void onDraw(Canvas canvas){
      super.onDraw(canvas);paint.setColor(isPressed() || isFocused() || isHovered()?WHITE:0xffaabbd0);
      float x=getWidth()-18*scale;
      for(int i=0;i<3;i++)canvas.drawCircle(x,(14+i*7)*scale,2.2f*scale,paint);
      if(isFocused()){paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(Math.max(1,scale));
        canvas.drawRoundRect(1,1,getWidth()-1,getHeight()-1,10*scale,10*scale,paint);paint.setStyle(Paint.Style.FILL);}
    }
  }
  private static final class CardSurface extends Drawable {
    final Paint fill=new Paint(Paint.ANTI_ALIAS_FLAG),line=new Paint(Paint.ANTI_ALIAS_FLAG),glow=new Paint(Paint.ANTI_ALIAS_FLAG);
    final RectF rect=new RectF();float radius,scale=1;boolean selected,focus,pressed,hover;
    CardSurface(){line.setStyle(Paint.Style.STROKE);glow.setStyle(Paint.Style.STROKE);}
    @Override protected void onBoundsChange(Rect bounds){
      scale=bounds.width()/448f;radius=24*scale;float inset=Math.max(1,scale)*.75f;
      rect.set(bounds.left+inset,bounds.top+inset,bounds.right-inset,bounds.bottom-inset);
      fill.setShader(new LinearGradient(bounds.left,bounds.top,bounds.right,bounds.bottom,
        new int[]{0xff010a0e,0xff01070a,0xff001016},new float[]{0,.55f,1},Shader.TileMode.CLAMP));
    }
    @Override public void draw(Canvas canvas){
      canvas.drawRoundRect(rect,radius,radius,fill);
      if(selected || focus){
        glow.setColor(0x1920d8f7);glow.setStrokeWidth(Math.max(1,10*scale));canvas.drawRoundRect(rect,radius,radius,glow);
        glow.setColor(0x4020d8f7);glow.setStrokeWidth(Math.max(1,6*scale));canvas.drawRoundRect(rect,radius,radius,glow);
      }
      line.setColor(selected || focus?0xff08d5f5:(pressed || hover)?0xff54c5d9:0xff0a657d);
      line.setStrokeWidth(Math.max(1,(selected || focus?3.2f:1.3f)*scale));canvas.drawRoundRect(rect,radius,radius,line);
    }
    @Override public boolean isStateful(){return true;}
    @Override protected boolean onStateChange(int[] states){
      boolean s=false,f=false,p=false,h=false;for(int state:states){s|=state==android.R.attr.state_selected;f|=state==android.R.attr.state_focused;p|=state==android.R.attr.state_pressed;h|=state==android.R.attr.state_hovered;}
      if(selected==s && focus==f && pressed==p && hover==h)return false;selected=s;focus=f;pressed=p;hover=h;invalidateSelf();return true;
    }
    @Override public void getOutline(Outline outline){outline.setRoundRect(getBounds(),radius);}
    @Override public void setAlpha(int alpha){fill.setAlpha(alpha);line.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter colorFilter){}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
  private static final class RoundedProgress extends Drawable {
    final Paint track=new Paint(Paint.ANTI_ALIAS_FLAG),fill=new Paint(Paint.ANTI_ALIAS_FLAG);
    final RectF whole=new RectF(),part=new RectF();float radius;
    RoundedProgress(){track.setColor(0xff2d4051);fill.setColor(0xff29c9ea);}
    @Override protected void onBoundsChange(Rect bounds){whole.set(bounds);part.set(whole);radius=bounds.height()/2f;}
    @Override public void draw(Canvas canvas){
      canvas.drawRoundRect(whole,radius,radius,track);
      if(getLevel()>0){part.right=whole.left+whole.width()*getLevel()/10000f;canvas.drawRoundRect(part,radius,radius,fill);}
    }
    @Override protected boolean onLevelChange(int level){invalidateSelf();return true;}
    @Override public void setAlpha(int alpha){track.setAlpha(alpha);fill.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter colorFilter){}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
  private static final class LiveDot extends Drawable {
    final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    LiveDot(){paint.setColor(CYAN);}
    @Override public void draw(Canvas canvas){Rect r=getBounds();canvas.drawCircle(r.exactCenterX(),r.exactCenterY(),Math.min(r.width(),r.height())*.45f,paint);}
    @Override public void setAlpha(int alpha){paint.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter colorFilter){}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
}
