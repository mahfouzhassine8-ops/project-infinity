from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v8 behavior fix, while keeping the v7 marker expected by the existing workflow.
# Keep the native Kodi volume action, use safe control IDs outside Kodi's reserved
# 9000-9999 group range, and only enlarge/translucently soften the HUD while the
# volume slider has focus (the closest skin-level state to active touch/drag).

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

                <!-- Infinity volume focus HUD v7 / v8 behavior fix -->
                <!-- Compact normally; expands and softens only while the slider has focus. -->
                <control type="group" id="8800">
                    <left>455</left>
                    <top>88</top>
                    <width>340</width>
                    <height>76</height>

                    <!-- Focus-driven enlargement. Reverses automatically on unfocus. -->
                    <animation effect="zoom" start="100" end="118,128" center="auto" time="120" tween="sine" easing="out" condition="Control.HasFocus(8802)">Conditional</animation>
                    <!-- Slight transparency only while interacting with the slider. -->
                    <animation effect="fade" start="100" end="78" time="100" condition="Control.HasFocus(8802)">Conditional</animation>

                    <!-- Translucent backing exists only while the slider is focused. -->
                    <control type="image">
                        <left>0</left>
                        <top>0</top>
                        <width>340</width>
                        <height>76</height>
                        <texture colordiffuse="70000000">white.png</texture>
                        <aspectratio>stretch</aspectratio>
                        <visible>Control.HasFocus(8802)</visible>
                        <animation effect="fade" start="0" end="100" time="90">Visible</animation>
                        <animation effect="fade" start="100" end="0" time="110">Hidden</animation>
                    </control>

                    <control type="button" id="8801">
                        <left>8</left>
                        <top>10</top>
                        <width>56</width>
                        <height>56</height>
                        <label></label>
                        <font></font>
                        <texturefocus colordiffuse="button_focus">osd/fullscreen/buttons/button-fo.png</texturefocus>
                        <texturenofocus />
                        <onclick>Mute</onclick>
                        <hinttext>Mute / Unmute</hinttext>
                        <pulseonselect>false</pulseonselect>
                        <onright>8802</onright>
                    </control>

                    <control type="image">
                        <left>20</left>
                        <top>22</top>
                        <width>32</width>
                        <height>32</height>
                        <texture colordiffuse="white">$VAR[VolumeIconVar]</texture>
                    </control>

                    <!-- Native Kodi tap + drag volume slider. -->
                    <control type="slider" id="8802">
                        <left>76</left>
                        <top>21</top>
                        <width>246</width>
                        <height>34</height>
                        <action>volume</action>
                        <orientation>horizontal</orientation>
                        <pulseonselect>false</pulseonselect>
                        <onleft>8801</onleft>
                        <onright>8802</onright>
                        <animation effect="zoom" start="100" end="106,120" center="auto" time="90">Focus</animation>
                        <animation effect="zoom" start="106,120" end="100" center="auto" time="100">Unfocus</animation>
                    </control>
                </control>
'''
    s = s[:gend] + block + s[gend:]

osd.write_text(s, encoding='utf-8')
print('Infinity v8 volume interaction behavior added. Native tap/drag volume and resume untouched.')
