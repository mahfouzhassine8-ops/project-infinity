package com.projectinfinity.kodi;

import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.view.View;
import android.widget.Button;
import android.widget.SeekBar;

/** Preview presentation only. No engine, persistence, provider or global theme access. */
public final class InfinityPreviewChrome {
    public final boolean light;
    public final int ink, secondary, accent, track;
    private final float density;
    private final float scaledDensity;
    private static Typeface cachedFont;
    public final Typeface font;

    public InfinityPreviewChrome(Context context, boolean light) {
        this.light = light; density = context.getResources().getDisplayMetrics().density; scaledDensity=context.getResources().getDisplayMetrics().scaledDensity;
        ink = light ? 0xff142c34 : 0xffeff7f8;
        secondary = light ? 0xff425b62 : 0xffc1ced1;
        accent = light ? 0xff007f8b : 0xff2ed9df;
        track = light ? 0xffbcced2 : 0xff35474d;
        if(cachedFont==null){
            try { cachedFont=Typeface.createFromAsset(context.getAssets(), "addons/skin.infinity.diggz/fonts/Roboto-Regular.ttf"); }
            catch (RuntimeException unavailable) { cachedFont=Typeface.create("sans-serif",Typeface.NORMAL); }
        }
        font = cachedFont;
    }
    public int dp(float value) { return Math.round(value * density); }
    public float sp(float value) { return value*scaledDensity; }
    public Drawable glass(float radius, boolean frame) { return new Glass(this, dp(radius), frame); }
    public Drawable backdrop() { return new Backdrop(this); }
    public Drawable thumb() { return new Thumb(this); }
    public void seek(SeekBar bar) {
        bar.setProgressTintList(android.content.res.ColorStateList.valueOf(accent));
        bar.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(track));
        bar.setSecondaryProgressTintList(android.content.res.ColorStateList.valueOf(track));
        bar.setThumb(thumb()); bar.setSplitTrack(false);
    }

    private static final class Glass extends Drawable {
        final InfinityPreviewChrome c; final float radius; final boolean frame;
        final Paint p = new Paint(3); final RectF r = new RectF();
        Glass(InfinityPreviewChrome c, float radius, boolean frame) { this.c=c;this.radius=radius;this.frame=frame; }
        public void draw(Canvas canvas) {
            r.set(getBounds()); float inset=Math.max(1,c.density*.5f); r.inset(inset,inset);
            if (!frame) {
                p.setStyle(Paint.Style.FILL);
                p.setShader(new LinearGradient(0,r.top,0,r.bottom,c.light?0xfaf6fbfc:0xed10272c,c.light?0xf2e8f1f3:0xe6041015,Shader.TileMode.CLAMP));
                canvas.drawRoundRect(r,radius,radius,p);p.setShader(null);
            }
            p.setStyle(Paint.Style.STROKE);
            if(!c.light){
                p.setColor(0x0700dce8);
                for(int glow=5;glow>=1;glow--){p.setStrokeWidth(c.dp(glow*1.4f));canvas.drawRoundRect(r,radius,radius,p);}
            }
            p.setStrokeWidth(Math.max(1,c.density*.55f));
            p.setShader(new LinearGradient(r.left,r.top,r.right,r.bottom,
                    new int[]{c.light?0xff8dbbc2:frame?0xff6bddd9:0xff407379,c.light?0x60617e83:frame?0xa0337981:0x35295258,c.light?0xff60a1aa:0xc040c5ca},null,Shader.TileMode.CLAMP));
            canvas.drawRoundRect(r,radius,radius,p);p.setShader(null);
        }
        @Override public void getOutline(Outline outline) { outline.setRoundRect(getBounds(),radius); }
        public void setAlpha(int a) {} public void setColorFilter(ColorFilter f) {} public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
    private static final class Backdrop extends Drawable {
        final InfinityPreviewChrome c; final Paint p=new Paint(3); final Path curve=new Path();
        Backdrop(InfinityPreviewChrome c){this.c=c;}
        public void draw(Canvas canvas) {
            Rect b=getBounds();float w=b.width(),h=b.height();
            p.setShader(new LinearGradient(0,0,w,h,c.light?0xffedf5f7:0xff001216,c.light?0xfff8fafb:0xff00070b,Shader.TileMode.CLAMP));
            canvas.drawRect(b,p);p.setShader(null);
            // Static, feathered contours; no timer, decoding or bitmap allocation.
            curve.reset();curve.moveTo(w*.30f,h*.16f);curve.cubicTo(w*.82f,h*.16f,w*.64f,-h*.04f,w*1.09f,-h*.035f);
            contour(canvas,w*.55f,h*.16f,w*.92f,0,.72f);
            curve.reset();curve.moveTo(-w*.05f,h*.86f);curve.cubicTo(w*.30f,h*.82f,w*.34f,h*.68f,w*.63f,h*.78f);
            contour(canvas,0,h*.86f,w*.55f,h*.75f,.35f);
            p.setStyle(Paint.Style.FILL);
        }
        private void contour(Canvas canvas,float x1,float y1,float x2,float y2,float strength){
            p.setStyle(Paint.Style.STROKE);p.setStrokeCap(Paint.Cap.ROUND);
            for(int i=12;i>=1;i--){
                int alpha=Math.round((i==1?96:5)*strength);
                int rgb=c.light?0x005fa1ad:0x000da6ba;
                p.setShader(new LinearGradient(x1,y1,x2,y2,new int[]{rgb,(alpha<<24)|rgb,(alpha/2<<24)|rgb,rgb},new float[]{0,.55f,.8f,1},Shader.TileMode.CLAMP));
                p.setStrokeWidth(c.dp(i==1?.5f:i*3f));canvas.drawPath(curve,p);
            }
            p.setShader(null);
        }
        public void setAlpha(int a){} public void setColorFilter(ColorFilter f){} public int getOpacity(){return PixelFormat.OPAQUE;}
    }
    private static final class Thumb extends Drawable {
        final InfinityPreviewChrome c;final Paint p=new Paint(3);
        Thumb(InfinityPreviewChrome c){this.c=c;}
        public int getIntrinsicWidth(){return c.dp(22);} public int getIntrinsicHeight(){return c.dp(22);}
        public void draw(Canvas canvas){Rect b=getBounds();float x=b.exactCenterX(),y=b.exactCenterY();
            p.setColor(c.accent);p.setAlpha(30);canvas.drawCircle(x,y,c.dp(9),p);
            p.setAlpha(75);canvas.drawCircle(x,y,c.dp(7),p);p.setAlpha(255);canvas.drawCircle(x,y,c.dp(5),p);
            p.setColor(c.light?0xfff9ffff:0xffdfffff);canvas.drawCircle(x,y,c.dp(3.5f),p);
        }
        public void setAlpha(int a){}public void setColorFilter(ColorFilter f){}public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
    public static final class Brand extends View {
        InfinityPreviewChrome c;final Paint p=new Paint(3);final Path path=new Path();
        public Brand(Context context,InfinityPreviewChrome c){super(context);this.c=c;setContentDescription("Infinity Preview");}
        public void theme(InfinityPreviewChrome c){this.c=c;invalidate();}
        protected void onDraw(Canvas canvas){
            float mid=getHeight()/2f, left=c.dp(5),cx=left+c.dp(11),rx=c.dp(10),ry=c.dp(3.5f);
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(c.dp(1.2f));p.setColor(c.accent);
            path.reset();path.moveTo(cx-rx,mid);path.cubicTo(cx-rx,mid-ry*2,cx-rx*.4f,mid-ry*2,cx,mid);
            path.cubicTo(cx+rx*.6f,mid+ry*2,cx+rx,mid+ry*2,cx+rx,mid);
            path.cubicTo(cx+rx,mid-ry*2,cx+rx*.4f,mid-ry*2,cx,mid);
            path.cubicTo(cx-rx*.6f,mid+ry*2,cx-rx,mid+ry*2,cx-rx,mid);canvas.drawPath(path,p);
            p.setStyle(Paint.Style.FILL);p.setColor(c.ink);p.setTypeface(c.font);p.setTextSize(c.sp(9.5f));
            if(getWidth()>c.dp(90))canvas.drawText("Infinity Preview",left+c.dp(29),mid+c.dp(3.4f),p);
        }
    }
    /** Native Button semantics and original action/text; only drawing changes. */
    public static final class Control extends Button {
        InfinityPreviewChrome c;final Paint p=new Paint(3);final Path path=new Path();
        public Control(Context context,InfinityPreviewChrome c){super(context);theme(c);setMinWidth(0);setMinHeight(0);setMinimumWidth(0);setMinimumHeight(0);setPadding(0,0,0,0);setBackgroundColor(Color.TRANSPARENT);}
        public void theme(InfinityPreviewChrome value){c=value;setTypeface(c.font);setTextColor(c.ink);invalidate();}
        @Override protected void drawableStateChanged(){super.drawableStateChanged();invalidate();}
        protected void onDraw(Canvas canvas){
            String action=getText().toString();boolean transport=action.equals("Pause")||action.equals("Play");
            boolean close=action.equals("Close");float w=getWidth(),h=getHeight(),d=c.density;
            float size=Math.min(c.dp(42),Math.min(w,h)-c.dp(4)),x=w/2,y=h/2;
            float alpha=isEnabled()?1f:.42f;
            canvas.saveLayerAlpha(0,0,w,h,(int)(255*alpha));
            p.setStyle(Paint.Style.FILL);p.setShader(null);
            if(transport){
                p.setColor(c.accent);p.setAlpha(18);canvas.drawCircle(x,y,size*.58f,p);p.setAlpha(32);canvas.drawCircle(x,y,size*.53f,p);
                p.setAlpha(255);p.setColor(c.light?0xffe0f5f6:0xff06313b);canvas.drawCircle(x,y,size*.46f,p);
                p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(d);p.setColor(c.accent);canvas.drawCircle(x,y,size*.46f,p);
            }else{
                float bw=close?w-c.dp(4):size, bh=close?c.dp(27):size*.94f;
                RectF b=new RectF(x-bw/2,y-bh/2,x+bw/2,y+bh/2);
                p.setShader(new LinearGradient(0,b.top,0,b.bottom,c.light?0xfafcffff:0xd01c353b,c.light?0xe6e3eef0:0xb007161d,Shader.TileMode.CLAMP));
                canvas.drawRoundRect(b,c.dp(close?12:10),c.dp(close?12:10),p);p.setShader(null);
                p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(Math.max(1,d*.5f));p.setColor(close?c.accent:c.light?0xffa1bdc3:0xff365057);canvas.drawRoundRect(b,c.dp(close?12:10),c.dp(close?12:10),p);
            }
            if(isSelected()){
                p.setStyle(Paint.Style.FILL);p.setColor(c.accent);p.setAlpha(c.light?30:40);
                canvas.drawRoundRect(new RectF(d,d,w-d,h-d),c.dp(12),c.dp(12),p);p.setAlpha(255);
            }
            if(isSelected()||isPressed()||isFocused()){
                p.setStyle(Paint.Style.STROKE);p.setColor(c.accent);p.setStrokeWidth(d*1.5f);
                canvas.drawRoundRect(new RectF(d,d,w-d,h-d),c.dp(12),c.dp(12),p);
            }
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(d*1.2f);p.setStrokeCap(Paint.Cap.ROUND);p.setStrokeJoin(Paint.Join.ROUND);p.setColor(isSelected()?c.accent:c.ink);
            boolean caption=action.equals("Audio")||action.equals("Subtitles")||action.equals("Display")||action.equals("Fullscreen")||action.equals("Exit fullscreen")||action.contains("10")||action.contains("rotate")||action.contains("locked")||action.equals("Volume");
            float iy=caption?y-c.dp(7):y;
            canvas.save();canvas.translate(x,iy);canvas.scale(d,d);
            p.setStrokeWidth(1.2f);
            if(close){path.reset();path.moveTo(-12,-5);path.lineTo(-17,0);path.lineTo(-12,5);canvas.drawPath(path,p);}
            else if(action.equals("Pause")){p.setStyle(Paint.Style.FILL);canvas.drawRoundRect(new RectF(-6,-7,-2,7),1,1,p);canvas.drawRoundRect(new RectF(2,-7,6,7),1,1,p);}
            else if(action.equals("Play")){path.reset();path.moveTo(-4,-8);path.lineTo(8,0);path.lineTo(-4,8);path.close();p.setStyle(Paint.Style.FILL);canvas.drawPath(path,p);}
            else if(action.equals("Stop")){p.setStyle(Paint.Style.FILL);canvas.drawRoundRect(new RectF(-5,-5,5,5),1,1,p);}
            else if(action.contains("10")){
                canvas.save();if(action.startsWith("−"))canvas.scale(-1,1);
                path.reset();path.moveTo(-6,3);path.cubicTo(-10,-7,4,-11,7,-3);canvas.drawPath(path,p);
                path.reset();path.moveTo(3,-4);path.lineTo(7,-3);path.lineTo(8,-7);canvas.drawPath(path,p);canvas.restore();
            }
            else if(action.contains("rotate")||action.contains("locked")){
                boolean back=action.startsWith("−");canvas.drawArc(new RectF(-6,-6,6,6),back?205:335,285,false,p);
                path.reset();if(back){path.moveTo(-8,-4);path.lineTo(-7,1);path.lineTo(-2,-1);}else{path.moveTo(8,-4);path.lineTo(7,1);path.lineTo(2,-1);}canvas.drawPath(path,p);
            }else if(action.equals("Mute")||action.equals("Unmute")){
                path.reset();path.moveTo(-8,-3);path.lineTo(-4,-3);path.lineTo(1,-7);path.lineTo(1,7);path.lineTo(-4,3);path.lineTo(-8,3);path.close();canvas.drawPath(path,p);
                if(action.equals("Unmute")){canvas.drawLine(5,-3,10,3,p);canvas.drawLine(5,3,10,-3,p);}else{canvas.drawArc(new RectF(0,-7,11,7),-65,130,false,p);}
            }else if(action.equals("Audio")){canvas.drawArc(new RectF(-7,-7,7,8),180,180,false,p);canvas.drawRoundRect(new RectF(-8,0,-4,7),1,1,p);canvas.drawRoundRect(new RectF(4,0,8,7),1,1,p);}
            else if(action.equals("Subtitles")){canvas.drawRoundRect(new RectF(-8,-6,8,6),2,2,p);p.setStyle(Paint.Style.FILL);p.setTypeface(c.font);p.setTextSize(7);p.setTextAlign(Paint.Align.CENTER);canvas.drawText("CC",0,2.5f,p);}
            else if(action.equals("Display")){canvas.drawRoundRect(new RectF(-8,-6,8,4),1,1,p);canvas.drawLine(0,4,0,7,p);canvas.drawLine(-4,7,4,7,p);}
            else if(action.equals("Fullscreen")||action.equals("Exit fullscreen")){
                float outer=8,inner=3;
                for(int sx:new int[]{-1,1})for(int sy:new int[]{-1,1}){
                    path.reset();if(action.equals("Fullscreen")){path.moveTo(sx*inner,sy*6);path.lineTo(sx*outer,sy*6);path.lineTo(sx*outer,sy*2);}
                    else{path.moveTo(sx*outer,sy*2);path.lineTo(sx*inner,sy*2);path.lineTo(sx*inner,sy*6);}canvas.drawPath(path,p);
                }
            }
            else if(action.equals("Volume")){canvas.drawLine(-7,5,-7,0,p);canvas.drawLine(-2,5,-2,-4,p);canvas.drawLine(3,5,3,-7,p);canvas.drawLine(8,5,8,-2,p);}
            canvas.restore();p.setStyle(Paint.Style.FILL);p.setTypeface(c.font);p.setTextAlign(Paint.Align.CENTER);p.setColor(isSelected()?c.accent:c.ink);
            if(close){p.setTextSize(c.sp(11));canvas.drawText("Close",x+c.dp(4),y+c.dp(4),p);}
            else if(caption){String label=action.contains("locked")?"Locked":action.startsWith("−")?"−10s":action.startsWith("+")?"+10s":action;p.setTextSize(c.sp(8));canvas.drawText(label,x,y+c.dp(14),p);}
            else if(action.equals("Retry")){p.setTextSize(c.sp(11));canvas.drawText(action,x,y+c.dp(4),p);}
            canvas.restore();
        }
    }
}
