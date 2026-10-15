from pathlib import Path
import re

ROOT = Path('/tmp/target')
MAIN = None
for d in ROOT.glob('smali*'):
    p = d / 'com/projectinfinity/kodi/Main.smali'
    if p.exists():
        MAIN = p
        break
if MAIN is None:
    raise SystemExit('Stable2 PiP v3 Main.smali not found')

text = MAIN.read_text()
if '.super Landroid/app/NativeActivity;' not in text:
    raise SystemExit('Unexpected Main superclass')

# The target MUST already contain Stable2 PiP v3's proven callback.
mm = re.search(r'(?ms)^\.method protected onUserLeaveHint\(\)V\n.*?^\.end method', text)
if not mm:
    raise SystemExit('Stable2 PiP v3 onUserLeaveHint missing')
block = mm.group(0)
required = [
    'invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V',
    'const/16 v1, 0x1a',
    'Lcom/projectinfinity/kodi/Main;->enterPictureInPictureMode()Z',
]
for marker in required:
    if marker not in block:
        raise SystemExit(f'Proven PiP callback shape changed: missing {marker}')
if 'InfinityController;->shouldAllowPiP()Z' in block:
    raise SystemExit('Gate already present; refusing duplicate')

# Insert one independent early-return gate AFTER the proven super call.
# Do not depend on, rename, or reuse any Stable2 internal labels.
super_line = '    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V'
insert = '''\n\n    # 5.3.6 brain gate. NO video = leave normally without PiP.\n    invoke-static {}, Lcom/projectinfinity/kodi/InfinityController;->shouldAllowPiP()Z\n    move-result v0\n    if-nez v0, :infinity_pip_continue\n    return-void\n\n    :infinity_pip_continue'''
block = block.replace(super_line, super_line + insert, 1)
text = text[:mm.start()] + block + text[mm.end():]

# Add the same one-time brain init hook used by the tested 5.3.6 donor.
if 'InfinityController;->init(Landroid/app/Activity;)V' not in text:
    om = re.search(r'(?ms)^\.method public onCreate\(Landroid/os/Bundle;\)V\n.*?^\.end method', text)
    if not om:
        raise SystemExit('Main.onCreate missing')
    ob = om.group(0)
    sm = re.search(r'(?m)^\s*invoke-super \{p0, p1\}, Landroid/app/NativeActivity;->onCreate\(Landroid/os/Bundle;\)V\s*$', ob)
    if not sm:
        raise SystemExit('Main.onCreate NativeActivity super call missing')
    init = '\n    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityController;->init(Landroid/app/Activity;)V\n'
    ob = ob[:sm.end()] + init + ob[sm.end():]
    text = text[:om.start()] + ob + text[om.end():]

MAIN.write_text(text)

manifest = (ROOT/'AndroidManifest.xml').read_text()
main_tag = re.search(r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>', manifest)
if not main_tag:
    raise SystemExit('Main manifest tag missing')
tag = main_tag.group(0)
if 'android:supportsPictureInPicture="true"' not in tag:
    raise SystemExit('Stable2 PiP capability missing')
if 'android:resizeableActivity="true"' not in tag:
    raise SystemExit('Stable2 resizeableActivity missing')

print('5.3.7.2 target patched: exact Stable2 PiP body preserved')
print('Only additions to Main: tested brain init + independent early-return brain gate')
