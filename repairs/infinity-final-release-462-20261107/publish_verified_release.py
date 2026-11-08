"""Explicit, gated GitHub draft -> verified assets -> prerelease publication.

Never signs or rewrites APKs. Never promotes the Fold-accepted baseline.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,tempfile
from package_verified_release import PINS,CERT,file_sha,load,save,require
REPO='mahfouzhassine8-ops/project-infinity'
TAG='infinity-2103464-fold-acceptance'

def command(*args):
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
    require(p.returncode==0,'PUBLICATION_COMMAND:'+str(args[0])+':'+p.stderr[-2000:])
    return p.stdout.strip()

def api(path,*args):return json.loads(command('gh','api','repos/'+REPO+'/'+path,*args))

def publish(request,payload,out):
    config=load(request);gate=load(payload/'PUBLICATION-GATE.json')
    require(config['operation']=='publish-verified464' and config['publication'] is True and config['prerelease'] is True,'EXPLICIT_VERIFIED_PRERELEASE_OPERATION')
    require(config['tag']==TAG and config['repository']==REPO,'EXACT_USER_REPOSITORY_AND_VERSION')
    require(gate['status']=='PASS_ONE_COMBINED_APK_AND_MATCHING_FORWARD_RECOVERY_READY','COMPLETE_PACKAGE_GATE')
    require(gate['candidate_sha256']==PINS[2103464] and gate['recovery_apk_sha256']==PINS[2103465] and gate['original_certificate_sha256']==CERT,'EXACT_BOTH_ORIGINAL_SIGNED_INPUTS')
    require(gate['physical_Fold']=='PENDING_ONE_FINAL_USER_TEST' and gate['accepted_pointer_updated'] is False,'NO_UNTESTED_FOLD_ACCEPTANCE')
    require(gate['manual_review_sha256']==config['ENGINEERING_REVIEW_sha256'] and file_sha(payload/'VERIFICATION.md')==config['VERIFICATION_md_sha256'],'EXACT_REVIEWED_LOGICAL_DELIVERABLE_AND_REPORT')
    require(config['build_tag_source']=='33c800fe656eca117a5bfbdc1d4ac46269f3d7ed','EXACT_PRIMARY_SIGNED_BUILD_SOURCE_TAG')
    run=api('actions/runs/'+str(config['Android_run']))
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==config['Android_source'],'COMPLETED_EXACT_ANDROID_RUN')
    rows=api('actions/runs/'+str(config['Android_run'])+'/artifacts?per_page=100')['artifacts']
    matches=[r for r in rows if r['id']==config['Android_artifact'] and not r['expired']]
    require(len(matches)==1 and matches[0]['digest']==config['Android_artifact_digest'],'EXACT_SOURCE_BOUND_ANDROID_EVIDENCE')
    require(load(payload/'ENGINEERING-REVIEW.json')['status']=='PASS_SELECTED_ENGINEERING_RELEASE_GATES','FINAL_VISUAL_AND_FILES_REVIEW_REQUIRED')
    # The checksum file describes every actual public asset except itself.
    sums={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (payload/'SHA256SUMS').read_text().splitlines()}
    files={p.name:p for p in payload.iterdir() if p.is_file()}
    require(set(files)==set(sums)|{'SHA256SUMS'},'EXACT_PUBLIC_ASSET_SET')
    for name,want in sums.items():require(file_sha(files[name])==want,'FINAL_ASSET_BYTES:'+name)
    require(file_sha(files['Infinity-2103464-Combined-Original-Signer.apk'])==PINS[2103464],'UNCHANGED_PRIMARY_APK')
    existing=[r for r in api('releases?per_page=100') if r['tag_name']==TAG]
    require(not existing,'NEW_RELEASE_ONLY_NO_SILENT_REPLACEMENT')
    notes=payload.parent/'release-notes.md'
    notes.write_text('Combined Infinity/Cobra2103464 for one final Fold acceptance test. Includes reviewed native-provider Search, keyboard and graphics corrections. Cobra, Preview and unrelated components are preserved.\n\nInstall the combined APK. The matching higher-version recovery ZIP is optional rollback and restores earlier268 functionality, including its original Search limitations.\n\nAll selected engineering and Android gates passed; see VERIFICATION.md and the source-bound reports. Fresh native replies accept provider settings changes, including meaningful changes and ABA; no immutable settings consistency is claimed. Cached replies remain strictly checked.\n\nPhysical Fold acceptance and final lock are pending. The accepted baseline pointer is unchanged.\n')
    # Draft remains private until all actual uploaded asset bytes are verified.
    command('gh','release','create',TAG,'--repo',REPO,'--target',config['build_tag_source'],'--title','Infinity2103464 combined Fold acceptance candidate','--draft','--prerelease','--notes-file',notes,*map(str,sorted(files.values())))
    drafts=[r for r in api('releases?per_page=100') if r['tag_name']==TAG]
    require(len(drafts)==1,'ONE_EXACT_NEW_RELEASE')
    release=drafts[0]
    require(release['draft'] is True and release['prerelease'] is True,'PRIVATE_DRAFT_BEFORE_COMPLETE_ASSET_CHECK')
    assets=api('releases/'+str(release['id'])+'/assets?per_page=100')
    actual={a['name']:a for a in assets}
    require(set(actual)==set(files),'COMPLETE_MATCHING_RELEASE_ASSETS')
    verified={}
    with tempfile.TemporaryDirectory(prefix='infinity-release-readback-') as temporary:
        for name,path in files.items():
            row=actual[name];want=file_sha(path)
            require(row['state']=='uploaded' and row['size']==path.stat().st_size,'COMPLETE_UPLOADED_ASSET:'+name)
            if row.get('digest'):
                require(row['digest']=='sha256:'+want,'SERVER_ASSET_DIGEST:'+name)
            else:
                target=Path(temporary)/'asset'
                with target.open('wb') as stream:subprocess.run(['gh','api','repos/'+REPO+'/releases/assets/'+str(row['id']),'-H','Accept: application/octet-stream'],stdout=stream,check=True)
                require(file_sha(target)==want,'UPLOADED_ASSET_READBACK:'+name);target.unlink()
            verified[name]=dict(sha256=want,bytes=row['size'],url=row['browser_download_url'])
    api('releases/'+str(release['id']),'--method','PATCH','-F','draft=false','-F','prerelease=true')
    final=api('releases/'+str(release['id']))
    require(final['draft'] is False and final['prerelease'] is True,'PUBLISHED_ONLY_AS_FOLD_ACCEPTANCE_CANDIDATE')
    save(out,dict(status='PUBLISHED_VERIFIED_COMBINED_APK_AND_MATCHING_FORWARD_RECOVERY',release=final['html_url'],tag=TAG,assets=verified,physical_Fold='PENDING_ONE_FINAL_USER_TEST',accepted_pointer_updated=False,APK_bytes_changed=False,signing_keys_accessed=False))
    print(final['html_url'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('request','payload','out'):p.add_argument('--'+n,type=Path,required=True)
    publish(**vars(p.parse_args()))
