"""Disposable stock-Kodi renderer fixture; never packaged into the candidate."""
from pathlib import Path
import argparse,shutil,xml.etree.ElementTree as E,json,math
p=argparse.ArgumentParser();p.add_argument('--skin',type=Path,required=True);p.add_argument('--width',type=int,default=2400);p.add_argument('--height',type=int,default=1080);p.add_argument('--version',required=True);a=p.parse_args()
profile=Path.home()/'.kodi/userdata';addons=profile.parent/'addons';profile.mkdir(parents=True,exist_ok=True);addons.mkdir(exist_ok=True)
root=addons/'skin.infinity.phased'
if root.exists():shutil.rmtree(root)
shutil.copytree(a.skin,root)
tree=E.parse(root/'addon.xml');r=tree.getroot();r.set('id','skin.infinity.phased');r.set('name','Infinity isolated renderer')
requires=r.find('requires')
for n in list(requires):requires.remove(n)
E.SubElement(requires,'import',addon='xbmc.gui',version='5.15.0')
res=r.find('./extension[@point="xbmc.gui.skin"]/res');res.set('width',str(a.width));res.set('height',str(a.height));res.set('aspect',f'{a.width}:{a.height}')
tree.write(root/'addon.xml',encoding='utf-8')
# Production XML/resources stay exact. Optional missing companion services are intentionally
# not installed; this harness evaluates skin rendering and GUI actions, not provider/network code.
keys=profile/'keymaps';keys.mkdir(exist_ok=True)
here=Path(__file__).resolve().parent
(keys/'phase-d.xml').write_text(f'<keymap><global><keyboard><f11>RunScript({here}/runtime.py,bootstrap)</f11><f12>RunScript({here}/runtime.py,run)</f12></keyboard></global></keymap>')
(profile/'advancedsettings.xml').write_text('<advancedsettings><loglevel hide="true">1</loglevel><network><disableipv6>true</disableipv6></network></advancedsettings>')
(profile/'phase-d-config.json').write_text(json.dumps(dict(version=a.version,width=a.width,height=a.height,source=str(a.skin))))
settings=profile/'guisettings.xml'
if settings.exists():
 t=E.parse(settings);r=t.getroot()
 for key,value in [('lookandfeel.skin','skin.infinity.phased'),('videoscreen.screenmode','WINDOW'),('window.width',str(a.width//2)),('window.height',str(a.height//2))]:
  n=r.find(f'setting[@id="{key}"]')
  if n is None:n=E.SubElement(r,'setting',id=key)
  n.attrib.pop('default',None);n.text=value
 t.write(settings,encoding='utf-8')
