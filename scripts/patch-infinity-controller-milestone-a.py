from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# Locate the real Kodi Main.smali in the decoded Stable 2 APK.
main_candidates = []
for smali_root in ROOT.glob('smali*'):
    main_candidates.extend(smali_root.rglob('Main.smali'))
main_candidates = [p for p in main_candidates if 'projectinfinity/kodi' in str(p).replace('\\', '/')]
if not main_candidates:
    raise SystemExit('Stable 2 Main.smali not found')
MAIN = main_candidates[0]
SMALI_ROOT = next(p for p in MAIN.parents if p.name.startswith('smali'))
PKG_DIR = MAIN.parent

main_text = MAIN.read_text()
class_match = re.search(r'^\.class[^\n]*\s(L[^;]+;)', main_text, re.M)
if not class_match:
    raise SystemExit('Could not determine Main class descriptor')
MAIN_DESC = class_match.group(1)
PKG_DESC = MAIN_DESC.rsplit('/', 1)[0]
CTRL = f'{PKG_DESC}/InfinityController;'
LISTENER = f'{PKG_DESC}/InfinityController$ListenerRunnable;'
PIPRUN = f'{PKG_DESC}/InfinityController$PipRunnable;'

controller = f'''.class public final {CTRL}
.super Ljava/lang/Object;
.source "InfinityController.java"

.field public static volatile isVideoPlaying:Z
.field private static volatile started:Z
.field private static activity:Landroid/app/Activity;

.method static constructor <clinit>()V
    .locals 1
    const/4 v0, 0x0
    sput-boolean v0, {CTRL}->isVideoPlaying:Z
    sput-boolean v0, {CTRL}->started:Z
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
    const/4 v0, 0x0
    invoke-static {{p0, v0}}, {CTRL}->applyAutoPip(Landroid/app/Activity;Z)V
    sget-boolean v0, {CTRL}->started:Z
    if-nez v0, :done
    const/4 v0, 0x1
    sput-boolean v0, {CTRL}->started:Z
    new-instance v0, Ljava/lang/Thread;
    new-instance v1, {LISTENER}
    invoke-direct {{v1}}, {LISTENER}-><init>()V
    invoke-direct {{v0, v1}}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    const-string v1, "InfinityController"
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

.method public static setVideoPlaying(Z)V
    .locals 2
    sput-boolean p0, {CTRL}->isVideoPlaying:Z
    sget-object v0, {CTRL}->activity:Landroid/app/Activity;
    if-eqz v0, :done
    new-instance v1, {PIPRUN}
    invoke-direct {{v1, v0, p0}}, {PIPRUN}-><init>(Landroid/app/Activity;Z)V
    invoke-virtual {{v0, v1}}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :done
    return-void
.end method

.method public static applyAutoPip(Landroid/app/Activity;Z)V
    .locals 2
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1f
    if-lt v0, v1, :done
    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {{v0}}, Landroid/app/PictureInPictureParams$Builder;-><init>()V
    invoke-virtual {{v0, p1}}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0
    invoke-virtual {{v0}}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {{p0, v0}}, Landroid/app/Activity;->setPictureInPictureParams(Landroid/app/PictureInPictureParams;)V
    :done
    return-void
.end method

.method public static enterPipIfAllowed(Landroid/app/Activity;)Z
    .locals 4
    invoke-static {{}}, {CTRL}->shouldAllowPiP()Z
    move-result v0
    if-eqz v0, :no
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :no
    invoke-virtual {{p0}}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :yes
    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {{v0}}, Landroid/app/PictureInPictureParams$Builder;-><init>()V
    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {{v1, v2, v3}}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {{v0, v1}}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0
    invoke-virtual {{v0}}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {{p0, v0}}, Landroid/app/Activity;->enterPictureInPictureMode(Landroid/app/PictureInPictureParams;)Z
    move-result v0
    return v0
    :yes
    const/4 v0, 0x1
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method
'''

listener = f'''.class public final {LISTENER}
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "InfinityController.java"

.method public constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public run()V
    .locals 8

    :reconnect
    const/4 v0, 0x0
    :try_start
    new-instance v1, Ljava/net/Socket;
    const-string v2, "127.0.0.1"
    const/16 v3, 0x2382
    invoke-direct {{v1, v2, v3}}, Ljava/net/Socket;-><init>(Ljava/lang/String;I)V

    new-instance v2, Ljava/io/BufferedReader;
    new-instance v3, Ljava/io/InputStreamReader;
    invoke-virtual {{v1}}, Ljava/net/Socket;->getInputStream()Ljava/io/InputStream;
    move-result-object v4
    invoke-direct {{v3, v4}}, Ljava/io/InputStreamReader;-><init>(Ljava/io/InputStream;)V
    invoke-direct {{v2, v3}}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V

    :read_loop
    invoke-virtual {{v2}}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v3
    if-eqz v3, :socket_done

    const-string v4, "Player.OnPlay"
    invoke-virtual {{v3, v4}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :check_stop

    const-string v4, "\\\"type\\\":\\\"video\\\""
    invoke-virtual {{v3, v4}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-nez v4, :mark_playing
    const-string v4, "\\\"playerid\\\":1"
    invoke-virtual {{v3, v4}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :read_loop

    :mark_playing
    const/4 v4, 0x1
    invoke-static {{v4}}, {CTRL}->setVideoPlaying(Z)V
    goto :read_loop

    :check_stop
    const-string v4, "Player.OnStop"
    invoke-virtual {{v3, v4}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-nez v4, :mark_stopped
    const-string v4, "Player.OnPause"
    invoke-virtual {{v3, v4}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :read_loop

    :mark_stopped
    const/4 v4, 0x0
    invoke-static {{v4}}, {CTRL}->setVideoPlaying(Z)V
    goto :read_loop

    :socket_done
    invoke-virtual {{v1}}, Ljava/net/Socket;->close()V
    :try_end
    .catch Ljava/lang/Throwable; {{:try_start .. :try_end}} :caught

    :caught
    const/4 v4, 0x0
    invoke-static {{v4}}, {CTRL}->setVideoPlaying(Z)V
    const-wide/16 v5, 0x7d0
    :sleep_try
    invoke-static {{v5, v6}}, Ljava/lang/Thread;->sleep(J)V
    :sleep_end
    .catch Ljava/lang/Throwable; {{:sleep_try .. :sleep_end}} :reconnect
    goto :reconnect
.end method
'''

piprun = f'''.class public final {PIPRUN}
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "InfinityController.java"

.field private final activity:Landroid/app/Activity;
.field private final enabled:Z

.method public constructor <init>(Landroid/app/Activity;Z)V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, {PIPRUN}->activity:Landroid/app/Activity;
    iput-boolean p2, p0, {PIPRUN}->enabled:Z
    return-void
.end method

.method public run()V
    .locals 2
    iget-object v0, p0, {PIPRUN}->activity:Landroid/app/Activity;
    iget-boolean v1, p0, {PIPRUN}->enabled:Z
    invoke-static {{v0, v1}}, {CTRL}->applyAutoPip(Landroid/app/Activity;Z)V
    return-void
.end method
'''

(PKG_DIR / 'InfinityController.smali').write_text(controller)
(PKG_DIR / 'InfinityController$ListenerRunnable.smali').write_text(listener)
(PKG_DIR / 'InfinityController$PipRunnable.smali').write_text(piprun)

if f'{CTRL}->init(Landroid/app/Activity;)V' not in main_text:
    m = re.search(r'(?ms)^\.method[^\n]* onCreate\(Landroid/os/Bundle;\)V\n.*?^\.end method', main_text)
    if not m:
        raise SystemExit('Main.onCreate(Bundle) not found')
    body = m.group(0)
    super_call = re.search(r'(?m)^\s*invoke-super \{p0, p1\}, L[^;]+;->onCreate\(Landroid/os/Bundle;\)V\s*$', body)
    if not super_call:
        raise SystemExit('Main.onCreate super call not found')
    add = f'\n    invoke-static {{p0}}, {CTRL}->init(Landroid/app/Activity;)V\n'
    body = body[:super_call.end()] + add + body[super_call.end():]
    main_text = main_text[:m.start()] + body + main_text[m.end():]

method_match = re.search(r'(?ms)^\.method[^\n]* onUserLeaveHint\(\)V\n.*?^\.end method', main_text)
if method_match:
    body = method_match.group(0)
    if f'{CTRL}->shouldAllowPiP()Z' not in body:
        locals_m = re.search(r'(?m)^\s*\.locals\s+(\d+)\s*$', body)
        if locals_m:
            n = int(locals_m.group(1))
            if n < 1:
                body = body[:locals_m.start()] + '    .locals 1' + body[locals_m.end():]
        else:
            regs_m = re.search(r'(?m)^\s*\.registers\s+(\d+)\s*$', body)
            if not regs_m:
                raise SystemExit('onUserLeaveHint has no .locals/.registers declaration')
            body = body[:regs_m.start()] + f'    .registers {int(regs_m.group(1)) + 1}' + body[regs_m.end():]
        decl_end = body.find('\n') + 1
        gate = f'''    invoke-static {{}}, {CTRL}->shouldAllowPiP()Z\n    move-result v0\n    if-nez v0, :infinity_allow_pip\n    return-void\n    :infinity_allow_pip\n'''
        body = body[:decl_end] + gate + body[decl_end:]
        main_text = main_text[:method_match.start()] + body + main_text[method_match.end():]
else:
    hook = f'''
.method public onUserLeaveHint()V
    .locals 1
    invoke-super {{p0}}, Landroid/app/NativeActivity;->onUserLeaveHint()V
    invoke-static {{p0}}, {CTRL}->enterPipIfAllowed(Landroid/app/Activity;)Z
    move-result v0
    return-void
.end method

'''
    insert_at = main_text.rfind('.method')
    if insert_at < 0:
        raise SystemExit('Could not find Main.smali insertion point')
    main_text = main_text[:insert_at] + hook + main_text[insert_at:]

MAIN.write_text(main_text)

manifest = ROOT / 'AndroidManifest.xml'
ms = manifest.read_text()
activity_pat = r'<activity\b[^>]*android:name="(?:com\.projectinfinity\.kodi|org\.xbmc\.kodi)\.Main"[^>]*>'
am = re.search(activity_pat, ms)
if not am:
    raise SystemExit('Main activity not found in AndroidManifest.xml')
tag = am.group(0)
if 'android:supportsPictureInPicture=' in tag:
    tag = re.sub(r'android:supportsPictureInPicture="[^"]*"', 'android:supportsPictureInPicture="true"', tag)
else:
    tag = tag[:-1] + ' android:supportsPictureInPicture="true">'
ms = ms[:am.start()] + tag + ms[am.end():]
manifest.write_text(ms)

print('Infinity Controller Milestone A brain created and wired')
print(f'Main: {MAIN}')
print(f'Controller: {PKG_DIR / "InfinityController.smali"}')
