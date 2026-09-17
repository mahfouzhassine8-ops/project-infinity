  // Cobra 2103156: diagnostics are observers, never a playback/session owner.
  private static final int REQUEST_COBRA_DIAGNOSTICS = 4174;
  private boolean mCobraDiagnosticsPicker;
  private String mCobraDiagnosticsSnapshot;

  @Override protected void onSaveInstanceState(Bundle state) {
    state.putBoolean("cobra_diagnostics_picker",mCobraDiagnosticsPicker);
    if(mCobraDiagnosticsSnapshot!=null && mCobraDiagnosticsSnapshot.length()<=128*1024)
      state.putString("cobra_diagnostics_snapshot",mCobraDiagnosticsSnapshot);
    super.onSaveInstanceState(state);
  }

  private void cobraDiagnosticSecrets() {
    ArrayList<String> secrets=new ArrayList<>();
    for(LiveSource source:mSources){secrets.add(source.username);secrets.add(source.password);}
    InfinityCobraDiagnostics.setSecrets(secrets);
  }

  private String cobraFreshHealthSnapshot() {
    cobraDiagnosticSecrets();
    JSONObject root=new JSONObject();
    try {
      root.put("schema",3);InfinityCobraDiagnostics.addIdentity(this,root);
      root.put("captured_at_ms",System.currentTimeMillis());root.put("snapshot_kind","live_activity_observation");
      root.put("active_ui",activeCobraUiLabel());root.put("ui_runtime",3);
      root.put("screen",mPlayerOverlay!=null?"player":mMultiOverlay!=null?"multiview":mCobraInternalScreen);
      root.put("view_mode",mCobraGuideStyle);root.put("lifecycle",InfinityCobraDiagnostics.state());
      root.put("background_stopped",mBackgroundStopped);root.put("picture_in_picture",mInPictureInPicture);
      root.put("source_count",mSources.size());root.put("channel_count",mChannels.size());
      root.put("guide_requests_in_flight",mCobraEpgRequest.size());root.put("short_guide_requests_in_flight",mCobraShortEpgBusy.size());
      root.put("cached_guide_source_count",mCobraEpg.size());root.put("multiview_tiles",mCobraTiles.keys().size());
      root.put("audio_owner",mMultiOverlay==null?-1:mAudioTile);root.put("recording_state",mRecordingSession.isEmpty()?"idle":"recording");
      root.put("dropped_diagnostic_events",InfinityCobraDiagnostics.droppedEvents());
      JSONArray players=new JSONArray();
      for(CobraPlayerBinding binding:mCobraPlayerBindings.values()){
        JSONObject p=new JSONObject();p.put("channel_hash",InfinityCobraFeatureRuntime.hashId(binding.channel.id));
        p.put("state",binding.player.getPlaybackState());p.put("play_when_ready",binding.player.getPlayWhenReady());
        p.put("is_playing",binding.player.isPlaying());p.put("last_error_code",binding.error);
        p.put("fallback_attempted",binding.fallback);players.put(p);
      }
      root.put("players",players);
      JSONArray sources=new JSONArray();
      for(LiveSource source:mSources){
        if(sources.length()>=64)break;
        JSONObject s=new JSONObject();s.put("source_hash",InfinityCobraFeatureRuntime.hashId(source.id));
        s.put("enabled",mFeatures.sourceEnabled(source.id));s.put("request_in_flight",mCobraEpgRequest.containsKey(source.id));
        String status=mCobraEpgStatus.get(source.id);s.put("guide_state",status==null?"not_observed":status);
        CobraEpgData data=mCobraEpg.get(source.id);
        if(data!=null){s.put("fetched_at_ms",data.fetched);s.put("guide_channel_keys",data.programs.size());s.put("partial",data.truncated);}
        sources.put(s);
      }
      root.put("source_states",sources);root.put("source_states_truncated",mSources.size()>64);
      root.put("crash_history","collected separately in the exported ZIP; this snapshot is not a crash detector");
      return root.toString(2);
    }catch(Exception failure){InfinityCobraDiagnostics.failure(this,"snapshot",failure);return "Snapshot unavailable: "+failure.getClass().getSimpleName();}
  }

  private void showCobraHealthSnapshot() {
    String snapshot=cobraFreshHealthSnapshot();
    LinearLayout rows=cobraOpenSheet("Cobra Health Snapshot","Fresh state • redacted • not proof that no crash occurred","diagnostics");
    boolean dark=cobraSheetIsDark();
    rows.addView(cobraSheetRow("source","Export Crash & Diagnostics ZIP","Choose where to save the report",false,dark,()->showCobraDiagnosticExport()));
    TextView report=cobraText(snapshot,dark?0xffdce7f3:cobraThemeColor("text",mTheme.text),12);
    report.setTypeface(Typeface.MONOSPACE);report.setTextIsSelectable(true);report.setPadding(dp(12),dp(12),dp(12),dp(12));
    rows.addView(report,new LinearLayout.LayoutParams(-1,-2));
  }

  private void showCobraDiagnosticExport() {
    if(mCobraDiagnosticsPicker||InfinityCobraDiagnostics.exporting()){toast("A diagnostics export is already in progress");return;}
    LinearLayout rows=cobraOpenSheet("Export Crash & Diagnostics ZIP","Save locally or to a provider you choose. Nothing is sent automatically.","diagnostic-export");
    boolean dark=cobraSheetIsDark();
    TextView notice=cobraText("Includes fresh state, recent captured errors, bounded Kodi logs and Android exit/ANR evidence when available. Credentials and URLs are redacted. Raw binary native tombstones, account files and recordings are excluded. Review the ZIP before sharing.",dark?0xffdce7f3:cobraThemeColor("text",mTheme.text),14);
    notice.setPadding(dp(12),dp(14),dp(12),dp(14));rows.addView(notice,new LinearLayout.LayoutParams(-1,-2));
    rows.addView(cobraSheetRow("source","Choose save location","Android will ask where to create the ZIP",false,dark,()->{
      mCobraDiagnosticsSnapshot=cobraFreshHealthSnapshot();mCobraDiagnosticsPicker=true;
      try{startActivityForResult(InfinityCobraDiagnostics.createDocumentIntent(),REQUEST_COBRA_DIAGNOSTICS);}
      catch(android.content.ActivityNotFoundException missing){mCobraDiagnosticsPicker=false;mCobraDiagnosticsSnapshot=null;toast("No system document picker is available on this device");}
      catch(RuntimeException failure){mCobraDiagnosticsPicker=false;mCobraDiagnosticsSnapshot=null;InfinityCobraDiagnostics.failure(this,"document-picker",failure);toast("Could not open the save-location picker");}
    }));
    rows.addView(cobraSheetRow("close","Cancel",null,false,dark,()->{}));
  }
