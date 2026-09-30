#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, difflib

ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
PARENT_ACTIVITY_SHA='9bc85e090e74d2c5e8c4170ae08978298863424725293ac3c86d0b6a349f72bd'
PARENT_APK='40de992889bda2c9f73862d2eee4937c252db10e5d9ca07777b4c4f9e37f4ad2'
PARENT_COMMIT='1aea5afdfe4bf7253e3db8bb869815651a9218b4'
PARENT_RUN=36759239156
VERSION_CODE=2103272
RELEASE='1.0.9-Sports-Polish-RC1'

ALLOWED_METHODS=[
  'cobraSportsPrepareHeader','cobraSportsRenderHub','cobraSportsAddSection',
  'cobraSportsAddLeagueSection','cobraSportsGameCard'
]

def sha(data): return hashlib.sha256(data).hexdigest()

def once(s,old,new):
    count=s.count(old)
    if count!=1: raise AssertionError(f'Expected one anchor, found {count}: {old[:120]!r}')
    return s.replace(old,new,1)

def method_span(s,name):
    needle=name+'('
    pos=0
    while True:
        start=s.find('\n  private ',pos)
        if start<0: raise AssertionError('Missing method declaration '+name)
        start+=1;line_end=s.find('\n',start)
        if line_end<0:line_end=len(s)
        line=s[start:line_end]
        if needle in line:
            p=start+line.index(needle);brace=s.find('{',p);depth=0
            for i in range(brace,len(s)):
                if s[i]=='{': depth+=1
                elif s[i]=='}':
                    depth-=1
                    if depth==0:return start,i+1
            raise AssertionError('Unclosed method '+name)
        pos=line_end

def replace_method(s,name,code):
    a,b=method_span(s,name)
    return s[:a]+code+s[b:]

HELPERS=r'''
  // 2103272 — presentation-only Sports Hub polish helpers. No data/player/provider ownership.
  private String cobraSportsHubSummary(int live,int upcoming){
    String refreshed=mCobraSportsLastRefresh==0?"WAITING FOR FIRST REFRESH":("UPDATED "+new SimpleDateFormat("h:mm a",Locale.US).format(new Date(mCobraSportsLastRefresh)).toUpperCase(Locale.US));
    if(mCobraSportsLoading)refreshed="UPDATING…";
    return live+" LIVE  •  "+upcoming+" UPCOMING  •  "+refreshed;
  }
  private String cobraSportsCardLine(CobraSportsGame game){
    if(game==null||game.home==null||game.away==null)return "";
    if(game.live()||game.finalGame())return cobraSportsScoreLine(game);
    return game.away.shortName+"  @  "+game.home.shortName;
  }
  private void cobraSportsStyleAction(Button button,boolean primary){
    boolean dark=cobraModeDark();button.setAllCaps(false);button.setMinHeight(dp(44));button.setTextSize(primary?13:12);
    button.setTypeface(Typeface.create("sans-serif-medium",primary?Typeface.BOLD:Typeface.NORMAL));
    if(primary){
      int normal=cobraAlpha(cobraModeColor("accent"),dark?72:42),focused=cobraAlpha(cobraModeColor("accent"),dark?185:130);
      button.setBackground(focusSurface(normal,focused,16));button.setTextColor(dark?Color.WHITE:cobraModeColor("text"));
    }else button.setBackground(cobraPhoneGlass(!dark,16,true));
  }
'''

PREPARE=r'''  private void cobraSportsPrepareHeader(){
    if(mHeader==null)return;
    mHeader.setText("☰  COBRA • SPORTS");mHeader.setClickable(true);mHeader.setFocusable(true);
    mHeader.setContentDescription("Open Cobra navigation drawer");mHeader.setTag("cobra_sports_drawer_header");
    mHeader.setOnClickListener(v->toggleCobraDrawer());CobraBrandDrawable brand=new CobraBrandDrawable();
    brand.setBounds(0,0,dp(40),dp(32));mHeader.setCompoundDrawablePadding(dp(8));mHeader.setCompoundDrawablesRelative(null,null,brand,null);
    if(mStatus!=null)mStatus.setVisibility("COBRA • SPORTS".equals(mCobraStageTitle)?View.GONE:View.VISIBLE);
  }'''

RENDER=r'''  private void cobraSportsRenderHub(){
    if(mStage==null)return;
    while(mStage.getChildCount()>2)mStage.removeViewAt(2);
    cobraSportsPrepareHeader();
    ArrayList<CobraSportsGame> all=new ArrayList<>(mCobraSportsGames);all.sort(cobraSportsComparator());
    ArrayList<CobraSportsGame> liveGames=new ArrayList<>(),favoriteGames=new ArrayList<>(),upcoming=new ArrayList<>();
    long now=System.currentTimeMillis();
    for(CobraSportsGame game:all){
      if(game.live())liveGames.add(game);
      if(cobraSportsFavoriteGame(game)&&game.startMs>now-86400000L)favoriteGames.add(game);
      if(game.upcoming()&&game.startMs>=now-3600000L)upcoming.add(game);
    }
    String summaryText=cobraSportsHubSummary(liveGames.size(),upcoming.size());status(summaryText);

    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setClipToPadding(false);
    LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(2),0,dp(2),dp(24));scroll.addView(body);

    TextView summary=cobraText(summaryText,cobraModeColor("muted"),12);summary.setTag("cobra_sports_summary");
    summary.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));summary.setLetterSpacing(.075f);
    summary.setGravity(Gravity.CENTER_VERTICAL);summary.setPadding(dp(8),0,dp(8),0);
    body.addView(summary,new LinearLayout.LayoutParams(-1,dp(32)));

    boolean dark=cobraModeDark(),compact=cobraWidthDp()<500;
    Button refresh=cobraTextButton(mCobraSportsLoading?"Updating…":"↻  Refresh",dark,()->cobraSportsRefresh(true));refresh.setEnabled(!mCobraSportsLoading);
    Button spoiler=cobraTextButton(cobraSportsHideScores()?"Scores Hidden":"Hide Scores",dark,()->{mPrefs.edit().putBoolean(COBRA_SPORTS_HIDE_SCORES,!cobraSportsHideScores()).apply();cobraSportsRenderCurrent();cobraSportsRefreshMultiOverlays();});
    Button multi=cobraTextButton("▦  Smart Multi-View",dark,()->cobraSportsOpenSmartMultiView("live",null));
    cobraSportsStyleAction(refresh,false);cobraSportsStyleAction(spoiler,false);cobraSportsStyleAction(multi,true);
    refresh.setTag("cobra_sports_refresh");spoiler.setTag("cobra_sports_hide_scores");multi.setTag("cobra_sports_smart_multiview");

    LinearLayout actionShell=new LinearLayout(this);actionShell.setGravity(Gravity.CENTER_VERTICAL);actionShell.setPadding(dp(6),dp(5),dp(6),dp(5));
    actionShell.setBackground(cobraPhoneGlass(!dark,19,true));actionShell.setTag("cobra_sports_action_bar");
    if(compact){
      android.widget.HorizontalScrollView actionScroll=new android.widget.HorizontalScrollView(this);actionScroll.setHorizontalScrollBarEnabled(false);actionScroll.setFillViewport(false);actionScroll.setClipToPadding(false);
      LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);actions.setGravity(Gravity.CENTER_VERTICAL);
      LinearLayout.LayoutParams small=new LinearLayout.LayoutParams(dp(116),dp(44));small.rightMargin=dp(6);actions.addView(refresh,small);
      LinearLayout.LayoutParams hide=new LinearLayout.LayoutParams(dp(128),dp(44));hide.rightMargin=dp(6);actions.addView(spoiler,hide);
      actions.addView(multi,new LinearLayout.LayoutParams(dp(176),dp(44)));actionScroll.addView(actions);actionShell.addView(actionScroll,new LinearLayout.LayoutParams(-1,dp(46)));
    }else{
      LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);actions.setGravity(Gravity.CENTER_VERTICAL);
      LinearLayout.LayoutParams a=new LinearLayout.LayoutParams(0,dp(44),1);a.rightMargin=dp(6);actions.addView(refresh,a);
      LinearLayout.LayoutParams b=new LinearLayout.LayoutParams(0,dp(44),1);b.rightMargin=dp(6);actions.addView(spoiler,b);
      actions.addView(multi,new LinearLayout.LayoutParams(0,dp(44),1.35f));actionShell.addView(actions,new LinearLayout.LayoutParams(-1,dp(46)));
    }
    LinearLayout.LayoutParams actionPosition=new LinearLayout.LayoutParams(-1,dp(56));actionPosition.bottomMargin=dp(8);body.addView(actionShell,actionPosition);

    if(mCobraSportsGames.isEmpty()){
      LinearLayout empty=new LinearLayout(this);empty.setOrientation(LinearLayout.VERTICAL);empty.setGravity(Gravity.CENTER);empty.setPadding(dp(16),dp(24),dp(16),dp(28));
      boolean failed=!mCobraSportsLastError.isEmpty(),never=mCobraSportsLastRefresh==0L;
      TextView title=cobraText(mCobraSportsLoading||never?"LOADING SPORTS…":failed?"SPORTS DATA UNAVAILABLE":"NO GAMES SCHEDULED",cobraModeColor("text"),21);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setGravity(Gravity.CENTER);
      TextView detail=cobraText(mCobraSportsLoading||never?"Connecting to the live sports feed…":failed?mCobraSportsLastError:"No games were returned for the current sports window.",cobraModeColor("muted"),13);detail.setGravity(Gravity.CENTER);
      empty.addView(title,new LinearLayout.LayoutParams(-1,-2));empty.addView(detail,new LinearLayout.LayoutParams(-1,-2));body.addView(empty,new LinearLayout.LayoutParams(-1,-2));
    }

    cobraSportsAddSection(body,"LIVE NOW",liveGames,12);
    cobraSportsAddSection(body,"MY TEAMS",favoriteGames,12);
    cobraSportsAddSection(body,"UPCOMING",upcoming,12);
    Set<String> enabled=cobraSportsEnabledLeagues();
    for(CobraSportsLeagueSpec spec:COBRA_SPORTS_SPECS)if(enabled.contains(spec.key)){
      ArrayList<CobraSportsGame> league=new ArrayList<>();for(CobraSportsGame game:all)if(spec.key.equals(game.leagueKey))league.add(game);
      cobraSportsAddLeagueSection(body,spec,league);
    }
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));body.post(()->cobraAnimateChildrenIn(body));
  }'''

ADD_SECTION=r'''  private void cobraSportsAddSection(LinearLayout body,String title,List<CobraSportsGame> games,int max){
    if(games==null||games.isEmpty())return;
    boolean liveSection="LIVE NOW".equals(title);
    LinearLayout headingRow=new LinearLayout(this);headingRow.setGravity(Gravity.CENTER_VERTICAL);headingRow.setPadding(dp(6),dp(3),dp(4),0);
    TextView heading=cobraText(title,liveSection?0xffff5069:cobraModeColor("text"),13);heading.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));heading.setLetterSpacing(.10f);
    headingRow.addView(heading,new LinearLayout.LayoutParams(0,dp(38),1));
    TextView count=cobraText(games.size()==1?"1 GAME":games.size()+" GAMES",cobraModeColor("muted"),10);count.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);count.setLetterSpacing(.08f);
    headingRow.addView(count,new LinearLayout.LayoutParams(dp(82),dp(38)));body.addView(headingRow,new LinearLayout.LayoutParams(-1,dp(40)));

    android.widget.HorizontalScrollView scroll=new android.widget.HorizontalScrollView(this);scroll.setHorizontalScrollBarEnabled(false);scroll.setClipToPadding(false);scroll.setPadding(0,0,dp(28),0);
    LinearLayout rail=new LinearLayout(this);rail.setOrientation(LinearLayout.HORIZONTAL);
    int countCards=Math.min(max,games.size());
    int cardWidth=liveSection?Math.max(dp(210),Math.min(dp(360),dp(cobraWidthDp()-44))):Math.max(dp(190),Math.min(dp(270),dp(cobraWidthDp()-74)));
    int cardHeight=dp(liveSection?202:150);
    for(int i=0;i<countCards;i++){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(cardWidth,cardHeight);p.rightMargin=dp(10);rail.addView(cobraSportsGameCard(games.get(i)),p);}
    scroll.addView(rail);LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,cardHeight+dp(10));rp.bottomMargin=dp(4);body.addView(scroll,rp);
  }'''

ADD_LEAGUE=r'''  private void cobraSportsAddLeagueSection(LinearLayout body,CobraSportsLeagueSpec spec,List<CobraSportsGame> games){
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(dp(6),dp(3),dp(2),0);
    TextView title=cobraText(spec.label.toUpperCase(Locale.US),cobraModeColor("text"),13);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setLetterSpacing(.10f);header.addView(title,new LinearLayout.LayoutParams(0,dp(38),1));
    Button open=cobraTextButton("See All  ›",cobraModeDark(),()->showCobraSportsLeague(spec.key));open.setTextSize(11);open.setTag("cobra_sports_league_all:"+spec.key);header.addView(open,new LinearLayout.LayoutParams(dp(104),dp(38)));body.addView(header,new LinearLayout.LayoutParams(-1,dp(40)));
    if(games==null||games.isEmpty()){
      TextView empty=cobraText("No games in the current window",cobraModeColor("muted"),12);empty.setPadding(dp(8),dp(2),dp(8),dp(10));body.addView(empty,new LinearLayout.LayoutParams(-1,dp(34)));return;
    }
    android.widget.HorizontalScrollView scroll=new android.widget.HorizontalScrollView(this);scroll.setHorizontalScrollBarEnabled(false);scroll.setClipToPadding(false);scroll.setPadding(0,0,dp(28),0);
    LinearLayout rail=new LinearLayout(this);rail.setOrientation(LinearLayout.HORIZONTAL);
    int width=Math.max(dp(190),Math.min(dp(270),dp(cobraWidthDp()-74))),height=dp(150);
    for(int i=0;i<Math.min(10,games.size());i++){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(width,height);p.rightMargin=dp(10);rail.addView(cobraSportsGameCard(games.get(i)),p);}
    scroll.addView(rail);LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,height+dp(10));rp.bottomMargin=dp(2);body.addView(scroll,rp);
  }'''

GAME_CARD=r'''  private View cobraSportsGameCard(CobraSportsGame game){
    boolean dark=cobraModeDark(),live=game.live(),upcoming=game.upcoming();
    LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(live?16:13),dp(10),dp(live?16:13),dp(10));
    card.setBackground(cobraPhoneGlass(!dark,live?24:20,true));card.setFocusable(true);card.setClickable(true);card.setElevation(dp(live?4:2));card.setTag("cobra-sports-game:"+game.id);

    LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);
    TextView league=cobraText(game.leagueLabel,cobraModeColor("accent"),11);league.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));league.setLetterSpacing(.09f);top.addView(league,new LinearLayout.LayoutParams(0,dp(26),1));
    if(live){
      TextView pill=cobraText("●  LIVE",Color.WHITE,11);pill.setGravity(Gravity.CENTER);pill.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));pill.setBackground(surface(0xffef2447,14,0xffff6b80,1));pill.setTag("cobra_sports_live_pill");
      top.addView(pill,new LinearLayout.LayoutParams(dp(72),dp(26)));
    }
    card.addView(top,new LinearLayout.LayoutParams(-1,dp(28)));

    LinearLayout marks=new LinearLayout(this);marks.setGravity(Gravity.CENTER_VERTICAL);
    int logo=dp(live?48:38);marks.addView(cobraSportsTeamMark(game.away),new LinearLayout.LayoutParams(logo,logo));
    TextView versus=cobraText("  "+(game.away==null?"AWAY":game.away.abbreviation)+"   @   "+(game.home==null?"HOME":game.home.abbreviation)+"  ",cobraModeColor("text"),live?19:16);
    versus.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));versus.setGravity(Gravity.CENTER);marks.addView(versus,new LinearLayout.LayoutParams(0,dp(live?52:44),1));
    marks.addView(cobraSportsTeamMark(game.home),new LinearLayout.LayoutParams(logo,logo));card.addView(marks,new LinearLayout.LayoutParams(-1,dp(live?56:46)));

    String center=cobraSportsCardLine(game);TextView score=cobraText(center,cobraModeColor("text"),live?24:14);score.setGravity(Gravity.CENTER);
    score.setTypeface(Typeface.create("sans-serif-medium",live?Typeface.BOLD:Typeface.NORMAL));score.setTag(upcoming?"cobra_sports_upcoming_matchup":"cobra_sports_score");
    card.addView(score,new LinearLayout.LayoutParams(-1,dp(live?42:30)));

    TextView meta=cobraText(cobraSportsMeta(game),cobraModeColor("muted"),live?12:11);meta.setGravity(Gravity.CENTER);meta.setMaxLines(2);meta.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));
    card.addView(meta,new LinearLayout.LayoutParams(-1,0,1));
    card.setContentDescription(cobraSportsMatchup(game)+", "+cobraSportsMeta(game));card.setOnClickListener(v->showCobraSportsGame(game.id));cobraPolishFocusable(card);return card;
  }'''

def patch_activity(s):
    # helper block is additive and presentation-only.
    anchor='  private void showCobraSportsHub(){'
    if HELPERS not in s:s=once(s,anchor,HELPERS+'\n'+anchor)
    s=replace_method(s,'cobraSportsPrepareHeader',PREPARE)
    s=replace_method(s,'cobraSportsRenderHub',RENDER)
    s=replace_method(s,'cobraSportsAddSection',ADD_SECTION)
    s=replace_method(s,'cobraSportsAddLeagueSection',ADD_LEAGUE)
    s=replace_method(s,'cobraSportsGameCard',GAME_CARD)
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    shell=a.root/'shell-kodi';a.out.mkdir(parents=True,exist_ok=True)
    activity=shell/ACTIVITY;before=activity.read_text();assert sha(activity.read_bytes())==PARENT_ACTIVITY_SHA,'Not exact locked 2103271 Activity'
    after=patch_activity(before);activity.write_text(after)
    gradle=shell/GRADLE;g=gradle.read_text();g=once(g,'versionCode 2103271','versionCode 2103272');g=once(g,'versionName "1.0.9-Sports-Data-RC1"','versionName "1.0.9-Sports-Polish-RC1"');gradle.write_text(g)
    script=a.root/'scripts/infinity_background_resume.py';v=script.read_text();v=once(v,'VERSION_CODE = 2103271','VERSION_CODE = 2103272');v=once(v,"RELEASE = '1.0.9-Sports-Data-RC1'",f"RELEASE = '{RELEASE}'");v=once(v,"BASE_COMMIT = 'fe36eda6020934e538b32f754d3175040960b2cc'",f"BASE_COMMIT = '{PARENT_COMMIT}'");v=once(v,"BASE_APK_SHA256 = '54223cd2dcc6ebbf1b0ddddc88114ca9c95541084077a7ea03dba7c6f7ac2259'",f"BASE_APK_SHA256 = '{PARENT_APK}'");script.write_text(v)
    package=a.root/'scripts/package_background_resume.py';v=package.read_text();v=v.replace('Infinity-2103271-Sports-Data-RC1','Infinity-2103272-Sports-Polish-RC1');v=once(v,"'base_run':36755538846",f"'base_run':{PARENT_RUN}");v=once(v,"ROOT/'repairs/sports-data-2103271/DEVICE-TEST.md'","ROOT/'repairs/sports-polish-2103272/DEVICE-TEST.md'");package.write_text(v)
    receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=VERSION_CODE,release=RELEASE,candidate_locked=False,physical_device_verified=False,complete_product_audit=False,sports_visual_polish=True,sports_compact_action_bar=True,sports_live_hero=True,sports_upcoming_scores_suppressed=True,sports_status_summary_local=True,sports_light_oled_polished=True,sports_data_logic_preserved=True,sports_channel_resolver_preserved=True,sports_smart_multiview_preserved=True)
    for n in [ACTIVITY,GRADLE]:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    (a.out/'sports-polish.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='locked2103271/'+ACTIVITY,tofile='candidate2103272/'+ACTIVITY)))
    print('Applied 2103272 Sports presentation polish over exact locked 2103271; Sports data/player/provider/Multi-View ownership preserved.')

if __name__=='__main__':main()
