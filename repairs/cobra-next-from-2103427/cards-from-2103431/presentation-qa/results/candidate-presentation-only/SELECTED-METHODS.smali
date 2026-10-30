.method private cobraRefreshProgrammeLabels()V
    .registers 25

    move-object/from16 v0, p0

    .line 8462
    invoke-direct/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->isCobraAsyncAlive()Z

    move-result v1

    if-nez v1, :cond_0

    return-void

    .line 8463
    :cond_0
    invoke-direct/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraRefreshQuickPeek()V

    .line 8464
    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mGuidePreviewChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    iget-object v2, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeEyebrow:Landroid/widget/TextView;
    if-eqz v2, :cobra_programme_original_guide_labels
    iget-object v2, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeLayout:Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;
    if-eqz v2, :cobra_programme_original_guide_labels

    # These constants were previously initialized inside the preliminary guide
    # block and remain live in the unchanged player-label/progress block.
    const/high16 v4, 0x447a0000
    const-string v7, "Next  "
    const/4 v8, 0x0
    const-string v9, ""
    const-wide/32 v10, 0xea5f
    const-string v12, " \u2013 "
    goto/16 :goto_5

    :cobra_programme_original_guide_labels


    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraCurrentProgram(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    move-result-object v2

    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraNextProgram(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    move-result-object v3

    .line 8465
    iget-object v4, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideNowLabel:Landroid/widget/TextView;

    const-string v5, "  \u00b7  "

    const-string v6, ""

    if-eqz v4, :cond_3

    if-nez v1, :cond_1

    const-string v7, "Select a channel"

    goto :goto_1

    :cond_1
    new-instance v7, Ljava/lang/StringBuilder;

    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V

    iget-object v8, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->name:Ljava/lang/String;

    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    if-nez v2, :cond_2

    move-object v8, v6

    goto :goto_0

    :cond_2
    new-instance v8, Ljava/lang/StringBuilder;

    invoke-direct {v8, v5}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    iget-object v9, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v8

    :goto_0
    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v7

    :goto_1
    invoke-virtual {v4, v7}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 8466
    :cond_3
    iget-object v4, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideNextLabel:Landroid/widget/TextView;

    const-string v7, "Next  "

    const-wide/32 v8, 0xea60

    const-wide/32 v10, 0xea5f

    const-string v12, " \u2013 "

    if-eqz v4, :cond_6

    if-nez v2, :cond_4

    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraGuideStatus(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;

    move-result-object v3

    goto :goto_3

    :cond_4
    new-instance v15, Ljava/lang/StringBuilder;

    invoke-direct {v15}, Ljava/lang/StringBuilder;-><init>()V

    iget-wide v13, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    invoke-direct {v0, v13, v14}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->formatTime(J)Ljava/lang/String;

    move-result-object v13

    invoke-virtual {v15, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v15, v12}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-wide v13, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-direct {v0, v13, v14}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->formatTime(J)Ljava/lang/String;

    move-result-object v13

    invoke-virtual {v15, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v15, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-wide v13, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v16

    sub-long v13, v13, v16

    add-long/2addr v13, v10

    div-long/2addr v13, v8

    const-wide/16 v8, 0x0

    invoke-static {v8, v9, v13, v14}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v13

    invoke-virtual {v15, v13, v14}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    const-string v5, " min left\n"

    invoke-virtual {v15, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    if-nez v3, :cond_5

    const-string v3, "Upcoming schedule unavailable"

    goto :goto_2

    :cond_5
    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5, v7}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    iget-object v3, v3, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    invoke-virtual {v5, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    :goto_2
    invoke-virtual {v15, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v15}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    :goto_3
    invoke-virtual {v4, v3}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 8467
    :cond_6
    iget-object v3, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideProgress:Landroid/widget/ProgressBar;

    const/high16 v4, 0x447a0000    # 1000.0f

    const/4 v8, 0x0

    if-eqz v3, :cond_8

    if-nez v2, :cond_7

    const/4 v9, 0x4

    goto :goto_4

    :cond_7
    const/4 v9, 0x0

    :goto_4
    invoke-virtual {v3, v9}, Landroid/widget/ProgressBar;->setVisibility(I)V

    if-eqz v2, :cond_8

    iget-object v3, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideProgress:Landroid/widget/ProgressBar;

    iget-wide v13, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    move-object v9, v6

    iget-wide v5, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v22

    move-wide/from16 v18, v13

    move-wide/from16 v20, v5

    invoke-static/range {v18 .. v23}, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraGuideMath;->progress(JJJ)F

    move-result v2

    mul-float v2, v2, v4

    invoke-static {v2}, Ljava/lang/Math;->round(F)I

    move-result v2

    invoke-virtual {v3, v2}, Landroid/widget/ProgressBar;->setProgress(I)V

    goto :goto_5

    :cond_8
    move-object v9, v6

    .line 8468
    :goto_5
    iget-object v2, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPreviewHost:Landroid/widget/FrameLayout;

    if-eqz v2, :cond_a

    const-string v3, "cobra_preview_favorite"

    invoke-virtual {v2, v3}, Landroid/widget/FrameLayout;->findViewWithTag(Ljava/lang/Object;)Landroid/view/View;

    move-result-object v2

    instance-of v3, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraIconButton;

    if-eqz v3, :cond_a

    check-cast v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraIconButton;

    if-eqz v1, :cond_9

    iget-object v3, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mFavorites:Ljava/util/Set;

    iget-object v1, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->id:Ljava/lang/String;

    invoke-interface {v3, v1}, Ljava/util/Set;->contains(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_9

    const-string v1, "favorite_on"

    goto :goto_6

    :cond_9
    const-string v1, "favorite"

    :goto_6
    invoke-virtual {v2, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraIconButton;->icon(Ljava/lang/String;)V

    .line 8469
    :cond_a
    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPlaying:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraCurrentProgram(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    move-result-object v2

    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraNextProgram(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    move-result-object v3

    .line 8470
    iget-object v5, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerProgram:Landroid/widget/TextView;

    if-eqz v5, :cond_d

    if-nez v2, :cond_c

    if-nez v1, :cond_b

    move-object v6, v9

    goto :goto_7

    :cond_b
    iget-object v6, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->name:Ljava/lang/String;

    goto :goto_7

    :cond_c
    iget-object v6, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    :goto_7
    invoke-virtual {v5, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 8471
    :cond_d
    iget-object v5, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerSchedule:Landroid/widget/TextView;

    if-eqz v5, :cond_f

    if-nez v2, :cond_e

    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraGuideStatus(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;

    move-result-object v1

    goto :goto_8

    :cond_e
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    iget-wide v13, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    invoke-direct {v0, v13, v14}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->formatTime(J)Ljava/lang/String;

    move-result-object v6

    invoke-virtual {v1, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1, v12}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-wide v12, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-direct {v0, v12, v13}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->formatTime(J)Ljava/lang/String;

    move-result-object v6

    invoke-virtual {v1, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v6, "   \u00b7   "

    invoke-virtual {v1, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-wide v12, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v18

    sub-long v12, v12, v18

    add-long/2addr v12, v10

    const-wide/32 v10, 0xea60

    div-long/2addr v12, v10

    const-wide/16 v10, 0x0

    invoke-static {v10, v11, v12, v13}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v12

    invoke-virtual {v1, v12, v13}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    const-string v6, " min left"

    invoke-virtual {v1, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    :goto_8
    invoke-virtual {v5, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 8472
    :cond_f
    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerUpcoming:Landroid/widget/TextView;

    if-eqz v1, :cond_11

    if-nez v3, :cond_10

    move-object v6, v9

    goto :goto_9

    :cond_10
    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5, v7}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    iget-object v3, v3, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    invoke-virtual {v5, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v6

    :goto_9
    invoke-virtual {v1, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 8473
    :cond_11
    invoke-direct/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraFinitePlayback()Z

    move-result v1

    if-eqz v1, :cond_13

    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPlayer:Landroidx/media3/exoplayer/ExoPlayer;

    if-eqz v1, :cond_13

    iget-object v3, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerSchedule:Landroid/widget/TextView;

    if-eqz v3, :cond_13

    .line 8474
    invoke-interface {v1}, Landroidx/media3/exoplayer/ExoPlayer;->getDuration()J

    move-result-wide v5

    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPlayer:Landroidx/media3/exoplayer/ExoPlayer;

    invoke-interface {v1}, Landroidx/media3/exoplayer/ExoPlayer;->getCurrentPosition()J

    move-result-wide v9

    const-wide/16 v11, 0x0

    invoke-static {v11, v12, v9, v10}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v9

    .line 8475
    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerSchedule:Landroid/widget/TextView;

    cmp-long v3, v5, v11

    if-lez v3, :cond_12

    const-wide v11, -0x7fffffffffffffffL    # -4.9E-324

    cmp-long v3, v5, v11

    if-eqz v3, :cond_12

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-wide/16 v11, 0x3e8

    div-long/2addr v9, v11

    invoke-static {v9, v10}, Landroid/text/format/DateUtils;->formatElapsedTime(J)Ljava/lang/String;

    move-result-object v7

    invoke-virtual {v3, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v7, " / "

    invoke-virtual {v3, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    div-long/2addr v5, v11

    invoke-static {v5, v6}, Landroid/text/format/DateUtils;->formatElapsedTime(J)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v3, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    goto :goto_a

    :cond_12
    const-string v3, "Loading playback\u2026"

    :goto_a
    invoke-virtual {v1, v3}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 8477
    :cond_13
    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerProgramProgress:Landroid/widget/ProgressBar;

    if-eqz v1, :cond_15

    invoke-direct/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraTimeshiftTimelineAvailable()Z

    move-result v1

    if-nez v1, :cond_15

    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerProgramProgress:Landroid/widget/ProgressBar;

    if-nez v2, :cond_14

    const/4 v5, 0x4

    goto :goto_b

    :cond_14
    const/4 v5, 0x0

    :goto_b
    invoke-virtual {v1, v5}, Landroid/widget/ProgressBar;->setVisibility(I)V

    if-eqz v2, :cond_15

    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraPlayerProgramProgress:Landroid/widget/ProgressBar;

    iget-wide v5, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    iget-wide v7, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v9

    invoke-static/range {v5 .. v10}, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraGuideMath;->progress(JJJ)F

    move-result v2

    mul-float v2, v2, v4

    invoke-static {v2}, Ljava/lang/Math;->round(F)I

    move-result v2

    invoke-virtual {v1, v2}, Landroid/widget/ProgressBar;->setProgress(I)V

    .line 8478
    :cond_15
    iget-object v1, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPlayerOverlay:Landroid/widget/FrameLayout;

    if-eqz v1, :cond_17

    const-string v2, "cobra_player_play_pause"

    invoke-virtual {v1, v2}, Landroid/widget/FrameLayout;->findViewWithTag(Ljava/lang/Object;)Landroid/view/View;

    move-result-object v1

    instance-of v2, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraIconButton;

    if-eqz v2, :cond_17

    check-cast v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraIconButton;

    iget-object v2, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPlayer:Landroidx/media3/exoplayer/ExoPlayer;

    if-eqz v2, :cond_16

    invoke-interface {v2}, Landroidx/media3/exoplayer/ExoPlayer;->getPlayWhenReady()Z

    move-result v2

    if-eqz v2, :cond_16

    const-string v2, "pause"

    goto :goto_c

    :cond_16
    const-string v2, "play"

    :goto_c
    invoke-virtual {v1, v2}, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraIconButton;->icon(Ljava/lang/String;)V

    .line 8479
    :cond_17
    invoke-direct/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraRefreshPlayingIndicators()V

    .line 8480
    invoke-direct/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraRefreshModeDetails()V

    return-void
.end method

.method private cobraRefreshModeDetails()V
    .registers 12

    .line 10141
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeEyebrow:Landroid/widget/TextView;

    if-eqz v0, :cond_13

    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeLayout:Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;

    if-nez v0, :cond_0

    goto/16 :goto_d

    :cond_0
    const-string v0, "grid"

    .line 10142
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideStyle:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraInspectedChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    if-eqz v0, :cond_1

    goto :goto_0

    :cond_1
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mGuidePreviewChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    .line 10143
    :goto_0
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraInspectedChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    if-ne v0, v1, :cond_2

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraInspectedProgram:Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    if-eqz v1, :cond_2

    goto :goto_1

    :cond_2
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraCurrentProgram(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    move-result-object v1

    :goto_1
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraNextProgram(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;

    move-result-object v2

    const/4 v3, 0x1

    const/4 v4, 0x0

    if-eqz v0, :cond_3

    .line 10144
    iget-object v5, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mGuidePreviewChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    if-eqz v5, :cond_3

    iget-object v5, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->id:Ljava/lang/String;

    iget-object v6, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mGuidePreviewChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;

    iget-object v6, v6, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->id:Ljava/lang/String;

    invoke-virtual {v5, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v5

    if-eqz v5, :cond_3

    const/4 v5, 0x1

    goto :goto_2

    :cond_3
    const/4 v5, 0x0

    .line 10145
    :goto_2
    iget-object v6, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeEyebrow:Landroid/widget/TextView;

    if-nez v0, :cond_4

    const-string v5, "LIVE TELEVISION"

    goto :goto_4

    :cond_4
    new-instance v7, Ljava/lang/StringBuilder;

    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V

    if-eqz v5, :cond_5

    const-string v5, "NOW PLAYING  /  "

    goto :goto_3

    :cond_5
    const-string v5, "BROWSING  /  "

    :goto_3
    invoke-virtual {v7, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-object v5, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->name:Ljava/lang/String;

    invoke-virtual {v7, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    :goto_4
    invoke-virtual {v6, v5}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 10146
    iget-object v5, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideNowLabel:Landroid/widget/TextView;

    if-nez v1, :cond_7

    if-nez v0, :cond_6

    const-string v6, "Choose a channel"

    goto :goto_5

    :cond_6
    iget-object v6, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->name:Ljava/lang/String;

    goto :goto_5

    :cond_7
    iget-object v6, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    :goto_5
    invoke-virtual {v5, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 10147
    iget-object v5, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideNextLabel:Landroid/widget/TextView;

    const-string v6, ""

    if-nez v1, :cond_8

    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraGuideStatus(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;

    move-result-object v2

    goto :goto_7

    :cond_8
    new-instance v7, Ljava/lang/StringBuilder;

    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V

    iget-wide v8, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    invoke-direct {p0, v8, v9}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->formatTime(J)Ljava/lang/String;

    move-result-object v8

    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v8, " \u2013 "

    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-wide v8, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-direct {p0, v8, v9}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->formatTime(J)Ljava/lang/String;

    move-result-object v8

    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    if-nez v2, :cond_9

    move-object v2, v6

    goto :goto_6

    :cond_9
    new-instance v8, Ljava/lang/StringBuilder;

    const-string v9, "\nNext  "

    invoke-direct {v8, v9}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    iget-object v2, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    invoke-virtual {v8, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    :goto_6
    invoke-virtual {v7, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    :goto_7
    invoke-virtual {v5, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 10148
    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeDescription:Landroid/widget/TextView;

    if-nez v1, :cond_a

    goto :goto_8

    :cond_a
    iget-object v6, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->description:Ljava/lang/String;

    :goto_8
    invoke-virtual {v2, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 10149
    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideDetails:Landroid/widget/LinearLayout;

    if-nez v0, :cond_b

    const-string v0, "Programme information"

    goto :goto_a

    :cond_b
    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V

    iget-object v6, v0, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;->name:Ljava/lang/String;

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v6, ", "

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    if-nez v1, :cond_c

    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraGuideStatus(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;

    move-result-object v0

    goto :goto_9

    :cond_c
    iget-object v0, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->title:Ljava/lang/String;

    :goto_9
    invoke-virtual {v5, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v0, ", open programme details"

    invoke-virtual {v5, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    :goto_a
    invoke-virtual {v2, v0}, Landroid/widget/LinearLayout;->setContentDescription(Ljava/lang/CharSequence;)V

    .line 10150
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideProgress:Landroid/widget/ProgressBar;

    if-eqz v1, :cond_d

    iget-wide v5, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v7

    cmp-long v2, v5, v7

    if-gtz v2, :cond_d

    iget-wide v5, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v7

    cmp-long v2, v5, v7

    if-lez v2, :cond_d

    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeLayout:Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;

    iget-object v2, v2, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;->details:[I

    const/4 v5, 0x3

    aget v2, v2, v5

    const/16 v5, 0x60

    if-lt v2, v5, :cond_d

    const/4 v2, 0x0

    goto :goto_b

    :cond_d
    const/16 v2, 0x8

    :goto_b
    invoke-virtual {v0, v2}, Landroid/widget/ProgressBar;->setVisibility(I)V

    if-eqz v1, :cond_e

    .line 10151
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideProgress:Landroid/widget/ProgressBar;

    iget-wide v5, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->start:J

    iget-wide v7, v1, Lcom/projectinfinity/kodi/InfinityLiveActivity$GuideProgram;->stop:J

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v9

    invoke-static/range {v5 .. v10}, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraGuideMath;->progress(JJJ)F

    move-result v1

    const/high16 v2, 0x447a0000    # 1000.0f

    mul-float v1, v1, v2

    invoke-static {v1}, Ljava/lang/Math;->round(F)I

    move-result v1

    invoke-virtual {v0, v1}, Landroid/widget/ProgressBar;->setProgress(I)V

    :cond_e
    const-string v0, "focus"

    .line 10152
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideStyle:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_f

    iget-boolean v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraProActive:Z

    if-eqz v0, :cond_f

    invoke-direct {p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraRefreshProHero()V

    .line 10153
    :cond_f
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeToolbar:Landroid/widget/LinearLayout;

    const-string v1, "cobra_mode_visuals"

    invoke-virtual {v0, v1}, Landroid/widget/LinearLayout;->findViewWithTag(Ljava/lang/Object;)Landroid/view/View;

    move-result-object v0

    if-eqz v0, :cond_11

    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "Visual settings, Ambient Mode "

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPrefs:Landroid/content/SharedPreferences;

    invoke-static {v2}, Lcom/projectinfinity/kodi/CobraPresentationEffects;->ambientMode(Landroid/content/SharedPreferences;)I

    move-result v2

    invoke-static {v2}, Lcom/projectinfinity/kodi/CobraPresentationEffects;->ambientLabel(I)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v2, ", Night Cinema "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPrefs:Landroid/content/SharedPreferences;

    const-string v5, "cobra_night_cinema"

    invoke-interface {v2, v5, v4}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z

    move-result v2

    if-eqz v2, :cond_10

    const-string v2, "on"

    goto :goto_c

    :cond_10
    const-string v2, "off"

    :goto_c
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/view/View;->setContentDescription(Ljava/lang/CharSequence;)V

    .line 10154
    :cond_11
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraModeSub:Landroid/widget/TextView;

    if-eqz v0, :cond_12

    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "COBRA LIVE  \u00b7  "

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {}, Ljava/util/Locale;->getDefault()Ljava/util/Locale;

    move-result-object v2

    new-array v3, v3, [Ljava/lang/Object;

    iget-object v5, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mChannels:Ljava/util/ArrayList;

    invoke-virtual {v5}, Ljava/util/ArrayList;->size()I

    move-result v5

    invoke-static {v5}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v5

    aput-object v5, v3, v4

    const-string v4, "%,d"

    invoke-static {v2, v4, v3}, Ljava/lang/String;->format(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v2, " CHANNELS"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 10156
    :cond_12
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideRuler:Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraGuideRuler;

    if-eqz v0, :cond_13

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraGuideRuler;->invalidate()V

    :cond_13
    :goto_d
    return-void
.end method
