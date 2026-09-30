  /** Phone presentation only: bounded state animation, fixed geometry, no video sampling. */
  static Drawable phoneGlass(Context c, boolean light, float radius, boolean raised) {
    return new Glass(c,light,radius,raised);
  }
  static final class Glass extends Drawable {
    final boolean light,raised; final float density,radius;
    final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);final RectF rect=new RectF();
    final Path clip=new Path();android.animation.ValueAnimator animator;
    float emphasis;boolean active,enabled=true;int opacity=255;ColorFilter filter;
    Glass(Context c,boolean l,float r,boolean elevated){light=l;raised=elevated;density=c.getResources().getDisplayMetrics().density;radius=r*density;}
    @Override public boolean isStateful(){return true;}
    @Override protected boolean onStateChange(int[] state){
      boolean next=false,on=false;for(int value:state){on|=value==android.R.attr.state_enabled;next|=value==android.R.attr.state_selected||value==android.R.attr.state_focused||value==android.R.attr.state_pressed;}
      next&=on;enabled=on;if(next==active){invalidateSelf();return true;}active=next;
      if(animator!=null){animator.cancel();animator=null;}
      float target=next?1:0;
      if(getCallback()==null||!isVisible()||(Build.VERSION.SDK_INT>=26&&!android.animation.ValueAnimator.areAnimatorsEnabled())){emphasis=target;invalidateSelf();return true;}
      animator=android.animation.ValueAnimator.ofFloat(emphasis,target);animator.setDuration(next?170:130);
      animator.setInterpolator(new android.view.animation.PathInterpolator(.2f,0f,0f,1f));
      animator.addUpdateListener(a->{emphasis=(Float)a.getAnimatedValue();invalidateSelf();});animator.start();return true;
    }
    @Override public boolean setVisible(boolean visible,boolean restart){if(!visible&&animator!=null){animator.cancel();animator=null;emphasis=active?1:0;}return super.setVisible(visible,restart);}
    @Override public void jumpToCurrentState(){if(animator!=null){animator.cancel();animator=null;}emphasis=active?1:0;invalidateSelf();}
    int blend(int a,int b,float t){return Color.argb(Math.round(Color.alpha(a)+(Color.alpha(b)-Color.alpha(a))*t),Math.round(Color.red(a)+(Color.red(b)-Color.red(a))*t),Math.round(Color.green(a)+(Color.green(b)-Color.green(a))*t),Math.round(Color.blue(a)+(Color.blue(b)-Color.blue(a))*t));}
    @Override public void draw(Canvas canvas){
      Rect bounds=getBounds();if(bounds.isEmpty())return;rect.set(bounds);rect.inset(density*.6f,density*.6f);float r=Math.min(radius,Math.min(rect.width(),rect.height())/2);
      paint.setColorFilter(filter);paint.setStyle(Paint.Style.FILL);paint.setAlpha(Math.round(opacity*(enabled?1f:.55f)));
      int top=light?(raised?0xfaffffff:0xeaf9fdff):(raised?0xf01c303b:0xd816252e),bottom=light?(raised?0xf1eaf3fa:0xdfe8f2f8):(raised?0xf006121a:0xc9061016);
      top=blend(top,light?0xffecfbff:0xf5245262,emphasis);bottom=blend(bottom,light?0xffd7f2fc:0xf30a2834,emphasis);
      paint.setShader(new LinearGradient(0,rect.top,0,rect.bottom,new int[]{top,bottom},null,Shader.TileMode.CLAMP));canvas.drawRoundRect(rect,r,r,paint);
      clip.reset();clip.addRoundRect(rect,r,r,Path.Direction.CW);int save=canvas.save();canvas.clipPath(clip);
      // A broad diagonal reflection and a top lip give depth without obscuring content.
      paint.setShader(new LinearGradient(rect.left,rect.top,rect.right*.7f,rect.bottom,new int[]{light?0x70ffffff:0x30d9f6ff,Color.TRANSPARENT,light?0x16ffffff:0x080cb9e2},new float[]{0,.42f,1},Shader.TileMode.CLAMP));canvas.drawRect(rect,paint);
      canvas.restoreToCount(save);paint.setShader(null);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(density*(.8f+emphasis*.7f));
      paint.setColor(blend(light?0xffb7d4e3:0xff3f6374,light?0xff087b9c:0xff28d1f0,emphasis));paint.setAlpha(opacity);canvas.drawRoundRect(rect,r,r,paint);
      paint.setShader(new LinearGradient(rect.left,rect.top,rect.right,rect.bottom,new int[]{light?0xb0ffffff:0x85d5f6ff,Color.TRANSPARENT},null,Shader.TileMode.CLAMP));paint.setStrokeWidth(density*.7f);RectF lip=new RectF(rect);lip.inset(density,density);canvas.drawRoundRect(lip,Math.max(0,r-density),Math.max(0,r-density),paint);paint.setShader(null);
    }
    @Override public void setAlpha(int value){opacity=value;invalidateSelf();}
    @Override public void setColorFilter(ColorFilter value){filter=value;invalidateSelf();}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    @Override public boolean getPadding(Rect out){out.set(0,0,0,0);return false;}
  }
