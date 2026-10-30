.method private cobraChannelsForCurrentView()Ljava/util/ArrayList;
    .registers 13
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()",
            "Ljava/util/ArrayList<",
            "Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;",
            ">;"
        }
    .end annotation

iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCategory:Ljava/lang/String;
    if-nez v0, :category_ready
    const-string v0, "ALL"
    :category_ready
    const-string v1, "FAVORITES"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    const-string v2, "RECENT"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    const-string v3, "MY:"
    invoke-virtual {v0, v3}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v3
    if-nez v1, :use_all_category
    if-nez v2, :use_all_category
    if-eqz v3, :filter_channels
    :use_all_category
    const-string v4, "ALL"
    iput-object v4, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCategory:Ljava/lang/String;
    :filter_channels
    invoke-direct {p0, v1, v2}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->filteredChannels(ZZ)Ljava/util/List;
    move-result-object v4
    check-cast v4, Ljava/util/ArrayList;
    iput-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCategory:Ljava/lang/String;
    invoke-virtual {v4}, Ljava/util/ArrayList;->size()I
    move-result v9
    if-eqz v9, :return_channels

    iget-object v6, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPrefs:Landroid/content/SharedPreferences;
    const-string v5, "cobra_hidden_channels"
    new-instance v11, Ljava/util/HashSet;
    invoke-direct {v11}, Ljava/util/HashSet;-><init>()V
    invoke-interface {v6, v5, v11}, Landroid/content/SharedPreferences;->getStringSet(Ljava/lang/String;Ljava/util/Set;)Ljava/util/Set;
    move-result-object v6
    const/4 v5, 0x0
    if-eqz v6, :hidden_ready
    invoke-interface {v6}, Ljava/util/Set;->isEmpty()Z
    move-result v11
    if-nez v11, :hidden_ready
    const/4 v5, 0x1
    :hidden_ready
    if-nez v5, :projection_filters_needed
    if-eqz v3, :return_channels
    :projection_filters_needed
    if-eqz v3, :no_custom_group
    const/4 v11, 0x3
    invoke-virtual {v0, v11}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v0
    goto :custom_group_ready
    :no_custom_group
    const-string v0, ""
    :custom_group_ready
    const/4 v7, 0x0
    const/4 v8, 0x0
    :next_channel
    if-ge v7, v9, :trim_channels
    invoke-virtual {v4, v7}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;
    move-result-object v10
    check-cast v10, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;
    if-eqz v5, :check_custom_group
    invoke-direct {p0, v10}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraChannelKey(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;
    move-result-object v11
    invoke-interface {v6, v11}, Ljava/util/Set;->contains(Ljava/lang/Object;)Z
    move-result v11
    if-nez v11, :advance_read
    :check_custom_group
    if-eqz v3, :keep_channel
    invoke-direct {p0, v10}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraCustomGroup(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;
    move-result-object v11
    invoke-virtual {v0, v11}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v11
    if-eqz v11, :advance_read
    :keep_channel
    if-eq v7, v8, :advance_write
    invoke-virtual {v4, v8, v10}, Ljava/util/ArrayList;->set(ILjava/lang/Object;)Ljava/lang/Object;
    :advance_write
    add-int/lit8 v8, v8, 0x1
    :advance_read
    add-int/lit8 v7, v7, 0x1
    goto :next_channel
    :trim_channels
    if-eq v8, v9, :return_channels
    invoke-virtual {v4, v8, v9}, Ljava/util/ArrayList;->subList(II)Ljava/util/List;
    move-result-object v5
    invoke-interface {v5}, Ljava/util/List;->clear()V
    :return_channels
    return-object v4
.end method

.method private cobraGuideChannels()Ljava/util/ArrayList;
    .registers 8
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()",
            "Ljava/util/ArrayList<",
            "Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;",
            ">;"
        }
    .end annotation

invoke-direct {p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraChannelsForCurrentView()Ljava/util/ArrayList;
    move-result-object v0
    invoke-virtual {v0}, Ljava/util/ArrayList;->size()I
    move-result v4
    if-eqz v4, :return_channels
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideSource:Ljava/lang/String;
    invoke-virtual {v1}, Ljava/lang/String;->isEmpty()Z
    move-result v6
    if-nez v6, :return_channels
    const/4 v2, 0x0
    const/4 v3, 0x0
    :next_channel
    if-ge v2, v4, :trim_channels
    invoke-virtual {v0, v2}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;
    move-result-object v5
    check-cast v5, Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;
    invoke-direct {p0, v5}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->sourceIdForChannel(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)Ljava/lang/String;
    move-result-object v6
    invoke-virtual {v1, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v6
    if-eqz v6, :advance_read
    if-eq v2, v3, :advance_write
    invoke-virtual {v0, v3, v5}, Ljava/util/ArrayList;->set(ILjava/lang/Object;)Ljava/lang/Object;
    :advance_write
    add-int/lit8 v3, v3, 0x1
    :advance_read
    add-int/lit8 v2, v2, 0x1
    goto :next_channel
    :trim_channels
    if-eq v3, v4, :return_channels
    invoke-virtual {v0, v3, v4}, Ljava/util/ArrayList;->subList(II)Ljava/util/List;
    move-result-object v1
    invoke-interface {v1}, Ljava/util/List;->clear()V
    :return_channels
    return-object v0
.end method
