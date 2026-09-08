from pathlib import Path
import re

root = Path('/tmp/target')
manifest = root / 'AndroidManifest.xml'
if not manifest.exists():
    raise SystemExit('AndroidManifest.xml missing')

s = manifest.read_text()
pat = r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m = re.search(pat, s)
if not m:
    raise SystemExit('Infinity Main activity not found')
tag = m.group(0)
for key, value in (
    ('android:supportsPictureInPicture', 'true'),
    ('android:resizeableActivity', 'true'),
):
    if key + '=' in tag:
        tag = re.sub(re.escape(key) + r'="[^"]*"', key + '="' + value + '"', tag)
    else:
        tag = tag[:-1] + f' {key}="{value}">'
s = s[:m.start()] + tag + s[m.end():]
manifest.write_text(s)

main = None
for d in sorted(root.glob('smali*')):
    p = d / 'com/projectinfinity/kodi/Main.smali'
    if p.exists():
        main = p
        break
if main is None:
    raise SystemExit('Main.smali missing')

t = main.read_text()

def drop_method(text: str, signature_fragment: str) -> str:
    pat = re.compile(r'\n\.method[^\n]*' + re.escape(signature_fragment) + r'.*?\n\.end method\n', re.S)
    return pat.sub('\n', text)

# Replace previous experimental callbacks with the bridge-controlled versions.
for sig in (
    'infinityRefreshWindow()V',
    'onConfigurationChanged(Landroid/content/res/Configuration;)V',
    'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V',
    'onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V',
    'onWindowFocusChanged(Z)V',
    'onUserLeaveHint()V',
    '_infinityHasActiveVideo()Z',
    '_infinitySyncDisplayState()V',
):
    t = drop_method(t, sig)

# Native methods are registered by the rebuilt Kodi 21.3 core.
t += r'''
.method public native _infinityHasActiveVideo()Z
.end method

.method public native _infinitySyncDisplayState()V
.end method
'''

bridge = root / 'smali/com/projectinfinity/kodi/InfinityCoreBridge.smali'
bridge.parent.mkdir(parents=True, exist_ok=True)
bridge.write_text(r'''.class public final Lcom/projectinfinity/kodi/InfinityCoreBridge;
.super Ljava/lang/Object;
.source "InfinityCoreBridge.java"

.method private constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static hasActiveVideoPlayer(Lcom/projectinfinity/kodi/Main;)Z
    .locals 1
    if-eqz p0, :no
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinityHasActiveVideo()Z
    move-result v0
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static updateInfinityPictureInPictureParams(Lcom/projectinfinity/kodi/Main;)V
    .locals 5
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :done

    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {v0}, Landroid/app/PictureInPictureParams$Builder;-><init>()V

    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {v1, v2, v3}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0

    # Explicit entry is used so Android never sends the whole idle app to PiP.
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x1f
    if-lt v1, v2, :build
    const/4 v4, 0x0
    invoke-virtual {v0, v4}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0

    :build
    invoke-virtual {v0}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setPictureInPictureParams(Landroid/app/PictureInPictureParams;)V
    :done
    return-void
.end method

.method public static enterInfinityPictureInPicture(Lcom/projectinfinity/kodi/Main;)Z
    .locals 4
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :skip

    invoke-virtual {p0}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :skip

    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->hasActiveVideoPlayer(Lcom/projectinfinity/kodi/Main;)Z
    move-result v0
    if-eqz v0, :skip

    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->updateInfinityPictureInPictureParams(Lcom/projectinfinity/kodi/Main;)V

    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {v0}, Landroid/app/PictureInPictureParams$Builder;-><init>()V
    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {v1, v2, v3}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0
    invoke-virtual {v0}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {p0, v0}, Landroid/app/Activity;->enterPictureInPictureMode(Landroid/app/PictureInPictureParams;)Z
    move-result v1
    return v1

    :skip
    const/4 v1, 0x0
    return v1
.end method

.method public static syncDisplayState(Lcom/projectinfinity/kodi/Main;)V
    .locals 0
    if-eqz p0, :done
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinitySyncDisplayState()V
    :done
    return-void
.end method
''')

# Keep PiP params configured but never auto-enter while idle.
if 'InfinityCoreBridge;->updateInfinityPictureInPictureParams' not in t:
    mm = re.search(r'(?ms)^\.method (?:public|protected) onResume\(\)V\n(.*?)^\.end method', t)
    if not mm:
        raise SystemExit('Main.onResume not found')
    body = mm.group(0)
    marker = '    invoke-super {p0}, Landroid/app/NativeActivity;->onResume()V\n'
    if marker not in body:
        raise SystemExit('Main.onResume super marker not found')
    body = body.replace(marker, marker + '\n    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->updateInfinityPictureInPictureParams(Lcom/projectinfinity/kodi/Main;)V\n', 1)
    t = t[:mm.start()] + body + t[mm.end():]

# Explicit Home/gesture path, gated by native core player state.
t += r'''
.method public onUserLeaveHint()V
    .locals 0
    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->enterInfinityPictureInPicture(Lcom/projectinfinity/kodi/Main;)Z
    return-void
.end method

.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->syncDisplayState(Lcom/projectinfinity/kodi/Main;)V
    return-void
.end method

.method public onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->syncDisplayState(Lcom/projectinfinity/kodi/Main;)V
    return-void
.end method
'''

main.write_text(t)

# Do not carry the crash-associated palette experiment into stabilization.
colors = root / 'assets/addons/skin.estuary/colors'
for name in ('Infinity OLED.xml', 'Infinity Light.xml'):
    p = colors / name
    if p.exists():
        p.unlink()

# Assertions: native-gated PiP and bridge callbacks must be in the packaged app.
check = main.read_text()
for token in (
    '_infinityHasActiveVideo()Z',
    '_infinitySyncDisplayState()V',
    'onUserLeaveHint()V',
    'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V',
):
    if token not in check:
        raise SystemExit(f'missing Main hook token: {token}')

b = bridge.read_text()
for token in ('setAutoEnterEnabled', 'hasActiveVideoPlayer', 'syncDisplayState'):
    if token not in b:
        raise SystemExit(f'missing bridge token: {token}')

print('Infinity 7.1 app hook applied: native-gated PiP + display sync bridge')
