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
    # The three displayed labels come from actual packaged metadata, not UI constants.
    # The third (app) version is read from Android's signed PackageInfo.
    labels=authority.get('experience_version_labels')
    if labels is not None:
        require(set(labels)=={'INFINITY','COBRA'},'EXACT_EXPERIENCE_LABEL_VECTOR')
        require(all(type(labels[o]) is int and labels[o]>=2103420 and
                    labels[o]<=authority['candidate_versionCode'] for o in ('INFINITY','COBRA')),
                'INVALID_LAST_UPDATED_VERSION')
        history=('infinity.last_updated_in='+str(labels['INFINITY'])+'\n'+
                 'cobra.last_updated_in='+str(labels['COBRA'])+'\n')
        expected={'owner':'CHOOSER_SHELL','sha256':digest(history.encode('utf-8'))}
        require(payload.get('member:assets/experience-component-updates.properties')==expected,
                'PACKAGED_VERSION_LABELS_MISMATCH')
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
    require(bool(targets) and targets<={'INFINITY','COBRA','CHOOSER_SHELL'},'SEPARATE_SHARED_SCOPE_REQUIRED')
    # A chooser-only update is independent of both experience owners and the
    # durability contract. Last-updated numbers must follow owner changes.
    prior_labels=previous.get('experience_version_labels')
    if prior_labels is None:
        require(previous['components']['INFINITY']['digest']=='ec27bce6252cbce21eecef0963285db720059e6c4ce27448f9ef441a8cb18f61' and
                previous['components']['COBRA']['digest']=='7091c30cff244beb75f900236da87d016a14573981aa84b7eee454080c23adf7',
                'UNVERIFIED_HISTORICAL_OWNER_VERSION_BINDING')
        prior_labels={'INFINITY':2103421,'COBRA':2103423}
    next_labels=proposed.get('experience_version_labels')
    require(next_labels is not None,'MISSING_VERSION_HISTORY_ON_NEW_RELEASE')
    for experience in ('INFINITY','COBRA'):
        expected=proposed['candidate_versionCode'] if experience in targets else prior_labels[experience]
        require(next_labels[experience]==expected,'LAST_UPDATED_VERSION_ROLLBACK:'+experience)
    if next_labels!=previous.get('experience_version_labels'):
        require('CHOOSER_SHELL' in targets,'UPDATED_LABELS_REQUIRE_SHELL_BUNDLE')
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
