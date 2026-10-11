#!/usr/bin/env python3
"""Render labelled XML geometry projections, never counterfeit Kodi screenshots.

Uses authored rectangles, packaged fonts and existing texture assets. Fixtures
replace runtime data; conditions, animations, native focus and 9-slice drawing
are not a Kodi implementation. Device evidence is still required.
"""
from pathlib import Path
import argparse, copy, json, re, math
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont, ImageChops
from validate_candidate import bounds, logical

HERE=Path(__file__).resolve().parent
def sliced(img,width,height,border,scale):
 """Approximate Kodi's fixed-corner border without stretching its rim."""
 src=min(int(border),img.width//2,img.height//2);dst=max(1,round(src*scale))
 if src==0:return img.resize((width,height))
 dst=min(dst,width//2,height//2);out=Image.new('RGBA',(width,height))
 sx=[0,src,img.width-src,img.width];sy=[0,src,img.height-src,img.height]
 dx=[0,dst,width-dst,width];dy=[0,dst,height-dst,height]
 for iy in range(3):
  for ix in range(3):
   w=dx[ix+1]-dx[ix];h=dy[iy+1]-dy[iy]
   if w>0 and h>0:out.paste(img.crop((sx[ix],sy[iy],sx[ix+1],sy[iy+1])).resize((w,h)),(dx[ix],dy[iy]))
 return out
LOCAL={146:'Type',21863:'Author',24051:'Version',24003:'Add-on information',20037:'Summary',24052:'Disclaimer',24096:'Broken',24054:'Install',24020:'Configure',24138:'Update',21340:'Auto-update',24069:'Versions',518:'Run',24022:'Enable',24021:'Disable',39024:'Dependencies',13406:'Select',20177:'Done',20178:'Shift',20179:'Caps',20182:'Space',20181:'Backspace',222:'Cancel'}
FIXTURE={'ListItem.AddonName':'Infinity UI Stability RC1','ListItem.AddonType':'Skin','ListItem.AddonCreator':'Infinity','ListItem.AddonVersion':'1.0.5.207',
 'ListItem.AddonSummary':'Preserves the approved Infinity design and native controls.',
 'ListItem.AddonDescription':'This is explicit sample text for geometry verification. Long descriptions remain inside their scrollable region. The skin uses the original Infinity theme, fonts and artwork. This projection cannot verify native interactions or rendering. '*14,
 'ListItem.AddonDisclaimer':'','ListItem.AddonBroken':'',
 'Window(Home).Property(KHC.Status)':'Needs attention',
 'Window(Home).Property(KHC.StatusDetail)':'Example reported status. Scan freshness requires backend verification.',
 'Window(Home).Property(KHC.LastScan)':'2026-10-11 01:37 (sample)',
 'Window(Home).Property(KHC.Baseline)':'Saved baseline record (sample)',
 'Window(Home).Property(KHC.Version)':'sample',
 'ListItem.Label':'Additional Link Info', 'ListItem.Label2':'Provider metadata • sample streaming source'}
FIXTURE['Container.FolderName']='Provider sources • explicit sample'

class Projection:
 def __init__(self,base,delta,version,profile,theme='dark',count=10,scroll=0):
  self.base=base;self.delta=delta;self.version=version;self.profile=profile;self.theme=theme;self.count=count;self.scroll=scroll
  self.w,self.h=logical(*profile);self.scale=min(840/self.w,1280/self.h)
  self.image=Image.new('RGBA',(round(self.w*self.scale),round(self.h*self.scale)),self.color('Base'))
  self.definitions={};self.variables={}
  for path in (base/'unified').glob('*.xml'):
   r=E.fromstring(self.read('unified/'+path.name))
   for n in r.findall('include'):
    if n.get('name'):self.definitions[n.get('name')]=n
   for n in r.findall('variable'):self.variables[n.get('name')]=n
  added=delta/'unified/Includes_InfinityUIRepair.xml'
  if version=='after':
   for n in E.parse(added).getroot():
    if n.tag=='variable':self.variables[n.get('name')]=n
  self.fonts={n.findtext('name'):(n.findtext('filename'),float(n.findtext('size'))) for n in E.fromstring(self.read('unified/Font.xml')).findall('.//font')}
 def read(self,name):
  path=self.delta/name if self.version=='after' and (self.delta/name).exists() else self.base/name
  return path.read_bytes()
 def value(self,name):
  vals=self.variables.get(name)
  if vals is None:return None
  index={'cinema':0,'OLED':1,'light':2,'dark':3}[self.theme]
  if name.startswith('InfinityLegacy') or name=='InfinityUIRepairSurface':return vals.findall('value')[index].text
  return vals.findall('value')[-1].text
 def color(self,token):
  if token=='Base':return {'dark':'#050a10','light':'#e5ebf2','OLED':'#000000','cinema':'#000000'}[self.theme]
  if token in ['Text','Secondary','Surface','Accent','Field','Danger']:
   token=self.value('InfinityLegacy'+token)
  if token=='$VAR[InfinityUIHealthStatusColor]':token=self.value('InfinityLegacyDanger')
  if token and token.startswith('$VAR['):
   name=token[5:-1];token=self.value(name) or self.value('InfinityLegacySecondary')
  if token and len(token)==8 and re.fullmatch('[A-Fa-f0-9]{8}',token):return tuple(int(token[i:i+2],16) for i in [2,4,6,0])
  return '#9eb2c4'
 def text(self,text):
  if not text:return ''
  if text.isdigit():return LOCAL.get(int(text),text)
  if text=='$VAR[AddonInfoHeading]':return 'Description'
  if text=='$VAR[AddonInfoDescription]':return FIXTURE['ListItem.AddonDescription']
  if text=='$VAR[InfinityUIHealthStatus]':return 'Needs attention'
  if text=='$VAR[SelectLabel]':return '10 items • sample'
  if text.startswith('$INFO[ListItem.AddonSummary,'):return FIXTURE['ListItem.AddonDescription']
  text=re.sub(r'\$LOCALIZE\[(\d+)\]',lambda m:LOCAL.get(int(m[1]),m[1]),text)
  text=re.sub(r'\$INFO\[([^\]]+)\]',lambda m:FIXTURE.get(m[1].split(',')[0],''),text)
  text=re.sub(r'\$VAR\[[^\]]+\]|\$PARAM\[[^\]]+\]','',text)
  return re.sub(r'\[/?(?:B|I|COLOR)[^\]]*\]','',text).replace('[CR]','\n')
 def resolved(self,c):
  c=copy.deepcopy(c)
  for inc in list(c.findall('include')):
   definition=self.definitions.get(inc.text or inc.get('content'))
   if definition is not None:
    for n in definition:
     if n.tag in ['param','definition']:continue
     if c.find(n.tag) is None:c.append(copy.deepcopy(n))
   c.remove(inc)
  return c
 def render_control(self,c,parent,forced=None):
  c=self.resolved(c);ident=c.get('id');kind=c.get('type')
  if ident in ['60','61','1188060','62','1000','313','314']:return
  vis=c.findtext('visible','')
  if c.get('id')=='400' or '!String.IsEmpty(ListItem.AddonDisclaimer)' in vis:return
  if 'Skin.HasSetting(KeyboardGraphicalTextures)' in vis and not vis.startswith('!'):return
  if 'Control.HasFocus' in vis and not vis.startswith('!'):return
  if ident in ['3','4','5','7','90'] and getattr(self,'selector',False):return
  px,py,pw,ph=parent;x,y,w,h=bounds(c,pw,ph) if forced is None else forced
  x+=px;y+=py
  if w<=0 or h<=0:return
  rect=(round(x*self.scale),round(y*self.scale),round((x+w)*self.scale),round((y+h)*self.scale))
  if kind=='list':
   layout=c.find('itemlayout')
   if layout is None:return
   snap=self.image.copy();rh=float(layout.get('height'));clip_box=tuple(max(0,min(v,self.image.width if i%2==0 else self.image.height)) for i,v in enumerate(rect))
   for index in range(12):
    if index*rh>h:break
    for child in layout.findall('control'):self.render_control(child,(x,y+index*rh,w,rh))
   crop=self.image.crop(clip_box);self.image=snap;self.image.paste(crop,clip_box[:2]);return
  if kind in ['group','grouplist']:
   if ident=='996':
    template=self.root.find(".//control[@id='1000']");rowheight=float(template.findtext('height'));gap=float(c.findtext('itemgap','0'))
    for index in range(self.count):
     item=copy.deepcopy(template);item.attrib.pop('id',None)
     itemlabel=item.find('label')
     if itemlabel is None:itemlabel=E.SubElement(item,'label')
     itemlabel.text=(['Resume from 01:04:58','Play from beginning'] if self.count==2 else ['Additional Link Info','Save to AllDebrid Cloud']+[f'Existing action {i}' for i in range(3,31)])[index]
     self.render_control(item,(x,y,w,h),(0,index*(rowheight+gap),w,rowheight))
    return
   layer=self.image;clip_box=tuple(max(0,min(v,layer.width if i%2==0 else layer.height)) for i,v in enumerate(rect))
   if kind=='grouplist':
    snap=layer.copy();position=-self.scroll if ident in ['1188000','1198899','1191888'] else 0
    horizontal=c.findtext('orientation')=='horizontal';gap=float(c.findtext('itemgap','0'))
    for child in c.findall('control'):
     child=self.resolved(child);_,_,cw,ch=bounds(child,w,h)
     self.render_control(child,(x,y,w,h),(position,0,cw,ch) if horizontal else (0,position,cw,ch))
     position+=(cw if horizontal else ch)+gap
    crop=self.image.crop(clip_box);self.image=snap;self.image.paste(crop,clip_box[:2]);return
   for child in c.findall('control'):self.render_control(child,(x,y,w,h))
   return
  draw=ImageDraw.Draw(self.image)
  if kind=='image':
   tex=c.find('texture');name=tex.text if tex is not None else '';tint=tex.get('colordiffuse') if tex is not None else None
   if ident=='999' and self.context_height is not None:
    rect=(rect[0],rect[1],rect[2],rect[1]+max(1,round(self.context_height*self.scale)))
   path=self.base/'media'/name if name and not name.startswith('$') else None
   if path and path.is_file():
    img=Image.open(path).convert('RGBA');cw=max(1,rect[2]-rect[0]);ch=max(1,rect[3]-rect[1])
    if c.findtext('aspectratio')=='keep':img.thumbnail((cw,ch));ix=rect[0]+(cw-img.width)//2;iy=rect[1]+(ch-img.height)//2
    else:
     border=tex.get('border') if tex is not None else None
     img=sliced(img,cw,ch,border,self.scale) if border and border.isdigit() else img.resize((cw,ch));ix,iy=rect[:2]
    if tint:
     color=self.color(tint);color=Image.new('RGBA',img.size,color);img=ImageChops.multiply(img,color)
    self.image.alpha_composite(img,(ix,iy))
   elif name and ('$VAR[InfinityPolishIcon' in name or 'ListItem' in name or 'DialogSelectImage' in name):
    draw.rounded_rectangle(rect,8,fill=self.color('Field'),outline=self.color('Accent'));draw.text((rect[0]+2,rect[1]+4),'Art',fill=self.color('Secondary'),font=ImageFont.truetype(str(self.base/'fonts/Roboto-Regular.ttf'),max(5,round(14*self.scale))))
   return
  if kind in ['button','radiobutton','edit','spincontrol','slider']:
   draw.rounded_rectangle(rect,max(2,round(12*self.scale)),fill=self.color('Field'))
   if ident=='995' or (not self.text(c.findtext('label')) and ('close' in c.findtext('texturenofocus','').lower())):
    draw.text((rect[0]+8,rect[1]+1),'×',fill=self.color('Text'),font=ImageFont.truetype(str(self.base/'fonts/Roboto-Regular.ttf'),max(12,round(42*self.scale))));return
  if kind not in ['label','textbox','button','radiobutton','edit']:return
  text=self.text(c.findtext('label'))
  if ident=='311':text='Keyboard • sample search'
  if ident=='312':text='Infinity'
  if ident and ident.isdigit() and 100<=int(ident)<=171:text=chr(65+(int(ident)%20)%26)
  if not text:return
  fontfile,size=self.fonts.get(c.findtext('font'),('Roboto-Regular.ttf',28))
  font=ImageFont.truetype(str(self.base/'fonts'/fontfile),max(5,round(size*self.scale)))
  color=self.color(c.findtext('textcolor','$VAR[InfinityLegacyText]'))
  tx=rect[0]+round(float(c.findtext('textoffsetx','0'))*self.scale);ty=rect[1]+round(float(c.findtext('textoffsety','0'))*self.scale)
  maxwidth=max(1,rect[2]-tx);maxheight=max(1,rect[3]-ty)
  if kind=='textbox' or c.findtext('wrapmultiline')=='true':
   lines=[]
   for line in text.split('\n'):
    current=''
    for word in line.split():
     if font.getlength((current+' '+word).strip())>maxwidth and current:lines.append(current);current=word
     else:current=(current+' '+word).strip()
    lines.append(current)
  else:
   while text and font.getlength(text)>maxwidth:text=text[:-1]
   lines=[text]
  lineheight=round(size*self.scale*1.2)
  if c.findtext('aligny')=='center':ty+=max(0,(maxheight-lineheight)//2)
  if c.findtext('align')=='center' and len(lines)==1:tx+=max(0,(maxwidth-round(font.getlength(lines[0])))//2)
  for index,line in enumerate(lines):
   if index>0 and (index+1)*lineheight>maxheight+2:break
   draw.text((tx,ty+index*lineheight),line,fill=color,font=font)
 def render(self,file):
  self.selector=file=='Selector.xml'
  if file in ['Selector.xml','Provider.xml']:
   source='Includes_InfinityLegacy.xml' if self.selector else 'View_50_List.xml'
   name='InfinityLegacy_DefaultDialogSelectLayout' if self.selector else 'InfinityPluginDirectoryCompact'
   inc=E.fromstring(self.read('unified/'+source)).find("include[@name='%s']"%name)
   root=E.Element('window');controls=E.SubElement(root,'controls');controls.append(copy.deepcopy(inc.find('control')))
  else:root=E.fromstring(self.read('unified/'+file))
  self.root=root;self.context_height=None
  if file=='DialogContextMenu.xml':
   if self.version=='before':
    bg=root.find(".//control[@id='999']");menu=root.find(".//control[@id='996']")
    maxbg=bounds(bg,self.w,self.h)[3];maxlist=bounds(menu,self.w,self.h)[3]
    self.context_height=maxbg-maxlist+min(maxlist,self.count*76+(self.count-1)*6)
   else:
    panel=root.find(".//control[@id='9900']");_,_,pw,ph=bounds(panel,self.w,self.h)
    inset=panel.find("control[@id='9901']");_,_,iw,ih=bounds(inset,pw,ph)
    self.context_height=104+min(ih,self.count*82+(self.count-1)*6)
  for c in root.find('controls').findall('control'):self.render_control(c,(0,0,self.w,self.h))
  return self.finish(file)
 def finish(self,title):
  img=self.image.convert('RGB');banner=Image.new('RGB',(img.width,img.height+76),'#101823');banner.paste(img,(0,76))
  draw=ImageDraw.Draw(banner);font=ImageFont.truetype(str(self.base/'fonts/Roboto-Regular.ttf'),14)
  draw.text((12,8),'XML layout projection — NOT a Kodi screenshot',font=font,fill='#ffffff')
  draw.text((12,29),f'{self.version.upper()} • {title} • {self.profile[0]}×{self.profile[1]} • {self.theme}',font=font,fill='#abc0d3')
  draw.text((12,50),'Fixture data; authored bounds/fonts; native behaviour untested',font=font,fill='#abc0d3')
  return banner

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 files=['DialogAddonInfo.xml','DialogContextMenu.xml','Custom_1188_InfinityHealthCenter.xml','Custom_1198_InfinityNav.xml','Custom_1191_InfinitySystemHub.xml','DialogKeyboard.xml','Provider.xml','Selector.xml']
 images=[]
 for file in files:
  for profile in [(412,915),(915,412)]:
   for version in ['before','after']:
    proj=Projection(a.base,HERE/'skin-delta',version,profile,count=2)
    img=proj.render(file);name=f'{file[:-4]}-{profile[0]}x{profile[1]}-{version}.png';img.save(a.out/name);images.append({'file':file,'profile':list(profile),'version':version,'image':name})
 for theme in ['light','OLED','cinema']:
  proj=Projection(a.base,HERE/'skin-delta','after',(673,790),theme)
  name='HealthCenter-'+theme+'.png';proj.render('Custom_1188_InfinityHealthCenter.xml').save(a.out/name);images.append({'file':'Custom_1188_InfinityHealthCenter.xml','profile':[673,790],'version':'after','theme':theme,'image':name})
 proj=Projection(a.base,HERE/'skin-delta','after',(412,915),scroll=2000)
 proj.render('Custom_1188_InfinityHealthCenter.xml').save(a.out/'HealthCenter-lower-scroll.png')
 for count in [1,10,30]:
  proj=Projection(a.base,HERE/'skin-delta','after',(915,412),count=count)
  name=f'Context-{count}-actions.png';proj.render('DialogContextMenu.xml').save(a.out/name);images.append({'file':'DialogContextMenu.xml','profile':[915,412],'version':'after','actions':count,'image':name})
 (a.out/'projection-index.json').write_text(json.dumps({'kind':'AUTHORED_XML_PROJECTION_NOT_RUNTIME_SCREENSHOT','assumptions':'Native conditions, animation, 9-slice, focus and dynamic data not implemented; explicit fixtures only. No physical device tested.','images':images},indent=2)+'\n')
 print(json.dumps({'projection_images':len(images)+1,'physical_device_tested':False}))

if __name__=='__main__':main()
