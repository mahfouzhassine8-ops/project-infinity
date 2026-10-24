from pathlib import Path
import re

root = Path('/tmp/target')
manifest = root / 'AndroidManifest.xml'
if not manifest.exists():
    raise SystemExit('AndroidManifest.xml missing')

# -----------------------------------------------------------------------------
# Infinity 7.1 candidate A
# - preserve 7.0 lock/UI identity
# - remove the 7.0 forced view-refresh resize experiment
# - port the proven Standalone-style PiP lifecycle pattern
# - leave libkodi.so untouched in this candidate so PiP can be isolated/tested
# -----------------------------------------------------------------------------

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

# Strip only the 7.0 geometry-refresh experiment. These methods were added above
# Kodi's native window system and are deliberately not carried into 7.1 candidate A.
def drop_method(text: str, signature_fragment: str) -> str:
    pat = re.compile(
        r'\n\.method[^\n]*' + re.escape(signature_fragment) + r'.*?\n\.end method\n',
        re.S,
    )
    return pat.sub('\n', text)

for sig in (
    'infinityRefreshWindow()V',
    'onConfigurationChanged(Landroid/content/res/Configuration;)V',
    'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V',
    'onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V',
    'onWindowFocusChanged(Z)V',
    'onUserLeaveHint()V',
):
    t = drop_method(t, sig)

# Standalone V1 exposed a richer PiP lifecycle (auto-enter + explicit fallback +
# parameter refresh). Keep that logic behind one bridge so later native/core work
# can expose state to it without repeatedly rewriting Main.
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

.method public static hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    .locals 4
    if-eqz p0, :no
    const-string v0, "{\"jsonrpc\":\"2.0\",\"method\":\"Player.GetActivePlayers\",\"id\":71}"
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

.method public static updateInfinityPictureInPictureParams(Landroid/app/Activity;)V
    .locals 4
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

    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x1f
    if-lt v1, v2, :build
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0

    :build
    invoke-virtual {v0}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setPictureInPictureParams(Landroid/app/PictureInPictureParams;)V

    :done
    return-void
.end method

.method public static enterInfinityPictureInPicture(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    .locals 4
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :skip

    invoke-virtual {p0}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :skip

    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    move-result v0
    if-eqz v0, :skip

    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->updateInfinityPictureInPictureParams(Landroid/app/Activity;)V

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
''')

# Configure Android 12+ auto-enter every time Main resumes. This mirrors the
# working Standalone lifecycle shape while retaining an explicit user-leave fallback.
if 'InfinityCoreBridge;->updateInfinityPictureInPictureParams' not in t:
    mm = re.search(r'(?ms)^\.method (?:public|protected) onResume\(\)V\n(.*?)^\.end method', t)
    if not mm:
        raise SystemExit('Main.onResume not found')
    body = mm.group(0)
    marker = '    invoke-super {p0}, Landroid/app/NativeActivity;->onResume()V\n'
    if marker not in body:
        raise SystemExit('Main.onResume super marker not found')
    body = body.replace(
        marker,
        marker + '\n    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->updateInfinityPictureInPictureParams(Landroid/app/Activity;)V\n',
        1,
    )
    t = t[:mm.start()] + body + t[mm.end():]

hook = r'''
.method public onUserLeaveHint()V
    .locals 1

    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->enterInfinityPictureInPicture(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z

    return-void
.end method
'''
t += '\n' + hook + '\n'
main.write_text(t)

# The 7.0 experimental palettes are not part of the 7.1 stabilization candidate.
# Keep stock Estuary/default dark behavior; remove only the crash-associated custom schemes.
colors = root / 'assets/addons/skin.estuary/colors'
for name in ('Infinity OLED.xml', 'Infinity Light.xml'):
    p = colors / name
    if p.exists():
        p.unlink()

print('Infinity 7.1 candidate A: 7.0 lock + Standalone-style PiP bridge applied')
print('7.0 forced resize-refresh experiment removed')
print('crash-associated Infinity OLED/Light schemes disabled for this candidate')
print('native libkodi.so intentionally untouched in candidate A')
