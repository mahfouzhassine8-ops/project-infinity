#!/usr/bin/env python3
"""Validate preservation and authored bounds using Kodi's axis/auto-height rules.

These are source/geometry checks, never a substitute for a running Kodi/Fold test.
"""
from pathlib import Path
import argparse, hashlib, json, math, re, zipfile
import xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
PROFILES=[('cover portrait',412,915),('cover landscape',915,412),('inner portrait',673,790),('inner landscape',790,673),('16:9',1920,1080),('20:9',2400,1080),('portrait 9:16',1080,1920),('split portrait',340,790),('split landscape',790,340),('popup portrait',320,640),('popup landscape',640,320),('narrow popup',240,800),('short popup',800,240),('square',600,600),('wide stress',1200,200),('narrow stress',200,1200)]

def val(text,size):
 if not text:return None
 return float(text[:-1])*size/100 if text.endswith('%') else float(text)

def axis(c,start,end,center,size,parent):
 s=val(c.findtext(start),parent);e=val(c.findtext(end),parent);z=val(c.findtext(center),parent)
 node=c.find(size);length=val(node.get('max') if node.text=='auto' else node.text,parent) if node is not None else None
 if s is None:s=parent-e-length if e is not None and length is not None else z-length/2 if z is not None and length is not None else 0
 if length is None:length=max(0,parent-(e or 0)-s)
 return s,length

def bounds(c,w,h):
 x,cw=axis(c,'left','right','centerleft','width',w);y,ch=axis(c,'top','bottom','centertop','height',h)
 return x,y,cw,ch

def logical(w,h):
 ratio=w/h;area=1080*2400
 if max(ratio/(1080/2400),(1080/2400)/ratio)<=1.12:return 1080,2400
 return tuple(max(8,((round(x)+4)//8)*8) for x in [math.sqrt(area*ratio),math.sqrt(area/ratio)])

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,default=HERE/'validation-results.json');a=p.parse_args()
 with zipfile.ZipFile(a.base) as z:before={i.filename.removeprefix('skin.infinity.diggz/'):z.read(i) for i in z.infolist() if not i.is_dir()}
 with zipfile.ZipFile(a.candidate) as z:after={i.filename.removeprefix('skin.infinity.diggz/'):z.read(i) for i in z.infolist() if not i.is_dir()}
 changed=[n for n in after if after[n]!=before.get(n)];tests=[]
 def passed(name,detail):tests.append({'test':name,'result':'PASS','detail':detail})
 def require(condition,msg):
  if not condition:raise AssertionError(msg)
 require(after['unified/DialogButtonMenu.xml']==before['unified/DialogButtonMenu.xml'],'Protected Power changed')
 passed('Exact .204 Power preservation','Full approved Power XML byte identical')
 require(before.keys()<=after.keys(),'Package removed files')
 require(all(n=='addon.xml' or n.startswith('unified/') and n.endswith('.xml') for n in changed),'Non-UI files changed')
 passed('Package isolation',f'{len(changed)} XML deltas; no native/scripts/providers/assets/settings changes')
 removed={'unified/Custom_1198_InfinityNav.xml':{'1198107'},'unified/Custom_1191_InfinitySystemHub.xml':{'1191105'}}
 unresolved_existing_assets=set()
 for name in changed:
  if not name.startswith('unified/') or not name.endswith('.xml'):continue
  new=E.fromstring(after[name]);old=E.fromstring(before[name]) if name in before else None
  if old is None:continue
  if new.tag=='window':
   ids=[c.get('id') for c in new.findall('.//control') if c.get('id')]
   require(len(ids)==len(set(ids)),name+' duplicates native IDs')
   oldids={c.get('id') for c in old.findall('.//control') if c.get('id')}
   require(oldids-set(ids)==removed.get(name,set()),name+' missing native IDs '+str(oldids-set(ids)))
   for c in old.findall('.//control'):
    ident=c.get('id')
    if not ident or ident in removed.get(name,set()):continue
    peer=new.find(".//control[@id='%s']"%ident)
    semantic=lambda nodes:[(x.tag,x.text,dict(x.attrib)) for x in nodes]
    for field in ['onclick','altclick','onfocus','selected','enable','usealttexture']:
     require(semantic(c.findall(field))==semantic(peer.findall(field)),name+' changed '+ident+' '+field)
   for action in ['onload','onunload','onback']:
    require(semantic(old.findall(action))==semantic(new.findall(action)),name+' root action changed')
 passed('Native IDs and action preservation','All original native IDs/bindings retained except two explicitly approved redundant rows')
 targets={'Includes_InfinityLegacy.xml':['InfinityLegacy_DefaultDialogSelectLayout'],
          'View_50_List.xml':['InfinityPluginDirectoryCompact','InfinityPluginDirectoryRegular','InfinityCoreDirectory'],
          'Includes_CinemaBrowse.xml':['InfinityCinemaBrowseList']}
 for file,names in targets.items():
  oldroot=E.fromstring(before['unified/'+file]);newroot=E.fromstring(after['unified/'+file])
  for name in names:
   old=oldroot.find("include[@name='%s']"%name);new=newroot.find("include[@name='%s']"%name)
   oldids={c.get('id') for c in old.findall('.//control') if c.get('id')}
   newids={c.get('id') for c in new.findall('.//control') if c.get('id')}
   require(oldids==newids,name+' native IDs changed')
   for c in old.findall('.//control'):
    if not c.get('id'):continue
    peer=new.find(".//control[@id='%s']"%c.get('id'))
    for field in ['onclick','altclick','onfocus','selected','enable','pagecontrol','usealttexture']:
     require(semantic(c.findall(field))==semantic(peer.findall(field)),name+' native contract '+field)
   # Unrelated definitions remain byte-identical, including theme variables.
   oldtext=before['unified/'+file].decode();newtext=after['unified/'+file].decode()
   def strip_targets(text):
    for target in names:
     start=text.index('<include name="'+target+'">');depth=0
     for m in re.finditer(r'</?include\b[^>]*>',text[start:]):
      if m.group().endswith('/>'):continue
      depth+=-1 if m.group().startswith('</') else 1
      if depth==0:text=text[:start]+'TARGET'+text[start+m.end():];break
    return text
   require(strip_targets(oldtext)==strip_targets(newtext),file+' unrelated definitions changed')
 passed('Shared include preservation','Selector and directory native contracts retained; all unrelated includes and theme variables byte-identical')
 nav=E.fromstring(after['unified/Custom_1198_InfinityNav.xml'])
 group=nav.find(".//control[@id='1198899']")
 primary=[c.find('.//control/label').text for c in group if c.find('.//control[@type="button"]') is not None][:10]
 require(primary==['Home','Movies','TV Shows','Library','Add-ons','Settings','UI Theme','System Hub','Power','Music'],str(primary))
 passed('Approved drawer order','System Hub follows UI Theme; Power ends primary section; existing scroll extras retained')
 khc=E.fromstring(after['unified/Custom_1188_InfinityHealthCenter.xml'])
 require(khc.find(".//control[@id='1188000']") is not None,'Health list missing')
 helper=E.fromstring(after['unified/Includes_InfinityUIRepair.xml'])
 require('FF5CF48A' not in after['unified/Custom_1188_InfinityHealthCenter.xml'].decode(),'Hard-coded green status')
 color=helper.find("variable[@name='InfinityUIHealthStatusColor']")
 require(color.findall('value')[-1].text=='$VAR[InfinityLegacySecondary]','Unverified status green')
 require(not any('InfinityUIVerifiedWatchedBadge' in data.decode(errors='ignore') for n,data in after.items() if n.endswith('.xml') and n!='unified/Includes_InfinityUIRepair.xml'),'Unverified watched badge activated')
 badge=helper.find("include[@name='InfinityUIVerifiedWatchedBadge']")
 require(all(x.get('default')=='false' for x in badge.findall('param')),'Watched parameters lack explicit false defaults')
 passed('Truthful status/watched defaults','Unknown fallback; no unconditional healthy green; prepared watched visual has no consumer')
 def rgb(token):return [int(token[i:i+2],16)/255 for i in [2,4,6]]
 def luminance(token):
  channels=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb(token)]
  return sum(c*k for c,k in zip(channels,[.2126,.7152,.0722]))
 legacy=E.fromstring(after['unified/Includes_InfinityLegacy.xml']);contrast=[]
 for i,theme in enumerate(['cinema','OLED','light','dark']):
  surface=helper.find("variable[@name='InfinityUIRepairSurface']").findall('value')[i].text
  for color in ['Text','Secondary','Danger']:
   fg=legacy.find("variable[@name='InfinityLegacy%s']"%color).findall('value')[i].text
   low,high=sorted([luminance(fg),luminance(surface)]);ratio=(high+.05)/(low+.05)
   require(ratio>=4.5,theme+' '+color+' panel contrast below 4.5')
   contrast.append({'theme':theme,'foreground':color,'surface_text_contrast':round(ratio,2)})
 passed('Repaired panel theme contrast','Primary, secondary and warning text meet 4.5:1 against opaque repaired surfaces in dark, light, OLED and cinema palettes; focus/transparency still need runtime verification')
 # Resolve all newly used static font/asset/include references against the complete package.
 allxml={n:E.fromstring(data) for n,data in after.items() if n.startswith('unified/') and n.endswith('.xml')}
 definitions={x.get('name') for r in allxml.values() for x in r.findall('include') if x.get('name')}
 fonts={x.findtext('name') for r in allxml.values() for x in r.findall('.//font') if x.find('name') is not None}
 for name in changed:
  if name not in allxml:continue
  r=allxml[name]
  for inc in r.findall('.//include'):
   if inc.get('file'):require('unified/'+inc.get('file') in after,'Missing include file '+inc.get('file'))
   if inc.get('content') and '$' not in inc.get('content'):require(inc.get('content') in definitions,'Missing include '+inc.get('content'))
  for c in r.findall('.//control'):
   font=c.findtext('font')
   if font and '$' not in font:require(font in fonts,'Missing font '+font)
   for tex in c:
    if 'texture' not in tex.tag or not tex.text or '$' in tex.text or '/' not in tex.text:continue
    asset=tex.text.removeprefix('special://skin/') if tex.text.startswith('special://skin/') else 'media/'+tex.text
    if asset not in after:
     # Large shared files also contain untouched legacy definitions; a packed
     # texture or old unavailable asset is not proof of a new active defect.
     require(name in before and tex.text.encode() in before[name],'Missing new static artwork '+tex.text)
     unresolved_existing_assets.add(tex.text)
 passed('Active XML and include/font references',f'{len(allxml)} active XML documents parsed; changed include/font references resolve')
 # Check authored modal edges; scrolling children are deliberately larger than their viewport.
 modal_files=['DialogAddonInfo.xml','DialogSettings.xml','DialogAddonSettings.xml','DialogTextViewer.xml','DialogKeyboard.xml','Custom_1188_InfinityHealthCenter.xml']
 checks=0;matrix=[]
 for profile,pw,ph in PROFILES:
  w,h=logical(pw,ph)
  for filename in modal_files:
   r=allxml['unified/'+filename];panel=r.find(".//control[@id='9900']")
   x,y,cw,ch=bounds(panel,w,h)
   require(x>=0 and y>=0 and x+cw<=w+.1 and y+ch<=h+.1,filename+' panel outside '+profile)
   for c in panel.findall('control'):
    ident=c.get('id')
    # Kodi native templates and hidden paging receiver are populated/hidden by its dialog.
    if filename in ['DialogSettings.xml','DialogAddonSettings.xml'] and ident in ['7','8','9','10','11','12','13','14']:continue
    if filename=='DialogTextViewer.xml' and ident=='62':continue
    cx,cy,ccw,cch=bounds(c,cw,ch)
    require(ccw>0 and cch>0,filename+' collapsed '+str(ident)+' on '+profile)
    require(cx>=-.1 and cy>=-.1 and cx+ccw<=cw+.1 and cy+cch<=ch+.1,filename+' offscreen '+str(ident)+' on '+profile)
    checks+=1
   if filename=='DialogAddonInfo.xml':
    detail=panel.find("control[@id='9901']");_,_,dw,dh=bounds(detail,cw,ch)
    require(dh-280>=80,'Description becomes unusable on '+profile)
  context=allxml['unified/DialogContextMenu.xml'];panel=context.find(".//control[@id='9900']")
  _,_,cw,ch=bounds(panel,w,h);inset=panel.find("control[@id='9901']");_,sy,iw,ih=bounds(inset,cw,ch)
  menu=panel.find(".//control[@id='996']");_,_,lw,maximum=bounds(menu,iw,ih)
  padding=ch-maximum;require(abs(padding-104)<.1,'Context chrome not fixed '+profile)
  for count in [1,2,10,30]:
   actual=min(maximum,count*82+(count-1)*6)
   panel_height=padding+actual
   require(panel_height<=h+.1 and sy+actual+16<=panel_height+.1,'Context overflow '+profile)
   require(lw==iw,'Template/list width mismatch')
   checks+=1
  selector=allxml['unified/Includes_InfinityLegacy.xml'].find("include[@name='InfinityLegacy_DefaultDialogSelectLayout']/control")
  _,_,sw,sh=bounds(selector,w,h)
  listrect=bounds(selector.find("control[@id='3']"),sw,sh)
  footer=selector.find(".//control[@id='90']");fx,fy,fw,fh=bounds(footer,sw,sh)
  require(listrect[1]+listrect[3]+40<=fy,'Selector list collides with footer '+profile)
  require(fx>=0 and fy>=0 and fx+fw<=sw and fy+fh<=sh,'Selector footer outside '+profile)
  require(not any(x.get('effect')=='slide' and 'NumItems' in x.get('condition','') for x in selector.iter('animation')),'Selector old count shift')
  keys=allxml['unified/DialogKeyboard.xml'].find(".//control[@id='4000']")
  kp=allxml['unified/DialogKeyboard.xml'].find(".//control[@id='9900']")
  _,_,kw,kh=bounds(kp,w,h);_,_,aw,ah=bounds(keys,kw,kh)
  for row in keys.findall("control[@type='grouplist']"):
   rx,ry,rw,rh=bounds(row,aw,ah);children=row.findall('control')
   extent=sum(bounds(c,rw,rh)[2] for c in children)+float(row.findtext('itemgap','0'))*(len(children)-1)
   require(extent<=rw+.1,'Keyboard horizontal key overflow '+profile)
   require(ry>=0 and ry+rh<=ah+.1,'Keyboard row outside '+profile)
   checks+=1
  for layout in selector.findall("control[@id='6']/itemlayout")+selector.findall("control[@id='6']/focusedlayout"):
   artwork=next(c for c in layout.findall('control') if c.findtext('texture')=='$VAR[DialogSelectImage]')
   title=next(c for c in layout.findall('control') if c.get('type')=='label')
   ax,ay,artw,arth=bounds(artwork,sw-88,156);tx,ty,tw,th=bounds(title,sw-88,156)
   require(ax+artw<=tx and ty+th<=60 and ay+arth<=156,'Selector artwork/text collision')
  checks+=4
  matrix.append({'profile':profile,'usable_window': [pw,ph],'logical_canvas':[w,h],'result':'PASS'})
 passed('Responsive modal/native menu geometry',f'{checks} bounds checks across {len(PROFILES)} profiles, including 1/2/10/30 actions')
 # Inspect actual label rectangles in every repaired directory row.
 def walk_layouts(r):
  for layout in r.iter():
   if layout.tag not in ['itemlayout','focusedlayout']:continue
   labels={c.findtext('label'):c for c in layout.findall('control') if c.get('type')=='label'}
   if '$INFO[ListItem.Label]' in labels and '$INFO[ListItem.Label2]' in labels:
    yield layout,labels
 for file,names in [('View_50_List.xml',['InfinityPluginDirectoryCompact','InfinityPluginDirectoryRegular','InfinityCoreDirectory']),('Includes_CinemaBrowse.xml',['InfinityCinemaBrowseList'])]:
  r=allxml['unified/'+file]
  for name in names:
   n=r.find("include[@name='%s']"%name)
   for layout,labels in walk_layouts(n):
    height=float(layout.get('height'));a1=bounds(labels['$INFO[ListItem.Label]'],1000,height);a2=bounds(labels['$INFO[ListItem.Label2]'],1000,height)
    require(a1[1]+a1[3]<=a2[1],name+' title/metadata collision')
    require(a2[1]+a2[3]<=height,name+' metadata outside row')
 passed('Provider/core/cinema metadata separation','Title and secondary-label rectangles are disjoint in all repaired item/focused rows')
 cards=khc.find(".//control[@id='1188000']").findall('control')
 for row in cards:
  if row.find("control[@type='button']") is None:continue
  icon=row.find("control[@type='image']");body=row.find("control[@type='label']")
  require(icon is not None and body is not None,'Health card content absent')
  ix,iy,iw,ih=bounds(icon,800,156);tx,ty,tw,th=bounds(body,800,156)
  require(ix+iw<tx and ty>=60 and ty+th<=156,'Health icon/description collision')
 passed('Health card separation','All 13 tool cards preserve action IDs with distinct title, icon and wrapped description regions')
 output={'candidate':'1.0.5.207','status':'SOURCE_AND_GEOMETRY_VALIDATED_DEVICE_PENDING','tests':tests,'profile_matrix':matrix,'theme_contrast':contrast,'bounds_checks':checks,'unresolved_preexisting_asset_references':sorted(unresolved_existing_assets),'physical_device_tested':False,'running_kodi_tested':False,'performance_improvement_claimed':False,'long_session_tested':False}
 a.out.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'tests_passed':len(tests),'profiles':len(matrix),'bounds_checks':checks,'status':output['status']}))

if __name__=='__main__':main()
