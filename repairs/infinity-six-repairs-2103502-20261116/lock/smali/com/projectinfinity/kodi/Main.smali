.class public Lcom/projectinfinity/kodi/Main;
.super Landroid/app/NativeActivity;
.source "Main.java"

# interfaces
.implements Landroid/view/Choreographer$FrameCallback;


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Lcom/projectinfinity/kodi/Main$DelayedIntent;
    }
.end annotation


# static fields
.field private static final INFINITY_ROTATION_ACTION_FOLLOW:Ljava/lang/String; = "com.projectinfinity.kodi.action.PLAYER_ROTATION_FOLLOW_DEVICE"

.field private static final INFINITY_ROTATION_ACTION_UNLOCKED:Ljava/lang/String; = "com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED"

.field private static final INFINITY_ROTATION_FOLLOW_DEVICE:I = 0x0

.field private static final INFINITY_ROTATION_PREFS:Ljava/lang/String; = "infinity_player_rotation"

.field private static final INFINITY_ROTATION_PREF_MODE:Ljava/lang/String; = "mode"

.field private static final INFINITY_ROTATION_UNLOCKED:I = 0x1

.field public static MainActivity:Lcom/projectinfinity/kodi/Main; = null

.field private static final TAG:Ljava/lang/String; = "Kodi"


# instance fields
.field private handler:Landroid/os/Handler;

.field private leanbackUpdateRunnable:Ljava/lang/Runnable;

.field private mDecorView:Landroid/view/View;

.field private mDelayedIntents:Ljava/util/ArrayList;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/ArrayList<",
            "Lcom/projectinfinity/kodi/Main$DelayedIntent;",
            ">;"
        }
    .end annotation
.end field

.field private mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

.field private volatile mInfinityDestroyed:Z

.field final mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

.field private mInfinityLastRequestedOrientation:I

.field private mInfinityLaunchReady:Z

.field private volatile mInfinityManagedSize:J

.field private mInfinityNativeEntryAdmitted:Z

.field private mInfinityNativeEntryAttempted:Z

.field private mInfinityNativeEntryDenied:Z

.field private mInfinityNativeEntryRecovery:Z

.field private mInfinityPlayerRotationMode:I

.field private mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

.field private mInfinityResponsiveness:Lcom/projectinfinity/kodi/InfinityResponsiveness;

.field mInfinityStopped:Z

.field private volatile mInfinitySystemTheme:I

.field private volatile mInfinityViewSize:J

.field private mInfinityWeatherCapture:Lcom/projectinfinity/kodi/InfinityChooserWeather;

.field private volatile mInfinityWindowMode:I

.field private mInputDeviceListener:Lcom/projectinfinity/kodi/XBMCInputDeviceListener;

.field private mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;

.field public mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

.field private mPaused:Z

.field private mSettingsContentObserver:Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;

.field private mVideoLayout:Landroid/widget/RelativeLayout;


# direct methods
.method static constructor <clinit>()V
    .registers 0

    return-void
.end method

.method public constructor <init>()V
    .registers 4

    .line 153
    invoke-direct {p0}, Landroid/app/NativeActivity;-><init>()V

    .line 43
    new-instance v0, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-direct {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;-><init>()V

    iput-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    const/4 v0, 0x1

    .line 44
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityStopped:Z

    const/4 v1, 0x0

    .line 59
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    .line 63
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;

    .line 64
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    .line 65
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mVideoLayout:Landroid/widget/RelativeLayout;

    .line 66
    new-instance v1, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v2

    invoke-direct {v1, v2}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    .line 78
    new-instance v1, Ljava/util/ArrayList;

    invoke-direct {v1}, Ljava/util/ArrayList;-><init>()V

    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    .line 79
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    const/4 v0, 0x0

    .line 92
    iput v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityPlayerRotationMode:I

    const/high16 v0, -0x80000000

    .line 93
    iput v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityLastRequestedOrientation:I

    .line 134
    new-instance v0, Lcom/projectinfinity/kodi/Main$1;

    invoke-direct {v0, p0}, Lcom/projectinfinity/kodi/Main$1;-><init>(Lcom/projectinfinity/kodi/Main;)V

    iput-object v0, p0, Lcom/projectinfinity/kodi/Main;->leanbackUpdateRunnable:Ljava/lang/Runnable;

    return-void
.end method

.method private native _callNative(JJ)V
.end method

.method static native _infinityHeartbeat()[J
.end method

.method static synthetic access$000(Lcom/projectinfinity/kodi/Main;)Lcom/projectinfinity/kodi/XBMCJsonRPC;
    .registers 1

    .line 33
    iget-object p0, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;

    return-object p0
.end method

.method static synthetic access$100(Lcom/projectinfinity/kodi/Main;)Landroid/os/Handler;
    .registers 1

    .line 33
    iget-object p0, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    return-object p0
.end method

.method static synthetic access$200(Lcom/projectinfinity/kodi/Main;)Landroid/view/View;
    .registers 1

    .line 33
    iget-object p0, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    return-object p0
.end method

.method static synthetic access$300(Lcom/projectinfinity/kodi/Main;)Z
    .registers 1

    .line 33
    iget-boolean p0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    return p0
.end method

.method static synthetic access$400(Lcom/projectinfinity/kodi/Main;)Z
    .registers 1

    .line 33
    iget-boolean p0, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    return p0
.end method

.method static synthetic access$500(Lcom/projectinfinity/kodi/Main;)Ljava/util/ArrayList;
    .registers 1

    .line 33
    iget-object p0, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    return-object p0
.end method

.method static synthetic access$600(Lcom/projectinfinity/kodi/Main;)Lcom/projectinfinity/kodi/InfinityCoreBridge;
    .registers 1

    .line 33
    iget-object p0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    return-object p0
.end method

.method static synthetic access$700(Lcom/projectinfinity/kodi/Main;)Lcom/projectinfinity/kodi/InfinityRefreshController;
    .registers 1

    .line 33
    iget-object p0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    return-object p0
.end method

.method static synthetic access$800(Lcom/projectinfinity/kodi/Main;Ljava/lang/String;)V
    .registers 2

    .line 33
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$900(Lcom/projectinfinity/kodi/Main;JJ)V
    .registers 5

    .line 33
    invoke-direct {p0, p1, p2, p3, p4}, Lcom/projectinfinity/kodi/Main;->_callNative(JJ)V

    return-void
.end method

.method private getLauncherName()Ljava/lang/String;
    .registers 4

    .line 829
    new-instance v0, Landroid/content/Intent;

    const-string v1, "android.intent.action.MAIN"

    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    const-string v1, "android.intent.category.HOME"

    .line 830
    invoke-virtual {v0, v1}, Landroid/content/Intent;->addCategory(Ljava/lang/String;)Landroid/content/Intent;

    .line 831
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object v1

    const/4 v2, 0x0

    invoke-virtual {v1, v0, v2}, Landroid/content/pm/PackageManager;->resolveActivity(Landroid/content/Intent;I)Landroid/content/pm/ResolveInfo;

    move-result-object v0

    .line 832
    iget-object v0, v0, Landroid/content/pm/ResolveInfo;->activityInfo:Landroid/content/pm/ActivityInfo;

    iget-object v0, v0, Landroid/content/pm/ActivityInfo;->packageName:Ljava/lang/String;

    return-object v0
.end method

.method private infinityApplyPlayerRotation(Ljava/lang/String;)V
    .registers 7

    const/4 v0, 0x0

    const/4 v1, 0x1

    .line 740
    :try_start_2
    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v3, 0x1a

    if-lt v2, v3, :cond_e

    .line 741
    invoke-static {p0}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Lcom/projectinfinity/kodi/Main;)Z

    move-result v2

    if-nez v2, :cond_1e

    :cond_e
    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v3, 0x18

    if-lt v2, v3, :cond_1b

    .line 742
    invoke-static {p0}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m$1(Lcom/projectinfinity/kodi/Main;)Z

    move-result v2
    :try_end_18
    .catch Ljava/lang/IllegalStateException; {:try_start_2 .. :try_end_18} :catch_1d

    if-eqz v2, :cond_1b

    goto :goto_1e

    :cond_1b
    const/4 v2, 0x0

    goto :goto_1f

    :catch_1d
    nop

    :cond_1e
    :goto_1e
    const/4 v2, 0x1

    .line 749
    :goto_1f
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object v3

    const-string v4, "android.software.leanback"

    invoke-virtual {v3, v4}, Landroid/content/pm/PackageManager;->hasSystemFeature(Ljava/lang/String;)Z

    move-result v3

    .line 750
    iget-boolean v4, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    if-nez v4, :cond_40

    iget-boolean v4, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    if-nez v4, :cond_40

    if-nez v3, :cond_40

    if-nez v2, :cond_40

    iget v2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityPlayerRotationMode:I

    if-ne v2, v1, :cond_40

    .line 751
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityHasActiveVideoSafely()Z

    move-result v2

    if-eqz v2, :cond_40

    const/4 v0, 0x1

    :cond_40
    if-eqz v0, :cond_45

    const/16 v0, 0xa

    goto :goto_46

    :cond_45
    const/4 v0, -0x1

    .line 752
    :goto_46
    invoke-direct {p0, v0, p1}, Lcom/projectinfinity/kodi/Main;->infinityRequestPlayerOrientation(ILjava/lang/String;)V

    return-void
.end method

.method static infinityClosePending()Z
    .registers 2

    .line 51
    sget-object v0, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    if-eqz v0, :cond_14

    .line 52
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/Main;->isDestroyed()Z

    move-result v1

    if-nez v1, :cond_14

    iget-object v0, v0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-eqz v0, :cond_14

    const/4 v0, 0x1

    goto :goto_15

    :cond_14
    const/4 v0, 0x0

    :goto_15
    return v0
.end method

.method private infinityHandlePlayerRotationIntent(Landroid/content/Intent;)Z
    .registers 5

    const/4 v0, 0x0

    if-nez p1, :cond_4

    return v0

    .line 699
    :cond_4
    invoke-virtual {p1}, Landroid/content/Intent;->getAction()Ljava/lang/String;

    move-result-object p1

    const-string v1, "com.projectinfinity.kodi.action.PLAYER_ROTATION_FOLLOW_DEVICE"

    .line 700
    invoke-virtual {v1, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    const/4 v2, 0x1

    if-eqz v1, :cond_15

    .line 702
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinitySetPlayerRotationMode(I)V

    return v2

    :cond_15
    const-string v1, "com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED"

    .line 705
    invoke-virtual {v1, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-eqz p1, :cond_21

    .line 707
    invoke-direct {p0, v2}, Lcom/projectinfinity/kodi/Main;->infinitySetPlayerRotationMode(I)V

    return v2

    :cond_21
    return v0
.end method

.method private infinityHasActiveVideoSafely()Z
    .registers 4

    .line 726
    :try_start_0
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinityHasActiveVideo()Z

    move-result v0
    :try_end_4
    .catch Ljava/lang/LinkageError; {:try_start_0 .. :try_end_4} :catch_5

    return v0

    :catch_5
    move-exception v0

    const-string v1, "InfinityRotation"

    const-string v2, "Player-state bridge unavailable"

    .line 730
    invoke-static {v1, v2, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    const/4 v0, 0x0

    return v0
.end method

.method static infinityLiveActivity()Lcom/projectinfinity/kodi/Main;
    .registers 5

    .line 55
    sget-object v0, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    const/4 v1, 0x1

    const/4 v2, 0x0

    if-eqz v0, :cond_14

    .line 56
    iget-boolean v3, v0, Lcom/projectinfinity/kodi/Main;->mInfinityLaunchReady:Z

    if-eqz v3, :cond_14

    iget-object v3, v0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v3}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v3

    if-nez v3, :cond_14

    const/4 v3, 0x1

    goto :goto_15

    :cond_14
    const/4 v3, 0x0

    :goto_15
    if-eqz v0, :cond_1c

    iget-boolean v4, v0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    if-eqz v4, :cond_1c

    goto :goto_1d

    :cond_1c
    const/4 v1, 0x0

    :goto_1d
    invoke-static {v0, v3, v1}, Lcom/projectinfinity/kodi/InfinityStartupHandoff;->isLive(Landroid/app/Activity;ZZ)Z

    move-result v1

    if-eqz v1, :cond_24

    goto :goto_25

    :cond_24
    const/4 v0, 0x0

    :goto_25
    return-object v0
.end method

.method private infinityLoadPlayerRotationMode()V
    .registers 4

    const-string v0, "infinity_player_rotation"

    const/4 v1, 0x0

    .line 690
    invoke-static {p0, v0, v1}, Lcom/projectinfinity/kodi/InfinityJavaPersistence;->preferences(Landroid/content/Context;Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v0

    const-string v2, "mode"

    .line 691
    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I

    move-result v0

    const/4 v2, 0x1

    if-ne v0, v2, :cond_11

    const/4 v1, 0x1

    .line 693
    :cond_11
    iput v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityPlayerRotationMode:I

    return-void
.end method

.method private infinityRequestPlayerOrientation(ILjava/lang/String;)V
    .registers 6

    const-string v0, "InfinityRotation"

    const-string v1, "Player rotation="

    .line 760
    iget v2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityLastRequestedOrientation:I

    if-ne v2, p1, :cond_9

    return-void

    .line 763
    :cond_9
    :try_start_9
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->setRequestedOrientation(I)V

    .line 764
    iput p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityLastRequestedOrientation:I

    .line 765
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    const/16 v1, 0xa

    if-ne p1, v1, :cond_1a

    const-string p1, "unlocked"

    goto :goto_1c

    :cond_1a
    const-string p1, "follow-device"

    .line 766
    :goto_1c
    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string p1, " reason="

    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    .line 765
    invoke-static {v0, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    :try_end_2e
    .catch Ljava/lang/IllegalStateException; {:try_start_9 .. :try_end_2e} :catch_31
    .catch Ljava/lang/SecurityException; {:try_start_9 .. :try_end_2e} :catch_2f

    goto :goto_37

    :catch_2f
    move-exception p1

    goto :goto_32

    :catch_31
    move-exception p1

    :goto_32
    const-string p2, "Android rejected player orientation request"

    .line 771
    invoke-static {v0, p2, p1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    :goto_37
    return-void
.end method

.method private infinityResponsiveTraceState()[J
    .registers 2

    .line 789
    :try_start_0
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinityGetState()[J

    move-result-object v0
    :try_end_4
    .catch Ljava/lang/RuntimeException; {:try_start_0 .. :try_end_4} :catch_5
    .catch Ljava/lang/LinkageError; {:try_start_0 .. :try_end_4} :catch_5

    return-object v0

    :catch_5
    const/4 v0, 0x0

    return-object v0
.end method

.method private infinitySetCurrentTaskExcludedFromRecents(Z)V
    .registers 6

    :try_start_0
    const-string v0, "activity"

    .line 377
    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/Main;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/app/ActivityManager;

    if-nez v0, :cond_b

    return-void

    .line 379
    :cond_b
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getTaskId()I

    move-result v1

    .line 380
    invoke-virtual {v0}, Landroid/app/ActivityManager;->getAppTasks()Ljava/util/List;

    move-result-object v0

    invoke-interface {v0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v0

    :cond_17
    invoke-interface {v0}, Ljava/util/Iterator;->hasNext()Z

    move-result v2

    if-eqz v2, :cond_3b

    invoke-interface {v0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v2

    check-cast v2, Landroid/app/ActivityManager$AppTask;

    .line 382
    invoke-virtual {v2}, Landroid/app/ActivityManager$AppTask;->getTaskInfo()Landroid/app/ActivityManager$RecentTaskInfo;

    move-result-object v3

    if-eqz v3, :cond_17

    .line 383
    invoke-static {v3}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Landroid/app/ActivityManager$RecentTaskInfo;)I

    move-result v3

    if-ne v3, v1, :cond_17

    .line 385
    invoke-virtual {v2, p1}, Landroid/app/ActivityManager$AppTask;->setExcludeFromRecents(Z)V
    :try_end_32
    .catch Ljava/lang/RuntimeException; {:try_start_0 .. :try_end_32} :catch_33

    return-void

    :catch_33
    move-exception p1

    const-string v0, "Kodi"

    const-string v1, "Infinity Recents task visibility update failed"

    .line 392
    invoke-static {v0, v1, p1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    :cond_3b
    return-void
.end method

.method private infinitySetPlayerRotationMode(I)V
    .registers 4

    const/4 v0, 0x0

    const/4 v1, 0x1

    if-ne p1, v1, :cond_5

    goto :goto_6

    :cond_5
    const/4 v1, 0x0

    .line 716
    :goto_6
    iput v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityPlayerRotationMode:I

    const-string p1, "infinity_player_rotation"

    .line 717
    invoke-static {p0, p1, v0}, Lcom/projectinfinity/kodi/InfinityJavaPersistence;->preferences(Landroid/content/Context;Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    iget v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityPlayerRotationMode:I

    const-string v1, "mode"

    .line 718
    invoke-interface {p1, v1, v0}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 719
    invoke-direct {p0, v1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    return-void
.end method

.method private infinityTraceWindow(Ljava/lang/String;)V
    .registers 10

    .line 795
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityResponsiveTraceState()[J

    move-result-object v3

    iget-wide v4, p0, Lcom/projectinfinity/kodi/Main;->mInfinityViewSize:J

    iget-wide v6, p0, Lcom/projectinfinity/kodi/Main;->mInfinityManagedSize:J

    move-object v0, p0

    move-object v1, p1

    invoke-static/range {v0 .. v7}, Lcom/projectinfinity/kodi/InfinityResponsiveTrace;->capture(Landroid/app/Activity;Ljava/lang/String;Landroid/view/View;[JJJ)V

    return-void
.end method

.method private infinityTraceWindowSettled(Ljava/lang/String;)V
    .registers 4

    .line 801
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityResponsiveTrace;->isEnabled(Landroid/content/Context;)Z

    move-result v0

    if-nez v0, :cond_7

    return-void

    .line 802
    :cond_7
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    if-eqz v0, :cond_c

    goto :goto_14

    :cond_c
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getWindow()Landroid/view/Window;

    move-result-object v0

    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    move-result-object v0

    :goto_14
    if-eqz v0, :cond_1f

    .line 803
    new-instance v1, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticLambda1;

    invoke-direct {v1, p0, p1}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticLambda1;-><init>(Lcom/projectinfinity/kodi/Main;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/view/View;->post(Ljava/lang/Runnable;)Z

    goto :goto_22

    .line 804
    :cond_1f
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindow(Ljava/lang/String;)V

    :goto_22
    return-void
.end method

.method private runNativeOnUiThread(JJ)V
    .registers 12

    .line 815
    new-instance v6, Lcom/projectinfinity/kodi/Main$5;

    move-object v0, v6

    move-object v1, p0

    move-wide v2, p1

    move-wide v4, p3

    invoke-direct/range {v0 .. v5}, Lcom/projectinfinity/kodi/Main$5;-><init>(Lcom/projectinfinity/kodi/Main;JJ)V

    invoke-virtual {p0, v6}, Lcom/projectinfinity/kodi/Main;->runOnUiThread(Ljava/lang/Runnable;)V

    return-void
.end method


# virtual methods
.method native _doFrame(J)V
.end method

.method public native _infinityBridgeVersion()I
.end method

.method public native _infinityCanEnterPictureInPicture()Z
.end method

.method public native _infinityGetState()[J
.end method

.method public native _infinityHasActiveVideo()Z
.end method

.method public native _infinitySyncDisplayState()V
.end method

.method public native _infinitySystemThemeMode()I
.end method

.method public native _infinityVideoAspectRatio()F
.end method

.method public native _infinityWindowHeight()I
.end method

.method public native _infinityWindowMode()I
.end method

.method public native _infinityWindowWidth()I
.end method

.method native _onActivityResult(IILandroid/content/Intent;)V
.end method

.method native _onNewIntent(Landroid/content/Intent;)V
.end method

.method native _onVisibleBehindCanceled()V
.end method

.method public doFrame(J)V
    .registers 4

    .line 585
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    if-eqz v0, :cond_5

    return-void

    .line 586
    :cond_5
    invoke-static {}, Landroid/view/Choreographer;->getInstance()Landroid/view/Choreographer;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/Choreographer;->postFrameCallback(Landroid/view/Choreographer$FrameCallback;)V

    .line 587
    invoke-virtual {p0, p1, p2}, Lcom/projectinfinity/kodi/Main;->_doFrame(J)V

    return-void
.end method

.method public getDisplayRect()Landroid/graphics/Rect;
    .registers 6

    .line 159
    iget-wide v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityViewSize:J

    .line 160
    new-instance v2, Landroid/graphics/Rect;

    const/16 v3, 0x20

    ushr-long v3, v0, v3

    long-to-int v4, v3

    long-to-int v1, v0

    const/4 v0, 0x0

    invoke-direct {v2, v0, v0, v4, v1}, Landroid/graphics/Rect;-><init>(IIII)V

    return-object v2
.end method

.method public native infinityAuthorizeCheckpointTermination(Ljava/lang/String;Ljava/lang/String;I)Z
.end method

.method public infinityCheckpointOwnerRetired(ILjava/lang/String;)Z
    .registers 4

    .line 127
    :try_start_0
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getFilesDir()Ljava/io/File;

    move-result-object v0

    invoke-static {v0, p1, p2}, Lcom/projectinfinity/kodi/InfinityKodiShutdown;->ownerRetired(Ljava/io/File;ILjava/lang/String;)Z

    move-result p1
    :try_end_8
    .catch Ljava/io/IOException; {:try_start_0 .. :try_end_8} :catch_9
    .catch Ljava/lang/RuntimeException; {:try_start_0 .. :try_end_8} :catch_9

    return p1

    :catch_9
    const/4 p1, 0x0

    return p1
.end method

.method public infinityCheckpointOwnsOwner(ILjava/lang/String;)Z
    .registers 4

    .line 123
    invoke-static {}, Landroid/os/Process;->myPid()I

    move-result v0

    if-ne p1, v0, :cond_1a

    if-eqz p2, :cond_1a

    invoke-virtual {p2}, Ljava/lang/String;->isEmpty()Z

    move-result p1

    if-nez p1, :cond_1a

    .line 124
    invoke-static {}, Lcom/projectinfinity/kodi/InfinityKodiShutdown;->confirmedLocalOwnerToken()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p2, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-eqz p1, :cond_1a

    const/4 p1, 0x1

    goto :goto_1b

    :cond_1a
    const/4 p1, 0x0

    :goto_1b
    return p1
.end method

.method public infinityGetSystemThemeMode()I
    .registers 2

    .line 808
    iget v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinitySystemTheme:I

    return v0
.end method

.method public infinityGetWindowMode()I
    .registers 2

    .line 809
    iget v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityWindowMode:I

    return v0
.end method

.method public infinityGetWindowSize()J
    .registers 3

    .line 807
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    if-eqz v0, :cond_7

    const-wide/16 v0, 0x0

    goto :goto_9

    :cond_7
    iget-wide v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityManagedSize:J

    :goto_9
    return-wide v0
.end method

.method public infinityOnPlaybackStateChanged()V
    .registers 2

    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onPlaybackChanged(Lcom/projectinfinity/kodi/Main;)V


    .line 658
    new-instance v0, Lcom/projectinfinity/kodi/Main$4;

    invoke-direct {v0, p0}, Lcom/projectinfinity/kodi/Main$4;-><init>(Lcom/projectinfinity/kodi/Main;)V

    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/Main;->runOnUiThread(Ljava/lang/Runnable;)V

    return-void
.end method

.method public native infinityPersistenceCheckpointStatus(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;
.end method

.method public infinityPrepareNativeTask()Z
    .registers 5

    .line 179
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryAttempted:Z

    const/4 v1, 0x0

    if-eqz v0, :cond_6

    return v1

    :cond_6
    const/4 v0, 0x1

    .line 180
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryAttempted:Z

    .line 181
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object v2

    invoke-static {v2}, Lcom/projectinfinity/kodi/InfinityNativeTaskEntry;->hasFreshIntent(Landroid/content/Intent;)Z

    move-result v2

    iput-boolean v2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryRecovery:Z

    .line 182
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityNativeTaskEntry;->admit(Landroid/app/Activity;)Z

    move-result v2

    if-nez v2, :cond_1c

    .line 183
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    return v1

    .line 186
    :cond_1c
    sput-object p0, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    .line 187
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object v1

    const-string v2, "infinity_kodi_launch_token"

    invoke-virtual {v1, v2}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-static {p0, v1}, Lcom/projectinfinity/kodi/InfinityKodiShutdown;->boot(Landroid/content/Context;Ljava/lang/String;)V

    const-string v1, "main.beforeNative"

    .line 188
    invoke-static {v1}, Lcom/projectinfinity/kodi/InfinityStartupTrace;->mainEvent(Ljava/lang/String;)V

    .line 189
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityInstalledCheckpointInstaller;->applyBeforeNative(Landroid/content/Context;)Z

    move-result v1

    if-nez v1, :cond_3f

    .line 190
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v1

    const-string v2, "checkpoint.addonParticipant.installUnconfirmed"

    invoke-static {v1, v2}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 192
    :cond_3f
    :try_start_3f
    invoke-static {}, Lcom/projectinfinity/kodi/InfinityKodiShutdown;->confirmedLocalOwnerToken()Ljava/lang/String;

    move-result-object v1

    .line 193
    invoke-virtual {v1}, Ljava/lang/String;->isEmpty()Z

    move-result v2

    if-nez v2, :cond_5b

    invoke-static {}, Landroid/os/Process;->myPid()I

    move-result v2

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getFilesDir()Ljava/io/File;

    move-result-object v3

    invoke-virtual {v3}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;

    move-result-object v3

    invoke-virtual {p0, v1, v2, v3}, Lcom/projectinfinity/kodi/Main;->infinityRegisterCheckpointOwner(Ljava/lang/String;ILjava/lang/String;)Z

    move-result v1

    if-nez v1, :cond_6e

    .line 194
    :cond_5b
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v1

    const-string v2, "checkpoint.engineOwner.registrationUnconfirmed"

    invoke-static {v1, v2}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V
    :try_end_64
    .catch Ljava/lang/RuntimeException; {:try_start_3f .. :try_end_64} :catch_65
    .catch Ljava/lang/LinkageError; {:try_start_3f .. :try_end_64} :catch_65

    goto :goto_6e

    .line 196
    :catch_65
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v1

    const-string v2, "checkpoint.engineOwner.registrationUnavailable"

    invoke-static {v1, v2}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 198
    :cond_6e
    :goto_6e
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryAdmitted:Z

    return v0
.end method

.method infinityPublishWindowSnapshot(IIIIZ)V
    .registers 12

    const-wide/16 v0, 0x0

    if-lez p1, :cond_13

    if-lez p2, :cond_13

    int-to-long v2, p1

    const/16 p1, 0x20

    shl-long/2addr v2, p1

    int-to-long p1, p2

    const-wide v4, 0xffffffffL

    and-long/2addr p1, v4

    or-long/2addr p1, v2

    goto :goto_14

    :cond_13
    move-wide p1, v0

    .line 778
    :goto_14
    iput-wide p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityViewSize:J

    if-eqz p5, :cond_19

    move-wide v0, p1

    .line 779
    :cond_19
    iput-wide v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityManagedSize:J

    .line 780
    iput p3, p0, Lcom/projectinfinity/kodi/Main;->mInfinitySystemTheme:I

    if-eqz p5, :cond_21

    const/4 p1, 0x4

    goto :goto_22

    :cond_21
    const/4 p1, 0x0

    :goto_22
    or-int/2addr p1, p4

    .line 781
    iput p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityWindowMode:I

    .line 782
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityAndroidKeyboard;->resized(Landroid/app/Activity;)V

    const-string p1, "bridge.publish"

    .line 783
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindow(Ljava/lang/String;)V

    return-void
.end method

.method public native infinityRegisterCheckpointOwner(Ljava/lang/String;ILjava/lang/String;)Z
.end method

.method public native infinityRequestPersistenceCheckpoint(Ljava/lang/String;Ljava/lang/String;I)Z
.end method

.method infinityStopWeatherCapture()V
    .registers 2

    .line 47
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityWeatherCapture:Lcom/projectinfinity/kodi/InfinityChooserWeather;

    if-eqz v0, :cond_7

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityChooserWeather;->stop()V

    :cond_7
    const/4 v0, 0x0

    .line 48
    iput-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityWeatherCapture:Lcom/projectinfinity/kodi/InfinityChooserWeather;

    return-void
.end method

.method synthetic lambda$infinityTraceWindowSettled$0$com-projectinfinity-kodi-Main(Ljava/lang/String;)V
    .registers 2

    .line 803
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindow(Ljava/lang/String;)V

    return-void
.end method

.method public onActivityResult(IILandroid/content/Intent;)V
    .registers 5

    .line 516
    invoke-super {p0, p1, p2, p3}, Landroid/app/NativeActivity;->onActivityResult(IILandroid/content/Intent;)V

    .line 517
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    if-nez v0, :cond_a

    invoke-virtual {p0, p1, p2, p3}, Lcom/projectinfinity/kodi/Main;->_onActivityResult(IILandroid/content/Intent;)V

    :cond_a
    return-void
.end method

.method public onConfigurationChanged(Landroid/content/res/Configuration;)V
    .registers 3

    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onConfigurationChanged(Lcom/projectinfinity/kodi/Main;)V


    .line 600
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onConfigurationChanged(Landroid/content/res/Configuration;)V

    .line 601
    iget-boolean p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz p1, :cond_8

    return-void

    .line 602
    :cond_8
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    const-string v0, "main.onConfigurationChanged"

    invoke-static {p1, v0}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 603
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz p1, :cond_18

    invoke-virtual {p1}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onWindowChanged()V

    .line 604
    :cond_18
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    if-eqz p1, :cond_21

    const-string v0, "window"

    invoke-virtual {p1, v0}, Lcom/projectinfinity/kodi/InfinityRefreshController;->apply(Ljava/lang/String;)V

    :cond_21
    const-string p1, "main.configuration"

    .line 605
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindow(Ljava/lang/String;)V

    const-string p1, "main.configuration.settled"

    .line 606
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindowSettled(Ljava/lang/String;)V

    return-void
.end method

.method public onCreate(Landroid/os/Bundle;)V
    .registers 7

    invoke-static {p0}, Lcom/projectinfinity/kodi/ContainerUpgrade;->beforeOwnerEntry(Landroid/content/Context;)V

    .line 205
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityJavaPersistence;->userEntry(Landroid/content/Context;)V

    .line 211
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    invoke-static {v0}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->start(Landroid/content/Context;)V

    .line 212
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.onCreate.beforeNative"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    const-string v0, "xbmc.proploaded"

    const-string v1, ""

    .line 213
    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/XBMCProperties;->getStringProperty(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    const-string v0, "kodi"

    .line 214
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    const-string v0, "main.nativeLoaded"

    .line 215
    invoke-static {v0}, Lcom/projectinfinity/kodi/InfinityStartupTrace;->mainEvent(Ljava/lang/String;)V

    .line 216
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.kodiNative.loaded"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 218
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onCreate(Landroid/os/Bundle;)V

    .line 219
    iget-boolean p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryAdmitted:Z

    const/4 v0, 0x0

    const/4 v1, 0x1

    if-nez p1, :cond_52

    .line 220
    iput-boolean v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    .line 221
    iput-boolean v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    .line 222
    sget-object p1, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    if-ne p1, p0, :cond_43

    sput-object v0, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    .line 223
    :cond_43
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    const-string v0, "main.nativeEntry.deferred"

    invoke-static {p1, v0}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 224
    iget-boolean p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryRecovery:Z

    invoke-static {p0, p1}, Lcom/projectinfinity/kodi/InfinityNativeTaskEntry;->returnToChooser(Landroid/app/Activity;Z)V

    return-void

    :cond_52
    const-string p1, "main.afterSuper"

    .line 227
    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityStartupTrace;->mainEvent(Ljava/lang/String;)V

    .line 228
    new-instance p1, Lcom/projectinfinity/kodi/InfinityResponsiveness;

    new-instance v2, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticLambda2;

    invoke-direct {v2}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticLambda2;-><init>()V

    invoke-direct {p1, p0, v2}, Lcom/projectinfinity/kodi/InfinityResponsiveness;-><init>(Landroid/app/Activity;Lcom/projectinfinity/kodi/InfinityResponsiveness$NativeSnapshot;)V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityResponsiveness:Lcom/projectinfinity/kodi/InfinityResponsiveness;

    .line 229
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    const-string v2, "main.onCreate.afterSuper"

    invoke-static {p1, v2}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    :try_start_6c
    const-string p1, "infinitycrash"

    .line 232
    invoke-static {p1}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    .line 233
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    const-string v2, "nativeCrashRecorder.loaded.afterKodiOnCreateOnCreate"

    invoke-static {p1, v2}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V
    :try_end_7a
    .catch Ljava/lang/LinkageError; {:try_start_6c .. :try_end_7a} :catch_7b

    goto :goto_a0

    :catch_7b
    move-exception p1

    .line 237
    new-instance v2, Ljava/lang/StringBuilder;

    const-string v3, "Native crash recorder unavailable: "

    invoke-direct {v2, v3}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    .line 238
    invoke-virtual {p1}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/Class;->getSimpleName()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string v2, "InfinityDiagnostics"

    .line 237
    invoke-static {v2, p1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 239
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    const-string v2, "nativeCrashRecorder.unavailable.afterKodiOnCreate"

    invoke-static {p1, v2}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 241
    :goto_a0
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->snapshotNativeMaps(Landroid/content/Context;)V

    const/4 p1, 0x3

    .line 244
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->setVolumeControlStream(I)V

    .line 246
    new-instance p1, Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;

    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    invoke-direct {p1, p0, v2}, Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;-><init>(Landroid/content/Context;Landroid/os/Handler;)V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mSettingsContentObserver:Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;

    .line 247
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    invoke-virtual {p1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object p1

    sget-object v2, Landroid/provider/Settings$System;->CONTENT_URI:Landroid/net/Uri;

    iget-object v3, p0, Lcom/projectinfinity/kodi/Main;->mSettingsContentObserver:Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;

    invoke-virtual {p1, v2, v1, v3}, Landroid/content/ContentResolver;->registerContentObserver(Landroid/net/Uri;ZLandroid/database/ContentObserver;)V

    .line 250
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object p1

    invoke-virtual {p1}, Landroid/content/Intent;->getData()Landroid/net/Uri;

    move-result-object p1

    if-eqz p1, :cond_e9

    .line 252
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    new-instance v2, Lcom/projectinfinity/kodi/Main$DelayedIntent;

    new-instance v3, Landroid/content/Intent;

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object v4

    invoke-direct {v3, v4}, Landroid/content/Intent;-><init>(Landroid/content/Intent;)V

    const/16 v4, 0x1388

    invoke-direct {v2, p0, v3, v4}, Lcom/projectinfinity/kodi/Main$DelayedIntent;-><init>(Lcom/projectinfinity/kodi/Main;Landroid/content/Intent;I)V

    invoke-virtual {p1, v2}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

    .line 253
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object p1

    invoke-virtual {p1, v0}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    .line 256
    :cond_e9
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object p1

    const-string v2, "android.software.leanback"

    invoke-virtual {p1, v2}, Landroid/content/pm/PackageManager;->hasSystemFeature(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_132

    .line 258
    sget p1, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v2, 0x1a

    if-lt p1, v2, :cond_10b

    .line 259
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->getLauncherName()Ljava/lang/String;

    move-result-object p1

    const-string v3, "com.google.android.tvlauncher"

    invoke-virtual {p1, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-eqz p1, :cond_10b

    .line 261
    invoke-static {p0}, Lcom/projectinfinity/kodi/channels/util/TvUtil;->scheduleSyncingChannel(Landroid/content/Context;)V

    goto :goto_132

    .line 263
    :cond_10b
    sget p1, Landroid/os/Build$VERSION;->SDK_INT:I

    if-ge p1, v2, :cond_132

    .line 264
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->getLauncherName()Ljava/lang/String;

    move-result-object p1

    const-string v2, "com.google.android.leanbacklauncher"

    invoke-virtual {p1, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-eqz p1, :cond_132

    .line 267
    new-instance p1, Lcom/projectinfinity/kodi/XBMCJsonRPC;

    invoke-direct {p1}, Lcom/projectinfinity/kodi/XBMCJsonRPC;-><init>()V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;

    .line 268
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->leanbackUpdateRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 269
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->leanbackUpdateRunnable:Ljava/lang/Runnable;

    const-wide/16 v3, 0x7530

    invoke-virtual {p1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 274
    :cond_132
    :goto_132
    new-instance p1, Lcom/projectinfinity/kodi/XBMCInputDeviceListener;

    invoke-direct {p1}, Lcom/projectinfinity/kodi/XBMCInputDeviceListener;-><init>()V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInputDeviceListener:Lcom/projectinfinity/kodi/XBMCInputDeviceListener;

    const-string p1, "input"

    .line 275
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object p1

    check-cast p1, Landroid/hardware/input/InputManager;

    .line 276
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mInputDeviceListener:Lcom/projectinfinity/kodi/XBMCInputDeviceListener;

    iget-object v3, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    invoke-virtual {p1, v2, v3}, Landroid/hardware/input/InputManager;->registerInputDeviceListener(Landroid/hardware/input/InputManager$InputDeviceListener;Landroid/os/Handler;)V

    .line 278
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getWindow()Landroid/view/Window;

    move-result-object p1

    invoke-virtual {p1}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    move-result-object p1

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    .line 279
    invoke-virtual {p1, v0}, Landroid/view/View;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 280
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getWindow()Landroid/view/Window;

    move-result-object p1

    invoke-virtual {p1, v0}, Landroid/view/Window;->takeSurface(Landroid/view/SurfaceHolder$Callback2;)V

    .line 281
    sget p1, Lcom/projectinfinity/kodi/R$layout;->activity_main:I

    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->setContentView(I)V

    .line 282
    sget p1, Lcom/projectinfinity/kodi/R$id;->VideoLayout:I

    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->findViewById(I)Landroid/view/View;

    move-result-object p1

    check-cast p1, Landroid/widget/RelativeLayout;

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mVideoLayout:Landroid/widget/RelativeLayout;

    .line 284
    new-instance p1, Lcom/projectinfinity/kodi/XBMCMainView;

    invoke-direct {p1, p0}, Lcom/projectinfinity/kodi/XBMCMainView;-><init>(Landroid/content/Context;)V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    .line 285
    new-instance p1, Landroid/widget/RelativeLayout$LayoutParams;

    const/4 v0, -0x1

    invoke-direct {p1, v0, v0}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    .line 286
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    const/high16 v2, 0x3f800000    # 1.0f

    invoke-virtual {v0, v2}, Lcom/projectinfinity/kodi/XBMCMainView;->setElevation(F)V

    .line 287
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mVideoLayout:Landroid/widget/RelativeLayout;

    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    invoke-virtual {v0, v2, p1}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 289
    new-instance p1, Lcom/projectinfinity/kodi/InfinityCoreBridge;

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;

    invoke-direct {p1, p0, v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;-><init>(Lcom/projectinfinity/kodi/Main;Landroid/view/View;)V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    .line 290
    invoke-virtual {p1}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->attach()V

    .line 291
    new-instance p1, Lcom/projectinfinity/kodi/InfinityRefreshController;

    invoke-direct {p1, p0}, Lcom/projectinfinity/kodi/InfinityRefreshController;-><init>(Lcom/projectinfinity/kodi/Main;)V

    iput-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    const-string v0, "attach"

    .line 292
    invoke-virtual {p1, v0}, Lcom/projectinfinity/kodi/InfinityRefreshController;->apply(Ljava/lang/String;)V

    .line 293
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityLoadPlayerRotationMode()V

    .line 294
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityHandlePlayerRotationIntent(Landroid/content/Intent;)Z

    .line 295
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    const-string p1, "main.attach"

    .line 296
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindowSettled(Ljava/lang/String;)V

    .line 298
    sget p1, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v0, 0x1e

    if-ge p1, v0, :cond_1c0

    .line 300
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    new-instance v0, Lcom/projectinfinity/kodi/Main$2;

    invoke-direct {v0, p0}, Lcom/projectinfinity/kodi/Main$2;-><init>(Lcom/projectinfinity/kodi/Main;)V

    invoke-virtual {p1, v0}, Landroid/view/View;->setOnSystemUiVisibilityChangeListener(Landroid/view/View$OnSystemUiVisibilityChangeListener;)V

    .line 325
    :cond_1c0
    iput-boolean v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityLaunchReady:Z

    const-string p1, "main.javaReady"

    .line 326
    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityStartupTrace;->mainEvent(Ljava/lang/String;)V

    .line 327
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getIntent()Landroid/content/Intent;

    move-result-object p1

    const-string v0, "infinity_kodi_launch_token"

    invoke-virtual {p1, v0}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    invoke-static {p0, p1}, Lcom/projectinfinity/kodi/InfinityKodiShutdown;->publish(Landroid/content/Context;Ljava/lang/String;)V

    return-void
.end method

.method public onDestroy()V
    .registers 5

    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onDestroy(Lcom/projectinfinity/kodi/Main;)V


    .line 523
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    const/4 v1, 0x0

    if-eqz v0, :cond_17

    .line 524
    :try_start_5
    invoke-super {p0}, Landroid/app/NativeActivity;->onDestroy()V
    :try_end_8
    .catchall {:try_start_5 .. :try_end_8} :catchall_f

    .line 525
    sget-object v0, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    if-ne v0, p0, :cond_e

    sput-object v1, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    :cond_e
    return-void

    :catchall_f
    move-exception v0

    sget-object v2, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    if-ne v2, p0, :cond_16

    sput-object v1, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    :cond_16
    throw v0

    :cond_17
    const-string v0, "exit.androidDestroy.enter"

    .line 528
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->trace(Landroid/content/Context;Ljava/lang/String;)V

    .line 529
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityAndroidKeyboard;->cancelOwner(Landroid/app/Activity;)V

    const-string v0, "main.destroy"

    .line 530
    invoke-static {v0}, Lcom/projectinfinity/kodi/InfinityStartupTrace;->mainEvent(Ljava/lang/String;)V

    .line 531
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityResponsiveness:Lcom/projectinfinity/kodi/InfinityResponsiveness;

    if-eqz v0, :cond_2b

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityResponsiveness;->close()V

    .line 532
    :cond_2b
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityResponsiveness:Lcom/projectinfinity/kodi/InfinityResponsiveness;

    const/4 v0, 0x0

    .line 533
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityLaunchReady:Z

    .line 534
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->infinityStopWeatherCapture()V

    .line 535
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v2}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->destroying()V

    const-string v2, "exit.beforeNativeDestroy"

    .line 536
    invoke-static {p0, v2}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V

    .line 537
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v2

    const-string v3, "main.onDestroy"

    invoke-static {v2, v3}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 538
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->isFinishing()Z

    move-result v2

    if-eqz v2, :cond_4f

    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityExtendedBackgroundService;->stopForExit(Landroid/content/Context;)V

    :cond_4f
    const/4 v2, 0x1

    .line 539
    iput-boolean v2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    .line 540
    invoke-static {v0, v0}, Lcom/projectinfinity/kodi/InfinityKodiAmbientGate;->update(ZZ)V

    .line 543
    invoke-static {}, Landroid/view/Choreographer;->getInstance()Landroid/view/Choreographer;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/Choreographer;->removeFrameCallback(Landroid/view/Choreographer$FrameCallback;)V

    .line 544
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacksAndMessages(Ljava/lang/Object;)V

    .line 545
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    invoke-virtual {v0}, Ljava/util/ArrayList;->clear()V

    .line 546
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    if-eqz v0, :cond_6d

    invoke-virtual {v0, v1}, Landroid/view/View;->setOnSystemUiVisibilityChangeListener(Landroid/view/View$OnSystemUiVisibilityChangeListener;)V

    .line 547
    :cond_6d
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz v0, :cond_74

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->detach()V

    .line 548
    :cond_74
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    if-eqz v0, :cond_7b

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityRefreshController;->close()V

    .line 549
    :cond_7b
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    .line 550
    iput-object v1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    .line 551
    invoke-static {p0}, Lcom/projectinfinity/kodi/channels/util/TvUtil;->cancelAllScheduledJobs(Landroid/content/Context;)V

    const-string v0, "input"

    .line 554
    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/Main;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/hardware/input/InputManager;

    if-eqz v0, :cond_93

    .line 555
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mInputDeviceListener:Lcom/projectinfinity/kodi/XBMCInputDeviceListener;

    if-eqz v2, :cond_93

    .line 556
    invoke-virtual {v0, v2}, Landroid/hardware/input/InputManager;->unregisterInputDeviceListener(Landroid/hardware/input/InputManager$InputDeviceListener;)V

    .line 558
    :cond_93
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mSettingsContentObserver:Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;

    if-eqz v0, :cond_a4

    .line 559
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mSettingsContentObserver:Lcom/projectinfinity/kodi/XBMCSettingsContentObserver;

    invoke-virtual {v0, v2}, Landroid/content/ContentResolver;->unregisterContentObserver(Landroid/database/ContentObserver;)V

    :cond_a4
    :try_start_a4
    const-string v0, "exit.nativeActivityDestroy.enter"

    .line 561
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->trace(Landroid/content/Context;Ljava/lang/String;)V

    .line 562
    invoke-super {p0}, Landroid/app/NativeActivity;->onDestroy()V

    const-string v0, "exit.nativeActivityDestroy.returned"

    .line 563
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->trace(Landroid/content/Context;Ljava/lang/String;)V

    .line 564
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->completed()V

    const-string v0, "exit.afterNativeDestroy.returned"

    .line 565
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V
    :try_end_bb
    .catchall {:try_start_a4 .. :try_end_bb} :catchall_c2

    .line 570
    sget-object v0, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    if-ne v0, p0, :cond_c1

    sput-object v1, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    :cond_c1
    return-void

    :catchall_c2
    move-exception v0

    sget-object v2, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    if-ne v2, p0, :cond_c9

    sput-object v1, Lcom/projectinfinity/kodi/Main;->MainActivity:Lcom/projectinfinity/kodi/Main;

    .line 572
    :cond_c9
    throw v0
.end method

.method public onMultiWindowModeChanged(Z)V
    .registers 2

    .line 683
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onMultiWindowModeChanged(Z)V

    .line 684
    iget-boolean p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz p1, :cond_8

    return-void

    :cond_8
    const-string p1, "multi-window"

    .line 685
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    return-void
.end method

.method public onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    .registers 3

    .line 624
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V

    .line 625
    iget-boolean p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz p1, :cond_8

    return-void

    .line 626
    :cond_8
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz p1, :cond_f

    invoke-virtual {p1}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onWindowChanged()V

    .line 627
    :cond_f
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    if-eqz p1, :cond_18

    const-string p2, "window"

    invoke-virtual {p1, p2}, Lcom/projectinfinity/kodi/InfinityRefreshController;->apply(Ljava/lang/String;)V

    :cond_18
    const-string p1, "multi-window"

    .line 628
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    const-string p1, "main.multiwindow"

    .line 629
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindowSettled(Ljava/lang/String;)V

    return-void
.end method

.method protected onNewIntent(Landroid/content/Intent;)V
    .registers 5

    .line 333
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityJavaPersistence;->userEntry(Landroid/content/Context;)V

    const-string v0, "main.newIntent"

    .line 335
    invoke-static {v0}, Lcom/projectinfinity/kodi/InfinityStartupTrace;->mainEvent(Ljava/lang/String;)V

    .line 336
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onNewIntent(Landroid/content/Intent;)V

    .line 337
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_18

    .line 338
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->setIntent(Landroid/content/Intent;)V

    .line 339
    iget-boolean p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryRecovery:Z

    invoke-static {p0, p1}, Lcom/projectinfinity/kodi/InfinityNativeTaskEntry;->returnToChooser(Landroid/app/Activity;Z)V

    return-void

    .line 342
    :cond_18
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-eqz v0, :cond_26

    const-string p1, "exit.checkpoint.rejectNewAndroidIntent"

    .line 343
    invoke-static {p0, p1}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->trace(Landroid/content/Context;Ljava/lang/String;)V

    return-void

    :cond_26
    const-string v0, "infinity_kodi_launch_token"

    .line 346
    invoke-virtual {p1, v0}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityKodiShutdown;->publish(Landroid/content/Context;Ljava/lang/String;)V

    .line 347
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityHandlePlayerRotationIntent(Landroid/content/Intent;)Z

    move-result v0

    if-eqz v0, :cond_36

    return-void

    .line 349
    :cond_36
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    const-string v1, "Kodi"

    if-eqz v0, :cond_53

    const-string v0, "Main: onNewIntent (delayed)"

    .line 351
    invoke-static {v1, v0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 352
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    new-instance v1, Lcom/projectinfinity/kodi/Main$DelayedIntent;

    new-instance v2, Landroid/content/Intent;

    invoke-direct {v2, p1}, Landroid/content/Intent;-><init>(Landroid/content/Intent;)V

    const/16 p1, 0x1f4

    invoke-direct {v1, p0, v2, p1}, Lcom/projectinfinity/kodi/Main$DelayedIntent;-><init>(Lcom/projectinfinity/kodi/Main;Landroid/content/Intent;I)V

    invoke-virtual {v0, v1}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

    goto :goto_5b

    :cond_53
    const-string v0, "Main: onNewIntent (immediate)"

    .line 356
    invoke-static {v1, v0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 357
    invoke-virtual {p0, p1}, Lcom/projectinfinity/kodi/Main;->_onNewIntent(Landroid/content/Intent;)V

    :goto_5b
    return-void
.end method

.method public onPause()V
    .registers 3

    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onPause(Lcom/projectinfinity/kodi/Main;)V


    .line 491
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_8

    invoke-super {p0}, Landroid/app/NativeActivity;->onPause()V

    return-void

    .line 492
    :cond_8
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityAndroidKeyboard;->cancelOwner(Landroid/app/Activity;)V

    const-string v0, "main.pause"

    .line 493
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindow(Ljava/lang/String;)V

    .line 494
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityResponsiveness:Lcom/projectinfinity/kodi/InfinityResponsiveness;

    if-eqz v0, :cond_17

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityResponsiveness;->pause()V

    .line 495
    :cond_17
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.onPause"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 496
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->infinityStopWeatherCapture()V

    .line 497
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-eqz v0, :cond_30

    const-string v0, "exit.normal.beforeAndroidPause"

    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V

    .line 498
    :cond_30
    invoke-super {p0}, Landroid/app/NativeActivity;->onPause()V

    .line 500
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-nez v0, :cond_5c

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object v0

    const-string v1, "android.software.leanback"

    invoke-virtual {v0, v1}, Landroid/content/pm/PackageManager;->hasSystemFeature(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_5c

    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v1, 0x1a

    if-lt v0, v1, :cond_5c

    .line 502
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->getLauncherName()Ljava/lang/String;

    move-result-object v0

    const-string v1, "com.google.android.tvlauncher"

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_5c

    .line 503
    invoke-static {p0}, Lcom/projectinfinity/kodi/channels/util/TvUtil;->scheduleSyncingChannel(Landroid/content/Context;)V

    :cond_5c
    const/4 v0, 0x1

    .line 506
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    const/4 v0, 0x0

    .line 507
    invoke-static {v0, v0}, Lcom/projectinfinity/kodi/InfinityKodiAmbientGate;->update(ZZ)V

    const-string v0, "pause"

    .line 508
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    .line 509
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-eqz v0, :cond_75

    const-string v0, "exit.normal.afterAndroidPause"

    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V

    :cond_75
    return-void
.end method

.method public onPictureInPictureModeChanged(Z)V
    .registers 3

    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p1}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onPictureInPictureChanged(Lcom/projectinfinity/kodi/Main;Z)V


    .line 673
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(Z)V

    .line 674
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_8

    return-void

    .line 675
    :cond_8
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    xor-int/lit8 v0, v0, 0x1

    invoke-static {v0, p1}, Lcom/projectinfinity/kodi/InfinityKodiAmbientGate;->update(ZZ)V

    const-string p1, "picture-in-picture"

    .line 676
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    return-void
.end method

.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    .registers 3

    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p1}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onPictureInPictureChanged(Lcom/projectinfinity/kodi/Main;Z)V


    .line 612
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V

    .line 613
    iget-boolean p2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz p2, :cond_8

    return-void

    .line 614
    :cond_8
    iget-boolean p2, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    xor-int/lit8 p2, p2, 0x1

    invoke-static {p2, p1}, Lcom/projectinfinity/kodi/InfinityKodiAmbientGate;->update(ZZ)V

    .line 615
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz p1, :cond_16

    invoke-virtual {p1}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onWindowChanged()V

    .line 616
    :cond_16
    iget-object p1, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    if-eqz p1, :cond_1f

    const-string p2, "window"

    invoke-virtual {p1, p2}, Lcom/projectinfinity/kodi/InfinityRefreshController;->apply(Ljava/lang/String;)V

    :cond_1f
    const-string p1, "picture-in-picture"

    .line 617
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    const-string p1, "main.pip"

    .line 618
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindowSettled(Ljava/lang/String;)V

    return-void
.end method

.method public onResume()V
    .registers 9

    .line 399
    invoke-super {p0}, Landroid/app/NativeActivity;->onResume()V

    .line 400
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_8

    return-void

    .line 401
    :cond_8
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.onResume"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 402
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    const/4 v1, 0x1

    if-eqz v0, :cond_47

    .line 406
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->checkpointPending()Z

    move-result v0

    if-eqz v0, :cond_28

    const-string v0, "exit.checkpoint.resumedDuringSave.ownerRetained"

    .line 407
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V

    return-void

    .line 412
    :cond_28
    invoke-direct {p0, v1}, Lcom/projectinfinity/kodi/Main;->infinitySetCurrentTaskExcludedFromRecents(Z)V

    const-string v0, "exit.checkpoint.recentsResumeRecovery"

    .line 413
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V

    .line 414
    new-instance v0, Landroid/content/Intent;

    const-class v2, Lcom/projectinfinity/kodi/Splash;

    invoke-direct {v0, p0, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v2, "infinity_checkpoint_chooser"

    invoke-virtual {v0, v2, v1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Z)Landroid/content/Intent;

    move-result-object v0

    const/high16 v1, 0x30000000

    .line 415
    invoke-virtual {v0, v1}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    move-result-object v0

    .line 414
    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/Main;->startActivity(Landroid/content/Intent;)V

    return-void

    :cond_47
    const/4 v0, 0x0

    .line 418
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinitySetCurrentTaskExcludedFromRecents(Z)V

    .line 419
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mInfinityResponsiveness:Lcom/projectinfinity/kodi/InfinityResponsiveness;

    if-eqz v2, :cond_52

    invoke-virtual {v2}, Lcom/projectinfinity/kodi/InfinityResponsiveness;->resume()V

    .line 421
    :cond_52
    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v3, 0x1e

    if-lt v2, v3, :cond_7a

    .line 423
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getWindow()Landroid/view/Window;

    move-result-object v2

    invoke-static {v2, v0}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0;->m$1(Landroid/view/Window;Z)V

    .line 424
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getWindow()Landroid/view/Window;

    move-result-object v2

    invoke-static {v2}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0;->m(Landroid/view/Window;)Landroid/view/WindowInsetsController;

    move-result-object v2

    if-eqz v2, :cond_81

    .line 427
    invoke-static {}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0;->m()I

    move-result v3

    invoke-static {}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m()I

    move-result v4

    or-int/2addr v3, v4

    invoke-static {v2, v3}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0;->m$1(Landroid/view/WindowInsetsController;I)V

    const/4 v3, 0x2

    .line 428
    invoke-static {v2, v3}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0;->m(Landroid/view/WindowInsetsController;I)V

    goto :goto_81

    .line 434
    :cond_7a
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    const/16 v3, 0x1706

    invoke-virtual {v2, v3}, Landroid/view/View;->setSystemUiVisibility(I)V

    .line 444
    :cond_81
    :goto_81
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    invoke-virtual {v2}, Ljava/util/ArrayList;->iterator()Ljava/util/Iterator;

    move-result-object v2

    :goto_87
    invoke-interface {v2}, Ljava/util/Iterator;->hasNext()Z

    move-result v3

    if-eqz v3, :cond_a1

    invoke-interface {v2}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v3

    check-cast v3, Lcom/projectinfinity/kodi/Main$DelayedIntent;

    .line 446
    iget-object v4, p0, Lcom/projectinfinity/kodi/Main;->handler:Landroid/os/Handler;

    new-instance v5, Lcom/projectinfinity/kodi/Main$3;

    invoke-direct {v5, p0, v3}, Lcom/projectinfinity/kodi/Main$3;-><init>(Lcom/projectinfinity/kodi/Main;Lcom/projectinfinity/kodi/Main$DelayedIntent;)V

    iget v3, v3, Lcom/projectinfinity/kodi/Main$DelayedIntent;->mDelay:I

    int-to-long v6, v3

    invoke-virtual {v4, v5, v6, v7}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_87

    .line 468
    :cond_a1
    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:Ljava/util/ArrayList;

    invoke-virtual {v2}, Ljava/util/ArrayList;->clear()V

    .line 469
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mPaused:Z

    .line 470
    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v3, 0x1a

    if-lt v2, v3, :cond_b5

    invoke-static {p0}, Lcom/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;->m(Lcom/projectinfinity/kodi/Main;)Z

    move-result v2

    if-eqz v2, :cond_b5

    const/4 v0, 0x1

    :cond_b5
    invoke-static {v1, v0}, Lcom/projectinfinity/kodi/InfinityKodiAmbientGate;->update(ZZ)V

    .line 471
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz v0, :cond_bf

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onResume()V

    .line 472
    :cond_bf
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    const-string v1, "resume"

    if-eqz v0, :cond_c8

    invoke-virtual {v0, v1}, Lcom/projectinfinity/kodi/InfinityRefreshController;->apply(Ljava/lang/String;)V

    .line 473
    :cond_c8
    invoke-direct {p0, v1}, Lcom/projectinfinity/kodi/Main;->infinityApplyPlayerRotation(Ljava/lang/String;)V

    .line 474
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-nez v0, :cond_d6

    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityExtendedBackgroundService;->sync(Landroid/app/Activity;)V

    .line 475
    :cond_d6
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-nez v0, :cond_e4

    .line 476
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityResumeHubInstaller;->apply(Landroid/content/Context;)V

    .line 477
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityPowerMenuRoutes;->applyAsync(Landroid/content/Context;)V

    .line 479
    :cond_e4
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-nez v0, :cond_103

    .line 480
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->infinityStopWeatherCapture()V

    .line 481
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.weather.snapshotOnly"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 482
    new-instance v0, Lcom/projectinfinity/kodi/InfinityChooserWeather;

    const/4 v1, 0x0

    invoke-direct {v0, p0, v1}, Lcom/projectinfinity/kodi/InfinityChooserWeather;-><init>(Landroid/content/Context;Landroid/widget/TextView;)V

    iput-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityWeatherCapture:Lcom/projectinfinity/kodi/InfinityChooserWeather;

    .line 483
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityChooserWeather;->start()V

    :cond_103
    const-string v0, "main.resume"

    .line 485
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindowSettled(Ljava/lang/String;)V


    # Infinity Repair5: session-owned lock; original method retained.
    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/InfinityVideoLockBridge;->onResume(Lcom/projectinfinity/kodi/Main;)V

    return-void
.end method

.method public onStart()V
    .registers 3

    const/4 v0, 0x0

    .line 364
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityStopped:Z

    .line 365
    invoke-super {p0}, Landroid/app/NativeActivity;->onStart()V

    .line 366
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_b

    return-void

    .line 367
    :cond_b
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.onStart"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 369
    invoke-static {}, Landroid/view/Choreographer;->getInstance()Landroid/view/Choreographer;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/Choreographer;->removeFrameCallback(Landroid/view/Choreographer$FrameCallback;)V

    .line 370
    invoke-static {}, Landroid/view/Choreographer;->getInstance()Landroid/view/Choreographer;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/Choreographer;->postFrameCallback(Landroid/view/Choreographer$FrameCallback;)V

    return-void
.end method

.method public onStop()V
    .registers 3

    .line 645
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_8

    invoke-super {p0}, Landroid/app/NativeActivity;->onStop()V

    return-void

    :cond_8
    const-string v0, "main.stop"

    .line 646
    invoke-direct {p0, v0}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindow(Ljava/lang/String;)V

    .line 647
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    const-string v1, "main.onStop"

    invoke-static {v0, v1}, Lcom/projectinfinity/kodi/InfinityExitDiagnostics;->breadcrumb(Landroid/content/Context;Ljava/lang/String;)V

    .line 648
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-eqz v0, :cond_23

    const-string v0, "exit.normal.beforeAndroidStop"

    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->record(Landroid/content/Context;Ljava/lang/String;)V

    :cond_23
    const/4 v0, -0x1

    const-string v1, "stop"

    .line 649
    invoke-direct {p0, v0, v1}, Lcom/projectinfinity/kodi/Main;->infinityRequestPlayerOrientation(ILjava/lang/String;)V

    .line 650
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz v0, :cond_30

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onStop()V

    .line 651
    :cond_30
    invoke-super {p0}, Landroid/app/NativeActivity;->onStop()V

    const/4 v0, 0x1

    .line 652
    iput-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityStopped:Z

    .line 653
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityExitCompletion;->afterStop(Lcom/projectinfinity/kodi/Main;)V

    return-void
.end method

.method protected onUserLeaveHint()V
    .registers 2

    .line 593
    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V

    .line 594
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityExitPlan:Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;->pending()Z

    move-result v0

    if-nez v0, :cond_12

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz v0, :cond_12

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onUserLeaveHint()V

    :cond_12
    return-void
.end method

.method public onVisibleBehindCanceled()V
    .registers 2

    .line 578
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityDestroyed:Z

    if-nez v0, :cond_7

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_onVisibleBehindCanceled()V

    .line 579
    :cond_7
    invoke-super {p0}, Landroid/app/NativeActivity;->onVisibleBehindCanceled()V

    return-void
.end method

.method public onWindowFocusChanged(Z)V
    .registers 4

    .line 635
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onWindowFocusChanged(Z)V

    .line 636
    iget-boolean v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityNativeEntryDenied:Z

    if-eqz v0, :cond_8

    return-void

    :cond_8
    if-eqz p1, :cond_11

    .line 637
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityBridge:Lcom/projectinfinity/kodi/InfinityCoreBridge;

    if-eqz v0, :cond_11

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->onWindowChanged()V

    :cond_11
    if-eqz p1, :cond_1c

    .line 638
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mInfinityRefresh:Lcom/projectinfinity/kodi/InfinityRefreshController;

    if-eqz v0, :cond_1c

    const-string v1, "focus"

    invoke-virtual {v0, v1}, Lcom/projectinfinity/kodi/InfinityRefreshController;->apply(Ljava/lang/String;)V

    :cond_1c
    if-eqz p1, :cond_23

    const-string p1, "main.focus"

    .line 639
    invoke-direct {p0, p1}, Lcom/projectinfinity/kodi/Main;->infinityTraceWindowSettled(Ljava/lang/String;)V

    :cond_23
    return-void
.end method

.method public registerMediaButtonEventReceiver()V
    .registers 5

    const-string v0, "audio"

    .line 165
    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/Main;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/media/AudioManager;

    .line 166
    new-instance v1, Landroid/content/ComponentName;

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getPackageName()Ljava/lang/String;

    move-result-object v2

    const-class v3, Lcom/projectinfinity/kodi/XBMCBroadcastReceiver;

    invoke-virtual {v3}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v3

    invoke-direct {v1, v2, v3}, Landroid/content/ComponentName;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/media/AudioManager;->registerMediaButtonEventReceiver(Landroid/content/ComponentName;)V

    return-void
.end method

.method public unregisterMediaButtonEventReceiver()V
    .registers 5

    const-string v0, "audio"

    .line 171
    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/Main;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/media/AudioManager;

    .line 172
    new-instance v1, Landroid/content/ComponentName;

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getPackageName()Ljava/lang/String;

    move-result-object v2

    const-class v3, Lcom/projectinfinity/kodi/XBMCBroadcastReceiver;

    invoke-virtual {v3}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v3

    invoke-direct {v1, v2, v3}, Landroid/content/ComponentName;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/media/AudioManager;->unregisterMediaButtonEventReceiver(Landroid/content/ComponentName;)V

    return-void
.end method
