#!/usr/bin/env python3
"""Verify approved .204 sources and preserve the protected .201 parent.

The .206 audit package is diagnostic guidance only; device acceptance is separate.
"""
from pathlib import Path
import argparse, hashlib, json, zipfile, xml.etree.ElementTree as ET

BASE = 'faf41ee1d35fe55140bb1e193089643cc9ac06ee'
BRANCH = 'work/infinity-ui-stabilization-2103365'
APPROVED_PACKAGE = 'skin.infinity.diggz-1.0.5.204-Closing-Status-Polish-RC1.zip'
APPROVED_SHA = '4238c9eaf341d921b319fd421bae5c47e3ed51925bed63033a558ae898787b47'
PARENT_PACKAGE = 'skin.infinity.diggz-1.0.5.201-Complete-Settings-Polish-RC1.zip'
PARENT_SHA = 'c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5'
POWER = 'unified/DialogButtonMenu.xml'
POWER_SHA = '149b614b9dd96094e64c7b7a837fbc911bfceda40e4ecef84716f7a3a6220d78'
OWNERS = [
 ('U01','Add-on Information','unified/DialogAddonInfo.xml','Kodi native actions; skin presentation','Viewport bounds and description/action scrolling; preserve native IDs and all install actions.'),
 ('U02','Global context menus','unified/DialogContextMenu.xml','Kodi CGUIDialogContextMenu','Preserve 996/999/1000; measure padding, placement, clipping and 1/2/10/30 action lists.'),
 ('U03','Provider source menus','unified/DialogContextMenu.xml','Shared menu probable; installed provider call site unverified','Confirm actual Umbrella owner; preserve source/debrid actions and third-party entries.'),
 ('U04','Playback resume prompt','unified/DialogContextMenu.xml','Kodi context menu at matched audit call site; installed alternate provider owner unverified','Repair shared presentation; retain stored resume position and options; heading requires verified data.'),
 ('U05','Navigation drawer','unified/Custom_1198_InfinityNav.xml','Skin window 1198','Remove only row 1198107; move 1198503 after UI Theme, before Power 1198304; preserve routes and scrolling.'),
 ('U06','System Hub','unified/Custom_1191_InfinitySystemHub.xml','Skin window 1191','Remove only Power group/control 1191105; preserve remaining actions and main drawer Power.'),
 ('U07','Health Center','unified/Custom_1188_InfinityHealthCenter.xml','Skin window 1188; script.kodihealthcenter publishes data','Reflow header/status/cards/scrolling; retain all action IDs; coordinate authoritative status/freshness.'),
 ('U08','Movie-list metadata','unified/MyVideoNav.xml','Installed active view/include remains unverified','Resolve active view ID and metadata include before targeted text geometry changes.'),
]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def hashes(root): return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def archive_hashes(path):
 with zipfile.ZipFile(path) as archive:
  if archive.testzip() is not None: raise ValueError('Corrupt archive: '+str(path))
  entries=[i for i in archive.infolist() if not i.is_dir()]
  prefix='skin.infinity.diggz/'
  if len({i.filename for i in entries})!=len(entries) or any(not i.filename.startswith(prefix) for i in entries):
   raise ValueError('Unexpected archive structure')
  return {i.filename[len(prefix):]:hashlib.sha256(archive.read(i)).hexdigest() for i in entries}

def inventory(approved, parent, packages, evidence):
 for name, expected in [(APPROVED_PACKAGE,APPROVED_SHA),(PARENT_PACKAGE,PARENT_SHA),('reproduced-1.0.5.204.zip',APPROVED_SHA)]:
  if sha(packages/name)!=expected: raise ValueError('Baseline/reproduction mismatch: '+name)
 addon=ET.parse(approved/'addon.xml').getroot()
 if (addon.get('id'),addon.get('version'))!=('skin.infinity.diggz','1.0.5.204'): raise ValueError('Wrong approved identity/version')
 active=[r.attrib for r in addon.findall("./extension[@point='xbmc.gui.skin']/res")]
 if len(active)!=1 or active[0]['folder']!='unified': raise ValueError('Resolve changed active profile')
 description=addon.findtext("./extension[@point='xbmc.addon.metadata']/description")
 if not description.startswith('Infinity 1.0.5.204 Closing Status Polish RC1. Built from locked .201.'): raise ValueError('Screenshot metadata mismatch')
 before,after=hashes(parent),hashes(approved)
 if before!=archive_hashes(packages/PARENT_PACKAGE) or after!=archive_hashes(packages/APPROVED_PACKAGE):
  raise ValueError('Extracted source files differ from verified original archives')
 delta=[{'path':k,'parent_sha256':before.get(k),'approved_sha256':after.get(k)} for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]
 if {x['path'] for x in delta}!={'addon.xml',POWER} or after[POWER]!=POWER_SHA: raise ValueError('Reconcile unexpected .201 to .204 changes')
 xml_paths=sorted((approved/'unified').glob('*.xml'));errors=[]
 for path in xml_paths:
  try: ET.parse(path)
  except ET.ParseError as error: errors.append({'path':str(path.relative_to(approved)),'error':str(error)})
 legacy=ET.parse(approved/'unified/Includes_InfinityLegacy.xml').getroot()
 names={'InfinityLegacy_DialogBackgroundCommons','InfinityLegacy_DialogCloseButton','InfinityLegacy_DialogCloseButtonClassic'}
 includes={n.get('name'):[str(p.relative_to(approved)) for p in xml_paths if n.get('name') in p.read_text()] for n in legacy.findall('include') if n.get('name') in names}
 themes={v.get('name'):[{'condition':x.get('condition'),'value':x.text} for x in v.findall('value')] for v in legacy.findall('variable') if v.get('name','').startswith('InfinityLegacy')}
 owners=[]
 for ident,screen,path,owner,repair in OWNERS:
  tree=ET.parse(approved/path)
  actions=[{'id':c.get('id'),'type':c.get('type'),'label':c.findtext('label'),'onclick':[x.text for x in c.findall('onclick')]} for c in tree.findall('.//control') if c.findall('onclick')]
  owners.append({'defect':ident,'screen':screen,'source_path':path,'source_sha256':after[path],'owner':owner,'repair_target':repair,'existing_actions':actions,'approved_source_verified':True,'repair_status':'not_patched'})
 khc=ET.parse(approved/'unified/Custom_1188_InfinityHealthCenter.xml').getroot()
 props=sorted({s.split('Property(')[1].split(')')[0] for e in khc.iter() for s in [e.text or ''] if 'Property(KHC.' in s})
 return {
  'schema':2,'branch':BRANCH,'protected_baseline_commit':BASE,'protected_baseline_branch':'work/infinity-android-close-2103365',
  'backend_branch_observed':'work/infinity-system-stability-2103366','backend_head_observed':'48dc19c221fc41f88f3d52614beef8a877e426d6',
  'scope':'Approved source verification and preservation records only; no skin/native/backend edits',
  'gate':'APPROVED_204_SOURCE_VERIFIED_RUNTIME_ACCEPTANCE_PENDING',
  'audit_sha256':sha(evidence/'Infinity-2103366-Read-Only-Audit-2026-10-11.html'),'diagnostic_zip_sha256':sha(evidence/'Infinity-Diagnostics-20261011-013725.zip'),
  'approved_package':APPROVED_PACKAGE,'approved_package_sha256':APPROVED_SHA,'approved_package_library_id':'libfile_1a44a717f4088191aca605a17505a3dc','approved_package_library_version':'1',
  'approved_id':addon.get('id'),'approved_version':addon.get('version'),'approved_description':description,'approved_active_profiles':active,
  'user_confirmed_installed_version':'1.0.5.204','installed_screenshot_library_id':'libfile_6041813b32d08191b0c8fee0a4b65cab','installed_bytes_independently_exported':False,
  'source_proof':'Recovered .204 metadata matches the user-confirmed screenshot; protected repository builder reproduces the complete ZIP byte for byte.',
  'source_builder':'repairs/directory-close-2103330/build_skin204.py','source_builder_sha256':sha(Path(__file__).resolve().parents[1]/'directory-close-2103330/build_skin204.py'),
  'protected_parent_package':PARENT_PACKAGE,'protected_parent_sha256':PARENT_SHA,'parent_to_approved_delta':delta,
  'preservation_requirements':[
   'Use the complete .204 package as the repair base; never substitute .201 or .206.',
   'Keep unified/DialogButtonMenu.xml byte identical to .204: closing acknowledgment, property transitions, optional motion and original Close/Force Close routes.',
   'Future version metadata must describe a repair of .204 and retain skin.infinity.diggz and existing dependency/profile contracts.',
   'Retain every unmodified .204 file byte for byte; explicitly list and review every authorized UI delta.',
   'Retain the original .204 ZIP as exact current-source rollback, and .201 as protected parent; reset no settings.'
  ],'protected_204_files':{POWER:POWER_SHA},
  'diagnostic_reference':{'package':'skin.infinity.diggz-1.0.5.206-Exact-201-Restore.zip','sha256':sha(evidence/'skin.infinity.diggz-1.0.5.206-Exact-201-Restore.zip'),'authorized_baseline':False},
  'approved_xml_parse':{'passed':len(xml_paths)-len(errors),'errors':errors},'owners':owners,'shared_include_consumers':includes,'theme_tokens':themes,'approved_health_properties':props,
  'installed_code_diagnostic':json.loads((evidence/'diagnostics/integration/installed-code.json').read_text()),
  'integration_requirements':[
   'Compare recovered source hashes with a physical Fold export before final device acceptance; screenshot verifies identity/description, not every installed byte.',
   'Exact installed Health Center publication contract; existing labels alone do not prove freshness or verified healthy state.',
   'Installed Umbrella/other provider menu entry points before attributing custom dialog ownership.',
   'Verified backend watched identity/state/actions before activating new checkmarks or actions.',
   'Physical Fold runtime bounds, touch/focus/Back, provider actions, all postures and theme acceptance.',
   'Comparable timing/memory observations and 60–120 minute device session; no performance claim from source checks.'
  ],'approved_file_hashes':after,
  'rollback':{'repository_commit':BASE,'current_source_package':APPROVED_PACKAGE,'current_source_sha256':APPROVED_SHA,'protected_parent_package':PARENT_PACKAGE,'protected_parent_sha256':PARENT_SHA,'current_source_available':True,'settings_reset_required':False,'automatic_reversion':False},
  'validation_limits':'Approved .204 source and .201 parent verified. No UI repairs, after-rendering, physical interaction tests, native build, performance measurements or candidate promotion yet.'
 }

def main():
 parser=argparse.ArgumentParser()
 for name in ('approved','parent','packages','evidence','out'): parser.add_argument('--'+name,type=Path,required=True)
 a=parser.parse_args();d=inventory(a.approved,a.parent,a.packages,a.evidence);a.out.mkdir(parents=True,exist_ok=True)
 (a.out/'source-inventory.json').write_text(json.dumps(d,indent=2)+'\n')
 excluded={'approved_file_hashes','theme_tokens','shared_include_consumers','owners','installed_code_diagnostic'}
 (a.out/'source-gate.json').write_text(json.dumps({k:v for k,v in d.items() if k not in excluded},indent=2)+'\n')
 print(json.dumps({'gate':d['gate'],'approved_files_hashed':len(d['approved_file_hashes']),'approved_xml_parsed':d['approved_xml_parse'],'parent_delta_files':len(d['parent_to_approved_delta']),'zip_reproduced_byte_identical':True,'owners_mapped':len(d['owners'])}))

if __name__=='__main__': main()
