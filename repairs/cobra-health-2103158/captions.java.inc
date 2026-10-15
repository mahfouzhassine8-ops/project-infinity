  /** App-owned caption presentation; Media3 retains decoding and track selection ownership. */
  private final class CobraCaptionOverlay extends View {
    java.util.List<androidx.media3.common.text.Cue> cues=Collections.emptyList();
    final android.text.TextPaint text=new android.text.TextPaint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    final android.graphics.Paint background=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    CobraCaptionOverlay(){super(InfinityLiveActivity.this);setFocusable(false);setClickable(false);setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);setWillNotDraw(false);}
    void cues(java.util.List<androidx.media3.common.text.Cue> values){
      ArrayList<androidx.media3.common.text.Cue> copy=new ArrayList<>();for(androidx.media3.common.text.Cue cue:values){if(copy.size()>=16)break;if(cue==null||(cue.text!=null&&cue.text.length()>32768))continue;copy.add(cue);}cues=copy;setVisibility(copy.isEmpty()?View.GONE:View.VISIBLE);invalidate();
    }
    @Override protected void onDraw(android.graphics.Canvas canvas){
      int w=getWidth(),h=getHeight();if(w<=0||h<=0)return;int save=canvas.save();canvas.clipRect(0,0,w,h);
      for(androidx.media3.common.text.Cue cue:cues){
        float pos=cue.position==androidx.media3.common.text.Cue.DIMEN_UNSET?.5f:Math.max(0,Math.min(1,cue.position));
        int anchor=cue.positionAnchor==androidx.media3.common.text.Cue.TYPE_UNSET?1:cue.positionAnchor;
        int lineAnchor=cue.lineAnchor==androidx.media3.common.text.Cue.TYPE_UNSET?2:cue.lineAnchor;
        float fraction=cue.size==androidx.media3.common.text.Cue.DIMEN_UNSET?.9f:Math.max(.05f,Math.min(1,cue.size));
        int width=Math.max(1,Math.round(w*fraction)),height;android.text.StaticLayout layout=null;
        if(cue.bitmap!=null){height=cue.bitmapHeight==androidx.media3.common.text.Cue.DIMEN_UNSET?Math.max(1,Math.round(width*cue.bitmap.getHeight()/(float)Math.max(1,cue.bitmap.getWidth()))):Math.max(1,Math.round(h*cue.bitmapHeight));}
        else if(cue.text!=null){
          float size=Math.max(dp(12),Math.min(dp(24),h*.045f))*getResources().getConfiguration().fontScale;
          text.setTextSize(size);text.setColor(Color.WHITE);text.setTypeface(Typeface.create("sans-serif-medium",0));text.setShadowLayer(dp(2),0,dp(1),Color.BLACK);
          layout=new android.text.StaticLayout(cue.text,text,width,cue.textAlignment==null?android.text.Layout.Alignment.ALIGN_CENTER:cue.textAlignment,1.08f,0,false);height=layout.getHeight();
        }else continue;
        float y=h-dp(12)-height;
        if(cue.line!=androidx.media3.common.text.Cue.DIMEN_UNSET){
          if(cue.lineType==androidx.media3.common.text.Cue.LINE_TYPE_FRACTION)y=h*cue.line-(lineAnchor==2?height:lineAnchor==1?height/2f:0);
          else y=cue.line>=0?cue.line*(layout==null?dp(18):layout.getLineBottom(0)):h+(cue.line+1)*(layout==null?dp(18):layout.getLineBottom(0))-height-dp(12);
        }
        float x=w*pos-(anchor==2?width:anchor==1?width/2f:0);x=Math.max(0,Math.min(w-width,x));y=Math.max(0,Math.min(h-height,y));
        if(cue.bitmap!=null){canvas.drawBitmap(cue.bitmap,null,new android.graphics.RectF(x,y,x+width,y+height),null);}
        else if(layout!=null){background.setColor(cue.windowColorSet?cue.windowColor:0x99000000);canvas.drawRoundRect(x,y,x+width,y+height,dp(3),dp(3),background);int content=canvas.save();canvas.translate(x,y);layout.draw(canvas);canvas.restoreToCount(content);}
      }
      canvas.restoreToCount(save);
    }
  }
  private void cobraAttachCaptions(CobraPlayerBinding binding,TextureView texture){
    if(binding.captions==null)binding.captions=new CobraCaptionOverlay();
    android.view.ViewParent old=binding.captions.getParent();if(old instanceof android.view.ViewGroup)((android.view.ViewGroup)old).removeView(binding.captions);
    if(texture.getParent() instanceof FrameLayout){FrameLayout parent=(FrameLayout)texture.getParent();parent.addView(binding.captions,parent.indexOfChild(texture)+1,new FrameLayout.LayoutParams(-1,-1));}
  }
