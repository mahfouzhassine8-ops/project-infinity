from pathlib import Path
import re

root = Path('/tmp/decoded')

ctrls = list(root.glob('smali*/com/projectinfinity/kodi/InfinityController.smali')) + list(root.glob('smali*/org/xbmc/kodi/InfinityController.smali'))
listeners = list(root.glob('smali*/com/projectinfinity/kodi/InfinityController$ListenerRunnable.smali')) + list(root.glob('smali*/org/xbmc/kodi/InfinityController$ListenerRunnable.smali'))
pipruns = list(root.glob('smali*/com/projectinfinity/kodi/InfinityController$PipRunnable.smali')) + list(root.glob('smali*/org/xbmc/kodi/InfinityController$PipRunnable.smali'))
if not ctrls or not listeners or not pipruns:
    raise SystemExit('Infinity Controller classes not found')

ctrl = ctrls[0]
listener = listeners[0]
piprun = pipruns[0]
ct = ctrl.read_text()
lt = listener.read_text()
pt = piprun.read_text()

m = re.search(r'^\.class[^\n]*\s(L[^;]+;)', ct, re.M)
if not m:
    raise SystemExit('Controller descriptor not found')
CTRL = m.group(1)
PKG = CTRL.rsplit('/', 1)[0]
PIPRUN = f'{PKG}/InfinityController$PipRunnable;'

# Only touch Android PiP params when the playback state actually changes.
new_set = f'''.method public static setVideoPlaying(Z)V
    .locals 3
    sget-boolean v0, {CTRL}->isVideoPlaying:Z
    if-eq v0, p0, :done
    sput-boolean p0, {CTRL}->isVideoPlaying:Z
    sget-object v1, {CTRL}->activity:Landroid/app/Activity;
    if-eqz v1, :done
    new-instance v2, {PIPRUN}
    invoke-direct {{v2, v1, p0}}, {PIPRUN}-><init>(Landroid/app/Activity;Z)V
    invoke-virtual {{v1, v2}}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :done
    return-void
.end method'''
ct, n = re.subn(r'(?ms)^\.method public static setVideoPlaying\(Z\)V\n.*?^\.end method', new_set, ct, count=1)
if n != 1:
    raise SystemExit('setVideoPlaying method replacement failed')

# A Samsung/Activity PiP exception must never be allowed to kill Kodi.
new_apply = f'''.method public static applyAutoPip(Landroid/app/Activity;Z)V
    .locals 2
    :try_start
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
    :try_end
    return-void
    .catch Ljava/lang/Throwable; {{:try_start .. :try_end}} :caught
    :caught
    return-void
.end method'''
ct, n = re.subn(r'(?ms)^\.method public static applyAutoPip\(Landroid/app/Activity;Z\)V\n.*?^\.end method', new_apply, ct, count=1)
if n != 1:
    raise SystemExit('applyAutoPip method replacement failed')
ctrl.write_text(ct)

# Connection failures are normal while Kodi's JSON-RPC server is starting.
# Reset the state silently instead of posting a UI task every reconnect.
old = f'''    :caught\n    const/4 v4, 0x0\n    invoke-static {{v4}}, {CTRL}->setVideoPlaying(Z)V'''
new = f'''    :caught\n    const/4 v4, 0x0\n    sput-boolean v4, {CTRL}->isVideoPlaying:Z'''
if old not in lt:
    raise SystemExit('Listener catch block not found')
lt = lt.replace(old, new, 1)
listener.write_text(lt)

# Last-resort guard on the UI Runnable too. This keeps a platform PiP failure
# from taking down Kodi's main thread.
new_run = f'''.method public run()V
    .locals 2
    :try_start
    iget-object v0, p0, {PIPRUN}->activity:Landroid/app/Activity;
    iget-boolean v1, p0, {PIPRUN}->enabled:Z
    invoke-static {{v0, v1}}, {CTRL}->applyAutoPip(Landroid/app/Activity;Z)V
    :try_end
    return-void
    .catch Ljava/lang/Throwable; {{:try_start .. :try_end}} :caught
    :caught
    return-void
.end method'''
pt, n = re.subn(r'(?ms)^\.method public run\(\)V\n.*?^\.end method', new_run, pt, count=1)
if n != 1:
    raise SystemExit('PipRunnable.run replacement failed')
piprun.write_text(pt)

print('Infinity Controller runtime hardening applied')