"""Host illustration from shipped XML, fonts, textures and geometry; NOT Kodi."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'addons/script.infinity.rails/resources'))
from lib.menu_geometry import layout
import build_rc3 as build


def ninepatch(src, width, height, border):
    out=Image.new('RGBA',(width,height))
    xs=[0,border,src.width-border,src.width]
    ys=[0,border,src.height-border,src.height]
    dx=[0,min(border,width//2),max(width-border,width//2),width]
    dy=[0,min(border,height//2),max(height-border,height//2),height]
    for x in range(3):
        for y in range(3):
            w,h=dx[x+1]-dx[x],dy[y+1]-dy[y]
            if w and h:
                p=src.crop((xs[x],ys[y],xs[x+1],ys[y+1])).resize((w,h),Image.Resampling.LANCZOS)
                out.alpha_composite(p,(dx[x],dy[y]))
    return out


def render(dw,dh,theme,count=5):
    xml=ET.parse(build.SKIN/'unified/DialogInfinityRails.xml')
    inc=ET.parse(build.SKIN/'unified/Includes_InfinityRails.xml')
    index={'oled':0,'light':1,'dark':2}[theme]
    colors={v.get('name'):v.findall('value')[index].text for v in inc.findall('variable') if v.get('name','').startswith('InfinityRails') and v.get('name')!='InfinityRailsContent'}
    def color(v):
        if v.startswith('$VAR['):v=colors[v[5:-1]]
        return tuple(int(v[i:i+2],16) for i in (2,4,6,0))
    bg={'light':(238,244,250,255),'dark':(18,26,38,255),'oled':(0,0,0,255)}[theme]
    out=Image.new('RGBA',(dw,dh),bg)
    g=layout(dw,dh,dw,dh,count)
    scale=g['width']/760
    choices=['Open Add-on','Move / Reorder','Remove from TV Show Add-ons','Add-on Settings','Cancel']
    props={'Rails.Title':'INFINITY — RAIL OPTIONS','Rails.Subtitle':'Empflix · TV Show Add-ons'}
    controls=xml.find('./controls/control').findall('control')
    for c in controls:
        cid=int(c.get('id'))
        if 200<=cid<205 and cid-200>=g['rows']:continue
        if cid in (210,211,212) and not g['paged']:continue
        x,y=float(c.findtext('left','0')),float(c.findtext('top','0'))
        w,h=float(c.findtext('width','0')),float(c.findtext('height','0'))
        if cid==2:h=g['design_height']
        if cid in (210,211,212):y=160+g['rows']*100
        x,y=int(g['left']+x*scale),int(g['top']+y*scale)
        w,h=max(1,round(w*scale)),max(1,round(h*scale))
        def texture(node):
            if node is None or not node.text:return
            src=Image.open(build.SKIN/'media'/node.text).convert('RGBA')
            tint=color(node.get('colordiffuse','FFFFFFFF'))
            overlay=Image.new('RGBA',src.size,tint[:3]+(255,))
            overlay.putalpha(src.getchannel('A').point(lambda a:a*tint[3]//255))
            border=int(node.get('border','0'))
            if border:overlay=ninepatch(overlay,w,h,min(border,src.width//2,src.height//2))
            else:overlay=overlay.resize((w,h),Image.Resampling.LANCZOS)
            out.alpha_composite(overlay,(x,y))
        if c.get('type')=='image':
            if cid!=5:texture(c.find('texture'));texture(c.find('bordertexture'))
            else:
                draw=ImageDraw.Draw(out);draw.rounded_rectangle((x,y,x+w,y+h),radius=round(10*scale),fill=color('$VAR[InfinityRailsField]'))
                font=ImageFont.truetype(str(build.SKIN/'fonts/Roboto-Bold.ttf'),max(8,round(34*scale)))
                draw.text((x+w/2,y+h/2),'E',font=font,anchor='mm',fill=color('$VAR[InfinityRailsAccent]'))
        elif c.get('type')=='button':
            texture(c.find('texturefocus') if cid==201 else c.find('texturenofocus'))
        if c.get('type') in ('label','button') and cid!=9:
            text=c.findtext('label','')
            if 200<=cid<205:text=choices[cid-200]
            if cid==212:text='1 / '+str((count+g['capacity']-1)//g['capacity'])
            for key,value in props.items():text=text.replace('$INFO[Window.Property('+key+')]',value)
            f=c.findtext('font','InfinitySmall');fs={'InfinityBody':34,'InfinityBodyBold':34,'InfinitySmall':28}.get(f,28)
            font=ImageFont.truetype(str(build.SKIN/('fonts/Roboto-Bold.ttf' if 'Bold' in f else 'fonts/Roboto-Regular.ttf')),max(8,round(fs*scale)))
            draw=ImageDraw.Draw(out)
            fill=color(c.findtext('textcolor','$VAR[InfinityRailsText]'))
            align=c.findtext('align','left')
            if align=='center':draw.text((x+w/2,y+h/2),text,font=font,anchor='mm',fill=fill)
            else:draw.text((x+float(c.findtext('textoffsetx','0'))*scale,y+h/2),text,font=font,anchor='lm',fill=fill)
    return out.convert('RGB'),g


def main():
    target=build.OUT/'visual-review';target.mkdir(exist_ok=True)
    viewports=[('Cover portrait',384,832),('Cover landscape',832,384),('Inner portrait',690,780),('Split / float',320,440)]
    sheet=Image.new('RGB',(1260,1220),(245,247,250));d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(str(build.SKIN/'fonts/Roboto-Regular.ttf'),18)
    d.text((20,12),'HOST XML ILLUSTRATIONS — NOT KODI OR FOLD SCREENSHOTS',font=font,fill=(20,35,50))
    records=[]
    for r,(name,w,h) in enumerate(viewports):
        for c,theme in enumerate(['light','dark','oled']):
            im,g=render(w,h,theme)
            filename=name.lower().replace(' / ','-').replace(' ','-')+'-'+theme+'.png'
            im.save(target/filename)
            thumb=im.copy();thumb.thumbnail((390,235))
            x,y=20+c*415,52+r*290
            d.text((x,y),name+' · '+theme.upper(),font=font,fill=(20,35,50))
            sheet.paste(thumb,(x+(390-thumb.width)//2,y+28))
            records.append(dict(viewport=name,viewport_width_dp=w,viewport_height_dp=h,theme=theme,**{k:g[k] for k in ['width_dp','height_dp','capacity','fit','dp_verified']}))
    sheet.save(build.OUT/'Infinity-Rails-RC3-Host-Visual-Review.png')
    (target/'geometry-review.json').write_text(json.dumps(records,indent=2))
    print('Generated 12 host XML illustrations; live renderer acceptance remains pending.')


if __name__=='__main__':main()
