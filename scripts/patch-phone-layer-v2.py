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
if 'android:supportsPictureInPicture=' not in tag:
    tag = tag[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in tag:
    tag = tag[:-1] + ' android:resizeableActivity="true">'
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

.method public static enterPipIfVideo(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    .locals 2
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :skip
    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z
    move-result v0
    if-eqz v0, :skip
    invoke-virtual {p0}, Landroid/app/Activity;->enterPictureInPictureMode()Z
    move-result v0
    return v0
    :skip
    const/4 v0, 0x0
    return v0
.end method
''')

p = root / 'smali/com/projectinfinity/kodi/Main.smali'
if not p.exists():
    hits = [x for d in root.glob('smali*') for x in d.rglob('Main.smali') if 'projectinfinity/kodi' in str(x)]
    if not hits:
        raise SystemExit('Main.smali not found')
    p = hits[0]
t = p.read_text()
mm = re.search(r'(?ms)^\.method public onPause\(\)V\n(.*?)^\.end method', t)
if not mm:
    raise SystemExit('Main.onPause not found')
body = mm.group(0)
marker = '    invoke-super {p0}, Landroid/app/NativeActivity;->onPause()V\n'
if marker not in body:
    raise SystemExit('onPause super marker not found')
hook = '''\n    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;\n    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->enterPipIfVideo(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z\n\n'''
newbody = body.replace(marker, marker + hook, 1)
t = t[:mm.start()] + newbody + t[mm.end():]
p.write_text(t)
print('Phone Layer v2 patched successfully')
