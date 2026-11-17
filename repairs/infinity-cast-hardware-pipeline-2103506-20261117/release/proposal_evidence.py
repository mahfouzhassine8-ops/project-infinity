"""Exact metadata reconciliation of retained successful preparation44052911061.

No APK/bundle/class/source-policy/acceptance field changes. Original proposals
remain in the authenticated producer artifact and are the sole accepted inputs.
"""
import copy,hashlib,json
ORIGINAL={'candidate':'c8acb8457777438d3280c8e2d9ecc6affc69e273bf39ca5a821e2358ef6ed6ca','recovery':'11b366906a80c6a35a77daffb589e96a365f0c4a28bc126687de80fbb1d13e2f'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
def reconcile(candidate,recovery):
 assert sha(candidate)==ORIGINAL['candidate'] and sha(recovery)==ORIGINAL['recovery'],'EXACT_ORIGINAL_PREPARATION_PROPOSALS'
 a,b=json.loads(candidate),json.loads(recovery);assert a['generation']==93 and a['candidate_versionCode']==2103508 and b['generation']==94 and b['candidate_versionCode']==2103509
 assert b['previous_authority_sha256']==sha(candidate)
 for x in (a,b):assert x['owner_update_evidence']['verification_toolchain']=={'java_major':21,'unchanged_original_DEX':True}
 new_a,new_b=copy.deepcopy(a),copy.deepcopy(b)
 new_a['owner_update_evidence']['verification_toolchain']['unchanged_original_DEX']=False
 new_a['owner_update_evidence']['verification_toolchain']['unchanged_non_Cast_DEX']=True
 new_b['previous_authority_sha256']=sha(canonical(new_a))
 # Inversion proves the exact two edits, independent of all payload maps.
 inverse=copy.deepcopy(new_a);inverse['owner_update_evidence']['verification_toolchain']=a['owner_update_evidence']['verification_toolchain'];assert inverse==a
 inverse=copy.deepcopy(new_b);inverse['previous_authority_sha256']=b['previous_authority_sha256'];assert inverse==b
 return {'candidate':canonical(new_a),'recovery':canonical(new_b)}
