from pathlib import Path
import re, shutil, hashlib

TARGET = Path('/tmp/target')
DONOR = Path('/tmp/donor')

# Find Stable2 Main and donor brain files.
def find_file(root, rel):
    for d in root.glob('smali*'):
        p = d / rel
        if p.exists():
            return p
    return None

main = find_file(TARGET, Path('com/projectinfinity/kodi/Main.smali'))
donor_ctrl = find_file(DONOR, Path('com/projectinfinity/kodi/InfinityController.smali'))
donor_listener = find_file(DONOR, Path('com/projectinfinity/kodi/InfinityController$KodiListenerRunnable.smali'))
if not main or not donor_ctrl or not donor_listener:
    raise SystemExit('Required Stable2/donor files not found')

text = main.read_text()

# PROTECT the exact Stable2 PiP callback. We do not gate it, replace it, or edit it.
mm = re.search(r'(?ms)^\.method protected onUserLeaveHint\(\)V\n.*?^\.end method', text)
if not mm:
    raise SystemExit('Stable2 onUserLeaveHint missing')
protected_pip = mm.group(0)
protected_hash = hashlib.sha256(protected_pip.encode()).hexdigest()
if 'enterPictureInPictureMode()Z' not in protected_pip:
    raise SystemExit('Stable2 proven PiP call missing')
if 'InfinityController;->shouldAllowPiP()Z' in protected_pip:
    raise SystemExit('Stable2 callback unexpectedly already gated')

# Copy the proven 5.3.6 brain classes into the Stable2 body.
target_pkg = main.parent
shutil.copy2(donor_ctrl, target_pkg / donor_ctrl.name)
shutil.copy2(donor_listener, target_pkg / donor_listener.name)

# Start the brain only. This is the ONLY Main change.
if 'InfinityController;->init(Landroid/app/Activity;)V' not in text:
    om = re.search(r'(?ms)^\.method public onCreate\(Landroid/os/Bundle;\)V\n.*?^\.end method', text)
    if not om:
        raise SystemExit('Stable2 Main.onCreate missing')
    ob = om.group(0)
    sm = re.search(r'(?m)^\s*invoke-super \{p0, p1\}, Landroid/app/NativeActivity;->onCreate\(Landroid/os/Bundle;\)V\s*$', ob)
    if not sm:
        raise SystemExit('Stable2 NativeActivity onCreate super call missing')
    init = '\n    invoke-static {p0}, Lcom/projectinfinity/kodi/InfinityController;->init(Landroid/app/Activity;)V\n'
    ob = ob[:sm.end()] + init + ob[sm.end():]
    text = text[:om.start()] + ob + text[om.end():]

main.write_text(text)

# Re-check the exact PiP callback stayed byte-for-byte identical.
new = main.read_text()
mm2 = re.search(r'(?ms)^\.method protected onUserLeaveHint\(\)V\n.*?^\.end method', new)
if not mm2:
    raise SystemExit('PiP callback disappeared')
new_hash = hashlib.sha256(mm2.group(0).encode()).hexdigest()
if new_hash != protected_hash:
    raise SystemExit('REFUSED: Stable2 PiP callback changed')

manifest = (TARGET/'AndroidManifest.xml').read_text()
if 'android:supportsPictureInPicture="true"' not in manifest:
    raise SystemExit('Stable2 PiP manifest capability missing')
if 'android:resizeableActivity="true"' not in manifest:
    raise SystemExit('Stable2 resizeableActivity missing')

print('Infinity 6.3 coexistence patch applied')
print('Stable2 PiP callback: byte-for-byte preserved')
print('Only Main change: start proven 5.3.6 brain in onCreate')
print('Brain observes playback but has ZERO authority over PiP in this checkpoint')
