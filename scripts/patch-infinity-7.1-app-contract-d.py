from pathlib import Path
import re

root = Path('/tmp/target')
main = None
for d in sorted(root.glob('smali*')):
    p = d / 'com/projectinfinity/kodi/Main.smali'
    if p.exists():
        main = p
        break
if main is None:
    raise SystemExit('Main.smali missing')

t = main.read_text()

# Candidate C must already have installed the two original native methods.
if '_infinityHasActiveVideo()Z' not in t or '_infinitySyncDisplayState()V' not in t:
    raise SystemExit('Candidate C app bridge must be applied first')

# Remove stale Candidate D methods if the patch is re-run.
def drop_method(text: str, signature_fragment: str) -> str:
    pat = re.compile(r'\n\.method[^\n]*' + re.escape(signature_fragment) + r'.*?\n\.end method\n', re.S)
    return pat.sub('\n', text)

for sig in (
    '_infinitySystemThemeMode()I',
    '_infinityWindowWidth()I',
    '_infinityWindowHeight()I',
    '_infinityBridgeVersion()I',
    'onConfigurationChanged(Landroid/content/res/Configuration;)V',
):
    t = drop_method(t, sig)

# These are stable native facts/actions exposed by the rebuilt 21.3 core.
t += r'''
.method public native _infinitySystemThemeMode()I
.end method

.method public native _infinityWindowWidth()I
.end method

.method public native _infinityWindowHeight()I
.end method

.method public native _infinityBridgeVersion()I
.end method
'''

bridge = root / 'smali/com/projectinfinity/kodi/InfinityCoreBridge.smali'
if not bridge.exists():
    raise SystemExit('InfinityCoreBridge.smali missing')
b = bridge.read_text()

# Append stable query wrappers only once. 0=unknown, 1=light, 2=dark.
if 'getSystemThemeMode(Lcom/projectinfinity/kodi/Main;)I' not in b:
    b += r'''
.method public static getSystemThemeMode(Lcom/projectinfinity/kodi/Main;)I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinitySystemThemeMode()I
    move-result v0
    return v0
    :unknown
    const/4 v0, 0x0
    return v0
.end method

.method public static getNativeWindowWidth(Lcom/projectinfinity/kodi/Main;)I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinityWindowWidth()I
    move-result v0
    return v0
    :unknown
    const/4 v0, -0x1
    return v0
.end method

.method public static getNativeWindowHeight(Lcom/projectinfinity/kodi/Main;)I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinityWindowHeight()I
    move-result v0
    return v0
    :unknown
    const/4 v0, -0x1
    return v0
.end method

.method public static getBridgeVersion(Lcom/projectinfinity/kodi/Main;)I
    .locals 1
    if-eqz p0, :unknown
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->_infinityBridgeVersion()I
    move-result v0
    return v0
    :unknown
    const/4 v0, 0x0
    return v0
.end method
'''
bridge.write_text(b)

# Configuration changes are now one coordinated event: first let NativeActivity/Kodi
# receive the Configuration, then ask the stable bridge to synchronize native display
# state. System theme consumers can query getSystemThemeMode() from the same bridge.
t += r'''
.method public onConfigurationChanged(Landroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onConfigurationChanged(Landroid/content/res/Configuration;)V
    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityCoreBridge;->syncDisplayState(Lcom/projectinfinity/kodi/Main;)V
    return-void
.end method
'''
main.write_text(t)

# Do not resurrect the old crash-associated palettes. Candidate D exposes the
# native System theme fact now; safe Light/Dark presentation can be changed above
# the core through this contract without rebuilding libkodi again.
colors = root / 'assets/addons/skin.estuary/colors'
for name in ('Infinity OLED.xml', 'Infinity Light.xml'):
    p = colors / name
    if p.exists():
        p.unlink()

for token in (
    '_infinitySystemThemeMode()I',
    '_infinityWindowWidth()I',
    '_infinityWindowHeight()I',
    '_infinityBridgeVersion()I',
    'onConfigurationChanged(Landroid/content/res/Configuration;)V',
):
    if token not in main.read_text():
        raise SystemExit(f'Main missing Candidate D token: {token}')

for token in ('getSystemThemeMode', 'getNativeWindowWidth', 'getNativeWindowHeight', 'getBridgeVersion'):
    if token not in bridge.read_text():
        raise SystemExit(f'bridge missing Candidate D token: {token}')

print('Infinity Candidate D app contract installed: core theme/window queries + configuration sync')
