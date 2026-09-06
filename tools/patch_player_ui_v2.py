from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v7 preserves the proven v6 native volume slider mechanics and resume behavior.
# Add a larger translucent visual treatment around the slider so touch adjustment
# is easier to see, while keeping the same native volume action underneath.

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

marker = '<control type="group" id="200">'
gstart = s.find(marker)
if gstart < 0:
    raise SystemExit('Playback OSD group 200 not found')
gend = matching_control_end(s, gstart)

if 'Infinity volume focus HUD v7' not in s:
    block = r'''

                <!-- Infinity volume focus HUD v7: larger translucent touch target, native slider preserved -->
                <control type="group" id="9880">
                    <left>430</left>
                    <top>76</top>
                    <width>390</width>
                    <height>104</height>

                    <!-- subtle translucent backing so the volume position is readable over video -->
                    <control type="image">
                        <left>0</left>
                        <top>5</top>
                        <width>390</width>
                        <height>94</height>
                        <texture colordiffuse="88000000">white.png</texture>
                        <aspectratio>stretch</aspectratio>
                    </control>

                    <control type="button" id="9881">
                        <left>12</left>
                        <top>15</top>
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
                        <left>29</left>
                        <top>32</top>
                        <width>40</width>
                        <height>40</height>
                        <texture colordiffuse="white">$VAR[VolumeIconVar]</texture>
                    </control>

                    <!-- Same Kodi-native tap + drag slider as v6, enlarged for touch. -->
                    <control type="slider" id="9882">
                        <left>100</left>
                        <top>30</top>
                        <width>270</width>
                        <height>44</height>
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
print('Infinity v7 volume focus HUD added. Native tap/drag volume and resume untouched.')
