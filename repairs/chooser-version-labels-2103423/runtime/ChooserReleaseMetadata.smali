.class public final Lcom/projectinfinity/kodi/ChooserReleaseMetadata;
.super Ljava/lang/Object;
.source "ChooserReleaseMetadata.java"

.method public static updated(Landroid/content/Context;Z)Ljava/lang/String;
    .registers 8
    :try_start_0
    new-instance v0, Ljava/util/Properties;
    invoke-direct {v0}, Ljava/util/Properties;-><init>()V
    invoke-virtual {p0}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v1
    const-string v2, "experience-component-updates.properties"
    invoke-virtual {v1, v2}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v1
    invoke-virtual {v0, v1}, Ljava/util/Properties;->load(Ljava/io/InputStream;)V
    invoke-virtual {v1}, Ljava/io/InputStream;->close()V
    if-eqz p1, :inf_key
    const-string v2, "cobra.last_updated_in"
    goto :read
    :inf_key
    const-string v2, "infinity.last_updated_in"
    :read
    invoke-virtual {v0, v2}, Ljava/util/Properties;->getProperty(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v2
    if-eqz v2, :unavailable
    invoke-virtual {v2}, Ljava/lang/String;->length()I
    move-result v3
    if-lez v3, :unavailable
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
    const-string v4, "Last updated in "
    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    :try_end_0
    return-object v0
    :catch_any
    move-exception v0
    :unavailable
    const-string v0, "Update information unavailable"
    return-object v0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_any
.end method

.method public static installed(Landroid/content/Context;)Ljava/lang/String;
    .registers 7
    :try_start_0
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;
    move-result-object v0
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v1
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;
    move-result-object v0
    iget v1, v0, Landroid/content/pm/PackageInfo;->versionCode:I
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "App version "
    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    :try_end_0
    return-object v0
    :catch_any
    move-exception v0
    const-string v0, "App version unavailable"
    return-object v0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_any
.end method
