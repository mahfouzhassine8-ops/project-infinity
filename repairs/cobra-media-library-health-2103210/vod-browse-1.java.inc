  /** Cinematic Movies/Shows browse surface. Data and playback routes are existing Cobra VOD owners only. */
  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    clearStage(series ? "COBRA • SHOWS" : "COBRA • MOVIES");
    status(items.size() + " titles across enabled providers");
    if (items.isEmpty()) { renderVodItems(items, series, failures); return; }

    final ScrollView scroll = new ScrollView(this);
    final LinearLayout page = new LinearLayout(this); page.setOrientation(LinearLayout.VERTICAL);
    page.setPadding(dp(isCompact()?8:14), dp(4), dp(isCompact()?8:14), dp(24)); scroll.addView(page);

    LinearLayout tabs = new LinearLayout(this); tabs.setGravity(Gravity.CENTER_VERTICAL);
    Button movies = cobraVodChip("Movies", !series); movies.setOnClickListener(v -> showMovies());
    Button shows = cobraVodChip("Shows", series); shows.setOnClickListener(v -> showSeries());
    Button search = cobraVodChip("Search", false); search.setOnClickListener(v -> searchVod(items, series));
    tabs.addView(movies,new LinearLayout.LayoutParams(0,dp(44),1));
    LinearLayout.LayoutParams middle=new LinearLayout.LayoutParams(0,dp(44),1);middle.leftMargin=dp(8);tabs.addView(shows,middle);
    LinearLayout.LayoutParams last=new LinearLayout.LayoutParams(0,dp(44),1);last.leftMargin=dp(8);tabs.addView(search,last);
    LinearLayout.LayoutParams tabsLp=new LinearLayout.LayoutParams(-1,-2);tabsLp.bottomMargin=dp(10);page.addView(tabs,tabsLp);

    VodItem hero = items.get(0);
    page.addView(cobraVodHero(hero, series), new LinearLayout.LayoutParams(-1, dp(isCompact()?286:320)));

    ArrayList<VodItem> continuing = cobraVodContinueSubset(items);
    if (!continuing.isEmpty()) cobraAddVodShelf(page, "Continue Watching", continuing, 12, true);
    ArrayList<VodItem> saved = cobraVodWatchlistSubset(items);
    if (!saved.isEmpty()) cobraAddVodShelf(page, "My List", saved, 12, false);

    LinkedHashMap<String,ArrayList<VodItem>> shelves = new LinkedHashMap<>();
    for (VodItem item : items) {
      ArrayList<VodItem> row=shelves.get(item.category);
      if(row==null){row=new ArrayList<>();shelves.put(item.category,row);}
      if(row.size()<18)row.add(item);
    }
    int shown=0;
    for(Map.Entry<String,ArrayList<VodItem>> entry:shelves.entrySet()){
      if(shown++>=7)break;
      cobraAddVodShelf(page,entry.getKey(),entry.getValue(),14,false);
    }
    cobraAddVodShelf(page, series ? "All Shows" : "All Movies", new ArrayList<>(items.subList(0,Math.min(items.size(),24))), 24, false);

    if(!failures.isEmpty()){
      TextView note=text("Some providers could not refresh. Existing available titles are shown.",cobraThemeColor("muted",mTheme.muted),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      page.addView(note,new LinearLayout.LayoutParams(-1,dp(42)));
    }
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  }

  private Button cobraVodChip(String label, boolean selected) {
    Button button=action(label);button.setAllCaps(false);button.setTextSize(13);button.setSelected(selected);
    int fill=selected?cobraModeColor("accent"):cobraModeColor("panel");
    int ink=selected?Color.BLACK:cobraModeColor("text");
    button.setTextColor(ink);button.setBackground(surface(fill,18,selected?cobraModeColor("accent"):cobraModeColor("line"),1));
    return button;
  }

  private View cobraVodHero(VodItem item, boolean series) {
    FrameLayout hero=new FrameLayout(this);hero.setClipToOutline(true);hero.setBackground(surface(cobraModeColor("panel"),20,cobraModeColor("line"),1));
    android.widget.ImageView art=new android.widget.ImageView(this);art.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);art.setBackgroundColor(cobraModeColor("panel"));
    hero.addView(art,new FrameLayout.LayoutParams(-1,-1));cobraLoadVodArtwork(art,item.icon);
    View veil=new View(this);android.graphics.drawable.GradientDrawable fade=new android.graphics.drawable.GradientDrawable(android.graphics.drawable.GradientDrawable.Orientation.BOTTOM_TOP,new int[]{0xf20a0e15,0xb20a0e15,0x100a0e15});veil.setBackground(fade);hero.addView(veil,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);copy.setGravity(Gravity.BOTTOM);copy.setPadding(dp(18),dp(18),dp(18),dp(16));
    TextView eyebrow=text(series?"COBRA SHOWS":"COBRA MOVIES",0xff7bdcff,11,Gravity.LEFT);eyebrow.setLetterSpacing(.12f);copy.addView(eyebrow,new LinearLayout.LayoutParams(-1,dp(28)));
    TextView title=text(item.title,Color.WHITE,isCompact()?26:31,Gravity.LEFT|Gravity.BOTTOM);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setMaxLines(2);copy.addView(title,new LinearLayout.LayoutParams(-1,-2));
    LiveSource source=sourceById(item.sourceId);String provider=source==null?"Provider":source.name;
    TextView meta=text(item.category+"  •  "+provider,0xffc5d0df,12,Gravity.LEFT);meta.setMaxLines(1);copy.addView(meta,new LinearLayout.LayoutParams(-1,dp(34)));
    LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
    Button play=action(series?"Browse Episodes":"▶  Play");play.setAllCaps(false);play.setOnClickListener(v->{if(item.series)openSeries(item);else playMovie(item);});
    Button details=action("Details");details.setAllCaps(false);details.setOnClickListener(v->cobraShowVodDetails(item));
    Button list=action("+ My List");list.setAllCaps(false);list.setOnClickListener(v->toggleWatchlist(item));
    actions.addView(play,new LinearLayout.LayoutParams(0,dp(48),1));LinearLayout.LayoutParams a2=new LinearLayout.LayoutParams(0,dp(48),1);a2.leftMargin=dp(8);actions.addView(details,a2);LinearLayout.LayoutParams a3=new LinearLayout.LayoutParams(0,dp(48),1);a3.leftMargin=dp(8);actions.addView(list,a3);
    copy.addView(actions,new LinearLayout.LayoutParams(-1,dp(52)));hero.addView(copy,new FrameLayout.LayoutParams(-1,-1));
    return hero;
  }

  private void cobraAddVodShelf(LinearLayout page,String title,ArrayList<VodItem> items,int limit,boolean progress) {
    if(items==null||items.isEmpty())return;
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);TextView label=text(title,cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);label.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));heading.addView(label,new LinearLayout.LayoutParams(0,dp(44),1));
    if(items.size()>limit){TextView more=text("See all  ›",cobraModeColor("accent"),12,Gravity.RIGHT|Gravity.CENTER_VERTICAL);heading.addView(more,new LinearLayout.LayoutParams(dp(84),dp(44)));}
    LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,-2);headLp.topMargin=dp(16);page.addView(heading,headLp);
    android.widget.HorizontalScrollView rail=new android.widget.HorizontalScrollView(this);rail.setHorizontalScrollBarEnabled(false);rail.setFillViewport(false);
    LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setPadding(dp(2),0,dp(12),dp(2));rail.addView(row,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
    int count=Math.min(limit,items.size());for(int i=0;i<count;i++)row.addView(cobraVodCard(items.get(i),progress),cobraVodCardParams());
    page.addView(rail,new LinearLayout.LayoutParams(-1,dp(isCompact()?236:270)));
  }

  private LinearLayout.LayoutParams cobraVodCardParams(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(isCompact()?126:148),-1);p.rightMargin=dp(10);return p;}

