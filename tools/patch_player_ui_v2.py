from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v5 is presentation-only: native resume and the proven v4 volume/mute mechanics stay untouched.
# Put volume with playback controls on the LEFT, while Settings remains the final RIGHT-side button.

def matching_control_end(text, start):
    pos = start
    depth = 0
    while True:
        next_open = text.find('<control', pos)
        next_close = text.find('</control>', pos)
        if next_close < 0:
            raise SystemExit('Unbalanced control tags')
        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open + 8
        else:
            depth -= 1
            if depth == 0:
                return next_close
            pos = next_close + 10

# Left playback row (previous / rewind / play / stop / forward / next).
marker = '<control type="grouplist" id="201">'
start = s.find(marker)
if start < 0:
    raise SystemExit('Playback OSD grouplist 201 not found')
end = matching_control_end(s, start)

if 'Infinity integrated volume v5' not in s:
    block = r'''

                    <!-- Infinity integrated volume v5: volume belongs with playback controls -->
                    <control type="group" id="9880">
                        <width>300</width>
                        <height>76</height>
                        <control type="button" id="9881">
                            <left>0</left>
                            <top>0</top>
                            <width>74</width>
                            <height>74</height>
                            <label></label>
                            <font></font>
                            <texturefocus colordiffuse="button_focus">osd/fullscreen/buttons/button-fo.png</texturefocus>
                            <texturenofocus />
                            <onclick>Mute</onclick>
                            <hinttext>Mute / Unmute</hinttext>
                            <pulseonselect>false</pulseonselect>
                            <onright>9882</onright>
                        </control>
                        <control type="image">
                            <left>17</left>
                            <top>17</top>
                            <width>40</width>
                            <height>40</height>
                            <texture colordiffuse="white">$VAR[VolumeIconVar]</texture>
                        </control>
                        <control type="slider" id="9882">
                            <left>88</left>
                            <top>23</top>
                            <width>195</width>
                            <height>28</height>
                            <action>volume</action>
                            <orientation>horizontal</orientation>
                            <pulseonselect>false</pulseonselect>
                            <onleft>9881</onleft>
                            <onright>9882</onright>
                        </control>
                    </control>
'''
    s = s[:end] + block + s[end:]

osd.write_text(s, encoding='utf-8')
print('Infinity volume v5 placed with playback controls; Settings remains last on right. Native resume untouched.')
