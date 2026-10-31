"""Evidence-only owner review. Reuses the immutable prepared Cards bytes."""
import argparse,copy,json,subprocess
from pathlib import Path
import release438 as r
from review_ownership import class_owner
PRIOR='8da6273e616f79521c638a0d76399ee9f1dc61aa'
POLICY=r.ISO/'ownership-reviewed-roots.json'

def prior():return json.loads(r.cmd('git','show',PRIOR+':'+str(r.AUTH.relative_to(r.REPO))))
def reviewed_policy():
    old=json.loads(r.cmd('git','show',PRIOR+':'+str(POLICY.relative_to(r.REPO))))
    current=r.load(POLICY);expected=copy.deepcopy(old);expected['project_roots']['CobraCardsTheme']='COBRA'
    r.require(current==expected,'EXACT_ONE_REVIEWED_CARDS_ROOT_ONLY')
    for n in ('Lcom/projectinfinity/kodi/CobraCardsTheme;','Lcom/projectinfinity/kodi/CobraCardsTheme$Colors;'):
        r.require(class_owner(n,'',current)=='COBRA','EXACT_CARDS_OWNER')
    try:class_owner('Lcom/projectinfinity/kodi/CobraCardsThemeUnknown;','',current)
    except ValueError:pass
    else:raise RuntimeError('UNREVIEWED_CLASS_WAS_ADMITTED')
    return current

def proposed():
    reviewed_policy();a=prior();b=copy.deepcopy(a)
    b.update(generation=24,update_kind='evidence_refresh',target_owners=[],previous_authority_sha256=r.digest(r.canonical(a)))
    for n,pin in a['source_files'].items():
        if n!=str(POLICY.relative_to(r.REPO)):r.require(r.file_sha(r.REPO/n)==pin,'UNCHANGED_REVIEWED_SOURCE:'+n)
    b['source_files'][str(POLICY.relative_to(r.REPO))]=r.file_sha(POLICY)
    b['workflow_sha256']=r.file_sha(r.REPO/'.github/workflows/infinity-combined-release.yml')
    b['policy_review_evidence']=dict(reason='Classify exactly the reviewed Cards palette adapter; no payload or runtime changes',root='CobraCardsTheme',owner='COBRA',expected_classes=['Lcom/projectinfinity/kodi/CobraCardsTheme;','Lcom/projectinfinity/kodi/CobraCardsTheme$Colors;'],source_sha256=r.file_sha(r.REPO/'repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsTheme.java'),prepared_run=41248722422,prior_signing_refusal=41249025549,APK_signed_in_refused_run=False)
    r.transition(a,b,[]);r.verify_evidence(b,lambda n:(r.REPO/n).read_bytes())
    return b

def check(prepared,run_id,out,apply=False):
    r.official(prepared,run_id);old=prior();proposal=proposed()
    r.require(run_id==41248722422,'IMMUTABLE_PREPARATION_RUN')
    r.require(r.load(prepared/'components/catalog.json')==old['bundle_catalog'],'UNCHANGED_PREPARED_CATALOG')
    for owner,row in old['bundle_catalog']['bundles'].items():r.read_bundle(prepared/'components'/row['file'],row)
    if apply:
        r.require(r.load(r.AUTH)==old,'EXACT_PRIOR_AUTHORITY');r.save(r.AUTH,proposal)
    else:r.require(r.load(r.AUTH)==proposal,'EXACT_POLICY_REVIEW_AUTHORITY')
    r.save(out,dict(status='PASS_EXACT_PREPARED_BYTES_AND_ONE_CARDS_OWNER_REVIEW',generation=24,run=run_id,APK_payload_changed=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--run-id',type=int,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--apply',action='store_true');check(**vars(p.parse_args()))
