  private View cobraVodCard(VodItem item,boolean progress) {
    LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setFocusable(true);card.setClickable(true);card.setPadding(0,0,0,dp(4));card.setContentDescription(item.title+", "+item.category);
    android.widget.ImageView poster=new android.widget.ImageView(this);poster.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);poster.setBackground(surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));
    card.addView(poster,new LinearLayout.LayoutParams(-1,dp(isCompact()?174:202)));cobraLoadVodArtwork(poster,item.icon);
    TextView name=text(item.title,cobraModeColor("text"),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);name.setMaxLines(2);name.setEllipsize(android.text.TextUtils.TruncateAt.END);card.addView(name,new LinearLayout.LayoutParams(-1,dp(46)));
    if(progress){int pct=cobraVodProgressPercent(item);if(pct>0){android.widget.ProgressBar bar=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(100);bar.setProgress(pct);card.addView(bar,new LinearLayout.LayoutParams(-1,dp(3)));}}
    card.setOnClickListener(v->{if(item.series)openSeries(item);else playMovie(item);});card.setOnLongClickListener(v->{toggleWatchlist(item);return true;});
    android.graphics.drawable.StateListDrawable focus=new android.graphics.drawable.StateListDrawable();focus.addState(new int[]{android.R.attr.state_focused},surface(Color.TRANSPARENT,14,cobraModeColor("accent"),2));focus.addState(new int[]{},surface(Color.TRANSPARENT,14,Color.TRANSPARENT,0));card.setBackground(focus);
    return card;
  }

  private ArrayList<VodItem> cobraVodContinueSubset(ArrayList<VodItem> items) {
    HashSet<String> keys=new HashSet<>();try{JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("continue_items"),"[]"));for(int i=0;i<list.length();i++){JSONObject o=list.optJSONObject(i);if(o!=null)keys.add(o.optString("key"));}}catch(Exception ignored){}
    ArrayList<VodItem> out=new ArrayList<>();for(VodItem item:items)if(keys.contains(item.sourceId+":"+item.id))out.add(item);return out;
  }

  private ArrayList<VodItem> cobraVodWatchlistSubset(ArrayList<VodItem> items) {
    HashSet<String> keys=new HashSet<>();try{JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("watchlist"),"[]"));for(int i=0;i<list.length();i++){JSONObject o=list.optJSONObject(i);if(o!=null)keys.add(o.optString("source")+":"+o.optString("id"));}}catch(Exception ignored){}
    ArrayList<VodItem> out=new ArrayList<>();for(VodItem item:items)if(keys.contains(item.sourceId+":"+item.id))out.add(item);return out;
  }

  private int cobraVodProgressPercent(VodItem item){try{JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("continue_items"),"[]"));String key=item.sourceId+":"+item.id;for(int i=0;i<list.length();i++){JSONObject o=list.optJSONObject(i);if(o!=null&&key.equals(o.optString("key"))){long p=o.optLong("position"),d=o.optLong("duration");return d>0?(int)Math.min(99,p*100L/d):0;}}}catch(Exception ignored){}return 0;}

  private void cobraShowVodDetails(VodItem item) {
    LiveSource source=sourceById(item.sourceId);if(source==null)return;status("Loading details…");
    submitCobraIo(()->{String description="";String extra="";try{String action=item.series?"get_series_info":"get_vod_info";String idKey=item.series?"series_id":"vod_id";JSONObject root=new JSONObject(httpGet(xtreamUrl(source,action)+"&"+idKey+"="+enc(item.id)));JSONObject info=root.optJSONObject("info");if(info!=null){description=info.optString("plot",info.optString("description",""));String year=info.optString("releasedate",info.optString("year",""));String rating=info.optString("rating","");extra=(year.isEmpty()?"":year)+(rating.isEmpty()?"":((year.isEmpty()?"":"  •  ")+rating+" ★"));}}catch(Exception ignored){}final String body=description==null||description.trim().isEmpty()?item.category:description.trim();final String metadata=extra;runOnUiThread(()->{status("Ready");new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle(item.title).setMessage((metadata.isEmpty()?"":metadata+"\n\n")+body).setPositiveButton(item.series?"Episodes":"Play",(d,w)->{if(item.series)openSeries(item);else playMovie(item);}).setNeutralButton("My List",(d,w)->toggleWatchlist(item)).setNegativeButton("Close",null).show();});});
  }

  private void cobraLoadVodArtwork(android.widget.ImageView view,String rawUrl) {
    final String url=rawUrl==null?"":rawUrl.trim();if(url.isEmpty()||!(url.startsWith("http://")||url.startsWith("https://")))return;
    final String tag="cobra-vod-art:"+url;view.setTag(tag);android.graphics.Bitmap cached; synchronized(mCobraVodArtwork){cached=mCobraVodArtwork.get(url);}if(cached!=null&&!cached.isRecycled()){view.setImageBitmap(cached);return;}
    submitCobraIo(()->{android.graphics.Bitmap bitmap=null;okhttp3.OkHttpClient client=null;okhttp3.Response response=null;try{int mode=cobraNetworkFamilyMode();CobraNetworkFamilyPolicy.NetworkTelemetry telemetry=new CobraNetworkFamilyPolicy.NetworkTelemetry(url);CobraNetworkFamilyPolicy.FamilyDns dns=CobraNetworkFamilyPolicy.dns(url,mode,telemetry);client=CobraNetworkFamilyPolicy.client(dns,telemetry,5000,8000);okhttp3.Request request=new okhttp3.Request.Builder().url(url).get().build();response=client.newCall(request).execute();if(!response.isSuccessful()||response.body()==null)return;long length=response.body().contentLength();if(length>4L*1024L*1024L)return;java.io.InputStream in=response.body().byteStream();bitmap=android.graphics.BitmapFactory.decodeStream(in);if(bitmap==null)return;synchronized(mCobraVodArtwork){mCobraVodArtwork.put(url,bitmap);}final android.graphics.Bitmap ready=bitmap;runOnUiThread(()->{if(tag.equals(view.getTag())&&!ready.isRecycled())view.setImageBitmap(ready);});}catch(Exception ignored){}finally{if(response!=null)response.close();if(client!=null){client.dispatcher().cancelAll();client.connectionPool().evictAll();}}});
  }

