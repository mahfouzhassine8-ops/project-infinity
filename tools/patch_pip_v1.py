from pathlib import Path
import re

manifest = Path('/tmp/decoded/AndroidManifest.xml')
s = manifest.read_text(encoding='utf-8')

# Phone integration v1, built on Stable 2 (v12):
# - enable Android picture-in-picture capability
# - allow resizing/multi-window
# - handle Fold/screen-size/orientation changes without forcing Android to recreate
#   the activity for those configuration changes
# Keep this manifest-only: no skin/player-control changes.

activity_match = re.search(r'<activity\b[^>]*android:name="org\.xbmc\.kodi\.Main"[^>]*>', s)
if not activity_match:
    raise SystemExit('Kodi main activity not found in AndroidManifest.xml')

new = activity_match.group(0)

if 'android:supportsPictureInPicture=' not in new:
    new = new[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in new:
    new = new[:-1] + ' android:resizeableActivity="true">'

wanted = ['orientation', 'screenSize', 'smallestScreenSize', 'screenLayout', 'uiMode']
m = re.search(r'android:configChanges="([^"]*)"', new)
if m:
    current = [x for x in m.group(1).split('|') if x]
    for item in wanted:
        if item not in current:
            current.append(item)
    new = new[:m.start()] + 'android:configChanges="' + '|'.join(current) + '"' + new[m.end():]
else:
    new = new[:-1] + ' android:configChanges="' + '|'.join(wanted) + '">'

s = s[:activity_match.start()] + new + s[activity_match.end():]
manifest.write_text(s, encoding='utf-8')
print('Infinity phone integration v1 enabled: PiP, resize/multi-window, Fold/config handling.')
