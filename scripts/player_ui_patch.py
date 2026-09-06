from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
select = root / 'DialogSelect.xml'

if not osd.exists():
    raise SystemExit('VideoOSD.xml not found')
if not select.exists():
    raise SystemExit('DialogSelect.xml not found')

s = osd.read_text(encoding='utf-8')
marker = '</controls>'
block = '''
            <!-- Infinity player audio controls -->
            <control type="group" id="9890">
              <left>70</left>
              <top>70</top>
              <animation effect="fade" start="0" end="100" time="140">Visible</animation>
              <animation effect="fade" start="100" end="0" time="180">Hidden</animation>
              <control type="button" id="9891">
                <width>56</width><height>56</height>
                <label>Mute</label>
                <onclick>Mute</onclick>
                <hinttext>Mute / Unmute</hinttext>
              </control>
              <control type="button" id="9892">
                <left>66</left><width>56</width><height>56</height>
                <label>-</label>
                <onclick>SetVolume(-5)</onclick>
                <hinttext>Volume Down</hinttext>
              </control>
              <control type="button" id="9893">
                <left>132</left><width>56</width><height>56</height>
                <label>+</label>
                <onclick>SetVolume(+5)</onclick>
                <hinttext>Volume Up</hinttext>
              </control>
            </control>
'''
if 'id="9890"' not in s:
    pos = s.rfind(marker)
    if pos < 0:
        raise SystemExit('VideoOSD controls marker not found')
    s = s[:pos] + block + s[pos:]
    osd.write_text(s, encoding='utf-8')

s = select.read_text(encoding='utf-8')
open_anim = '<animation effect="fade" start="0" end="100" time="140">WindowOpen</animation>'
if open_anim not in s:
    needle = '<controls>'
    if needle not in s:
        raise SystemExit('DialogSelect controls marker not found')
    anim = (
        open_anim + '\n'
        + '<animation effect="slide" start="0,18" end="0,0" time="160">WindowOpen</animation>\n'
        + '<animation effect="fade" start="100" end="0" time="120">WindowClose</animation>\n'
    )
    s = s.replace(needle, anim + needle, 1)
    select.write_text(s, encoding='utf-8')

print('Player UI patch applied')
