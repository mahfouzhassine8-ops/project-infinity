"""Commit a fully checked engineering owner registry; never mark acceptance.

Only the exact corrective working ref advances, with an explicit lease.
Locked refs, production source, user data and the accepted pointer are untouched.
No private signing credential is exposed to this job.
"""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile
import final_release as r
from inventory import canonical,digest,file_sha,load,save
from release_gate import require

def register(prepared,version,audit,out):
    out.mkdir(parents=True,exist_ok=False)
    source=os.environ['GITHUB_SHA']
    require(os.environ['GITHUB_REF']=='refs/heads/'+r.BRANCH,'EXACT_CORRECTIVE_REF')
    require(r.cmd('git','rev-parse','HEAD')==source,'EXACT_EXECUTING_SOURCE')
    require(not r.cmd('git','status','--porcelain','--untracked-files=no'),'COMMITTED_SOURCE_REQUIRED')
    previous=load(r.ROOT/r.AUTHORITY_PATH)
    # Only the already-reviewed signer inventory data may differ from gen49's
    # 39 protected release-source pins. The original 38 implementations stay.
    for name,want in previous['source_files'].items():
        if name=='repairs/dual-experience-isolation-2103420/signer-policy.json' and version==2103464:
            require((r.ROOT/name).read_bytes()==subprocess.check_output(['git','show',r.PREPARED_SOURCE+':'+name]),'EXACT_PREVIOUSLY_VERIFIED_ADDITIVE_SIGNER_INVENTORY')
        else:require(file_sha(r.ROOT/name)==want,'PROTECTED_RELEASE_SOURCE_CHANGED:'+name)
    proposal=r.proposed(prepared,version,audit)
    save(out/'PROPOSED-AUTHORITY.json',proposal)
    require(proposal['accepted_pointer_updated'] is False and proposal['release_blockers']==[],'ENGINEERING_ONLY_AUTHORITY')
    require(proposal['owner_update_evidence']['public_release']=='BLOCKED_UNTIL_SELECTED_ANDROID_GATES_PASS','PUBLICATION_GATE_RETAINED')
    remote={line.split()[1]:line.split()[0] for line in r.cmd('git','ls-remote','origin','refs/heads/'+r.BRANCH,'refs/heads/'+r.CANONICAL).splitlines()}
    require(remote['refs/heads/'+r.BRANCH]==source,'CORRECTIVE_SOURCE_HEAD_RACE')
    canonical_head=remote['refs/heads/'+r.CANONICAL]
    if version==2103464:require(canonical_head=='86d5b5e2b65acb878632d407c3a3a07dd1af3b6d','EXACT_PROTECTED_WORKING_PARENT')
    subprocess.run(['git','merge-base','--is-ancestor',canonical_head,source],check=True)
    save(r.ROOT/r.AUTHORITY_PATH,proposal)
    audit_dest=r.HERE/'MODULE-UPGRADE-RECOVERY.json'
    if audit.resolve()!=audit_dest.resolve():shutil.copyfile(audit,audit_dest)
    staged=[r.AUTHORITY_PATH,str(audit_dest.relative_to(r.ROOT))]
    subprocess.run(['git','add','--',*staged],check=True)
    actual=set(r.cmd('git','diff','--cached','--name-only').splitlines())
    require(actual<=set(staged) and r.AUTHORITY_PATH in actual,'EXACT_ENGINEERING_METADATA_COMMIT_ONLY')
    subprocess.run(['git','-c','user.name=Infinity scoped engineering','-c','user.email=infinity-engineering@users.noreply.github.com','commit','-m','Register reviewed '+str(version)+' engineering payload; Android and Fold acceptance pending'],check=True)
    commit=r.cmd('git','rev-parse','HEAD')
    with tempfile.TemporaryDirectory(prefix='infinity-scoped-git-auth-') as temporary:
        askpass=Path(temporary)/'askpass.py'
        askpass.write_text('#!/usr/bin/env python3\nimport os,sys\nprint("x-access-token" if "Username" in sys.argv[1] else os.environ["GH_TOKEN"])\n')
        askpass.chmod(0o700)
        env=dict(os.environ,GIT_ASKPASS=str(askpass),GIT_TERMINAL_PROMPT='0')
        subprocess.run(['git','push',
            '--force-with-lease=refs/heads/'+r.BRANCH+':'+source,
            'origin',commit+':refs/heads/'+r.BRANCH],check=True,env=env)
    save(out/'ENGINEERING-AUTHORITY-RECEIPT.json',dict(status='PASS_CHECKED_ENGINEERING_PAYLOAD_STAGED_WITH_LEASE',versionCode=version,generation=proposal['generation'],source_reviewed=source,registered_commit=commit,previous_authority_sha256=digest(canonical(previous)),authority_sha256=digest(canonical(proposal)),module_audit_sha256=file_sha(audit),canonical_authority_advance='PENDING_SEPARATE_REVIEWED_LEASE_BEFORE_SIGNING',locked_references_updated=False,accepted_pointer_updated=False,APK_signed=False,public_release=False,Android='PENDING_SUCCESSOR',Fold='PENDING_ONE_FINAL_TEST'))
    print('PASS registered engineering-only payload:',commit)

def refresh(toolchain,out):
    out.mkdir(parents=True,exist_ok=False)
    source=os.environ['GITHUB_SHA']
    require(os.environ['GITHUB_REF']=='refs/heads/'+r.BRANCH and r.cmd('git','rev-parse','HEAD')==source,'EXACT_CORRECTIVE_SOURCE')
    require(not r.cmd('git','status','--porcelain','--untracked-files=no'),'COMMITTED_SOURCE_REQUIRED')
    request=load(r.HERE/'REQUEST.json')
    require(request['operation']=='refresh-original-java21' and request['version']==2103464 and request['publication'] is False,'EXACT_TOOLCHAIN_ONLY_REQUEST')
    previous=load(r.ROOT/r.AUTHORITY_PATH)
    for name,want in previous['source_files'].items():require(file_sha(r.ROOT/name)==want,'UNCHANGED_RELEASE_GUARD_SOURCE:'+name)
    proposal=r.toolchain_refresh(previous,toolchain)
    save(out/'PROPOSED-AUTHORITY.json',proposal)
    remote=r.cmd('git','ls-remote','origin','refs/heads/'+r.BRANCH).split()[0]
    require(remote==source,'CORRECTIVE_HEAD_RACE')
    dest=r.HERE/'DEX-TOOLCHAIN-VERIFICATION.json'
    shutil.copyfile(toolchain,dest);save(r.ROOT/r.AUTHORITY_PATH,proposal)
    paths=[r.AUTHORITY_PATH,str(dest.relative_to(r.ROOT))]
    subprocess.run(['git','add','--',*paths],check=True)
    require(set(r.cmd('git','diff','--cached','--name-only').splitlines())==set(paths),'EXACT_TOOLCHAIN_EVIDENCE_METADATA_ONLY')
    subprocess.run(['git','-c','user.name=Infinity scoped engineering','-c','user.email=infinity-engineering@users.noreply.github.com','commit','-m','Restore original Java21 verification evidence; identical payload and unmodified owner guard'],check=True)
    commit=r.cmd('git','rev-parse','HEAD')
    with tempfile.TemporaryDirectory(prefix='infinity-scoped-git-auth-') as temporary:
        askpass=Path(temporary)/'askpass.py'
        askpass.write_text('#!/usr/bin/env python3\nimport os,sys\nprint("x-access-token" if "Username" in sys.argv[1] else os.environ["GH_TOKEN"])\n')
        askpass.chmod(0o700)
        subprocess.run(['git','push','--force-with-lease=refs/heads/'+r.BRANCH+':'+source,'origin',commit+':refs/heads/'+r.BRANCH],check=True,env=dict(os.environ,GIT_ASKPASS=str(askpass),GIT_TERMINAL_PROMPT='0'))
    save(out/'ENGINEERING-AUTHORITY-RECEIPT.json',dict(status='PASS_ORIGINAL_JAVA21_EVIDENCE_REFRESH_ONLY',generation=51,versionCode=2103464,registered_commit=commit,authority_sha256=digest(canonical(proposal)),payload_identical=True,components_identical=True,original_guard_unchanged=True,locked_references_updated=False,accepted_pointer_updated=False,APK_signed=False,public_release=False))
    print('PASS original Java21 evidence-only authority:',commit)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('prepared','audit','toolchain'):p.add_argument('--'+name,type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--version',type=int)
    p.add_argument('--refresh-toolchain',action='store_true')
    args=vars(p.parse_args())
    if args.pop('refresh_toolchain'):
        refresh(args['toolchain'],args['out'])
    else:
        assert all(args[n] is not None for n in ('prepared','audit','version'))
        args.pop('toolchain');register(**args)
