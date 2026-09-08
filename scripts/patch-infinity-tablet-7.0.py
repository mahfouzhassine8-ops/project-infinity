from pathlib import Path
import re

root = Path('/tmp/target')
skin = root / 'assets/addons/skin.estuary'
if not skin.exists():
    raise SystemExit('Estuary skin missing')

colors_dir = skin / 'colors'
colors_dir.mkdir(parents=True, exist_ok=True)
defaults = colors_dir / 'defaults.xml'
if defaults.exists():
    s = defaults.read_text()
    for old in ('FF101010','FF111111','FF121212','FF131313','FF171717','FF181818','FF1A1A1A','FF202020','FF242424','FF262626'):
        s = re.sub(old, 'FF000000', s, flags=re.I)
    defaults.write_text(s)

(colors_dir / 'Infinity OLED.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<colors>
  <color name="black">FF000000</color>
  <color name="background">FF000000</color>
  <color name="background100">FF000000</color>
  <color name="background90">E6000000</color>
  <color name="background80">CC000000</color>
  <color name="background70">B3000000</color>
  <color name="background60">99000000</color>
  <color name="background50">80000000</color>
  <color name="background40">66000000</color>
  <color name="background30">4D000000</color>
  <color name="background20">33000000</color>
  <color name="background10">1A000000</color>
  <color name="white">FFFFFFFF</color>
  <color name="grey">FFB8B8B8</color>
  <color name="selected">FFFFFFFF</color>
</colors>
''')

(colors_dir / 'Infinity Light.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<colors>
  <color name="black">FF111111</color>
  <color name="background">FFF4F4F4</color>
  <color name="background100">FFFFFFFF</color>
  <color name="background90">E6FFFFFF</color>
  <color name="background80">CCFFFFFF</color>
  <color name="white">FF111111</color>
  <color name="grey">FF555555</color>
  <color name="selected">FF000000</color>
</colors>
''')

osd = skin / 'xml/VideoOSD.xml'
text = osd.read_text()
marker = '<control type="radiobutton" id="804">'
lock = '''<control type="radiobutton" id="7999">
                        <include content="OSDButton">
                            <param name="texture" value="osd/fullscreen/buttons/infinity-lock.png"/>
                        </include>
                        <label>Lock screen</label>
                        <onclick>Dialog.Close(VideoOSD)</onclick>
                        <onclick>ActivateWindow(1199)</onclick>
                        <visible>Player.HasVideo</visible>
                    </control>
                    '''
if 'id="7999"' not in text:
    if marker not in text:
        raise SystemExit('VideoOSD insertion point missing')
    osd.write_text(text.replace(marker, lock + marker, 1))

(skin / 'xml/Custom_1199_InfinityVideoLock.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<window type="dialog" id="1199">
  <onload>SetProperty(InfinityLockHint,true)</onload>
  <onload>ClearProperty(InfinityUnlockVisible)</onload>
  <onload>ClearProperty(InfinityUnlocking)</onload>
  <onload>AlarmClock(InfinityHideLockHint,ClearProperty(InfinityLockHint),00:00:01,silent)</onload>
  <onunload>CancelAlarm(InfinityHideLockHint,silent)</onunload>
  <onunload>CancelAlarm(InfinityHideUnlock,silent)</onunload>
  <onunload>CancelAlarm(InfinityFinishUnlock,silent)</onunload>
  <defaultcontrol always="true">9900</defaultcontrol>
  <controls>
    <control type="button" id="9900">
      <left>0</left><top>0</top><width>100%</width><height>100%</height>
      <texturefocus colordiffuse="00FFFFFF">white.png</texturefocus>
      <texturenofocus colordiffuse="00FFFFFF">white.png</texturenofocus>
      <label></label>
      <onclick condition="String.IsEmpty(Window.Property(InfinityUnlocking))">SetProperty(InfinityUnlockVisible,true)</onclick>
      <onclick condition="String.IsEmpty(Window.Property(InfinityUnlocking))">CancelAlarm(InfinityHideUnlock,silent)</onclick>
      <onclick condition="String.IsEmpty(Window.Property(InfinityUnlocking))">AlarmClock(InfinityHideUnlock,ClearProperty(InfinityUnlockVisible),00:00:03,silent)</onclick>
    </control>
    <control type="image">
      <left>48</left><top>35</top><width>58</width><height>58</height>
      <texture>osd/fullscreen/buttons/infinity-lock.png</texture>
      <visible>!String.IsEmpty(Window.Property(InfinityLockHint)) + String.IsEmpty(Window.Property(InfinityUnlocking))</visible>
      <animation effect="fade" start="0" end="100" time="100">Visible</animation>
      <animation effect="fade" start="100" end="0" time="220">Hidden</animation>
    </control>
    <control type="button" id="9901">
      <left>38</left><top>25</top><width>80</width><height>80</height>
      <texturefocus>osd/fullscreen/buttons/infinity-lock.png</texturefocus>
      <texturenofocus>osd/fullscreen/buttons/infinity-lock.png</texturenofocus>
      <label></label>
      <visible>!String.IsEmpty(Window.Property(InfinityUnlockVisible)) + String.IsEmpty(Window.Property(InfinityUnlocking))</visible>
      <onclick>CancelAlarm(InfinityHideUnlock,silent)</onclick>
      <onclick>ClearProperty(InfinityUnlockVisible)</onclick>
      <onclick>SetProperty(InfinityUnlocking,true)</onclick>
      <onclick>AlarmClock(InfinityFinishUnlock,Dialog.Close(1199),00:00:01,silent)</onclick>
    </control>
    <control type="image">
      <left>48</left><top>35</top><width>58</width><height>58</height>
      <texture>osd/fullscreen/buttons/infinity-unlock.png</texture>
      <visible>!String.IsEmpty(Window.Property(InfinityUnlocking))</visible>
      <animation effect="fade" start="0" end="100" time="90">Visible</animation>
      <animation effect="zoom" start="88" end="104" center="77,64" time="140">Visible</animation>
      <animation effect="fade" start="100" end="0" time="220" delay="500">Visible</animation>
    </control>
  </controls>
</window>
''')

main = None
for d in root.glob('smali*'):
    p = d / 'com/projectinfinity/kodi/Main.smali'
    if p.exists():
        main = p
        break
if not main:
    raise SystemExit('Main.smali missing')
mtxt = main.read_text()

helper = '''
.method private infinityRefreshWindow()V
    .locals 2
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/Main;->getWindow()Landroid/view/Window;
    move-result-object v0
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;
    move-result-object v1
    if-eqz v1, :done
    invoke-virtual {v1}, Landroid/view/View;->requestLayout()V
    invoke-virtual {v1}, Landroid/view/View;->invalidate()V
:done
    return-void
.end method
'''
if '.method private infinityRefreshWindow()V' not in mtxt:
    mtxt += '\n' + helper

# Fold inner/cover transitions and rotations land here.
if '.method public onConfigurationChanged(Landroid/content/res/Configuration;)V' not in mtxt:
    mtxt += '''
.method public onConfigurationChanged(Landroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onConfigurationChanged(Landroid/content/res/Configuration;)V
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshWindow()V
    return-void
.end method
'''

# PiP expand/collapse can change the app window without a full activity restart.
if '.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V' not in mtxt:
    mtxt += '''
.method public onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshWindow()V
    return-void
.end method
'''

# Samsung multi-window / Flex-style resizing can also remap the surface.
if '.method public onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V' not in mtxt:
    mtxt += '''
.method public onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshWindow()V
    return-void
.end method
'''

# A second safe refresh when focus returns catches the final settled Fold size.
if '.method public onWindowFocusChanged(Z)V' not in mtxt:
    mtxt += '''
.method public onWindowFocusChanged(Z)V
    .locals 0
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onWindowFocusChanged(Z)V
    if-eqz p1, :done_focus
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshWindow()V
:done_focus
    return-void
.end method
'''

main.write_text(mtxt)

print('Infinity Tablet/Fold 7.0 patch applied')
print('OLED dark is true #000000')
print('VLC-style player lock installed')
print('Fold inner/cover, PiP, multi-window and focus refresh paths installed')
print('libkodi and the proven Stable2 PiP callback are not rewritten')
