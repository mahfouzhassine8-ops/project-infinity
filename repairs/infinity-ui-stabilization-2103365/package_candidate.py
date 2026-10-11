#!/usr/bin/env python3
"""Apply reviewed XML deltas to the exact .204 ZIP; preserve other entries."""
from pathlib import Path
import argparse, copy, hashlib, json, zipfile
import xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
BASE_SHA='4238c9eaf341d921b319fd421bae5c47e3ed51925bed63033a558ae898787b47'
POWER='skin.infinity.diggz/unified/DialogButtonMenu.xml'
POWER_SHA='149b614b9dd96094e64c7b7a837fbc911bfceda40e4ecef84716f7a3a6220d78'

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--delta',type=Path,default=HERE/'skin-delta');p.add_argument('--lock-ui-source',action='store_true',help='Mark this exact presentation-only ZIP as an isolated UI-source lock; never implies device acceptance');a=p.parse_args()
 if sha(a.base.read_bytes())!=BASE_SHA:raise ValueError('Only the verified .204 package is permitted')
 changes={'skin.infinity.diggz/'+str(x.relative_to(a.delta)):x.read_bytes() for x in a.delta.rglob('*') if x.is_file()}
 if POWER in changes:raise ValueError('Approved Power XML must not be patched')
 if not all(n=='skin.infinity.diggz/addon.xml' or n.startswith('skin.infinity.diggz/unified/') and n.endswith('.xml') for n in changes):raise ValueError('Non-presentation delta rejected')
 for name,data in changes.items():E.fromstring(data)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 staging=a.out.with_suffix('.building')
 with zipfile.ZipFile(a.base) as base:
  if base.testzip() is not None:raise ValueError('Corrupt baseline')
  infos=base.infolist();original={i.filename:base.read(i) for i in infos if not i.is_dir()}
  if sha(original[POWER])!=POWER_SHA:raise ValueError('Power source mismatch')
  with zipfile.ZipFile(staging,'w') as output:
   for info in infos:output.writestr(copy.copy(info),changes.get(info.filename,base.read(info)))
   for name in sorted(changes.keys()-original.keys()):
    info=zipfile.ZipInfo(name,date_time=(2026,10,11,7,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
    output.writestr(info,changes[name])
 with zipfile.ZipFile(staging) as output:
  if output.testzip() is not None:raise ValueError('Corrupt candidate')
  names=output.namelist()
  if len(set(names))!=len(names):raise ValueError('Duplicate ZIP paths')
  final={i.filename:output.read(i) for i in output.infolist() if not i.is_dir()}
  actual={n for n in final if final[n]!=original.get(n)}
  if actual!=set(changes) or original.keys()-final.keys():raise ValueError('Unexpected changes/removals')
  if final[POWER]!=original[POWER]:raise ValueError('Power changed')
  root=E.fromstring(final['skin.infinity.diggz/addon.xml'])
  if (root.get('id'),root.get('version'))!=('skin.infinity.diggz','1.0.5.207'):raise ValueError('Candidate identity mismatch')
  old=E.fromstring(original['skin.infinity.diggz/addon.xml'])
  for query in ['requires',"extension[@point='xbmc.gui.skin']"]:
   if E.tostring(root.find(query))!=E.tostring(old.find(query)):raise ValueError('Dependency or active-profile contract changed')
  xml=[n for n in final if n.startswith('skin.infinity.diggz/unified/') and n.endswith('.xml')]
  for n in xml:E.fromstring(final[n])
 staging.replace(a.out)
 manifest={
  'candidate':'1.0.5.207 UI Stability RC1','skin_id':root.get('id'),'authoritative_parent':'1.0.5.204 Closing Status Polish RC1',
  'base_package':a.base.name,'base_sha256':BASE_SHA,'protected_locked_parent':'1.0.5.201',
  'protected_parent_sha256':'c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5',
  'candidate_file':a.out.name,'candidate_sha256':sha(a.out.read_bytes()),'candidate_size_bytes':a.out.stat().st_size,
  'changed_files':[{'path':n,'baseline_sha256':sha(original[n]) if n in original else None,'candidate_sha256':sha(final[n]),'kind':'modified' if n in original else 'added'} for n in sorted(actual)],
  'unchanged_entries':len(original)-len(actual&original.keys()),'removed_entries':0,'active_xml_parsed':len(xml),
  'power_byte_identical':True,'power_sha256':POWER_SHA,'all_other_entries_byte_identical':True,
  'native_rebuild':False,'backend_or_provider_code_changed':False,'settings_reset':False,
  'physical_fold_tested':False,'combined_release_accepted':False,'locked':a.lock_ui_source,
  'lock_scope':'ISOLATED_UI_SOURCE_CANDIDATE' if a.lock_ui_source else 'UNLOCKED_CANDIDATE',
  'rollback':'Install the original .204 ZIP over this skin without removing settings or userdata; do not automatically revert to .201.',
 }
 a.out.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (HERE/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:manifest[k] for k in ['candidate_file','candidate_sha256','unchanged_entries','active_xml_parsed','power_byte_identical']}))

if __name__=='__main__':main()
