  private static final class CobraVodCollectionState {
    final String title;
    final ArrayList<VodItem> source;
    final boolean series;
    String sort="newest";
    String provider="";
    String watch="all";
    String genre="";
    boolean myListOnly=false;
    CobraVodCollectionState(String title,ArrayList<VodItem> items,boolean series){
      this.title=title;this.source=new ArrayList<>(items);this.series=series;
    }
  }

  private void cobraRememberVodCatalog(ArrayList<VodItem> items,boolean series){
    ArrayList<VodItem> target=series?mCobraVodShowsCatalog:mCobraVodMoviesCatalog;
    target.clear();target.addAll(items);
  }

  private ArrayList<VodItem> cobraVodCatalog(boolean series){
    return new ArrayList<>(series?mCobraVodShowsCatalog:mCobraVodMoviesCatalog);
  }

  private boolean cobraVodWatchlistContains(VodItem item){
    try{
      JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("watchlist"),"[]"));
      for(int i=0;i<list.length();i++){
        JSONObject o=list.optJSONObject(i);if(o==null)continue;
        if(item.sourceId.equals(o.optString("source"))&&item.id.equals(o.optString("id")))return true;
      }
    }catch(Exception ignored){}
    return false;
  }

  private boolean cobraVodWatchedKey(String key,String group){
    try{
      JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("vod_watched"),"[]"));
      for(int i=0;i<list.length();i++){
        JSONObject o=list.optJSONObject(i);if(o==null)continue;
        if(key!=null&&!key.isEmpty()&&key.equals(o.optString("key")))return true;
        if(group!=null&&!group.isEmpty()&&group.equalsIgnoreCase(o.optString("group")))return true;
      }
    }catch(Exception ignored){}
    return false;
  }

  private boolean cobraVodWatched(VodItem item){
    if(item==null)return false;
    return cobraVodWatchedKey(cobraVodKey(item),item.series?item.title:"");
  }

  private void cobraMarkVodWatched(String key,String group){
    if(key==null||key.isEmpty())return;
    try{
      String pref=mFeatures.profileKey("vod_watched");
      JSONArray old;
      try{old=new JSONArray(mPrefs.getString(pref,"[]"));}catch(Exception ignored){old=new JSONArray();}
      JSONArray next=new JSONArray();JSONObject current=new JSONObject();
      current.put("key",key);current.put("group",group==null?"":group);current.put("updated",System.currentTimeMillis());next.put(current);
      for(int i=0;i<old.length()&&next.length()<400;i++){
        JSONObject o=old.optJSONObject(i);if(o==null||key.equals(o.optString("key")))continue;next.put(o);
      }
      mPrefs.edit().putString(pref,next.toString()).apply();
    }catch(Exception ignored){}
  }

  private int cobraVodYearNumber(VodItem item){
    if(item==null||item.year==null)return 0;
    Matcher match=Pattern.compile("(19|20)\\d{2}").matcher(item.year);
    if(match.find())try{return Integer.parseInt(match.group());}catch(Exception ignored){}
    return 0;
  }

  private ArrayList<VodItem> cobraVodFilteredItems(CobraVodCollectionState state){
    ArrayList<VodItem> out=new ArrayList<>();
    for(VodItem item:state.source){
      if(!state.provider.isEmpty()&&!state.provider.equals(item.sourceId))continue;
      if(!state.genre.isEmpty()&&!state.genre.equals(cobraVodGenreLabel(item.category)))continue;
      if(state.myListOnly&&!cobraVodWatchlistContains(item))continue;
      boolean watched=cobraVodWatched(item);
      if("watched".equals(state.watch)&&!watched)continue;
      if("unwatched".equals(state.watch)&&watched)continue;
      out.add(item);
    }
    Comparator<VodItem> comparator;
    if("az".equals(state.sort))comparator=(a,b)->a.title.compareToIgnoreCase(b.title);
    else if("rating".equals(state.sort))comparator=(a,b)->{
      int score=Double.compare(b.rating,a.rating);return score!=0?score:a.title.compareToIgnoreCase(b.title);
    };
    else if("added".equals(state.sort))comparator=(a,b)->{
      int added=Long.compare(b.addedEpoch,a.addedEpoch);return added!=0?added:a.title.compareToIgnoreCase(b.title);
    };
    else comparator=(a,b)->{
      int year=Integer.compare(cobraVodYearNumber(b),cobraVodYearNumber(a));
      if(year!=0)return year;int added=Long.compare(b.addedEpoch,a.addedEpoch);
      return added!=0?added:a.title.compareToIgnoreCase(b.title);
    };
    Collections.sort(out,comparator);return out;
  }

  private String cobraVodSortLabel(String sort){
    if("az".equals(sort))return "A–Z";
    if("rating".equals(sort))return "Rating";
    if("added".equals(sort))return "Recently Added";
    return "Newest";
  }

  private String cobraVodFilterSummary(CobraVodCollectionState state){
    ArrayList<String> parts=new ArrayList<>();
    if(!state.provider.isEmpty()){
      LiveSource source=sourceById(state.provider);parts.add(source==null?"Provider":source.name);
    }
    if(!"all".equals(state.watch))parts.add("watched".equals(state.watch)?"Watched":"Unwatched");
    if(state.myListOnly)parts.add("My List");
    if(!state.genre.isEmpty())parts.add(state.genre);
    return parts.isEmpty()?"All titles":android.text.TextUtils.join("  •  ",parts);
  }

  private void cobraShowVodSortPicker(CobraVodCollectionState state){
    final String[] labels={"Newest","A–Z","Rating","Recently Added"};
    final String[] values={"newest","az","rating","added"};
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle("Sort")
        .setItems(labels,(d,which)->{if(which>=0&&which<values.length){state.sort=values[which];cobraRenderVodCollection(state);}})
        .setNegativeButton("Cancel",null).show();
  }

  private void cobraShowVodProviderFilter(CobraVodCollectionState state){
    LinkedHashMap<String,String> providers=new LinkedHashMap<>();
    for(VodItem item:state.source){LiveSource source=sourceById(item.sourceId);providers.put(item.sourceId,source==null?"Provider":source.name);}
    ArrayList<String> ids=new ArrayList<>();ArrayList<String> labels=new ArrayList<>();
    ids.add("");labels.add("All providers");
    for(Map.Entry<String,String> entry:providers.entrySet()){ids.add(entry.getKey());labels.add(entry.getValue());}
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle("Provider")
        .setItems(labels.toArray(new String[0]),(d,which)->{if(which>=0&&which<ids.size()){state.provider=ids.get(which);cobraRenderVodCollection(state);}})
        .setNegativeButton("Cancel",null).show();
  }

  private void cobraShowVodWatchFilter(CobraVodCollectionState state){
    final String[] labels={"All","Watched","Unwatched"};final String[] values={"all","watched","unwatched"};
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle("Watch state")
        .setItems(labels,(d,which)->{if(which>=0&&which<values.length){state.watch=values[which];cobraRenderVodCollection(state);}})
        .setNegativeButton("Cancel",null).show();
  }

  private void cobraShowVodGenreFilter(CobraVodCollectionState state){
    LinkedHashMap<String,ArrayList<VodItem>> buckets=cobraVodGenreBuckets(state.source);
    ArrayList<String> labels=new ArrayList<>();labels.add("All genres");labels.addAll(buckets.keySet());
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle("Genre")
        .setItems(labels.toArray(new String[0]),(d,which)->{if(which>=0&&which<labels.size()){state.genre=which==0?"":labels.get(which);cobraRenderVodCollection(state);}})
        .setNegativeButton("Cancel",null).show();
  }

  private void cobraShowVodFilters(CobraVodCollectionState state){
    LiveSource provider=state.provider.isEmpty()?null:sourceById(state.provider);
    String[] options={
      "Provider  •  "+(provider==null?"All":provider.name),
      "Watch state  •  "+("all".equals(state.watch)?"All":"watched".equals(state.watch)?"Watched":"Unwatched"),
      "My List  •  "+(state.myListOnly?"On":"Off"),
      "Genre  •  "+(state.genre.isEmpty()?"All":state.genre),
      "Clear filters"
    };
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog").setTitle("Filters")
        .setItems(options,(d,which)->{
          if(which==0)cobraShowVodProviderFilter(state);
          else if(which==1)cobraShowVodWatchFilter(state);
          else if(which==2){state.myListOnly=!state.myListOnly;cobraRenderVodCollection(state);}
          else if(which==3)cobraShowVodGenreFilter(state);
          else if(which==4){state.provider="";state.watch="all";state.genre="";state.myListOnly=false;cobraRenderVodCollection(state);}
        }).setNegativeButton("Close",null).show();
  }

  private void cobraRenderVodCollection(CobraVodCollectionState state){
    mCobraInternalScreen="internal";clearStage("COBRA • "+state.title.toUpperCase(Locale.US));
    ArrayList<VodItem> items=cobraVodFilteredItems(state);status(items.size()+" titles  •  "+cobraVodFilterSummary(state));
    ScrollView scroll=new ScrollView(this);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);
    page.setPadding(dp(isCompact()?8:14),dp(6),dp(isCompact()?8:14),dp(24));scroll.addView(page);

    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);
    View edge=cobraTrackVodTrim(new View(this),"section");LinearLayout.LayoutParams edgeLp=new LinearLayout.LayoutParams(dp(4),dp(30));edgeLp.rightMargin=dp(9);header.addView(edge,edgeLp);
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);
    TextView title=text(state.title,cobraModeColor("text"),20,Gravity.LEFT|Gravity.CENTER_VERTICAL);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));copy.addView(title);
    TextView summary=text("Sort: "+cobraVodSortLabel(state.sort)+"  •  "+cobraVodFilterSummary(state),cobraModeColor("muted"),11,Gravity.LEFT|Gravity.CENTER_VERTICAL);copy.addView(summary);
    header.addView(copy,new LinearLayout.LayoutParams(0,dp(58),1));page.addView(header,new LinearLayout.LayoutParams(-1,dp(62)));

    LinearLayout tools=new LinearLayout(this);tools.setGravity(Gravity.CENTER_VERTICAL);
    Button sort=action("Sort  •  "+cobraVodSortLabel(state.sort));sort.setAllCaps(false);sort.setOnClickListener(v->cobraShowVodSortPicker(state));
    Button filter=action("Filter");filter.setAllCaps(false);filter.setOnClickListener(v->cobraShowVodFilters(state));
    Button clear=action("Clear");clear.setAllCaps(false);clear.setEnabled(!state.provider.isEmpty()||!"all".equals(state.watch)||state.myListOnly||!state.genre.isEmpty());
    clear.setOnClickListener(v->{state.provider="";state.watch="all";state.genre="";state.myListOnly=false;cobraRenderVodCollection(state);});
    tools.addView(sort,new LinearLayout.LayoutParams(0,dp(48),1));LinearLayout.LayoutParams fp=new LinearLayout.LayoutParams(0,dp(48),1);fp.leftMargin=dp(8);tools.addView(filter,fp);
    LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,dp(48),.7f);cp.leftMargin=dp(8);tools.addView(clear,cp);page.addView(tools,new LinearLayout.LayoutParams(-1,dp(54)));

    if(items.isEmpty()){
      TextView empty=text("No titles match these filters.",cobraModeColor("muted"),15,Gravity.CENTER);page.addView(empty,new LinearLayout.LayoutParams(-1,dp(100)));
      Button reset=action("Clear filters");reset.setAllCaps(false);reset.setOnClickListener(v->{state.provider="";state.watch="all";state.genre="";state.myListOnly=false;cobraRenderVodCollection(state);});page.addView(reset,new LinearLayout.LayoutParams(-1,dp(52)));
    }else{
      int columns=isCompact()?2:4,index=0;LinearLayout row=null;
      for(VodItem item:items){
        if(index%columns==0){row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);page.addView(row,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)));}
        View card=cobraVodCard(item,cobraVodContinueObject(item)!=null);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-1,1);lp.setMargins(dp(5),0,dp(5),0);row.addView(card,lp);index++;if(index>=160)break;
      }
    }
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraRefreshVodAmbientTrim();
  }

  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series){
    cobraRenderVodCollection(new CobraVodCollectionState(title,items,series));
  }

  private JSONObject cobraVodInfo(VodItem item)throws Exception{
    LiveSource source=sourceById(item.sourceId);if(source==null)return new JSONObject();
    String action=item.series?"get_series_info":"get_vod_info";String idKey=item.series?"series_id":"vod_id";
    JSONObject root=new JSONObject(httpGet(xtreamUrl(source,action)+"&"+idKey+"="+enc(item.id)));
    JSONObject info=root.optJSONObject("info");return info==null?new JSONObject():info;
  }

  private String cobraVodCollectionName(JSONObject info){
    if(info==null)return "";
    for(String key:new String[]{"belongs_to_collection","collection","collection_name","franchise"}){
      Object raw=info.opt(key);
      if(raw instanceof JSONObject){String name=((JSONObject)raw).optString("name","").trim();if(!name.isEmpty())return name;}
      else if(raw!=null){String name=String.valueOf(raw).trim();if(!name.isEmpty()&&!"null".equalsIgnoreCase(name)&&!"{}".equals(name))return name;}
    }
    return "";
  }

  private ArrayList<String> cobraVodPeople(JSONObject info){
    ArrayList<String> out=new ArrayList<>();if(info==null)return out;
    String joined=info.optString("cast",info.optString("actors",""));
    if(!joined.isEmpty())for(String part:joined.split("[,|/]")){String person=part.trim();if(person.length()>1&&!out.contains(person)){out.add(person);if(out.size()>=5)break;}}
    String director=info.optString("director","").trim();if(!director.isEmpty()&&!out.contains(director)&&out.size()<6)out.add(director);
    return out;
  }

  private ArrayList<VodItem> cobraVodRelatedItems(VodItem item){
    ArrayList<VodItem> catalog=cobraVodCatalog(item.series);ArrayList<VodItem> out=new ArrayList<>();
    String genre=cobraVodGenreLabel(item.category);
    for(VodItem candidate:catalog){
      if(cobraVodKey(candidate).equals(cobraVodKey(item)))continue;
      if((!genre.isEmpty()&&genre.equals(cobraVodGenreLabel(candidate.category)))||item.category.equalsIgnoreCase(candidate.category))out.add(candidate);
    }
    Collections.sort(out,(a,b)->{int rating=Double.compare(b.rating,a.rating);return rating!=0?rating:Long.compare(b.addedEpoch,a.addedEpoch);});
    if(out.size()>12)return new ArrayList<>(out.subList(0,12));return out;
  }

  private boolean cobraVodMetadataHasPerson(JSONObject info,String person){
    String hay=(info.optString("cast",info.optString("actors",""))+" "+info.optString("director","")).toLowerCase(Locale.US);
    return hay.contains(person.toLowerCase(Locale.US));
  }

  private void cobraBrowseVodPerson(VodItem item,String person){
    status("Finding "+person+"…");final ArrayList<VodItem> candidates=cobraVodCatalog(item.series);
    submitCobraIo(()->{
      ArrayList<VodItem> matches=new ArrayList<>();int inspected=0;
      for(VodItem candidate:candidates){
        if(cobraVodKey(candidate).equals(cobraVodKey(item)))continue;
        if(inspected++>=48||matches.size()>=18)break;
        try{if(cobraVodMetadataHasPerson(cobraVodInfo(candidate),person))matches.add(candidate);}catch(Exception ignored){}
      }
      runOnUiThread(()->{status("Ready");if(matches.isEmpty())toast("No other enabled-provider titles found for "+person);else cobraShowVodCollection(person,matches,item.series);});
    });
  }

  private void cobraBrowseVodCollectionMetadata(VodItem item,String collection){
    status("Finding collection…");final ArrayList<VodItem> candidates=cobraVodCatalog(item.series);
    submitCobraIo(()->{
      ArrayList<VodItem> matches=new ArrayList<>();int inspected=0;
      for(VodItem candidate:candidates){
        if(!candidate.sourceId.equals(item.sourceId))continue;
        if(inspected++>=56||matches.size()>=24)break;
        try{if(collection.equalsIgnoreCase(cobraVodCollectionName(cobraVodInfo(candidate))))matches.add(candidate);}catch(Exception ignored){}
      }
      runOnUiThread(()->{status("Ready");if(matches.size()<2)toast("No additional collection titles were returned by this provider");else cobraShowVodCollection(collection,matches,item.series);});
    });
  }

  private void cobraRenderVodDetails(VodItem item,JSONObject info){
    LiveSource source=sourceById(item.sourceId);if(source==null)return;
    String description=info.optString("plot",info.optString("description",""));
    String year=info.optString("releasedate",info.optString("year",item.year));
    String rating=info.optString("rating",item.rating>0.0?String.format(Locale.US,"%.1f",item.rating):"");
    String runtime=info.optString("duration",info.optString("duration_secs",""));
    String genre=info.optString("genre",item.category);String collection=cobraVodCollectionName(info);
    String metadata=(year.isEmpty()?"":year)+(rating.isEmpty()?"":((year.isEmpty()?"":"  •  ")+rating+" ★"));
    if(!runtime.isEmpty())metadata+=(metadata.isEmpty()?"":"  •  ")+runtime;
    if(!genre.isEmpty())metadata+=(metadata.isEmpty()?"":"  •  ")+genre;
    metadata+=(metadata.isEmpty()?"":"\n")+"Available via "+source.name;
    LinearLayout rows=cobraOpenSheet(item.title,metadata,"vod-details");boolean dark=cobraSheetIsDark();
    if(!description.trim().isEmpty()){TextView plot=cobraInfoText(rows,description.trim());plot.setMaxLines(8);}
    rows.addView(cobraSheetRow(item.series?"television":"play",item.series?"Browse Episodes":"Play",item.series?"Seasons and episodes":"Start playback",false,dark,()->{if(item.series)openSeries(item);else playMovie(item);}));
    boolean listed=cobraVodWatchlistContains(item);
    rows.addView(cobraSheetRow("favorite",listed?"✓ In My List":"+ My List",listed?"Tap to remove":"Save for later",false,dark,()->{toggleWatchlist(item);cobraShowVodDetails(item);}));
    if(!collection.isEmpty())rows.addView(cobraSheetRow("film","Collection  •  "+collection,"Browse titles returned with the same collection metadata",false,dark,()->cobraBrowseVodCollectionMetadata(item,collection)));
    ArrayList<String> people=cobraVodPeople(info);
    if(!people.isEmpty()){
      cobraInfoText(rows,"Cast & Crew");
      for(String person:people)rows.addView(cobraSheetRow("search",person,"Find other titles in enabled providers",false,dark,()->cobraBrowseVodPerson(item,person)));
    }
    ArrayList<VodItem> related=cobraVodRelatedItems(item);
    if(!related.isEmpty()){
      cobraInfoText(rows,"More Like This");int count=Math.min(6,related.size());
      for(int i=0;i<count;i++){VodItem relatedItem=related.get(i);rows.addView(cobraSheetRow(relatedItem.series?"television":"film",relatedItem.title,cobraVodCardMeta(relatedItem),false,dark,()->cobraShowVodDetails(relatedItem)));}
      if(related.size()>6)rows.addView(cobraSheetRow("more","See all similar titles",related.size()+" available",false,dark,()->cobraShowVodCollection("More Like This",related,item.series)));
    }
  }

  private void cobraShowVodDetails(VodItem item){
    LiveSource source=sourceById(item.sourceId);if(source==null)return;status("Loading details…");
    submitCobraIo(()->{
      JSONObject info;try{info=cobraVodInfo(item);}catch(Exception ignored){info=new JSONObject();}
      final JSONObject ready=info;runOnUiThread(()->{status("Ready");cobraRenderVodDetails(item,ready);});
    });
  }

  private VodItem cobraEpisodeFromJson(LiveSource source,VodItem parent,String seasonKey,int fallbackIndex,JSONObject episode){
    String id=episode.optString("id","");if(id.isEmpty())return null;
    JSONObject info=episode.optJSONObject("info");if(info==null)info=new JSONObject();
    int season=episode.optInt("season",0);if(season<=0)try{season=Integer.parseInt(seasonKey.replaceAll("[^0-9]",""));}catch(Exception ignored){}
    int number=episode.optInt("episode_num",episode.optInt("episode",fallbackIndex+1));if(number<=0)number=fallbackIndex+1;
    String title=episode.optString("title",info.optString("name","Episode "+number));
    String thumb=info.optString("movie_image",info.optString("cover_big",info.optString("poster_path",episode.optString("movie_image",""))));
    String air=info.optString("releasedate",info.optString("releaseDate",info.optString("air_date",episode.optString("releasedate",""))));
    String plot=info.optString("plot",info.optString("description",""));
    double rating=0.0;try{rating=Double.parseDouble(info.optString("rating",episode.optString("rating","0")));}catch(Exception ignored){}
    String label=String.format(Locale.US,"S%02dE%02d • %s",Math.max(0,season),Math.max(1,number),title);
    return new VodItem(source.id,id,label,parent.title,thumb,sanitizeExtension(episode.optString("container_extension","mp4")),false,0L,rating,air,season,number,air,plot,parent.title);
  }

  private ArrayList<VodItem> cobraSeriesEpisodes(JSONObject root,LiveSource source,VodItem parent){
    ArrayList<VodItem> episodes=new ArrayList<>();Object raw=root.opt("episodes");
    if(raw instanceof JSONObject){
      JSONObject seasons=(JSONObject)raw;ArrayList<String> keys=new ArrayList<>();java.util.Iterator<String> it=seasons.keys();while(it.hasNext())keys.add(it.next());
      Collections.sort(keys,(a,b)->{try{return Integer.compare(Integer.parseInt(a.replaceAll("[^0-9]","")),Integer.parseInt(b.replaceAll("[^0-9]","")));}catch(Exception ignored){return a.compareToIgnoreCase(b);}});
      for(String season:keys){JSONArray list=seasons.optJSONArray(season);if(list==null)continue;for(int i=0;i<list.length();i++){JSONObject e=list.optJSONObject(i);if(e==null)continue;VodItem ep=cobraEpisodeFromJson(source,parent,season,i,e);if(ep!=null)episodes.add(ep);}}
    }else if(raw instanceof JSONArray){
      JSONArray list=(JSONArray)raw;for(int i=0;i<list.length();i++){JSONObject e=list.optJSONObject(i);if(e==null)continue;VodItem ep=cobraEpisodeFromJson(source,parent,String.valueOf(e.optInt("season",1)),i,e);if(ep!=null)episodes.add(ep);}
    }
    Collections.sort(episodes,(a,b)->{int season=Integer.compare(a.seasonNumber,b.seasonNumber);return season!=0?season:Integer.compare(a.episodeNumber,b.episodeNumber);});return episodes;
  }

  private JSONObject cobraSeriesResumeObject(VodItem parent){return cobraVodContinueObject(parent);}

  private VodItem cobraSeriesResumeEpisode(VodItem parent,ArrayList<VodItem> episodes){
    JSONObject resume=cobraSeriesResumeObject(parent);if(resume==null)return null;String key=resume.optString("key","");
    for(VodItem ep:episodes)if(cobraVodKey(ep).equals(key))return ep;return null;
  }

  private VodItem cobraSeriesNextEpisode(VodItem parent,ArrayList<VodItem> episodes){
    VodItem resume=cobraSeriesResumeEpisode(parent,episodes);
    if(resume!=null){int index=episodes.indexOf(resume);if(index>=0&&index+1<episodes.size())return episodes.get(index+1);}
    int last=-1;for(int i=0;i<episodes.size();i++)if(cobraVodWatched(episodes.get(i)))last=i;
    int next=last+1;return next>=0&&next<episodes.size()?episodes.get(next):null;
  }

  private String cobraEpisodeProgressLabel(VodItem episode){
    if(cobraVodWatched(episode))return "✓ Watched";
    JSONObject progress=cobraVodContinueObject(episode);if(progress!=null){long p=progress.optLong("position",0L),d=progress.optLong("duration",0L);if(d>0)return Math.min(99,(p*100L)/d)+"% watched";return "Resume";}
    return "Unwatched";
  }

  private void cobraPlaySeriesEpisode(VodItem parent,VodItem episode,ArrayList<VodItem> episodes){
    LiveSource source=sourceById(episode.sourceId);if(source==null)return;
    mCobraActiveSeriesItem=parent;mEpisodeQueue.clear();mEpisodeQueue.addAll(episodes);mEpisodeQueueIndex=episodes.indexOf(episode);
    String url=source.server+"/series/"+encPath(source.username)+"/"+encPath(source.password)+"/"+encPath(episode.id)+"."+episode.extension;
    playVodUrl(episode,url,parent.title);
  }

  private View cobraEpisodeRow(VodItem parent,VodItem episode,ArrayList<VodItem> all){
    LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(8),dp(8),dp(8),dp(8));
    row.setBackground(cobraVodTrimDrawable("card"));
    android.widget.ImageView thumb=new android.widget.ImageView(this);thumb.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);thumb.setBackground(surface(cobraVodAmbientPanelColor(),12,cobraVodAmbientTrimColor(),1));
    cobraLoadVodArtwork(thumb,episode.icon);row.addView(thumb,new LinearLayout.LayoutParams(dp(isCompact()?116:148),dp(isCompact()?72:88)));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);copy.setPadding(dp(12),0,dp(8),0);
    String clean=episode.title.replaceFirst("^S\\d+E\\d+\\s*•\\s*","");
    TextView title=text(String.format(Locale.US,"S%02d · E%02d  %s",episode.seasonNumber,episode.episodeNumber,clean),cobraModeColor("text"),13,Gravity.LEFT);title.setMaxLines(2);title.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(title,new LinearLayout.LayoutParams(-1,dp(38)));
    String meta=cobraEpisodeProgressLabel(episode);if(!episode.airDate.isEmpty())meta+="  •  "+episode.airDate;
    TextView sub=text(meta,cobraModeColor("muted"),10,Gravity.LEFT|Gravity.CENTER_VERTICAL);copy.addView(sub,new LinearLayout.LayoutParams(-1,dp(24)));
    if(!episode.description.isEmpty()){TextView plot=text(episode.description,cobraModeColor("muted"),10,Gravity.LEFT);plot.setMaxLines(2);plot.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(plot,new LinearLayout.LayoutParams(-1,dp(34)));}
    JSONObject progress=cobraVodContinueObject(episode);if(progress!=null){long p=progress.optLong("position",0),d=progress.optLong("duration",0);if(d>0){android.widget.ProgressBar bar=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(100);bar.setProgress((int)Math.min(99,p*100L/d));copy.addView(bar,new LinearLayout.LayoutParams(-1,dp(3)));}}
    row.addView(copy,new LinearLayout.LayoutParams(0,-2,1));
    Button play=action(cobraVodContinueObject(episode)!=null?"Resume":"Play");play.setAllCaps(false);play.setOnClickListener(v->cobraPlaySeriesEpisode(parent,episode,all));row.addView(play,new LinearLayout.LayoutParams(dp(88),dp(48)));
    return row;
  }

  private void cobraRenderSeasonEpisodes(LinearLayout container,VodItem parent,ArrayList<VodItem> all,int season){
    container.removeAllViews();int shown=0;
    for(VodItem episode:all)if(episode.seasonNumber==season){container.addView(cobraEpisodeRow(parent,episode,all),new LinearLayout.LayoutParams(-1,-2));shown++;}
    if(shown==0)container.addView(text("No episodes returned for this season.",cobraModeColor("muted"),14,Gravity.CENTER),new LinearLayout.LayoutParams(-1,dp(100)));
  }

  private void cobraShowSeriesBrowser(VodItem parent,JSONObject root,ArrayList<VodItem> episodes){
    mCobraInternalScreen="internal";mCobraActiveSeriesItem=parent;mEpisodeQueue.clear();mEpisodeQueue.addAll(episodes);mEpisodeQueueIndex=-1;
    clearStage("COBRA • "+parent.title.toUpperCase(Locale.US));
    LinkedHashMap<Integer,Integer> seasons=new LinkedHashMap<>();for(VodItem ep:episodes)seasons.put(ep.seasonNumber,seasons.getOrDefault(ep.seasonNumber,0)+1);
    status(seasons.size()+" season"+(seasons.size()==1?"":"s")+"  •  "+episodes.size()+" episodes");
    ScrollView scroll=new ScrollView(this);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(dp(isCompact()?8:14),dp(6),dp(isCompact()?8:14),dp(24));scroll.addView(page);
    Button back=action("‹  Back to Shows");back.setAllCaps(false);back.setOnClickListener(v->showSeries());page.addView(back,new LinearLayout.LayoutParams(-1,dp(48)));
    JSONObject info=root.optJSONObject("info");if(info==null)info=new JSONObject();String plot=info.optString("plot",info.optString("description",""));
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);View edge=cobraTrackVodTrim(new View(this),"section");LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(dp(4),dp(34));ep.rightMargin=dp(10);heading.addView(edge,ep);
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);TextView title=text(parent.title,cobraModeColor("text"),22,Gravity.LEFT);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));copy.addView(title);
    if(!plot.isEmpty()){TextView synopsis=text(plot,cobraModeColor("muted"),11,Gravity.LEFT);synopsis.setMaxLines(3);synopsis.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(synopsis);}heading.addView(copy,new LinearLayout.LayoutParams(0,-2,1));page.addView(heading,new LinearLayout.LayoutParams(-1,-2));
    LinearLayout actions=new LinearLayout(this);VodItem resume=cobraSeriesResumeEpisode(parent,episodes),next=cobraSeriesNextEpisode(parent,episodes);
    if(resume!=null){Button resumeButton=action("Resume Episode");resumeButton.setAllCaps(false);resumeButton.setOnClickListener(v->cobraPlaySeriesEpisode(parent,resume,episodes));actions.addView(resumeButton,new LinearLayout.LayoutParams(0,dp(48),1));}
    if(next!=null){Button nextButton=action("Play Next Episode");nextButton.setAllCaps(false);nextButton.setOnClickListener(v->cobraPlaySeriesEpisode(parent,next,episodes));LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(0,dp(48),1);if(actions.getChildCount()>0)np.leftMargin=dp(8);actions.addView(nextButton,np);}
    Button list=action(cobraVodWatchlistContains(parent)?"✓ In My List":"+ My List");list.setAllCaps(false);list.setOnClickListener(v->{toggleWatchlist(parent);list.setText(cobraVodWatchlistContains(parent)?"✓ In My List":"+ My List");});LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(48),1);if(actions.getChildCount()>0)lp.leftMargin=dp(8);actions.addView(list,lp);page.addView(actions,new LinearLayout.LayoutParams(-1,dp(56)));
    android.widget.HorizontalScrollView seasonScroll=new android.widget.HorizontalScrollView(this);seasonScroll.setHorizontalScrollBarEnabled(false);LinearLayout chips=new LinearLayout(this);chips.setOrientation(LinearLayout.HORIZONTAL);seasonScroll.addView(chips,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));page.addView(seasonScroll,new LinearLayout.LayoutParams(-1,dp(58)));
    LinearLayout episodesHost=new LinearLayout(this);episodesHost.setOrientation(LinearLayout.VERTICAL);page.addView(episodesHost,new LinearLayout.LayoutParams(-1,-2));
    int firstSeason=seasons.isEmpty()?1:seasons.keySet().iterator().next();for(Integer season:seasons.keySet()){Button chip=action("Season "+season);chip.setAllCaps(false);chip.setOnClickListener(v->cobraRenderSeasonEpisodes(episodesHost,parent,episodes,season));LinearLayout.LayoutParams chipLp=new LinearLayout.LayoutParams(dp(116),dp(48));chipLp.rightMargin=dp(8);chips.addView(chip,chipLp);}cobraRenderSeasonEpisodes(episodesHost,parent,episodes,firstSeason);
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraRefreshVodAmbientTrim();
  }

  private void openSeries(VodItem item){
    if(!isCobraAsyncAlive())return;LiveSource source=sourceById(item.sourceId);if(source==null)return;status("Loading seasons & episodes…");final long ticket=mCobraNavigation.advance();
    submitCobraIo(()->{
      try{
        JSONObject root=new JSONObject(httpGet(xtreamUrl(source,"get_series_info")+"&series_id="+enc(item.id)));ArrayList<VodItem> episodes=cobraSeriesEpisodes(root,source,item);
        cobraPublishNavigation(ticket,()->{if(episodes.isEmpty()){showError("Series","Provider returned no episodes.");return;}cobraShowSeriesBrowser(item,root,episodes);});
      }catch(Exception e){cobraPublishNavigation(ticket,()->showError("Series","Could not load episodes from this provider."));}
    });
  }

  private void cobraShowVodCompletion(){
    if(mCobraCurrentVodItem==null||mPlayingVodKey.isEmpty())return;final VodItem finished=mCobraCurrentVodItem;
    boolean episode=!finished.parentTitle.isEmpty();boolean dark=true;LinearLayout rows=cobraOpenSheet("Finished",episode?finished.parentTitle:finished.title,"vod-complete");
    if(episode&&mCobraActiveSeriesItem!=null){rows.addView(cobraSheetRow("television","Back to Show","Return to seasons & episodes",false,dark,()->{closePlayer();openSeries(mCobraActiveSeriesItem);}));rows.addView(cobraSheetRow("back","Back to Shows",null,false,dark,()->{closePlayer();showSeries();}));}
    else{
      ArrayList<VodItem> related=cobraVodRelatedItems(finished);rows.addView(cobraSheetRow("back","Back to Movies",null,false,dark,()->{closePlayer();showMovies();}));
      if(!related.isEmpty())rows.addView(cobraSheetRow("film","More Like This",related.size()+" related titles",false,dark,()->{closePlayer();cobraShowVodCollection("More Like This",related,false);}));
    }
  }
