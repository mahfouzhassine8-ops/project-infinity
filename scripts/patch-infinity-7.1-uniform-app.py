from pathlib import Path
import re, shutil

root = Path('/tmp/decoded')
old = Path('/tmp/old')
manifest = root / 'AndroidManifest.xml'
if not manifest.exists():
    raise SystemExit('decoded AndroidManifest.xml missing')

# Find the real Main activity from this exact freshly-built Kodi package.
main = None
for p in sorted(root.glob('smali*/**/Main.smali')):
    try:
        t = p.read_text()
    except Exception:
        continue
    if 'Landroid/app/NativeActivity;' in t:
        main = p
        break
if main is None:
    raise SystemExit('NativeActivity Main.smali not found')

t = main.read_text()
m = re.search(r'^\.class[^\n]* L([^;]+)/Main;$', t, re.M)
if not m:
    raise SystemExit('Main class descriptor not found')
pkg = m.group(1)
main_desc = f'L{pkg}/Main;'
bridge_desc = f'L{pkg}/InfinityCoreBridge;'
print('Uniform app package:', pkg.replace('/', '.'))

# Manifest: preserve the freshly-built package/class wiring; only enable supported capabilities.
s = manifest.read_text()
activity_name = pkg.replace('/', '.') + '.Main'
pat = re.compile(r'<activity\b[^>]*android:name="' + re.escape(activity_name) + r'"[^>]*>')
mm = pat.search(s)
if not mm:
    # Some apktool manifests use a leading-dot class name.
    pat = re.compile(r'<activity\b[^>]*android:name="\.Main"[^>]*>')
    mm = pat.search(s)
if not mm:
    raise SystemExit('Main activity manifest tag not found')
tag = mm.group(0)
for key, value in (('android:supportsPictureInPicture','true'),('android:resizeableActivity','true')):
    if key + '=' in tag:
        tag = re.sub(re.escape(key) + r'="[^"]*"', key + f'="{value}"', tag)
    else:
        tag = tag[:-1] + f' {key}="{value}">'
s = s[:mm.start()] + tag + s[mm.end():]
manifest.write_text(s)

# Remove old copies before installing one uniform callback contract.
def drop_method(text, signature):
    return re.sub(r'\n\.method[^\n]*' + re.escape(signature) + r'.*?\n\.end method\n', '\n', text, flags=re.S)

for sig in (
    'onUserLeaveHint()V',
    'onConfigurationChanged(Landroid/content/res/Configuration;)V',
    'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V',
    'onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V',
    '_infinityHasActiveVideo()Z',
    '_infinitySyncDisplayState()V',
    '_infinitySystemThemeMode()I',
    '_infinityWindowWidth()I',
    '_infinityWindowHeight()I',
    '_infinityBridgeVersion()I',
):
    t = drop_method(t, sig)

t += f'''
.method public native _infinityHasActiveVideo()Z
.end method

.method public native _infinitySyncDisplayState()V
.end method

.method public native _infinitySystemThemeMode()I
.end method

.method public native _infinityWindowWidth()I
.end method

.method public native _infinityWindowHeight()I
.end method

.method public native _infinityBridgeVersion()I
.end method
'''

bridge = main.parent / 'InfinityCoreBridge.smali'
bridge.write_text(f'''.class public final {bridge_desc}
.super Ljava/lang/Object;
.source "InfinityCoreBridge.java"

.method private constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static hasActiveVideoPlayer({main_desc})Z
    .locals 1
    if-eqz p0, :no
    invoke-virtual {{p0}}, {main_desc}->_infinityHasActiveVideo()Z
    move-result v0
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static syncDisplayState({main_desc})V
    .locals 0
    if-eqz p0, :done
    invoke-virtual {{p0}}, {main_desc}->_infinitySyncDisplayState()V
    :done
    return-void
.end method

.method public static getSystemThemeMode({main_desc})I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {{p0}}, {main_desc}->_infinitySystemThemeMode()I
    move-result v0
    return v0
    :unknown
    const/4 v0, 0x0
    return v0
.end method

.method public static getNativeWindowWidth({main_desc})I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {{p0}}, {main_desc}->_infinityWindowWidth()I
    move-result v0
    return v0
    :unknown
    const/4 v0, -0x1
    return v0
.end method

.method public static getNativeWindowHeight({main_desc})I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {{p0}}, {main_desc}->_infinityWindowHeight()I
    move-result v0
    return v0
    :unknown
    const/4 v0, -0x1
    return v0
.end method

.method public static getBridgeVersion({main_desc})I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {{p0}}, {main_desc}->_infinityBridgeVersion()I
    move-result v0
    return v0
    :unknown
    const/4 v0, 0x0
    return v0
.end method

.method public static updateInfinityPictureInPictureParams({main_desc})V
    .locals 5
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :done
    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {{v0}}, Landroid/app/PictureInPictureParams$Builder;-><init>()V
    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {{v1, v2, v3}}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {{v0, v1}}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x1f
    if-lt v1, v2, :build
    const/4 v4, 0x0
    invoke-virtual {{v0, v4}}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0
    :build
    invoke-virtual {{v0}}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v0
    invoke-virtual {{p0, v0}}, Landroid/app/Activity;->setPictureInPictureParams(Landroid/app/PictureInPictureParams;)V
    :done
    return-void
.end method

.method public static enterInfinityPictureInPicture({main_desc})Z
    .locals 4
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :skip
    invoke-virtual {{p0}}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :skip
    invoke-static {{p0}}, {bridge_desc}->hasActiveVideoPlayer({main_desc})Z
    move-result v0
    if-eqz v0, :skip
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
    move-result v1
    return v1
    :skip
    const/4 v1, 0x0
    return v1
.end method
''')

# Configure PiP on resume without auto-entering an idle app.
# Validate the generated bridge method itself; Main receives the call below.
bridge_text = bridge.read_text()
if 'updateInfinityPictureInPictureParams' not in bridge_text:
    raise SystemExit('bridge PiP parameter method missing after generation')
rm = re.search(r'(?ms)^\.method (?:public|protected) onResume\(\)V\n(.*?)^\.end method', t)
if rm:
    body = rm.group(0)
    supercall = re.search(r'^\s*invoke-super \{p0\}[^\n]*->onResume\(\)V\s*$', body, re.M)
    if supercall and f'{bridge_desc}->updateInfinityPictureInPictureParams' not in body:
        insert = supercall.group(0) + f'\n    invoke-static {{p0}}, {bridge_desc}->updateInfinityPictureInPictureParams({main_desc})V'
        body = body[:supercall.start()] + insert + body[supercall.end():]
        t = t[:rm.start()] + body + t[rm.end():]

# One callback map for PiP, Fold/configuration and multi-window.
t += f'''
.method public onUserLeaveHint()V
    .locals 0
    invoke-super {{p0}}, Landroid/app/NativeActivity;->onUserLeaveHint()V
    invoke-static {{p0}}, {bridge_desc}->enterInfinityPictureInPicture({main_desc})Z
    return-void
.end method

.method public onConfigurationChanged(Landroid/content/res/Configuration;)V
    .locals 0
    invoke-super {{p0, p1}}, Landroid/app/NativeActivity;->onConfigurationChanged(Landroid/content/res/Configuration;)V
    invoke-static {{p0}}, {bridge_desc}->syncDisplayState({main_desc})V
    return-void
.end method

.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {{p0, p1, p2}}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-static {{p0}}, {bridge_desc}->syncDisplayState({main_desc})V
    return-void
.end method

.method public onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {{p0, p1, p2}}, Landroid/app/NativeActivity;->onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-static {{p0}}, {bridge_desc}->syncDisplayState({main_desc})V
    return-void
.end method
'''
main.write_text(t)

# Preserve custom Infinity Python add-ons from 7.0, but never copy native binaries or Kodi system add-ons.
old_addons = old / 'assets/addons'
new_addons = root / 'assets/addons'
copied = []
if old_addons.exists() and new_addons.exists():
    for d in old_addons.iterdir():
        if not d.is_dir() or d.name == 'skin.estuary':
            continue
        addon_xml = d / 'addon.xml'
        probe = d.name.lower()
        if addon_xml.exists():
            try:
                probe += ' ' + addon_xml.read_text(errors='ignore').lower()
            except Exception:
                pass
        if 'infinity' not in probe:
            continue
        if any(p.suffix.lower() in {'.so','.dll','.dylib'} for p in d.rglob('*') if p.is_file()):
            print('Skipping native-bearing old addon', d.name)
            continue
        dst = new_addons / d.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(d, dst)
        copied.append(d.name)
print('Copied Infinity upper-layer addons:', copied)

# Estuary presentation: OLED + Light palettes, video lock, native resume wording.
skin = root / 'assets/addons/skin.estuary'
if not skin.exists():
    raise SystemExit('Estuary skin missing')
colors = skin / 'colors'
colors.mkdir(parents=True, exist_ok=True)
(colors / 'Infinity OLED.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<colors><color name="black">FF000000</color><color name="background">FF000000</color><color name="background100">FF000000</color><color name="white">FFFFFFFF</color><color name="grey">FFB8B8B8</color><color name="selected">FFFFFFFF</color></colors>\n''')
(colors / 'Infinity Light.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<colors><color name="black">FF111111</color><color name="background">FFF4F4F4</color><color name="background100">FFFFFFFF</color><color name="white">FF111111</color><color name="grey">FF555555</color><color name="selected">FF000000</color></colors>\n''')

osd = skin / 'xml/VideoOSD.xml'
if osd.exists():
    x = osd.read_text()
    if 'id="7999"' not in x:
        marker = '<control type="radiobutton" id="804">'
        lock = '''<control type="radiobutton" id="7999"><include content="OSDButton"><param name="texture" value="osd/fullscreen/buttons/infinity-lock.png"/></include><label>Lock screen</label><onclick>Dialog.Close(VideoOSD)</onclick><onclick>ActivateWindow(1199)</onclick><visible>Player.HasVideo</visible></control>'''
        if marker not in x:
            raise SystemExit('VideoOSD lock insertion point missing')
        osd.write_text(x.replace(marker, lock + marker, 1))

(skin / 'xml/Custom_1199_InfinityVideoLock.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>\n<window type="dialog" id="1199"><defaultcontrol always="true">9900</defaultcontrol><controls><control type="button" id="9900"><left>0</left><top>0</top><width>100%</width><height>100%</height><texturefocus colordiffuse="00FFFFFF">white.png</texturefocus><texturenofocus colordiffuse="00FFFFFF">white.png</texturenofocus><label></label><onclick>SetProperty(InfinityUnlockVisible,true)</onclick></control><control type="button" id="9901"><left>38</left><top>25</top><width>80</width><height>80</height><texturefocus>osd/fullscreen/buttons/infinity-lock.png</texturefocus><texturenofocus>osd/fullscreen/buttons/infinity-lock.png</texturenofocus><label></label><visible>!String.IsEmpty(Window.Property(InfinityUnlockVisible))</visible><onclick>Dialog.Close(1199)</onclick></control></controls></window>\n''')

# Kodi owns resume bookmarks; retain the native mechanism and normalize the visible choice.
for p in (root / 'assets/addons').rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.xml','.po'}:
        continue
    try:
        q = p.read_text(encoding='utf-8')
    except Exception:
        continue
    nq = q
    for a,b in [('Start from beginning','Start Over'),('Start from Beginning','Start Over'),('Start from the beginning','Start Over'),('Play from beginning','Start Over'),('Play from Beginning','Start Over')]:
        nq = nq.replace(a,b)
    if nq != q:
        p.write_text(nq, encoding='utf-8')

# Visible Infinity branding only; preserve the matched package/class identifiers.
for p in root.glob('res/values*/strings.xml'):
    q = p.read_text(errors='ignore')
    nq = re.sub(r'(<string\s+name="app_name"[^>]*>).*?(</string>)', r'\1Infinity\2', q, flags=re.S)
    if nq != q:
        p.write_text(nq)
old_sentence = 'Kodi requires access to your device media and files to function. Please allow this via the following dialogue box or Kodi will exit.'
new_sentence = 'Infinity requires access to your device media and files to function. Please allow this via the following dialogue box or Infinity will exit.'
for p in root.glob('smali*/**/*.smali'):
    q = p.read_text(errors='ignore')
    if old_sentence in q or 'Starting Kodi...' in q:
        p.write_text(q.replace(old_sentence,new_sentence).replace('Starting Kodi...','Starting Infinity...'))

# Final structural assertions.
final = main.read_text()
for token in ('_infinityHasActiveVideo()Z','_infinitySyncDisplayState()V','_infinitySystemThemeMode()I','_infinityWindowWidth()I','_infinityWindowHeight()I','_infinityBridgeVersion()I','onConfigurationChanged(Landroid/content/res/Configuration;)V','onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V','onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V','onUserLeaveHint()V'):
    if token not in final:
        raise SystemExit('missing final token: ' + token)
if final.count('.method public onConfigurationChanged(Landroid/content/res/Configuration;)V') != 1:
    raise SystemExit('duplicate configuration callback')
if final.count('.method public onUserLeaveHint()V') != 1:
    raise SystemExit('duplicate leave callback')
print('Uniform Infinity 7.1 upper layer mapped onto matched Kodi 21.3 package')