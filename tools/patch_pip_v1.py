from pathlib import Path
import re

manifest = Path('/tmp/decoded/AndroidManifest.xml')
s = manifest.read_text(encoding='utf-8')

# Stable 2 phone integration: locate the APK's real launcher activity instead
# of assuming a hard-coded Kodi activity class. Manifest-only; no skin/player changes.
activities = list(re.finditer(r'<activity\b[^>]*>', s))
if not activities:
    raise SystemExit('No activities found in AndroidManifest.xml')

# Prefer the activity whose body contains the MAIN/LAUNCHER intent filter.
activity_match = None
for m in activities:
    close = s.find('</activity>', m.end())
    if close == -1:
        continue
    body = s[m.start():close + len('</activity>')]
    if ('android.intent.action.MAIN' in body and
            'android.intent.category.LAUNCHER' in body):
        activity_match = m
        break

# Kodi manifests can vary after apktool decode. If launcher markers are not
# discoverable, prefer an activity containing xbmc/kodi in its class name.
if activity_match is None:
    for m in activities:
        tag = m.group(0)
        name = re.search(r'android:name="([^"]+)"', tag)
        if name and any(x in name.group(1).lower() for x in ('xbmc', 'kodi')):
            activity_match = m
            break

if activity_match is None:
    raise SystemExit('Could not identify Kodi launcher activity')

old = activity_match.group(0)
name_m = re.search(r'android:name="([^"]+)"', old)
activity_name = name_m.group(1) if name_m else '<unknown>'
new = old

if 'android:supportsPictureInPicture=' not in new:
    new = new[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in new:
    new = new[:-1] + ' android:resizeableActivity="true">'

wanted = ['orientation', 'screenSize', 'smallestScreenSize', 'screenLayout', 'uiMode']
cm = re.search(r'android:configChanges="([^"]*)"', new)
if cm:
    current = [x for x in cm.group(1).split('|') if x]
    for item in wanted:
        if item not in current:
            current.append(item)
    new = new[:cm.start()] + 'android:configChanges="' + '|'.join(current) + '"' + new[cm.end():]
else:
    new = new[:-1] + ' android:configChanges="' + '|'.join(wanted) + '">'

s = s[:activity_match.start()] + new + s[activity_match.end():]
manifest.write_text(s, encoding='utf-8')
print(f'Infinity PiP enabled on launcher activity: {activity_name}')
