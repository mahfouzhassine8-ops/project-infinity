#!/usr/bin/env python3
"""Build a complete, hash-pinned .215-derived .217 skin and non-patching helper."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE = Path(__file__).resolve().parents[1]
ADDON = HERE / 'addons/script.infinity.rails'
sys.path.insert(0, str(ADDON/'resources'))
sys.path.insert(0, str(HERE/'tools'))
import baseline_integration as legacy

BASE_SHA = legacy.BASE_SHA
PROFILES = legacy.PROFILES
CONTROLS = (9200, 8820, 8720, 19600)
ROOT = 'skin.infinity.diggz/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def xml(root):
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)+b'\n'


def scope(control):
    return ('Window.IsActive(home) + System.AddonIsEnabled(script.infinity.rails) + '
            'String.IsEqual(Window(Home).Property(Infinity.Rails.ContextControl),'+str(control)+') + '
            'String.IsEqual(Container('+str(control)+').ListItem.Property(Infinity.Rails.Item),true)')


OWNED = ' | '.join('['+scope(c)+']' for c in CONTROLS)


def home(raw):
    text = legacy.patch_home(raw).decode()
    for control in CONTROLS:
        start = text.index('id="'+str(control)+'">')+len('id="'+str(control)+'">')
        integration = ('\n        <onfocus>SetProperty(Infinity.Rails.ContextControl,'+str(control)+',home)</onfocus>'
                       '\n        <onunfocus>ClearProperty(Infinity.Rails.ContextControl,home)</onunfocus>')
        text = text[:start]+integration+text[start:]
    return text.encode()


def context(raw):
    tree = ET.fromstring(raw)
    old = tree.find('controls')
    original = copy.deepcopy(old)
    tree.remove(old)
    # Keep all other context menus' original animations and control semantics.
    for node in tree.findall('include')+tree.findall('animation'):
        existing = node.get('condition')
        node.set('condition', ('['+existing+'] + ' if existing else '')+'!['+OWNED+']')
    for control in CONTROLS:
        tag = ET.SubElement(tree, 'onload', {'condition':scope(control)})
        tag.text = ('RunScript(script.infinity.rails,options,'
                    '$INFO[Container('+str(control)+').ListItem.Property(Infinity.Rails.Section)],'
                    '$INFO[Container('+str(control)+').ListItem.Property(Infinity.Rails.Key)])')
    controls = ET.SubElement(tree, 'controls')
    ET.SubElement(controls, 'include', {'content':'InfinityRailsLegacyContext', 'condition':'!['+OWNED+']'})
    return xml(tree), original


def includes(raw, original):
    tree = ET.fromstring(legacy.rails_include(raw))
    for value in tree.findall("variable[@name='InfinityRailsContent']/value"):
        if value.text:
            section = 'movies' if 'section=movies&' in value.text else 'tvshows'
            value.text = value.text.replace('Infinity.Rails.Revision', 'Infinity.Rails.'+section+'.Revision')
    inc = ET.SubElement(tree, 'include', {'name':'InfinityRailsLegacyContext'})
    for node in original:
        inc.append(copy.deepcopy(node))
    # Same approved theme tokens, without a frozen Python color snapshot.
    for name, light, dark, oled in [
        ('Surface','F7FFFFFF','F20A111A','FF000000'),
        ('Text','FF102237','FFF2F6FB','FFFFFFFF'),
        ('Secondary','FF50647A','FF9EB2C4','FFA5B7C8'),
        ('Field','FFEAF1F7','F0131D29','FF000000'),
        ('Border','FFB8C9D8','FF29445C','FF223A50'),
        ('Accent','FF006DCB','FF24A8FF','FF24A8FF'),
    ]:
        var = ET.SubElement(tree, 'variable', {'name':'InfinityRails'+name})
        ET.SubElement(var, 'value', {'condition':'String.IsEqual(Window(Home).Property(Infinity.SystemTheme),OLED)'}).text=oled
        ET.SubElement(var, 'value', {'condition':'[String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light) | [String.IsEmpty(Window(Home).Property(Infinity.SystemTheme)) + String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),light)]]'}).text=light
        ET.SubElement(var, 'value').text=dark
    for width in (192, 320, 480, 720, 900):
        for rows in range(1,9):
            inc = ET.SubElement(tree, "include", {"name":"InfinityRailsShape%dRows%d" % (width,rows)})
            inc.append(dialog_group(width, rows))
    return xml(tree)


DIALOG_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<window type="dialog">
  <defaultcontrol always="true">6</defaultcontrol>
  <controls>
    <control type="image" id="999">
      <left>1</left><top>1</top><width>1</width><height>1</height>
      <texture border="24" colordiffuse="$VAR[InfinityRailsSurface]">infinity_glass/surface.png</texture>
      <bordertexture border="24" colordiffuse="$VAR[InfinityRailsBorder]">infinity_glass/rim.png</bordertexture><bordersize>2</bordersize>
    </control>
    <control type="label" id="1">
      <left>1</left><top>1</top><width>1</width><height>1</height>
      <font>InfinitySmall</font><aligny>center</aligny><textcolor>$VAR[InfinityRailsText]</textcolor>
      <label>$INFO[Window.Property(Infinity.Rails.Title)]</label><scroll>true</scroll>
    </control>
    <control type="label" id="3">
      <left>1</left><top>1</top><width>1</width><height>1</height>
      <font>InfinitySmall</font><aligny>center</aligny><textcolor>$VAR[InfinityRailsSecondary]</textcolor>
      <label>$INFO[Window.Property(Infinity.Rails.Subtitle)]</label><scroll>true</scroll>
    </control>
    <control type="button" id="2">
      <left>1</left><top>1</top><width>1</width><height>1</height><label />
      <texturefocus colordiffuse="$VAR[InfinityRailsAccent]">infinity_legacy/close_focus.png</texturefocus>
      <texturenofocus colordiffuse="$VAR[InfinityRailsText]">infinity_legacy/close.png</texturenofocus>
      <onleft>6</onleft><onright>6</onright><onup>6</onup><ondown>6</ondown>
    </control>
    <control type="list" id="6">
      <left>1</left><top>1</top><width>1</width><height>1</height>
      <orientation>vertical</orientation><scrolltime>120</scrolltime>
      <onleft>2</onleft><onright>2</onright><onup>6</onup><ondown>6</ondown>
      <itemlayout width="100%" height="82">
        <control type="image"><left>0</left><top>3</top><width>100%</width><height>76</height><texture border="16" colordiffuse="$VAR[InfinityRailsField]">infinity_glass/field.png</texture></control>
        <control type="label"><left>24</left><right>24</right><top>3</top><height>76</height><font>InfinityBody</font><aligny>center</aligny><textcolor>$VAR[InfinityRailsText]</textcolor><label>$INFO[ListItem.Label]</label><scroll>true</scroll></control>
      </itemlayout>
      <focusedlayout width="100%" height="82">
        <control type="image"><left>0</left><top>3</top><width>100%</width><height>76</height><texture border="16" colordiffuse="$VAR[InfinityRailsField]">infinity_glass/field.png</texture><bordertexture border="16" colordiffuse="$VAR[InfinityRailsAccent]">infinity_glass/rim.png</bordertexture><bordersize>2</bordersize></control>
        <control type="label"><left>24</left><right>24</right><top>3</top><height>76</height><font>InfinityBody</font><aligny>center</aligny><textcolor>$VAR[InfinityRailsText]</textcolor><label>$INFO[ListItem.Label]</label><scroll>true</scroll></control>
      </focusedlayout>
    </control>
  </controls>
  <animation effect="fade" start="0" end="100" time="190" condition="!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)">WindowOpen</animation>
  <animation effect="fade" start="100" end="0" time="140" condition="!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)">WindowClose</animation>
</window>
'''.encode()


def dialog_group(width, rows):
    original = ET.fromstring(DIALOG_TEMPLATE)
    group = ET.Element('control', {'type':'group', 'id':'9900'})
    for tag, value in [('centerleft','50%'),('centertop','50%'),('width',str(width)),('height',str(144+rows*82))]:
        ET.SubElement(group,tag).text=value
    for control in original.find('controls'):
        group.append(copy.deepcopy(control))
    for cid,x,y,w,h in [(999,0,0,width,144+rows*82),(1,24,16,width-112,48),(3,24,64,width-48,38),(2,width-72,14,52,52),(6,16,120,width-32,rows*82)]:
        control=group.find("control[@id='%d']" % cid)
        for tag,value in [('left',x),('top',y),('width',w),('height',h)]:control.find(tag).text=str(value)
    return group


def dialog_xml():
    tree=ET.fromstring(DIALOG_TEMPLATE)
    controls=tree.find('controls');controls.clear()
    for width in (192,320,480,720,900):
        for rows in range(1,9):
            ET.SubElement(controls,'include',{'content':'InfinityRailsShape%dRows%d' % (width,rows),'condition':'String.IsEqual(Window(Home).Property(Infinity.Rails.DialogShape),%dx%d)' % (width,rows)})
    return xml(tree)


DIALOG=dialog_xml()


def build(baseline, output):
    if sha(baseline.read_bytes()) != BASE_SHA:
        raise ValueError('Source must be the exact verified .215 ZIP; no downgrade or reconstruction.')
    with ZipFile(baseline) as z:
        before={n[len(ROOT):]:z.read(n) for n in z.namelist() if n.startswith(ROOT) and not n.endswith('/')}
    after=dict(before)
    for profile in PROFILES:
        after[profile+'/Home.xml']=home(before[profile+'/Home.xml'])
        old_context=before[profile+'/DialogContextMenu.xml']
        after[profile+'/DialogContextMenu.xml'], original=context(old_context)
        source=before.get(profile+'/script-skinshortcuts-includes.xml', before['16x9/script-skinshortcuts-includes.xml'])
        after[profile+'/Includes_InfinityRails.xml']=includes(source, original)
        old=before.get(profile+'/Includes.xml',before['16x9/Includes.xml'])
        after[profile+'/Includes.xml']=old.replace(b'<includes>', b'<includes>\n  <include file="Includes_InfinityRails.xml"/>',1)
        after[profile+'/InfinityRailsOptions.xml']=DIALOG
    addon=before['addon.xml'].decode().replace('version="1.0.5.215"','version="1.0.5.219"',1)
    # Helper is required, with its separate installation disclosed. Kodi cannot
    # fetch an unpublished dependency merely because a ZIP declares it.
    addon=addon.replace('</requires>','  <import addon="script.infinity.rails" version="0.2.1"/>\n  </requires>',1)
    addon=re.sub(r'<description lang="en_GB">.*?</description>', '<description lang="en_GB">Infinity 1.0.5.219 Custom Rails RC3 TEST. Complete .215-derived skin update; requires Rails helper 0.2.1. Saved .216 rail choices are retained. Physical-device acceptance pending. Not locked.</description>', addon, count=1, flags=re.S)
    after['addon.xml']=addon.encode()
    for name in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
        data=json.loads(before[name]);data['skin_version']='1.0.5.219';data['candidate']=219;data['candidate_locked']=False
        for key in ('version','candidate_version'):
            if key in data:data[key]='1.0.5.219'
        if 'candidate_name' in data:data['candidate_name']='Custom Add-on Rails RC3 TEST'
        data['custom_addon_rails_219']={'base_version':'1.0.5.215','base_sha256':BASE_SHA,'source_record_commit':'85b1305ef7a220dd23aaeb40c7d38150b8da4a92','reconciled_rc2_helper_sha256':'b0d0b293cc66d937cb82dd6c8ac9e97956e67f88efec10e764d4631540f7a9da','helper_version':'0.2.1','locked':False,'physical_device_verified':False}
        for path in data.get('protected_files',{}):
            if path in after and after[path]!=before.get(path):data['protected_files'][path]=sha(after[path])
        after[name]=(json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
    output.mkdir(parents=True,exist_ok=True)
    skin=output/'skin.infinity.diggz-1.0.5.219-Custom-Rails-RC3-TEST.zip'
    package(skin, {ROOT+n:b for n,b in after.items()})
    fallback=ADDON/'resources/skins/Default/1080i/InfinityRailsOptions.xml'
    fallback.parent.mkdir(parents=True,exist_ok=True);fallback.write_bytes(DIALOG)
    helper=output/'script.infinity.rails-0.2.1-Custom-Rails-RC3-TEST.zip'
    files={}
    for p in ADDON.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo'):
            files[ADDON.name+'/'+p.relative_to(ADDON).as_posix()]=p.read_bytes()
    package(helper,files)
    changed=[p for p in before if after[p]!=before[p]]
    report={'base_sha256':BASE_SHA,'base_record_commit':'85b1305ef7a220dd23aaeb40c7d38150b8da4a92','rc2_record_commit':'faae58d7594b8be1e423e119ddd1e1c9839767fd','base_version':'1.0.5.215','candidate_version':'1.0.5.219','helper_version':'0.2.1','changed_existing':changed,'added':sorted(set(after)-set(before)),'deleted':sorted(set(before)-set(after)),'unchanged_count':len(before)-len(changed),'original_count':len(before),'profiles':PROFILES,'modes':dict(zip(('normal','compact','twopane','cinema'),CONTROLS)),'apk_changed':False,'physical_device_verified':False,'locked':False,'packages':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in (skin,helper)}}
    (HERE/'evidence/preservation.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'evidence/baseline-file-sha256.json').write_text(json.dumps({n:sha(b) for n,b in before.items()},sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('changed_existing','added','profiles')},indent=2))
    return before,after


def package(path, entries):
    with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for name, data in sorted(entries.items()):
            zi=ZipInfo(name,date_time=(2026,10,14,0,0,0));zi.compress_type=ZIP_DEFLATED;zi.external_attr=0o100644<<16
            z.writestr(zi,data,compress_type=ZIP_DEFLATED,compresslevel=9)
    with ZipFile(path) as z:
        if z.testzip():raise ValueError('ZIP CRC failure')
        for name in z.namelist():
            if name.endswith('.xml'):ET.fromstring(z.read(name))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('baseline',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    build(args.baseline,args.output)
