from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# 5.3.7 PIP DECISION WIRING
# Base: tested 5.3.6 persistent listener APK.
# Add exactly one Android-side decision hook:
#   Android onUserLeaveHint -> brain shouldAllowPiP -> enterPictureInPictureMode
# No listener changes. No surface/native changes. No polling.

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
PKG_DESC=cm.group(1).rsplit('/',1)[0]
CTRL=f'{PKG_DESC}/InfinityController;'

ctrl_path=MAIN.parent/'InfinityController.smali'
listener_path=MAIN.parent/'InfinityController$KodiListenerRunnable.smali'
if not ctrl_path.exists() or not listener_path.exists():
    raise SystemExit('5.3.6 brain/listener missing; refusing to widen scope')
ctrl_text=ctrl_path.read_text()
listener_text=listener_path.read_text()
if '.method public static shouldAllowPiP()Z' not in ctrl_text:
    raise SystemExit('5.3.6 shouldAllowPiP missing')
if 'Player.OnAVStart' not in listener_text or 'Player.OnStop' not in listener_text:
    raise SystemExit('5.3.6 persistent listener markers missing')

# Refuse to stack another leave hook on top of an unknown implementation.
if '.method public onUserLeaveHint()V' in main_text:
    raise SystemExit('Main already defines onUserLeaveHint; refusing blind overwrite')

hook=f'''
.method public onUserLeaveHint()V
    .locals 2

    # Preserve Android Activity lifecycle behavior first.
    invoke-super {{p0}}, Landroid/app/Activity;->onUserLeaveHint()V

    # Brain owns the decision. If Kodi has not confirmed video playback, do nothing.
    invoke-static {{}}, {CTRL}->shouldAllowPiP()Z
    move-result v0
    if-eqz v0, :done

    # Android PiP API. This method runs on the Activity/UI thread.
    invoke-virtual {{p0}}, Landroid/app/Activity;->enterPictureInPictureMode()Z
    move-result v1

    :done
    return-void
.end method
'''

# Append one Activity callback; do not touch existing methods.
main_text = main_text.rstrip() + '\n\n' + hook.strip() + '\n'
MAIN.write_text(main_text)

manifest=(ROOT/'AndroidManifest.xml').read_text()
if 'android:supportsPictureInPicture="true"' not in manifest:
    raise SystemExit('PiP manifest capability missing')

print('5.3.7 applied: onUserLeaveHint -> brain gate -> Android PiP')
print('No video = no action; confirmed video = enterPictureInPictureMode')
print('Persistent listener/native/surface code untouched')
