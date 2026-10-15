from pathlib import Path
import re

ROOT = Path('/tmp/target')
MAIN = None
CTRL = None
PKGDIR = None
for d in ROOT.glob('smali*'):
    p = d / 'com/projectinfinity/kodi/Main.smali'
    c = d / 'com/projectinfinity/kodi/InfinityController.smali'
    if p.exists() and c.exists():
        MAIN = p
        CTRL = c
        PKGDIR = p.parent
        break
if MAIN is None or CTRL is None:
    raise SystemExit('6.0 Main/InfinityController not found')

main = MAIN.read_text()
ctrl = CTRL.read_text()

# Preconditions: preserve the known-good 6.0 brain and PiP capability.
for marker in [
    '.field private static activity:Landroid/app/Activity;',
    '.field public static volatile isVideoPlaying:Z',
    '.method public static setVideoPlaying(ZLjava/lang/String;)V',
    '.method public static shouldAllowPiP()Z',
]:
    if marker not in ctrl:
        raise SystemExit(f'6.0 brain shape changed: missing {marker}')
if 'Lcom/projectinfinity/kodi/Main;->enterPictureInPictureMode()Z' not in main:
    raise SystemExit('6.0 fallback PiP path missing')
if 'android:supportsPictureInPicture="true"' not in (ROOT/'AndroidManifest.xml').read_text():
    raise SystemExit('PiP manifest capability missing')

# 1) Add a small helper that posts PiP-parameter updates to the Activity/UI thread.
if '.method public static updateAutoPiP(Z)V' not in ctrl:
    helper = r'''
.method public static updateAutoPiP(Z)V
    .locals 2

    sget-object v0, Lcom/projectinfinity/kodi/InfinityController;->activity:Landroid/app/Activity;
    if-eqz v0, :infinity_auto_pip_done

    new-instance v1, Lcom/projectinfinity/kodi/InfinityController$AutoPiPRunnable;
    invoke-direct {v1, p0}, Lcom/projectinfinity/kodi/InfinityController$AutoPiPRunnable;-><init>(Z)V
    invoke-virtual {v0, v1}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V

    :infinity_auto_pip_done
    return-void
.end method
'''
    # Place before shouldAllowPiP to keep controller organization simple.
    anchor = '.method public static shouldAllowPiP()Z'
    idx = ctrl.find(anchor)
    if idx < 0:
        raise SystemExit('shouldAllowPiP anchor missing')
    ctrl = ctrl[:idx] + helper + '\n' + ctrl[idx:]

# 2) When the proven brain state actually changes, update Android's Auto-PiP permission.
sm = re.search(r'(?ms)^\.method public static setVideoPlaying\(ZLjava/lang/String;\)V\n.*?^\.end method', ctrl)
if not sm:
    raise SystemExit('setVideoPlaying method missing')
block = sm.group(0)
if 'InfinityController;->updateAutoPiP(Z)V' not in block:
    needle = '    sput-boolean p0, Lcom/projectinfinity/kodi/InfinityController;->isVideoPlaying:Z'
    if needle not in block:
        raise SystemExit('setVideoPlaying state write missing')
    block = block.replace(
        needle,
        needle + '\n\n    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityController;->updateAutoPiP(Z)V',
        1,
    )
    ctrl = ctrl[:sm.start()] + block + ctrl[sm.end():]
CTRL.write_text(ctrl)

# 3) New Runnable: Android 12+ uses PictureInPictureParams.setAutoEnterEnabled.
#    Older Android keeps 6.0's existing manually-triggered fallback.
runnable = r'''.class public final Lcom/projectinfinity/kodi/InfinityController$AutoPiPRunnable;
.super Ljava/lang/Object;
.source "InfinityController.java"

.implements Ljava/lang/Runnable;

.field private final enabled:Z

.method public constructor <init>(Z)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-boolean p1, p0, Lcom/projectinfinity/kodi/InfinityController$AutoPiPRunnable;->enabled:Z
    return-void
.end method

.method public run()V
    .locals 4

    :try_start_0
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1f
    if-lt v0, v1, :infinity_auto_pip_done

    sget-object v0, Lcom/projectinfinity/kodi/InfinityController;->activity:Landroid/app/Activity;
    if-eqz v0, :infinity_auto_pip_done

    new-instance v1, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {v1}, Landroid/app/PictureInPictureParams$Builder;-><init>()V

    iget-boolean v2, p0, Lcom/projectinfinity/kodi/InfinityController$AutoPiPRunnable;->enabled:Z
    invoke-virtual {v1, v2}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v1

    invoke-virtual {v1}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/app/Activity;->setPictureInPictureParams(Landroid/app/PictureInPictureParams;)V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    :infinity_auto_pip_done
    return-void
.end method
'''
(PKGDIR / 'InfinityController$AutoPiPRunnable.smali').write_text(runnable)

# 4) On Android 12+, do not also manually enter PiP from onUserLeaveHint.
#    Auto-enter is now owned by Android; API 26-30 keeps the 6.0 fallback untouched.
mm = re.search(r'(?ms)^\.method protected onUserLeaveHint\(\)V\n.*?^\.end method', main)
if not mm:
    raise SystemExit('6.0 onUserLeaveHint missing')
mb = mm.group(0)
if ':infinity_pre12_fallback' not in mb:
    super_line = '    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V'
    if super_line not in mb:
        raise SystemExit('onUserLeaveHint super call missing')
    gate = r'''

    # Android 12+ Auto-PiP is armed/disarmed by the brain. Avoid a second manual request.
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1f
    if-lt v0, v1, :infinity_pre12_fallback
    return-void

    :infinity_pre12_fallback'''
    mb = mb.replace(super_line, super_line + gate, 1)
    main = main[:mm.start()] + mb + main[mm.end():]
MAIN.write_text(main)

print('Infinity 6.1 patch applied')
print('Protected: 6.0 brain/listener, manifest, native lib, pre-Android-12 fallback')
print('Changed only: brain state -> Android 12+ Auto-PiP params')
