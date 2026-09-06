from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v7 is Stable 2. Keep the same expansion size the user liked.
# v12 workaround: Kodi keeps the slider focused after touch ends, so do not rely
# on Unfocus to restore size. Instead, run a finite expand/return pulse whenever
# the slider receives focus. This guarantees it returns to normal even if focus sticks.

old_group = '''<animation effect="zoom" start="100" end="118,128" center="auto" time="120" tween="sine" easing="out" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <!-- Slight transparency only while interacting with the slider. -->\n                    <animation effect="fade" start="100" end="78" time="100" condition="Control.HasFocus(8802)">Conditional</animation>'''
new_group = '''<!-- Infinity volume fluid polish v12: timed pulse; no sticky focus dependency -->\n                    <animation effect="zoom" start="100" end="118,128" center="auto" time="170" tween="sine" easing="inout">Focus</animation>\n                    <animation effect="zoom" start="118,128" end="100" center="auto" delay="220" time="130" tween="sine" easing="inout">Focus</animation>\n                    <animation effect="fade" start="100" end="82" time="150" tween="sine" easing="inout">Focus</animation>\n                    <animation effect="fade" start="82" end="100" delay="220" time="110" tween="sine" easing="inout">Focus</animation>'''

old_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="90">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="100">Unfocus</animation>'''
new_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="150" tween="sine" easing="inout">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" delay="220" time="120" tween="sine" easing="inout">Focus</animation>'''

if 'Infinity volume fluid polish v12' not in s:
    if old_group not in s:
        raise SystemExit('Stable 2 volume group animation not found')
    if old_slider not in s:
        raise SystemExit('Stable 2 slider animation not found')
    s = s.replace(old_group, new_group, 1)
    s = s.replace(old_slider, new_slider, 1)

osd.write_text(s, encoding='utf-8')
print('Infinity Stable 2 volume v12 applied; timed pulse returns to normal without waiting for Unfocus.')
