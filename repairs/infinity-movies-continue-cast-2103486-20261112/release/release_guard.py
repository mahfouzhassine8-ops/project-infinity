"""Exact Cast manifest allowance and its forward inverse; no general exception.

All old shared nodes/classes/resources and historical external-player proof stay
frozen. The original signer verifies this derivation before accessing its key.
"""
import copy,hashlib,importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
PREFIX='repairs/infinity-movies-continue-cast-2103486-20261112/release/'
REFERENCE=PREFIX+'AndroidManifest-2103486.xml.bin'
REFERENCE_SHA='060b0260b023128efbd34c39eebc7cdaf53c58bf10f1d23020fc3b2061333907'
NORMALIZED='febbbcf340bd74e3e919ba399b4a81bbe4aa487779d9f456c2975840f41c6d82'
APK='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
AUTH=PREFIX+'OWNER-QA-AUTHORIZATION.json'
OWNER='MINIMAL_ANDROID_CONTRACT'
SOURCE_NAMES={AUTH,REFERENCE,PREFIX+'patch_cast_manifest.py',PREFIX+'release_guard.py'}
def expected(mode):
    from release_gate import require,normalize_manifest
    raw=(HERE/'AndroidManifest-2103486.xml.bin').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==REFERENCE_SHA,'EXACT_ACCEPTED86_MANIFEST')
    require(hashlib.sha256(normalize_manifest(raw)[0]).hexdigest()==NORMALIZED,'EXACT_ACCEPTED86_NORMALIZED_MANIFEST')
    if mode=='candidate':
        spec=importlib.util.spec_from_file_location('_fixed_cast_manifest_transform',HERE/'patch_cast_manifest.py')
        patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch);raw=patch.patch(raw)
    else:require(mode=='recovery','EXACT_CAST_MANIFEST_MODE')
    return hashlib.sha256(normalize_manifest(raw)[0]).hexdigest()
def validate(authority):
    from release_gate import require
    proof=authority.get('cast_manifest_exception')
    require(isinstance(proof,dict) and set(proof)=={'schema','mode','baseline_APK_sha256','reference','reference_sha256','baseline_normalized_sha256','candidate_manifest_sha256','source_inputs'},'CAST_MANIFEST_PROOF_SCHEMA')
    require(proof['schema']==1 and proof['baseline_APK_sha256']==APK and proof['reference']==REFERENCE and
            proof['reference_sha256']==REFERENCE_SHA and proof['baseline_normalized_sha256']==NORMALIZED,'EXACT86_CAST_PROVENANCE')
    require(set(proof['source_inputs'])==SOURCE_NAMES,'EXACT_CAST_MANIFEST_REVIEW_SCOPE')
    require(proof['mode'] in ('candidate','recovery') and proof['candidate_manifest_sha256']==expected(proof['mode']),'EXACT_CAST_MANIFEST_DERIVATION')
    require(authority['payload']['member:AndroidManifest.xml']==dict(owner=OWNER,sha256=proof['candidate_manifest_sha256']),'CAST_MANIFEST_PAYLOAD_BINDING')
    require(authority.get('external_player_manifest_exception',{}).get('candidate_manifest_sha256')==NORMALIZED,'ORIGINAL_EXTERNAL_PLAYER_MANIFEST_PROOF_PRESERVED')
    return proof
def historical(authority):
    """Validate old external-player evidence against its unchanged predecessor.

    The real payload is ALWAYS checked separately by validate()/pre_sign. This
    projection never approves current APK bytes or replaces their manifest hash.
    """
    validate(authority);result=copy.deepcopy(authority)
    result['payload']['member:AndroidManifest.xml']=dict(owner=OWNER,sha256=NORMALIZED)
    return result
def transition(previous,proposed,targets):
    from release_gate import require
    proof=validate(proposed)
    require(set(targets)=={'INFINITY','CHOOSER_SHELL',OWNER},'CAST_EXACT_OWNER_VECTOR')
    require(proposed['components'][OWNER]['settings_schema']==previous['components'][OWNER]['settings_schema'],'SHARED_SETTINGS_SCHEMA_FROZEN')
    require(proposed.get('external_player_manifest_exception')==previous.get('external_player_manifest_exception') and
            proposed.get('launcher_icon_exception')==previous.get('launcher_icon_exception'),'HISTORICAL_MANIFEST_AND_ARTWORK_PROOFS_FROZEN')
    a={k:v for k,v in previous['payload'].items() if v['owner']==OWNER}
    b={k:v for k,v in proposed['payload'].items() if v['owner']==OWNER}
    require(set(a)==set(b) and {k for k in a if a[k]!=b[k]}=={'member:AndroidManifest.xml'},'ALL_EXISTING_SHARED_CLASSES_AND_RESOURCES_FROZEN')
    if proof['mode']=='candidate':
        require(previous['candidate_versionCode']==2103487 and proposed['candidate_versionCode']==2103488 and previous.get('cast_manifest_exception') is None,'EXACT_RECONCILED87_TO88_CAST')
        require(a['member:AndroidManifest.xml']['sha256']==NORMALIZED,'ACCEPTED86_MANIFEST_REQUIRED')
    else:
        require(previous['candidate_versionCode']==2103488 and proposed['candidate_versionCode']==2103489 and
                validate(previous)['mode']=='candidate','EXACT88_TO89_FORWARD_RECOVERY')
        require(b['member:AndroidManifest.xml']['sha256']==NORMALIZED,'EXACT86_MANIFEST_RECOVERY')
    return proof
def verify_evidence(authority,read):
    from release_gate import require
    proof=validate(authority)
    for name,wanted in proof['source_inputs'].items():require(hashlib.sha256(read(name)).hexdigest()==wanted,'CAST_REVIEWED_SOURCE:'+name)
    require(hashlib.sha256(read(REFERENCE)).hexdigest()==REFERENCE_SHA,'CAST_REFERENCE_CHANGED')
    return True
