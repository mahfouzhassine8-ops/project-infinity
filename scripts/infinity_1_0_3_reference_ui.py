#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, io, json, math, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SKIN='assets/addons/skin.estuary/'
LIGHT='String.IsEqual(Skin.String(Infinity.ThemePolicy),light) | [[String.IsEmpty(Skin.String(Infinity.ThemePolicy)) | String.IsEqual(Skin.String(Infinity.ThemePolicy),system)] + String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light)]'
DARK=f'![{LIGHT}]'
MOBILE='String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)'
PORTRAIT=f'Integer.IsLess(System.ScreenWidth,System.ScreenHeight) + {MOBILE}'
MOBILE_LANDSCAPE=f'Integer.IsGreater(System.ScreenWidth,System.ScreenHeight) + {MOBILE}'
NON_MOBILE=f'![{MOBILE}]'
NOT_MOBILE_LANDSCAPE=f'![{MOBILE_LANDSCAPE}]'

LIGHT_VALUES={
 'background':'FFF8FBFF','primary_background':'FFF8FBFF','secondary_background':'FFEAF2F8',
 'dialog_tint':'FFFFFFFF','bg_image':'FFF8FBFF','bg_overlay':'00FFFFFF','black':'FFF8FBFF',
 'white':'FF111821','grey':'FF334252','disabled':'A05B6976','text_shadow':'10000000',
 'button_focus':'FF0A8FFF','button_alt_focus':'FFE1F1FF','blue':'FF0A8FFF','border_alpha':'304A6780'
}
DARK_VALUES={
 'background':'FF000000','primary_background':'FF000000','secondary_background':'FF0A1017',
 'dialog_tint':'FF070A0E','bg_image':'FF000000','bg_overlay':'00000000','black':'FF000000',
 'white':'FFF5F7FA','grey':'FF8FA5B8','disabled':'66FFFFFF','text_shadow':'26000000',
 'button_focus':'FF0A8FFF','button_alt_focus':'FF087FE4','blue':'FF19BFFF','border_alpha':'4833B9FF'
}
EXTRA_VARS={
 'InfinityColor_menu_focus_bg':('FFE1F1FF','FF0A8FFF'),
 'InfinityColor_menu_focus_text':('FF0877E8','FFFFFFFF'),
 'InfinityColor_menu_icon':('FF13202C','FF19BFFF'),
 'InfinityColor_menu_text':('FF111821','FFF5F7FA'),
 'InfinityColor_sidebar':('FFF5F9FD','FF030507'),
 'InfinityColor_button_surface':('FFE9EFF5','FF141A21'),
 'InfinityColor_action_icon':('FF111821','FF19BFFF'),
}
TARGET_XML={
 SKIN+'xml/Variables.xml', SKIN+'xml/Font.xml', SKIN+'xml/Home.xml',
 SKIN+'xml/Includes.xml', SKIN+'xml/Includes_Home.xml', SKIN+'xml/Includes_Buttons.xml',
 SKIN+'xml/VideoOSD.xml', SKIN+'xml/DialogSeekBar.xml'
}

def set_text(parent, tag, value):
    node=parent.find(tag)
    if node is None:
        node=ET.SubElement(parent, tag)
    node.text=value
    return node

def set_visible(control, cond):
    for v in list(control.findall('visible')):
        control.remove(v)
    ET.SubElement(control,'visible').text=cond

def append_visible(control, cond):
    ET.SubElement(control,'visible').text=cond

def _ensure_variable(root, name, light_value, dark_value):
    var=next((v for v in root.findall('variable') if v.attrib.get('name')==name),None)
    if var is None:
        var=ET.SubElement(root,'variable',{'name':name})
    for child in list(var): var.remove(child)
    ET.SubElement(var,'value',{'condition':LIGHT}).text=light_value
    ET.SubElement(var,'value',{'condition':DARK}).text=dark_value
    ET.SubElement(var,'value').text=dark_value

def patch_variables(data):
    root=ET.fromstring(data)
    for key,lv in LIGHT_VALUES.items():
        name='InfinityColor_'+key
        var=next((v for v in root.findall('variable') if v.attrib.get('name')==name),None)
        if var is None: continue
        for value in var.findall('value'):
            cond=value.attrib.get('condition','')
            if 'ThemePolicy),light' in cond or 'SystemTheme),light' in cond:
                value.text=lv
            elif 'ThemePolicy),oled' in cond or 'SystemTheme),dark' in cond:
                value.text=DARK_VALUES[key]
            elif not cond:
                value.text=DARK_VALUES[key]
    for name,(lv,dv) in EXTRA_VARS.items():
        _ensure_variable(root,name,lv,dv)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_fonts(data):
    root=ET.fromstring(data)
    wanted={
      'InfinityMenu':(31,'1.05'),
      'InfinityMenuPortrait':(34,'1.05'),
      'InfinityBodyHero':(26,'1.18'),
      'InfinityBodyHeroCompact':(21,'1.20'),
      'InfinityBodyHeroPortrait':(24,'1.18'),
      'InfinityButtonHero':(22,'1.05'),
      'InfinityButtonHeroCompact':(20,'1.05'),
    }
    for fs in root.findall('fontset'):
        for f in list(fs.findall('font')):
            if f.findtext('name') in wanted:
                fs.remove(f)
        for name,(size,spacing) in wanted.items():
            f=ET.SubElement(fs,'font')
            ET.SubElement(f,'name').text=name
            ET.SubElement(f,'filename').text='NotoSans-Regular.ttf'
            ET.SubElement(f,'size').text=str(size)
            ET.SubElement(f,'linespacing').text=spacing
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def _texture(control):
    return control.find('texture') if control is not None else None

def patch_home(data):
    root=ET.fromstring(data)
    fixed=next((c for c in root.iter('control') if c.attrib.get('type')=='fixedlist' and c.attrib.get('id')=='9000'),None)
    if fixed is None: raise RuntimeError('Home fixedlist 9000 missing')
    set_text(fixed,'top','265')
    set_text(fixed,'width','462')
    for layout_name in ('focusedlayout','itemlayout'):
        layout=fixed.find(layout_name)
        if layout is None: raise RuntimeError('Missing '+layout_name)
        labels=[c for c in layout.findall('control') if c.attrib.get('type')=='label']
        if not labels: raise RuntimeError('Missing menu label in '+layout_name)
        base=labels[0]
        for extra in labels[1:]: layout.remove(extra)
        set_text(base,'left','104'); set_text(base,'width','338'); set_text(base,'font','InfinityMenu')
        set_text(base,'shadowcolor','$VAR[InfinityColor_text_shadow]')
        set_visible(base,f'![{PORTRAIT}]')
        portrait=copy.deepcopy(base); set_visible(portrait,PORTRAIT); set_text(portrait,'font','InfinityMenuPortrait'); layout.append(portrait)
        if layout_name=='focusedlayout':
            for c in layout.iter('control'):
                if c.attrib.get('type')!='image': continue
                t=_texture(c)
                if t is None: continue
                txt=(t.text or '').strip()
                if txt=='lists/focus.png':
                    t.attrib['colordiffuse']='$VAR[InfinityColor_menu_focus_bg]'
                elif '$INFO[ListItem.Art(thumb)]' in txt:
                    t.attrib['colordiffuse']='$VAR[InfinityColor_menu_focus_text]'
                elif txt=='colors/black.png':
                    t.attrib['colordiffuse']='00FFFFFF'
            for label in [base,portrait]:
                set_text(label,'textcolor','$VAR[InfinityColor_menu_focus_text]')
                set_text(label,'focusedcolor','$VAR[InfinityColor_menu_focus_text]')
            marker=next((c for c in layout.findall('control') if c.attrib.get('type')=='image' and c.findtext('width')=='7'),None)
            if marker is None:
                marker=ET.Element('control',{'type':'image'})
                set_text(marker,'left','0'); set_text(marker,'top','0'); set_text(marker,'width','7'); set_text(marker,'height','95')
                t=ET.SubElement(marker,'texture'); t.text='white.png'; layout.insert(1,marker)
            t=_texture(marker); t.attrib['colordiffuse']='$VAR[InfinityColor_blue]'
        else:
            for c in layout.iter('control'):
                if c.attrib.get('type')!='image': continue
                t=_texture(c)
                if t is not None and '$INFO[ListItem.Art(thumb)]' in (t.text or ''):
                    t.attrib['colordiffuse']='$VAR[InfinityColor_menu_icon]'
            for label in [base,portrait]:
                set_text(label,'textcolor','$VAR[InfinityColor_menu_text]')
                set_text(label,'focusedcolor','$VAR[InfinityColor_menu_text]')
    util=next((c for c in root.iter('control') if c.attrib.get('type')=='grouplist' and c.attrib.get('id')=='700'),None)
    if util is not None:
        set_text(util,'top','150'); set_text(util,'left','-8')
    for c in root.iter('control'):
        if c.attrib.get('type')!='image': continue
        t=_texture(c)
        if t is None: continue
        txt=(t.text or '').strip()
        if txt in ('infinity/logo-dark.png','infinity/logo-light.png','infinity/icon.png'):
            set_text(c,'left','20'); set_text(c,'top','0'); set_text(c,'width','320'); set_text(c,'height','128'); set_text(c,'aspectratio','keep')
            if txt=='infinity/icon.png': t.text='infinity/sidebar-dark.png'; set_visible(c,DARK)
            elif txt=='infinity/logo-dark.png': t.text='infinity/sidebar-dark.png'; set_visible(c,DARK)
            elif txt=='infinity/logo-light.png': t.text='infinity/sidebar-light.png'; set_visible(c,LIGHT)
    top_brand=None
    for g in root.iter('control'):
        if g.attrib.get('type')!='group': continue
        imgs=[x for x in g.findall('control') if x.attrib.get('type')=='image']
        if any((_texture(x) is not None and (_texture(x).text or '').strip() in ('infinity/sidebar-dark.png','infinity/sidebar-light.png')) for x in imgs):
            top_brand=g; break
    if top_brand is not None:
        have_dark=any((_texture(x) is not None and (_texture(x).text or '').strip()=='infinity/sidebar-dark.png') for x in top_brand.findall('control'))
        have_light=any((_texture(x) is not None and (_texture(x).text or '').strip()=='infinity/sidebar-light.png') for x in top_brand.findall('control'))
        template=next((x for x in top_brand.findall('control') if x.attrib.get('type')=='image'),None)
        if template is not None and not have_dark:
            d=copy.deepcopy(template); _texture(d).text='infinity/sidebar-dark.png'; set_visible(d,DARK); top_brand.append(d)
        if template is not None and not have_light:
            l=copy.deepcopy(template); _texture(l).text='infinity/sidebar-light.png'; set_visible(l,LIGHT); top_brand.append(l)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def _new_bg(texture, cond):
    c=ET.Element('control',{'type':'image'})
    ET.SubElement(c,'depth').text='DepthBackground'
    ET.SubElement(c,'include').text='FullScreenDimensions'
    ET.SubElement(c,'aspectratio').text='scale'
    ET.SubElement(c,'texture').text=texture
    ET.SubElement(c,'visible').text=cond
    return c

def patch_includes(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ColoredBackgroundImages'),None)
    if inc is None: raise RuntimeError('ColoredBackgroundImages include missing')
    for c in list(inc.findall('control')): inc.remove(c)
    inc.append(_new_bg('infinity/background-dark.png',DARK))
    inc.append(_new_bg('infinity/background-light.png',LIGHT))
    panel=next((i for i in root.findall('include') if i.attrib.get('name')=='ContentPanel'),None)
    if panel is None: raise RuntimeError('ContentPanel include missing')
    definition=panel.find('definition')
    if definition is None: raise RuntimeError('ContentPanel definition missing')
    for c in list(definition.findall('control')):
        if c.attrib.get('type')=='image': definition.remove(c)
    for color,cond in [('$VAR[InfinityColor_sidebar]',DARK),('$VAR[InfinityColor_sidebar]',LIGHT)]:
        c=ET.Element('control',{'type':'image'})
        t=ET.SubElement(c,'texture',{'colordiffuse':color}); t.text='white.png'
        ET.SubElement(c,'width').text='$PARAM[width]'; ET.SubElement(c,'left').text='$PARAM[left]'; ET.SubElement(c,'right').text='$PARAM[right]'
        ET.SubElement(c,'top').text='$PARAM[top]'; ET.SubElement(c,'height').text='$PARAM[height]'; ET.SubElement(c,'visible').text=cond
        definition.append(c)
    divider=ET.Element('control',{'type':'image'})
    td=ET.SubElement(divider,'texture',{'colordiffuse':'$VAR[InfinityColor_border_alpha]'}); td.text='white.png'
    ET.SubElement(divider,'right').text='0'; ET.SubElement(divider,'top').text='0'; ET.SubElement(divider,'width').text='2'; ET.SubElement(divider,'height').text='100%'
    definition.append(divider)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def _hero_control(texture, cond, height):
    c=ET.Element('control',{'type':'image'})
    ET.SubElement(c,'width').text='100%'; ET.SubElement(c,'height').text=str(height)
    ET.SubElement(c,'aspectratio').text='keep'; ET.SubElement(c,'texture').text=texture
    ET.SubElement(c,'visible').text=cond
    return c

def patch_includes_home(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='ImageWidget'),None)
    if inc is None: raise RuntimeError('ImageWidget include missing')
    definition=inc.find('definition')
    if definition is None: raise RuntimeError('ImageWidget definition missing')
    gl=next((c for c in definition.iter('control') if c.attrib.get('type')=='grouplist' and (c.attrib.get('id') or '').endswith('577')),None)
    if gl is None: raise RuntimeError('ImageWidget vertical grouplist missing')
    set_text(gl,'left','40'); set_text(gl,'right','40'); set_text(gl,'itemgap','12')
    for c in list(gl.findall('control')):
        if c.attrib.get('type')=='image' and (_texture(c) is not None) and (_texture(c).text or '').startswith('infinity/hero-'):
            gl.remove(c)
    first_index=0
    gl.insert(first_index,_hero_control('infinity/hero-dark.png',f'{DARK} + {NOT_MOBILE_LANDSCAPE}',330)); first_index+=1
    gl.insert(first_index,_hero_control('infinity/hero-light.png',f'{LIGHT} + {NOT_MOBILE_LANDSCAPE}',330)); first_index+=1
    gl.insert(first_index,_hero_control('infinity/hero-dark.png',f'{DARK} + {MOBILE_LANDSCAPE}',235)); first_index+=1
    gl.insert(first_index,_hero_control('infinity/hero-light.png',f'{LIGHT} + {MOBILE_LANDSCAPE}',235)); first_index+=1
    textboxes=[c for c in gl.findall('control') if c.attrib.get('type')=='textbox']
    if not textboxes: raise RuntimeError('ImageWidget textbox missing')
    base=textboxes[0]
    for extra in textboxes[1:]: gl.remove(extra)
    set_text(base,'width','760'); set_text(base,'height','auto'); set_text(base,'font','InfinityBodyHero'); set_text(base,'textcolor','$VAR[InfinityColor_menu_text]'); set_visible(base,NON_MOBILE)
    compact=copy.deepcopy(base); set_text(compact,'width','930'); set_text(compact,'font','InfinityBodyHeroCompact'); set_visible(compact,MOBILE_LANDSCAPE); gl.insert(list(gl).index(base)+1,compact)
    portrait=copy.deepcopy(base); set_text(portrait,'width','790'); set_text(portrait,'font','InfinityBodyHeroPortrait'); set_visible(portrait,PORTRAIT); gl.insert(list(gl).index(compact)+1,portrait)
    for b in [c for c in definition.iter('control') if c.attrib.get('type')=='button']:
        set_text(b,'height','76'); set_text(b,'font','InfinityButtonHero'); set_text(b,'textoffsetx','24')
        set_text(b,'textcolor','$VAR[InfinityColor_menu_text]'); set_text(b,'focusedcolor','FFFFFFFF')
        tf=b.find('texturefocus')
        if tf is None: tf=ET.SubElement(b,'texturefocus')
        tf.text='buttons/dialogbutton-fo.png'; tf.attrib['border']='23'; tf.attrib['colordiffuse']='$VAR[InfinityColor_button_focus]'
        tn=b.find('texturenofocus')
        if tn is None: tn=ET.SubElement(b,'texturenofocus')
        tn.text='buttons/dialogbutton-fo.png'; tn.attrib['border']='23'; tn.attrib['colordiffuse']='$VAR[InfinityColor_button_surface]'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_includes_buttons(data):
    root=ET.fromstring(data)
    inc=next((i for i in root.findall('include') if i.attrib.get('name')=='IconButton'),None)
    if inc is None: return data
    definition=inc.find('definition')
    if definition is None: return data
    radio=next((c for c in definition.findall('control') if c.attrib.get('type')=='radiobutton'),None)
    if radio is None: return data
    for tag in ('textureradioonnofocus','textureradiooffnofocus'):
        n=radio.find(tag)
        if n is not None: n.attrib['colordiffuse']='$VAR[InfinityColor_action_icon]'
    for tag in ('textureradioonfocus','textureradioofffocus'):
        n=radio.find(tag)
        if n is not None: n.attrib['colordiffuse']='$VAR[InfinityColor_action_icon]'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def patch_player_xml(data):
    s=data.decode('utf-8')
    repl={
      'colordiffuse="button_focus"':'colordiffuse="$VAR[InfinityColor_blue]"',
      'colordiffuse="$VAR[InfinityColor_button_focus]"':'colordiffuse="$VAR[InfinityColor_blue]"',
      'colordiffuse="white"':'colordiffuse="$VAR[InfinityColor_white]"',
      '<textcolor>white</textcolor>':'<textcolor>$VAR[InfinityColor_white]</textcolor>',
      '<focusedcolor>white</focusedcolor>':'<focusedcolor>$VAR[InfinityColor_white]</focusedcolor>',
    }
    for a,b in repl.items(): s=s.replace(a,b)
    ET.fromstring(s.encode())
    return s.encode()

def _font(size,bold=False):
    candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if bold else []
    candidates += ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
    for p in candidates:
        try:return ImageFont.truetype(p,size)
        except OSError:pass
    return ImageFont.load_default()

def _symbol_mask(src_icon):
    im=Image.open(io.BytesIO(src_icon)).convert('RGBA')
    px=im.load(); mask=Image.new('L',im.size,0); mp=mask.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=px[x,y]
            if a and max(r,g,b)>170 and abs(r-g)<80 and abs(g-b)<80:
                mp[x,y]=a
    bbox=mask.getbbox()
    if not bbox:
        mask=im.getchannel('A'); bbox=mask.getbbox()
    if not bbox: raise RuntimeError('Infinity symbol mask missing')
    return mask.crop(bbox)

def _gradient_symbol(mask):
    w,h=mask.size
    grad=Image.new('RGBA',(w,h),(0,0,0,0)); gp=grad.load()
    stops=[(0.0,(5,74,245)),(.32,(0,139,255)),(.65,(0,192,255)),(1.0,(65,226,255))]
    for x in range(w):
        t=x/max(1,w-1)
        for i in range(len(stops)-1):
            if stops[i][0] <= t <= stops[i+1][0]:
                t0,c0=stops[i]; t1,c1=stops[i+1]; u=(t-t0)/(t1-t0)
                c=tuple(int(c0[j]+(c1[j]-c0[j])*u) for j in range(3)); break
        else:c=stops[-1][1]
        for y in range(h):gp[x,y]=(*c,255)
    grad.putalpha(mask)
    hi=Image.new('RGBA',(w,h),(0,0,0,0)); hd=ImageDraw.Draw(hi)
    hd.ellipse((-w*.05,-h*.55,w*1.05,h*.65),fill=(255,255,255,38))
    hi.putalpha(Image.composite(hi.getchannel('A'),Image.new('L',(w,h),0),mask))
    return Image.alpha_composite(grad,hi)

def _fit_symbol(src_icon,target_w):
    mask=_symbol_mask(src_icon); sym=_gradient_symbol(mask)
    scale=target_w/sym.width
    return sym.resize((int(target_w),max(1,int(sym.height*scale))),Image.Resampling.LANCZOS)

def _draw_centered_text(draw, xy_y, text, font, fill, width):
    b=draw.textbbox((0,0),text,font=font); x=(width-(b[2]-b[0]))//2
    draw.text((x,xy_y),text,font=font,fill=fill)

def make_sidebar_logo(src_icon, light=False):
    out=Image.new('RGBA',(360,180),(0,0,0,0)); sym=_fit_symbol(src_icon,155)
    out.alpha_composite(sym,((360-sym.width)//2,3))
    d=ImageDraw.Draw(out); color=(15,22,30,255) if light else (246,249,252,255)
    _draw_centered_text(d,118,'I N F I N I T Y',_font(30),color,360)
    return out

def make_hero(src_icon,light=False):
    out=Image.new('RGBA',(900,430),(0,0,0,0)); sym=_fit_symbol(src_icon,390)
    out.alpha_composite(sym,((900-sym.width)//2,4))
    d=ImageDraw.Draw(out); color=(13,20,29,255) if light else (248,250,252,255)
    _draw_centered_text(d,252,'I N F I N I T Y',_font(62),color,900)
    accent=(15,113,205,255) if light else (93,208,255,255)
    _draw_centered_text(d,342,'Y O U R   M E D I A .   Y O U R   W A Y .',_font(20),accent,900)
    return out

def make_launcher(src_icon,size=512):
    out=Image.new('RGBA',(size,size),(5,8,12,255)); d=ImageDraw.Draw(out)
    d.rounded_rectangle((0,0,size-1,size-1),radius=int(size*.18),fill=(5,8,12,255),outline=(0,130,240,145),width=max(2,size//128))
    sym=_fit_symbol(src_icon,int(size*.62)); out.alpha_composite(sym,((size-sym.width)//2,int(size*.12)))
    _draw_centered_text(d,int(size*.69),'I N F I N I T Y',_font(max(12,int(size*.072))), (245,249,252,255),size)
    return out

def make_splash(src_icon,light=False,size=(1920,1080)):
    bg=(248,251,255) if light else (0,0,0)
    out=Image.new('RGB',size,bg); sym=_fit_symbol(src_icon,570)
    out.paste(sym,((size[0]-sym.width)//2,210),sym)
    d=ImageDraw.Draw(out); color=(15,22,30) if light else (248,250,252)
    _draw_centered_text(d,610,'I N F I N I T Y',_font(80),color,size[0])
    accent=(0,119,222) if light else (77,202,255)
    _draw_centered_text(d,735,'Y O U R   M E D I A .   Y O U R   W A Y .',_font(26),accent,size[0])
    return out

def make_background(light=False,size=(1920,1080)):
    if light:
        base=Image.new('RGB',size,(248,251,255)); overlay=Image.new('RGBA',size,(0,0,0,0)); d=ImageDraw.Draw(overlay)
        for offset,alpha,w in [(0,72,75),(115,48,58),(220,35,45)]:
            pts=[]
            for x in range(850,2050,18):
                y=int(140+offset + 0.00042*(x-1180)**2 + 55*math.sin((x-780)/310))
                pts.append((x,y))
            d.line(pts,fill=(82,177,245,alpha),width=w,joint='curve')
        for offset,alpha,w in [(0,26,42),(120,18,32)]:
            pts=[]
            for x in range(-100,1550,18):
                y=int(1040-offset - .00025*(x-500)**2)
                pts.append((x,y))
            d.line(pts,fill=(90,190,255,alpha),width=w)
        overlay=overlay.filter(ImageFilter.GaussianBlur(34)); return Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')
    base=Image.new('RGB',size,(0,0,0)); overlay=Image.new('RGBA',size,(0,0,0,0)); d=ImageDraw.Draw(overlay)
    for offset,alpha,w in [(0,78,60),(100,52,44),(190,35,34)]:
        pts=[]
        for x in range(-180,2050,20):
            y=int(840-offset + 80*math.sin((x+180)/340) + .00011*(x-960)**2)
            pts.append((x,y))
        d.line(pts,fill=(0,83,180,alpha),width=w)
    overlay=overlay.filter(ImageFilter.GaussianBlur(30)); return Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')

def image_bytes(im,fmt='PNG',**kw):
    b=io.BytesIO(); im.save(b,fmt,**kw); return b.getvalue()

def build(src:Path,out:Path,receipt:Path):
    if out.exists(): out.unlink()
    replacements={}
    with zipfile.ZipFile(src) as zin:
        source_icon=zin.read('res/zp.png')
        replacements['res/zp.png']=image_bytes(make_launcher(source_icon,512))
        replacements['res/OK.png']=image_bytes(make_launcher(source_icon,36))
        replacements['res/85.png']=image_bytes(make_splash(source_icon,False))
        replacements['assets/media/splash.jpg']=image_bytes(make_splash(source_icon,False),'JPEG',quality=94)
        replacements[SKIN+'media/infinity/sidebar-dark.png']=image_bytes(make_sidebar_logo(source_icon,False))
        replacements[SKIN+'media/infinity/sidebar-light.png']=image_bytes(make_sidebar_logo(source_icon,True))
        replacements[SKIN+'media/infinity/logo-dark.png']=replacements[SKIN+'media/infinity/sidebar-dark.png']
        replacements[SKIN+'media/infinity/logo-light.png']=replacements[SKIN+'media/infinity/sidebar-light.png']
        replacements[SKIN+'media/infinity/hero-dark.png']=image_bytes(make_hero(source_icon,False))
        replacements[SKIN+'media/infinity/hero-light.png']=image_bytes(make_hero(source_icon,True))
        replacements[SKIN+'media/infinity/background-dark.png']=image_bytes(make_background(False))
        replacements[SKIN+'media/infinity/background-light.png']=image_bytes(make_background(True))
        for n in (16,32,48,80,120,256): replacements[f'assets/media/icon{n}x{n}.png']=image_bytes(make_launcher(source_icon,n))
        with zipfile.ZipFile(out,'w',allowZip64=True) as zout:
            seen=set()
            for item in zin.infolist():
                data=zin.read(item.filename)
                if item.filename==SKIN+'xml/Variables.xml': data=patch_variables(data)
                elif item.filename==SKIN+'xml/Font.xml': data=patch_fonts(data)
                elif item.filename==SKIN+'xml/Home.xml': data=patch_home(data)
                elif item.filename==SKIN+'xml/Includes.xml': data=patch_includes(data)
                elif item.filename==SKIN+'xml/Includes_Home.xml': data=patch_includes_home(data)
                elif item.filename==SKIN+'xml/Includes_Buttons.xml': data=patch_includes_buttons(data)
                elif item.filename in (SKIN+'xml/VideoOSD.xml',SKIN+'xml/DialogSeekBar.xml'): data=patch_player_xml(data)
                if item.filename in replacements:
                    data=replacements[item.filename]; seen.add(item.filename)
                zout.writestr(item,data)
            for name,data in replacements.items():
                if name not in seen and name not in zin.namelist(): zout.writestr(name,data)
    with zipfile.ZipFile(out) as z, zipfile.ZipFile(src) as base:
        for p in TARGET_XML: ET.fromstring(z.read(p))
        home=z.read(SKIN+'xml/Home.xml').decode(); incl=z.read(SKIN+'xml/Includes.xml').decode(); ih=z.read(SKIN+'xml/Includes_Home.xml').decode()
        checks={
          'engine_files_unchanged': all(z.read(n)==base.read(n) for n in base.namelist() if n.startswith('lib/') and n in z.namelist()),
          'launcher_changed':z.read('res/zp.png')!=base.read('res/zp.png'),
          'splash_changed':z.read('res/85.png')!=base.read('res/85.png'),
          'large_sidebar_logo':'infinity/sidebar-dark.png' in home and '<width>320</width>' in home,
          'hero_logo':'infinity/hero-dark.png' in ih and 'infinity/hero-light.png' in ih,
          'reference_backgrounds':'infinity/background-dark.png' in incl and 'infinity/background-light.png' in incl,
          'opaque_dark_focus':'FF0A8FFF' in z.read(SKIN+'xml/Variables.xml').decode(),
          'noto_fonts':'NotoSans-Regular.ttf' in z.read(SKIN+'xml/Font.xml').decode(),
          'front_landscape':MOBILE_LANDSCAPE in ih,
          'player_blue':'$VAR[InfinityColor_blue]' in z.read(SKIN+'xml/VideoOSD.xml').decode(),
        }
        if not all(checks.values()): raise RuntimeError('Reference UI self-audit failed: '+repr(checks))
    receipt.write_text(json.dumps({
      'base':src.name,'engine_changed':False,'design_target':'approved 10696 reference',
      'dark':'OLED true black + subtle blue ribbons + bright blue selected row',
      'light':'ice-white + pale blue ribbons + pale-blue selected row + dark text/icons',
      'sidebar_brand':'large stacked Infinity emblem + wordmark','hero_brand':'large centered emblem + wordmark + Your Media. Your Way.',
      'front_landscape':'smaller Noto Sans body + wider text box','portrait':'responsive Noto Sans typography',
      'launcher':'adaptive-safe dark Infinity icon with wordmark','player_osd':'existing translucent OSD preserved with Infinity blue focus',
      'same_signing_identity_required':True,'checks':checks
    },indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(); p.add_argument('src',type=Path); p.add_argument('out',type=Path); p.add_argument('receipt',type=Path)
    a=p.parse_args(); build(a.src,a.out,a.receipt)
if __name__=='__main__': main()
