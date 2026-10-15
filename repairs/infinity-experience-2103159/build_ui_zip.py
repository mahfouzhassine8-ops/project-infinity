#!/usr/bin/env python3
"""Build UI 1.4.0 from exact locked 1.3.9, adding only the optional experience theme adjunct."""
from pathlib import Path
import argparse,hashlib,json,zipfile,xml.etree.ElementTree as ET
BASE_SHA='88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a'
PREFIX='script.infinity.cobra.theme/'
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build(base,out):
 if sha(base)!=BASE_SHA:raise ValueError('Not exact locked matching UI 1.3.9')
 with zipfile.ZipFile(base) as source:
  if source.testzip():raise ValueError('Baseline UI ZIP CRC failure')
  names=source.namelist()
  if len(names)!=len(set(names)):raise ValueError('Duplicate baseline UI ZIP member')
  files={n:source.read(n) for n in names if not n.endswith('/')}
 required={PREFIX+'addon.xml',PREFIX+'resources/cobra-theme.json',PREFIX+'resources/cobra-ui.json',PREFIX+'lib/__init__.py'}
 if set(files)!=required:raise ValueError('Unexpected locked 1.3.9 inventory')
 untouched={n:hashlib.sha256(files[n]).hexdigest() for n in (PREFIX+'resources/cobra-theme.json',PREFIX+'lib/__init__.py')}
 addon=ET.fromstring(files[PREFIX+'addon.xml']);
 if addon.attrib.get('id')!='script.infinity.cobra.theme' or addon.attrib.get('version')!='1.3.9':raise ValueError('Unexpected baseline addon identity')
 addon.set('version','1.4.0')
 for ext in addon.findall('extension'):
  if ext.attrib.get('point')=='xbmc.addon.metadata':
   for child in ext:
    if child.tag=='summary':child.text='Infinity/Cobra UI with ZIP-driven startup experience styling.'
    elif child.tag=='description':child.text='Carries the locked Cobra UI contract plus an optional Infinity experience-chooser visual theme for runtime bridge 1. Playback, EPG, native engine, signer and launch ownership are not replaced by this ZIP.'
 files[PREFIX+'addon.xml']=ET.tostring(addon,encoding='utf-8',xml_declaration=True)
 ui=json.loads(files[PREFIX+'resources/cobra-ui.json'])
 if ui.get('schema')!=1 or ui.get('runtime',{}).get('scope')!='cobra-live-only' or ui.get('runtime',{}).get('minimum_runtime',99)>3:raise ValueError('Locked UI runtime contract drift')
 if any(ui.get('protected_contracts',{}).get(k)!='native' for k in ('rotation','fold','background_resume','renderer','provider_playback','infinity_handoff')):raise ValueError('Protected UI contract drift')
 ui['version']='1.4.0';files[PREFIX+'resources/cobra-ui.json']=(json.dumps(ui,indent=2,ensure_ascii=False)+'\n').encode()
 experience=(ROOT/'experience-theme.json').read_bytes();validate_experience(json.loads(experience));files[PREFIX+'resources/experience-chooser.json']=experience
 out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():out.unlink()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as target:
  for name,data in sorted(files.items()):target.writestr(name,data)
 with zipfile.ZipFile(out) as check:
  if check.testzip():raise ValueError('Built UI ZIP CRC failure')
  if set(n for n in check.namelist() if not n.endswith('/'))!=set(files):raise ValueError('Built UI inventory mismatch')
  if hashlib.sha256(check.read(PREFIX+'resources/cobra-theme.json')).hexdigest()!=untouched[PREFIX+'resources/cobra-theme.json'] or hashlib.sha256(check.read(PREFIX+'lib/__init__.py')).hexdigest()!=untouched[PREFIX+'lib/__init__.py']:raise ValueError('Untargeted locked UI bytes changed')
 digest=sha(out);out.with_suffix(out.suffix+'.sha256').write_text(digest+'  '+out.name+'\n');print('PASS: exact UI 1.3.9 + experience adjunct ->',out,digest)
def validate_experience(data):
 if data.get('schema')!=1 or data.get('scope')!='infinity-experience-chooser' or data.get('minimum_bridge',99)>1:raise ValueError('Wrong experience theme contract')
 copy=data.get('copy',{});palette=data.get('palette',{})
 required=('brand','brand_tagline','title','initials','personalization','infinity_title','infinity_subtitle','cobra_title','cobra_subtitle','footer_brand','footer_tagline')
 if any(not isinstance(copy.get(k),str) or not copy[k].strip() for k in required):raise ValueError('Missing experience copy')
 infinity=copy['infinity_subtitle'].lower();
 if 'live tv' in infinity or '2-in-1' in infinity or '2 in 1' in infinity:raise ValueError('Legacy Infinity copy forbidden')
 if copy['title']!='Choose Your Experience' or copy['initials']!='HM':raise ValueError('Approved title/initials drift')
 if any(token in json.dumps(copy).lower() for token in ('two separate environments','2-in-1')):raise ValueError('Removed chooser copy returned')
 for key in ('background','background_glow','text','muted','infinity_top','infinity_bottom','infinity_border','infinity_glow','cobra_top','cobra_bottom','cobra_border','cobra_glow','badge_fill','badge_border','horizon'):
  value=palette.get(key,'')
  if not isinstance(value,str) or len(value) not in (7,9) or not value.startswith('#'):raise ValueError('Invalid palette token '+key)
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
if __name__=='__main__':main()
