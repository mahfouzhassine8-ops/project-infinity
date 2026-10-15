from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# 5.3.6 PERSISTENT EVENT LISTENER
# Base: proven 5.3.4 transport checkpoint.
# Goal: keep ONE TCP JSON-RPC connection open and let Kodi notify the brain.
# - initial GetActivePlayers sync after connect
# - Player.OnAVStart (video player id 1) => isVideoPlaying = true
# - Player.OnStop (video player id 1, or if video was active) => false
# - automatic reconnect with 2-second backoff
# - proper brace framing that ignores braces inside quoted JSON strings
# - NO PiP action yet, NO native changes

main_candidates=[]
for smali_root in ROOT.glob('smali*'):
    main_candidates.extend(smali_root.rglob('Main.smali'))
main_candidates=[p for p in main_candidates if 'projectinfinity/kodi' in str(p).replace('\\','/')]
if not main_candidates:
    raise SystemExit('5.3.4 Main.smali not found')
MAIN=main_candidates[0]
PKG_DIR=MAIN.parent
main_text=MAIN.read_text()
cm=re.search(r'^\.class[^\n]*\s(L[^;]+;)', main_text, re.M)
if not cm:
    raise SystemExit('Could not determine Main descriptor')
PKG_DESC=cm.group(1).rsplit('/',1)[0]
CTRL=f'{PKG_DESC}/InfinityController;'
LISTENER=f'{PKG_DESC}/InfinityController$KodiListenerRunnable;'
TOAST=f'{PKG_DESC}/InfinityController$ToastRunnable;'

controller=f'''.class public final {CTRL}
.super Ljava/lang/Object;
.source "InfinityController.java"

.field private static activity:Landroid/app/Activity;
.field public static volatile isVideoPlaying:Z
.field private static volatile listenerStarted:Z

.method static constructor <clinit>()V
    .locals 1
    const/4 v0, 0x0
    sput-boolean v0, {CTRL}->isVideoPlaying:Z
    sput-boolean v0, {CTRL}->listenerStarted:Z
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
    sget-boolean v0, {CTRL}->listenerStarted:Z
    if-nez v0, :done
    const/4 v0, 0x1
    sput-boolean v0, {CTRL}->listenerStarted:Z
    new-instance v0, Ljava/lang/Thread;
    new-instance v1, {LISTENER}
    invoke-direct {{v1}}, {LISTENER}-><init>()V
    invoke-direct {{v0, v1}}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    const-string v1, "InfinityKodiListener"
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

.method public static setVideoPlaying(ZLjava/lang/String;)V
    .locals 2
    sget-boolean v0, {CTRL}->isVideoPlaying:Z
    if-ne v0, p0, :changed
    return-void
    :changed
    sput-boolean p0, {CTRL}->isVideoPlaying:Z
    invoke-static {{p1}}, {CTRL}->showResult(Ljava/lang/String;)V
    return-void
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

listener=f'''.class public final {LISTENER}
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "InfinityController.java"

.method public constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method private static handleMessage(Ljava/lang/String;)V
    .locals 4

    # Initial sync response: GetActivePlayers id=53.
    const-string v0, "\\\"id\\\":53"
    invoke-virtual {{p0, v0}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v0
    if-eqz v0, :check_start
    const-string v0, "\\\"type\\\":\\\"video\\\""
    invoke-virtual {{p0, v0}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v0
    if-eqz v0, :sync_off
    const/4 v0, 0x1
    const-string v1, "Infinity brain: VIDEO PLAYING"
    invoke-static {{v0, v1}}, {CTRL}->setVideoPlaying(ZLjava/lang/String;)V
    return-void
    :sync_off
    const/4 v0, 0x0
    const-string v1, "Infinity brain: NO VIDEO"
    invoke-static {{v0, v1}}, {CTRL}->setVideoPlaying(ZLjava/lang/String;)V
    return-void

    :check_start
    const-string v0, "Player.OnAVStart"
    invoke-virtual {{p0, v0}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v0
    if-eqz v0, :check_stop
    const-string v0, "\\\"playerid\\\":1"
    invoke-virtual {{p0, v0}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v0
    if-eqz v0, :done
    const/4 v0, 0x1
    const-string v1, "Infinity brain: VIDEO PLAYING"
    invoke-static {{v0, v1}}, {CTRL}->setVideoPlaying(ZLjava/lang/String;)V
    return-void

    :check_stop
    const-string v0, "Player.OnStop"
    invoke-virtual {{p0, v0}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v0
    if-eqz v0, :done
    sget-boolean v0, {CTRL}->isVideoPlaying:Z
    if-eqz v0, :done
    const/4 v0, 0x0
    const-string v1, "Infinity brain: NO VIDEO"
    invoke-static {{v0, v1}}, {CTRL}->setVideoPlaying(ZLjava/lang/String;)V

    :done
    return-void
.end method

.method public run()V
    .locals 16

    # Let Kodi finish booting before the first connect attempt.
    const-wide/16 v0, 0x1388
    :first_sleep_start
    invoke-static {{v0, v1}}, Ljava/lang/Thread;->sleep(J)V
    :first_sleep_end
    .catch Ljava/lang/Throwable; {{:first_sleep_start .. :first_sleep_end}} :reconnect

    :reconnect
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

    # Keep reads blocking while connected; notifications arrive whenever Kodi emits them.
    const/4 v4, 0x0
    invoke-virtual {{v3, v4}}, Ljava/net/Socket;->setSoTimeout(I)V

    # One initial state sync so reconnects know whether a video is already active.
    invoke-virtual {{v3}}, Ljava/net/Socket;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v4
    const-string v5, "{{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"Player.GetActivePlayers\\\",\\\"id\\\":53}}"
    const-string v6, "UTF-8"
    invoke-virtual {{v5, v6}}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B
    move-result-object v5
    invoke-virtual {{v4, v5}}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {{v4}}, Ljava/io/OutputStream;->flush()V

    invoke-virtual {{v3}}, Ljava/net/Socket;->getInputStream()Ljava/io/InputStream;
    move-result-object v4

    # Framing state: depth, started, inString, escaped, current JSON bytes.
    const/4 v6, 0x0
    const/4 v7, 0x0
    const/4 v8, 0x0
    const/4 v9, 0x0
    new-instance v10, Ljava/io/ByteArrayOutputStream;
    invoke-direct {{v10}}, Ljava/io/ByteArrayOutputStream;-><init>()V

    :read_loop
    invoke-virtual {{v4}}, Ljava/io/InputStream;->read()I
    move-result v11
    const/4 v12, -0x1
    if-eq v11, v12, :disconnected

    # Ignore whitespace/noise before the opening brace.
    if-nez v7, :store_char
    const/16 v12, 0x7b
    if-ne v11, v12, :read_loop
    const/4 v7, 0x1
    const/4 v6, 0x1
    invoke-virtual {{v10, v11}}, Ljava/io/ByteArrayOutputStream;->write(I)V
    goto :read_loop

    :store_char
    invoke-virtual {{v10, v11}}, Ljava/io/ByteArrayOutputStream;->write(I)V

    # If previous character was an escape inside a string, this char is literal.
    if-eqz v8, :not_in_string
    if-eqz v9, :string_not_escaped
    const/4 v9, 0x0
    goto :maybe_frame_done

    :string_not_escaped
    const/16 v12, 0x5c
    if-ne v11, v12, :string_quote_check
    const/4 v9, 0x1
    goto :maybe_frame_done
    :string_quote_check
    const/16 v12, 0x22
    if-ne v11, v12, :maybe_frame_done
    const/4 v8, 0x0
    goto :maybe_frame_done

    :not_in_string
    const/16 v12, 0x22
    if-ne v11, v12, :brace_open_check
    const/4 v8, 0x1
    goto :maybe_frame_done
    :brace_open_check
    const/16 v12, 0x7b
    if-ne v11, v12, :brace_close_check
    add-int/lit8 v6, v6, 0x1
    goto :maybe_frame_done
    :brace_close_check
    const/16 v12, 0x7d
    if-ne v11, v12, :maybe_frame_done
    add-int/lit8 v6, v6, -0x1

    :maybe_frame_done
    if-nez v6, :read_loop
    if-nez v8, :read_loop

    const-string v12, "UTF-8"
    invoke-virtual {{v10, v12}}, Ljava/io/ByteArrayOutputStream;->toString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v12
    invoke-static {{v12}}, {LISTENER}->handleMessage(Ljava/lang/String;)V

    # Reset frame state for the next notification/response on the SAME socket.
    const/4 v6, 0x0
    const/4 v7, 0x0
    const/4 v8, 0x0
    const/4 v9, 0x0
    new-instance v10, Ljava/io/ByteArrayOutputStream;
    invoke-direct {{v10}}, Ljava/io/ByteArrayOutputStream;-><init>()V
    goto :read_loop

    :disconnected
    invoke-virtual {{v3}}, Ljava/net/Socket;->close()V
    :try_end
    .catch Ljava/lang/Throwable; {{:try_start .. :try_end}} :caught
    goto :backoff

    :caught
    if-eqz v2, :backoff
    :close_start
    invoke-virtual {{v2}}, Ljava/net/Socket;->close()V
    :close_end
    .catch Ljava/lang/Throwable; {{:close_start .. :close_end}} :backoff

    :backoff
    # Lost connection means state is unknown; clear it without UI spam.
    const/4 v12, 0x0
    sput-boolean v12, {CTRL}->isVideoPlaying:Z
    const-wide/16 v13, 0x7d0
    :sleep_start
    invoke-static {{v13, v14}}, Ljava/lang/Thread;->sleep(J)V
    :sleep_end
    .catch Ljava/lang/Throwable; {{:sleep_start .. :sleep_end}} :reconnect
    goto :reconnect
.end method
'''

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

# Replace 5.3.4's one-shot diagnostic helper with the persistent listener only.
for old in [
    'InfinityController$TransportProbeRunnable.smali',
    'InfinityController$PlaybackProbeRunnable.smali',
    'InfinityController$ToastRunnable.smali',
    'InfinityController$KodiListenerRunnable.smali',
]:
    p=PKG_DIR/old
    if p.exists(): p.unlink()

(PKG_DIR/'InfinityController.smali').write_text(controller)
(PKG_DIR/'InfinityController$KodiListenerRunnable.smali').write_text(listener)
(PKG_DIR/'InfinityController$ToastRunnable.smali').write_text(toast)

if f'{CTRL}->init(Landroid/app/Activity;)V' not in main_text:
    raise SystemExit('5.3.4 init hook missing; refusing to widen scope')
manifest=(ROOT/'AndroidManifest.xml').read_text()
if 'android:supportsPictureInPicture="true"' not in manifest:
    raise SystemExit('5.3.4 PiP manifest capability missing; refusing to widen scope')

print('5.3.6 applied: persistent Kodi TCP notification listener')
print('Initial GetActivePlayers sync + OnAVStart/OnStop events + reconnect; no PiP action')
