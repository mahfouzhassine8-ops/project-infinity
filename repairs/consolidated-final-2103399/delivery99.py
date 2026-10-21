"""Permanent final signature; strictly reuse the actual compiled/tested 98 engine.

The final source and native/ART source are recorded separately. No fresh compile
is claimed, no original proof is rewritten, no native/DEX/provider file changes.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile,ZIP_DEFLATED
import components99 as f
import delivery98 as previous
import native98
import dex98
c=f.c
ORIGIN='53ed214b629f078d6ab48b992ecdeca468ab1d88'
ORIGIN_RUN=39662467387
CODE=2103399
NAME='1.0.9-All-In-One-Bugfix-TEST0009'
FILENAME='Infinity-2103399-Fold-Corrective-EXPERIMENTAL.apk'
save=previous.save


def verify_origin(directory,tools):
    receipt=json.loads((directory/'INFINITY-2103398-DELIVERY.json').read_text())
    c.require(receipt['source_commit']==ORIGIN and receipt['version_code']==2103398,
              'actual completed originating native/ART run required')
    apk=directory/previous.FILENAME
    c.require(c.digest(apk)==receipt['apk_sha256'],'signed origin hash mismatch')
    d,_,_=native98.old_adapters()
    signature=d.verify_signature(apk,tools)
    c.require(receipt['signed_permanently'] and receipt['permanent_certificate_sha256']==previous.CERT and
              receipt['complete_native_engine_compiled'] and receipt['cobra_members_and_instructions_byte_identical'] and
              not receipt['essential_first_guards_weakened'],'origin preservation/compilation missing')
    with ZipFile(directory/'Infinity-2103398-Source-and-Build-Receipts.zip') as z:
        c.require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'corrupt origin source archive')
        sources=json.loads(z.read('NATIVE-SOURCE-MAP.json'))
        names={n[7:] for n in z.namelist() if n.startswith('native/') and not n.endswith('/')}
        c.require(len(sources)==len(names)==9404 and set(sources)==names,'all compiler inputs required')
        for n,h in sources.items():c.require(c.sha(z.read('native/'+n))==h,'native compiler source drift '+n)
        engine=json.loads(z.read('receipts/ENGINE-PROOF.json'))
        art=json.loads(z.read('receipts/ART-COMPONENT-VERIFICATION.json'))
        dex=json.loads(z.read('receipts/STARTUP-DEX-INTEGRATION.json'))
        binding=json.loads(z.read('receipts/FOLD98-NATIVE-BINDING.json'))
        c.require(engine['source_commit']==ORIGIN and engine['complete_native_engine_compiled'] and
                  engine['native_sha256']==receipt['native_sha256'],'real full native proof required')
        c.require(binding['source_commit']==ORIGIN and binding['all_other_sources_byte_identical'] and
                  set(binding['after'])==native98.PATHS,'origin native scope mismatch')
        c.require(art['source_commit']==dex['source_commit']==ORIGIN and art['passed'] and
                  art['candidate_cases_passed']==45 and art['baseline_control_cases_passed']==1 and
                  art['platform']['api']==37 and art['integrated_search_android']['passed'] and
                  art['integrated_search_android']['assertions']==33,'real Android17 execution proof missing')
        c.require(dex['decoded_protected_instructions_identical'] and
                  dex['fields']['encoded_values_and_presence_preserved'] and
                  dex['fields']['all_original_field_definitions_verified'],'DEX/Cobra preservation proof missing')
    with ZipFile(apk) as z:
        c.require(c.sha(z.read(previous.ENGINE))==engine['native_sha256'],'actual APK engine differs from proof')
        c.require(c.sha(z.read('classes.dex'))==dex['component_dex_sha256'],'actual DEX differs from executed DEX')
        c.require(c.sha(z.read('classes2.dex'))==dex98.SHARD2,'second DEX shard drift')
    return apk,receipt,signature,sources


def assemble(directory,out,commit):
    c.require(not out.exists() and re.fullmatch('[a-f0-9]{40}',commit),'new delivery/full source SHA mandatory')
    tools=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    parent,origin,parent_signature,sources=verify_origin(directory,tools)
    with ZipFile(parent) as z:
        before={n[14:]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and
                not n.endswith('/') and n.split('/')[2] in f.VERSIONS}
    after,delta=f.components(before)
    d,_,_=native98.old_adapters()
    c.require(all(os.environ.get(k) for k in d.KEYS),'original permanent signing secrets mandatory')
    manifest=d.module('final99_manifest',c.ROOT/'repairs/critical-preview-2103376/manifest_patch.py')
    manifest.PARENT_CODE=2103398;manifest.CODE=CODE
    manifest.PARENT_NAME=previous.NAME;manifest.NAME=NAME
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.infinity-final99-',dir=out.parent) as temporary:
        temp=Path(temporary);unsigned=temp/'unsigned.apk';signed=temp/FILENAME
        with ZipFile(parent) as z:
            patched,edits=manifest.patch(z.read('AndroidManifest.xml'))
            c.require(len(edits)==2 and {v['field'] for v in edits}=={'versionCode','versionName'},'package manifest scope changed')
            targets={'assets/addons/'+n:b for n,b in delta.items()}
            targets['AndroidManifest.xml']=patched
            evidence=json.loads(c.evidence_manifest(after))
            encoded=(json.dumps(evidence,indent=2,sort_keys=True)+'\n').encode()
            for code in range(2103395,2103400):targets['assets/infinity-'+str(code)+'-components.json']=encoded
            with ZipFile(unsigned,'w',allowZip64=True) as result:
                for info in z.infolist():
                    if not previous.SIGNATURE.fullmatch(info.filename):
                        result.writestr(copy.copy(info),targets.get(info.filename,z.read(info)))
                for name in sorted(set(targets)-set(z.namelist())):
                    result.writestr(name,targets[name],compress_type=ZIP_DEFLATED,compresslevel=9)
        previous.verify_delta(parent,unsigned,targets)
        subprocess.run(['bash',str(c.ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
        signature=d.verify_signature(signed,tools)
        changed=previous.verify_delta(parent,signed,targets)
        badging=d.command([tools/'aapt','dump','badging',signed])
        c.require("package: name='com.projectinfinity.kodi' versionCode='2103399'" in badging and
                  "versionName='"+NAME+"'" in badging and 'application-debuggable' not in badging,'install-over package/version/debug check failed')
        with ZipFile(parent) as old,ZipFile(signed) as z:
            for n in (previous.ENGINE,previous.RECORDER,'classes.dex','classes2.dex'):
                c.require(z.read(n)==old.read(n),'native/DEX mutation in final presentation stage '+n)
            for addon,version in f.VERSIONS.items():
                filename=addon+'-'+version+'.zip'
                entries=sorted(n for n in z.namelist() if n.startswith('assets/addons/'+addon+'/') and not n.endswith('/'))
                if addon not in (c.UI,c.SKIN,c.HEALTH):shutil.copyfile(directory/filename,temp/filename)
                else:
                    with ZipFile(temp/filename,'w',compression=ZIP_DEFLATED,compresslevel=9) as component:
                        for n in entries:component.writestr(n[14:],z.read(n))
                with ZipFile(temp/filename) as component:
                    c.require(component.testzip() is None and len(component.namelist())==len(set(component.namelist())) and
                              set(component.namelist())=={n[14:] for n in entries},'invalid component archive '+addon)
                    c.require(all(component.read(n)==z.read('assets/addons/'+n) for n in component.namelist()),'ZIP/APK mismatch '+addon)
        receipt=dict(origin)
        receipt.update(version_code=CODE,version_name=NAME,source_commit=commit,
            build_run=int(os.environ['GITHUB_RUN_ID']),
            build_url='https://github.com/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID'],
            immediate_parent_commit=ORIGIN,immediate_parent_apk_sha256=c.digest(parent),apk_sha256=c.digest(signed),
            native_build_source_commit=ORIGIN,native_build_run=ORIGIN_RUN,native_compilation_reused=True,
            native_source_map_sha256=c.sha(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()),
            all_9404_compiler_inputs_verified_and_unchanged=True,native_binary_byte_identical_to_verified_2103398=True,
            original_engine_proof_not_rewritten=True,art_tested_source_commit=ORIGIN,
            tested_dex_byte_identical_to_verified_2103398=True,matching_component_versions=f.VERSIONS,
            apk_changed_members=changed,apk_changed_members_from_2103397=sorted(set(origin['apk_changed_members'])|set(changed)),
            final_presentation_files=sorted(delta),final_stage_source_files=sorted(delta),final_stage_scope='Popup presentation and Health report classification',physical_fold_verified=False,actual_install_over_tested=False,
            final_lock=False,experimental_only=True)
        save(temp/'INFINITY-2103399-DELIVERY.json',receipt)
        origin_manifest=json.loads((directory/'CHANGED-FILE-MANIFEST.json').read_text())
        cumulative=copy.deepcopy(origin_manifest['components'])
        cumulative['versions']=f.VERSIONS
        for n,b in delta.items():
            entry=cumulative['changed'].setdefault(n,{'before':c.sha(before[n])})
            entry['after']=c.sha(b)
        changed_manifest={'components':cumulative,'native':origin_manifest['native'],'dex':origin_manifest['dex'],
            'final_stage_changed':{n:{'before':c.sha(before[n]),'after':c.sha(b)} for n,b in delta.items()},
            'originating_98_changes':origin['apk_changed_members'],'final_apk_changes':changed,
            'native_and_dex_changed_in_final_stage':False,'originating_source_commit':ORIGIN,'final_source_commit':commit}
        save(temp/'CHANGED-FILE-MANIFEST.json',changed_manifest)
        report=json.loads((directory/'PASS-FAIL-REPORT.json').read_text())
        report.update(source_commit=commit,native_and_android17_source_commit=ORIGIN,native_and_android17_run=ORIGIN_RUN,
            final_presentation_tests_passed=9,all_final_components_match_apk=True,
            android17_execution_scope='Production DEX and component/Search UI on API37 emulator; whole ARM64 app execution not claimed',
            whole_apk_android_execution='NEEDS EVIDENCE: physical ARM64 installation and execution',
            physical_popup_reference_approval='NEEDS EVIDENCE',final_lock=False)
        report['workstreams']['7']['implementation']='IMPLEMENTED: proven observer/Health correction; other reported TMDb/SlyGuy causes NEEDS EVIDENCE'
        save(temp/'PASS-FAIL-REPORT.json',report)
        (temp/'FINAL-SIGNATURE.txt').write_text(signature)
        (temp/'PARENT-SIGNATURE.txt').write_text(parent_signature)
        (temp/'APK-BADGING.txt').write_text(badging)
        for leaf in ('ENGINE-PROOF.json','ART-COMPONENT-VERIFICATION.json','STARTUP-DEX-INTEGRATION.json','FOLD98-NATIVE-BINDING.json','BASELINE97-REUSED-PROOFS.json','TARGETED-SOURCE-REGRESSIONS.log'):
            shutil.copyfile(directory/leaf,temp/leaf)
        shutil.copyfile(c.ROOT/'final99-tests.log',temp/'FINAL-PRESENTATION-TESTS.log')
        for leaf in ('INSTALLATION.txt','CORRECTIVE-ACCEPTANCE.md'):
            shutil.copyfile(f.HERE/leaf,temp/leaf)
        with ZipFile(directory/'Infinity-2103398-Source-and-Build-Receipts.zip') as old,ZipFile(
            temp/'Infinity-2103399-Source-and-Build-Receipts.zip','w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
            for info in old.infolist():archive.writestr(copy.copy(info),old.read(info.filename))
            archive.writestr('FINAL-SOURCE-COMMIT.txt',commit+'\n')
            for n,b in delta.items():archive.writestr('final-components/'+n,b)
            for path in sorted(f.HERE.iterdir()):
                if path.is_file():archive.write(path,'final-corrective/'+path.name)
            for leaf in ('INFINITY-2103399-DELIVERY.json','CHANGED-FILE-MANIFEST.json','PASS-FAIL-REPORT.json','FINAL-PRESENTATION-TESTS.log'):
                archive.write(temp/leaf,'final-receipts/'+leaf)
        unsigned.unlink()
        save(temp/'COMPONENTS.json',{a:{'version':v,'file':a+'-'+v+'.zip','sha256':c.digest(temp/(a+'-'+v+'.zip'))} for a,v in f.VERSIONS.items()})
        (temp/'SHA256SUMS').write_text(''.join(c.digest(p)+'  '+p.name+'\n' for p in sorted(temp.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
        os.rename(temp,out)
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=='__main__':
    c.require(len(sys.argv)==4,'origin-directory output-directory final-source-commit required')
    assemble(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
