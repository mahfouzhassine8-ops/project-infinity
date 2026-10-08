#!/usr/bin/env python3
"""Two-file closing acknowledgment on exact locked .201; not simulated progress."""
from pathlib import Path
import argparse,copy,hashlib,json,zipfile,xml.etree.ElementTree as ET
BASE='c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5'
DIALOG='skin.infinity.diggz/unified/DialogButtonMenu.xml'
ADDON='skin.infinity.diggz/addon.xml'

def build(base,out):
    assert hashlib.sha256(base.read_bytes()).hexdigest()==BASE
    with zipfile.ZipFile(base) as z:
        assert z.testzip() is None
        names=z.namelist();assert len(names)==len(set(names))
        data={n:z.read(n) for n in names};infos=z.infolist()
    t=data[DIALOG].decode()
    anchor='<onback>PreviousMenu</onback>';assert t.count(anchor)==1
    t=t.replace(anchor,anchor+'\n  <onload>ClearProperty(Infinity.Close.InProgress,Home)</onload>',1)
    root=ET.fromstring(t);original=next(x for x in root.iter('control') if x.get('id')=='2000')
    # Preserve existing formatting, bounds and commands everywhere outside the
    # one Close row. Locate its balanced XML span rather than reserialize dialog.
    start=t.index('        <control type="group" id="2000">')
    at=start;depth=0;end=None
    import re
    for m in re.finditer(r'</?control\b[^>]*>',t[start:]):
        if m.group().startswith('</'):depth-=1
        else:depth+=1
        if depth==0:end=start+m.end();break
    assert end is not None
    old=t[start:end]
    new=old.replace('<visible>System.ShowExitButton</visible>',
       '<visible>System.ShowExitButton + String.IsEmpty(Window(Home).Property(Infinity.Close.InProgress))</visible>',1)
    action='<onclick condition="System.Platform.Android">StartAndroidActivity('
    assert new.count(action)==1
    new=new.replace(action,'<onclick condition="System.Platform.Android">SetProperty(Infinity.Close.InProgress,true,Home)</onclick>\n            '+action,1)
    closing='''
        <control type="group" id="2001">
          <visible>System.ShowExitButton + String.IsEqual(Window(Home).Property(Infinity.Close.InProgress),true)</visible>
          <width>100%</width><height>160</height>
          <control type="image">
            <left>0</left><top>0</top><width>100%</width><height>160</height>
            <texture border="20" colordiffuse="$VAR[InfinityDrawerFocusWash]">infinity_polish/field.png</texture>
          </control>
          <control type="image">
            <left>22</left><top>52</top><width>40</width><height>40</height><aspectratio>keep</aspectratio>
            <texture colordiffuse="$VAR[InfinityLegacyAccent]">infinity_ui/icons/power.png</texture>
            <animation effect="fade" start="55" end="100" time="700" pulse="true" condition="!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)">Conditional</animation>
          </control>
          <control type="label">
            <left>84</left><top>14</top><right>22</right><height>38</height>
            <font>InfinitySmall</font><textcolor>$VAR[InfinityLegacyText]</textcolor><aligny>center</aligny>
            <label>[B]CLOSING INFINITY...[/B]</label>
          </control>
          <control type="label">
            <left>84</left><top>52</top><right>22</right><height>30</height>
            <font>InfinityTiny</font><textcolor>$VAR[InfinityLegacyText]</textcolor><aligny>center</aligny>
            <label>Please wait while your session closes safely.</label>
          </control>
          <control type="label">
            <left>84</left><top>92</top><right>22</right><height>30</height>
            <font>InfinityTiny</font><textcolor>$VAR[InfinityLegacySecondary]</textcolor><aligny>center</aligny>
            <label>Live status is available in notifications.</label>
          </control>
        </control>'''
    t=t[:start]+new+closing+t[end:]
    ET.fromstring(t)
    addon=data[ADDON].decode();assert addon.count('version="1.0.5.201"')==1
    addon=addon.replace('version="1.0.5.201"','version="1.0.5.204"',1)
    root=ET.fromstring(addon)
    assert root.attrib['id']=='skin.infinity.diggz'
    addon=re.sub(r'Infinity 1\.0\.5\.201 Complete Settings Audit and Polish RC1\.[^<]+',
      'Infinity 1.0.5.204 Closing Status Polish RC1. Built from locked .201. A clear closing acknowledgment in Infinity Power, without a false percentage or missing-font separators. Pair with APK 2103330. Device acceptance pending.',addon,count=1)
    changes={DIALOG:t.encode(),ADDON:addon.encode()}
    with zipfile.ZipFile(out,'w') as z:
        for info in infos:z.writestr(copy.copy(info),changes.get(info.filename,data[info.filename]))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None and z.namelist()==names
        changed=[n for n in names if z.read(n)!=data[n]]
        assert set(changed)==set(changes)
        before=ET.fromstring(data[DIALOG]);after=ET.fromstring(z.read(DIALOG))
        old_buttons=[c for c in before.iter('control') if c.get('type')=='button' and c.get('id')!='200']
        new_buttons=[c for c in after.iter('control') if c.get('type')=='button' and c.get('id')!='200']
        assert [ET.tostring(c) for c in old_buttons]==[ET.tostring(c) for c in new_buttons]
        old_actions=[c.text for c in before.iter('onclick')]
        new_actions=[c.text for c in after.iter('onclick') if not (c.text or '').startswith('SetProperty(Infinity.Close.InProgress')]
        assert old_actions==new_actions
        group=next(c for c in after.iter('control') if c.get('id')=='2001')
        assert all(ord(ch)<128 for l in group.iter('label') for ch in (l.text or ''))
        assert not list(group.iter('onclick')) and not any(c.get('type')=='progress' for c in group.iter('control'))
        assert '46%' not in ET.tostring(group).decode()
        ids=[c.get('id') for c in after.iter('control') if c.get('id')]
        assert len(ids)==len(set(ids)), 'Duplicate control ID'
    report=dict(candidate='1.0.5.204',addon_id='skin.infinity.diggz',parent='1.0.5.201',parent_sha256=BASE,
       sha256=hashlib.sha256(out.read_bytes()).hexdigest(),changed=changed,protected_entries=len(names)-2,
       all_other_entries_byte_identical=True,all_other_power_actions_preserved=True,fake_percentage=False,
       native_progress_claim_in_skin=False,physical_device_verified=False,locked=False)
    out.with_suffix('.proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
