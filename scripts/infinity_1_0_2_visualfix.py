#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, io, json, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

SKIN='assets/addons/skin.estuary/'
LIGHT='String.IsEqual(Skin.String(Infinity.ThemePolicy),light) | [[String.IsEmpty(Skin.String(Infinity.ThemePolicy)) | String.IsEqual(Skin.String(Infinity.ThemePolicy),system)] + String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light)]'
MOBILE='String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)'
PORTRAIT=f'Integer.IsLess(System.ScreenWidth,System.ScreenHeight) + {MOBILE}'
MOBILE_LANDSCAPE=f'Integer.IsGreater(System.ScreenWidth,System.ScreenHeight) + {MOBILE}'
NON_MOBILE=f'![{MOBILE}]'

LIGHT_VALUES={
 'background':'FFF7FBFF','primary_background':'FFF7FBFF','secondary_background':'FFEAF4FC',
 'dialog_tint':'FFFFFFFF','bg_image':'FFF7FBFF','bg_overlay':'00FFFFFF','black':'FFF7FBFF',
 'white':'FF111820','grey':'FF44515E','disabled':'A0667481','text_shadow':'10000000',
 'button_focus':'FF1597E5','button_alt_focus':'331597E5','blue':'FF1597E5','border_alpha':'405B6573'
}
TARGET_XML={
 SKIN+'xml/Variables.xml',SKIN+'xml/Home.xml',SKIN+'xml/Includes.xml',SKIN+'xml/Includes_Home.xml',
 SKIN+'xml/VideoOSD.xml',SKIN+'xml/DialogSeekBar.xml',SKIN+'xml/Font.xml'
}

def set_text(parent, tag, value):
    node=parent.find(tag)
    if node is None: node=ET.SubElement(parent,tag)
    node.text=value

def set_visible(control, cond):
    for v in list(control.findall('visible')): control.remove(v)
    ET.SubElement(control,'visible').text=cond

def append_visible(control, cond): ET.SubElement(control,'visible').text=cond

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

def patch_fonts(data):
    root=ET.fromstring(data)
    wanted={
      'InfinityMenu':36,
      'InfinityMenuPortrait':40,
      'InfinityBody':30,
      'InfinityBodyCompact':24,
      'InfinityButton':26,
      'InfinityButtonCompact':23,
    }
    for fs in root.findall('fontset'):
        existing={f.findtext('name') for f in fs.findall('font')}
        first=fs.find('font/filename')
        filename=first.text if first is not None and first.text else 'NotoSans-Regular.ttf'
        for name,size in wanted.items():
            if name in existing: continue
            f=ET.SubElement(fs,'font')
            ET.SubElement(f,'name').text=name
            ET.SubElement(f,'filename').text=filename
            ET.SubElement(f,'size').text=str(size)
            if 'BodyCompact' in name:
                ET.SubElement(f,'linespacing').text='1.08'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_home(data):
    root=ET.fromstring(data)
    fixed=next((c for c in root.iter('control') if c.attrib.get('type')=='fixedlist' and c.attrib.get('id')=='9000'),None)
    if fixed is None: raise RuntimeError('Home fixedlist 9000 missing')
    for layout_name in ('focusedlayout','itemlayout'):
        layout=fixed.find(layout_name)
        if layout is None: raise RuntimeError('Missing '+layout_name)
        labels=[c for c in layout.findall('control') if c.attrib.get('type')=='label']
        if not labels: raise RuntimeError('Missing menu label in '+layout_name)
        base=labels[0]
        for extra in labels[1:]: layout.remove(extra)
        set_text(base,'left','104'); set_text(base,'width','338'); set_text(base,'font','InfinityMenu')
        set_text(base,'textcolor','$VAR[InfinityColor_white]'); set_text(base,'focusedcolor','$VAR[InfinityColor_white]')
        set_visible(base,f'![{PORTRAIT}]')
        portrait=copy.deepcopy(base); set_visible(portrait,PORTRAIT); set_text(portrait,'font','InfinityMenuPortrait'); layout.append(portrait)
        imgs=[c for c in layout.iter('control') if c.attrib.get('type')=='image']
        for img in imgs:
            tex=img.find('texture')
            if tex is not None and '$INFO[ListItem.Art(thumb)]' in (tex.text or ''):
                tex.attrib['colordiffuse']='$VAR[InfinityColor_white]'
        if layout_name=='focusedlayout':
            for img in layout.iter('control'):
                tex=img.find('texture') if img.attrib.get('type')=='image' else None
                if tex is not None and (tex.text or '')=='lists/focus.png':
                    tex.attrib['colordiffuse']='$VAR[InfinityColor_button_alt_focus]'
                    break
            marker=ET.Element('control',{'type':'image'})
            ET.SubElement(marker,'left').text='0'; ET.SubElement(marker,'top').text='0'; ET.SubElement(marker,'width').text='7'; ET.SubElement(marker,'height').text='95'
            t=ET.SubElement(marker,'texture',{'colordiffuse':'$VAR[InfinityColor_blue]'}); t.text='white.png'
            layout.insert(1,marker)
    for c in root.iter('control'):
        if c.attrib.get('type')=='multiimage':
            imagepath=c.find('imagepath')
            if imagepath is not None and (imagepath.text or '').strip()=='$VAR[HomeFanartVar]':
                vis=c.find('visible')
                if vis is None: vis=ET.SubElement(c,'visible')
                vis.text='!Player.HasMedia + !['+LIGHT+']'; break
    for group in root.iter('control'):
        if group.attrib.get('type')!='group': continue
        children=list(group)
        for idx,c in enumerate(children):
            if c.attrib.get('type')!='image': continue
            tex=c.find('texture')
            if tex is None or (tex.text or '')!='infinity/icon.png': continue
            dark=copy.deepcopy(c); set_visible(dark,'!['+LIGHT+']'); dark.find('texture').text='infinity/logo-dark.png'
            light=copy.deepcopy(c); set_visible(light,LIGHT); light.find('texture').text='infinity/logo-light.png'
            group.remove(c); group.insert(idx,dark); group.insert(idx+1,light)
            break
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ColoredBackgroundImages'),None)
    if inc is None: raise RuntimeError('ColoredBackgroundImages include missing')
    container=inc.find('definition') or inc
    images=[c for c in container.findall('control') if c.attrib.get('type')=='image']
    if len(images)<2: raise RuntimeError('Unexpected background image count')
    for x in list(container.findall('control')):
        tex=x.find('texture')
        if tex is not None and tex.attrib.get('colordiffuse')=='FFF7FBFF' and (tex.text or '')=='white.png': container.remove(x)
    for image in [c for c in container.findall('control') if c.attrib.get('type')=='image']: append_visible(image,'!['+LIGHT+']')
    light=ET.Element('control',{'type':'image'}); ET.SubElement(light,'depth').text='DepthBackground'; ET.SubElement(light,'include').text='FullScreenDimensions'; ET.SubElement(light,'aspectratio').text='scale'
    tex=ET.SubElement(light,'texture',{'colordiffuse':'FFF7FBFF'}); tex.text='white.png'; append_visible(light,LIGHT); container.append(light)
    panel=next((i for i in root.findall('include') if i.attrib.get('name')=='ContentPanel'),None)
    if panel is None: raise RuntimeError('ContentPanel include missing')
    definition=panel.find('definition') or panel
    pimgs=[c for c in definition.findall('control') if c.attrib.get('type')=='image']
    if not pimgs: raise RuntimeError('ContentPanel image missing')
    original=pimgs[0]
    for x in pimgs[1:]:
        tx=x.find('texture')
        if tx is not None and (tx.text or '')=='white.png': definition.remove(x)
    set_visible(original,'!['+LIGHT+']')
    lp=copy.deepcopy(original); set_visible(lp,LIGHT)
    lpt=lp.find('texture'); lpt.text='white.png'; lpt.attrib['colordiffuse']='FFF7FBFF'; lpt.attrib.pop('flipx',None)
    definition.append(lp)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes_home(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ImageWidget'),None)
    if inc is None: raise RuntimeError('ImageWidget include missing')
    definition=inc.find('definition')
    if definition is None: raise RuntimeError('ImageWidget definition missing')
    gl=next((c for c in definition.iter('control') if c.attrib.get('type')=='grouplist' and (c.attrib.get('id') or '').endswith('577')),None)
    if gl is None: raise RuntimeError('ImageWidget vertical grouplist missing')
    set_text(gl,'left','24'); set_text(gl,'right','24')
    textboxes=[c for c in gl.findall('control') if c.attrib.get('type')=='textbox']
    if not textboxes: raise RuntimeError('ImageWidget textbox missing')
    base=textboxes[0]
    for extra in textboxes[1:]: gl.remove(extra)
    set_text(base,'font','InfinityBody'); set_text(base,'textcolor','$VAR[InfinityColor_white]'); set_visible(base,NON_MOBILE)
    compact=copy.deepcopy(base); set_text(compact,'font','InfinityBodyCompact'); set_text(compact,'height','auto'); set_visible(compact,MOBILE_LANDSCAPE); gl.insert(list(gl).index(base)+1,compact)
    portrait=copy.deepcopy(base); set_text(portrait,'font','InfinityBody'); set_visible(portrait,PORTRAIT); gl.insert(list(gl).index(compact)+1,portrait)
    for b in [c for c in definition.iter('control') if c.attrib.get('type')=='button']:
        set_text(b,'height','96'); set_text(b,'font','InfinityButton'); set_text(b,'textoffsetx','28')
        set_text(b,'textcolor','$VAR[InfinityColor_white]'); set_text(b,'focusedcolor','FFFFFFFF')
        tf=b.find('texturefocus')
        if tf is None: tf=ET.SubElement(b,'texturefocus')
        tf.text='buttons/dialogbutton-fo.png'; tf.attrib['border']='23'; tf.attrib['colordiffuse']='$VAR[InfinityColor_button_focus]'
        tn=b.find('texturenofocus')
        if tn is None: tn=ET.SubElement(b,'texturenofocus')
        tn.text='buttons/dialogbutton-fo.png'; tn.attrib['border']='23'; tn.attrib['colordiffuse']='$VAR[InfinityColor_secondary_background]'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_player_xml(data):
    s=data.decode('utf-8')
    s=s.replace('colordiffuse="$VAR[InfinityColor_button_focus]"','colordiffuse="$VAR[InfinityColor_blue]"')
    s=s.replace('colordiffuse="button_focus"','colordiffuse="$VAR[InfinityColor_blue]"')
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
    im=Image.open(io.BytesIO(src_icon)).convert('RGBA'); px=im.load(); mask=Image.new('L',im.size,0); mp=mask.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=px[x,y]
            if a and r>180 and g>180 and b>180: mp[x,y]=a
    bbox=mask.getbbox()
    if not bbox: raise RuntimeError('Infinity symbol mask missing')
    return mask.crop(bbox)

def _gradient_symbol(mask):
    w,h=mask.size; grad=Image.new('RGBA',(w,h)); gp=grad.load()
    for x in range(w):
        t=x/max(1,w-1)
        if t<.50:
            u=t/.50; c=(int(15+(0-15)*u),int(94+(152-94)*u),255,255)
        else:
            u=(t-.50)/.50; c=(int(0+(45)*u),int(152+(215-152)*u),255,255)
        for y in range(h): gp[x,y]=c
    grad.putalpha(mask); return grad

def make_launcher(src,size=512):
    mask=_symbol_mask(src); sym=_gradient_symbol(mask)
    target_w=int(size*.55); scale=target_w/sym.width; sym=sym.resize((target_w,int(sym.height*scale)),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(size,size),(12,14,19,255)); d=ImageDraw.Draw(out); d.rounded_rectangle((0,0,size-1,size-1),radius=int(size*.18),fill=(12,14,19,255))
    out.alpha_composite(sym,((size-sym.width)//2,(size-sym.height)//2-3)); return out

def make_horizontal_logo(src,light=False):
    mask=_symbol_mask(src); sym=_gradient_symbol(mask); sym=sym.resize((190,int(190*sym.height/sym.width)),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(700,180),(0,0,0,0)); out.alpha_composite(sym,(15,(180-sym.height)//2))
    d=ImageDraw.Draw(out); f=_font(54); word='I N F I N I T Y'; color=(15,22,30,255) if light else (245,248,252,255)
    d.text((230,58),word,font=f,fill=color); return out

def make_splash(src,light=False,size=(1920,1080)):
    mask=_symbol_mask(src); sym=_gradient_symbol(mask); sym=sym.resize((420,int(420*sym.height/sym.width)),Image.Resampling.LANCZOS)
    bg=(247,251,255) if light else (0,0,0); out=Image.new('RGB',size,bg); out.paste(sym,((size[0]-sym.width)//2,270),sym)
    d=ImageDraw.Draw(out); f=_font(76); word='I N F I N I T Y'; box=d.textbbox((0,0),word,font=f); color=(15,22,30) if light else (245,248,252)
    d.text(((size[0]-(box[2]-box[0]))//2,665),word,font=f,fill=color)
    return out

def make_banner(src):
    splash=make_splash(src,False,(640,360)); return splash.resize((320,180),Image.Resampling.LANCZOS)

def image_bytes(im,fmt,**kw):
    b=io.BytesIO(); im.save(b,fmt,**kw); return b.getvalue()

def build(src,out,receipt):
    if out.exists(): out.unlink()
    replacements={}
    with zipfile.ZipFile(src) as zin:
        source_icon=zin.read('res/zp.png')
        launcher=make_launcher(source_icon,512)
        replacements['res/zp.png']=image_bytes(launcher,'PNG')
        replacements['res/OK.png']=image_bytes(make_launcher(source_icon,36),'PNG')
        replacements['res/OA.png']=image_bytes(make_banner(source_icon),'PNG')
        replacements['res/85.png']=image_bytes(make_splash(source_icon,False),'PNG')
        replacements['assets/media/splash.jpg']=image_bytes(make_splash(source_icon,False),'JPEG',quality=93)
        replacements[SKIN+'media/infinity/icon.png']=image_bytes(make_horizontal_logo(source_icon,False),'PNG')
        replacements[SKIN+'media/infinity/logo-dark.png']=image_bytes(make_horizontal_logo(source_icon,False),'PNG')
        replacements[SKIN+'media/infinity/logo-light.png']=image_bytes(make_horizontal_logo(source_icon,True),'PNG')
        for n in (16,32,48,80,120,256): replacements[f'assets/media/icon{n}x{n}.png']=image_bytes(make_launcher(source_icon,n),'PNG')
        with zipfile.ZipFile(out,'w',allowZip64=True) as zout:
            seen=set()
            for item in zin.infolist():
                data=zin.read(item.filename)
                if item.filename==SKIN+'xml/Variables.xml': data=patch_variables(data)
                elif item.filename==SKIN+'xml/Font.xml': data=patch_fonts(data)
                elif item.filename==SKIN+'xml/Home.xml': data=patch_home(data)
                elif item.filename==SKIN+'xml/Includes.xml': data=patch_includes(data)
                elif item.filename==SKIN+'xml/Includes_Home.xml': data=patch_includes_home(data)
                elif item.filename in (SKIN+'xml/VideoOSD.xml',SKIN+'xml/DialogSeekBar.xml'): data=patch_player_xml(data)
                if item.filename in replacements: data=replacements[item.filename]; seen.add(item.filename)
                zout.writestr(item,data)
            for name,data in replacements.items():
                if name not in seen and name not in zin.namelist(): zout.writestr(name,data)
    with zipfile.ZipFile(out) as z, zipfile.ZipFile(src) as base:
        for p in TARGET_XML: ET.fromstring(z.read(p))
        checks={
          'android_icon_changed':z.read('res/zp.png')!=base.read('res/zp.png'),
          'android_launch_changed':z.read('res/85.png')!=base.read('res/85.png'),
          'light_panel':'FFF7FBFF' in z.read(SKIN+'xml/Includes.xml').decode(),
          'mobile_landscape':MOBILE_LANDSCAPE in z.read(SKIN+'xml/Includes_Home.xml').decode(),
          'theme_logo':'infinity/logo-light.png' in z.read(SKIN+'xml/Home.xml').decode(),
          'player_blue':'$VAR[InfinityColor_blue]' in z.read(SKIN+'xml/VideoOSD.xml').decode(),
        }
        if not all(checks.values()): raise RuntimeError('V3 self-audit failed: '+repr(checks))
    receipt.write_text(json.dumps({
      'base':src.name,'engine_changed':False,'dark_mode':'OLED true black preserved','light_mode':'ice-white canvas + light sidebar + dark regular-weight text',
      'front_portrait':'regular-weight responsive typography','front_landscape':'compact regular-weight body text + wider text area',
      'player_osd':'translucent stock OSD preserved; Infinity blue focus + theme-aware text/icons','android_launcher_resource':'res/zp.png (manifest @0x7f040012)',
      'android_splash_resource':'res/85.png (applaunch_screen) + Splash ImageView uses res/zp.png','in_app_logo':'separate dark/light logo assets',
      'same_signing_identity_required':True,'checks':checks
    },indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(); p.add_argument('src',type=Path); p.add_argument('out',type=Path); p.add_argument('receipt',type=Path); a=p.parse_args(); build(a.src,a.out,a.receipt)
if __name__=='__main__': main()
