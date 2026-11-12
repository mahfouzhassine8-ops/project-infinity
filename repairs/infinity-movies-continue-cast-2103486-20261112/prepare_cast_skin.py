"""Two approved Cast controls in the sole declared, adaptive skin directory.

Preserve every original byte except the two navigation edges beside the new
icon. No legacy layout, Home widget, TV layout or Cobra member is edited.
"""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,re,sys,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
BASE=HERE/'baseline/skin.infinity.diggz'
OUT=HERE/'overlay/skin.infinity.diggz'
def block(text,start):
 depth=0
 for token in re.finditer(r'<control\b[^>]*>|</control>',text[start:]):
  value=token.group();depth+=-1 if value=='</control>' else (0 if value.endswith('/>') else 1)
  if depth==0:return text[start:start+token.end()]
 raise ValueError('Unclosed source control')
def prepare(maven):
 manifest=ET.parse(BASE/'addon.xml').getroot()
 assert [r.get('folder') for r in manifest.findall('./extension/res')]==['unified']
 source=(BASE/'unified/VideoOSD.xml').read_text()
 assert 'id="6121"' not in source and 'id="6122"' not in source
 button=source.index('<control type="button" id="257">')
 start=source.rindex('<control type="group">',0,button);drawer=block(source,start)
 icon=ET.fromstring(drawer);button=icon.find("control[@id='257']")
 button.set('id','6121');button.find('description').text='Cast to Device'
 for onclick in list(button.findall('onclick')):button.remove(onclick)
 ET.SubElement(button,'onclick').text='InfinityCast()'
 button.find('onleft').text='257';button.find('onright').text='264'
 button.find('enable').text='System.Platform.Android + Player.HasVideo + !Skin.HasSetting(Infinity.PlayerDrawerOpen)'
 for animation in button.findall('animation'):
  animation.set('condition',animation.get('condition','').replace('(257)','(6121)'))
 image=icon.find("control[@type='image']")
 image.find('texture').text='infinity_cast/cast.png'
 ET.SubElement(image,'visible').text='!String.IsEqual(Window(Home).Property(Infinity.Cast.Connected),true)'
 connected=copy.deepcopy(image);connected.find('texture').set('colordiffuse','FF00C1E0')
 connected.find('visible').text='String.IsEqual(Window(Home).Property(Infinity.Cast.Connected),true)';icon.append(connected)
 ET.indent(icon,space='  ');icon_text=ET.tostring(icon,encoding='unicode')
 now_start=source.index('<control type="button" id="270">');now=block(source,now_start)
 menu=ET.fromstring(now);menu.set('id','6122');menu.find('label').text='Cast to Device'
 ET.SubElement(menu,'enable').text='System.Platform.Android + Player.HasVideo'
 actions=menu.findall('onclick');assert [n.text for n in actions]==['Skin.Reset(Infinity.PlayerDrawerOpen)','SetFocus(257)']
 ET.SubElement(menu,'onclick').text='InfinityCast()'
 for animation in menu.findall('animation'):
  animation.set('condition',animation.get('condition','').replace('(270)','(6122)'))
 ET.indent(menu,space='  ');menu_text=ET.tostring(menu,encoding='unicode')
 changed=source.replace(drawer,drawer.replace('<onright>264</onright>','<onright>6121</onright>',1)+'\n'+icon_text,1)
 volume_start=changed.index('<control type="button" id="264">');volume=block(changed,volume_start)
 assert '<onleft>257</onleft>' in volume
 replacement=volume.replace('<onleft>257</onleft>','<onleft>6121</onleft>',1)
 changed=changed.replace(volume,replacement,1).replace(now,now+'\n'+menu_text,1)
 # Reversibility is a preservation assertion, not a screenshot/layout PASS.
 restored=changed.replace('\n'+icon_text,'',1).replace('\n'+menu_text,'',1)
 restored=restored.replace(drawer.replace('<onright>264</onright>','<onright>6121</onright>',1),drawer,1)
 restored=restored.replace(replacement,volume,1);assert restored==source
 tree=ET.fromstring(changed)
 row=tree.find(".//control[@id='290']")
 assert [g.find('control').get('id') for g in row.findall('control')[:3]]==['257','6121','264']
 menu_row=tree.find(".//control[@id='291']")
 assert [c.get('id') for c in menu_row.findall('control')[:3]]==['270','6122','272']
 target=OUT/'unified/VideoOSD.xml';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(changed)
 lock=json.loads((Path(maven)/'SDK-DEPENDENCIES.json').read_text())
 row=next(r for r in lock['artifacts'] if r['coordinate']=='androidx.mediarouter:mediarouter:1.3.0')
 artifact=Path(maven)/row['file'];assert hashlib.sha256(artifact.read_bytes()).hexdigest()==row['sha256']
 member='res/drawable-xhdpi-v4/ic_mr_button_disconnected_dark.png'
 with ZipFile(artifact) as z:data=z.read(member)
 target=OUT/'media/infinity_cast/cast.png';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 result=dict(status='PASS_TWO_CONTROL_SOURCE_PRESERVATION',active_layout='unified',
  existing_controls='All unchanged except Drawer right and Volume left edges to new Cast control',
  other_layouts_changed=False,Home_changed=False,Cobra_changed=False,Android='NOT_RUN',
  icon=dict(source='androidx.mediarouter:mediarouter:1.3.0',member=member,sha256=hashlib.sha256(data).hexdigest(),modified=False))
 (HERE/'research/CAST-SKIN-PRESERVATION.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':prepare(sys.argv[1])
