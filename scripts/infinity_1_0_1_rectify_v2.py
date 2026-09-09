#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, io, json, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

SKIN='assets/addons/skin.estuary/'
LIGHT='String.IsEqual(Skin.String(Infinity.ThemePolicy),light) | [[String.IsEmpty(Skin.String(Infinity.ThemePolicy)) | String.IsEqual(Skin.String(Infinity.ThemePolicy),system)] + String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light)]'
PORTRAIT='Integer.IsLess(System.ScreenWidth,System.ScreenHeight) + String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)'
LIGHT_VALUES={
 'background':'FFF7FBFF','primary_background':'FFF7FBFF','secondary_background':'FFEAF4FC',
 'dialog_tint':'FFFFFFFF','bg_image':'FFF7FBFF','bg_overlay':'00FFFFFF','black':'FFF7FBFF',
 'white':'FF111820','grey':'FF44515E','disabled':'99616D78','text_shadow':'10000000',
 'button_focus':'FF1597E5','button_alt_focus':'801597E5','blue':'FF1597E5','border_alpha':'405B6573'
}
TARGET_XML={
 SKIN+'xml/Variables.xml',SKIN+'xml/Home.xml',SKIN+'xml/Includes.xml',SKIN+'xml/Includes_Home.xml',
 SKIN+'xml/VideoOSD.xml',SKIN+'xml/DialogSeekBar.xml'
}

def set_text(parent, tag, value):
    node=parent.find(tag)
    if node is None: node=ET.SubElement(parent,tag)
    node.text=value

def append_visible(control, condition): ET.SubElement(control,'visible').text=condition

def patch_variables(data):
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

def patch_home(data):
    root=ET.fromstring(data)
    fixed=next((c for c in root.iter('control') if c.attrib.get('type')=='fixedlist' and c.attrib.get('id')=='9000'),None)
    if fixed is None: raise RuntimeError('Home fixedlist 9000 missing')
    for layout_name in ('focusedlayout','itemlayout'):
        layout=fixed.find(layout_name)
        if layout is None: raise RuntimeError('Missing '+layout_name)
        label=next((c for c in layout.findall('control') if c.attrib.get('type')=='label'),None)
        if label is None: raise RuntimeError('Missing menu label in '+layout_name)
        set_text(label,'textcolor','$VAR[InfinityColor_white]'); set_text(label,'focusedcolor','$VAR[InfinityColor_white]')
        append_visible(label,'!['+PORTRAIT+']')
        big=copy.deepcopy(label)
        for v in list(big.findall('visible')): big.remove(v)
        append_visible(big,PORTRAIT); set_text(big,'font','font45'); layout.append(big)
    for c in root.iter('control'):
        if c.attrib.get('type')=='multiimage':
            imagepath=c.find('imagepath')
            if imagepath is not None and (imagepath.text or '').strip()=='$VAR[HomeFanartVar]':
                vis=c.find('visible')
                if vis is None: vis=ET.SubElement(c,'visible')
                vis.text='!Player.HasMedia + !['+LIGHT+']'; break
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ColoredBackgroundImages'),None)
    if inc is None: raise RuntimeError('ColoredBackgroundImages include missing')
    container=inc.find('definition') or inc
    images=[c for c in container.findall('control') if c.attrib.get('type')=='image']
    if len(images)<2: raise RuntimeError('Unexpected background image count')
    for image in images: append_visible(image,'!['+LIGHT+']')
    light=ET.Element('control',{'type':'image'})
    ET.SubElement(light,'depth').text='DepthBackground'; ET.SubElement(light,'include').text='FullScreenDimensions'; ET.SubElement(light,'aspectratio').text='scale'
    tex=ET.SubElement(light,'texture',{'colordiffuse':'FFF7FBFF'}); tex.text='white.png'; append_visible(light,LIGHT); container.append(light)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes_home(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ImageWidget'),None)
    if inc is None: raise RuntimeError('ImageWidget include missing')
    definition=inc.find('definition')
    if definition is None: raise RuntimeError('ImageWidget definition missing')
    textbox=next((c for c in definition.iter('control') if c.attrib.get('type')=='textbox'),None)
    if textbox is None: raise RuntimeError('ImageWidget textbox missing')
    set_text(textbox,'textcolor','$VAR[InfinityColor_white]'); append_visible(textbox,'!['+PORTRAIT+']')
    big=copy.deepcopy(textbox)
    for v in list(big.findall('visible')): big.remove(v)
    append_visible(big,PORTRAIT); set_text(big,'font','font37')
    parent=next(p for p in definition.iter() if textbox in list(p)); parent.insert(list(parent).index(textbox)+1,big)
    for b in [c for c in definition.iter('control') if c.attrib.get('type')=='button']:
        set_text(b,'textcolor','$VAR[InfinityColor_white]'); set_text(b,'focusedcolor','$VAR[InfinityColor_white]')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_player_xml(data):
    s=data.decode('utf-8')
    s=s.replace('colordiffuse="button_focus"','colordiffuse="$VAR[InfinityColor_button_focus]"')
    s=s.replace('colordiffuse="white"','colordiffuse="$VAR[InfinityColor_white]"')
    s=s.replace('<textcolor>white</textcolor>','<textcolor>$VAR[InfinityColor_white]</textcolor>')
    s=s.replace('<focusedcolor>white</focusedcolor>','<focusedcolor>$VAR[InfinityColor_white]</focusedcolor>')
    ET.fromstring(s.encode())
    return s.encode()

def _font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        try: return ImageFont.truetype(p,size)
        except OSError: pass
    return ImageFont.load_default()

def _symbol_mask(src_icon):
    im=Image.open(io.BytesIO(src_icon)).convert('RGBA')
    px=im.load(); mask=Image.new('L',im.size,0); mp=mask.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=px[x,y]
            if a and r>190 and g>190 and b>190: mp[x,y]=a
    return mask

def _gradient_symbol(mask):
    w,h=mask.size; grad=Image.new('RGBA',(w,h))
    gp=grad.load()
    for x in range(w):
        t=x/max(1,w-1)
        if t<.55:
            u=t/.55; c=(int(24+(0-24)*u),int(106+(161-106)*u),int(255+(255-255)*u),255)
        else:
            u=(t-.55)/.45; c=(int(0+(45-0)*u),int(161+(214-161)*u),int(255+(255-255)*u),255)
        for y in range(h): gp[x,y]=c
    grad.putalpha(mask)
    return grad

def make_icon(src_icon,size,bg=(10,12,16,255)):
    mask=_symbol_mask(src_icon); sym=_gradient_symbol(mask)
    canvas=Image.new('RGBA',(512,512),(0,0,0,0)); d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((0,0,511,511),radius=88,fill=bg)
    canvas.alpha_composite(sym)
    return canvas.resize((size,size),Image.Resampling.LANCZOS)

def make_splash(src_icon):
    mask=_symbol_mask(src_icon); sym=_gradient_symbol(mask).resize((420,420),Image.Resampling.LANCZOS)
    out=Image.new('RGB',(1920,1080),(0,0,0)); out.paste(sym,(750,255),sym)
    d=ImageDraw.Draw(out); f=_font(86); word='I N F I N I T Y'; box=d.textbbox((0,0),word,font=f); x=(1920-(box[2]-box[0]))//2
    d.text((x,700),word,font=f,fill=(245,248,252))
    return out

def image_bytes(im,fmt,**kw):
    b=io.BytesIO(); im.save(b,fmt,**kw); return b.getvalue()

def build(src,out,receipt):
    replacements={}
    with zipfile.ZipFile(src) as zin:
        source_icon=zin.read(SKIN+'media/infinity/icon.png')
        replacements[SKIN+'media/infinity/icon.png']=image_bytes(make_icon(source_icon,512),'PNG')
        for n in (16,32,48,80,120,256):
            replacements[f'assets/media/icon{n}x{n}.png']=image_bytes(make_icon(source_icon,n),'PNG')
        replacements['assets/media/splash.jpg']=image_bytes(make_splash(source_icon),'JPEG',quality=92)
        with zipfile.ZipFile(out,'w',allowZip64=True) as zout:
            for item in zin.infolist():
                data=zin.read(item.filename)
                if item.filename==SKIN+'xml/Variables.xml': data=patch_variables(data)
                elif item.filename==SKIN+'xml/Home.xml': data=patch_home(data)
                elif item.filename==SKIN+'xml/Includes.xml': data=patch_includes(data)
                elif item.filename==SKIN+'xml/Includes_Home.xml': data=patch_includes_home(data)
                elif item.filename in (SKIN+'xml/VideoOSD.xml',SKIN+'xml/DialogSeekBar.xml'): data=patch_player_xml(data)
                if item.filename in replacements: data=replacements[item.filename]
                zout.writestr(item,data)
    with zipfile.ZipFile(out) as z:
        for p in TARGET_XML: ET.fromstring(z.read(p))
        if 'FFF7FBFF' not in z.read(SKIN+'xml/Includes.xml').decode(): raise RuntimeError('Light surface missing')
        if 'font45' not in z.read(SKIN+'xml/Home.xml').decode(): raise RuntimeError('Portrait font marker missing')
        if '$VAR[InfinityColor_button_focus]' not in z.read(SKIN+'xml/VideoOSD.xml').decode(): raise RuntimeError('Player theme marker missing')
    receipt.write_text(json.dumps({
      'base':src.name,'engine_changed':False,'dark_mode':'OLED true black preserved','light_mode':'ice white + dark text',
      'portrait':'font-only responsive enlargement','player_osd':'theme-aware controls; video canvas unchanged',
      'branding':'gradient Infinity icon + OLED splash','same_signing_identity_required':True
    },indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(); p.add_argument('src',type=Path); p.add_argument('out',type=Path); p.add_argument('receipt',type=Path)
    a=p.parse_args(); build(a.src,a.out,a.receipt)
if __name__=='__main__': main()
