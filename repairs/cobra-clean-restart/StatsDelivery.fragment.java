    /** Optional projection of the existing summary; original detailed lines remain intact. */
    final class SummaryMetadata {
      String venue="",location="",situation="",progress="",phase="";boolean valid;
      final ArrayList<String[]> teamStats=new ArrayList<>();
    }
    SummaryMetadata readSummaryMetadata(CobraSportsGame game,JSONObject root) {
      SummaryMetadata out=new SummaryMetadata();JSONObject header=root==null?null:root.optJSONObject("header");
      if(game==null||header==null||!game.id.equals(header.optString("id","")))return out;
      out.valid=true;JSONArray competitions=header.optJSONArray("competitions");JSONObject competition=competitions==null?null:competitions.optJSONObject(0);
      JSONObject info=root.optJSONObject("gameInfo"),venue=info==null?null:info.optJSONObject("venue");if(venue==null&&competition!=null)venue=competition.optJSONObject("venue");
      if(venue!=null){
        out.venue=venue.optString("fullName","");JSONObject address=venue.optJSONObject("address");ArrayList<String> parts=new ArrayList<>();
        if(address!=null)for(String key:new String[]{"city","state","country"}){String value=address.optString(key,"").trim();if(!value.isEmpty()&&!parts.contains(value))parts.add(value);}
        out.location=android.text.TextUtils.join(", ",parts);
      }
      JSONObject status=competition==null?null:competition.optJSONObject("status"),type=status==null?null:status.optJSONObject("type");
      if(type!=null){out.progress=type.optString("shortDetail",type.optString("detail",""));out.phase=type.optString("state","");}
      JSONObject situation=competition==null?null:competition.optJSONObject("situation");if(situation==null)situation=root.optJSONObject("situation");
      if(situation!=null){
        out.situation=situation.optString("downDistanceText","");String possession=situation.optString("possessionText","");
        if(possession.isEmpty()){
          String id=situation.optString("possession","");
          if(game.home!=null&&!id.isEmpty()&&id.equals(game.home.id))possession=game.home.name+" possession";
          else if(game.away!=null&&!id.isEmpty()&&id.equals(game.away.id))possession=game.away.name+" possession";
        }
        if(!possession.isEmpty())out.situation+=(out.situation.isEmpty()?"":" • ")+possession;
      }
      // A scheduled summary may contain season averages despite boxscoreAvailable=false.
      // Never label those as this game's live boxscore; original detail lines remain available below.
      if("pre".equals(out.phase)||(competition!=null&&competition.has("boxscoreAvailable")&&!competition.optBoolean("boxscoreAvailable")))return out;
      JSONObject box=root.optJSONObject("boxscore");JSONArray teams=box==null?null:box.optJSONArray("teams");LinkedHashMap<String,String[]> paired=new LinkedHashMap<>();
      if(teams!=null)for(int i=0;i<teams.length();i++){
        JSONObject row=teams.optJSONObject(i),team=row==null?null:row.optJSONObject("team");String id=team==null?"":team.optString("id","");
        int column=game.away!=null&&id.equals(game.away.id)?1:game.home!=null&&id.equals(game.home.id)?2:0;if(column==0)continue;
        JSONArray stats=row.optJSONArray("statistics");if(stats==null)continue;
        for(int j=0;j<stats.length();j++){
          JSONObject stat=stats.optJSONObject(j);if(stat==null)continue;String name=stat.optString("name",""),label=stat.optString("label",name),value=stat.optString("displayValue","");
          if(label.isEmpty()||value.isEmpty())continue;if(name.isEmpty())name=label;if(!paired.containsKey(name)&&paired.size()>=24)continue;
          String[] values=paired.get(name);if(values==null){values=new String[]{label,"",""};paired.put(name,values);}values[column]=value;
        }
      }
      out.teamStats.addAll(paired.values());return out;
    }
    void statsTeams(LinearLayout rows,CobraSportsGame game,boolean fullscreen) {
      if(!fullscreen){team(rows,game.away,"Away");team(rows,game.home,"Home");return;}
      TextView match=cobraText(cobraSportsMatchup(game),Color.WHITE,21);match.setTypeface(Typeface.DEFAULT_BOLD);rows.addView(match,new LinearLayout.LayoutParams(-1,-2));
      TextView league=cobraText(game.leagueLabel,0xff9fbcca,12);league.setPadding(0,dp(4),0,dp(10));rows.addView(league,new LinearLayout.LayoutParams(-1,-2));
      LinearLayout pair=new LinearLayout(InfinityLiveActivity.this);pair.setGravity(Gravity.TOP);CobraSportsTeam[] teams={game.away,game.home};String[] sides={"AWAY TEAM","HOME TEAM"};
      for(int i=0;i<2;i++){
        CobraSportsTeam team=teams[i];LinearLayout card=new LinearLayout(InfinityLiveActivity.this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(8),dp(8),dp(8),dp(8));card.setBackground(cobraPanelSurface(0x2216222b,10,0x554ebad1));
        TextView side=cobraText(sides[i],0xff9fc6d6,11);card.addView(side,new LinearLayout.LayoutParams(-1,-2));LinearLayout mark=new LinearLayout(InfinityLiveActivity.this);mark.setGravity(Gravity.CENTER_VERTICAL);
        android.widget.ImageView logo=new android.widget.ImageView(InfinityLiveActivity.this);logo.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);logo.setContentDescription(team==null?sides[i]:(team.name+" logo"));mark.addView(logo,new LinearLayout.LayoutParams(dp(44),dp(48)));if(team!=null)cobraSportsLoadLogo(team.logo,logo);
        TextView name=cobraText(team==null?"Unavailable":team.name,Color.WHITE,15);name.setMaxLines(3);name.setPadding(dp(6),0,0,0);mark.addView(name,new LinearLayout.LayoutParams(0,-2,1));card.addView(mark,new LinearLayout.LayoutParams(-1,-2));
        if(team!=null&&!team.record.isEmpty()){TextView record=cobraText(team.record,0xffaabfcb,12);card.addView(record,new LinearLayout.LayoutParams(-1,-2));}
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-2,1);if(i==0)lp.rightMargin=dp(6);pair.addView(card,lp);
      }
      rows.addView(pair,new LinearLayout.LayoutParams(-1,-2));
    }
    void statsTable(LinearLayout rows,CobraSportsGame game,SummaryMetadata data) {
      if(data==null||data.teamStats.isEmpty())return;LinearLayout head=new LinearLayout(InfinityLiveActivity.this);
      statsTableRow(head,new String[]{"Team Stats",game.away==null?"Away":game.away.abbreviation,game.home==null?"Home":game.home.abbreviation},true);rows.addView(head,new LinearLayout.LayoutParams(-1,-2));
      for(String[] values:data.teamStats){LinearLayout row=new LinearLayout(InfinityLiveActivity.this);statsTableRow(row,values,false);rows.addView(row,new LinearLayout.LayoutParams(-1,-2));}
    }
    void statsTableRow(LinearLayout row,String[] values,boolean heading) {
      row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,dp(7),0,dp(7));
      for(int i=0;i<3;i++){TextView text=cobraText(values[i].isEmpty()?"—":values[i],heading?Color.WHITE:0xffc2d0df,13);text.setMaxLines(3);if(heading)text.setTypeface(Typeface.DEFAULT_BOLD);if(i>0)text.setGravity(Gravity.CENTER);row.addView(text,new LinearLayout.LayoutParams(0,-2,i==0?2.2f:1f));}
    }
    final class StatsSession implements Runnable,View.OnAttachStateChangeListener {
      final CobraSportsGame original;final String profile;final View owner;final LinearLayout rows;final boolean fullscreen;
      CobraSportsSummary summary;long receivedAt;boolean failed,closed;String rendered="";
      StatsSession(CobraSportsGame game,String profile,View owner,LinearLayout rows,boolean fullscreen){this.original=game;this.profile=profile;this.owner=owner;this.rows=rows;this.fullscreen=fullscreen;}
      boolean current(){return !closed&&owner==mCobraActionSheet&&owner.isAttachedToWindow()&&sports()&&profile.equals(mFeatures.activeProfileId());}
      @Override public void onViewAttachedToWindow(View view){}
      @Override public void onViewDetachedFromWindow(View view){closed=true;mMain.removeCallbacks(this);summary=null;}
      @Override public void run(){
        mMain.removeCallbacks(this);if(!current())return;CobraSportsGame game=cobraSportsGame(original.id);if(game==null)game=original;
        boolean hidden=cobraSportsHidden(game),delayed=cobraSportsDelayed(game);long age=System.currentTimeMillis()-receivedAt;SummaryMetadata meta=summary==null?null:summary.proData;
        boolean invalid=meta!=null&&(!meta.valid||(!meta.phase.isEmpty()&&!meta.phase.equals(game.state)));
        boolean detailsFresh=summary!=null&&(game.finalGame()||(age>=0&&age<=COBRA_SPORTS_STALE_MS))&&!delayed&&!invalid;
        String signature=hidden+"|"+delayed+"|"+detailsFresh+"|"+failed+"|"+cobraSportsScoreLine(game)+"|"+cobraSportsMeta(game)+"|"+(summary==null?"loading":summary.lines.toString());
        if(!signature.equals(rendered)){
          rendered=signature;rows.removeAllViews();statsTeams(rows,game,fullscreen);String venue=meta!=null&&!meta.venue.isEmpty()?meta.venue:game.venue;
          cobraInfoText(rows,"Venue • "+(venue.isEmpty()?"Unavailable":venue));if(meta!=null&&!meta.location.isEmpty())cobraInfoText(rows,"Location • "+meta.location);
          cobraInfoText(rows,"Kickoff • "+(game.timeConfirmed?cobraSportsClock(game.startMs):"Time TBA"));cobraInfoText(rows,cobraSportsScoreLine(game));cobraInfoText(rows,cobraSportsMeta(game));
          if(hidden)cobraInfoText(rows,"Scores and statistics are hidden by Spoiler Protection.");
          else if(delayed||(summary!=null&&!detailsFresh))cobraInfoText(rows,"Statistics delayed • current game data is unavailable.");
          else if(failed)cobraInfoText(rows,"Statistics are unavailable right now.");
          else if(summary==null)cobraInfoText(rows,"Loading game statistics…");
          else{
            if(meta!=null&&!meta.progress.isEmpty())cobraInfoText(rows,meta.progress);if(meta!=null&&!meta.situation.isEmpty())cobraInfoText(rows,meta.situation);
            if(fullscreen)statsTable(rows,game,meta);if(game.upcoming())cobraInfoText(rows,"Pre-game team statistics");
            for(String line:summary.lines)cobraInfoText(rows,line);
          }
        }
        if(current())mMain.postDelayed(this,1000L);
      }
    }
    boolean stats(CobraSportsGame game) {
      if(!sports()||game==null||cobraSportsHidden(game))return false;final LinearLayout rows;final View owner;boolean fullscreen=mPlayerOverlay!=null;
      if(!fullscreen){rows=cobraOpenSheet("Stats • "+cobraSportsMatchup(game),"Game information and detailed statistics","sports-stats");owner=mCobraActionSheet;}
      else{rows=new LinearLayout(InfinityLiveActivity.this);rows.setOrientation(LinearLayout.VERTICAL);rows.setPadding(dp(12),dp(8),dp(12),dp(12));android.widget.ScrollView scroll=new android.widget.ScrollView(InfinityLiveActivity.this);scroll.setFillViewport(false);scroll.addView(rows,new FrameLayout.LayoutParams(-1,-2));owner=panel("Stats","sports-stats",scroll,0);}
      statsOwner=owner;final StatsSession session=new StatsSession(game,mFeatures.activeProfileId(),owner,rows,fullscreen);owner.addOnAttachStateChangeListener(session);session.run();
      boolean submitted=submitCobraIo(()->{
        try{final CobraSportsSummary result=mCobraSportsRepository.summary(game);final long received=System.currentTimeMillis();publishCobraUi(()->{if(!session.current())return;session.summary=result;session.receivedAt=received;session.run();});}
        catch(Exception error){publishCobraUi(()->{if(!session.current())return;session.failed=true;session.run();});}
      });
      if(!submitted){session.failed=true;session.run();}return true;
    }
