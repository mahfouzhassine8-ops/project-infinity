from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# 5.3.7.1 = TESTED 5.3.6 BRAIN + PROVEN STABLE2 PIP v3 TRIGGER
# Exact proven Stable2 PiP pattern:
#   protected onUserLeaveHint()
#   invoke-super NativeActivity
#   SDK >= 26
#   invoke Main.enterPictureInPictureMode()
# Only addition: brain gate before the proven PiP call.
# No listener changes, no surface changes, no native changes.

main_candidates=[]
for smali_root in ROOT.glob('smali*'):
    main_candidates.extend(smali_root.rglob('Main.smali'))
main_candidates=[p for p in main_candidates if 'projectinfinity/kodi' in str(p).replace('\\','/')]
if not main_candidates:
    raise SystemExit('Main.smali not found')
MAIN=main_candidates[0]
main_text=MAIN.read_text()

cm=re.search(r'^\.class[^\n]*\s(L[^;]+;)', main_text, re.M)
if not cm:
    raise SystemExit('Could not determine Main descriptor')
MAIN_DESC=cm.group(1)
PKG_DESC=MAIN_DESC.rsplit('/',1)[0]
CTRL=f'{PKG_DESC}/InfinityController;'

# Must be the exact Main class shape used by the proven Stable2 PiP v3 recipe.
if '.super Landroid/app/NativeActivity;' not in main_text:
    raise SystemExit('Main no longer extends NativeActivity; refusing to apply Stable2 PiP recipe')

ctrl_path=MAIN.parent/'InfinityController.smali'
listener_path=MAIN.parent/'InfinityController$KodiListenerRunnable.smali'
if not ctrl_path.exists() or not listener_path.exists():
    raise SystemExit('5.3.6 brain/listener missing')
ctrl_text=ctrl_path.read_text()
listener_text=listener_path.read_text()
if '.method public static shouldAllowPiP()Z' not in ctrl_text:
    raise SystemExit('Brain PiP gate missing')
if 'Player.OnAVStart' not in listener_text or 'Player.OnStop' not in listener_text:
    raise SystemExit('5.3.6 persistent listener missing')

# 5.3.6 should not already contain any PiP leave callback.
if re.search(r'^\.method[^\n]*onUserLeaveHint\(\)V', main_text, re.M):
    raise SystemExit('Existing onUserLeaveHint found; refusing duplicate')

# This is Stable2 PiP v3's proven callback, with ONE gate inserted.
hook=f'''
.method protected onUserLeaveHint()V
    .locals 2

    invoke-super {{p0}}, Landroid/app/NativeActivity;->onUserLeaveHint()V

    # Infinity brain gate: no confirmed video = preserve fullscreen exit, no PiP.
    invoke-static {{}}, {CTRL}->shouldAllowPiP()Z
    move-result v0
    if-eqz v0, :pip_done

    # Proven Stable2 PiP v3 path begins here, unchanged.
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :pip_done

    invoke-virtual {{p0}}, {MAIN_DESC}->enterPictureInPictureMode()Z

    :pip_done
    return-void
.end method
'''

MAIN.write_text(main_text.rstrip()+'\n\n'+hook.strip()+'\n')

manifest_path=ROOT/'AndroidManifest.xml'
manifest=manifest_path.read_text()
pat=r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m=re.search(pat, manifest)
if not m:
    raise SystemExit('Main activity not found in manifest')
tag=m.group(0)
if 'android:supportsPictureInPicture="true"' not in tag:
    raise SystemExit('5.3.6 Main PiP capability missing')

print('5.3.7.1 applied: exact Stable2 PiP v3 trigger + 5.3.6 brain gate')
print('protected callback; NativeActivity super; Main PiP call; no other behavior changed')
