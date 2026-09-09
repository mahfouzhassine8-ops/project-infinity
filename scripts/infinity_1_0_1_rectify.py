#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

SKIN='assets/addons/skin.estuary/'
LIGHT='String.IsEqual(Skin.String(Infinity.ThemePolicy),light) | [[String.IsEmpty(Skin.String(Infinity.ThemePolicy)) | String.IsEqual(Skin.String(Infinity.ThemePolicy),system)] + String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light)]'
PORTRAIT='Integer.IsLess(System.ScreenWidth,System.ScreenHeight) + String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)'
TARGETS={SKIN+'xml/Variables.xml',SKIN+'xml/Home.xml',SKIN+'xml/Includes.xml',SKIN+'xml/Includes_Home.xml'}

# Light mode follows the approved Infinity mockup: clean white/ice surfaces,
# near-black text/icons, pale-blue focus surfaces, and the existing Infinity blue accent.
# Dark mode is intentionally not recolored here: the Golden Master keeps its OLED true-black palette.
LIGHT_VALUES={
 'background':'FFF7FBFF','primary_background':'FFF7FBFF','secondary_background':'FFEAF4FC',
 'dialog_tint':'FFFFFFFF','bg_image':'FFF7FBFF','bg_overlay':'00FFFFFF','black':'FFF7FBFF',
 'white':'FF111820','grey':'FF44515E','disabled':'99616D78','text_shadow':'10000000',
 'button_focus':'FF1597E5','button_alt_focus':'801597E5','blue':'FF1597E5','border_alpha':'405B6573'
}

def set_text(parent, tag, value):
    node=parent.find(tag)
    if node is None: node=ET.SubElement(parent,tag)
    node.text=value

def append_visible(control, condition): ET.SubElement(control,'visible').text=condition

def patch_variables(data: bytes) -> bytes:
    root=ET.fromstring(data); seen=set()
    for var in root.findall('variable'):
        name=var.attrib.get('name','')
        if not name.startswith('InfinityColor_'): continue
        key=name[len('InfinityColor_'):]
        if key not in LIGHT_VALUES: continue
        for value in var.findall('value'):
            cond=value.attrib.get('condition','')
            if 'ThemePolicy),light' in cond or 'SystemTheme),light' in cond:
                value.text=LIGHT_VALUES[key]; seen.add(key); break
    missing=set(LIGHT_VALUES)-seen
    if missing: raise RuntimeError('Missing Infinity light variables: '+','.join(sorted(missing)))
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_home(data: bytes) -> bytes:
    root=ET.fromstring(data)
    fixed=next((c for c in root.iter('control') if c.attrib.get('type')=='fixedlist' and c.attrib.get('id')=='9000'),None)
    if fixed is None: raise RuntimeError('Home fixedlist 9000 missing')
    for layout_name in ('focusedlayout','itemlayout'):
        layout=fixed.find(layout_name)
        if layout is None: raise RuntimeError('Missing '+layout_name)
        label=next((c for c in layout.findall('control') if c.attrib.get('type')=='label'),None)
        if label is None: raise RuntimeError('Missing menu label in '+layout_name)
        # Use theme variables instead of hard-coded white so light mode gets black labels/icons.
        set_text(label,'textcolor','$VAR[InfinityColor_white]'); set_text(label,'focusedcolor','$VAR[InfinityColor_white]')
        append_visible(label,'!['+PORTRAIT+']')
        big=copy.deepcopy(label)
        for v in list(big.findall('visible')): big.remove(v)
        append_visible(big,PORTRAIT); set_text(big,'font','font45'); layout.append(big)
    # Light mode must expose the clean ice-white surface, not dark fanart.
    for c in root.iter('control'):
        if c.attrib.get('type')=='multiimage':
            imagepath=c.find('imagepath')
            if imagepath is not None and (imagepath.text or '').strip()=='$VAR[HomeFanartVar]':
                vis=c.find('visible')
                if vis is None: vis=ET.SubElement(c,'visible')
                vis.text='!Player.HasMedia + !['+LIGHT+']'; break
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes(data: bytes) -> bytes:
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ColoredBackgroundImages'),None)
    if inc is None: raise RuntimeError('ColoredBackgroundImages include missing')
    definition=inc.find('definition')
    if definition is None: raise RuntimeError('ColoredBackgroundImages definition missing')
    images=[c for c in definition.findall('control') if c.attrib.get('type')=='image']
    if len(images)<2: raise RuntimeError('Unexpected background image count')
    for image in images: append_visible(image,'!['+LIGHT+']')
    light=ET.Element('control',{'type':'image'})
    ET.SubElement(light,'depth').text='DepthBackground'; ET.SubElement(light,'include').text='FullScreenDimensions'; ET.SubElement(light,'aspectratio').text='scale'
    tex=ET.SubElement(light,'texture',{'colordiffuse':'FFF7FBFF'}); tex.text='white.png'; append_visible(light,LIGHT); definition.append(light)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes_home(data: bytes) -> bytes:
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ImageWidget'),None)
    if inc is None: raise RuntimeError('ImageWidget include missing')
    definition=inc.find('definition')
    textbox=next((c for c in definition.iter('control') if c.attrib.get('type')=='textbox'),None)
    if textbox is None: raise RuntimeError('ImageWidget textbox missing')
    set_text(textbox,'textcolor','$VAR[InfinityColor_white]'); append_visible(textbox,'!['+PORTRAIT+']')
    big=copy.deepcopy(textbox)
    for v in list(big.findall('visible')): big.remove(v)
    append_visible(big,PORTRAIT); set_text(big,'font','font37')
    parent=next(p for p in definition.iter() if textbox in list(p)); parent.insert(list(parent).index(textbox)+1,big)
    # Button labels also follow the active theme; no white-on-white light-mode buttons.
    for b in [c for c in definition.iter('control') if c.attrib.get('type')=='button']:
        set_text(b,'textcolor','$VAR[InfinityColor_white]'); set_text(b,'focusedcolor','$VAR[InfinityColor_white]')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def build(src: Path, out: Path, receipt: Path):
    if out.exists(): raise RuntimeError('Refusing to overwrite '+str(out))
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out,'w',allowZip64=True) as zout:
        for item in zin.infolist():
            data=zin.read(item.filename)
            if item.filename==SKIN+'xml/Variables.xml': data=patch_variables(data)
            elif item.filename==SKIN+'xml/Home.xml': data=patch_home(data)
            elif item.filename==SKIN+'xml/Includes.xml': data=patch_includes(data)
            elif item.filename==SKIN+'xml/Includes_Home.xml': data=patch_includes_home(data)
            zout.writestr(item,data)
    with zipfile.ZipFile(out) as z:
        for p in TARGETS: ET.fromstring(z.read(p))
        home=z.read(SKIN+'xml/Home.xml').decode(); includes=z.read(SKIN+'xml/Includes.xml').decode()
        if 'effect="zoom" center="231,540" start="100" end="114"' in home: raise RuntimeError('Bad whole-menu portrait zoom survived')
        if 'font45' not in home or 'FFF7FBFF' not in includes: raise RuntimeError('Rectification markers missing')
    receipt.write_text(json.dumps({'base':src.name,'changed':sorted(TARGETS),'engine_changed':False,'whole_layout_zoom':False,'dark_mode':'OLED Golden Master unchanged','light_background':'FFF7FBFF','light_text':'FF111820','accent':'FF1597E5','portrait':'font-only'},indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(); p.add_argument('src',type=Path); p.add_argument('out',type=Path); p.add_argument('receipt',type=Path)
    a=p.parse_args(); build(a.src,a.out,a.receipt)
if __name__=='__main__': main()
