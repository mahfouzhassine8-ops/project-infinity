from pathlib import Path
import re

root = Path('/tmp/decoded')
manifest = root / 'AndroidManifest.xml'
s = manifest.read_text()

# Find Infinity main activity and make it PiP/multi-window capable without touching libkodi.so.
pat = r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m = re.search(pat, s)
if not m:
    raise SystemExit('Main activity not found')
tag = m.group(0)
attrs = {
    'android:supportsPictureInPicture': 'true',
    'android:resizeableActivity': 'true',
    'android:launchMode': 'singleTask',
    'android:configChanges': 'density|fontScale|keyboard|keyboardHidden|layoutDirection|locale|mcc|mnc|navigation|orientation|screenLayout|screenSize|smallestScreenSize|uiMode',
}
for key, value in attrs.items():
    if key + '=' in tag:
        tag = re.sub(re.escape(key) + r'="[^"]*"', key + '="' + value + '"', tag)
    else:
        tag = tag[:-1] + f' {key}="{value}">'
s = s[:m.start()] + tag + s[m.end():]
manifest.write_text(s)

# Reuse Stable 2's built-in XBMCJsonRPC wrapper for playback gating.
bridge = root / 'smali/com/projectinfinity/kodi/InfinityPipAndroidOnly.smali'
bridge.parent.mkdir(parents=True, exist_ok=True)
bridge.write_text(r'''.class public final Lcom/projectinfinity/kodi/InfinityPipAndroidOnly;
.super Ljava/lang/Object;

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

.method public static enterPipIfVideo(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    .locals 4
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :skip
    invoke-virtual {p0}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :skip
    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityPipAndroidOnly;->hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
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

# Locate Main.smali.
main = None
for d in root.glob('smali*'):
    cand = d / 'com/projectinfinity/kodi/Main.smali'
    if cand.exists():
        main = cand
        break
if main is None:
    raise SystemExit('Main.smali not found')
t = main.read_text()

# Remove any old unconditional auto-PiP call if present.
t = re.sub(r'\n\s*invoke-static \{p0\}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->configureAutoPip\(Landroid/app/Activity;\)V\n', '\n', t)

# Replace existing onUserLeaveHint with explicit video-gated PiP, or add it.
method_pat = r'(?ms)^\.method public onUserLeaveHint\(\)V\n.*?^\.end method\n?'
new_leave = r'''.method public onUserLeaveHint()V
    .locals 1

    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityPipAndroidOnly;->enterPipIfVideo(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    return-void
.end method

'''
if re.search(method_pat, t):
    t = re.sub(method_pat, new_leave, t, count=1)
else:
    insert_at = t.rfind('.method')
    t = t[:insert_at] + new_leave + t[insert_at:]

# Replace any existing PiP mode callback with the Android-only surface-buffer unlock.
pip_pat = r'(?ms)^\.method public onPictureInPictureModeChanged\(ZLandroid/content/res/Configuration;\)V\n.*?^\.end method\n?'
new_pip = r'''.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 2

    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;
    if-eqz v0, :done
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/XBMCMainView;->getHolder()Landroid/view/SurfaceHolder;
    move-result-object v1
    if-eqz v1, :done

    # Gemini Android-only fix: drop any stale fullscreen buffer lock when entering PiP.
    if-eqz p1, :restore_layout
    invoke-interface {v1}, Landroid/view/SurfaceHolder;->setSizeFromLayout()V
    invoke-virtual {v0}, Landroid/view/View;->requestLayout()V
    invoke-virtual {v0}, Landroid/view/View;->invalidate()V
    goto :done

    :restore_layout
    # On exit, keep layout-driven sizing so the current Fold panel/window decides the size.
    invoke-interface {v1}, Landroid/view/SurfaceHolder;->setSizeFromLayout()V
    invoke-virtual {v0}, Landroid/view/View;->requestLayout()V
    invoke-virtual {v0}, Landroid/view/View;->invalidate()V

    :done
    return-void
.end method

'''
if re.search(pip_pat, t):
    t = re.sub(pip_pat, new_pip, t, count=1)
else:
    insert_at = t.rfind('.method')
    t = t[:insert_at] + new_pip + t[insert_at:]
main.write_text(t)

# IMPORTANT: do NOT add XBMCMainView.onSizeChanged()->setFixedSize().
# That is the stale fullscreen-buffer behavior this experiment is trying to remove.
print('Applied Android-only PiP v5.5: video gate + 16:9 + SurfaceHolder.setSizeFromLayout; libkodi untouched')
