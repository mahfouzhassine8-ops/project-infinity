from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# Native resume stays completely untouched in this patch.
# Add a true Kodi volume slider directly into the fullscreen player OSD.
# Kodi's skin engine supports <action>volume</action>, so dragging this slider
# changes volume without opening the separate top volume popup.

insert_at = s.rfind('</controls>')
if insert_at < 0:
    raise SystemExit('VideoOSD controls marker not found')

if 'Infinity integrated volume v3' not in s:
    block = r'''
    <!-- Infinity integrated volume v3: bottom-bar volume + mute -->
    <control type="group" id="9880">
      <right>410</right>
      <bottom>20</bottom>
      <width>290</width>
      <height>58</height>
      <animation effect="fade" start="0" end="100" time="120">Visible</animation>
      <animation effect="fade" start="100" end="0" time="150">Hidden</animation>

      <!-- Speaker button: tap to mute/unmute. Icon follows Kodi's real mute/volume state. -->
      <control type="button" id="9881">
        <left>0</left>
        <top>3</top>
        <width>52</width>
        <height>52</height>
        <label></label>
        <texturefocus colordiffuse="FFFFFFFF">$VAR[VolumeIconVar]</texturefocus>
        <texturenofocus colordiffuse="D9FFFFFF">$VAR[VolumeIconVar]</texturenofocus>
        <onclick>Mute</onclick>
        <hinttext>Mute / Unmute</hinttext>
        <pulseonselect>false</pulseonselect>
      </control>

      <!-- Native Kodi volume slider: direct touch/drag control, no popup window. -->
      <control type="slider" id="9882">
        <left>62</left>
        <top>15</top>
        <width>220</width>
        <height>28</height>
        <action>volume</action>
        <orientation>horizontal</orientation>
        <texturesliderbar colordiffuse="99FFFFFF">colors/white.png</texturesliderbar>
        <texturesliderbardisabled colordiffuse="55FFFFFF">colors/white.png</texturesliderbardisabled>
        <textureslidernib colordiffuse="FFFFFFFF">buttons/round.png</textureslidernib>
        <textureslidernibfocus colordiffuse="FFFFFFFF">buttons/round.png</textureslidernibfocus>
        <pulseonselect>false</pulseonselect>
        <onleft>9881</onleft>
        <onright>9882</onright>
      </control>
    </control>
'''
    s = s[:insert_at] + block + s[insert_at:]

osd.write_text(s, encoding='utf-8')
print('Infinity volume v3 patched. Native resume untouched.')
