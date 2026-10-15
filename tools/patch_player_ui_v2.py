from pathlib import Path

root = Path('/tmp/decoded/assets/addons/skin.estuary/xml')
osd = root / 'VideoOSD.xml'
s = osd.read_text(encoding='utf-8')

# v13 final attempt: stop using focus as the trigger.
# A tiny Kodi service watches the actual Player.Volume label. Every time the
# volume value changes it raises a short-lived Home-window property. The skin
# uses that property for the zoom/fade, so the control returns to normal after
# volume activity stops even if Kodi leaves the slider focused.

old_group = '''<animation effect="zoom" start="100" end="118,128" center="auto" time="120" tween="sine" easing="out" condition="Control.HasFocus(8802)">Conditional</animation>\n                    <!-- Slight transparency only while interacting with the slider. -->\n                    <animation effect="fade" start="100" end="78" time="100" condition="Control.HasFocus(8802)">Conditional</animation>'''
new_group = '''<!-- Infinity volume fluid polish v13: driven by real volume changes -->\n                    <animation effect="zoom" start="100" end="118,128" center="auto" time="150" tween="sine" easing="inout" condition="String.IsEqual(Window(home).Property(Infinity.VolumeActive),true)" reversible="true">Conditional</animation>\n                    <animation effect="fade" start="100" end="82" time="130" tween="sine" easing="inout" condition="String.IsEqual(Window(home).Property(Infinity.VolumeActive),true)" reversible="true">Conditional</animation>'''

old_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="90">Focus</animation>\n                        <animation effect="zoom" start="106,120" end="100" center="auto" time="100">Unfocus</animation>'''
new_slider = '''<animation effect="zoom" start="100" end="106,120" center="auto" time="140" tween="sine" easing="inout" condition="String.IsEqual(Window(home).Property(Infinity.VolumeActive),true)" reversible="true">Conditional</animation>'''

if 'Infinity volume fluid polish v13' not in s:
    if old_group not in s:
        raise SystemExit('Stable 2 volume group animation not found')
    if old_slider not in s:
        raise SystemExit('Stable 2 slider animation not found')
    s = s.replace(old_group, new_group, 1)
    s = s.replace(old_slider, new_slider, 1)

osd.write_text(s, encoding='utf-8')

addon = Path('/tmp/decoded/assets/addons/service.infinity.volume')
addon.mkdir(parents=True, exist_ok=True)
(addon / 'addon.xml').write_text('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<addon id="service.infinity.volume" name="Infinity Volume Activity" version="1.0.0" provider-name="Infinity">
  <requires>
    <import addon="xbmc.python" version="3.0.0"/>
  </requires>
  <extension point="xbmc.service" library="service.py" start="startup"/>
  <extension point="xbmc.addon.metadata">
    <summary lang="en_GB">Tracks active volume changes for the Infinity player UI.</summary>
    <description lang="en_GB">Raises a temporary skin property while the player volume is changing.</description>
    <platform>all</platform>
    <license>MIT</license>
  </extension>
</addon>
''', encoding='utf-8')

(addon / 'service.py').write_text('''import time
import xbmc
import xbmcgui

monitor = xbmc.Monitor()
home = xbmcgui.Window(10000)
last_volume = None
active_until = 0.0
active = False

home.clearProperty('Infinity.VolumeActive')

while not monitor.abortRequested():
    current = xbmc.getInfoLabel('Player.Volume')
    now = time.monotonic()

    if current and last_volume is not None and current != last_volume:
        active_until = now + 0.32
        if not active:
            home.setProperty('Infinity.VolumeActive', 'true')
            active = True

    if current:
        last_volume = current

    if active and now >= active_until:
        home.clearProperty('Infinity.VolumeActive')
        active = False

    if monitor.waitForAbort(0.05):
        break

home.clearProperty('Infinity.VolumeActive')
''', encoding='utf-8')

print('Infinity Stable 2 volume v13 applied; expansion now follows real volume changes, not focus.')
