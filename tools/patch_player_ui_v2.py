from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# Remove the previous experimental floating volume cluster if present.
start = s.find('<!-- Infinity player audio controls:')
if start >= 0:
    end = s.find('</control>', start)
    # group contains nested controls, so remove through the known following controls marker conservatively
    tail = s.find('</control>\n            </control>', start)
    if tail >= 0:
        s = s[:start] + s[tail + len('</control>\n            </control>'):]

# Add a single bottom-bar volume button. It opens Kodi's native volume control UI;
# mute remains integrated via Kodi's speaker/mute state rather than separate +/- text buttons.
needle = '<control type="button" id="' 
insert_at = s.rfind('</controls>')
if insert_at < 0:
    raise SystemExit('VideoOSD controls marker not found')

if 'id="9895"' not in s:
    block = '''\n    <!-- Infinity integrated audio control: bottom player bar -->\n    <control type="button" id="9895">\n      <right>420</right>\n      <bottom>18</bottom>\n      <width>64</width>\n      <height>64</height>\n      <label>🔊</label>\n      <font>font20</font>\n      <onclick>ActivateWindow(volumebar)</onclick>\n      <hinttext>Volume / Mute</hinttext>\n      <animation effect="fade" start="0" end="100" time="120">Visible</animation>\n      <animation effect="fade" start="100" end="0" time="160">Hidden</animation>\n    </control>\n'''
    s = s[:insert_at] + block + s[insert_at:]

osd.write_text(s, encoding='utf-8')

# Presentation-only resume dialog polish. Native bookmark/resume logic is untouched.
d = root / 'DialogSelect.xml'
t = d.read_text(encoding='utf-8')
if 'Infinity resume presentation' not in t:
    marker = '<controls>'
    anim = '''<!-- Infinity resume presentation: visual only; native resume logic untouched -->\n<animation effect="fade" start="0" end="100" time="130">WindowOpen</animation>\n<animation effect="slide" start="24,0" end="0,0" time="170" tween="cubic" easing="out">WindowOpen</animation>\n<animation effect="fade" start="100" end="0" time="110">WindowClose</animation>\n'''
    if marker not in t:
        raise SystemExit('DialogSelect controls marker not found')
    t = t.replace(marker, anim + marker, 1)
    d.write_text(t, encoding='utf-8')

print('Player UI v2 patched; native resume logic untouched.')
