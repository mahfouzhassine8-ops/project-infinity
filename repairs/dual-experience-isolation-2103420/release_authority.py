"""Reviewed component authority; separate from physical-device acceptance.

Only exact, reviewed payloads can be signed. A higher Android version cannot
override a stale component. Proposals never update the accepted pointer.
"""
import re
from inventory import PACKAGE,CERT_SHA,HERE,canonical,digest,file_sha,load
from release_gate import require,component_digest

OWNED=('INFINITY','COBRA','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT')
AUTHORITY_PATH='repairs/dual-experience-isolation-2103420/release-authority.json'
GUARDED_ROOTS=('InfinityJavaPersistence','InfinityJavaWriteBarrier','CobraJavaPersistence',
               'CobraJavaWriteBarrier','ShellJavaPersistence','ShellJavaWriteBarrier',
               'CombinedDurability','OwnerDurabilityWiring','CobraRuntimeLease',
               'InfinityCloseGuardService','InfinityCloseNativeLease')

def guarded(key):
    if not key.startswith('class:Lcom/projectinfinity/kodi/'):return False
    return key.split('/')[-1].split('$')[0].rstrip(';') in GUARDED_ROOTS

def validate(authority):
    require(authority.get('schema')==2,'AUTHORITY_SCHEMA')
    require(authority.get('package')==PACKAGE and authority.get('certificate_sha256')==CERT_SHA,'IDENTITY')
    require(authority.get('status')=='ENGINEERING_REVIEWED_FOLD_PENDING','AUTHORITY_STATUS')
    require(type(authority.get('generation')) is int and authority['generation']>=2,'AUTHORITY_GENERATION')
    require(set(authority.get('components',{}))==set(OWNED),'EXACT_OWNER_VECTOR_REQUIRED')
    require(2103420<=authority['last_issued_versionCode']<authority['candidate_versionCode']<=2100000000,'APP_ROLLBACK')
    require(authority.get('release_blockers')==[],'UNRESOLVED_RELEASE_BLOCKERS')
    payload=authority['payload'];require(bool(payload),'EMPTY_PAYLOAD')
    for key,row in payload.items():
        require(key.startswith(('class:','member:')) and set(row)=={'owner','sha256'},'PAYLOAD_IDENTITY')
        require(row['owner'] in OWNED and re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'UNOWNED_PAYLOAD')
    for owner,row in authority['components'].items():
        require(row['digest']==component_digest(payload,owner),'COMPONENT_DIGEST:'+owner)
        require(type(row['revision']) is int and row['revision']>=1,'COMPONENT_REVISION:'+owner)
        require(bool(row['version']) and bool(row['settings_schema']),'COMPONENT_VERSION_SCHEMA:'+owner)
        require(re.fullmatch('[0-9a-f]{40}',row['approved_source']) is not None,'COMPONENT_SOURCE:'+owner)
    # Schema 1 is readable only as historical authority. Schema 2 adds the
    # actual native-lease class (the original guard list misspelled its name).
    require(authority.get('guard_schema',1) in (1,2),'GUARD_SCHEMA')
    expected={k:v['sha256'] for k,v in payload.items() if guarded(k) and
              (authority.get('guard_schema',1)==2 or '/InfinityCloseNativeLease' not in k)}
    require(bool(expected) and authority.get('protected_contract')==expected,'PROTECTED_CONTRACT')
    require(authority.get('accepted_pointer_updated') is False,'PHYSICAL_ACCEPTANCE_REQUIRED')
    return authority

def verify(authority,actual,version,generation):
    validate(authority)
    require(generation==authority['generation'],'STALE_REGISTRY')
    require(version==authority['candidate_versionCode'],'UNRESERVED_OR_STALE_APP_VERSION')
    require(set(actual)==set(authority['payload']),'MISSING_OR_UNOWNED_MEMBER')
    for key,row in authority['payload'].items():
        require(actual[key]==row['sha256'],'STALE_OR_MUTATED_OWNER:'+row['owner']+':'+key)
    return {'generation':generation,'payload_digest':digest(canonical(actual)),
            'component_versions':{o:r['version'] for o,r in authority['components'].items()},
            'component_sources':{o:r['approved_source'] for o,r in authority['components'].items()}}

def transition(previous,proposed,targets):
    validate(previous);validate(proposed);targets=set(targets)
    require(proposed['generation']==previous['generation']+1,'REGISTRY_GENERATION_RACE')
    require(proposed['accepted_registry_sha256']==previous['accepted_registry_sha256'],'ACCEPTED_POINTER_CHANGED')
    require(proposed.get('guard_schema')==2,'CURRENT_GUARD_SCHEMA_REQUIRED')
    if proposed.get('update_kind')=='evidence_refresh':
        require(not targets,'EVIDENCE_REFRESH_HAS_NO_FEATURE_TARGET')
        for key in ('payload','components','candidate_versionCode','last_issued_versionCode'):
            require(proposed[key]==previous[key],'EVIDENCE_REFRESH_CHANGED_PAYLOAD_OR_VERSION:'+key)
        require(all(proposed['protected_contract'].get(k)==v for k,v in previous['protected_contract'].items()),
                'EVIDENCE_REFRESH_WEAKENED_CONTRACT')
        return True
    require(bool(targets) and targets<={'INFINITY','COBRA'},'SEPARATE_SHARED_SCOPE_REQUIRED')
    require(proposed['candidate_versionCode']>previous['candidate_versionCode'],'APP_ROLLBACK')
    require(proposed['last_issued_versionCode']>=previous['last_issued_versionCode'],'ISSUED_VERSION_ROLLBACK')
    require(proposed['protected_contract']==previous['protected_contract'],'SEPARATE_LIFECYCLE_AUTHORIZATION_REQUIRED')
    for owner in OWNED:
        old={k:v for k,v in previous['payload'].items() if v['owner']==owner}
        new={k:v for k,v in proposed['payload'].items() if v['owner']==owner}
        a,b=previous['components'][owner],proposed['components'][owner]
        if owner not in targets:require(old==new and a==b,'CROSS_OWNER_MUTATION:'+owner)
        else:
            require(old!=new and b['revision']==a['revision']+1 and b['version']!=a['version'],
                    'OWNER_REVISION_NOT_ADVANCED:'+owner)
    return True

def verify_evidence(authority,read):
    """read(path) must return bytes from the exact remote-authorized commit."""
    import json
    base='repairs/dual-experience-isolation-2103420/'
    require(authority.get('guard_schema')==2,'CURRENT_GUARD_SCHEMA_REQUIRED')
    require(digest(read(base+'accepted-combined-release.json'))==authority['accepted_registry_sha256'],'ACCEPTED_BASELINE_CHANGED')
    required={'RUNTIME-PRESERVATION.json','OWNER-CONTRACT.json','PRODUCTION-BOUNDARIES.json',
              'OWNERSHIP.json','COMBINATION-CONTROLS.json'}
    proofs=authority['proofs'];require(set(proofs)==required,'MISSING_FOCUSED_PROOF')
    data={}
    for name,sha in proofs.items():
        raw=read(base+'results/scoped-correction/final/'+name)
        require(digest(raw)==sha,'PROOF_CHANGED:'+name);data[name]=json.loads(raw)
    require(data['RUNTIME-PRESERVATION.json']['original_methods_checked']==64143 and
            data['RUNTIME-PRESERVATION.json']['status']=='EXACT_OR_EXPLICIT_BOUNDARY_INSTRUCTIONS_VERIFIED','INSTRUCTION_PRESERVATION')
    require(data['OWNER-CONTRACT.json']['status']=='PASS_OWNER_DURABILITY_CONTRACT','OWNER_CONTRACT')
    require(data['PRODUCTION-BOUNDARIES.json']['status']=='PASS' and data['PRODUCTION-BOUNDARIES.json']['tests']==13,'PRODUCTION_BOUNDARIES')
    require(data['OWNERSHIP.json']['direct_infinity_cobra_feature_edges']==0,'CROSS_FEATURE_IMPORT')
    require(data['COMBINATION-CONTROLS.json']['status']=='PASS_ACTUAL_INDEPENDENT_COMPONENT_MATRIX','COMBINATION_CONTROLS')
    for name,sha in authority['source_files'].items():
        require(name.startswith(base) and '..' not in name.split('/'),'SOURCE_SCOPE')
        require(digest(read(name))==sha,'REVIEWED_SOURCE_CHANGED:'+name)
    for name,sha in data['RUNTIME-PRESERVATION.json']['new_source_sha256'].items():
        require(digest(read(base+'runtime/'+name))==sha,'RUNTIME_PROOF_SOURCE_CHANGED:'+name)
    for name,sha in data['COMBINATION-CONTROLS.json']['source_inputs'].items():
        require(digest(read(base+name))==sha,'MATRIX_PROOF_SOURCE_CHANGED:'+name)
    require(digest(read('.github/workflows/infinity-combined-release.yml'))==authority['workflow_sha256'],'SIGNING_WORKFLOW_CHANGED')
    return True
