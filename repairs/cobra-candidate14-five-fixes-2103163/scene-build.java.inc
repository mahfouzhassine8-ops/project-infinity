  static View build(Context context,CobraVisualRenderer renderer,JSONObject scene,Map<String,View> slots,int widthDp) throws Exception {
    if(scene==null||!slots.keySet().equals(CHOOSER_SLOTS))return null;
    final float referenceWidth=scene.getInt("width"),referenceHeight=scene.getInt("height");
    final float density=context.getResources().getDisplayMetrics().density;
    final JSONArray nodes=scene.getJSONArray("nodes");
    float minimum=0f;
    for(int i=0;i<nodes.length();i++){
      JSONObject n=nodes.getJSONObject(i);if(!"slot".equals(n.getString("type")))continue;
      JSONArray r=n.getJSONArray("rect");minimum=Math.max(minimum,Math.max(44f/(float)r.getDouble(2),44f/(float)r.getDouble(3)));
    }
    if(widthDp/referenceWidth<minimum)return null;
    final float minimumScale=minimum;
    final FrameLayout canvas=new FrameLayout(context);canvas.setTag("visual-scene-canvas");
    canvas.setBackgroundColor(android.graphics.Color.parseColor(scene.optString("background","#000000")));
    final ArrayList<View> views=new ArrayList<>();final ArrayList<float[]> rectangles=new ArrayList<>();final ArrayList<Float> textSizes=new ArrayList<>();
    ScrollView scroll=new ScrollView(context){
      @Override protected void onMeasure(int ws,int hs){
        int width=View.MeasureSpec.getSize(ws)-getPaddingLeft()-getPaddingRight();
        if(width<=0)width=Math.round(widthDp*density);
        int height=View.MeasureSpec.getSize(hs)-getPaddingTop()-getPaddingBottom();
        float widthScale=width/(density*referenceWidth),scale=widthScale;
        if(View.MeasureSpec.getMode(hs)!=View.MeasureSpec.UNSPECIFIED&&height>0){
          float fit=Math.min(widthScale,height/(density*referenceHeight));
          // Fit the same artwork and native actions; retain scrolling only when accessibility requires it.
          if(fit>=minimumScale)scale=fit;
        }
        int contentWidth=Math.max(1,Math.round(referenceWidth*scale*density));
        int contentHeight=Math.max(1,Math.round(referenceHeight*scale*density));
        ScrollView.LayoutParams cp=(ScrollView.LayoutParams)canvas.getLayoutParams();cp.width=contentWidth;cp.height=contentHeight;cp.gravity=Gravity.TOP|Gravity.CENTER_HORIZONTAL;
        for(int i=0;i<views.size();i++){
          View child=views.get(i);float[] r=rectangles.get(i);FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)child.getLayoutParams();
          p.width=Math.max(1,Math.round(r[2]*scale*density));p.height=Math.max(1,Math.round(r[3]*scale*density));p.leftMargin=Math.round(r[0]*scale*density);p.topMargin=Math.round(r[1]*scale*density);
          if(child instanceof TextView){float base=textSizes.get(i),ratio=scale/widthScale;float minSp=child.isClickable()?14:12;float desired=Math.max(Math.min(base,minSp*getResources().getDisplayMetrics().scaledDensity),base*ratio);TextView text=(TextView)child;if(Math.abs(text.getTextSize()-desired)>.1f)text.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,desired);}
        }
        super.onMeasure(ws,hs);
      }
    };
    scroll.setFillViewport(true);scroll.setTag("visual-scene:chooser");
    scroll.addView(canvas,new ScrollView.LayoutParams(-1,Math.round(referenceHeight*widthDp/referenceWidth*density)));
    for(String pass:new String[]{"decoration","slot"})for(int i=0;i<nodes.length();i++){
      JSONObject n=nodes.getJSONObject(i);String type=n.getString("type");if(type.equals("slot")!=pass.equals("slot"))continue;
      View v;
      if(type.equals("slot")){
        v=slots.get(n.getString("slot"));if(v.getParent()!=null)throw new IOException("Native action slot already attached");
        if(n.has("label")&&v instanceof TextView){((TextView)v).setText(n.getString("label"));v.setContentDescription(n.getString("label"));}
      }else if(type.equals("text")){
        TextView t=new TextView(context);t.setText(n.getString("label"));t.setTextColor(android.graphics.Color.WHITE);t.setTextSize(14);
        String align=n.optString("align","center");t.setGravity(Gravity.CENTER_VERTICAL|(align.equals("left")?Gravity.LEFT:align.equals("right")?Gravity.RIGHT:Gravity.CENTER_HORIZONTAL));t.setIncludeFontPadding(false);v=t;
      }else{
        final String asset=n.getString("asset"),fit=n.optString("fit","contain");
        v=new View(context){@Override protected void onDraw(Canvas c){CobraVisualRenderer.drawBitmap(c,CobraVisualRenderer.active.bitmaps.get(asset),new android.graphics.RectF(0,0,getWidth(),getHeight()),fit,255);}};
        v.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);v.setClickable(false);v.setFocusable(false);
      }
      if(!type.equals("slot"))v.setTag("visual-node:"+n.getString("id"));
      if(n.has("asset")&&!type.equals("image")){
        JSONObject style=n.has("style")?new JSONObject(n.getJSONObject("style").toString()):new JSONObject();style.put("image",n.getString("asset"));style.put("image_fit",n.optString("fit","contain"));renderer.inline(v,"chooser.node."+n.getString("id"),style);
      }else if(n.has("style"))renderer.inline(v,"chooser.node."+n.getString("id"),n.getJSONObject("style"));else renderer.paint(v,"chooser.node."+n.getString("id"));
      JSONArray r=n.getJSONArray("rect");float scale=widthDp/referenceWidth;
      float[] rect={(float)r.getDouble(0),(float)r.getDouble(1),(float)r.getDouble(2),(float)r.getDouble(3)};
      FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.round(rect[2]*scale*density),Math.round(rect[3]*scale*density));p.leftMargin=Math.round(rect[0]*scale*density);p.topMargin=Math.round(rect[1]*scale*density);canvas.addView(v,p);
      views.add(v);rectangles.add(rect);textSizes.add(v instanceof TextView?((TextView)v).getTextSize():0f);
    }
    return scroll;
  }
