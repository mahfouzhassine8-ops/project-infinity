from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v6 keeps native resume, mute, volume action, and v5 placement concept.
# Diagnosis: Kodi's slider itself supports both tap and drag, but placing it inside
# the horizontal grouplist can let the parent row consume horizontal gestures.
# Fix: keep the volume UI visually beside playback controls, but move the slider
# outside grouplist 201 so it can receive Kodi's native drag/gesture events directly.


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

# Find the parent playback group 200. The native playback grouplist 201 stays untouched.
marker = '<control type="group" id="200">'
gstart = s.find(marker)
if gstart < 0:
    raise SystemExit('Playback OSD group 200 not found')
gend = matching_control_end(s, gstart)

if 'Infinity integrated volume v6' not in s:
    block = r'''

                <!-- Infinity integrated volume v6: tap + true drag beside playback controls -->
                <control type="group" id="9880">
                    <left>455</left>
                    <top>90</top>
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

                    <!-- Kodi native slider: supports tap-to-jump and drag/gesture pan. -->
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
    s = s[:gend] + block + s[gend:]

osd.write_text(s, encoding='utf-8')
print('Infinity volume v6: tap + drag enabled beside playback controls. Native resume untouched.')
