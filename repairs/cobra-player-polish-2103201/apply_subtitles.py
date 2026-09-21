"""Repair existing subtitle controls; never manufacture tracks or change extraction."""


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Subtitle source contract missing or repeated: " + old[:100])
    return source.replace(old, new, 1)


def method(source, signature, following, replacement):
    start = source.index(signature)
    end = source.index(following, start)
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]


TRACKS = r'''  private ExoPlayer mCobraTrackSheetPlayer;
  private LinearLayout mCobraTrackSheetRows;

  private boolean cobraCurrentTrackPlayer(ExoPlayer player) {
    CobraPlayerBinding binding=mCobraPlayerBindings.get(player);
    return player!=null&&binding!=null&&binding.current()
        &&(player==mPlayer||player==mCobraPreviewPlayer);
  }

  private boolean cobraCaptionsRequested(ExoPlayer player) {
    androidx.media3.common.TrackSelectionParameters params=player.getTrackSelectionParameters();
    if(params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT))return false;
    if(!params.preferredTextLanguages.isEmpty()||params.selectUndeterminedTextLanguage)return true;
    for(TrackSelectionOverride override:params.overrides.values())if(override.getType()==C.TRACK_TYPE_TEXT)return true;
    for(Tracks.Group group:player.getCurrentTracks().getGroups())if(group.getType()==C.TRACK_TYPE_TEXT&&group.isSelected())return true;
    return false;
  }

  private void cobraSetCaptionsEnabled(ExoPlayer player,boolean enabled) {
    if(!cobraCurrentTrackPlayer(player))return;
    androidx.media3.common.TrackSelectionParameters.Builder next=player.getTrackSelectionParameters().buildUpon()
        .setTrackTypeDisabled(C.TRACK_TYPE_TEXT,!enabled);
    if(enabled){
      next.setSelectUndeterminedTextLanguage(true);
      TrackSelectionOverride choice=cobraRequestedCaptionOverride(player);
      if(choice!=null)next.setOverrideForType(choice);
    }
    else next.clearOverridesOfType(C.TRACK_TYPE_TEXT);
    player.setTrackSelectionParameters(next.build());
    CobraPlayerBinding binding=mCobraPlayerBindings.get(player);
    if(!enabled&&binding!=null&&binding.captions!=null)binding.captions.cues(Collections.emptyList());
    cobraUpdatePreviewSubtitleState();
  }

  private TrackSelectionOverride cobraRequestedCaptionOverride(ExoPlayer player) {
    androidx.media3.common.TrackSelectionParameters params=player.getTrackSelectionParameters();
    TrackSelectionOverride first=null,preferred=null;int preferredIndex=Integer.MAX_VALUE,preferredScore=0;
    for(Tracks.Group group:player.getCurrentTracks().getGroups())if(group.getType()==C.TRACK_TYPE_TEXT){
      TrackSelectionOverride existing=params.overrides.get(group.getMediaTrackGroup());
      if(existing!=null&&!existing.trackIndices.isEmpty()){
        boolean supported=true;for(int index:existing.trackIndices)if(index<0||index>=group.length||!group.isTrackSupported(index)){supported=false;break;}
        if(supported)return existing;
      }
    }
    for(Tracks.Group group:player.getCurrentTracks().getGroups())if(group.getType()==C.TRACK_TYPE_TEXT){
      for(int i=0;i<group.length;i++)if(group.isTrackSupported(i)){
        TrackSelectionOverride candidate=new TrackSelectionOverride(group.getMediaTrackGroup(),i);
        if(group.isTrackSelected(i))return candidate;
        if(first==null)first=candidate;
        String language=group.getTrackFormat(i).language;
        if(language!=null)for(int p=0;p<params.preferredTextLanguages.size()&&p<=preferredIndex;p++){
          String requested=params.preferredTextLanguages.get(p);
          int score=language.equalsIgnoreCase(requested)?2:language.split("-",2)[0].equalsIgnoreCase(requested.split("-",2)[0])?1:0;
          if(score>0&&(p<preferredIndex||score>preferredScore)){preferred=candidate;preferredIndex=p;preferredScore=score;break;}
        }
      }
    }
    return preferred!=null?preferred:first;
  }

  private void cobraSelectRequestedCaptions(ExoPlayer player) {
    if(!cobraCurrentTrackPlayer(player))return;
    androidx.media3.common.TrackSelectionParameters params=player.getTrackSelectionParameters();
    // Explicit preview On (and saved Automatic) requests any available language.
    // Keep that request in Media3 parameters while tracks are still being discovered.
    if(params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT)||!params.selectUndeterminedTextLanguage)return;
    TrackSelectionOverride choice=cobraRequestedCaptionOverride(player);
    if(choice!=null&&!choice.equals(params.overrides.get(choice.mediaTrackGroup)))
      player.setTrackSelectionParameters(params.buildUpon().setOverrideForType(choice).build());
  }

  private void cobraUpdatePreviewSubtitleState() {
    View button=mCobraPreviewHost==null?null:mCobraPreviewHost.findViewWithTag("cobra_preview_captions");
    if(button==null)return;
    boolean enabled=cobraCurrentTrackPlayer(mCobraPreviewPlayer)&&cobraCaptionsRequested(mCobraPreviewPlayer);
    button.setSelected(enabled);button.setContentDescription(enabled?"Turn subtitles off":"Turn subtitles on when available");
  }

  private String cobraLanguageLabel(String language) {
    if(language==null||language.isEmpty()||"und".equalsIgnoreCase(language))return "Language not supplied";
    java.util.Locale locale=java.util.Locale.forLanguageTag(language.replace('_','-'));
    String label=locale.getDisplayName(java.util.Locale.getDefault());
    if(label.isEmpty())return language;
    return label.substring(0,1).toUpperCase(java.util.Locale.getDefault())+label.substring(1);
  }

  private String cobraSubtitlePreferenceLabel(String value) {
    if("inherit".equals(value))return "Inherit default";
    if("off".equals(value))return "Off";
    if("auto".equals(value))return "Automatic • when available";
    return cobraLanguageLabel(value)+" • when available";
  }

  private String cobraTrackLabel(Format format,int index,boolean audio) {
    if(format.label!=null&&!format.label.trim().isEmpty())return format.label;
    if(format.language!=null&&!format.language.isEmpty()&&!"und".equalsIgnoreCase(format.language))return cobraLanguageLabel(format.language);
    return (audio?"Audio":"Subtitle")+" track "+(index+1);
  }

  private void showTrackChooser() {
    final ExoPlayer player=mPlayer;if(!cobraCurrentTrackPlayer(player)||mCobraPlayerLocked)return;
    LinearLayout rows=cobraOpenSheet("Audio & subtitles","Available tracks • this playback session","tracks");
    mCobraTrackSheetPlayer=player;mCobraTrackSheetRows=rows;cobraRefreshTrackChooser(player);
  }

  private void cobraTrackDetail(ExoPlayer player,LinearLayout rows,String icon,String title,String detail,String tag,boolean selected,Runnable action) {
    cobraAddDetail(rows,icon,title,detail,tag,selected,action);
    View row=rows.getChildAt(rows.getChildCount()-1);FrameLayout sheet=mCobraActionSheet;
    row.setOnClickListener(view->{
      if(!cobraCurrentTrackPlayer(player)||mCobraTrackSheetPlayer!=player||mCobraActionSheet!=sheet||row.getParent()!=rows)return;
      closeCobraActionSheet();action.run();
    });
  }

  private void cobraRefreshTrackChooser(ExoPlayer player) {
    if(!cobraCurrentTrackPlayer(player)||player!=mCobraTrackSheetPlayer||mCobraTrackSheetRows==null
        ||!"tracks".equals(mCobraSheetKind)||mCobraActionSheet==null)return;
    LinearLayout rows=mCobraTrackSheetRows;
    View focused=rows.findFocus();Object focusedTag=focused==null?null:focused.getTag();
    rows.removeAllViews();
    boolean disabled=player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_TEXT);
    cobraTrackDetail(player,rows,"cc","Subtitles off",disabled?"Selected":"Turn off subtitles for this playback", "cobra-track-off",disabled,()->cobraSetCaptionsEnabled(player,false));
    int audioCount=0,textCount=0,unsupportedText=0,groupIndex=0;
    for(Tracks.Group group:player.getCurrentTracks().getGroups()) {
      final int groupNumber=groupIndex++;
      if(group.getType()!=C.TRACK_TYPE_AUDIO&&group.getType()!=C.TRACK_TYPE_TEXT)continue;
      for(int i=0;i<group.length;i++) {
        boolean audio=group.getType()==C.TRACK_TYPE_AUDIO;
        if(!group.isTrackSupported(i)){if(!audio)unsupportedText++;continue;}
        final int index=i;Format format=group.getTrackFormat(i);
        String detail=audio?"Audio":"Subtitles";
        if(format.language==null||format.language.isEmpty()||"und".equalsIgnoreCase(format.language))detail+=" • language not supplied";
        boolean selected=group.isTrackSelected(i)&&!player.getTrackSelectionParameters().disabledTrackTypes.contains(group.getType());
        cobraTrackDetail(player,rows,audio?"audio":"cc",cobraTrackLabel(format,i,audio),detail,
            "cobra-track:"+groupNumber+":"+i,selected,()->{
          if(!cobraCurrentTrackPlayer(player))return;
          boolean available=false;
          for(Tracks.Group current:player.getCurrentTracks().getGroups())if(current.getMediaTrackGroup().equals(group.getMediaTrackGroup())
              &&index<current.length&&current.isTrackSupported(index)){available=true;break;}
          if(!available)return;
          player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon()
              .setTrackTypeDisabled(group.getType(),false)
              .setOverrideForType(new TrackSelectionOverride(group.getMediaTrackGroup(),index)).build());
          cobraUpdatePreviewSubtitleState();
        });
        if(audio)audioCount++;else textCount++;
      }
    }
    if(textCount==0)cobraInfoText(rows,unsupportedText>0?"Subtitle tracks are present but unsupported on this player.":"No subtitle tracks available in this stream.");
    if(audioCount==0)cobraInfoText(rows,"No audio tracks available in this stream.");
    if(focusedTag!=null){View replacement=rows.findViewWithTag(focusedTag);if(replacement!=null)replacement.requestFocus();}
  }
'''


def transform(source):
    source = once(source, "  private boolean mCobraPreviewCaptions = false;\n", "")
    source = once(source,
        'CobraIconButton captions=cobraIcon("cc","Preview captions",true,v->toggleCobraPreviewCaptions());',
        'CobraIconButton captions=cobraIcon("cc","Turn subtitles on when available",true,v->toggleCobraPreviewCaptions());captions.setTag("cobra_preview_captions");')
    source = once(source,
        '  private void updateCobraPreviewPlayPause() {\n    if(mCobraPreviewHost==null)return;',
        '  private void updateCobraPreviewPlayPause() {\n    cobraUpdatePreviewSubtitleState();\n    if(mCobraPreviewHost==null)return;')
    source = once(source,
        '    host.setOnLongClickListener(v->{mCobraNextSheetAnchor=v;cobraShowPreviewActions();return true;});\n    return host;',
        '    host.setOnLongClickListener(v->{mCobraNextSheetAnchor=v;cobraShowPreviewActions();return true;});\n    cobraUpdatePreviewSubtitleState();return host;')
    source = once(source,
        '    mCobraPreviewGeneration++;cobraDisposePlayer(previous);',
        '    mCobraPreviewGeneration++;cobraDisposePlayer(previous);cobraUpdatePreviewSubtitleState();')
    source = method(source, "  private void toggleCobraPreviewCaptions() {", "  private View cobraPreviewDetails(", r'''
  private void toggleCobraPreviewCaptions() {
    ExoPlayer player=mCobraPreviewPlayer;if(!cobraCurrentTrackPlayer(player))return;
    boolean enabled=!cobraCaptionsRequested(player);
    cobraSetCaptionsEnabled(player,enabled);
    toast(enabled?"Subtitles on when available":"Subtitles off");
  }
''')
    source = method(source, "  private void showTrackChooser() {", "  private String cobraAspectLabel(", TRACKS)
    source = once(source, 'rows.addView(cobraSheetRow("cc","Captions",null,false,dark,()->toggleCobraPreviewCaptions()));',
        'rows.addView(cobraSheetRow("cc",mCobraPreviewPlayer!=null&&cobraCaptionsRequested(mCobraPreviewPlayer)?"Turn subtitles off":"Turn subtitles on",null,false,dark,()->toggleCobraPreviewCaptions()));')
    source = once(source, '    mCobraActionSheet=null;mCobraSheetKind="";',
        '    mCobraActionSheet=null;mCobraSheetKind="";mCobraTrackSheetPlayer=null;mCobraTrackSheetRows=null;')
    source = once(source,
        '    @Override public void onTracksChanged(Tracks tracks){if(current())vitals.recovery.suspend();}',
        '''    @Override public void onTracksChanged(Tracks tracks){if(current()){vitals.recovery.suspend();cobraSelectRequestedCaptions(player);cobraRefreshTrackChooser(player);cobraUpdatePreviewSubtitleState();}}
    @Override public void onTrackSelectionParametersChanged(androidx.media3.common.TrackSelectionParameters parameters){if(current()){
      if(parameters.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT)&&captions!=null)captions.cues(Collections.emptyList());
      cobraRefreshTrackChooser(player);cobraUpdatePreviewSubtitleState();
    }}''')
    source = once(source,
        'cobraAddDetail(rows,"audio","Preferred audio language",prefs.audio.isEmpty()?"Automatic / default":prefs.audio,"cobra-channel-audio",false,()->cobraShowChannelLanguage(channel,false));',
        'cobraAddDetail(rows,"audio","Preferred audio language",prefs.audio.isEmpty()?"Automatic / default":cobraLanguageLabel(prefs.audio)+" • when available","cobra-channel-audio",false,()->cobraShowChannelLanguage(channel,false));')
    source = once(source,
        'cobraAddDetail(rows,"cc","Subtitles",prefs.subtitles,"cobra-channel-subtitles",false,()->cobraShowChannelLanguage(channel,true));',
        'cobraAddDetail(rows,"cc","Preferred subtitles",cobraSubtitlePreferenceLabel(prefs.subtitles),"cobra-channel-subtitles",false,()->cobraShowChannelLanguage(channel,true));')
    source = once(source,
        'LinearLayout rows=cobraOpenSheet(text?"Channel subtitles":"Channel audio language",channel.name,"channel-language");',
        'LinearLayout rows=cobraOpenSheet(text?"Preferred subtitles":"Preferred audio language",channel.name+" • saved preference, when available","channel-language");')
    source = once(source,
        'String label="inherit".equals(value)?"Inherit default":"off".equals(value)?"Off":"auto".equals(value)?"Automatic subtitles":value;',
        'String label="inherit".equals(value)?"Inherit default":"off".equals(value)?"Off":"auto".equals(value)?"Automatic subtitles":cobraLanguageLabel(value);')
    source = once(source,
        '    if("off".equals(p.subtitles)&&b.captions!=null)b.captions.cues(Collections.emptyList());',
        '    if(b.player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_TEXT)&&b.captions!=null)b.captions.cues(Collections.emptyList());\n    cobraUpdatePreviewSubtitleState();')
    return source
