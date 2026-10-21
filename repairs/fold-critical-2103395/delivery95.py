#!/usr/bin/env python3
"""Full verified native compilation -> permanent signature -> individual files.

No debug-signing fallback, test waiver, profile reset, native binary patch or
unrelated APK-member change. A candidate remains experimental until Fold acceptance.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile,ZIP_DEFLATED
import components95 as c
import native95 as n
import dex95

CODE=2103395
NAME='1.0.9-All-In-One-Bugfix-TEST0005'
OLD_NAME='1.0.9-All-In-One-Bugfix-TEST0004'
FILENAME='Infinity-2103395-Fold-Corrective-EXPERIMENTAL.apk'
ENGINE='lib/arm64-v8a/libkodi.so'
RECORDER='lib/arm64-v8a/libinfinitycrash.so'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',re.I)

def save(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def verify_delta(parent,candidate,targets):
    with ZipFile(parent) as a,ZipFile(candidate) as b:
        old={x for x in a.namelist() if not SIGNATURE.fullmatch(x)}
        new={x for x in b.namelist() if not SIGNATURE.fullmatch(x)}
        c.require(len(b.namelist())==len(set(b.namelist())) and b.testzip() is None,'corrupt/duplicate final members')
        c.require(not old-new and new-old==set(targets)-old,'unexpected removed/added APK members')
        changed=[]
        for name in sorted(new):
            body=b.read(name)
            if name in targets:
                c.require(body==targets[name],'signed target drift '+name)
            if name not in old or body!=a.read(name):changed.append(name)
        c.require(set(changed)==set(targets),'unexpected/missing APK delta '+repr(sorted(set(changed)^set(targets))))
        c.require(not any('cobra' in x.lower() for x in changed),'Cobra member changed')
        c.require(c.sha(b.read('classes2.dex'))==dex95.SHARD2,'second DEX shard changed')
        return changed

def assemble(args):
    d,r,_=n.old_adapters()
    _,_,signer=d.adapters()
    c.require(all(os.environ.get(k) for k in d.KEYS),'all permanent signing secrets required; no fallback')
    producer=args.producer.resolve();checkpoint=producer/'checkpoint-build'
    c.require(d.command(['git','-C',producer,'rev-parse','HEAD']).strip()==d.PRODUCER,'wrong original producer')
    c.require(not d.command(['git','-C',producer,'diff','--name-only']).strip(),'immutable producer modified')
    parent=d.exact_file(args.parent_dir,'Infinity-2103394-Fold-Corrective-EXPERIMENTAL.apk',c.PARENT)
    original=c.read_parent(parent);final=c.components(original)
    ledger=c.ledger(original,final)
    c.require(ledger==json.loads((c.HERE/'MEMBER-DELTA.json').read_text()),'unreviewed component payload')
    for name,body in final.items():c.require((args.stage/name).read_bytes()==body,'staged source mismatch '+name)
    binding=json.loads((checkpoint/'FOLD95-NATIVE-BINDING.json').read_text())
    c.require(binding['source_commit']==args.source_commit and binding['original_source_count']==binding['final_source_count']==9404,'incomplete native binding')
    c.require(binding['protected_source_count']==9404-len(n.PATHS) and set(binding['after'])==n.PATHS and binding['all_other_sources_byte_identical'],'native delta scope mismatch')
    expected=json.loads((checkpoint/'FOLD95-NATIVE-SOURCE-MAP.json').read_text())
    c.require(len(expected)==9404 and all(c.digest(producer/'kodi'/name)==pin for name,pin in expected.items()),'native reviewed source changed during compile')
    for name,value in binding['unchanged_build_links'].items():
        path=producer/'kodi'/name
        c.require(path.is_symlink() and os.readlink(path)==value['target'] and str(path.resolve())==value['resolved'],'native build link changed')
    post=json.loads((checkpoint/'POST-BUILD-SOURCE-INVENTORY.json').read_text())
    c.require(post['reviewed_file_count']==9404 and not post['changed_or_missing_reviewed'],'post-compile source verification failed')
    engine=checkpoint/'libkodi.so';engine_hash=c.digest(engine)
    proof=json.loads((checkpoint/'ENGINE-PROOF.json').read_text())
    c.require(proof['source_commit']==args.source_commit and proof['complete_native_engine_compiled'] and proof['native_sha256']==engine_hash,'full ARM64 provenance missing')
    c.require(proof['shutdown_policy']=='essential_first_process_exit_v1' and proof['crash_fixed'] is False and proof['physical_fold_verified'] is False,'native guard/acceptance misrepresentation')
    native=engine.read_bytes();c.require(len(native)>90_000_000,'full native engine missing')
    for symbol in (b'InfinityPlaybackSettings.xml',b'InfinitySubtitleSettings.xml',b'InfinityVideoSettings.xml',b'RunScript(script.infinity.uirepair,option-b,',b'0.3.5.25',b'Skin.HasSetting(Infinity.SilentMode)'):
        c.require(symbol in native,'compiled corrective behavior missing '+repr(symbol))
    for pin in json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json']).values():c.require(pin.encode() in native,'compiled controller pin missing')
    dexproof=json.loads((args.component/'STARTUP-DEX-INTEGRATION.json').read_text())
    dex=args.component/'component/classes.dex'
    c.require(dexproof['source_commit']==args.source_commit and dexproof['source_apk_sha256']==c.PARENT and c.digest(dex)==dexproof['component_dex_sha256'],'wrong startup DEX')
    c.require(dexproof['decoded_protected_instructions_identical'] and dexproof['fields']['encoded_values_and_presence_preserved'] and dexproof['protected_classes_in_changed_shard']==7852,'DEX/Cobra preservation failed')
    art=json.loads((args.component/'ART-COMPONENT-VERIFICATION.json').read_text())
    c.require(art['source_commit']==args.source_commit and art['component_sha256']==dexproof['component_dex_sha256'] and art['passed'] and art['candidate_cases_passed']==45 and art['baseline_control_cases_passed']==1,'Android execution required')
    c.require(art['integrated_search_android']['passed'] and art['integrated_search_android']['assertions']>=30,'integrated Android Search UI must pass')
    c.require(art['platform']['api']==37 and art['platform']['release'].split('.')[0]=='17','wrong ART platform')
    tools=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    parent_signature=d.verify_signature(parent,tools)
    out=args.out.resolve();c.require(not out.exists(),'refusing existing delivery overwrite')
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.infinity-2103394-',dir=out.parent) as temporary:
        temp=Path(temporary);unsigned=temp/'unsigned.apk';signed=temp/FILENAME
        with ZipFile(parent) as a:
            old_engine=a.read(ENGINE)
            c.require(c.sha(old_engine)=='42057e189be8caaa993473b33fce7b740a6d2e4dceb90a6c957955989ba49fae','wrong protected parent engine')
            abi=signer.native_export_compatibility(old_engine,native)
            old_recorder=a.read(RECORDER)
            recorder=d.replace_recorder_field(old_recorder,c.sha(old_engine),engine_hash,signer.nativeidentity.elf_sections(old_recorder))
            manifest=d.module('fold93_binary_manifest',c.ROOT/'repairs/critical-preview-2103376/manifest_patch.py')
            manifest.PARENT_CODE=2103394;manifest.CODE=CODE;manifest.PARENT_NAME=OLD_NAME;manifest.NAME=NAME
            patched,edits=manifest.patch(a.read('AndroidManifest.xml'))
            c.require(len(edits)==2 and {e['field'] for e in edits}=={'versionCode','versionName'},'manifest delta not limited to version')
            targets={'assets/addons/'+name:final[name] for name in ledger['changed']}
            targets['assets/infinity-2103395-components.json']=c.evidence_manifest(final)
            targets.update({ENGINE:native,RECORDER:recorder,'classes.dex':dex.read_bytes(),'AndroidManifest.xml':patched})
            with ZipFile(unsigned,'w',allowZip64=True) as z:
                for info in a.infolist():
                    if not SIGNATURE.fullmatch(info.filename):
                        z.writestr(copy.copy(info),targets.get(info.filename,a.read(info)))
                for name in sorted(set(targets)-set(a.namelist())):
                    z.writestr(name,targets[name],compress_type=ZIP_DEFLATED,compresslevel=9)
        verify_delta(parent,unsigned,targets)
        subprocess.run(['bash',str(c.ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
        signature=d.verify_signature(signed,tools)
        badging=d.command([tools/'aapt','dump','badging',signed])
        c.require("package: name='com.projectinfinity.kodi' versionCode='2103395'" in badging and "versionName='"+NAME+"'" in badging,'package/version mismatch')
        c.require('application-debuggable' not in badging,'debug APK forbidden')
        changed=verify_delta(parent,signed,targets)
        with ZipFile(signed) as z:
            for addon,_,version in c.PACKAGES:
                entries=[name for name in z.namelist() if name.startswith('assets/addons/'+addon+'/') and not name.endswith('/')]
                filename=addon+'-'+version+'.zip'
                with ZipFile(temp/filename,'w',compression=ZIP_DEFLATED,compresslevel=9) as component:
                    for name in sorted(entries):component.writestr(name[len('assets/addons/'):],z.read(name))
                with ZipFile(temp/filename) as component:
                    c.require(component.testzip() is None and len(component.namelist())==len(entries),'corrupt matching ZIP')
                    c.require(all(component.read(name)==z.read('assets/addons/'+name) for name in component.namelist()),'component differs from signed APK')
        receipt={'schema':1,'version_code':CODE,'version_name':NAME,'source_commit':args.source_commit,
                 'parent_commit':c.COMMIT,'parent_apk_sha256':c.PARENT,'apk_sha256':c.digest(signed),
                 'native_sha256':engine_hash,'native_source_files_verified':9404,'native_changed_from_2103394':sorted(n.PATHS),
                 'protected_native_source_files':9404-len(n.PATHS),'complete_native_engine_compiled':True,'native_abi':abi,
                 'startup_dex_sha256':dexproof['component_dex_sha256'],'unchanged_classes2_dex_sha256':dex95.SHARD2,
                 'protected_runtime_classes_in_changed_shard':7852,'permanent_certificate_sha256':CERT,
                 'signed_permanently':True,'android_art_verifier_cases_passed':45,
                 'apk_changed_members':changed,'matching_component_versions':ledger['versions'],
                 'matching_zips_identical_to_apk':True,'cobra_members_and_instructions_byte_identical':True,
                 'shutdown_policy':'essential_first_process_exit_v1','essential_first_guards_weakened':False,
                 'install_over_signing_and_package_compatible':True,'actual_install_over_tested':False,
                 'physical_fold_verified':False,'original_sigsegv_fixed':False,'option_b_normal_root_cause_proven':False,'normal_option_b_status':'diagnostic_only_no_speculative_behavior_change','integrated_search_android':art['integrated_search_android'],'final_lock':False,'experimental_only':True}
        save(temp/'INFINITY-2103395-DELIVERY.json',receipt)
        (temp/'FINAL-SIGNATURE.txt').write_text(signature);(temp/'PARENT-SIGNATURE.txt').write_text(parent_signature)
        (temp/'APK-BADGING.txt').write_text(badging)
        for filename in ('FOLD95-NATIVE-BINDING.json','ENGINE-PROOF.json'):
            shutil.copyfile(checkpoint/filename,temp/filename)
        for filename in ('STARTUP-DEX-INTEGRATION.json','ART-COMPONENT-VERIFICATION.json'):
            shutil.copyfile(args.component/filename,temp/filename)
        shutil.copyfile(c.HERE/'CORRECTIVE-ACCEPTANCE.md',temp/'CORRECTIVE-ACCEPTANCE.md')
        (temp/'INSTALLATION.txt').write_text((c.HERE/'INSTALLATION.txt').read_text())
        unsigned.unlink()
        hashes={p.name:c.digest(p) for p in temp.iterdir() if p.is_file()}
        (temp/'SHA256SUMS').write_text(''.join(h+'  '+name+'\n' for name,h in sorted(hashes.items())))
        save(temp/'COMPONENTS.json',{a:{'version':v,'file':a+'-'+v+'.zip','sha256':hashes[a+'-'+v+'.zip']} for a,_,v in c.PACKAGES})
        # Include the component index itself in the final hash list.
        (temp/'SHA256SUMS').write_text(''.join(c.digest(p)+'  '+p.name+'\n' for p in sorted(temp.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
        os.rename(temp,out)
    print(json.dumps(receipt,indent=2,sort_keys=True))

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['bind','assemble'])
    for arg in ('producer','parent-dir','stage','component','out'):p.add_argument('--'+arg,type=Path)
    p.add_argument('--source-commit',required=True);a=p.parse_args()
    d,_,_=n.old_adapters()
    parent=d.exact_file(a.parent_dir,'Infinity-2103394-Fold-Corrective-EXPERIMENTAL.apk',c.PARENT)
    if a.mode=='bind':
        c.stage(parent,a.stage)
        print(json.dumps(n.bind(a.producer,parent,a.stage,a.source_commit),indent=2,sort_keys=True))
    else:assemble(a)

if __name__=='__main__':main()
