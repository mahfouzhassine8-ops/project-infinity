#!/usr/bin/env python3
"""Record reference UI ownership; require installed sources before layout edits."""
from pathlib import Path
import argparse, hashlib, json, xml.etree.ElementTree as ET

BASE = 'faf41ee1d35fe55140bb1e193089643cc9ac06ee'
BRANCH = 'work/infinity-ui-stabilization-2103365'
OWNERS = [
 ('U01','Add-on Information','unified/DialogAddonInfo.xml','Kodi native actions; skin presentation','Viewport bounds, independent description/action scrolling; preserve native IDs and all install actions.'),
 ('U02','Global context menus','unified/DialogContextMenu.xml','Kodi CGUIDialogContextMenu','Preserve 996/999/1000; measure padding, panel placement, clipping and 1/2/10/30 action lists.'),
 ('U03','Provider source menus','unified/DialogContextMenu.xml','Shared menu probable; installed provider call site unverified','Confirm actual Umbrella owner; preserve source/debrid actions and third-party entries.'),
 ('U04','Playback resume prompt','unified/DialogContextMenu.xml','Kodi context menu at matched audit call site; installed alternate provider owner unverified','Repair shared presentation; retain stored resume position and existing options; heading requires verified data.'),
 ('U05','Navigation drawer','unified/Custom_1198_InfinityNav.xml','Skin window 1198','Remove only row 1198107; move 1198503 after UI Theme, before Power 1198304; retain other routes and scrolling.'),
 ('U06','System Hub','unified/Custom_1191_InfinitySystemHub.xml','Skin window 1191','Remove only Power group/control 1191105; preserve remaining actions and main drawer Power.'),
 ('U07','Health Center','unified/Custom_1188_InfinityHealthCenter.xml','Skin window 1188; script.kodihealthcenter publishes data','Reflow header/status/cards/scrolling; retain all action IDs; coordinate authoritative status and freshness.'),
 ('U08','Movie-list metadata','unified/MyVideoNav.xml','Installed active view/include remains unverified','Resolve active view ID and metadata include before any targeted text geometry change.'),
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(reference, evidence):
 addon=ET.parse(reference/'addon.xml').getroot()
 active=[r.attrib for r in addon.findall("./extension[@point='xbmc.gui.skin']/res")]
 if addon.get('id')!='skin.infinity.diggz': raise ValueError('Wrong skin identity')
 xml_paths=sorted((reference/'unified').glob('*.xml'))
 parsed=[]; errors=[]
 for p in xml_paths:
  try: ET.parse(p);parsed.append(str(p.relative_to(reference)))
  except ET.ParseError as e: errors.append({'path':str(p.relative_to(reference)),'error':str(e)})
 legacy=ET.parse(reference/'unified/Includes_InfinityLegacy.xml').getroot()
 includes={n.get('name'):[str(p.relative_to(reference)) for p in xml_paths if n.get('name') in p.read_text()] for n in legacy.findall('include') if n.get('name') in ['InfinityLegacy_DialogBackgroundCommons','InfinityLegacy_DialogCloseButton','InfinityLegacy_DialogCloseButtonClassic']}
 themes={v.get('name'):[{'condition':x.get('condition'),'value':x.text} for x in v.findall('value')] for v in legacy.findall('variable') if v.get('name','').startswith('InfinityLegacy')}
 owners=[]
 for ident,screen,f,owner,repair in OWNERS:
  p=reference/f;tree=ET.parse(p)
  actions=[{'id':c.get('id'),'type':c.get('type'),'label':c.findtext('label'),'onclick':[x.text for x in c.findall('onclick')]} for c in tree.findall('.//control') if c.findall('onclick')]
  owners.append({'defect':ident,'screen':screen,'reference_path':f,'reference_sha256':sha(p),'owner':owner,'repair_target':repair,'existing_actions':actions,'installed_source_verified':False,'repair_status':'pending_source_gate'})
 data=json.loads((evidence/'diagnostics/integration/installed-code.json').read_text())
 khc=ET.parse(reference/'unified/Custom_1188_InfinityHealthCenter.xml').getroot()
 props=sorted({s.split('Property(')[1].split(')')[0] for e in khc.iter() for s in [e.text or ''] if 'Property(KHC.' in s})
 hashes={str(p.relative_to(reference)):sha(p) for p in sorted(reference.rglob('*')) if p.is_file()}
 return {'schema':1,'branch':BRANCH,'protected_baseline_commit':BASE,'protected_baseline_branch':'work/infinity-android-close-2103365','backend_branch_observed':'work/infinity-system-stability-2103366','backend_head_observed':'48dc19c221fc41f88f3d52614beef8a877e426d6','scope':'UI source verification only; no skin/native/script/workflow modifications','gate':'BLOCKED_INSTALLED_UI_SOURCE_UNVERIFIED','audit_sha256':sha(evidence/'Infinity-2103366-Read-Only-Audit-2026-10-11.html'),'diagnostic_zip_sha256':sha(evidence/'Infinity-Diagnostics-20261011-013725.zip'),'reference_package':'skin.infinity.diggz-1.0.5.206-Exact-201-Restore.zip','reference_package_sha256':sha(evidence/'skin.infinity.diggz-1.0.5.206-Exact-201-Restore.zip'),'reference_id':addon.get('id'),'reference_version':addon.get('version'),'reference_active_profiles':active,'reference_is_installed_proof':False,'installed_code_diagnostic':data,'reference_xml_parse':{'passed':len(parsed),'errors':errors},'owners':owners,'shared_include_consumers':includes,'theme_tokens':themes,'reference_health_properties':props,'integration_requirements':['Exact installed skin export including addon.xml, active XML/includes/fonts/themes/media; reconcile SHA256 before editing.','Exact installed Health Center source/publication contract; existing labels do not prove freshness or verified healthy state.','Installed Umbrella/other provider menu entry points before attributing custom dialog ownership.','Verified backend watched identity/state/actions before activating new checkmarks or actions.','Physical Fold runtime control bounds, touch/focus/Back, provider actions, all postures and theme acceptance.','Comparable timing/memory observations and 60-120 minute device session; no performance claim from source checks.'],'reference_file_hashes':hashes,'rollback':{'repository_commit':BASE,'reference_package_available':True,'installed_rollback_package_available':False,'settings_reset_required':False},'validation_limits':'Reference XML parsing and source ownership only. No actual UI repair, rendered-after evidence, device testing, native compilation, performance measurement, or release acceptance.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 d=inventory(a.reference,a.evidence);(a.out/'source-inventory.json').write_text(json.dumps(d,indent=2)+'\n')
 summary={k:v for k,v in d.items() if k not in ('reference_file_hashes','theme_tokens','shared_include_consumers','owners','installed_code_diagnostic')};summary['required_source_export']='Kodi Health Center > Infinity Skin Export: export the installed skin package. Code-only is sufficient; saved settings/userdata are not required. Exact Health/provider code exports may be needed for their contracts.';(a.out/'source-gate.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({'gate':d['gate'],'reference_files_hashed':len(d['reference_file_hashes']),'reference_xml_parsed':d['reference_xml_parse'],'owners_mapped':len(d['owners']),'installed_skin_state':d['installed_code_diagnostic']['addons'][0]['state']}))
if __name__=='__main__':main()
