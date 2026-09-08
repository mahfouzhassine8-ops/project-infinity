from pathlib import Path
import re, runpy

ROOT = Path('/tmp/xbmc')
if not ROOT.exists():
    raise SystemExit('/tmp/xbmc source tree missing')

# Keep the proven native video-renderer PiP work as the baseline.
runpy.run_path('scripts/patch-native-pip-v5-3-surgical-renderer.py', run_name='__main__')

# ------------------------------------------------------------------
# 1) CORE WINDOW RESIZE / FOLD INPUT SYNCHRONIZATION
# Kodi 21.2 Android explicitly ignores configuration changes and assumes
# resize events cannot happen because it was historically fullscreen-only.
# That assumption is wrong for PiP, Samsung multi-window and foldables.
# Push a real XBMC_VIDEORESIZE event using the current ANativeWindow size.
# This makes GUI geometry and touch hit-testing use the same dimensions.
# ------------------------------------------------------------------
app = ROOT / 'xbmc/platform/android/activity/XBMCApp.cpp'
s = app.read_text()

inc = '#include "windowing/WinEvents.h"\n'
if '#include "windowing/XBMC_events.h"' not in s:
    if inc not in s:
        raise SystemExit('XBMCApp include anchor missing')
    s = s.replace(inc, inc + '#include "windowing/XBMC_events.h"\n', 1)

old_cfg = '''void CXBMCApp::onConfigurationChanged()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  // ignore any configuration changes like screen rotation etc\n}\n'''
new_cfg = '''void CXBMCApp::onConfigurationChanged()\n{\n  android_printf("%s: Infinity dynamic configuration refresh", __PRETTY_FUNCTION__);\n  // Fold open/close, DeX, split-screen and PiP all change the usable surface.\n  // Treat configuration changes as real window resizes instead of ignoring them.\n  onResizeWindow();\n}\n'''
if old_cfg not in s:
    raise SystemExit('Kodi 21.2 onConfigurationChanged anchor changed')
s = s.replace(old_cfg, new_cfg, 1)

old_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  m_window.reset();\n  // no need to do anything because we are fixed in fullscreen landscape mode\n}\n'''
new_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: Infinity dynamic resize", __PRETTY_FUNCTION__);\n\n  // Drop Kodi's cached native-window wrapper and reacquire the CURRENT surface.\n  m_window.reset();\n  auto window = GetNativeWindow(0);\n  if (!window)\n  {\n    android_printf("Infinity resize: current native window unavailable");\n    return;\n  }\n\n  const int width = window->GetWidth();\n  const int height = window->GetHeight();\n  if (width <= 0 || height <= 0)\n  {\n    android_printf("Infinity resize: invalid surface %dx%d", width, height);\n    return;\n  }\n\n  auto* winSystem = dynamic_cast<CWinSystemAndroid*>(CServiceBroker::GetWinSystem());\n  if (!winSystem)\n    return;\n\n  XBMC_Event event{};\n  event.type = XBMC_VIDEORESIZE;\n  event.resize.width = width;\n  event.resize.height = height;\n  event.resize.scale = 1.0;\n  winSystem->MessagePush(&event);\n\n  // DPI can also change across Samsung display/window modes. Keep gesture\n  // thresholds in the same coordinate space as the newly resized GUI.\n  m_inputHandler.setDPI(GetDPI());\n\n  android_printf("Infinity resize: pushed GUI/input resize %dx%d", width, height);\n}\n'''
if old_resize not in s:
    raise SystemExit('Kodi 21.2 onResizeWindow anchor changed')
s = s.replace(old_resize, new_resize, 1)
app.write_text(s)

# ------------------------------------------------------------------
# 2) PLAYER LOCK IN THE ACTUAL VISIBLE RIGHT-HAND OSD GROUP
# The earlier patch inserted before control 804 globally; on-device evidence
# showed it was not landing in the rendered row. Insert directly inside
# grouplist id=202 before the always-visible information button 70043.
# ------------------------------------------------------------------
skin = ROOT / 'addons/skin.estuary'
osd = skin / 'xml/VideoOSD.xml'
t = osd.read_text()
if 'id="7999"' not in t:
    marker = '<control type="radiobutton" id="70043">'
    lock = '''<control type="radiobutton" id="7999">\n\t\t\t\t\t\t<include content="OSDButton">\n\t\t\t\t\t\t\t<param name="texture" value="osd/fullscreen/buttons/infinity-lock.png"/>\n\t\t\t\t\t\t</include>\n\t\t\t\t\t\t<label>Lock screen</label>\n\t\t\t\t\t\t<onclick>Dialog.Close(VideoOSD)</onclick>\n\t\t\t\t\t\t<onclick>ActivateWindow(1199)</onclick>\n\t\t\t\t\t\t<visible>Player.HasVideo</visible>\n\t\t\t\t\t</control>\n\t\t\t\t\t'''
    if marker not in t:
        raise SystemExit('Active OSD right-group marker 70043 missing')
    t = t.replace(marker, lock + marker, 1)
osd.write_text(t)

# Lock overlay catches the whole player surface and exposes only unlock.
overlay = skin / 'xml/Custom_1199_InfinityVideoLock.xml'
overlay.write_text('''<?xml version="1.0" encoding="utf-8"?>\n<window type="dialog" id="1199">\n  <defaultcontrol always="true">9900</defaultcontrol>\n  <controls>\n    <control type="button" id="9900">\n      <left>0</left><top>0</top><width>100%</width><height>100%</height>\n      <texturefocus colordiffuse="00FFFFFF">white.png</texturefocus>\n      <texturenofocus colordiffuse="00FFFFFF">white.png</texturenofocus>\n      <label></label>\n      <onclick>SetProperty(InfinityUnlockVisible,true)</onclick>\n      <onclick>AlarmClock(InfinityHideUnlock,ClearProperty(InfinityUnlockVisible),00:00:03,silent)</onclick>\n    </control>\n    <control type="button" id="9901">\n      <left>40</left><top>35</top><width>86</width><height>86</height>\n      <texturefocus>osd/fullscreen/buttons/infinity-unlock.png</texturefocus>\n      <texturenofocus>osd/fullscreen/buttons/infinity-unlock.png</texturenofocus>\n      <label></label>\n      <visible>!String.IsEmpty(Window.Property(InfinityUnlockVisible))</visible>\n      <onclick>CancelAlarm(InfinityHideUnlock,silent)</onclick>\n      <onclick>Dialog.Close(1199)</onclick>\n    </control>\n  </controls>\n</window>\n''')

# ------------------------------------------------------------------
# 3) COLOR THEMES
# Provide explicit true-black OLED and light palettes at source level.
# The build layer must package matching media/background overrides too; this
# script intentionally changes source skin files, not a post-build APK only.
# ------------------------------------------------------------------
colors = skin / 'colors'
colors.mkdir(exist_ok=True)
(colors / 'Infinity OLED.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<colors>\n  <color name="black">FF000000</color>\n  <color name="background">FF000000</color>\n  <color name="background100">FF000000</color>\n  <color name="background90">E6000000</color>\n  <color name="background80">CC000000</color>\n  <color name="background70">B3000000</color>\n  <color name="background60">99000000</color>\n  <color name="background50">80000000</color>\n  <color name="white">FFFFFFFF</color>\n  <color name="grey">FFB8B8B8</color>\n  <color name="selected">FFFFFFFF</color>\n</colors>\n''')
(colors / 'Infinity Light.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<colors>\n  <color name="black">FF111111</color>\n  <color name="background">FFF5F5F5</color>\n  <color name="background100">FFFFFFFF</color>\n  <color name="background90">E6FFFFFF</color>\n  <color name="background80">CCFFFFFF</color>\n  <color name="white">FF111111</color>\n  <color name="grey">FF555555</color>\n  <color name="selected">FF000000</color>\n</colors>\n''')

print('Infinity 8.0 core-integrated patch applied')
print(' - native PiP renderer baseline retained')
print(' - Android core now propagates real native-window resize into Kodi GUI/input')
print(' - lock inserted in active OSD grouplist 202 before control 70043')
print(' - source-level OLED #000000 and Light palettes added')
