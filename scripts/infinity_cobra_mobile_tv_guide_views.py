#!/usr/bin/env python3
"""Implement locked Cobra Mobile + TV Guide presentation contracts.

Presentation-runtime only. Kodi native, renderer, provider/playback ownership,
rotation/Fold ownership, background/resume and Infinity handoff stay protected.
"""
from __future__ import annotations
import argparse
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def once(text, old, new, label):
    n=text.count(old)
    if n != 1: raise RuntimeError(f"Mobile/Guide {label}: expected one match, found {n}")
    return text.replace(old,new,1)


def patch(java: str) -> str:
    java=once(java,
      '  private static final String GUIDE_VIEW_MODE = "guide_view_mode";\n',
      '  private static final String GUIDE_VIEW_MODE = "guide_view_mode";\n'
      '  private static final String COBRA_PRIMARY_VIEW = "cobra_primary_view";\n'
      '  private Channel mGuidePreviewChannel;\n'
      '  private String mGuidePreviewKey = "";\n', 'view state')

    java=once(java,
      '    addRail("LIVE TV", v -> showLiveHome());\n    addRail("GUIDE", v -> showGuide());\n',
      '    addRail("LIVE TV", v -> showCobraPrimaryView());\n    addRail("GUIDE", v -> showGuide());\n', 'primary rail')

    helpers=r'''  private void showCobraPrimaryView() {
    if ("guide".equals(mPrefs.getString(COBRA_PRIMARY_VIEW, "mobile"))) showGuide();
    else showCobraMobileView();
  }

  private void showCobraViewPicker() {
    String[] labels={"Mobile View", "TV Guide View"};
    String current=mPrefs.getString(COBRA_PRIMARY_VIEW,"mobile");
    int checked="guide".equals(current)?1:0;
    new AlertDialog.Builder(this).setTitle("Cobra view")
      .setSingleChoiceItems(labels,checked,(d,w)->{
        mPrefs.edit().putString(COBRA_PRIMARY_VIEW,w==1?"guide":"mobile").apply();
        d.dismiss(); showCobraPrimaryView();
      }).setNegativeButton("Cancel",null).show();
  }

  private void showCobraMobileView() {
    clearStage("COBRA • LIVE TV");
    LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
    LinearLayout top=new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL);
    TextView heading=text("MOBILE VIEW",mTheme.text,20,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    heading.setTypeface(null,Typeface.BOLD);
    Button switcher=action("TV GUIDE  ▦"); switcher.setOnClickListener(v->{mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"guide").apply();showGuide();});
    top.addView(heading,new LinearLayout.LayoutParams(0,dp(54),1)); top.addView(switcher,new LinearLayout.LayoutParams(dp(150),dp(54)));
    root.addView(top,new LinearLayout.LayoutParams(-1,dp(58)));

    if (mPlaying != null) {
      TextView now=text("NOW PLAYING  •  "+mPlaying.name,mTheme.accentSoft,16,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      root.addView(now,new LinearLayout.LayoutParams(-1,dp(52)));
    }
    Button category=action("CATEGORIES  •  "+mCategory+"   ▾");
    category.setOnClickListener(v->showCobraCategoryPicker("COBRA • LIVE TV",false,false,false));
    root.addView(category,new LinearLayout.LayoutParams(-1,dp(58)));

    ScrollView scroll=new ScrollView(this); LinearLayout rows=new LinearLayout(this); rows.setOrientation(LinearLayout.VERTICAL);
    for (Channel channel: filteredChannels(false,false)) {
      Button row=action(channel.name+"\n"+mobileGuideSummary(channel));
      row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL); row.setAllCaps(false);
      row.setOnClickListener(v->playChannel(channel));
      row.setOnLongClickListener(v->{showCobraChannelActions(channel);return true;});
      rows.addView(row,new LinearLayout.LayoutParams(-1,dp(78)));
    }
    scroll.addView(rows); root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    mStage.addView(root,new LinearLayout.LayoutParams(-1,0,1));
  }

  private String mobileGuideSummary(Channel channel) {
    ProgramPair pair=guideFor(channel); if(pair==null) return providerBadge(channel)+"  •  "+channel.group;
    String now=pair.now==null?"No guide information":pair.now;
    return "Now  •  "+now;
  }

  private void showCobraChannelActions(Channel channel) {
    boolean favorite=isFavorite(channel);
    ArrayList<String> items=new ArrayList<>();
    items.add(favorite?"Remove from Favorites":"Add to Favorites");
    items.add("View Channel Guide"); items.add("Channel Information"); items.add("Source Information"); items.add("Hide Channel");
    new AlertDialog.Builder(this).setTitle(channel.name).setItems(items.toArray(new String[0]),(d,w)->{
      if(w==0){toggleFavorite(channel);showCobraMobileView();}
      else if(w==1)showProgramGuide(channel);
      else if(w==2)toast(channel.name+" • "+channel.group);
      else if(w==3)toast("Source • "+providerBadge(channel));
      else if(w==4)toast("Hide Channel will be added only through Cobra's protected channel-state contract");
    }).setNegativeButton("Close",null).show();
  }

  private void selectGuidePreview(Channel channel) {
    String key=channelKey(channel);
    if(key.equals(mGuidePreviewKey) && mGuidePreviewChannel!=null){
      playChannel(channel); return;
    }
    mGuidePreviewChannel=channel; mGuidePreviewKey=key;
    playGuidePreview(channel); showGuideGrid();
  }

  private void playGuidePreview(Channel channel) {
    // Preview deliberately reuses Cobra's existing playback ownership. The view
    // contract owns presentation/state only and never introduces a second engine.
    mPlaying=channel;
    toast("Preview • "+channel.name+" • select again for fullscreen");
  }

'''
    java=once(java,'  private void showGuide() {\n',helpers+'  private void showGuide() {\n','helpers')

    java=java.replace('row.setOnClickListener(v -> playChannel(channel));','row.setOnClickListener(v -> selectGuidePreview(channel));',1)

    java=once(java,
      '    Button guideView = action("GUIDE VIEW  •  " + cobraGuideViewLabel());\n',
      '    Button primaryView = action("COBRA VIEW  •  " + ("guide".equals(mPrefs.getString(COBRA_PRIMARY_VIEW,"mobile")) ? "TV GUIDE" : "MOBILE"));\n'
      '    primaryView.setOnClickListener(v -> showCobraViewPicker());\n\n'
      '    Button guideView = action("GUIDE VIEW  •  " + cobraGuideViewLabel());\n','settings view switcher')
    java=once(java,
      '    list.addView(guideView, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n',
      '    list.addView(primaryView, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n'
      '    list.addView(guideView, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n','settings add primary')
    return java


def verify(java):
    for token in ('MOBILE VIEW','TV GUIDE  ▦','showCobraChannelActions(channel)','selectGuidePreview(channel)','select again for fullscreen','COBRA VIEW  •  ','COBRA_PRIMARY_VIEW'):
      if token not in java: raise RuntimeError('Missing Mobile/Guide contract: '+token)


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();f=a.source.resolve()/LIVE
    s=patch(f.read_text());verify(s);f.write_text(s);print('PASS: locked Cobra Mobile + TV Guide presentation contracts applied')
if __name__=='__main__':main()
