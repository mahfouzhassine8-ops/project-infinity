// @append
  private void cobraRenderMobileMode(LinearLayout parent,ArrayList<Channel> channels){
    cobraModeBrowserHeader(parent,cobraModeGroupName());if(mCobraModeLayout.browser[3]>=260)cobraModeFilters(parent);
    if(channels.isEmpty()){cobraModeEmpty(parent,"Your channels will appear here. Choose a group or add favorites.");return;}
    cobraInstallModeList(parent,new android.widget.ListView(this),new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraMobileChannelRow row=old instanceof CobraMobileChannelRow?(CobraMobileChannelRow)old:new CobraMobileChannelRow();row.bind(getItem(p),p);return row;}});
  }
  private void cobraRenderCompactMode(LinearLayout parent,ArrayList<Channel> channels){
    cobraModeBrowserHeader(parent,cobraModeGroupName()+"  ·  "+channels.size());
    if(channels.isEmpty()){cobraModeEmpty(parent,"No channels match this filter.");return;}
    TextView columns=cobraText("#     CHANNEL                                       ON NOW",cobraModeColor("muted"),10);columns.setLetterSpacing(.08f);columns.setPadding(dp(10),0,0,0);parent.addView(columns,new LinearLayout.LayoutParams(-1,dp(26)));
    cobraInstallModeList(parent,new android.widget.ListView(this),new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraCompactChannelRow row=old instanceof CobraCompactChannelRow?(CobraCompactChannelRow)old:new CobraCompactChannelRow();row.bind(getItem(p),p);return row;}});
  }
  private void cobraRenderCardsMode(LinearLayout parent,ArrayList<Channel> channels){
    cobraModeBrowserHeader(parent,cobraModeGroupName()+" / Channel wall");
    if(channels.isEmpty()){cobraModeEmpty(parent,"Choose a group to explore its channel wall.");return;}
    android.widget.GridView grid=new android.widget.GridView(this);grid.setNumColumns(mCobraModeLayout.columns);grid.setHorizontalSpacing(dp(10));grid.setVerticalSpacing(dp(10));grid.setPadding(dp(2),dp(6),dp(2),dp(8));grid.setStretchMode(android.widget.GridView.STRETCH_COLUMN_WIDTH);
    cobraInstallModeList(parent,grid,new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraPosterChannelCard row=old instanceof CobraPosterChannelCard?(CobraPosterChannelCard)old:new CobraPosterChannelCard();row.bind(getItem(p),p);return row;}});
  }
  private void cobraRenderFocusMode(LinearLayout parent,ArrayList<Channel> channels){
    LinearLayout nav=new LinearLayout(this);String[] labels={"Channels","Up next"};
    for(int i=0;i<2;i++){final boolean schedule=i==1;Button b=cobraTextButton(labels[i],cobraModeDark(),()->{cobraRememberModeScroll();mCobraFocusSchedule=schedule;cobraRenderGuideBrowser();});b.setSelected(mCobraFocusSchedule==schedule);nav.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));}
    nav.addView(cobraIcon("guide","Browse categories",cobraModeDark(),v->cobraToggleModeGroups()),new LinearLayout.LayoutParams(dp(48),dp(48)));parent.addView(nav,new LinearLayout.LayoutParams(-1,dp(52)));
    if(!mCobraFocusSchedule){if(channels.isEmpty()){cobraModeEmpty(parent,"Choose a category to build your viewing queue.");return;}
      cobraInstallModeList(parent,new android.widget.ListView(this),new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraFocusQueueRow row=old instanceof CobraFocusQueueRow?(CobraFocusQueueRow)old:new CobraFocusQueueRow();row.bind(getItem(p),p);return row;}});return;}
    final Channel channel=mGuidePreviewChannel;final ArrayList<GuideProgram> future=new ArrayList<>();ArrayList<GuideProgram> all=channel==null?null:cobraPrograms(channel);long now=System.currentTimeMillis();if(all!=null)for(GuideProgram p:all)if(p.stop>now&&future.size()<64)future.add(p);
    if(future.isEmpty()){cobraModeEmpty(parent,channel==null?"Choose a channel first.":cobraGuideStatus(channel));return;}
    cobraInstallModeList(parent,new android.widget.ListView(this),new android.widget.BaseAdapter(){public int getCount(){return future.size();}public Object getItem(int p){return future.get(p);}public long getItemId(int p){return future.get(p).start;}public boolean hasStableIds(){return true;}public View getView(int p,View old,android.view.ViewGroup host){CobraFocusProgrammeRow row=old instanceof CobraFocusProgrammeRow?(CobraFocusProgrammeRow)old:new CobraFocusProgrammeRow();row.bind(channel,future.get(p));return row;}});
  }
  private void cobraRenderGridMode(LinearLayout parent,ArrayList<Channel> channels){
    // The same time-aligned guide exists on the cover screen and on TV; only its time span changes.
    cobraModeBrowserHeader(parent,cobraModeGroupName());
    if(mCobraGuideWindow==0){long t=System.currentTimeMillis();mCobraGuideWindow=t-t%1800000L;}
    LinearLayout time=new LinearLayout(this);time.setGravity(Gravity.CENTER_VERTICAL);
    time.addView(cobraIcon("back","Earlier programmes",cobraModeDark(),v->cobraMoveGuideTime(-1)),new LinearLayout.LayoutParams(dp(48),dp(48)));
    Button live=cobraTextButton("Now",cobraModeDark(),()->cobraMoveGuideTime(0));time.addView(live,new LinearLayout.LayoutParams(dp(58),dp(48)));
    TextView date=cobraText(new SimpleDateFormat("EEE, d MMM",Locale.getDefault()).format(new Date(mCobraGuideWindow)),cobraModeColor("muted"),11);mCobraModeDate=date;date.setSingleLine(true);date.setGravity(Gravity.CENTER);time.addView(date,new LinearLayout.LayoutParams(0,dp(48),1));
    time.addView(cobraIcon("next","Later programmes",cobraModeDark(),v->cobraMoveGuideTime(1)),new LinearLayout.LayoutParams(dp(48),dp(48)));if(mCobraModeLayout.browser[3]>=230)parent.addView(time,new LinearLayout.LayoutParams(-1,dp(48)));
    mCobraGuideRuler=new CobraGuideRuler();mCobraGuideRuler.setTag("cobra_tv_time_ruler");parent.addView(mCobraGuideRuler,new LinearLayout.LayoutParams(-1,dp(32)));
    if(channels.isEmpty()){cobraModeEmpty(parent,"No channels in this group.");return;}
    cobraInstallModeList(parent,new android.widget.ListView(this),new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraBroadcastRow row=old instanceof CobraBroadcastRow?(CobraBroadcastRow)old:new CobraBroadcastRow();row.bind(getItem(p),p);return row;}});
  }
  private void cobraMoveGuideTime(int direction){
    cobraRememberModeScroll();long now=System.currentTimeMillis();long step=mCobraModeLayout==null?1800000L:mCobraModeLayout.timeSpan/2;
    mCobraGuideWindow=direction==0?now-now%1800000L:Math.max(now-7L*86400000L,Math.min(now+7L*86400000L,mCobraGuideWindow+direction*step));
    if(mCobraModeDate!=null)mCobraModeDate.setText(new SimpleDateFormat("EEE, d MMM",Locale.getDefault()).format(new Date(mCobraGuideWindow)));
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();if(mCobraGuideRuler!=null)mCobraGuideRuler.invalidate();
  }
  private void cobraInspectProgramme(Channel channel,GuideProgram program){mCobraInspectedChannel=channel;mCobraInspectedProgram=program;cobraRefreshModeDetails();}
  private void cobraRefreshModeDetails(){
    if(mCobraModeEyebrow==null||mCobraModeLayout==null)return;
    Channel channel="grid".equals(mCobraGuideStyle)&&mCobraInspectedChannel!=null?mCobraInspectedChannel:mGuidePreviewChannel;
    GuideProgram now=channel==mCobraInspectedChannel&&mCobraInspectedProgram!=null?mCobraInspectedProgram:cobraCurrentProgram(channel),next=cobraNextProgram(channel);
    boolean playing=channel!=null&&mGuidePreviewChannel!=null&&channel.id.equals(mGuidePreviewChannel.id);
    mCobraModeEyebrow.setText(channel==null?"LIVE TELEVISION":(playing?"NOW PLAYING  /  ":"BROWSING  /  ")+channel.name);
    mCobraGuideNowLabel.setText(now==null?channel==null?"Choose a channel":channel.name:now.title);
    mCobraGuideNextLabel.setText(now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+(next==null?"":"\nNext  "+next.title));
    mCobraModeDescription.setText(now==null?"":now.description);
    mCobraGuideDetails.setContentDescription(channel==null?"Programme information":channel.name+", "+(now==null?cobraGuideStatus(channel):now.title)+", open programme details");
    mCobraGuideProgress.setVisibility(now!=null&&now.start<=System.currentTimeMillis()&&now.stop>System.currentTimeMillis()&&mCobraModeLayout.details[3]>=96?View.VISIBLE:View.GONE);
    if(now!=null)mCobraGuideProgress.setProgress(Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000));
    View button=mCobraModeToolbar.findViewWithTag("cobra_mode_play_pause");boolean running=mCobraPreviewPlayer!=null&&mCobraPreviewPlayer.getPlayWhenReady();if(button instanceof CobraIconButton){((CobraIconButton)button).icon(running?"pause":"play");button.setContentDescription(running?"Pause live preview":"Play live preview");}
    if(mCobraModeSub!=null)mCobraModeSub.setText("COBRA LIVE  ·  "+String.format(Locale.getDefault(),"%,d",mChannels.size())+" CHANNELS");
    View state=mCobraPreviewHost==null?null:mCobraPreviewHost.findViewWithTag("cobra_preview_label");if(state!=null)state.setVisibility(mCobraPreviewPlayer!=null&&mCobraPreviewPlayer.getPlaybackState()==Player.STATE_READY?View.GONE:View.VISIBLE);
    if(mCobraGuideRuler!=null)mCobraGuideRuler.invalidate();
  }
  private void cobraShowPreviewActions(){
    Channel c=mGuidePreviewChannel;LinearLayout rows=cobraOpenSheet(c==null?"Live preview":c.name,"Preview controls","preview-actions");boolean dark=cobraSheetIsDark();
    rows.addView(cobraSheetRow("play","Play / Pause",null,false,dark,()->toggleCobraPreviewPlayPause()));
    rows.addView(cobraSheetRow("audio",mCobraPreviewMuted?"Unmute":"Mute",null,false,dark,()->toggleCobraPreviewMute()));
    rows.addView(cobraSheetRow("cc","Captions",null,false,dark,()->toggleCobraPreviewCaptions()));
    if(c!=null){rows.addView(cobraSheetRow("fullscreen","Fullscreen",null,false,dark,()->promoteCobraPreviewToFullscreen(c)));rows.addView(cobraSheetRow("more","Channel actions","Favorite, schedule recording and more",false,dark,()->showCobraChannelActions(c)));}
  }
