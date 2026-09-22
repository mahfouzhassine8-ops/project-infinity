  /** 2103211 locked Movies/TV Shows browse: no cross-destination tabs or duplicate Search. */
  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");
    status(items.size() + " titles across enabled providers");
    if (items.isEmpty()) { renderVodItems(items, series, failures); return; }

    final ScrollView scroll = new ScrollView(this);
    final LinearLayout page = new LinearLayout(this);
    page.setOrientation(LinearLayout.VERTICAL);
    page.setPadding(dp(isCompact()?8:14), dp(4), dp(isCompact()?8:14), dp(24));
    scroll.addView(page);

    ArrayList<VodItem> featured = cobraVodFeaturedSubset(items);
    page.addView(cobraVodHeroCarousel(featured, series),
        new LinearLayout.LayoutParams(-1, dp(isCompact()?286:320)));

    ArrayList<VodItem> recent = cobraVodRecentSubset(items);
    cobraAddVodShelf(page, "Recent Releases", recent, 14, false, series);

    ArrayList<VodItem> continuing = cobraVodContinueSubset(items);
    if (!continuing.isEmpty())
      cobraAddVodShelf(page, "Continue Watching", continuing, 12, true, series);

    ArrayList<VodItem> trending = cobraVodTrendingSubset(items);
    cobraAddVodShelf(page, series ? "Trending Shows" : "Trending Movies", trending, 14, false, series);

    ArrayList<VodItem> popular = cobraVodPopularSubset(items);
    cobraAddVodShelf(page, "Popular Now", popular, 14, false, series);

    // Locked structure: Genres sits directly below Popular Now.
    cobraAddVodGenres(page, items, series);

    ArrayList<VodItem> because = cobraVodBecauseYouWatched(items);
    if (!because.isEmpty())
      cobraAddVodShelf(page, "Because You Watched…", because, 14, false, series);

    if (!failures.isEmpty()) {
      TextView note=text("Some providers could not refresh. Existing available titles are shown.",
          cobraThemeColor("muted",mTheme.muted),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      page.addView(note,new LinearLayout.LayoutParams(-1,dp(42)));
    }
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  }

  private long cobraVodParseEpoch(String raw) {
    if (raw == null) return 0L;
    try {
      long value = Long.parseLong(raw.trim());
      if (value > 0L && value < 100000000000L) value *= 1000L;
      return value;
    } catch (Exception ignored) { return 0L; }
  }

  private String cobraVodKey(VodItem item) { return item.sourceId + ":" + item.id; }

  private ArrayList<VodItem> cobraVodRecentSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> out=new ArrayList<>(items);
    Collections.sort(out,(a,b)->Long.compare(b.addedEpoch,a.addedEpoch));
    return out;
  }

  private double cobraVodTrendScore(VodItem item) {
    return Math.max(0.0,item.rating)*10000000000000.0 + Math.max(0L,item.addedEpoch);
  }

  private ArrayList<VodItem> cobraVodTrendingSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> out=new ArrayList<>(items);
    Collections.sort(out,(a,b)->{
      int score=Double.compare(cobraVodTrendScore(b),cobraVodTrendScore(a));
      return score!=0?score:a.title.compareToIgnoreCase(b.title);
    });
    return out;
  }

  private ArrayList<VodItem> cobraVodPopularSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> out=new ArrayList<>(items);
    Collections.sort(out,(a,b)->{
      int rating=Double.compare(b.rating,a.rating);
      if(rating!=0)return rating;
      return Long.compare(b.addedEpoch,a.addedEpoch);
    });
    return out;
  }

  private ArrayList<VodItem> cobraVodFeaturedSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> ranked=cobraVodTrendingSubset(items);
    ArrayList<VodItem> out=new ArrayList<>();
    HashSet<String> seen=new HashSet<>();
    for(VodItem item:ranked){
      if(seen.add(cobraVodKey(item)))out.add(item);
      if(out.size()>=5)break;
    }
    if(out.isEmpty())out.add(items.get(0));
    return out;
  }

  private JSONObject cobraVodContinueObject(VodItem item) {
    try {
      JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("continue_items"),"[]"));
      String exact=cobraVodKey(item);
      for(int i=0;i<list.length();i++){
        JSONObject o=list.optJSONObject(i);if(o==null)continue;
        if(exact.equals(o.optString("key")))return o;
        if(item.series && item.title.equalsIgnoreCase(o.optString("group","")) &&
            o.optString("key","").startsWith(item.sourceId+":"))return o;
      }
    }catch(Exception ignored){}
    return null;
  }

  private ArrayList<VodItem> cobraVodContinueSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> out=new ArrayList<>();
    for(VodItem item:items)if(cobraVodContinueObject(item)!=null)out.add(item);
    Collections.sort(out,(a,b)->{
      JSONObject aa=cobraVodContinueObject(a),bb=cobraVodContinueObject(b);
      long at=aa==null?0L:aa.optLong("updated",0L),bt=bb==null?0L:bb.optLong("updated",0L);
      return Long.compare(bt,at);
    });
    return out;
  }

  private String cobraVodContinueLabel(VodItem item) {
    JSONObject o=cobraVodContinueObject(item);if(o==null)return "";
    if(item.series){
      String episode=o.optString("title","Resume episode");
      return episode.isEmpty()?"Resume episode":episode.replace(" • "," · ");
    }
    long p=o.optLong("position",0L),d=o.optLong("duration",0L);
    int pct=d>0?(int)Math.min(99,p*100L/d):0;
    return pct>0?pct+"% watched":"Resume";
  }

  private int cobraVodProgressPercent(VodItem item) {
    JSONObject o=cobraVodContinueObject(item);if(o==null)return 0;
    long p=o.optLong("position",0L),d=o.optLong("duration",0L);
    return d>0?(int)Math.min(99,p*100L/d):0;
  }

  private String cobraVodGenreLabel(String raw) {
    if(raw==null)return "";
    String value=raw.trim();if(value.isEmpty())return "";
    String s=value.toLowerCase(Locale.US);
    if(s.contains("adult")||s.contains("xxx"))return "";
    if(s.matches(".*\\b(19|20)\\d{2}\\b.*"))return "";
    if(s.contains("action")||s.contains("adventure"))return "Action & Adventure";
    if(s.contains("sci-fi")||s.contains("science fiction")||s.contains("fantasy"))return "Sci-Fi & Fantasy";
    if(s.contains("comedy"))return "Comedy";
    if(s.contains("horror"))return "Horror";
    if(s.contains("drama"))return "Drama";
    if(s.contains("thriller"))return "Thriller";
    if(s.contains("crime"))return "Crime";
    if(s.contains("family")||s.contains("kids")||s.contains("children"))return "Family";
    if(s.contains("animation")||s.contains("anime"))return "Animation";
    if(s.contains("romance"))return "Romance";
    if(s.contains("documentary"))return "Documentary";
    if(s.contains("reality"))return "Reality";
    if(s.contains("mystery"))return "Mystery";
    if(s.contains("western"))return "Western";
    if(s.contains("history"))return "History";
    if(s.contains("music"))return "Music";
    if(s.contains("sport"))return "Sports";
    return value.length()<=28?value:"";
  }

  private LinkedHashMap<String,ArrayList<VodItem>> cobraVodGenreBuckets(ArrayList<VodItem> items) {
    LinkedHashMap<String,ArrayList<VodItem>> raw=new LinkedHashMap<>();
    for(VodItem item:items){
      String label=cobraVodGenreLabel(item.category);if(label.isEmpty())continue;
      ArrayList<VodItem> bucket=raw.get(label);
      if(bucket==null){bucket=new ArrayList<>();raw.put(label,bucket);}
      bucket.add(item);
    }
    String[] preferred={"Action & Adventure","Comedy","Horror","Drama","Sci-Fi & Fantasy","Thriller",
        "Crime","Family","Animation","Romance","Documentary","Reality","Mystery","Western","History","Music","Sports"};
    LinkedHashMap<String,ArrayList<VodItem>> ordered=new LinkedHashMap<>();
    for(String label:preferred)if(raw.containsKey(label))ordered.put(label,raw.remove(label));
    ArrayList<String> rest=new ArrayList<>(raw.keySet());Collections.sort(rest,String.CASE_INSENSITIVE_ORDER);
    for(String label:rest)ordered.put(label,raw.get(label));
    return ordered;
  }

  private ArrayList<VodItem> cobraVodBecauseYouWatched(ArrayList<VodItem> items) {
    try {
      JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("continue_items"),"[]"));
      if(list.length()==0)return new ArrayList<>();
      JSONObject recent=list.optJSONObject(0);if(recent==null)return new ArrayList<>();
      String key=recent.optString("key",""),group=recent.optString("group","");
      VodItem anchor=null;
      for(VodItem item:items){
        if(key.equals(cobraVodKey(item)) ||
            (item.series && item.title.equalsIgnoreCase(group) && key.startsWith(item.sourceId+":"))){
          anchor=item;break;
        }
      }
      if(anchor==null)return new ArrayList<>();
      String genre=cobraVodGenreLabel(anchor.category);if(genre.isEmpty())return new ArrayList<>();
      ArrayList<VodItem> out=new ArrayList<>();
      for(VodItem item:items){
        if(cobraVodKey(item).equals(cobraVodKey(anchor)))continue;
        if(genre.equals(cobraVodGenreLabel(item.category)))out.add(item);
        if(out.size()>=24)break;
      }
      return out;
    }catch(Exception ignored){return new ArrayList<>();}
  }

  private View cobraVodHeroCarousel(ArrayList<VodItem> items, boolean series) {
    android.widget.ViewFlipper carousel=new android.widget.ViewFlipper(this);
    carousel.setAutoStart(false);carousel.setFlipInterval(9000);
    carousel.setInAnimation(this,android.R.anim.fade_in);carousel.setOutAnimation(this,android.R.anim.fade_out);
    int count=Math.min(5,items.size());
    for(int i=0;i<count;i++)carousel.addView(cobraVodHero(items.get(i),series,carousel),
        new FrameLayout.LayoutParams(-1,-1));
    if(count>1)carousel.startFlipping();
    return carousel;
  }

  private void cobraVodHeroFocus(View view, android.widget.ViewFlipper carousel) {
    if(view==null||carousel==null)return;
    view.setOnFocusChangeListener((v,focused)->{
      if(focused)carousel.stopFlipping();
      else if(!carousel.hasFocus()&&carousel.getChildCount()>1)carousel.startFlipping();
    });
  }

  private View cobraVodHero(VodItem item, boolean series, android.widget.ViewFlipper carousel) {
    FrameLayout hero=new FrameLayout(this);hero.setClipToOutline(true);
    hero.setBackground(surface(cobraModeColor("panel"),20,cobraModeColor("line"),1));
    android.widget.ImageView art=new android.widget.ImageView(this);
    art.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);art.setBackgroundColor(cobraModeColor("panel"));
    hero.addView(art,new FrameLayout.LayoutParams(-1,-1));cobraLoadVodArtwork(art,item.icon);
    View veil=new View(this);
    android.graphics.drawable.GradientDrawable fade=new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.BOTTOM_TOP,new int[]{0xf20a0e15,0xb20a0e15,0x100a0e15});
    veil.setBackground(fade);hero.addView(veil,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);
    copy.setGravity(Gravity.BOTTOM);copy.setPadding(dp(18),dp(18),dp(18),dp(16));
    TextView eyebrow=text(series?"COBRA TV SHOWS":"COBRA MOVIES",0xff7bdcff,11,Gravity.LEFT);
    eyebrow.setLetterSpacing(.12f);copy.addView(eyebrow,new LinearLayout.LayoutParams(-1,dp(28)));
    TextView title=text(item.title,Color.WHITE,isCompact()?26:31,Gravity.LEFT|Gravity.BOTTOM);
    title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setMaxLines(2);
    copy.addView(title,new LinearLayout.LayoutParams(-1,-2));
    LiveSource source=sourceById(item.sourceId);String provider=source==null?"Provider":source.name;
    String meta=item.category+"  •  "+provider;
    if(!item.year.isEmpty())meta+="  •  "+item.year;
    if(item.rating>0.0)meta+="  •  "+String.format(Locale.US,"%.1f ★",item.rating);
    TextView metadata=text(meta,0xffc5d0df,12,Gravity.LEFT);metadata.setMaxLines(1);
    copy.addView(metadata,new LinearLayout.LayoutParams(-1,dp(34)));
    LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
    Button play=action(series?"Browse Episodes":"▶  Play");play.setAllCaps(false);
    play.setOnClickListener(v->{carousel.stopFlipping();if(item.series)openSeries(item);else playMovie(item);});
    Button details=action("Details");details.setAllCaps(false);
    details.setOnClickListener(v->{carousel.stopFlipping();cobraShowVodDetails(item);});
    Button list=action("+ My List");list.setAllCaps(false);
    list.setOnClickListener(v->{carousel.stopFlipping();toggleWatchlist(item);});
    cobraVodHeroFocus(play,carousel);cobraVodHeroFocus(details,carousel);cobraVodHeroFocus(list,carousel);
    actions.addView(play,new LinearLayout.LayoutParams(0,dp(48),1));
    LinearLayout.LayoutParams a2=new LinearLayout.LayoutParams(0,dp(48),1);a2.leftMargin=dp(8);actions.addView(details,a2);
    LinearLayout.LayoutParams a3=new LinearLayout.LayoutParams(0,dp(48),1);a3.leftMargin=dp(8);actions.addView(list,a3);
    copy.addView(actions,new LinearLayout.LayoutParams(-1,dp(52)));hero.addView(copy,new FrameLayout.LayoutParams(-1,-1));
    return hero;
  }

  private void cobraAddVodShelf(LinearLayout page,String title,ArrayList<VodItem> items,int limit,
      boolean progress,boolean series) {
    if(items==null||items.isEmpty())return;
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    TextView label=text(title,cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    label.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    heading.addView(label,new LinearLayout.LayoutParams(0,dp(44),1));
    TextView more=text("See all  ›",cobraModeColor("accent"),12,Gravity.RIGHT|Gravity.CENTER_VERTICAL);
    more.setFocusable(true);more.setClickable(true);more.setContentDescription("See all "+title);
    more.setOnClickListener(v->cobraShowVodCollection(title,items,series));
    heading.addView(more,new LinearLayout.LayoutParams(dp(90),dp(44)));
    LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,-2);headLp.topMargin=dp(16);page.addView(heading,headLp);
    android.widget.HorizontalScrollView rail=new android.widget.HorizontalScrollView(this);
    rail.setHorizontalScrollBarEnabled(false);rail.setFillViewport(false);
    LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setPadding(dp(2),0,dp(12),dp(2));
    rail.addView(row,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
    int count=Math.min(limit,items.size());
    for(int i=0;i<count;i++)row.addView(cobraVodCard(items.get(i),progress),cobraVodCardParams());
    page.addView(rail,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)));
  }

  private LinearLayout.LayoutParams cobraVodCardParams(){
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(isCompact()?126:148),-1);p.rightMargin=dp(10);return p;
  }

  private String cobraVodCardMeta(VodItem item) {
    String meta="";
    if(!item.year.isEmpty())meta=item.year;
    if(item.rating>0.0)meta+=(meta.isEmpty()?"":"  •  ")+String.format(Locale.US,"%.1f ★",item.rating);
    return meta;
  }

  private View cobraVodCard(VodItem item,boolean progress) {
    LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);
    card.setFocusable(true);card.setClickable(true);card.setPadding(0,0,0,dp(4));
    card.setContentDescription(item.title+", "+item.category);
    android.widget.ImageView poster=new android.widget.ImageView(this);
    poster.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
    poster.setBackground(surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));
    card.addView(poster,new LinearLayout.LayoutParams(-1,dp(isCompact()?174:202)));cobraLoadVodArtwork(poster,item.icon);
    TextView name=text(item.title,cobraModeColor("text"),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    name.setMaxLines(2);name.setEllipsize(android.text.TextUtils.TruncateAt.END);
    card.addView(name,new LinearLayout.LayoutParams(-1,dp(42)));
    String sub=progress?cobraVodContinueLabel(item):cobraVodCardMeta(item);
    if(!sub.isEmpty()){
      TextView line=text(sub,cobraModeColor("muted"),10,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      line.setMaxLines(1);line.setEllipsize(android.text.TextUtils.TruncateAt.END);
      card.addView(line,new LinearLayout.LayoutParams(-1,dp(22)));
    }
    if(progress){
      int pct=cobraVodProgressPercent(item);
      if(pct>0){android.widget.ProgressBar bar=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        bar.setMax(100);bar.setProgress(pct);card.addView(bar,new LinearLayout.LayoutParams(-1,dp(3)));}
    }
    // Posters open details; playback happens only from an explicit Play/Browse Episodes action.
    card.setOnClickListener(v->cobraShowVodDetails(item));
    card.setOnLongClickListener(v->{toggleWatchlist(item);return true;});
    android.graphics.drawable.StateListDrawable focus=new android.graphics.drawable.StateListDrawable();
    focus.addState(new int[]{android.R.attr.state_focused},surface(Color.TRANSPARENT,14,cobraModeColor("accent"),2));
    focus.addState(new int[]{},surface(Color.TRANSPARENT,14,Color.TRANSPARENT,0));card.setBackground(focus);
    return card;
  }

  private void cobraAddVodGenres(LinearLayout page,ArrayList<VodItem> items,boolean series) {
    LinkedHashMap<String,ArrayList<VodItem>> buckets=cobraVodGenreBuckets(items);if(buckets.isEmpty())return;
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    TextView label=text("Genres",cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    label.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    heading.addView(label,new LinearLayout.LayoutParams(0,dp(44),1));
    if(buckets.size()>12){
      TextView more=text("See all  ›",cobraModeColor("accent"),12,Gravity.RIGHT|Gravity.CENTER_VERTICAL);
      more.setFocusable(true);more.setClickable(true);more.setOnClickListener(v->cobraShowVodGenrePicker(buckets,series));
      heading.addView(more,new LinearLayout.LayoutParams(dp(90),dp(44)));
    }
    LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,-2);headLp.topMargin=dp(16);page.addView(heading,headLp);
    LinearLayout grid=new LinearLayout(this);grid.setOrientation(LinearLayout.VERTICAL);
    int columns=isCompact()?2:3,index=0,shown=0;
    LinearLayout row=null;
    for(Map.Entry<String,ArrayList<VodItem>> entry:buckets.entrySet()){
      if(shown++>=12)break;
      if(index%columns==0){row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);grid.addView(row,new LinearLayout.LayoutParams(-1,dp(82)));}
      Button genre=action(entry.getKey());genre.setAllCaps(false);genre.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
      genre.setTextSize(13);genre.setBackground(surface(cobraModeColor("panel"),16,cobraModeColor("line"),1));
      final String genreName=entry.getKey();final ArrayList<VodItem> genreItems=entry.getValue();
      genre.setOnClickListener(v->cobraShowVodCollection(genreName,genreItems,series));
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(72),1);lp.setMargins(dp(4),dp(4),dp(4),dp(4));
      row.addView(genre,lp);index++;
    }
    page.addView(grid,new LinearLayout.LayoutParams(-1,-2));
  }

  private void cobraShowVodGenrePicker(LinkedHashMap<String,ArrayList<VodItem>> buckets,boolean series) {
    final ArrayList<String> names=new ArrayList<>(buckets.keySet());
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle("Genres")
        .setItems(names.toArray(new String[0]),(d,which)->{
          if(which>=0&&which<names.size())cobraShowVodCollection(names.get(which),buckets.get(names.get(which)),series);
        }).setNegativeButton("Close",null).show();
  }

  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series) {
    clearStage("COBRA • "+title.toUpperCase(Locale.US));status(items.size()+" titles");
    ScrollView scroll=new ScrollView(this);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);
    page.setPadding(dp(isCompact()?8:14),dp(6),dp(isCompact()?8:14),dp(24));scroll.addView(page);
    int columns=isCompact()?2:4,index=0;LinearLayout row=null;
    for(VodItem item:items){
      if(index%columns==0){row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(row,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)));}
      View card=cobraVodCard(item,cobraVodContinueObject(item)!=null);
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-1,1);lp.setMargins(dp(5),0,dp(5),0);row.addView(card,lp);index++;
      if(index>=120)break;
    }
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  }

  private void cobraShowVodDetails(VodItem item) {
    LiveSource source=sourceById(item.sourceId);if(source==null)return;status("Loading details…");
    submitCobraIo(()->{
      String description="",extra="",runtime="",genre=item.category;
      try{
        String action=item.series?"get_series_info":"get_vod_info";
        String idKey=item.series?"series_id":"vod_id";
        JSONObject root=new JSONObject(httpGet(xtreamUrl(source,action)+"&"+idKey+"="+enc(item.id)));
        JSONObject info=root.optJSONObject("info");
        if(info!=null){
          description=info.optString("plot",info.optString("description",""));
          String year=info.optString("releasedate",info.optString("year",item.year));
          String rating=info.optString("rating",item.rating>0.0?String.format(Locale.US,"%.1f",item.rating):"");
          runtime=info.optString("duration",info.optString("duration_secs",""));
          genre=info.optString("genre",item.category);
          extra=(year.isEmpty()?"":year)+(rating.isEmpty()?"":((year.isEmpty()?"":"  •  ")+rating+" ★"));
        }
      }catch(Exception ignored){}
      final String body=description==null||description.trim().isEmpty()?item.category:description.trim();
      final String metadata=extra,finalRuntime=runtime,finalGenre=genre==null?item.category:genre;
      final String provider=source.name;
      runOnUiThread(()->{
        status("Ready");
        String details=(metadata.isEmpty()?"":metadata+"\n")+
            (finalRuntime.isEmpty()?"":"Runtime: "+finalRuntime+"\n")+
            "Genre: "+finalGenre+"\nAvailable via: "+provider+"\n\n"+body;
        new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle(item.title).setMessage(details)
            .setPositiveButton(item.series?"Browse Episodes":"Play",(d,w)->{if(item.series)openSeries(item);else playMovie(item);})
            .setNeutralButton("My List",(d,w)->toggleWatchlist(item))
            .setNegativeButton("Close",null).show();
      });
    });
  }

  private void cobraLoadVodArtwork(android.widget.ImageView view,String rawUrl) {
    final String url=rawUrl==null?"":rawUrl.trim();if(url.isEmpty()||!(url.startsWith("http://")||url.startsWith("https://")))return;
    final String tag="cobra-vod-art:"+url;view.setTag(tag);android.graphics.Bitmap cached;
    synchronized(mCobraVodArtwork){cached=mCobraVodArtwork.get(url);}
    if(cached!=null&&!cached.isRecycled()){view.setImageBitmap(cached);return;}
    submitCobraIo(()->{
      android.graphics.Bitmap bitmap=null;okhttp3.OkHttpClient client=null;okhttp3.Response response=null;
      try{
        int mode=cobraNetworkFamilyMode();CobraNetworkFamilyPolicy.NetworkTelemetry telemetry=new CobraNetworkFamilyPolicy.NetworkTelemetry(url);
        CobraNetworkFamilyPolicy.FamilyDns dns=CobraNetworkFamilyPolicy.dns(url,mode,telemetry);
        client=CobraNetworkFamilyPolicy.client(dns,telemetry,5000,8000);
        okhttp3.Request request=new okhttp3.Request.Builder().url(url).get().build();response=client.newCall(request).execute();
        if(!response.isSuccessful()||response.body()==null)return;long length=response.body().contentLength();if(length>4L*1024L*1024L)return;
        java.io.InputStream in=response.body().byteStream();bitmap=android.graphics.BitmapFactory.decodeStream(in);if(bitmap==null)return;
        synchronized(mCobraVodArtwork){mCobraVodArtwork.put(url,bitmap);}final android.graphics.Bitmap ready=bitmap;
        runOnUiThread(()->{if(tag.equals(view.getTag())&&!ready.isRecycled())view.setImageBitmap(ready);});
      }catch(Exception ignored){}finally{
        if(response!=null)response.close();
        if(client!=null){client.dispatcher().cancelAll();client.connectionPool().evictAll();}
      }
    });
  }

