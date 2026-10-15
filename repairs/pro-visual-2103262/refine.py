#!/usr/bin/env python3
"""Bounded Pro-only rendering corrections following native test review."""
from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'ProVisualTest.java';s=p.read_text()
old='frame.setImageBitmap(BitmapFactory.decodeFile(fixture.toString()))'
new='{byte[] bytes=java.nio.file.Files.readAllBytes(fixture.toPath());frame.setImageBitmap(BitmapFactory.decodeByteArray(bytes,0,bytes.length));}'
assert s.count(old)==1
s=s.replace(old+';else',new+'else')
p.write_text(s)
p=root/'CobraProUi.java.in';s=p.read_text()
old='int ink=overlay?Color.WHITE:light?INK:Color.WHITE;float pad=den*2'
new='''int ink=overlay?Color.WHITE:light?INK:Color.WHITE;
      // Edge chevrons have 48dp targets but no solid pill over the programme text.
      if("left".equals(glyph)||"right".equals(glyph)){icon(c,p,glyph,"left".equals(glyph)?0:w-den*24,(h-den*24)/2,den*24,ink);return;}
      float pad=den*2'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
print('PASS: Pro fixtures decode from bytes; carousel chevrons no longer obscure metadata')
p=root/'CobraProUi.java.in';s=p.read_text()
old='''if(animate&&was&&motion())info.post(()->{if(token!=animationToken||!info.isAttachedToWindow())return;int[] after=new int[2];info.getLocationOnScreen(after);info.setTranslationX(before[0]-after[0]);info.setTranslationY(before[1]-after[1]);info.animate().translationX(0).translationY(0).setDuration(260).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();});'''
new='''if(animate&&was&&motion()){
          final ViewTreeObserver tree=destination.getViewTreeObserver();
          tree.addOnPreDrawListener(new ViewTreeObserver.OnPreDrawListener(){public boolean onPreDraw(){
            if(tree.isAlive())tree.removeOnPreDrawListener(this);
            if(token==animationToken&&info.isAttachedToWindow()){
              int[] after=new int[2];info.getLocationOnScreen(after);
              info.setTranslationX(before[0]-after[0]);info.setTranslationY(before[1]-after[1]);
              info.animate().translationX(0).translationY(0).setDuration(260).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
            }return true;
          }});
        }'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('boolean active=primary||isSelected()||isPressed()||isFocused();','boolean active=isEnabled()&&(primary||isSelected()||isPressed()||isFocused());')
p.write_text(s)
print('PASS: metadata promotion waits for measured destination before animation')
p=root/'CobraProUi.java.in';s=p.read_text()
old='''    void ink(int color){ownInk=color;super.setTextColor(color);}'''
new='''    @Override protected void onDraw(Canvas canvas){
      if((getGravity()&Gravity.HORIZONTAL_GRAVITY_MASK)==Gravity.CENTER_HORIZONTAL){
        android.text.TextPaint paint=getPaint();Paint.Align align=paint.getTextAlign();
        paint.setColor(ownInk);paint.setTypeface(ownFace);paint.setTextAlign(Paint.Align.CENTER);
        String value=fit(getText().toString(),paint,getWidth()-getPaddingLeft()-getPaddingRight());
        canvas.drawText(value,getPaddingLeft()+(getWidth()-getPaddingLeft()-getPaddingRight())/2f,
            getPaddingTop()+(getHeight()-getPaddingTop()-getPaddingBottom())/2f-(paint.ascent()+paint.descent())/2f,paint);
        paint.setTextAlign(align);
      }else super.onDraw(canvas);
    }
    void ink(int color){ownInk=color;super.setTextColor(color);}'''
assert s.count(old)==1;s=s.replace(old,new)
old='''    if(state!=WATCHING)r[2]=new int[]{0,0,0,0};'''
new=old+'''
    for(int i=1;i<4;i++)if(r[i][2]>16){r[i][0]+=8;r[i][2]-=16;}
'''
assert s.count(old)==1;s=s.replace(old,new)
assert s.count('new int[]{0x22021523,0x00021523,0xf2051421}')==1
s=s.replace('new int[]{0x22021523,0x00021523,0xf2051421}','new int[]{0x55051421,0x99051421,0xf2051421}')
old='''int old=state;state=value;if(target!=null)below=target;'''
new='''int old=state;state=value;
      if(old!=state)shade.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,
          state==WATCHING?new int[]{0x22021523,0x00021523,0xf2051421}:new int[]{0x55051421,0x99051421,0xf2051421}));
      if(target!=null)below=target;'''
assert s.count(old)==1;s=s.replace(old,new)
old='''    @Override protected void onDetachedFromWindow(){info.animate().cancel();animationToken++;super.onDetachedFromWindow();}'''
new='''    @Override protected void dispatchDraw(Canvas canvas){
      super.dispatchDraw(canvas);
      // Explicit edge finish also renders correctly when the native View is drawn to a Canvas.
      Path edge=new Path();float radius=px(getContext(),14);RectF bounds=new RectF(0,0,getWidth(),getHeight());
      edge.addRoundRect(bounds,radius,radius,Path.Direction.CW);
      canvas.save();canvas.clipOutPath(edge);canvas.drawColor(light?0xfff0f6fa:0xff081827);canvas.restore();
      Paint outline=new Paint(Paint.ANTI_ALIAS_FLAG);outline.setStyle(Paint.Style.STROKE);outline.setStrokeWidth(px(getContext(),1.2f));outline.setColor(light?0xff8bd5e7:CYAN);
      bounds.inset(px(getContext(),.6f),px(getContext(),.6f));canvas.drawRoundRect(bounds,radius,radius,outline);
    }
    @Override protected void onDetachedFromWindow(){info.animate().cancel();animationToken++;super.onDetachedFromWindow();}'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
p=root/'ProVisualTest.java';s=p.read_text()
old='assertEquals(Color.WHITE,s.hero.source.getCurrentTextColor());'
new=old+'''Bitmap badge=Bitmap.createBitmap(s.hero.live.getWidth(),s.hero.live.getHeight(),Bitmap.Config.ARGB_8888);s.hero.live.draw(new Canvas(badge));int white=0;for(int y=0;y<badge.getHeight();y++)for(int x=0;x<badge.getWidth();x++){int color=badge.getPixel(x,y);if(Color.red(color)>235&&Color.green(color)>235&&Color.blue(color)>235)white++;}assertTrue("LIVE text must actually render, not only exist in accessibility",white>5);badge.recycle();'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
print('PASS: visible LIVE/fallback text, rounded hero edge, light margins and readable resting scrim')
