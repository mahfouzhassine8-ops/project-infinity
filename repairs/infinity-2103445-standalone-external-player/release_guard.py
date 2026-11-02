"""One explicit external-player manifest exception; no shared code permission."""
import importlib.util
from pathlib import Path
from hashlib import sha256
H=Path(__file__).resolve().parent
PREFIX='repairs/infinity-2103445-standalone-external-player/'
AUTH=PREFIX+'ASTRA-MASTER-IMPLEMENTATION-BRIEF.md'
AUTH_SHA='66ab48798123c22e37997cd4514d48cf472b3be2e50a11887a51cc089ccbec78'
REFERENCE=PREFIX+'reference/AndroidManifest-2103445.xml.bin'
REFERENCE_SHA='f53e75db187bbf0d2e47f4260db6e0235c8c265735274f14fb5495a932123a18'
NORMALIZED='1949a8ee902bf21493255017019ca1330b5dfbf358daa69ca85d3e98cceb5ab4'
OWNER='MINIMAL_ANDROID_CONTRACT'
def validate(authority):
 from release_gate import require
 proof=authority.get('external_player_manifest_exception')
 require(isinstance(proof,dict) and set(proof)=={'schema','authorization','authorization_sha256','reference','reference_sha256','candidate_manifest_sha256','source_inputs'},'EXTERNAL_MANIFEST_EXCEPTION_SCHEMA')
 require(proof['schema']==1 and proof['authorization']==AUTH and proof['authorization_sha256']==AUTH_SHA,'EXPLICIT_EXTERNAL_PLAYER_AUTHORITY')
 require(proof['reference']==REFERENCE and proof['reference_sha256']==REFERENCE_SHA,'EXACT445_MANIFEST_REFERENCE')
 require(set(proof['source_inputs'])=={PREFIX+'patch_manifest.py',PREFIX+'release_guard.py',REFERENCE,AUTH},'EXTERNAL_MANIFEST_SOURCE_SCOPE')
 require(authority['payload']['member:AndroidManifest.xml']==dict(owner=OWNER,sha256=proof['candidate_manifest_sha256']),'EXTERNAL_MANIFEST_PAYLOAD_BINDING')
 return proof
def transition(previous,proposed,targets):
 from release_gate import require
 proof=validate(proposed)
 require(previous['candidate_versionCode']==2103445 and proposed['candidate_versionCode']==2103447,'EXTERNAL_EXACT445_TO447')
 require(set(targets)=={'INFINITY','CHOOSER_SHELL',OWNER},'EXTERNAL_EXACT_OWNER_SCOPE')
 require(previous.get('external_player_manifest_exception') is None,'EXTERNAL_MANIFEST_EXCEPTION_ALREADY_USED')
 require(proposed.get('launcher_icon_exception')==previous.get('launcher_icon_exception'),'ORIGINAL_LAUNCHER_ARTWORK_PROOF_FROZEN')
 require(proposed['components'][OWNER]['settings_schema']==previous['components'][OWNER]['settings_schema'],'SHARED_SETTINGS_SCHEMA_FROZEN')
 old={k:v for k,v in previous['payload'].items() if v['owner']==OWNER}
 new={k:v for k,v in proposed['payload'].items() if v['owner']==OWNER}
 require(old['member:AndroidManifest.xml']['sha256']==NORMALIZED,'EXACT445_TYPED_MANIFEST')
 require(set(old)==set(new) and {k for k in old if old[k]!=new[k]}=={'member:AndroidManifest.xml'},'SHARED_EXECUTABLE_RESOURCE_NATIVE_BYTES_FROZEN')
 return proof
def verify_evidence(authority,read):
 from release_gate import require,normalize_manifest
 proof=validate(authority)
 for name,pin in proof['source_inputs'].items():require(sha256(read(name)).hexdigest()==pin,'EXTERNAL_MANIFEST_REVIEWED_SOURCE:'+name)
 require(sha256(read(AUTH)).hexdigest()==AUTH_SHA and sha256(read(REFERENCE)).hexdigest()==REFERENCE_SHA,'EXTERNAL_EXACT_AUTHORIZATION_REFERENCE')
 spec=importlib.util.spec_from_file_location('_fixed_external_manifest',H/'patch_manifest.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 derived=module.patch(read(REFERENCE))
 require(sha256(normalize_manifest(derived)[0]).hexdigest()==proof['candidate_manifest_sha256'],'EXTERNAL_EXACT_DERIVED_MANIFEST')
 return True
