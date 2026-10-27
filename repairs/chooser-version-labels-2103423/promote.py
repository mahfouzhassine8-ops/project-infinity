"""Promote one verified chooser-only owner proposal to official unsigned authority.

This script changes only the current combined release-authority file in a fresh
checkout of the integration branch. It does not possess or use signing keys.
The existing sole signer independently rechecks all required hashes and HEAD.
"""
import argparse, copy, json, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SIGNED_2103423='4cbbf963be72904de962f434d00ee5f9d5080de6b6b9fd4b3e31ab1d6ac01aff'
PRODUCER_RUN=40590499416
PRODUCER_SOURCE='67967bc42cd62375f2c4f5f79061630162940046'
SHELL_ZIP_SHA='c91590042994669599a2670c485b634d3e10391ffbc85c8d653a4a1aaad13e9c'
MEMBER='member:assets/experience-component-updates.properties'
COMPONENT_KEY='CHOOSER_SHELL'
OLD_SHELL_DIGEST='1c27b2bc8a50d86a11e1c9bc3384902ccad9fa21f52b7c569be40e1d5bce3ba8'
OLD_COBRA_DIGEST='7091c30cff244beb75f900236da87d016a14573981aa84b7eee454080c23adf7'
OLD_INFINITY_DIGEST='ec27bce6252cbce21eecef0963285db720059e6c4ce27448f9ef441a8cb18f61'
NEW_SHELL_DIGEST='815da51885ef1e69f3542dd3c273c5fef8de5a64977e714d165e83ffc951996d'
EXACT_NEW_CLASSES={
 'Lcom/projectinfinity/kodi/ChooserReleaseMetadata;',
 'Lcom/projectinfinity/kodi/ChooserReleaseFooter;',
 'Lcom/projectinfinity/kodi/InfinityGlassChooser$Card;',
 'Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;'
}
def promote(checkout,producer):
 root=checkout/'repairs/dual-experience-isolation-2103420'
 sys.path.insert(0,str(root))
 from inventory import load,save,digest,file_sha,canonical
 from component_bundles import read_bundle
 from release_gate import require,component_digest
 from release_authority import validate,transition
 require((checkout/'.git').exists(),'CHECKOUT_REQUIRED')
 authority=root/'release-authority.json'
 old=load(authority)
 require(old['schema']==2 and old['generation']==6 and old['candidate_versionCode']==2103423,
         'EXPECTED_SIGNED2103423_AUTHORITY_REQUIRED')
 require(old['bundle_catalog']['bundles'][COMPONENT_KEY]['digest']==OLD_SHELL_DIGEST,
         'OLDER_SHELL_MISMATCH')
 require(old['components']['INFINITY']['digest']==OLD_INFINITY_DIGEST and
         old['components']['COBRA']['digest']==OLD_COBRA_DIGEST,
         'HISTORICAL_EXPERIENCE_COMPONENT_MISMATCH')
 require(file_sha(producer/'CHOOSER_SHELL.zip')==SHELL_ZIP_SHA,'EXACT_CI_SHELL_REQUIRED')
 preservation=load(producer/'PRESERVATION.json')
 require(preservation['status']=='PASS_TARGETED_SHELL_ONLY' and
         preservation['signed_base_sha256']==SIGNED_2103423 and
         preservation['exact_unchanged_shell_classes']==148 and
         preservation['new_shell_class_count']==152 and
         preservation['original_HM_caption_preserved'] is True and
         preservation['stage_measure_and_layout_unmodified'] is True and
         preservation['offline_component_history']=={'INFINITY':2103421,'COBRA':2103423},
         'FOCUSED_PRODUCER_PRESERVATION_REQUIRED')
 row=load(producer/'catalog-row.json')
 require(row['approved_source']==PRODUCER_SOURCE and
         row['sha256']==SHELL_ZIP_SHA and row['digest']==NEW_SHELL_DIGEST and
         row['version']=='2103420.container.2.labels.1','PRODUCER_SOURCE_OR_VERSION_MISMATCH')
 meta=read_bundle(producer/'CHOOSER_SHELL.zip',row)
 old_shell={k:v for k,v in old['payload'].items() if v['owner']==COMPONENT_KEY}
 new_shell=meta['payload']
 require(set(new_shell)-set(old_shell)=={'class:Lcom/projectinfinity/kodi/ChooserReleaseMetadata;',
                                    'class:Lcom/projectinfinity/kodi/ChooserReleaseFooter;',MEMBER},
         'EXTRA_NEW_MEMBER')
 require(set(old_shell)-set(new_shell)==set(),'MISSING_SHELL_MEMBER')
 require({k for k in old_shell if old_shell[k]!=new_shell[k]}==
         {'class:Lcom/projectinfinity/kodi/InfinityGlassChooser$Card;',
          'class:Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;'},
         'UNRELATED_SHELL_MUTATION')
 require(meta['members']=={'assets/experience-component-updates.properties':
         {'sha256':'652f0e3d6276006214b9a64de9ea08b1f2c3a15ca6a1c0265da6822885ba95f6',
          'compress_type':8,'external_attr':0o100644<<16}},'METADATA_ASSET_MISMATCH')
 proposed=copy.deepcopy(old)
 for k in old_shell:del proposed['payload'][k]
 proposed['payload'].update(new_shell)
 proposed['components'][COMPONENT_KEY]={
    'approved_source':PRODUCER_SOURCE,'digest':NEW_SHELL_DIGEST,
    'revision':old['components'][COMPONENT_KEY]['revision']+1,
    'settings_schema':'original-launch-preference','version':'2103420.container.2.labels.1'
 }
 proposed['bundle_catalog']['bundles'][COMPONENT_KEY]=row
 proposed['bundle_sources'][COMPONENT_KEY]={
     'artifact':'Chooser-Original-UI-Version-Labels-40590499416',
     'build_source':PRODUCER_SOURCE,
     'path':'CHOOSER_SHELL.zip','run_id':PRODUCER_RUN
 }
 proposed['candidate_versionCode']=2103424
 proposed['last_issued_versionCode']=2103423
 proposed['generation']=old['generation']+1
 proposed['target_owners']=[COMPONENT_KEY]
 proposed['update_kind']='owner_update'
 proposed['experience_version_labels']={'INFINITY':2103421,'COBRA':2103423}
 proposed['previous_authority_sha256']=digest(canonical(old))
 proposed['owner_update_evidence']={
     'owner':COMPONENT_KEY,'producer_source':PRODUCER_SOURCE,'producer_run':PRODUCER_RUN,
     'component_zip_sha256':SHELL_ZIP_SHA,
     'preservation':preservation,
     'physical_Fold':'PENDING','accepted_pointer_updated':False,
     'signed_baseline_2103423_sha256':SIGNED_2103423,
     'changed_owners':[COMPONENT_KEY],
     'unchanged_owners':['INFINITY','COBRA','MINIMAL_ANDROID_CONTRACT']
 }
 # Bind actual checked-in review implementation, never a prefabricated JSON.
 modified=['review_ownership.py','ownership-reviewed-roots.json','release_authority.py',
           'signer-policy.json']
 for name in modified:
     p=root/name
     require(p.exists(),'MISSING_REVIEWED_SOURCE:'+name)
     proposed['source_files']['repairs/dual-experience-isolation-2103420/'+name]=file_sha(p)
 require(component_digest(proposed['payload'],COMPONENT_KEY)==NEW_SHELL_DIGEST,
         'SHELL_PAYLOAD_NOT_CI_APPROVED')
 for owner in ('INFINITY','COBRA','MINIMAL_ANDROID_CONTRACT'):
     require(proposed['components'][owner]==old['components'][owner],
             'CROSS_OWNER_METADATA_MUTATED:'+owner)
     require({k:v for k,v in proposed['payload'].items() if v['owner']==owner}==
             {k:v for k,v in old['payload'].items() if v['owner']==owner},
             'CROSS_OWNER_PAYLOAD_MUTATED:'+owner)
 require(proposed['protected_contract']==old['protected_contract'],
         'PROTECTED_SHUTDOWN_CHANGED')
 validate(proposed)
 transition(old,proposed,{COMPONENT_KEY})
 save(authority,proposed)
 print(json.dumps({'status':'READY_FOR_SOLE_SIGNER_GATE',
     'generation':proposed['generation'],'versionCode':2103424,
     'previous_authority_sha256':proposed['previous_authority_sha256'],
     'unchanged_experience_components':['INFINITY','COBRA'],
     'shell_bundle_sha256':SHELL_ZIP_SHA},indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--checkout',type=Path,required=True)
 parser.add_argument('--producer',type=Path,required=True)
 args=parser.parse_args()
 promote(**vars(args))
