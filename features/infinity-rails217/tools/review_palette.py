"""Source palette review drawing, not a Kodi/device screenshot."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from zipfile import ZipFile
import xml.etree.ElementTree as ET
with ZipFile('delivery/skin.infinity.diggz-1.0.5.217-Custom-Rails-RC3-TEST.zip') as z:r=ET.fromstring(z.read('skin.infinity.diggz/unified/Includes_InfinityRails.xml'))
colors={n.removeprefix('InfinityRails'):[x.text[-6:] for x in node] for node in r.findall('variable') if (n:=node.get('name')) in ['InfinityRailsSurface','InfinityRailsField','InfinityRailsText','InfinityRailsSecondary','InfinityRailsBorder','InfinityRailsAccent','InfinityRailsFocusedText']}
im=Image.new('RGB',(1230,665),'#f2f6fa');d=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';f=ImageFont.truetype(font,18);small=ImageFont.truetype(font,15);heading=ImageFont.truetype(bold,18)
d.text((30,22),'SOURCE PALETTE REVIEW — reference drawing, not Kodi rendering',font=heading,fill='#102237')
for idx,label in enumerate(['LIGHT','OLED','DARK']):
 x=30+idx*400;y=106;w=370;h=440;c={n:'#'+v[idx] for n,v in colors.items()}
 d.text((x,72),label,font=heading,fill='#102237');d.rounded_rectangle((x,y,x+w,y+h),radius=18,fill=c['Surface'],outline=c['Border'],width=2)
 d.text((x+22,y+24),'INFINITY — RAIL OPTIONS',font=heading,fill=c['Text']);d.text((x+w-30,y+22),'×',font=heading,fill=c['Accent']);d.text((x+22,y+57),'Open Add-on · Empflix',font=small,fill=c['Secondary'])
 for i,t in enumerate(['Open Add-on · Empflix','Move / Reorder','Remove from TV Show Add-ons','Add-on Settings','Cancel']):
  rowy=y+99+i*61;focus=i==2;d.rounded_rectangle((x+18,rowy,x+w-18,rowy+55),radius=10,fill=c['Accent'] if focus else c['Field']);d.text((x+30,rowy+18),t,font=small,fill=c['FocusedText'] if focus else c['Text'])
d.text((30,580),'The packaged XML controls/native layout still require Fold validation.',font=f,fill='#102237');d.text((30,610),'Normal · Cinema · Compact · Two-Pane share this palette and saved configuration.',font=small,fill='#50647a')
im.save('project/evidence/PALETTE-REFERENCE.png')
