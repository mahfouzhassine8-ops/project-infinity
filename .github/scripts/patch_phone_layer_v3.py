from pathlib import Path
import re

root = Path('/tmp/decoded')
manifest = root / 'AndroidManifest.xml'
text = manifest.read_text()

pat = r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m = re.search(pat, text)
if not m:
    raise SystemExit('Main activity not found')
tag = m.group(0)
if 'android:supportsPictureInPicture=' not in tag:
    tag = tag[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in tag:
    tag = tag[:-1] + ' android:resizeableActivity="true">'
text = text[:m.start()] + tag + text[m.end():]
manifest.write_text(text)

# Phone bridge: ask Kodi itself whether an active VIDEO player exists.
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

main = root / 'smali/com/projectinfinity/kodi/Main.smali'
if not main.exists():
    hits = [x for d in root.glob('smali*') for x in d.rglob('Main.smali') if 'projectinfinity/kodi' in str(x)]
    if not hits:
        raise SystemExit('Main.smali not found')
    main = hits[0]

t = main.read_text()

# VLC-style trigger: PiP is requested specifically when Android says the USER is leaving
# (Home/app switch), not from generic onPause().
if '.method public onUserLeaveHint()V' in t:
    mm = re.search(r'(?ms)^\.method public onUserLeaveHint\(\)V\n.*?^\.end method\n?', t)
    if not mm:
        raise SystemExit('Could not parse existing onUserLeaveHint')
    t = t[:mm.start()] + t[mm.end():]

method = r'''
.method public onUserLeaveHint()V
    .locals 1

    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V

    # Infinity Phone Layer v3: VLC-style Home/app-switch trigger.
    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mJsonRPC:Lcom/projectinfinity/kodi/XBMCJsonRPC;
    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->enterPipIfVideo(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z

    return-void
.end method
'''

t = t.rstrip() + '\n' + method
main.write_text(t)
print('Phone Layer v3 wired into', main)
