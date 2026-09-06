from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v7 is Stable 2. Keep the exact expansion size the user liked, but make the
# movement smoother and make the HUD visibly return toward normal as it hides.

old_group = '''<animation effect="zoom" start="100" end="118,128" center="auto" time="120" tween="sine" easing="out" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <!-- Slight transparency only while interacting with the slider. -->\n                    <animation effect="fade" start="100" end="78" time="100" condition="Control.HasFocus(8802)">Conditional</animation>'''
new_group = '''<!-- Infinity volume fluid polish v10: same v7 size, smoother motion -->\n                    <animation effect="zoom" start="100" end="118,128" center="auto" time="190" tween="sine" easing="inout" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <animation effect="fade" start="100" end="82" time="170" tween="sine" easing="inout" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <!-- When the OSD starts hiding, settle the HUD back toward normal before it disappears. -->\n                    <animation effect="zoom" start="118,128" end="100" center="auto" time="120" tween="sine" easing="inout">Hidden</animation>\n                    <animation effect="fade" start="82" end="100" time="100" tween="sine" easing="inout">Hidden</animation>'''

old_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="90">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="100">Unfocus</animation>'''
new_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="170" tween="sine" easing="inout">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="120" tween="sine" easing="inout">Unfocus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="100" tween="sine" easing="inout">Hidden</animation>'''

if 'Infinity volume fluid polish v10' not in s:
    if 'Infinity volume fluid polish v9' in s:
        raise SystemExit('This patch expects the clean v7 Stable 2 baseline, not a v9-patched base')
    if old_group not in s:
        raise SystemExit('Stable 2 volume group animation not found')
    if old_slider not in s:
        raise SystemExit('Stable 2 slider animation not found')
    s = s.replace(old_group, new_group, 1)
    s = s.replace(old_slider, new_slider, 1)

osd.write_text(s, encoding='utf-8')
print('Infinity Stable 2 fluid volume v10 applied; v7 size preserved and hide timing polished.')
