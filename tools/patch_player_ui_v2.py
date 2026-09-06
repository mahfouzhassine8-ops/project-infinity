from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v7 is Stable 2. Keep the exact expansion size the user liked.
# New behavior: expand while the slider has focus, then smoothly return to normal
# immediately when focus leaves instead of waiting for the whole OSD to hide.

old_group = '''<animation effect="zoom" start="100" end="118,128" center="auto" time="120" tween="sine" easing="out" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <!-- Slight transparency only while interacting with the slider. -->\n                    <animation effect="fade" start="100" end="78" time="100" condition="Control.HasFocus(8802)">Conditional</animation>'''
new_group = '''<!-- Infinity volume fluid polish v11: return immediately after interaction -->\n                    <animation effect="zoom" start="100" end="118,128" center="auto" time="190" tween="sine" easing="inout" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <animation effect="fade" start="100" end="82" time="170" tween="sine" easing="inout" condition="Control.HasFocus(8802)">Conditional</animation>'''

old_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="90">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="100">Unfocus</animation>'''
new_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="170" tween="sine" easing="inout">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="110" tween="sine" easing="inout">Unfocus</animation>'''

if 'Infinity volume fluid polish v11' not in s:
    if old_group not in s:
        raise SystemExit('Stable 2 volume group animation not found')
    if old_slider not in s:
        raise SystemExit('Stable 2 slider animation not found')
    s = s.replace(old_group, new_group, 1)
    s = s.replace(old_slider, new_slider, 1)

osd.write_text(s, encoding='utf-8')
print('Infinity Stable 2 volume v11 applied; same expansion, immediate return after interaction.')
