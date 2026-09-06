from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# Native resume stays completely untouched.
# v4 diagnosis:
# - v3's slider worked but rendered as a blank gray rectangle because we forced
#   ad-hoc slider textures and positioned it outside Estuary's real OSD grouplist.
# - Put volume inside Estuary's existing right-side OSD button row and let Kodi
#   render the slider with its native/default slider skin.


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

marker = '<control type="grouplist" id="202">'
start = s.find(marker)
if start < 0:
    raise SystemExit('Right-side OSD grouplist 202 not found')
end = matching_control_end(s, start)

if 'Infinity integrated volume v4' not in s:
    block = r'''

                    <!-- Infinity integrated volume v4: native-looking volume + mute -->
                    <control type="group" id="9880">
                        <width>300</width>
                        <height>76</height>

                        <!-- Same focus ring style as the surrounding Estuary OSD buttons. -->
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

                        <!-- Kodi's own dynamic volume icon, including muted state. -->
                        <control type="image">
                            <left>17</left>
                            <top>17</top>
                            <width>40</width>
                            <height>40</height>
                            <texture colordiffuse="white">$VAR[VolumeIconVar]</texture>
                        </control>

                        <!-- Native Kodi volume slider. No custom/fallback textures: use the skin's normal slider visuals. -->
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
print('Infinity volume v4 patched into Estuary OSD row. Native resume untouched.')
