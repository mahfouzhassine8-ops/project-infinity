from pathlib import Path

root = Path('/tmp/decoded')
bridge = root / 'smali/com/projectinfinity/kodi/InfinityPhoneBridge.smali'
if not bridge.exists():
    hits = [x for d in root.glob('smali*') for x in d.rglob('InfinityPhoneBridge.smali')]
    if not hits:
        raise SystemExit('InfinityPhoneBridge.smali not found; apply phone-layer v4 first')
    bridge = hits[0]

text = bridge.read_text()

old = '''    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
'''
new = '''    # Infinity PiP v5.4: never let Android auto-enter PiP blindly.
    # PiP entry is handled by enterPipOnUserLeave(), which first calls
    # hasActiveVideoPlayer() and therefore only enters PiP during video playback.
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAutoEnterEnabled(Z)Landroid/app/PictureInPictureParams$Builder;
'''

if old not in text:
    raise SystemExit('Could not locate v4 unconditional auto-PiP block')
text = text.replace(old, new, 1)

# Safety checks: keep the existing explicit, playback-gated Home/Recents path.
required = [
    'hasActiveVideoPlayer(Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z',
    'enterPipOnUserLeave(Landroid/app/Activity;Lcom/projectinfinity/kodi/XBMCJsonRPC;)Z',
    'setAutoEnterEnabled(Z)',
    'const/4 v1, 0x0',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'Missing required playback-gate marker: {marker}')

bridge.write_text(text)
print('Applied Infinity PiP v5.4 playback gate: no video = no PiP')
