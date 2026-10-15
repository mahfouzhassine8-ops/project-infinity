from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# 5.3.6 TWO-SHOT PLAYBACK DIAGNOSTIC
# Base: proven 5.3.5 playback-probe build.
# Goal: prove BOTH Kodi states in one app session.
# Check 1 at ~7s (stay on menu) and Check 2 at ~30s (start a video after Check 1).
# No PiP action, no permanent listener, no polling loop, no native changes.

main_candidates=[]
for smali_root in ROOT.glob('smali*'):
    main_candidates.extend(smali_root.rglob('Main.smali'))
main_candidates=[p for p in main_candidates if 'projectinfinity/kodi' in str(p).replace('\\','/')]
if not main_candidates:
    raise SystemExit('5.3.5 Main.smali not found')
MAIN=main_candidates[0]
PKG_DIR=MAIN.parent
main_text=MAIN.read_text()
cm=re.search(r'^\.class[^\n]*\s(L[^;]+;)', main_text, re.M)
if not cm:
    raise SystemExit('Could not determine Main descriptor')
PKG_DESC=cm.group(1).rsplit('/',1)[0]
CTRL=f'{PKG_DESC}/InfinityController;'
PROBE1=f'{PKG_DESC}/InfinityController$PlaybackProbe1Runnable;'
PROBE2=f'{PKG_DESC}/InfinityController$PlaybackProbe2Runnable;'
TOAST=f'{PKG_DESC}/InfinityController$ToastRunnable;'

controller=f'''.class public final {CTRL}
.super Ljava/lang/Object;
.source "InfinityController.java"

.field private static activity:Landroid/app/Activity;
.field public static volatile isVideoPlaying:Z
.field private static volatile playbackProbeStarted:Z

.method static constructor <clinit>()V
    .locals 1
    const/4 v0, 0x0
    sput-boolean v0, {CTRL}->isVideoPlaying:Z
    sput-boolean v0, {CTRL}->playbackProbeStarted:Z
    return-void
.end method

.method private constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static init(Landroid/app/Activity;)V
    .locals 2
    sput-object p0, {CTRL}->activity:Landroid/app/Activity;
    sget-boolean v0, {CTRL}->playbackProbeStarted:Z
    if-nez v0, :done
    const/4 v0, 0x1
    sput-boolean v0, {CTRL}->playbackProbeStarted:Z

    new-instance v0, Ljava/lang/Thread;
    new-instance v1, {PROBE1}
    invoke-direct {{v1}}, {PROBE1}-><init>()V
    invoke-direct {{v0, v1}}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    const-string v1, "InfinityPlaybackProbe1"
    invoke-virtual {{v0, v1}}, Ljava/lang/Thread;->setName(Ljava/lang/String;)V
    invoke-virtual {{v0}}, Ljava/lang/Thread;->start()V

    new-instance v0, Ljava/lang/Thread;
    new-instance v1, {PROBE2}
    invoke-direct {{v1}}, {PROBE2}-><init>()V
    invoke-direct {{v0, v1}}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    const-string v1, "InfinityPlaybackProbe2"
    invoke-virtual {{v0, v1}}, Ljava/lang/Thread;->setName(Ljava/lang/String;)V
    invoke-virtual {{v0}}, Ljava/lang/Thread;->start()V

    :done
    return-void
.end method

.method public static shouldAllowPiP()Z
    .locals 1
    sget-boolean v0, {CTRL}->isVideoPlaying:Z
    return v0
.end method

.method public static showResult(Ljava/lang/String;)V
    .locals 2
    sget-object v0, {CTRL}->activity:Landroid/app/Activity;
    if-eqz v0, :done
    new-instance v1, {TOAST}
    invoke-direct {{v1, v0, p0}}, {TOAST}-><init>(Landroid/app/Activity;Ljava/lang/String;)V
    invoke-virtual {{v0, v1}}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :done
    return-void
.end method
'''

def make_probe(desc, delay_hex, label):
    return f'''.class public final {desc}
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "InfinityController.java"

.method public constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public run()V
    .locals 14
    const-wide/16 v0, {delay_hex}
    :sleep_start
    invoke-static {{v0, v1}}, Ljava/lang/Thread;->sleep(J)V
    :sleep_end
    .catch Ljava/lang/Throwable; {{:sleep_start .. :sleep_end}} :fail

    const/4 v2, 0x0
    :try_start
    new-instance v3, Ljava/net/Socket;
    invoke-direct {{v3}}, Ljava/net/Socket;-><init>()V
    move-object v2, v3
    new-instance v4, Ljava/net/InetSocketAddress;
    const-string v5, "127.0.0.1"
    const/16 v6, 0x2382
    invoke-direct {{v4, v5, v6}}, Ljava/net/InetSocketAddress;-><init>(Ljava/lang/String;I)V
    const/16 v5, 0x5dc
    invoke-virtual {{v3, v4, v5}}, Ljava/net/Socket;->connect(Ljava/net/SocketAddress;I)V
    const/16 v4, 0x7d0
    invoke-virtual {{v3, v4}}, Ljava/net/Socket;->setSoTimeout(I)V
    invoke-virtual {{v3}}, Ljava/net/Socket;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v4
    const-string v5, "{{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"Player.GetActivePlayers\\\",\\\"id\\\":6}}"
    const-string v6, "UTF-8"
    invoke-virtual {{v5,v6}}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B
    move-result-object v5
    invoke-virtual {{v4,v5}}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {{v4}}, Ljava/io/OutputStream;->flush()V
    invoke-virtual {{v3}}, Ljava/net/Socket;->getInputStream()Ljava/io/InputStream;
    move-result-object v4
    new-instance v5, Ljava/io/ByteArrayOutputStream;
    invoke-direct {{v5}}, Ljava/io/ByteArrayOutputStream;-><init>()V
    const/4 v6,0x0
    const/4 v7,0x0
    :read_loop
    invoke-virtual {{v4}}, Ljava/io/InputStream;->read()I
    move-result v8
    const/4 v9,-0x1
    if-eq v8,v9,:finish_read
    invoke-virtual {{v5,v8}}, Ljava/io/ByteArrayOutputStream;->write(I)V
    const/16 v9,0x7b
    if-ne v8,v9,:check_close
    add-int/lit8 v6,v6,0x1
    const/4 v7,0x1
    goto :maybe_done
    :check_close
    const/16 v9,0x7d
    if-ne v8,v9,:maybe_done
    add-int/lit8 v6,v6,-0x1
    :maybe_done
    if-eqz v7,:read_loop
    if-nez v6,:read_loop
    :finish_read
    const-string v4,"UTF-8"
    invoke-virtual {{v5,v4}}, Ljava/io/ByteArrayOutputStream;->toString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    const-string v5,"\\\"type\\\":\\\"video\\\""
    invoke-virtual {{v4,v5}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v5
    if-eqz v5,:no_video
    const/4 v6,0x1
    sput-boolean v6, {CTRL}->isVideoPlaying:Z
    invoke-virtual {{v3}}, Ljava/net/Socket;->close()V
    const-string v4,"{label}: VIDEO PLAYING"
    invoke-static {{v4}}, {CTRL}->showResult(Ljava/lang/String;)V
    return-void

    :no_video
    const/4 v6,0x0
    sput-boolean v6, {CTRL}->isVideoPlaying:Z
    invoke-virtual {{v3}}, Ljava/net/Socket;->close()V
    const-string v4,"{label}: NO VIDEO"
    invoke-static {{v4}}, {CTRL}->showResult(Ljava/lang/String;)V
    return-void

    :try_end
    .catch Ljava/lang/Throwable; {{:try_start .. :try_end}} :caught
    :caught
    if-eqz v2,:fail
    :close_try
    invoke-virtual {{v2}}, Ljava/net/Socket;->close()V
    :close_end
    .catch Ljava/lang/Throwable; {{:close_try .. :close_end}} :fail
    :fail
    const-string v4,"{label}: PROBE FAIL"
    invoke-static {{v4}}, {CTRL}->showResult(Ljava/lang/String;)V
    return-void
.end method
'''

probe1=make_probe(PROBE1, '0x1b58', 'Check 1')
probe2=make_probe(PROBE2, '0x7530', 'Check 2')

toast=f'''.class public final {TOAST}
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "InfinityController.java"
.field private final activity:Landroid/app/Activity;
.field private final message:Ljava/lang/String;
.method public constructor <init>(Landroid/app/Activity;Ljava/lang/String;)V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    iput-object p1,p0,{TOAST}->activity:Landroid/app/Activity;
    iput-object p2,p0,{TOAST}->message:Ljava/lang/String;
    return-void
.end method
.method public run()V
    .locals 3
    iget-object v0,p0,{TOAST}->activity:Landroid/app/Activity;
    iget-object v1,p0,{TOAST}->message:Ljava/lang/String;
    const/4 v2,0x1
    invoke-static {{v0,v1,v2}}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {{v0}}, Landroid/widget/Toast;->show()V
    return-void
.end method
'''

(PKG_DIR/'InfinityController.smali').write_text(controller)
for old in [
    'InfinityController$PlaybackProbeRunnable.smali',
    'InfinityController$PlaybackProbe1Runnable.smali',
    'InfinityController$PlaybackProbe2Runnable.smali',
    'InfinityController$ToastRunnable.smali'
]:
    p=PKG_DIR/old
    if p.exists(): p.unlink()
(PKG_DIR/'InfinityController$PlaybackProbe1Runnable.smali').write_text(probe1)
(PKG_DIR/'InfinityController$PlaybackProbe2Runnable.smali').write_text(probe2)
(PKG_DIR/'InfinityController$ToastRunnable.smali').write_text(toast)

if f'{CTRL}->init(Landroid/app/Activity;)V' not in main_text:
    raise SystemExit('5.3.5 init hook missing')
manifest=(ROOT/'AndroidManifest.xml').read_text()
if 'android:supportsPictureInPicture="true"' not in manifest:
    raise SystemExit('PiP manifest capability missing')

print('5.3.6 applied: two one-shot playback checks at ~7s and ~30s')
