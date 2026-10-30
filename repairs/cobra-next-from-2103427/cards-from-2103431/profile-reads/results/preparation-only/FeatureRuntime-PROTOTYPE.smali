.class public final Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;
.super Ljava/lang/Object;
.source "InfinityCobraFeatureRuntime.java"


# static fields
.field public static final ACTION_RECORD:Ljava/lang/String; = "com.projectinfinity.cobra.RECORD"

.field public static final ACTION_REMINDER:Ljava/lang/String; = "com.projectinfinity.cobra.REMINDER"

.field public static final ACTION_RESCHEDULE:Ljava/lang/String; = "com.projectinfinity.cobra.RESCHEDULE"

.field public static final ACTION_STOP_RECORD:Ljava/lang/String; = "com.projectinfinity.cobra.STOP_RECORD"

.field private static final ACTIVE_PROFILE:Ljava/lang/String; = "active_profile"

.field public static final EXTRA_CHANNEL_ID:Ljava/lang/String; = "channel_id"

.field public static final EXTRA_END_AT:Ljava/lang/String; = "end_at"

.field public static final EXTRA_HEADERS:Ljava/lang/String; = "headers"

.field public static final EXTRA_NAME:Ljava/lang/String; = "name"

.field public static final EXTRA_PROGRAM:Ljava/lang/String; = "program"

.field public static final EXTRA_SESSION:Ljava/lang/String; = "session"

.field public static final EXTRA_SOURCE_ID:Ljava/lang/String; = "source_id"

.field public static final EXTRA_URL:Ljava/lang/String; = "url"

.field private static final HEALTH:Ljava/lang/String; = "health_snapshot"

.field private static final MIN_RECORD_FREE_BYTES:J = 0x10000000L

.field public static final PREFS:Ljava/lang/String; = "infinity_cobra_features_v2"

.field private static final PROFILES:Ljava/lang/String; = "profiles"

.field private static final RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/concurrent/ConcurrentHashMap<",
            "Ljava/lang/String;",
            "Ljava/lang/Object;",
            ">;"
        }
    .end annotation
.end field

.field private static final REMINDERS:Ljava/lang/String; = "reminders"

.field private static final SCHEDULES:Ljava/lang/String; = "recording_schedules"

.field private static final SOURCE_META:Ljava/lang/String; = "source_meta"


# instance fields
.field private final context:Landroid/content/Context;

.field private final prefs:Landroid/content/SharedPreferences;


# direct methods
.method static constructor <clinit>()V
    .registers 1

    .line 259
    new-instance v0, Ljava/util/concurrent/ConcurrentHashMap;

    invoke-direct {v0}, Ljava/util/concurrent/ConcurrentHashMap;-><init>()V

    sput-object v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;)V
    .registers 4

    .line 60
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 61
    invoke-virtual {p1}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    iput-object p1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-string v0, "infinity_cobra_features_v2"

    const/4 v1, 0x0

    .line 62
    invoke-static {p1, v0, v1}, Lcom/projectinfinity/kodi/CobraJavaPersistence;->preferences(Landroid/content/Context;Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object p1

    iput-object p1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    .line 63
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->ensureDefaultProfile()V

    return-void
.end method

.method private addReminderLocked(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)Ljava/lang/String;
    .registers 10

    const-string v0, ""

    .line 359
    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "rem-"

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    invoke-static {v2, v3}, Ljava/lang/Long;->toHexString(J)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    .line 360
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    :try_start_0
    const-string v3, "id"

    .line 362
    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v3, "source_id"

    if-nez p1, :cond_0

    move-object p1, v0

    .line 363
    :cond_0
    invoke-virtual {v2, v3, p1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "channel_id"

    if-nez p2, :cond_1

    move-object p2, v0

    .line 364
    :cond_1
    invoke-virtual {v2, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "program"

    const-string p2, "Programme"

    .line 365
    invoke-static {p3, p2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->cleanName(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v2, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "when"

    .line 366
    invoke-virtual {v2, p1, p4, p5}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    .line 367
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object p1

    .line 368
    invoke-virtual {p1, v2}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    .line 369
    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p2

    const-string p3, "reminders"

    invoke-virtual {p1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-interface {p2, p3, p1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 370
    invoke-direct {p0, v2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->scheduleReminderAlarm(Lorg/json/JSONObject;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v1

    :catch_0
    return-object v0
.end method

.method private static cleanName(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    if-nez p0, :cond_0

    const-string p0, ""

    goto :goto_0

    .line 559
    :cond_0
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    .line 560
    :goto_0
    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_1

    goto :goto_1

    :cond_1
    move-object p1, p0

    .line 561
    :goto_1
    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result p0

    const/16 v0, 0x78

    if-le p0, v0, :cond_2

    const/4 p0, 0x0

    invoke-virtual {p1, p0, v0}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object p1

    :cond_2
    return-object p1
.end method

.method public static hashId(Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    if-eqz p0, :cond_1

    .line 479
    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 480
    :cond_0
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sha256(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    const/4 v0, 0x0

    const/16 v1, 0xc

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object p0

    return-object p0

    :cond_1
    :goto_0
    const-string p0, ""

    return-object p0
.end method

.method private static headersJson(Ljava/util/Map;)Ljava/lang/String;
    .registers 4
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Ljava/util/Map<",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            ">;)",
            "Ljava/lang/String;"
        }
    .end annotation

    .line 549
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    if-eqz p0, :cond_0

    .line 551
    invoke-interface {p0}, Ljava/util/Map;->entrySet()Ljava/util/Set;

    move-result-object p0

    invoke-interface {p0}, Ljava/util/Set;->iterator()Ljava/util/Iterator;

    move-result-object p0

    :goto_0
    invoke-interface {p0}, Ljava/util/Iterator;->hasNext()Z

    move-result v1

    if-eqz v1, :cond_0

    invoke-interface {p0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Ljava/util/Map$Entry;

    .line 552
    :try_start_0
    invoke-interface {v1}, Ljava/util/Map$Entry;->getKey()Ljava/lang/Object;

    move-result-object v2

    check-cast v2, Ljava/lang/String;

    invoke-interface {v1}, Ljava/util/Map$Entry;->getValue()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v2, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :catch_0
    nop

    goto :goto_0

    .line 555
    :cond_0
    invoke-virtual {v0}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static inside(Ljava/io/File;Ljava/io/File;)Z
    .registers 3
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 543
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {p0}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;

    move-result-object p0

    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    sget-object p0, Ljava/io/File;->separator:Ljava/lang/String;

    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    .line 544
    invoke-virtual {p1}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;

    move-result-object p1

    .line 545
    invoke-virtual {p1, p0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result p0

    return p0
.end method

.method static synthetic lambda$recordings$0(Ljava/io/File;Ljava/io/File;)I
    .registers 4

    .line 209
    invoke-virtual {p1}, Ljava/io/File;->lastModified()J

    move-result-wide v0

    invoke-virtual {p0}, Ljava/io/File;->lastModified()J

    move-result-wide p0

    invoke-static {v0, v1, p0, p1}, Ljava/lang/Long;->compare(JJ)I

    move-result p0

    return p0
.end method

.method static recordingFinished(Ljava/lang/String;Ljava/lang/Object;)V
    .registers 4

    if-eqz p0, :cond_2

    .line 263
    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    :cond_0
    if-eqz p1, :cond_1

    .line 264
    sget-object v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;

    invoke-virtual {v0, p0, p1}, Ljava/util/concurrent/ConcurrentHashMap;->remove(Ljava/lang/Object;Ljava/lang/Object;)Z

    return-void

    .line 265
    :cond_1
    sget-object p1, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;

    invoke-virtual {p1, p0}, Ljava/util/concurrent/ConcurrentHashMap;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v0

    instance-of v1, v0, Ljava/lang/Long;

    if-eqz v1, :cond_2

    invoke-virtual {p1, p0, v0}, Ljava/util/concurrent/ConcurrentHashMap;->remove(Ljava/lang/Object;Ljava/lang/Object;)Z

    :cond_2
    :goto_0
    return-void
.end method

.method private recordingPendingIntent(Ljava/lang/String;Landroid/content/Intent;)Landroid/app/PendingIntent;
    .registers 6

    .line 504
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v1, 0x17

    if-lt v0, v1, :cond_0

    const/high16 v0, 0xc000000

    goto :goto_0

    :cond_0
    const/high16 v0, 0x8000000

    .line 505
    :goto_0
    invoke-virtual {p1}, Ljava/lang/String;->hashCode()I

    move-result p1

    invoke-static {p1}, Ljava/lang/Math;->abs(I)I

    move-result p1

    .line 506
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v2, 0x1a

    if-lt v1, v2, :cond_1

    .line 507
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {v1, p1, p2, v0}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;

    move-result-object p1

    return-object p1

    .line 509
    :cond_1
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {v1, p1, p2, v0}, Landroid/app/PendingIntent;->getService(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;

    move-result-object p1

    return-object p1
.end method

.method static recordingRequested(Ljava/lang/String;)V
    .registers 6

    .line 260
    sget-object v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v1

    const-wide/16 v3, 0x7530

    add-long/2addr v1, v3

    invoke-static {v1, v2}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v1

    invoke-virtual {v0, p0, v1}, Ljava/util/concurrent/ConcurrentHashMap;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    return-void
.end method

.method static recordingStarted(Ljava/lang/String;Ljava/lang/Object;)V
    .registers 3

    .line 261
    sget-object v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;

    invoke-virtual {v0, p0, p1}, Ljava/util/concurrent/ConcurrentHashMap;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    return-void
.end method

.method public static redact(Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    .line 474
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCobraDiagnostics;->redact(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 475
    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v0

    const/16 v1, 0x1f4

    if-le v0, v1, :cond_0

    const/4 v0, 0x0

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object p0

    :cond_0
    return-object p0
.end method

.method private reminderPendingIntent(Ljava/lang/String;)Landroid/app/PendingIntent;
    .registers 5

    .line 533
    new-instance v0, Landroid/content/Intent;

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-class v2, Lcom/projectinfinity/kodi/InfinityCobraReminderReceiver;

    invoke-direct {v0, v1, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v1, "com.projectinfinity.cobra.REMINDER"

    .line 534
    invoke-virtual {v0, v1}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v0

    const-string v1, "sports:"

    .line 535
    invoke-virtual {p1, v1}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v1

    if-eqz v1, :cond_0

    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "cobra-reminder:"

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v1

    goto :goto_0

    :cond_0
    const/4 v1, 0x0

    :goto_0
    invoke-virtual {v0, v1}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    move-result-object v0

    const-string v1, "id"

    .line 536
    invoke-virtual {v0, v1, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v0

    .line 538
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v2, 0x17

    if-lt v1, v2, :cond_1

    const/high16 v1, 0xc000000

    goto :goto_1

    :cond_1
    const/high16 v1, 0x8000000

    .line 539
    :goto_1
    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-virtual {p1}, Ljava/lang/String;->hashCode()I

    move-result p1

    invoke-static {p1}, Ljava/lang/Math;->abs(I)I

    move-result p1

    invoke-static {v2, p1, v0, v1}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;

    move-result-object p1

    return-object p1
.end method

.method private removeReminderLocked(Ljava/lang/String;)V
    .registers 7

    .line 432
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object v0

    .line 433
    new-instance v1, Lorg/json/JSONArray;

    invoke-direct {v1}, Lorg/json/JSONArray;-><init>()V

    const/4 v2, 0x0

    .line 434
    :goto_0
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v3

    if-ge v2, v3, :cond_1

    .line 435
    invoke-virtual {v0, v2}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v3

    if-eqz v3, :cond_0

    const-string v4, "id"

    .line 436
    invoke-virtual {v3, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {p1, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v4

    if-nez v4, :cond_0

    invoke-virtual {v1, v3}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    :cond_0
    add-int/lit8 v2, v2, 0x1

    goto :goto_0

    .line 438
    :cond_1
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v2, "reminders"

    invoke-virtual {v1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 439
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-string v1, "alarm"

    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/app/AlarmManager;

    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminderPendingIntent(Ljava/lang/String;)Landroid/app/PendingIntent;

    move-result-object p1

    invoke-virtual {v0, p1}, Landroid/app/AlarmManager;->cancel(Landroid/app/PendingIntent;)V

    return-void
.end method

.method private static safe(Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    if-nez p0, :cond_0

    const-string p0, ""

    return-object p0

    :cond_0
    const-string v0, "[\\r\\n\\t]+"

    const-string v1, " "

    .line 572
    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    .line 573
    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v0

    const/16 v1, 0xa0

    if-le v0, v1, :cond_1

    const/4 v0, 0x0

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object p0

    :cond_1
    return-object p0
.end method

.method private static safeFileName(Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    const-string v0, "[^A-Za-z0-9._ -]+"

    const-string v1, "_"

    .line 566
    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    .line 567
    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    const-string p0, "Recording"

    :cond_0
    return-object p0
.end method

.method private scheduleAlarm(Lorg/json/JSONObject;)V
    .registers 12

    const-string v0, "channel_id"

    const-string v1, "source_id"

    const-string v2, "end_at"

    const-string v3, "headers"

    const-string v4, "name"

    const-string v5, "url"

    :try_start_0
    const-string v6, "id"

    .line 485
    invoke-virtual {p1, v6}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 486
    new-instance v7, Landroid/content/Intent;

    iget-object v8, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-class v9, Lcom/projectinfinity/kodi/InfinityCobraRecordingService;

    invoke-direct {v7, v8, v9}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v8, "com.projectinfinity.cobra.RECORD"

    .line 487
    invoke-virtual {v7, v8}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v7

    const-string v8, "session"

    .line 488
    invoke-virtual {v7, v8, v6}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v7

    .line 489
    invoke-virtual {p1, v5}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v8

    invoke-virtual {v7, v5, v8}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v5

    .line 490
    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    invoke-virtual {v5, v4, v7}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v4

    const-string/jumbo v5, "{}"

    .line 491
    invoke-virtual {p1, v3, v5}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v4, v3, v5}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v3

    const-wide/16 v4, 0x0

    .line 492
    invoke-virtual {p1, v2, v4, v5}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v7

    invoke-virtual {v3, v2, v7, v8}, Landroid/content/Intent;->putExtra(Ljava/lang/String;J)Landroid/content/Intent;

    move-result-object v2

    .line 493
    invoke-virtual {p1, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, v1, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v1

    .line 494
    invoke-virtual {p1, v0}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v0, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v0

    .line 495
    invoke-direct {p0, v6, v0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingPendingIntent(Ljava/lang/String;Landroid/content/Intent;)Landroid/app/PendingIntent;

    move-result-object v0

    .line 496
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-string v2, "alarm"

    invoke-virtual {v1, v2}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Landroid/app/AlarmManager;

    .line 497
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    const-wide/16 v6, 0x3e8

    add-long/2addr v2, v6

    const-string v6, "start_at"

    invoke-virtual {p1, v6, v4, v5}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v4

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v2

    const/4 p1, 0x0

    .line 498
    invoke-static {v1, p1, v2, v3, v0}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Landroid/app/AlarmManager;IJLandroid/app/PendingIntent;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method

.method private scheduleReminderAlarm(Lorg/json/JSONObject;)V
    .registers 11

    const-string v0, "program"

    const-string v1, "channel_id"

    const-string v2, "source_id"

    const-string v3, "sports_game"

    const-string v4, "id"

    const-string v5, "cobra-reminder:"

    .line 514
    :try_start_0
    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    invoke-direct {p0, v6}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminderPendingIntent(Ljava/lang/String;)Landroid/app/PendingIntent;

    .line 515
    new-instance v6, Landroid/content/Intent;

    iget-object v7, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-class v8, Lcom/projectinfinity/kodi/InfinityCobraReminderReceiver;

    invoke-direct {v6, v7, v8}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v7, "com.projectinfinity.cobra.REMINDER"

    .line 516
    invoke-virtual {v6, v7}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v6

    .line 517
    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    invoke-virtual {v6, v4, v7}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v6

    .line 518
    invoke-virtual {p1, v3}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v7

    if-eqz v7, :cond_0

    new-instance v7, Ljava/lang/StringBuilder;

    invoke-direct {v7, v5}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v7, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    invoke-static {v5}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v5

    goto :goto_0

    :cond_0
    const/4 v5, 0x0

    :goto_0
    invoke-virtual {v6, v5}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    move-result-object v5

    .line 519
    invoke-virtual {p1, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    invoke-virtual {v5, v3, v6}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v3

    .line 520
    invoke-virtual {p1, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v3, v2, v5}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v2

    .line 521
    invoke-virtual {p1, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, v1, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v1

    .line 522
    invoke-virtual {p1, v0}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v0, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v0

    .line 524
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v2, 0x17

    if-lt v1, v2, :cond_1

    const/high16 v1, 0xc000000

    goto :goto_1

    :cond_1
    const/high16 v1, 0x8000000

    .line 525
    :goto_1
    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/String;->hashCode()I

    move-result v3

    invoke-static {v3}, Ljava/lang/Math;->abs(I)I

    move-result v3

    invoke-static {v2, v3, v0, v1}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;

    move-result-object v0

    .line 526
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-string v2, "alarm"

    invoke-virtual {v1, v2}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Landroid/app/AlarmManager;

    .line 528
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    const-wide/16 v4, 0x3e8

    add-long/2addr v2, v4

    const-string v4, "when"

    const-wide/16 v5, 0x0

    invoke-virtual {p1, v4, v5, v6}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v4

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v2

    const/4 p1, 0x0

    .line 527
    invoke-static {v1, p1, v2, v3, v0}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Landroid/app/AlarmManager;IJLandroid/app/PendingIntent;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method

.method private static sha256(Ljava/lang/String;)Ljava/lang/String;
    .registers 9

    :try_start_0
    const-string v0, "SHA-256"

    .line 582
    invoke-static {v0}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;

    move-result-object v0

    .line 583
    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p0, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p0

    invoke-virtual {v0, p0}, Ljava/security/MessageDigest;->digest([B)[B

    move-result-object p0

    .line 584
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 585
    array-length v1, p0

    const/4 v2, 0x0

    const/4 v3, 0x0

    :goto_0
    if-ge v3, v1, :cond_0

    aget-byte v4, p0, v3

    sget-object v5, Ljava/util/Locale;->US:Ljava/util/Locale;

    const-string v6, "%02x"

    const/4 v7, 0x1

    new-array v7, v7, [Ljava/lang/Object;

    invoke-static {v4}, Ljava/lang/Byte;->valueOf(B)Ljava/lang/Byte;

    move-result-object v4

    aput-object v4, v7, v2

    invoke-static {v5, v6, v7}, Ljava/lang/String;->format(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 586
    :cond_0
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object p0

    :catch_0
    const-string p0, "00000000000000000000000000000000"

    return-object p0
.end method

.method private static writeAtomic(Ljava/io/File;[B)V
    .registers 2
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 577
    invoke-static {p0, p1}, Lcom/projectinfinity/kodi/CobraDiagnosticArchive;->atomicWrite(Ljava/io/File;[B)V

    return-void
.end method


# virtual methods
.method public activeProfileId()Ljava/lang/String;
    .registers 4

    .line 67
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string v1, "active_profile"

    const-string v2, "default"

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    return-object v0
.end method

.method public addReminder(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)Ljava/lang/String;
    .registers 7

    .line 356
    const-class v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;

    monitor-enter v0

    :try_start_0
    invoke-direct/range {p0 .. p5}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->addReminderLocked(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)Ljava/lang/String;

    move-result-object p1

    monitor-exit v0

    return-object p1

    :catchall_0
    move-exception p1

    monitor-exit v0
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    throw p1
.end method

.method public adultLocked()Z
    .registers 3

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->activeProfileId()Ljava/lang/String;
    move-result-object v0
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;
    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/CobraProfileDataReuse;->adultLocked(Ljava/lang/String;Landroid/content/SharedPreferences;)Z
    move-result v0
    return v0
.end method

.method public consumeSportsReminder(Ljava/lang/String;)Z
    .registers 13

    .line 417
    const-class v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;

    monitor-enter v0

    .line 418
    :try_start_0
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object v1

    const/4 v2, 0x0

    const/4 v3, 0x0

    :goto_0
    invoke-virtual {v1}, Lorg/json/JSONArray;->length()I

    move-result v4

    if-ge v3, v4, :cond_4

    invoke-virtual {v1, v3}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v4

    if-eqz v4, :cond_3

    const-string v5, "id"

    .line 419
    invoke-virtual {v4, v5}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {p1, v5}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v5

    if-nez v5, :cond_0

    goto :goto_2

    .line 420
    :cond_0
    new-instance p1, Lcom/projectinfinity/kodi/CobraSportsPreferences;

    iget-object v3, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-direct {p1, v3}, Lcom/projectinfinity/kodi/CobraSportsPreferences;-><init>(Landroid/content/Context;)V

    const-string v3, "delivered"

    .line 421
    invoke-virtual {v4, v3}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;)Z

    move-result v3

    if-nez v3, :cond_2

    const-string v3, "when"

    invoke-virtual {v4, v3}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J

    move-result-wide v5

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v7

    const-wide/16 v9, 0x3e8

    add-long/2addr v7, v9

    cmp-long v3, v5, v7

    if-gtz v3, :cond_2

    const-string v3, "start"

    invoke-virtual {v4, v3}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J

    move-result-wide v5

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v7

    const-wide/32 v9, 0xea60

    sub-long/2addr v7, v9

    cmp-long v3, v5, v7

    if-ltz v3, :cond_2

    const-string v3, "manual"

    .line 422
    invoke-virtual {v4, v3}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;)Z

    move-result v3

    if-nez v3, :cond_1

    const-string v3, "away"

    invoke-virtual {v4, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    const-string v5, "home"

    invoke-virtual {v4, v5}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {p1, v3, v5}, Lcom/projectinfinity/kodi/CobraSportsPreferences;->automatic(Ljava/lang/String;Ljava/lang/String;)Z

    move-result p1
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    if-nez p1, :cond_1

    goto :goto_1

    :cond_1
    :try_start_1
    const-string p1, "delivered"

    const/4 v3, 0x1

    .line 423
    invoke-virtual {v4, p1, v3}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    iget-object p1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    const-string v4, "reminders"

    invoke-virtual {v1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-interface {p1, v4, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->commit()Z
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_0
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    :try_start_2
    monitor-exit v0

    return v3

    :catch_0
    monitor-exit v0

    return v2

    .line 422
    :cond_2
    :goto_1
    monitor-exit v0

    return v2

    :cond_3
    :goto_2
    add-int/lit8 v3, v3, 0x1

    goto/16 :goto_0

    .line 424
    :cond_4
    monitor-exit v0

    return v2

    :catchall_0
    move-exception p1

    .line 425
    monitor-exit v0
    :try_end_2
    .catchall {:try_start_2 .. :try_end_2} :catchall_0

    throw p1
.end method

.method public createProfile(Ljava/lang/String;Ljava/lang/String;Z)Ljava/lang/String;
    .registers 10

    const-string v0, ""

    .line 98
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->profiles()Lorg/json/JSONArray;

    move-result-object v1

    .line 99
    new-instance v2, Ljava/lang/StringBuilder;

    const-string v3, "p"

    invoke-direct {v2, v3}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v3

    invoke-static {v3, v4}, Ljava/lang/Long;->toHexString(J)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    .line 100
    new-instance v3, Lorg/json/JSONObject;

    invoke-direct {v3}, Lorg/json/JSONObject;-><init>()V

    :try_start_0
    const-string v4, "id"

    .line 102
    invoke-virtual {v3, v4, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v4, "name"

    const-string v5, "Profile"

    .line 103
    invoke-static {p1, v5}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->cleanName(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v3, v4, p1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "pin_hash"

    if-eqz p2, :cond_1

    .line 104
    invoke-virtual {p2}, Ljava/lang/String;->isEmpty()Z

    move-result v4

    if-eqz v4, :cond_0

    goto :goto_0

    :cond_0
    invoke-static {p2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sha256(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    goto :goto_1

    :cond_1
    :goto_0
    move-object p2, v0

    :goto_1
    invoke-virtual {v3, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "adult_locked"

    .line 105
    invoke-virtual {v3, p1, p3}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    .line 106
    invoke-virtual {v1, v3}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    .line 107
    iget-object p1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    const-string p2, "profiles"

    invoke-virtual {v1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object p3

    invoke-interface {p1, p2, p3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v2

    :catch_0
    return-object v0
.end method

.method public deleteRecording(Ljava/lang/String;)Z
    .registers 5

    const-string v0, "InfinityCobraFeatureRuntime:220"

    .line 225
    invoke-static {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier;->enter(Ljava/lang/String;)Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;

    move-result-object v0

    const/4 v1, 0x0

    .line 228
    :try_start_0
    new-instance v2, Ljava/io/File;

    invoke-direct {v2, p1}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    .line 229
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object p1

    invoke-static {p1, v2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->inside(Ljava/io/File;Ljava/io/File;)Z

    move-result p1

    if-eqz p1, :cond_2

    invoke-virtual {v2}, Ljava/io/File;->isFile()Z

    move-result p1

    if-nez p1, :cond_0

    goto :goto_0

    .line 230
    :cond_0
    invoke-static {v2}, Lcom/projectinfinity/kodi/CobraJavaPersistence;->delete(Ljava/io/File;)Z

    move-result p1
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    if-eqz v0, :cond_1

    .line 235
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_1
    return p1

    :cond_2
    :goto_0
    if-eqz v0, :cond_3

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_3
    return v1

    :catchall_0
    move-exception p1

    if-eqz v0, :cond_4

    .line 225
    :try_start_1
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_1

    goto :goto_1

    :catchall_1
    move-exception v0

    invoke-virtual {p1, v0}, Ljava/lang/Throwable;->addSuppressed(Ljava/lang/Throwable;)V

    :cond_4
    :goto_1
    throw p1

    :catch_0
    nop

    if-eqz v0, :cond_5

    .line 235
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_5
    return v1
.end method

.method public ensureDefaultProfile()V
    .registers 6

    const-string v0, "default"

    .line 83
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->profiles()Lorg/json/JSONArray;

    move-result-object v1

    .line 84
    invoke-virtual {v1}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-lez v2, :cond_0

    return-void

    .line 85
    :cond_0
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    :try_start_0
    const-string v3, "id"

    .line 87
    invoke-virtual {v2, v3, v0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v3, "name"

    const-string v4, "Main"

    .line 88
    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v3, "pin_hash"

    const-string v4, ""

    .line 89
    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v3, "adult_locked"

    const/4 v4, 0x0

    .line 90
    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    .line 91
    invoke-virtual {v1, v2}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    .line 92
    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {v2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v2

    const-string v3, "profiles"

    invoke-virtual {v1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-interface {v2, v3, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v1

    const-string v2, "active_profile"

    .line 93
    invoke-interface {v1, v2, v0}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method

.method public hasRecordingSpace()Z
    .registers 6

    .line 199
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object v0

    .line 200
    invoke-virtual {v0}, Ljava/io/File;->getUsableSpace()J

    move-result-wide v0

    const-wide/32 v2, 0x10000000

    cmp-long v4, v0, v2

    if-ltz v4, :cond_0

    const/4 v0, 0x1

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0
.end method

.method public healthSnapshot()Ljava/lang/String;
    .registers 4

    .line 470
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string v1, "health_snapshot"

    const-string/jumbo v2, "{}"

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    return-object v0
.end method

.method public looksAdult(Ljava/lang/String;)Z
    .registers 4

    .line 140
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->adultLocked()Z

    move-result v0

    const/4 v1, 0x0

    if-eqz v0, :cond_2

    if-nez p1, :cond_0

    goto :goto_0

    .line 141
    :cond_0
    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p1, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p1

    const-string v0, "adult"

    .line 142
    invoke-virtual {p1, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "18+"

    invoke-virtual {p1, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string/jumbo v0, "xxx"

    invoke-virtual {p1, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "porn"

    .line 143
    invoke-virtual {p1, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "erotic"

    invoke-virtual {p1, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-eqz p1, :cond_2

    :cond_1
    const/4 v1, 0x1

    :cond_2
    :goto_0
    return v1
.end method

.method public profileKey(Ljava/lang/String;)Ljava/lang/String;
    .registers 4

    .line 71
    new-instance v0, Ljava/lang/StringBuilder;

    const-string v1, "profile:"

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->activeProfileId()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v1, ":"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    return-object p1
.end method

.method public profiles()Lorg/json/JSONArray;
    .registers 5

    .line 76
    :try_start_0
    new-instance v0, Lorg/json/JSONArray;

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string v2, "profiles"

    const-string v3, "[]"

    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Lorg/json/JSONArray;-><init>(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v0

    .line 78
    :catch_0
    new-instance v0, Lorg/json/JSONArray;

    invoke-direct {v0}, Lorg/json/JSONArray;-><init>()V

    return-object v0
.end method

.method public reconcileSportsReminders()V
    .registers 17

    move-object/from16 v10, p0

    .line 405
    const-class v11, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;

    monitor-enter v11

    .line 406
    :try_start_0
    new-instance v0, Lcom/projectinfinity/kodi/CobraSportsPreferences;

    iget-object v1, v10, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-direct {v0, v1}, Lcom/projectinfinity/kodi/CobraSportsPreferences;-><init>(Landroid/content/Context;)V

    invoke-virtual/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object v12

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v13

    const/4 v1, 0x0

    const/4 v15, 0x0

    .line 407
    :goto_0
    invoke-virtual {v12}, Lorg/json/JSONArray;->length()I

    move-result v1

    if-ge v15, v1, :cond_3

    invoke-virtual {v12, v15}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v1

    if-eqz v1, :cond_2

    const-string v2, "sports_game"

    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_0

    goto :goto_1

    :cond_0
    const-string v2, "start"

    .line 408
    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J

    move-result-wide v2

    cmp-long v4, v2, v13

    if-gtz v4, :cond_1

    const-string v2, "id"

    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v10, v1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->removeReminder(Ljava/lang/String;)V

    goto :goto_1

    :cond_1
    const-string v2, "sports_game"

    .line 409
    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    const-string v3, "away"

    invoke-virtual {v1, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    const-string v4, "home"

    invoke-virtual {v1, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    const-string v5, "program"

    invoke-virtual {v1, v5}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    const-string v6, "start"

    .line 410
    invoke-virtual {v1, v6}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J

    move-result-wide v6

    const-string v8, "away"

    invoke-virtual {v1, v8}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v8

    const-string v9, "home"

    invoke-virtual {v1, v9}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v9

    invoke-virtual {v0, v8, v9}, Lcom/projectinfinity/kodi/CobraSportsPreferences;->automatic(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v8

    const-string v9, "manual"

    invoke-virtual {v1, v9}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;)Z

    move-result v9

    move-object/from16 v1, p0

    .line 409
    invoke-virtual/range {v1 .. v9}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sportsReminder(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;JZZ)V

    :cond_2
    :goto_1
    add-int/lit8 v15, v15, 0x1

    goto :goto_0

    .line 412
    :cond_3
    monitor-exit v11

    return-void

    :catchall_0
    move-exception v0

    monitor-exit v11
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    throw v0
.end method

.method public recordingActive(Ljava/lang/String;)Z
    .registers 10

    const/4 v0, 0x0

    if-eqz p1, :cond_2

    .line 268
    invoke-virtual {p1}, Ljava/lang/String;->isEmpty()Z

    move-result v1

    if-eqz v1, :cond_0

    goto :goto_0

    :cond_0
    sget-object v1, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->RECORDING_OWNERS:Ljava/util/concurrent/ConcurrentHashMap;

    invoke-virtual {v1, p1}, Ljava/util/concurrent/ConcurrentHashMap;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v2

    .line 269
    instance-of v3, v2, Ljava/lang/Long;

    if-eqz v3, :cond_1

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v3

    move-object v5, v2

    check-cast v5, Ljava/lang/Long;

    invoke-virtual {v5}, Ljava/lang/Long;->longValue()J

    move-result-wide v5

    cmp-long v7, v3, v5

    if-lez v7, :cond_1

    invoke-virtual {v1, p1, v2}, Ljava/util/concurrent/ConcurrentHashMap;->remove(Ljava/lang/Object;Ljava/lang/Object;)Z

    return v0

    :cond_1
    if-eqz v2, :cond_2

    const/4 v0, 0x1

    :cond_2
    :goto_0
    return v0
.end method

.method public recordings()Lorg/json/JSONArray;
    .registers 8

    .line 204
    new-instance v0, Lorg/json/JSONArray;

    invoke-direct {v0}, Lorg/json/JSONArray;-><init>()V

    .line 205
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object v1

    invoke-virtual {v1}, Ljava/io/File;->listFiles()[Ljava/io/File;

    move-result-object v1

    if-nez v1, :cond_0

    return-object v0

    .line 207
    :cond_0
    new-instance v2, Ljava/util/ArrayList;

    invoke-direct {v2}, Ljava/util/ArrayList;-><init>()V

    .line 208
    invoke-static {v2, v1}, Ljava/util/Collections;->addAll(Ljava/util/Collection;[Ljava/lang/Object;)Z

    .line 209
    new-instance v1, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime$$ExternalSyntheticLambda4;

    invoke-direct {v1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime$$ExternalSyntheticLambda4;-><init>()V

    invoke-static {v2, v1}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Ljava/util/ArrayList;Ljava/util/Comparator;)V

    .line 210
    invoke-virtual {v2}, Ljava/util/ArrayList;->iterator()Ljava/util/Iterator;

    move-result-object v1

    :cond_1
    :goto_0
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z

    move-result v2

    if-eqz v2, :cond_3

    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v2

    check-cast v2, Ljava/io/File;

    .line 211
    invoke-virtual {v2}, Ljava/io/File;->isFile()Z

    move-result v3

    if-eqz v3, :cond_1

    invoke-virtual {v2}, Ljava/io/File;->getName()Ljava/lang/String;

    move-result-object v3

    const-string v4, ".json"

    invoke-virtual {v3, v4}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v3

    if-eqz v3, :cond_2

    goto :goto_0

    .line 212
    :cond_2
    new-instance v3, Lorg/json/JSONObject;

    invoke-direct {v3}, Lorg/json/JSONObject;-><init>()V

    :try_start_0
    const-string v4, "name"

    .line 214
    invoke-virtual {v2}, Ljava/io/File;->getName()Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v3, v4, v5}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v4, "path"

    .line 215
    invoke-virtual {v2}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v3, v4, v5}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v4, "size"

    .line 216
    invoke-virtual {v2}, Ljava/io/File;->length()J

    move-result-wide v5

    invoke-virtual {v3, v4, v5, v6}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    const-string v4, "modified"

    .line 217
    invoke-virtual {v2}, Ljava/io/File;->lastModified()J

    move-result-wide v5

    invoke-virtual {v3, v4, v5, v6}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    .line 218
    invoke-virtual {v0, v3}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :catch_0
    nop

    goto :goto_0

    :cond_3
    return-object v0
.end method

.method public recordingsDir()Ljava/io/File;
    .registers 5

    const-string v0, "InfinityCobraFeatureRuntime:186"

    .line 187
    invoke-static {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier;->enter(Ljava/lang/String;)Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;

    move-result-object v0

    .line 189
    :try_start_0
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    sget-object v2, Landroid/os/Environment;->DIRECTORY_MOVIES:Ljava/lang/String;

    invoke-virtual {v1, v2}, Landroid/content/Context;->getExternalFilesDir(Ljava/lang/String;)Ljava/io/File;

    move-result-object v1

    if-nez v1, :cond_0

    .line 190
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-virtual {v1}, Landroid/content/Context;->getFilesDir()Ljava/io/File;

    move-result-object v1

    .line 191
    :cond_0
    new-instance v2, Ljava/io/File;

    const-string v3, "CobraRecordings"

    invoke-direct {v2, v1, v3}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    .line 192
    invoke-virtual {v2}, Ljava/io/File;->isDirectory()Z

    move-result v1

    if-nez v1, :cond_1

    invoke-static {v2}, Lcom/projectinfinity/kodi/CobraJavaPersistence;->mkdirs(Ljava/io/File;)Z
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    :cond_1
    if-eqz v0, :cond_2

    .line 195
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_2
    return-object v2

    :catchall_0
    move-exception v1

    if-eqz v0, :cond_3

    .line 187
    :try_start_1
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_1

    goto :goto_0

    :catchall_1
    move-exception v0

    invoke-virtual {v1, v0}, Ljava/lang/Throwable;->addSuppressed(Ljava/lang/Throwable;)V

    :cond_3
    :goto_0
    throw v1
.end method

.method public reminders()Lorg/json/JSONArray;
    .registers 5

    .line 376
    :try_start_0
    new-instance v0, Lorg/json/JSONArray;

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string v2, "reminders"

    const-string v3, "[]"

    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Lorg/json/JSONArray;-><init>(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v0

    .line 377
    :catch_0
    new-instance v0, Lorg/json/JSONArray;

    invoke-direct {v0}, Lorg/json/JSONArray;-><init>()V

    return-object v0
.end method

.method public removeReminder(Ljava/lang/String;)V
    .registers 3

    .line 429
    const-class v0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;

    monitor-enter v0

    :try_start_0
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->removeReminderLocked(Ljava/lang/String;)V

    monitor-exit v0

    return-void

    :catchall_0
    move-exception p1

    monitor-exit v0
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    throw p1
.end method

.method public removeSchedule(Ljava/lang/String;)V
    .registers 7

    .line 344
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->schedules()Lorg/json/JSONArray;

    move-result-object v0

    .line 345
    new-instance v1, Lorg/json/JSONArray;

    invoke-direct {v1}, Lorg/json/JSONArray;-><init>()V

    const/4 v2, 0x0

    .line 346
    :goto_0
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v3

    if-ge v2, v3, :cond_1

    .line 347
    invoke-virtual {v0, v2}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v3

    if-eqz v3, :cond_0

    const-string v4, "id"

    .line 348
    invoke-virtual {v3, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {p1, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v4

    if-nez v4, :cond_0

    invoke-virtual {v1, v3}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    :cond_0
    add-int/lit8 v2, v2, 0x1

    goto :goto_0

    .line 350
    :cond_1
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v2, "recording_schedules"

    invoke-virtual {v1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 351
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-string v1, "alarm"

    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/app/AlarmManager;

    new-instance v1, Landroid/content/Intent;

    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-class v3, Lcom/projectinfinity/kodi/InfinityCobraRecordingService;

    invoke-direct {v1, v2, v3}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    .line 352
    invoke-direct {p0, p1, v1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingPendingIntent(Ljava/lang/String;Landroid/content/Intent;)Landroid/app/PendingIntent;

    move-result-object p1

    .line 351
    invoke-virtual {v0, p1}, Landroid/app/AlarmManager;->cancel(Landroid/app/PendingIntent;)V

    return-void
.end method

.method public renameRecording(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 10

    const-string v0, ".mp4"

    const-string v1, ""

    const-string v2, "InfinityCobraFeatureRuntime:230"

    .line 239
    invoke-static {v2}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier;->enter(Ljava/lang/String;)Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;

    move-result-object v2

    .line 242
    :try_start_0
    new-instance v3, Ljava/io/File;

    invoke-direct {v3, p1}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    .line 243
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object p1

    invoke-static {p1, v3}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->inside(Ljava/io/File;Ljava/io/File;)Z

    move-result p1

    if-eqz p1, :cond_5

    invoke-virtual {v3}, Ljava/io/File;->isFile()Z

    move-result p1

    if-nez p1, :cond_0

    goto :goto_1

    .line 244
    :cond_0
    invoke-virtual {v3}, Ljava/io/File;->getName()Ljava/lang/String;

    move-result-object p1

    sget-object v4, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p1, v4}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p1, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_1

    goto :goto_0

    :cond_1
    const-string v0, ".ts"

    .line 245
    :goto_0
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "Recording"

    invoke-static {p2, v4}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->cleanName(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-static {p2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->safeFileName(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {p1, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    .line 246
    new-instance p2, Ljava/io/File;

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object v0

    invoke-direct {p2, v0, p1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    .line 247
    invoke-virtual {p2}, Ljava/io/File;->exists()Z

    move-result v0

    if-eqz v0, :cond_2

    new-instance p2, Ljava/io/File;

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object v0

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v5

    invoke-virtual {v4, v5, v6}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    const-string v5, "-"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-direct {p2, v0, p1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    .line 248
    :cond_2
    invoke-static {v3, p2}, Lcom/projectinfinity/kodi/CobraJavaPersistence;->rename(Ljava/io/File;Ljava/io/File;)Z

    move-result p1

    if-eqz p1, :cond_3

    invoke-virtual {p2}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;

    move-result-object v1
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    :cond_3
    if-eqz v2, :cond_4

    .line 253
    invoke-virtual {v2}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_4
    return-object v1

    :cond_5
    :goto_1
    if-eqz v2, :cond_6

    invoke-virtual {v2}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_6
    return-object v1

    :catchall_0
    move-exception p1

    if-eqz v2, :cond_7

    .line 239
    :try_start_1
    invoke-virtual {v2}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_1

    goto :goto_2

    :catchall_1
    move-exception p2

    invoke-virtual {p1, p2}, Ljava/lang/Throwable;->addSuppressed(Ljava/lang/Throwable;)V

    :cond_7
    :goto_2
    throw p1

    :catch_0
    if-eqz v2, :cond_8

    .line 253
    invoke-virtual {v2}, Lcom/projectinfinity/kodi/CobraJavaWriteBarrier$Scope;->close()V

    :cond_8
    return-object v1
.end method

.method public rescheduleAll()V
    .registers 11

    .line 329
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {v0}, Lcom/projectinfinity/kodi/CobraSportsReminderJob;->schedule(Landroid/content/Context;)V

    .line 330
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->schedules()Lorg/json/JSONArray;

    move-result-object v0

    .line 331
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v1

    const/4 v3, 0x0

    const/4 v4, 0x0

    .line 332
    :goto_0
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v5

    const-wide/16 v6, 0x0

    if-ge v4, v5, :cond_1

    .line 333
    invoke-virtual {v0, v4}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v5

    if-eqz v5, :cond_0

    const-string v8, "end_at"

    .line 334
    invoke-virtual {v5, v8, v6, v7}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v6

    cmp-long v8, v6, v1

    if-lez v8, :cond_0

    invoke-direct {p0, v5}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->scheduleAlarm(Lorg/json/JSONObject;)V

    :cond_0
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 336
    :cond_1
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object v0

    .line 337
    :goto_1
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v4

    if-ge v3, v4, :cond_3

    .line 338
    invoke-virtual {v0, v3}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v4

    if-eqz v4, :cond_2

    const-string v5, "when"

    .line 339
    invoke-virtual {v4, v5, v6, v7}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v8

    cmp-long v5, v8, v1

    if-lez v5, :cond_2

    invoke-direct {p0, v4}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->scheduleReminderAlarm(Lorg/json/JSONObject;)V

    :cond_2
    add-int/lit8 v3, v3, 0x1

    goto :goto_1

    :cond_3
    return-void
.end method

.method public scheduleRecording(Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;JJLjava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 14
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            "Ljava/util/Map<",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            ">;JJ",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            ")",
            "Ljava/lang/String;"
        }
    .end annotation

    const-string v0, ""

    .line 302
    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "sched-"

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    invoke-static {v2, v3}, Ljava/lang/Long;->toHexString(J)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    .line 303
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    :try_start_0
    const-string v3, "id"

    .line 305
    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v3, "url"

    .line 306
    invoke-virtual {v2, v3, p1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "name"

    const-string v3, "Scheduled recording"

    .line 307
    invoke-static {p2, v3}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->cleanName(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v2, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "headers"

    .line 308
    invoke-static {p3}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->headersJson(Ljava/util/Map;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v2, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "start_at"

    .line 309
    invoke-virtual {v2, p1, p4, p5}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    const-string p1, "end_at"

    .line 310
    invoke-virtual {v2, p1, p6, p7}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    const-string p1, "source_id"

    if-nez p8, :cond_0

    move-object p8, v0

    .line 311
    :cond_0
    invoke-virtual {v2, p1, p8}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "channel_id"

    if-nez p9, :cond_1

    move-object p9, v0

    .line 312
    :cond_1
    invoke-virtual {v2, p1, p9}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 313
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->schedules()Lorg/json/JSONArray;

    move-result-object p1

    .line 314
    invoke-virtual {p1, v2}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    .line 315
    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p2

    const-string p3, "recording_schedules"

    invoke-virtual {p1}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-interface {p2, p3, p1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 316
    invoke-direct {p0, v2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->scheduleAlarm(Lorg/json/JSONObject;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v1

    :catch_0
    return-object v0
.end method

.method public schedules()Lorg/json/JSONArray;
    .registers 5

    .line 324
    :try_start_0
    new-instance v0, Lorg/json/JSONArray;

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string v2, "recording_schedules"

    const-string v3, "[]"

    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Lorg/json/JSONArray;-><init>(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v0

    .line 325
    :catch_0
    new-instance v0, Lorg/json/JSONArray;

    invoke-direct {v0}, Lorg/json/JSONArray;-><init>()V

    return-object v0
.end method

.method public setSourceMeta(Ljava/lang/String;ZLjava/lang/String;Ljava/lang/String;)V
    .registers 9

    const-string v0, "source_meta"

    .line 163
    :try_start_0
    new-instance v1, Lorg/json/JSONObject;

    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string/jumbo v3, "{}"

    invoke-interface {v2, v0, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-direct {v1, v2}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 164
    invoke-virtual {v1, p1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v2

    if-nez v2, :cond_0

    .line 165
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    :cond_0
    const-string v3, "enabled"

    .line 166
    invoke-virtual {v2, v3, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    const-string p2, "color"

    if-eqz p3, :cond_1

    .line 167
    invoke-virtual {p3}, Ljava/lang/String;->isEmpty()Z

    move-result v3

    if-eqz v3, :cond_2

    :cond_1
    const-string p3, "#FF4059"

    :cond_2
    invoke-virtual {v2, p2, p3}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p2, "icon"

    if-eqz p4, :cond_3

    .line 168
    invoke-virtual {p4}, Ljava/lang/String;->isEmpty()Z

    move-result p3

    if-eqz p3, :cond_4

    :cond_3
    const-string/jumbo p4, "\u25c8"

    :cond_4
    invoke-virtual {v2, p2, p4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 169
    invoke-virtual {v1, p1, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 170
    iget-object p1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-virtual {v1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p2

    invoke-interface {p1, v0, p2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method

.method public sourceColor(Ljava/lang/String;)Ljava/lang/String;
    .registers 4

    .line 179
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sourceMeta(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    const-string v0, "color"

    const-string v1, "#FF4059"

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    return-object p1
.end method

.method public sourceEnabled(Ljava/lang/String;)Z
    .registers 4

    .line 175
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sourceMeta(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    const-string v0, "enabled"

    const/4 v1, 0x1

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result p1

    return p1
.end method

.method public sourceIcon(Ljava/lang/String;)Ljava/lang/String;
    .registers 4

    .line 183
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sourceMeta(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    const-string v0, "icon"

    const-string/jumbo v1, "\u25c8"

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    return-object p1
.end method

.method public sourceMeta(Ljava/lang/String;)Lorg/json/JSONObject;
    .registers 6

    .line 148
    :try_start_0
    new-instance v0, Lorg/json/JSONObject;

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    const-string v2, "source_meta"

    const-string/jumbo v3, "{}"

    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 149
    invoke-virtual {v0, p1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    if-eqz p1, :cond_0

    return-object p1

    .line 152
    :catch_0
    :cond_0
    new-instance p1, Lorg/json/JSONObject;

    invoke-direct {p1}, Lorg/json/JSONObject;-><init>()V

    :try_start_1
    const-string v0, "enabled"

    const/4 v1, 0x1

    .line 154
    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    const-string v0, "color"

    const-string v1, "#FF4059"

    .line 155
    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string v0, "icon"

    const-string/jumbo v1, "\u25c8"

    .line 156
    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_1

    :catch_1
    return-object p1
.end method

.method public sportsReminder(Ljava/lang/String;)Lorg/json/JSONObject;
    .registers 6

    .line 401
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object v0

    const/4 v1, 0x0

    :goto_0
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v1, v2, :cond_1

    .line 402
    invoke-virtual {v0, v1}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v2

    if-eqz v2, :cond_0

    const-string v3, "sports_game"

    invoke-virtual {v2, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {p1, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-eqz v3, :cond_0

    return-object v2

    :cond_0
    add-int/lit8 v1, v1, 0x1

    goto :goto_0

    :cond_1
    const/4 p1, 0x0

    return-object p1
.end method

.method public sportsReminder(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;JZZ)V
    .registers 24

    move-object v1, p0

    move-object/from16 v0, p1

    move-wide/from16 v2, p5

    move/from16 v4, p7

    move/from16 v5, p8

    const-string v6, "sports:"

    .line 382
    const-class v7, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;

    monitor-enter v7

    .line 383
    :try_start_0
    new-instance v8, Ljava/lang/StringBuilder;

    invoke-direct {v8, v6}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {v8, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v6

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->reminders()Lorg/json/JSONArray;

    move-result-object v8

    new-instance v9, Lorg/json/JSONArray;

    invoke-direct {v9}, Lorg/json/JSONArray;-><init>()V

    const/4 v10, 0x0

    const/4 v11, 0x0

    .line 384
    :goto_0
    invoke-virtual {v8}, Lorg/json/JSONArray;->length()I

    move-result v12

    if-ge v11, v12, :cond_2

    invoke-virtual {v8, v11}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v12

    if-nez v12, :cond_0

    goto :goto_1

    :cond_0
    const-string v13, "id"

    .line 385
    invoke-virtual {v12, v13}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v13

    invoke-virtual {v6, v13}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v13

    if-eqz v13, :cond_1

    move-object v10, v12

    goto :goto_1

    :cond_1
    invoke-virtual {v9, v12}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    :goto_1
    add-int/lit8 v11, v11, 0x1

    goto :goto_0

    .line 386
    :cond_2
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v11
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    cmp-long v8, v2, v11

    if-lez v8, :cond_7

    if-nez v4, :cond_3

    if-nez v5, :cond_3

    goto/16 :goto_2

    :cond_3
    const-wide/16 v13, 0x3e8

    add-long/2addr v11, v13

    const-wide/32 v13, 0x493e0

    sub-long v13, v2, v13

    .line 389
    :try_start_1
    invoke-static {v11, v12, v13, v14}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v11

    if-eqz v10, :cond_4

    const-string v8, "start"

    .line 391
    invoke-virtual {v10, v8}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J

    move-result-wide v13

    cmp-long v8, v13, v2

    if-nez v8, :cond_4

    const-string v8, "when"

    invoke-virtual {v10, v8, v11, v12}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v11

    .line 392
    :cond_4
    new-instance v8, Lorg/json/JSONObject;

    invoke-direct {v8}, Lorg/json/JSONObject;-><init>()V

    const-string v13, "id"

    invoke-virtual {v8, v13, v6}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    move-result-object v6

    const-string v8, "sports_game"

    invoke-virtual {v6, v8, v0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    move-result-object v0

    const-string v6, "away"

    move-object/from16 v8, p2

    invoke-virtual {v0, v6, v8}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    move-result-object v0

    const-string v6, "home"

    move-object/from16 v8, p3

    invoke-virtual {v0, v6, v8}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    move-result-object v0

    const-string v6, "program"

    move-object/from16 v8, p4

    .line 393
    invoke-virtual {v0, v6, v8}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    move-result-object v0

    const-string v6, "start"

    invoke-virtual {v0, v6, v2, v3}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    move-result-object v0

    const-string v6, "when"

    invoke-virtual {v0, v6, v11, v12}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    move-result-object v0

    const-string v6, "automatic"

    invoke-virtual {v0, v6, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    move-result-object v0

    const-string v4, "manual"

    invoke-virtual {v0, v4, v5}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    move-result-object v0

    if-eqz v10, :cond_5

    const-string v4, "start"

    .line 394
    invoke-virtual {v10, v4}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J

    move-result-wide v4

    cmp-long v6, v4, v2

    if-nez v6, :cond_5

    const-string v2, "delivered"

    const-string v3, "delivered"

    invoke-virtual {v10, v3}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;)Z

    move-result v3

    invoke-virtual {v0, v2, v3}, Lorg/json/JSONObject;->put(Ljava/lang/String;Z)Lorg/json/JSONObject;

    .line 395
    :cond_5
    invoke-virtual {v9, v0}, Lorg/json/JSONArray;->put(Ljava/lang/Object;)Lorg/json/JSONArray;

    iget-object v2, v1, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {v2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v2

    const-string v3, "reminders"

    invoke-virtual {v9}, Lorg/json/JSONArray;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-interface {v2, v3, v4}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v2

    invoke-interface {v2}, Landroid/content/SharedPreferences$Editor;->apply()V

    const-string v2, "delivered"

    .line 396
    invoke-virtual {v0, v2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_6

    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->scheduleReminderAlarm(Lorg/json/JSONObject;)V
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_0
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    .line 398
    :catch_0
    :cond_6
    :try_start_2
    monitor-exit v7

    return-void

    :cond_7
    :goto_2
    if-eqz v10, :cond_8

    .line 387
    invoke-virtual {p0, v6}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->removeReminder(Ljava/lang/String;)V

    :cond_8
    monitor-exit v7

    return-void

    :catchall_0
    move-exception v0

    .line 398
    monitor-exit v7
    :try_end_2
    .catchall {:try_start_2 .. :try_end_2} :catchall_0

    throw v0
.end method

.method public startRecording(Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;JLjava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 13
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            "Ljava/util/Map<",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            ">;J",
            "Ljava/lang/String;",
            "Ljava/lang/String;",
            ")",
            "Ljava/lang/String;"
        }
    .end annotation

    .line 275
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->hasRecordingSpace()Z

    move-result v0

    const-string v1, ""

    if-nez v0, :cond_0

    return-object v1

    .line 276
    :cond_0
    new-instance v0, Ljava/lang/StringBuilder;

    const-string v2, "rec-"

    invoke-direct {v0, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    invoke-static {v2, v3}, Ljava/lang/Long;->toHexString(J)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    .line 277
    new-instance v2, Landroid/content/Intent;

    iget-object v3, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-class v4, Lcom/projectinfinity/kodi/InfinityCobraRecordingService;

    invoke-direct {v2, v3, v4}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v3, "com.projectinfinity.cobra.RECORD"

    .line 278
    invoke-virtual {v2, v3}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v2

    const-string v3, "session"

    .line 279
    invoke-virtual {v2, v3, v0}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v2

    const-string v3, "url"

    .line 280
    invoke-virtual {v2, v3, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object p1

    const-string v2, "Recording"

    .line 281
    invoke-static {p2, v2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->cleanName(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    const-string v2, "name"

    invoke-virtual {p1, v2, p2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object p1

    const-string p2, "headers"

    .line 282
    invoke-static {p3}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->headersJson(Ljava/util/Map;)Ljava/lang/String;

    move-result-object p3

    invoke-virtual {p1, p2, p3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object p1

    const-string p2, "end_at"

    .line 283
    invoke-virtual {p1, p2, p4, p5}, Landroid/content/Intent;->putExtra(Ljava/lang/String;J)Landroid/content/Intent;

    move-result-object p1

    if-nez p6, :cond_1

    move-object p6, v1

    :cond_1
    const-string p2, "source_id"

    .line 284
    invoke-virtual {p1, p2, p6}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object p1

    if-nez p7, :cond_2

    move-object p7, v1

    :cond_2
    const-string p2, "channel_id"

    .line 285
    invoke-virtual {p1, p2, p7}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object p1

    .line 286
    invoke-static {v0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingRequested(Ljava/lang/String;)V

    .line 287
    :try_start_0
    sget p2, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 p3, 0x1a

    if-lt p2, p3, :cond_3

    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {p2, p1}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Landroid/content/Context;Landroid/content/Intent;)Landroid/content/ComponentName;

    goto :goto_0

    :cond_3
    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-virtual {p2, p1}, Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;
    :try_end_0
    .catch Ljava/lang/RuntimeException; {:try_start_0 .. :try_end_0} :catch_0

    :goto_0
    return-object v0

    :catch_0
    move-exception p1

    const/4 p2, 0x0

    .line 288
    invoke-static {v0, p2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingFinished(Ljava/lang/String;Ljava/lang/Object;)V

    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-string p3, "recording-start"

    invoke-static {p2, p3, p1}, Lcom/projectinfinity/kodi/InfinityCobraDiagnostics;->failure(Landroid/content/Context;Ljava/lang/String;Ljava/lang/Throwable;)V

    return-object v1
.end method

.method public stopRecording(Ljava/lang/String;)V
    .registers 5

    if-eqz p1, :cond_0

    .line 293
    invoke-virtual {p1}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-nez v0, :cond_0

    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingActive(Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :cond_0

    return-void

    .line 294
    :cond_0
    new-instance v0, Landroid/content/Intent;

    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    const-class v2, Lcom/projectinfinity/kodi/InfinityCobraRecordingService;

    invoke-direct {v0, v1, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v1, "com.projectinfinity.cobra.STOP_RECORD"

    .line 295
    invoke-virtual {v0, v1}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v0

    if-nez p1, :cond_1

    const-string p1, ""

    :cond_1
    const-string v1, "session"

    .line 296
    invoke-virtual {v0, v1, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object p1

    .line 297
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v1, 0x1a

    if-lt v0, v1, :cond_2

    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {v0, p1}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Landroid/content/Context;Landroid/content/Intent;)Landroid/content/ComponentName;

    goto :goto_0

    :cond_2
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-virtual {v0, p1}, Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;

    :goto_0
    return-void
.end method

.method public unlockAndSelectProfile(Ljava/lang/String;Ljava/lang/String;)Z
    .registers 8

    .line 115
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->profiles()Lorg/json/JSONArray;

    move-result-object v0

    const/4 v1, 0x0

    const/4 v2, 0x0

    .line 116
    :goto_0
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v3

    if-ge v2, v3, :cond_4

    .line 117
    invoke-virtual {v0, v2}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v3

    if-eqz v3, :cond_3

    const-string v4, "id"

    .line 118
    invoke-virtual {v3, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {p1, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v4

    if-nez v4, :cond_0

    goto :goto_1

    :cond_0
    const-string v0, "pin_hash"

    const-string v2, ""

    .line 119
    invoke-virtual {v3, v0, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 120
    invoke-virtual {v0}, Ljava/lang/String;->isEmpty()Z

    move-result v3

    if-nez v3, :cond_2

    if-nez p2, :cond_1

    move-object p2, v2

    :cond_1
    invoke-static {p2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->sha256(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-nez p2, :cond_2

    return v1

    .line 121
    :cond_2
    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p2

    const-string v0, "active_profile"

    invoke-interface {p2, v0, p1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V

    const/4 p1, 0x1

    return p1

    :cond_3
    :goto_1
    add-int/lit8 v2, v2, 0x1

    goto :goto_0

    :cond_4
    return v1
.end method

.method public writeHealth(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;IIILjava/lang/String;Ljava/lang/String;)V
    .registers 15

    .line 445
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    :try_start_0
    const-string v1, "schema"

    const/4 v2, 0x3

    .line 447
    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    const-string v1, "snapshot_kind"

    const-string v2, "historical_event_sample"

    .line 448
    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 449
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {v1, v0}, Lcom/projectinfinity/kodi/InfinityCobraDiagnostics;->addIdentity(Landroid/content/Context;Lorg/json/JSONObject;)V

    const-string v1, "timestamp"

    .line 450
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    invoke-virtual {v0, v1, v2, v3}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    const-string v1, "screen"

    .line 451
    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->safe(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v0, v1, p1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "profile"

    .line 452
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->activeProfileId()Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->hashId(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, p1, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "source"

    .line 453
    invoke-static {p2}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->hashId(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "media"

    .line 454
    invoke-static {p3}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->hashId(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "player_state"

    .line 455
    invoke-static {p4}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->safe(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "last_error"

    .line 456
    invoke-static {p5}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->redact(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "retry_count"

    .line 457
    invoke-virtual {v0, p1, p6}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    const-string p1, "multiview_tiles"

    .line 458
    invoke-virtual {v0, p1, p7}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    const-string p1, "audio_owner"

    .line 459
    invoke-virtual {v0, p1, p8}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    const-string p1, "recording_state"

    .line 460
    invoke-static {p9}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->safe(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "guide_state"

    .line 461
    invoke-static {p10}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->safe(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {v0, p1, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    const-string p1, "free_recording_bytes"

    .line 462
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->recordingsDir()Ljava/io/File;

    move-result-object p2

    invoke-virtual {p2}, Ljava/io/File;->getUsableSpace()J

    move-result-wide p2

    invoke-virtual {v0, p1, p2, p3}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    .line 463
    invoke-virtual {v0}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    .line 464
    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->prefs:Landroid/content/SharedPreferences;

    invoke-interface {p2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p2

    const-string p3, "health_snapshot"

    invoke-interface {p2, p3, p1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p2

    invoke-interface {p2}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 465
    iget-object p2, p0, Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;->context:Landroid/content/Context;

    invoke-static {p2, p1, p5}, Lcom/projectinfinity/kodi/InfinityCobraDiagnostics;->saveHealth(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method
