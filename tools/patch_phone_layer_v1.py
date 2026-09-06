from pathlib import Path
import re

root = Path('/tmp/decoded')
manifest = root / 'AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')

pat = r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m = re.search(pat, s)
if not m:
    raise SystemExit('Main manifest activity not found')

tag = m.group(0)
if 'android:supportsPictureInPicture=' not in tag:
    tag = tag[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in tag:
    tag = tag[:-1] + ' android:resizeableActivity="true">'

cm = re.search(r'android:configChanges="([^"]*)"', tag)
wanted = ['orientation','screenSize','smallestScreenSize','screenLayout','uiMode','keyboard','keyboardHidden','navigation','touchscreen','colorMode']
if cm:
    vals = [x for x in cm.group(1).split('|') if x]
    for w in wanted:
        if w not in vals:
            vals.append(w)
    tag = tag[:cm.start()] + 'android:configChanges="' + '|'.join(vals) + '"' + tag[cm.end():]

s = s[:m.start()] + tag + s[m.end():]
manifest.write_text(s, encoding='utf-8')

bridge = root / 'smali/com/projectinfinity/kodi/InfinityPhoneBridge.smali'
bridge.parent.mkdir(parents=True, exist_ok=True)
bridge.write_text('''.class public final Lcom/projectinfinity/kodi/InfinityPhoneBridge;
.super Ljava/lang/Object;
.source "InfinityPhoneBridge.java"

.method private constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static shouldEnterPip(Landroid/widget/RelativeLayout;)Z
    .locals 2

    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :no

    if-eqz p0, :no
    invoke-virtual {p0}, Landroid/widget/RelativeLayout;->getChildCount()I
    move-result v0
    const/4 v1, 0x1
    if-le v0, v1, :no

    const/4 v0, 0x1
    return v0

    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static enterPip(Landroid/app/Activity;Landroid/widget/RelativeLayout;)Z
    .locals 1

    invoke-static {p1}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->shouldEnterPip(Landroid/widget/RelativeLayout;)Z
    move-result v0
    if-eqz v0, :skip

    invoke-virtual {p0}, Landroid/app/Activity;->enterPictureInPictureMode()Z
    move-result v0
    return v0

    :skip
    const/4 v0, 0x0
    return v0
.end method
''', encoding='utf-8')

main = root / 'smali/com/projectinfinity/kodi/Main.smali'
if not main.exists():
    hits = [x for d in root.glob('smali*') for x in d.rglob('Main.smali') if 'projectinfinity/kodi' in str(x)]
    if not hits:
        raise SystemExit('Main.smali not found')
    main = hits[0]

t = main.read_text(encoding='utf-8')
mm = re.search(r'(?ms)^\.method public onPause\(\)V\n(.*?)^\.end method', t)
if not mm:
    raise SystemExit('Main.onPause not found')
body = mm.group(0)
if 'InfinityPhoneBridge;->enterPip' in body:
    raise SystemExit('Phone bridge already wired')

marker = '    invoke-super {p0}, Landroid/app/NativeActivity;->onPause()V\n'
if marker not in body:
    raise SystemExit('onPause super marker not found')

hook = '''\n    # Infinity Android phone layer: delegate phone-specific PiP behavior.\n    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mVideoLayout:Landroid/widget/RelativeLayout;\n    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/InfinityPhoneBridge;->enterPip(Landroid/app/Activity;Landroid/widget/RelativeLayout;)Z\n\n'''
newbody = body.replace(marker, marker + hook, 1)
t = t[:mm.start()] + newbody + t[mm.end():]
main.write_text(t, encoding='utf-8')
print('Infinity phone layer wired into', main)
