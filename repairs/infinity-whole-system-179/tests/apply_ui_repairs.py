"""Apply only demonstrated source-lookup, navigation and action repairs.
Run after apply_skin_repairs.py; immutable baseline archives are not written.
"""
from pathlib import Path
import re,json,shutil,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'candidate/skin.infinity.diggz'
profiles=('16x9','20x9','6x5','5x6','portrait')
receipt={'custom_moves':[],'navigation_links':0,'volume_duplicates_removed':0,'page_down_repairs':0,'seek_routes':0}
def custom(folder):return {p.name:p for p in folder.glob('*.xml') if p.name.lower().startswith('custom')}
common=set(custom(out/'16x9'))-set(custom(out/'portrait'));assert len(common)==21
for name in sorted(common):
 for profile in profiles[1:]:assert not (out/profile/name).exists()
 assert not (out/'fallback'/name).exists()
 shutil.move(out/'16x9'/name,out/'fallback'/name);receipt['custom_moves'].append(name)
p=out/'addon.xml';s=p.read_text();old='    <res width="1100" height="1000" aspect="11:10" default="true" folder="fallback" />\n';assert s.count(old)==1;s=s.replace(old,'')
anchor='    <res width="1920" height="1080" aspect="16:9" default="false" folder="16x9" />'
assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n    <res width="1920" height="1080" aspect="16:9" default="true" folder="fallback" />')
s=s.replace('''    <!-- 1.0.5.165: neutral default fallback contains standard windows/includes only.
         Custom windows stay only in the active responsive profile, preventing
         Kodi from registering the same custom ID from active + default paths. -->''','''    <!-- Shared windows use their authored 1920x1080 default canvas. The active
         16x9 alias precedes its equal-aspect fallback. Common custom windows are
         in fallback only; adaptive custom windows stay in each active profile. -->''')
p.write_text(s)
def add_links(path,mapping):
 s=path.read_text()
 for key,links in mapping.items():
  pattern=r'(<control\s+type="button"\s+id="'+key+r'"[^>]*>)(.*?)(</control>)'
  matches=list(re.finditer(pattern,s,re.S));assert len(matches)==1,(path,key)
  m=matches[0];body=m.group(2)
  for direction,target in links.items():
   assert '<'+direction not in body,(path,key,direction)
   body+='\n      <'+direction+'>'+str(target)+'</'+direction+'>\n'
   receipt['navigation_links']+=1
  s=s[:m.start()]+m.group(1)+body+m.group(3)+s[m.end():]
 path.write_text(s)
for profile in profiles:
 order=('1191199','1191101','1191102','1191103','1191104','1191106','1191107','1191105')
 links={key:{'onup':order[(i-1)%len(order)],'ondown':order[(i+1)%len(order)],'onleft':'1191199','onright':'1191199'} for i,key in enumerate(order)}
 links['1191199']['onright']='1191101';links['1191199']['onleft']='1191105'
 add_links(out/profile/'Custom_1191_InfinitySystemHub.xml',links)
 for name,close,keys,horiz in [
  ('Custom_1195_InfinityAudioSubtitles.xml','5199',('5101','5102','5103'),False),
  ('Custom_1196_InfinityPlaybackSpeed.xml','5299',('5201','5202','5203'),True),
  ('Custom_1197_InfinityDisplayMode.xml','5399',('5301','5302','5303'),False)]:
  links={key:({'onup':close,'ondown':close} if horiz else {'onleft':close,'onright':close}) for key in keys}
  links[close]={'onup':keys[-1],'ondown':keys[0],'onleft':keys[-1],'onright':keys[0]}
  add_links(out/profile/name,links)
for p in out.rglob('*.xml'):
 s=p.read_text();before=s
 for direction in ('Up','Down'):
  s,n=re.subn(r'(<onclick>\$VAR\[VolumeStep'+direction+r'\]</onclick>)\s*<onclick>Volume'+direction+r'</onclick>',r'\1',s)
  receipt['volume_duplicates_removed']+=n
 # The actual 44 occurrences have been validated as scrollbar direction actions.
 n=s.count('<ondown>PageUp(70)</ondown>');receipt['page_down_repairs']+=n
 s=s.replace('<ondown>PageUp(70)</ondown>','<ondown>PageDown(70)</ondown>')
 if p.name=='VideoOSD.xml':
  pattern=r'(<control\s+type="button"\s+id="278"[^>]*>)(.*?)(</control>)'
  m=re.search(pattern,s,re.S);assert m
  body=m.group(2);assert body.count('<onclick>DialogSeekBar</onclick>')==1
  body=body.replace('<onclick>DialogSeekBar</onclick>','<onclick>RunScript(special://skin/resources/lib/infinity_seek_time.py)</onclick>')
  s=s[:m.start()]+m.group(1)+body+m.group(3)+s[m.end():];receipt['seek_routes']+=1
 if s!=before:p.write_text(s)
assert receipt['navigation_links']==310,receipt
assert receipt['volume_duplicates_removed']==24,receipt
assert receipt['page_down_repairs']==44,receipt
assert receipt['seek_routes']==6,receipt
shutil.copy2(ROOT/'tests/infinity_seek_time.py',out/'resources/lib/infinity_seek_time.py')
(ROOT/'results/ui-repair-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))
