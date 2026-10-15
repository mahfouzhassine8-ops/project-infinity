from pathlib import Path
import re

root = Path('/tmp/decoded')
man = root / 'AndroidManifest.xml'
text = man.read_text()

pat = r'<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>'
m = re.search(pat, text)
if not m:
    raise SystemExit('Main activity not found')
tag = m.group(0)

cfg = 'orientation|screenSize|smallestScreenSize|screenLayout|density|uiMode'
for key, value in (
    ('android:configChanges', cfg),
    ('android:resizeableActivity', 'true'),
    ('android:supportsPictureInPicture', 'true'),
):
    if key + '=' in tag:
        tag = re.sub(re.escape(key) + r'="[^"]*"', key + '="' + value + '"', tag)
    else:
        tag = tag[:-1] + f' {key}="{value}">'

text = text[:m.start()] + tag + text[m.end():]

# Add Android's foldable size-change opt-in metadata to Main if absent.
if 'android.supports_size_changes' not in text:
    close = text.find('</activity>', m.start())
    if close < 0:
        raise SystemExit('Main activity closing tag not found')
    meta = '\n        <meta-data android:name="android.supports_size_changes" android:value="true" />\n'
    text = text[:close] + meta + text[close:]

man.write_text(text)
print('Applied fold/multitask manifest configuration')
