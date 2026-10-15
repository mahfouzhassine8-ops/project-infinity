#!/usr/bin/env python3
"""Build skin.infinity.diggz 1.0.5.202 from the exact locked 1.0.5.201 ZIP."""
import argparse
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED='c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5'
EXPECTED_OUT='42fc05048d3873670e1cba63a1ea44a3f2fdae0fbd20102923115db58b74ea4a'
DIALOG='skin.infinity.diggz/unified/DialogButtonMenu.xml'
ADDON='skin.infinity.diggz/addon.xml'

def sha(data): return hashlib.sha256(data).hexdigest()

def build(base: Path, out: Path):
    if sha(base.read_bytes()) != EXPECTED:
        raise ValueError('Not exact locked skin 1.0.5.201')
    with zipfile.ZipFile(base) as zin:
        if zin.testzip() is not None or len(zin.namelist()) != len(set(zin.namelist())):
            raise ValueError('Invalid parent ZIP')
        original={n:zin.read(n) for n in zin.namelist()}
        infos={n:zin.getinfo(n) for n in zin.namelist()}

    text=original[DIALOG].decode('utf-8')
    anchor='<onback>PreviousMenu</onback>'
    if text.count(anchor)!=1: raise ValueError('Power dialog onback preimage changed')
    text=text.replace(anchor,anchor+'\n  <onload>ClearProperty(Infinity.Close.InProgress,Home)</onload>',1)

    old='''        <control type="group" id="2000">
          <visible>System.ShowExitButton</visible>
          <control type="button" id="200">
            <label>CLOSE KODI</label>
            <font>InfinitySmall</font>
            <align>left</align>
            <textcolor>$VAR[InfinityLegacyText]</textcolor>
            <focusedcolor>$VAR[InfinityLegacyText]</focusedcolor>
            <onclick condition="!System.Platform.Android">Quit()</onclick>
            <disabledcolor>$VAR[InfinityLegacyDisabled]</disabledcolor>
            <left>0</left>
            <top>0</top>
            <width>100%</width>
            <height>112</height>
            <textoffsetx>84</textoffsetx>
            <textoffsety>16</textoffsety>
            <aligny>top</aligny>
            <texturefocus border="20" colordiffuse="$VAR[InfinityDrawerFocusWash]">infinity_polish/field.png</texturefocus>
            <texturenofocus border="20" colordiffuse="$VAR[InfinityDrawerQuietRow]">infinity_polish/field.png</texturenofocus>
            <onclick condition="System.Platform.Android">StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.CLOSE_KODI,,,,,,,com.projectinfinity.kodi.InfinityPowerControlActivity)</onclick>
          </control>
          <control type="image">
            <aspectratio>keep</aspectratio>
            <texture colordiffuse="$VAR[InfinityLegacyAccent]">infinity_ui/icons/power.png</texture>
            <left>22</left>
            <top>34</top>
            <width>40</width>
            <height>40</height>
          </control>
          <control type="label">
            <font>InfinityTiny</font>
            <textcolor>$VAR[InfinityLegacySecondary]</textcolor>
            <label>Exit Kodi normally</label>
            <aligny>center</aligny>
            <left>84</left>
            <top>58</top>
            <right>22</right>
            <height>34</height>
          </control>
          <width>100%</width>
          <height>112</height>
        </control>'''

    new='''        <control type="group" id="2000">
          <visible>System.ShowExitButton + String.IsEmpty(Window(Home).Property(Infinity.Close.InProgress))</visible>
          <control type="button" id="200">
            <label>CLOSE KODI</label>
            <font>InfinitySmall</font>
            <align>left</align>
            <textcolor>$VAR[InfinityLegacyText]</textcolor>
            <focusedcolor>$VAR[InfinityLegacyText]</focusedcolor>
            <onclick condition="!System.Platform.Android">Quit()</onclick>
            <disabledcolor>$VAR[InfinityLegacyDisabled]</disabledcolor>
            <left>0</left>
            <top>0</top>
            <width>100%</width>
            <height>112</height>
            <textoffsetx>84</textoffsetx>
            <textoffsety>16</textoffsety>
            <aligny>top</aligny>
            <texturefocus border="20" colordiffuse="$VAR[InfinityDrawerFocusWash]">infinity_polish/field.png</texturefocus>
            <texturenofocus border="20" colordiffuse="$VAR[InfinityDrawerQuietRow]">infinity_polish/field.png</texturenofocus>
            <onclick condition="System.Platform.Android">SetProperty(Infinity.Close.InProgress,true,Home)</onclick>
            <onclick condition="System.Platform.Android">StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.CLOSE_KODI,,,,,,,com.projectinfinity.kodi.InfinityPowerControlActivity)</onclick>
          </control>
          <control type="image">
            <aspectratio>keep</aspectratio>
            <texture colordiffuse="$VAR[InfinityLegacyAccent]">infinity_ui/icons/power.png</texture>
            <left>22</left>
            <top>34</top>
            <width>40</width>
            <height>40</height>
          </control>
          <control type="label">
            <font>InfinityTiny</font>
            <textcolor>$VAR[InfinityLegacySecondary]</textcolor>
            <label>Exit Kodi normally</label>
            <aligny>center</aligny>
            <left>84</left>
            <top>58</top>
            <right>22</right>
            <height>34</height>
          </control>
          <width>100%</width>
          <height>112</height>
        </control>
        <control type="group" id="2001">
          <visible>System.ShowExitButton + String.IsEqual(Window(Home).Property(Infinity.Close.InProgress),true)</visible>
          <control type="image">
            <left>0</left>
            <top>0</top>
            <width>100%</width>
            <height>160</height>
            <texture border="20" colordiffuse="$VAR[InfinityDrawerFocusWash]">infinity_polish/field.png</texture>
          </control>
          <control type="image">
            <aspectratio>keep</aspectratio>
            <texture colordiffuse="$VAR[InfinityLegacyAccent]">infinity_ui/icons/power.png</texture>
            <left>22</left>
            <top>58</top>
            <width>40</width>
            <height>40</height>
            <animation effect="fade" start="45" end="100" time="700" pulse="true" condition="!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)">Conditional</animation>
          </control>
          <control type="label">
            <font>InfinitySmall</font>
            <textcolor>$VAR[InfinityLegacyText]</textcolor>
            <label>CLOSING INFINITY…</label>
            <aligny>center</aligny>
            <left>84</left>
            <top>12</top>
            <right>22</right>
            <height>38</height>
          </control>
          <control type="label">
            <font>InfinityTiny</font>
            <textcolor>$VAR[InfinityLegacySecondary]</textcolor>
            <label>Please wait while your session is saved</label>
            <aligny>center</aligny>
            <left>84</left>
            <top>48</top>
            <right>22</right>
            <height>30</height>
          </control>
          <control type="label">
            <font>InfinityTiny</font>
            <textcolor>$VAR[InfinityLegacySecondary]</textcolor>
            <label>Saving → Services → Scripts → Cleanup</label>
            <aligny>center</aligny>
            <left>84</left>
            <top>80</top>
            <right>22</right>
            <height>30</height>
          </control>
          <control type="image">
            <left>84</left>
            <top>126</top>
            <right>22</right>
            <height>8</height>
            <texture colordiffuse="$VAR[InfinityLegacyField]">infinity_reference/white.png</texture>
          </control>
          <control type="image">
            <left>84</left>
            <top>126</top>
            <width>46%</width>
            <height>8</height>
            <texture colordiffuse="$VAR[InfinityLegacyAccent]">infinity_reference/white.png</texture>
            <animation effect="fade" start="55" end="100" time="650" pulse="true" condition="!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)">Conditional</animation>
          </control>
          <width>100%</width>
          <height>160</height>
        </control>'''
    if text.count(old)!=1: raise ValueError('Exact locked Close Kodi row not found')
    text=text.replace(old,new,1)
    ET.fromstring(text)

    addon=original[ADDON].decode('utf-8')
    if addon.count('version="1.0.5.201"')!=1: raise ValueError('Unexpected addon version preimage')
    addon=addon.replace('version="1.0.5.201"','version="1.0.5.202"',1)
    old_desc='Infinity 1.0.5.201 Complete Settings Audit and Polish RC1. Built from locked .200. Settings control placement, nested forms, scrolling and theme polish. APK 2103306 and Arctic Mirage 421. Device acceptance pending.'
    new_desc='Infinity 1.0.5.202 Closing Infinity UI RC1. Built from locked .201. Adds the approved live closing state to Infinity Power while preserving navigation, settings, themes, providers and playback. Pair with APK 2103328 or later. Arctic Mirage 421 retained.'
    if addon.count(old_desc)!=1: raise ValueError('Unexpected .201 description preimage')
    addon=addon.replace(old_desc,new_desc,1)
    ET.fromstring(addon)

    changes={DIALOG:text.encode(),ADDON:addon.encode()}
    with zipfile.ZipFile(out,'w') as zout:
        for name in original:
            info=infos[name]
            data=changes.get(name,original[name])
            zi=zipfile.ZipInfo(info.filename,info.date_time)
            zi.compress_type=info.compress_type;zi.comment=info.comment;zi.extra=info.extra
            zi.internal_attr=info.internal_attr;zi.external_attr=info.external_attr
            zi.create_system=info.create_system;zi.flag_bits=info.flag_bits
            zout.writestr(zi,data)

    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None: raise ValueError('Candidate ZIP CRC failure')
        if len(z.namelist())!=len(set(z.namelist())) or len(z.namelist())!=len(original):
            raise ValueError('Candidate ZIP entries changed unexpectedly')
        changed=[name for name in original if z.read(name)!=original[name]]
        if set(changed)!={DIALOG,ADDON}: raise ValueError('Unexpected skin delta: '+repr(changed))
        root=ET.fromstring(z.read(ADDON))
        if root.attrib.get('id')!='skin.infinity.diggz' or root.attrib.get('version')!='1.0.5.202':
            raise ValueError('Skin identity changed')
        dialog=z.read(DIALOG).decode()
        for token in ['CLOSING INFINITY…','Please wait while your session is saved',
                      'Saving → Services → Scripts → Cleanup',
                      'SetProperty(Infinity.Close.InProgress,true,Home)']:
            if token not in dialog: raise ValueError('Closing UI contract missing: '+token)
        if dialog.count('StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.CLOSE_KODI')!=1:
            raise ValueError('Close route changed')
        if dialog.count('FORCE CLOSE KODI')!=1:
            raise ValueError('Force Close row changed')
        for name in z.namelist():
            if (name.startswith('skin.infinity.diggz/unified/') and name.endswith('.xml')) or name==ADDON:
                ET.fromstring(z.read(name))

    digest=sha(out.read_bytes())
    if digest!=EXPECTED_OUT:
        raise ValueError('Candidate bytes differ from reviewed 1.0.5.202 proof: '+digest)
    print('PASS',out,digest)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
