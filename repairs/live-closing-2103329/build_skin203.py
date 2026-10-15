#!/usr/bin/env python3
"""Narrow truthful closing acknowledgment from exact .202; immutable .201 rollback."""
import argparse,hashlib,json,copy,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
BASE='42fc05048d3873670e1cba63a1ea44a3f2fdae0fbd20102923115db58b74ea4a'
DIALOG='skin.infinity.diggz/unified/DialogButtonMenu.xml';ADDON='skin.infinity.diggz/addon.xml'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def build(base,out,proof):
 require(sha(base.read_bytes())==BASE,'Not exact skin .202')
 with zipfile.ZipFile(base) as z:
  require(z.testzip() is None,'Base CRC failure');infos=z.infolist();original={i.filename:z.read(i.filename) for i in infos};comment=z.comment
 require(len(original)==len(infos),'Duplicate parent entries')
 text=original[DIALOG].decode();a=text.index('<control type="group" id="2001">');b=text.index('\n        <control type="group"',a+1)
 before=text[a:b];row=before
 require(row.count('Saving → Services → Scripts → Cleanup')==1,'Unexpected closing stage row')
 row=row.replace('CLOSING INFINITY…','[B]CLOSING INFINITY...[/B]').replace('Saving → Services → Scripts → Cleanup','Live status appears in the closing panel')
 require(row.count('<width>46%</width>')==1,'Unexpected fixed fraction bar')
 row=row.replace('<width>46%</width>','<right>22</right>')
 text=text[:a]+row+text[b:];ET.fromstring(text)
 addon=original[ADDON].decode().replace('version="1.0.5.202"','version="1.0.5.203"',1)
 # Metadata only; all dependencies and identity retained.
 addon=addon.replace('Infinity 1.0.5.202 Closing Infinity UI RC1.','Infinity 1.0.5.203 Live Closing Polish RC1.').replace('Pair with APK 2103328 or later.','Pair with APK 2103329 or later.')
 changes={DIALOG:text.encode(),ADDON:addon.encode()}
 with zipfile.ZipFile(out,'w') as z:
  z.comment=comment
  for info in infos:z.writestr(copy.copy(info),changes.get(info.filename,original[info.filename]))
 with zipfile.ZipFile(out) as z:
  require(z.testzip() is None,'Candidate CRC failure');changed=[n for n in original if original[n]!=z.read(n)]
  require(set(changed)==set(changes),'Unexpected skin changes')
  for n in original:
   if n.endswith('.xml'):ET.fromstring(z.read(n))
  old=ET.fromstring(original[ADDON]);new=ET.fromstring(z.read(ADDON))
  require(new.attrib['id']==old.attrib['id']=='skin.infinity.diggz','Skin ID changed')
  require(new.attrib['version']=='1.0.5.203','Wrong skin version')
  require(ET.tostring(old.find('requires'))==ET.tostring(new.find('requires')),'Dependencies changed')
  # Every other row, command, foreground menu geometry and non-closing control is untouched.
  require(text.replace(row,'CLOSING_ROW')==original[DIALOG].decode().replace(before,'CLOSING_ROW'),'Unrelated menu changed')
  require(text.count('action.CLOSE_KODI')==1,'Normal-close route duplicated')
  require('→' not in row and '<width>46%</width>' not in row,'Missing-glyph/fake-percentage regression')
 result={'skin_candidate':'1.0.5.203','skin_parent':'1.0.5.202','locked_skin_rollback':'1.0.5.201','base_sha256':BASE,'artifact':out.name,'sha256':sha(out.read_bytes()),'changed':changed,'protected_entries':len(original)-2,'apk_pairing':2103329,'physical_device_verified':False,'locked':False}
 proof.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);a=p.parse_args();build(a.base,a.out,a.proof)
