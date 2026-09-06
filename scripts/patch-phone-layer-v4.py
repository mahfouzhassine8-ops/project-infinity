from pathlib import Path
import re

root = Path('/tmp/decoded')
man = root / 'AndroidManifest.xml'
s = man.read_text()
pat = r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m = re.search(pat, s)
if not m:
    raise SystemExit('Main activity not found')
tag = m.group(0)
for key, value in (
    ('android:supportsPictureInPicture', 'true'),
    ('android:resizeableActivity', 'true'),
):
    if key + '=' in tag:
        tag = re.sub(re.escape(key) + r'="[^"]*"', key + '="' + value + '"', tag)
    else:
        tag = tag[:-1] + ' ' + key + '="' + value + '">'
s = s[:m.start()] + tag + s[m.end():]
man.write_text(s)

bridge = root / 'smali/com/projectinfinity/kodi/InfinityPhoneBridge.smali'
bridge.parent.mkdir(parents=True, exist_ok=True)
bridge.write_text(r'''.class public final Lcom/projectinfinity/kodi/InfinityPhoneBridge;
.super Ljava/lang/Object;
.source "InfinityPhoneBridge.java"

.method private constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    .locals 4
    if-eqz p0, :no
    const-string v0, "{\"jsonrpc\":\"2.0\",\"method\":\"Player.GetActivePlayers\",\"id\":1}"
    invoke-virtual {p0, v0}, Lcom/projectinfinity/kodi/XBMCJsonRPC;->request_string(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :no
    const-string v1, "video"
    invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :no
    const/4 v3, 0x1
    return v3
    :no
    const/4 v3, 0x0
    return v3
.end method

.method public static configureAutoPip(Landroid/app/Activity;)V
    .locals 4
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1f
    if-lt v0, v1, :done

    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {v0}, Landroid/app/PictureInPictureParams$Builder;-><init>()V

    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0

    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {v1, v2, v3}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0

    invoke-virtual {v0}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setPictureInPictureParams(Landroid/app/PictureInPictureParams;)V

    :done
    return-void
.end method

.method public static enterPipOnUserLeave(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    .locals 4
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :skip

    invoke-virtual {p0}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :skip

    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    move-result v0
    if-eqz v0, :skip

    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {v0}, Landroid/app/PictureInPictureParams$Builder;-><init>()V

    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {v1, v2, v3}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0

    invoke-virtual {v0}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v1
    invoke-virtual {p0, v1}, Landroid/app/Activity;->enterPictureInPictureMode(Landroid/app/PictureInPictureParams;)Z
    move-result v2
    return v2

    :skip
    const/4 v2, 0x0
    return v2
.end method
''')

# Find Main.smali from the successfully decoded Stable 2 base.
p = root / 'smali/com/projectinfinity/kodi/Main.smali'
if not p.exists():
    hits = [x for d in root.glob('smali*') for x in d.rglob('Main.smali') if 'projectinfinity/kodi' in str(x)]
    if not hits:
        raise SystemExit('Main.smali not found')
    p = hits[0]
t = p.read_text()

# Android 12+ native auto-enter PiP. Configure it whenever Main resumes.
if 'InfinityPhoneBridge;->configureAutoPip' not in t:
    mm = re.search(r'(?ms)^\.method (?:public|protected) onResume\(\)V\n(.*?)^\.end method', t)
    if not mm:
        raise SystemExit('onResume not found')
    body = mm.group(0)
    marker = '    invoke-super {p0}, Landroid/app/NativeActivity;->onResume()V\n'
    if marker not in body:
        raise SystemExit('onResume super marker not found')
    add = '\n    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->configureAutoPip(Landroid/app/Activity;)V\n'
    newbody = body.replace(marker, marker + add, 1)
    t = t[:mm.start()] + newbody + t[mm.end():]

# Keep the explicit Home/Recents fallback.
if '.method public onUserLeaveHint()V' not in t:
    hook = r'''
.method public onUserLeaveHint()V
    .locals 1

    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->enterPipOnUserLeave(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z

    return-void
.end method

'''
    insert_at = t.rfind('.method')
    if insert_at < 0:
        raise SystemExit('Could not find insertion point in Main.smali')
    t = t[:insert_at] + hook + t[insert_at:]

# PiP v4 surface fix: when Android changes into/out of PiP, force Kodi's SurfaceView
# back to MATCH_PARENT and request a fresh layout/draw against the new activity size.
if 'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V' not in t:
    pip_changed = r'''
.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 3

    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;
    if-eqz v0, :pip_resize_done

    invoke-virtual {v0}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;
    move-result-object v1
    if-eqz v1, :pip_request_only

    const/4 v2, -0x1
    iput v2, v1, Landroid/view/ViewGroup$LayoutParams;->width:I
    iput v2, v1, Landroid/view/ViewGroup$LayoutParams;->height:I
    invoke-virtual {v0, v1}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    :pip_request_only
    invoke-virtual {v0}, Landroid/view/View;->requestLayout()V
    invoke-virtual {v0}, Landroid/view/View;->invalidate()V

    :pip_resize_done
    return-void
.end method

'''
    insert_at = t.rfind('.method')
    t = t[:insert_at] + pip_changed + t[insert_at:]

p.write_text(t)

# Force the SurfaceHolder buffer to follow the SurfaceView's actual PiP size.
# This causes SurfaceHolder.Callback.surfaceChanged() to report the new dimensions
# into Kodi's native _surfaceChanged() path instead of keeping the Fold-sized buffer.
view = None
for d in root.glob('smali*'):
    cand = d / 'com/projectinfinity/kodi/XBMCMainView.smali'
    if cand.exists():
        view = cand
        break
if view is None:
    raise SystemExit('XBMCMainView.smali not found')
vt = view.read_text()
if 'infinityPipSurfaceResize' not in vt:
    resize_method = r'''
.method protected onSizeChanged(IIII)V
    .locals 1

    invoke-super {p0, p1, p2, p3, p4}, Landroid/view/SurfaceView;->onSizeChanged(IIII)V

    if-lez p1, :pip_surface_done
    if-lez p2, :pip_surface_done

    invoke-virtual {p0}, Lcom/projectinfinity/kodi/XBMCMainView;->getHolder()Landroid/view/SurfaceHolder;
    move-result-object v0
    if-eqz v0, :pip_surface_done

    invoke-interface {v0, p1, p2}, Landroid/view/SurfaceHolder;->setFixedSize(II)V

    :pip_surface_done
    return-void
.end method

# infinityPipSurfaceResize
'''
    insert_at = vt.rfind('.method')
    if insert_at < 0:
        raise SystemExit('Could not find XBMCMainView insertion point')
    vt = vt[:insert_at] + resize_method + vt[insert_at:]
    view.write_text(vt)

print('Phone Layer v4 PiP surface resize patch applied')
