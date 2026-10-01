from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];skin=ROOT/'candidate/skin.infinity.diggz';cc=ROOT/'candidate/script.infinity.commandcenter'
p=cc/'addon.xml';s=p.read_text();s=s.replace('version="0.3.5.17"','version="0.3.5.18"',1);p.write_text(s)
p=skin/'addon.xml';s=p.read_text();s=s.replace('version="1.0.5.178"','version="1.0.5.179"',1).replace('addon="script.infinity.commandcenter" version="0.3.5.17"','addon="script.infinity.commandcenter" version="0.3.5.18"')
s=re.sub(r'(<description lang="en_GB">).*?(</description>)',r'\1Infinity Mobile whole-system audit repair RC1. Preserves approved Home geometry, rotation controls, provider routes and theme assets. Repairs shared-window lookup, navigation, playback actions, controller recovery and observer policy. Requires Command Center 0.3.5.18. Partial audit candidate: native X-Ambient equivalence and physical-device acceptance remain open.\2',s,flags=re.S);p.write_text(s)
release={'title':'Infinity Mobile Whole-System Audit Repair RC1','status':'partial_audit_test_candidate_not_locked','baseline':'1.0.5.176','baseline_sha256':'4263de3906ea0dc6e24f3c6f04c2f779b0c7a8bbdd31656b82e221402063d1c9','reviewed_observer_reference':'1.0.5.178','reviewed_observer_reference_sha256':'8e14c98fa50dfc5defe16732588a509e819d9e99983b91541ba1edf23ca60cd3','controller':'0.3.5.18','apk_rebuilt':False,'apk_reference':2103284,'apk_locked_parent':2103282,'physical_device_tested':False,'live_provider_tested':False,'native_xambient_equivalence':'open','source_date':'2026-10-01'}
for name in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
 p=skin/name;d=json.loads(p.read_text());d['skin_version']='1.0.5.179';d['candidate']=179 if name=='infinity-skin.json' else release['title'];d['candidate_name']=release['title'];d['current_release']=release
 if 'native_video_ambient' in d:d['native_video_ambient'].pop('command_center_unchanged',None);d['native_video_ambient']['controller']='0.3.5.18'
 if name=='infinity-skin.json':d['ui_health']['backup_policy']='matching canonical version + exact metadata identity; staged verified replacement; no self-heal during playback'
 p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
p=skin/'Infinity-Protected-Manifest.json';d=json.loads(p.read_text());known=set(d['protected_files'])
for name in json.loads((ROOT/'results/ui-repair-receipt.json').read_text())['custom_moves']:
 known.discard('16x9/'+name);known.add('fallback/'+name)
known.add('resources/lib/infinity_seek_time.py')
# Native observer and helper already in the protected contract. No font is copied
# into this metadata: only file names and SHA-256 values are recorded.
known.add('resources/lib/infinity_native_ambient.py')
d['protected_files']={rel:hashlib.sha256((skin/rel).read_bytes()).hexdigest() for rel in sorted(known)}
p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
(cc/'WHOLE_SYSTEM_AUDIT_RC1.txt').write_text('Command Center 0.3.5.18 audit test candidate. Preserves existing settings/profile formats. Requires paired skin 1.0.5.179 for repaired UI contracts. Not a claim of physical Fold, live provider, native-crash or X-Ambient acceptance.\n')
(ROOT/'results/candidate-release.json').write_text(json.dumps(release,indent=2)+'\n')
print(len(known),'protected files')
