from pathlib import Path
import re

ROOT = Path('/tmp/target')
MAIN = CTRL = LISTENER = None
for d in ROOT.glob('smali*'):
    p = d / 'com/projectinfinity/kodi/Main.smali'
    c = d / 'com/projectinfinity/kodi/InfinityController.smali'
    l = d / 'com/projectinfinity/kodi/InfinityController$KodiListenerRunnable.smali'
    if p.exists() and c.exists() and l.exists():
        MAIN, CTRL, LISTENER = p, c, l
        break
if not all([MAIN, CTRL, LISTENER]):
    raise SystemExit('Exact Infinity 6.0 brain files not found')

main = MAIN.read_text()
ctrl = CTRL.read_text()
listener = LISTENER.read_text()

# Protect the known-good pieces.
required_main = [
    '.method protected onUserLeaveHint()V',
    'InfinityController;->shouldAllowPiP()Z',
    'Lcom/projectinfinity/kodi/Main;->enterPictureInPictureMode()Z',
]
for marker in required_main:
    if marker not in main:
        raise SystemExit(f'6.0 PiP path changed: missing {marker}')
for marker in [
    '.field public static volatile isVideoPlaying:Z',
    '.method public static setVideoPlaying(ZLjava/lang/String;)V',
    '.method public static shouldAllowPiP()Z',
]:
    if marker not in ctrl:
        raise SystemExit(f'6.0 brain changed: missing {marker}')

# The 6.0 listener incorrectly treated ANY socket/transport loss as "video stopped".
# That can race the Home transition and make shouldAllowPiP() false right when
# Stable2's proven onUserLeaveHint() asks the brain.
# Playback state must only change from actual Kodi playback evidence:
# Player.GetActivePlayers response, Player.OnAVStart, or Player.OnStop.
pattern = re.compile(
    r'(?ms)(:goto_3\n\s*const/4 v12, 0x0\n\s*)'
    r'sput-boolean v12, Lcom/projectinfinity/kodi/InfinityController;->isVideoPlaying:Z\n'
)
listener2, count = pattern.subn(r'\1# Infinity 6.2: transport loss is NOT playback stop. Preserve last proven state.\n', listener, count=1)
if count != 1:
    raise SystemExit(f'Expected exactly one transport-reset state write, found {count}')

# Refuse accidental Auto-PiP experiments in this build. 6.2 uses Stable2's
# exact proven manual PiP trigger, gated only by the brain state.
if 'AutoPiPRunnable' in listener2 or 'updateAutoPiP' in ctrl:
    raise SystemExit('Unexpected Auto-PiP code in protected 6.0 base')

LISTENER.write_text(listener2)

print('Infinity 6.2 patch applied')
print('Only change: socket disconnect/reconnect no longer forces video state false')
print('Stable2 proven PiP trigger + 6.0 brain gate remain untouched')
