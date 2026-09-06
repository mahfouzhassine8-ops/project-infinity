from pathlib import Path
import re

manifest = Path('/tmp/decoded/AndroidManifest.xml')
s = manifest.read_text(encoding='utf-8')

# PiP v1: Android must know Kodi's main activity supports picture-in-picture.
# Keep this surgical: manifest only, no skin/player-control changes.

activity_match = re.search(r'<activity\b[^>]*android:name="org\.xbmc\.kodi\.Main"[^>]*>', s)
if not activity_match:
    raise SystemExit('Kodi main activity not found in AndroidManifest.xml')

old = activity_match.group(0)
new = old
if 'android:supportsPictureInPicture=' not in new:
    new = new[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in new:
    new = new[:-1] + ' android:resizeableActivity="true">'

s = s[:activity_match.start()] + new + s[activity_match.end():]
manifest.write_text(s, encoding='utf-8')
print('Infinity PiP v1 manifest support enabled.')
