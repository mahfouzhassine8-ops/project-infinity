from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# 5.3.4 TRANSPORT PROBE
# Base: proven 5.3.3 development checkpoint.
# Goal: prove Android/InfinityController can talk to Kodi and receive a reply.
# Scope: ONE delayed, ONE-SHOT JSON-RPC Ping over Kodi TCP 9090.
# No PiP entry logic, no polling loop, no playback listener, no native changes.

main_candidates = []
for smali_root in ROOT.glob('smali*'):
    main_candidates.extend(smali_root.rglob('Main.smali'))
main_candidates = [p for p in main_candidates if 'projectinfinity/kodi' in str(p).replace('\\', '/')]
if not main_candidates:
    raise SystemExit('5.3.3 Main.smali not found')

MAIN = main_candidates[0]
PKG_DIR = MAIN.parent
main_text = MAIN.read_text()

class_match = re.search(r'^\.class[^\n]*\s(L[^;]+;)', main_text, re.M)
if not class_match:
    raise SystemExit('Could not determine Main descriptor')
MAIN_DESC = class_match.group(1)
PKG_DESC = MAIN_DESC.rsplit('/', 1)[0]
CTRL = f'{PKG_DESC}/InfinityController;'
PROBE = f'{PKG_DESC}/InfinityController$TransportProbeRunnable;'
TOAST = f'{PKG_DESC}/InfinityController$ToastRunnable;'

controller = f'''.class public final {CTRL}
.super Ljava/lang/Object;
.source "InfinityController.java"

.field private static activity:Landroid/app/Activity;
.field public static volatile isVideoPlaying:Z
.field private static volatile transportProbeStarted:Z

.method static constructor <clinit>()V
    .locals 1
    const/4 v0, 0x0
    sput-boolean v0, {CTRL}->isVideoPlaying:Z
    sput-boolean v0, {CTRL}->transportProbeStarted:Z
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

    # Start exactly one diagnostic thread for this process.
    sget-boolean v0, {CTRL}->transportProbeStarted:Z
    if-nez v0, :done
    const/4 v0, 0x1
    sput-boolean v0, {CTRL}->transportProbeStarted:Z

    new-instance v0, Ljava/lang/Thread;
    new-instance v1, {PROBE}
    invoke-direct {{v1}}, {PROBE}-><init>()V
    invoke-direct {{v0, v1}}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    const-string v1, "InfinityTransportProbe"
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

.method public static showTransportResult(Ljava/lang/String;)V
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

probe = f'''.class public final {PROBE}
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

    # Give Kodi time to finish reaching its main menu before probing.
    const-wide/16 v0, 0x1b58
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
    const-string v5, "{{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"JSONRPC.Ping\\\",\\\"id\\\":1}}"
    const-string v6, "UTF-8"
    invoke-virtual {{v5, v6}}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B
    move-result-object v5
    invoke-virtual {{v4, v5}}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {{v4}}, Ljava/io/OutputStream;->flush()V

    invoke-virtual {{v3}}, Ljava/net/Socket;->getInputStream()Ljava/io/InputStream;
    move-result-object v4
    new-instance v5, Ljava/io/ByteArrayOutputStream;
    invoke-direct {{v5}}, Ljava/io/ByteArrayOutputStream;-><init>()V

    const/4 v6, 0x0
    const/4 v7, 0x0

    :read_loop
    invoke-virtual {{v4}}, Ljava/io/InputStream;->read()I
    move-result v8
    const/4 v9, -0x1
    if-eq v8, v9, :finish_read
    invoke-virtual {{v5, v8}}, Ljava/io/ByteArrayOutputStream;->write(I)V

    const/16 v9, 0x7b
    if-ne v8, v9, :check_close
    add-int/lit8 v6, v6, 0x1
    const/4 v7, 0x1
    goto :maybe_done

    :check_close
    const/16 v9, 0x7d
    if-ne v8, v9, :maybe_done
    add-int/lit8 v6, v6, -0x1

    :maybe_done
    if-eqz v7, :read_loop
    if-nez v6, :read_loop

    :finish_read
    const-string v4, "UTF-8"
    invoke-virtual {{v5, v4}}, Ljava/io/ByteArrayOutputStream;->toString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4

    const-string v5, "\\\"result\\\":\\\"pong\\\""
    invoke-virtual {{v4, v5}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v5
    if-nez v5, :success

    const-string v5, "\\\"id\\\":1"
    invoke-virtual {{v4, v5}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v5
    if-eqz v5, :bad_reply

    :success
    invoke-virtual {{v3}}, Ljava/net/Socket;->close()V
    const-string v4, "Infinity transport OK - Kodi replied"
    invoke-static {{v4}}, {CTRL}->showTransportResult(Ljava/lang/String;)V
    return-void

    :bad_reply
    invoke-virtual {{v3}}, Ljava/net/Socket;->close()V
    const-string v4, "Infinity transport reached Kodi, unexpected reply"
    invoke-static {{v4}}, {CTRL}->showTransportResult(Ljava/lang/String;)V
    return-void

    :try_end
    .catch Ljava/lang/Throwable; {{:try_start .. :try_end}} :caught

    :caught
    if-eqz v2, :fail
    :close_try
    invoke-virtual {{v2}}, Ljava/net/Socket;->close()V
    :close_end
    .catch Ljava/lang/Throwable; {{:close_try .. :close_end}} :fail

    :fail
    const-string v4, "Infinity transport FAIL - Kodi did not reply"
    invoke-static {{v4}}, {CTRL}->showTransportResult(Ljava/lang/String;)V
    return-void
.end method
'''

toast = f'''.class public final {TOAST}
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "InfinityController.java"

.field private final activity:Landroid/app/Activity;
.field private final message:Ljava/lang/String;

.method public constructor <init>(Landroid/app/Activity;Ljava/lang/String;)V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, {TOAST}->activity:Landroid/app/Activity;
    iput-object p2, p0, {TOAST}->message:Ljava/lang/String;
    return-void
.end method

.method public run()V
    .locals 3
    iget-object v0, p0, {TOAST}->activity:Landroid/app/Activity;
    iget-object v1, p0, {TOAST}->message:Ljava/lang/String;
    const/4 v2, 0x1
    invoke-static {{v0, v1, v2}}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {{v0}}, Landroid/widget/Toast;->show()V
    return-void
.end method
'''

(PKG_DIR / 'InfinityController.smali').write_text(controller)
(PKG_DIR / 'InfinityController$TransportProbeRunnable.smali').write_text(probe)
(PKG_DIR / 'InfinityController$ToastRunnable.smali').write_text(toast)

# Keep 5.3.3's Main.init hook and manifest PiP declaration untouched.
if f'{CTRL}->init(Landroid/app/Activity;)V' not in main_text:
    raise SystemExit('5.3.3 brain init hook missing; refusing to widen scope')

manifest = (ROOT / 'AndroidManifest.xml').read_text()
if 'android:supportsPictureInPicture="true"' not in manifest:
    raise SystemExit('5.3.3 PiP manifest capability missing; refusing to widen scope')

print('5.3.4 transport probe applied')
print('One delayed JSON-RPC Ping, brace-counted response, one toast, no loop, no PiP action')
