    liveRewind.setTag("cobra_live_rewind");
    liveRewind.setOnClickListener(v -> showCobraLiveRewindPicker());''',
'''    Button liveRewind = action("LIVE TV REWIND  •  " + cobraLiveRewindLabel());
    liveRewind.setTag("cobra_live_rewind");
    liveRewind.setOnClickListener(v -> showCobraLiveRewindPicker());

    Button displayPerformance=action("DISPLAY & PERFORMANCE  •  "+cobraRefreshLabel());
    displayPerformance.setTag("cobra_display_performance");displayPerformance.setOnClickListener(v->showCobraDisplayPerformancePicker());
    Button buffering=action("LIVE TV BUFFERING & TIMESHIFT  •  "+cobraLocalTimeshiftLabel()+" / "+cobraSmartBufferMode().toUpperCase(Locale.US));
    buffering.setTag("cobra_buffer_timeshift");buffering.setOnClickListener(v->showCobraBufferingTimeshiftPicker());
    Button diagnostics=action("PLAYBACK & NETWORK DIAGNOSTICS  •  "+(cobraPlaybackDiagnosticsEnabled()?"ON":"OFF"));
    diagnostics.setTag("cobra_playback_diagnostics");diagnostics.setOnClickListener(v->showCobraPlaybackDiagnosticsPicker());''','settings controls')
 settings=once(settings,
'''    list.addView(chooser, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(theme, new LinearLayout.LayoutParams(-1, dp(58)));
    list.addView(appearance, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(miniBackground, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(liveRewind, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));
    list.addView(refresh, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(allSources, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(profiles, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(health, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(exportDiagnostics, new LinearLayout.LayoutParams(-1, dp(64)));
    list.addView(customEpg, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(subscriptionStatus, new LinearLayout.LayoutParams(-1, dp(86)));''',
'''    list.addView(cobraSettingsSection("Experience"));
    list.addView(chooser, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(theme, new LinearLayout.LayoutParams(-1, dp(58)));
    list.addView(appearance, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(displayPerformance,new LinearLayout.LayoutParams(-1,dp(56)));
    list.addView(cobraSettingsSection("Playback"));
    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(miniBackground, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(liveRewind, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(buffering,new LinearLayout.LayoutParams(-1,dp(56)));
    list.addView(cobraSettingsSection("System"));
    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));
    list.addView(refresh, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(allSources, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(profiles, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(customEpg, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(cobraSettingsSection("Diagnostics"));
    list.addView(diagnostics,new LinearLayout.LayoutParams(-1,dp(56)));
    list.addView(health, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(exportDiagnostics, new LinearLayout.LayoutParams(-1, dp(64)));
    list.addView(subscriptionStatus, new LinearLayout.LayoutParams(-1, dp(86)));''','settings polish sections')
 settings=once(settings,'    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));','    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));settingsScroll.setAlpha(0f);settingsScroll.setTranslationY(dp(8));settingsScroll.animate().alpha(1f).translationY(0f).setDuration(vtheme().motion("cobra.settings.enter",180)).start();','settings entrance polish')
 text=replace_method(text,'showSettings',settings)

 # Display refresh lifecycle.
 resume=method(text,'onResume');resume=once(resume,'    mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");','    mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");\n    cobraApplyRefreshPolicy("resume");cobraStartFrameMeter();','refresh resume');text=replace_method(text,'onResume',resume)
