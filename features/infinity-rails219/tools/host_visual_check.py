"""Draw owned dialog geometry with its actual Roboto font. NOT a Kodi renderer."""
import argparse
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'addons/script.infinity.rails/resources'))
from lib.menu import geometry

p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);args=p.parse_args()
fontfile=args.baseline/'fonts/Roboto-Regular.ttf'
font=ImageFont.truetype(str(fontfile),34);small=ImageFont.truetype(str(fontfile),28)
header=ImageFont.truetype(str(fontfile),26)
viewports=[('Cover portrait',1080,2400),('Cover landscape',2400,1080),('Inner portrait',1536,2152),('Inner landscape',2152,1536),('Narrow split',360,640),('Small floating',640,360)]
colors={'Light':('#F7FAFD','#FFFFFF','#102237','#50647A','#EAF1F7','#B8C9D8','#006DCB'), 'Dark':('#03070C','#0A111A','#F2F6FB','#9EB2C4','#131D29','#29445C','#24A8FF'), 'OLED':('#000000','#000000','#FFFFFF','#A5B7C8','#000000','#223A50','#24A8FF')}
canvas=Image.new('RGB',(1500,6*470+110),'#EEF2F6');d=ImageDraw.Draw(canvas)
d.text((24,20),'RC3 — host geometry and theme preview',font=header,fill='#102237')
d.text((24,58),'Illustrative layout check; not a Kodi screenshot or a Fold test.',font=header,fill='#50647A')
report=[]
labels=['Open Add-on','Move / Reorder','Remove from TV Show Add-ons','Add-on Settings','Cancel']
for col,(theme,palette) in enumerate(colors.items()):
 bg,surface,text,secondary,field,border,accent=palette
 for row,(name,w,h) in enumerate(viewports):
  b=geometry(w,h,len(labels));frame=Image.new('RGB',(b.width,b.height),bg);draw=ImageDraw.Draw(frame)
  draw.rounded_rectangle((0,0,b.width-1,b.height-1),radius=24,fill=surface,outline=border,width=2)
  for msg,pos,ff,fill,maxwidth in [('INFINITY — RAIL OPTIONS',(24,26),small,text,b.width-112),('Empflix',(24,72),small,secondary,b.width-48)]:
   layer=Image.new('RGBA',(max(1,maxwidth),48),(0,0,0,0));ImageDraw.Draw(layer).text((0,0),msg,font=ff,fill=fill);frame.paste(layer,pos,layer)
  draw.line((b.width-56,30,b.width-36,50),fill=text,width=3);draw.line((b.width-36,30,b.width-56,50),fill=text,width=3)
  rows_visible=min(len(labels),b.list_height//82)
  for i,label in enumerate(labels[:rows_visible]):
   y=120+i*82
   draw.rounded_rectangle((16,y+3,b.width-17,y+79),radius=16,fill=field,outline=accent if i==0 else field,width=2)
   layer=Image.new('RGBA',(max(1,b.width-80),76),(0,0,0,0));ImageDraw.Draw(layer).text((0,16),label,font=font,fill=text);frame.paste(layer,(40,y+3),layer)
  scale=min(450/frame.width,380/frame.height)
  frame=frame.resize((round(frame.width*scale),round(frame.height*scale)),Image.Resampling.LANCZOS)
  x=col*500+(500-frame.width)//2;y=110+row*470
  d.text((col*500+24,y+10),theme+' • '+name,font=header,fill='#102237')
  canvas.paste(frame,(x,y+58))
  if rows_visible<len(labels):d.text((col*500+24,y+430),'Scrollable actions',font=header,fill='#50647A')
  report.append({'theme':theme,'viewport':[w,h],'dialog':b.__dict__,'rows_visible':rows_visible,'labels_require_scrolling':sum(font.getlength(l)>b.width-80 for l in labels)})
canvas.save(HERE/'evidence/host-visual-preview.png')
(HERE/'evidence/visual-check.json').write_text(json.dumps({'scope':'Pillow layout preview with actual baseline font; not skin textures composited by Kodi; all 14 XML profiles checked by regression suite','view_mode_ui':'The same owned dialog is used by Normal/Cinema/Compact/Two-Pane; each home retains its own original geometry','checks':report,'physical_device_verified':False},indent=2)+'\n')
