#!/usr/bin/env python3
"""Integrate only the reviewed CC22 startup route into its original DEX shard.

Compiles the verbatim reviewed Java verifier with javac/D8, retains every old
method and branch except an exact additive routing branch, then reassembles the
original shard. This produces a build component, NOT an APK or an installation.
No native build, signing, device write, or user-profile operation is performed.
"""
from __future__ import annotations
import argparse
import difflib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
import integration as i
import release as r

TARGET=i.TARGET_CLASS
CLASS='L'+TARGET.removesuffix('.smali')+';'
NAME='InfinityInstalledCheckpointInstaller'
HELPER='verifyReviewedController22(Ljava/io/File;)Z'
APPLY='applyBeforeNative(Landroid/content/Context;)Z'
METHOD=re.compile(r'(?ms)^\.method [^\n]*\n.*?^\.end method\n?')
OLD_PIN='23320bab6c3a1d661987ee30533dc7a8890ca67ed4ff87b2fc6e6014e2e5b69a'
PIN22='af43f2b192337ed4b342a594e980a1095d236e12209168505697cd0245497306'


def methods(text: str) -> dict[str,str]:
    result={}
    for match in METHOD.finditer(text):
        block=match.group(0);name=block.splitlines()[0].split()[-1]
        i.require(name not in result,'Duplicate method definition')
        result[name]=block
    return result


def merge_router(original: str, helper: str) -> tuple[str,dict]:
    """Preserve original exception paths as well as original executable code."""
    old=methods(original)
    i.require(set(old)=={'<init>()V',APPLY,'hash(Ljava/io/File;)Ljava/lang/String;'},'Unrecognized original startup methods')
    i.require(original.startswith('.class final '+CLASS+'\n'),'Wrong startup class')
    i.require('infinity_cc22' not in original and '0.3.5.22' not in original,'Startup route already patched')
    i.require(set(methods(helper))=={HELPER},'Verifier method is not the exact compiled helper')
    i.require(PIN22 in helper,'Compiled verifier omits reviewed manifest identity')
    block=old[APPLY]
    anchor='    const-string v6, "'+OLD_PIN+'"\n'
    i.require(block.count(anchor)==1 and '    .registers 13\n' in block,'Original register/dispatch preimage differs')
    i.require(block.count('    :goto_1\n')==1 and block.count('    :catch_1\n')==1,'Original common path/exception handler missing')
    selector=('    # INFINITY_CC22_SELECTOR_V1\n'
              '    const-string v6, "'+PIN22+'"\n'
              '    invoke-virtual {v6, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n'
              '    move-result v6\n'
              '    if-nez v6, :infinity_cc22_route\n\n')
    tail=('    # INFINITY_CC22_ROUTE_V1\n'
          '    :infinity_cc22_route\n'
          '    const-string v2, "0.3.5.22"\n'
          '    :infinity_cc22_try_start\n'
          '    invoke-static {v5}, '+CLASS+'->'+HELPER+'\n'
          '    move-result v6\n'
          '    :infinity_cc22_try_end\n'
          '    .catch Ljava/lang/Exception; {:infinity_cc22_try_start .. :infinity_cc22_try_end} :catch_1\n'
          '    goto/16 :goto_1\n')
    patched=block.replace(anchor,selector+anchor,1).replace('.end method',tail+'.end method',1)
    i.require(patched.replace(selector,'',1).replace(tail,'',1)==block,'Original startup instructions were altered')
    result=original.replace(block,patched,1)+'\n'+helper.rstrip()+'\n'
    i.require(set(methods(result))==set(old)|{HELPER},'Unexpected method added or removed')
    for name,body in old.items():
        if name!=APPLY:i.require(methods(result)[name]==body,'Original helper or constructor changed')
    i.require(result.removesuffix('\n'+helper.rstrip()+'\n').replace(patched,block,1)==original,'Unapproved class changes outside additions')
    return result,dict(original_class_sha256=r.sha(original.encode()),
        integrated_smali_sha256=r.sha(result.encode()),
        original_methods_preserved_except_additive_route=True,
        original_exception_paths_preserved=True,new_route_exception_handler='original catch_1 preserves CC22 version',
        new_method=HELPER,added_registers=0)


def javac_helper(java: bytes, work: Path, android: Path, d8: Path, api: int, cp: str) -> tuple[str,dict]:
    i.require(r.sha(java)==i.FINAL_JAVA,'Not the exact reviewed Java router')
    start=b'  private static boolean verifyReviewedController22(File addons) throws Exception {'
    end=b'  private static String hash(File file)throws Exception {'
    i.require(java.count(start)==java.count(end)==1,'Unrecognized reviewed helper boundaries')
    helper=java[java.index(start):java.index(end)]
    text=(b'package com.projectinfinity.kodi;\nimport java.io.File;\nimport java.io.FileInputStream;\n'
          b'import java.security.MessageDigest;\nfinal class InfinityInstalledCheckpointInstaller {\n'+helper+b'}\n')
    src=work/'java'/(NAME+'.java');src.parent.mkdir();src.write_bytes(text)
    classes=work/'javac';classes.mkdir()
    subprocess.run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',str(classes),str(src)],check=True)
    produced=list(classes.rglob('*.class'))
    i.require(len(produced)==1 and produced[0].relative_to(classes).as_posix()==TARGET.replace('.smali','.class'),'Unexpected verifier class dependencies')
    out=work/'verifier-dex';out.mkdir()
    subprocess.run([str(d8),'--release','--min-api',str(api),'--lib',str(android),'--output',str(out),str(produced[0])],check=True)
    files=list(out.glob('*.dex'));i.require(len(files)==1,'Unexpected helper DEX shards')
    dis=work/'verifier-smali'
    subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(files[0]),'-o',str(dis)],check=True)
    bodies=list(dis.rglob('*.smali'));i.require(len(bodies)==1 and bodies[0].relative_to(dis).as_posix()==TARGET,'D8 generated unexpected runtime classes')
    compiled=methods(bodies[0].read_text())
    i.require(set(compiled)=={'<init>()V',HELPER},'D8 verifier generated unexpected methods')
    return compiled[HELPER],dict(reviewed_java_sha256=i.FINAL_JAVA,
        verbatim_helper_java_sha256=r.sha(helper),compiled_helper_class_sha256=r.sha(produced[0].read_bytes()),
        compiled_helper_dex_sha256=r.sha(files[0].read_bytes()),
        helper_smali_sha256=r.sha(compiled[HELPER].encode()),actual_javac_and_d8_executed=True,
        platform_api_stubs_compiled_into_dex=False)


def normalize_module():
    path=r.ROOT/'repairs/cobra-clean-restart/bytecode_guard.py'
    spec=importlib.util.spec_from_file_location('original_instruction_comparison',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    value.selftest()
    return value.normalize


def record_differences(before: dict[str,str], after: dict[str,str]) -> None:
    """Retain first-party source evidence; do not reinterpret a failing gate."""
    output=r.ROOT/'integration-preflight-output'/'dex-roundtrip-comparison'
    output.mkdir(parents=True,exist_ok=True)
    changed=sorted(n for n in before.keys()|after.keys() if before.get(n)!=after.get(n))
    unexpected=[n for n in changed if n!=TARGET]
    (output/'INDEX.json').write_bytes(i.json_bytes(dict(changed=changed,unexpected=unexpected,
        original_classes=len(before),candidate_classes=len(after),protection_gate_relaxed=False)))
    print('=== DEX ROUND-TRIP DIFFERENCES ===\n'+json.dumps(dict(changed=len(changed),unexpected=unexpected),indent=2),flush=True)
    for index,name in enumerate(changed):
        diff=''.join(difflib.unified_diff(before.get(name,'').splitlines(True),after.get(name,'').splitlines(True),fromfile='original/'+name,tofile='assembled/'+name))
        (output/(str(index)+'.diff')).write_text(diff)
        if name in unexpected[:12]:print(diff[:6000],flush=True)


def build(apk: Path, stage: Path, out: Path, android: Path, tools: Path, cp: str) -> dict:
    i.verified_stage(apk,stage)
    i.require(not out.exists(),'Refusing DEX output overwrite')
    i.require(not apk.resolve().is_relative_to(out.resolve()),'Output must not contain original APK')
    for path in (android,tools/'d8',tools/'aapt'):i.require(path.is_file(),'Required Android SDK tool missing')
    out.mkdir(parents=True)
    work=out/'work';work.mkdir()
    try:
        badging=subprocess.check_output([str(tools/'aapt'),'dump','badging',str(apk)],text=True)
        matched=re.search(r"(?m)^sdkVersion:'(\d+)'",badging)
        i.require(matched is not None,'Original APK minimum Android API missing')
        api=int(matched.group(1));i.require(api>=19,'Unsupported original API for verifier try-with-resources')
        (out/'original-apk-badging.txt').write_text(badging)
        dex_map={};owners=[];classes_seen=set()
        with zipfile.ZipFile(apk) as archive:
            for name in archive.namelist():
                if not i.DEX.fullmatch(name):continue
                raw=archive.read(name);dex_map[name]=r.sha(raw)
                dex=work/name;dex.write_bytes(raw)
                listed=subprocess.check_output(['java','-cp',cp,'org.jf.baksmali.Main','list','classes',str(dex)],text=True)
                descriptors=[line.strip() for line in listed.splitlines() if line.strip()]
                i.require(len(descriptors)==len(set(descriptors)) and not classes_seen.intersection(descriptors),'Duplicate class in original DEX')
                classes_seen.update(descriptors)
                if CLASS in descriptors:owners.append(name)
        i.require(len(owners)==1,'Original startup class not uniquely owned')
        name=owners[0];original_dex=work/name;original_smali=work/'original-smali'
        subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(original_dex),'-o',str(original_smali)],check=True)
        original_raw={p.relative_to(original_smali).as_posix():p.read_text() for p in original_smali.rglob('*.smali')}
        helper,helper_proof=javac_helper((stage/'java'/r.JAVA_PATH).read_bytes(),work,android,tools/'d8',api,cp)
        modified,route_proof=merge_router(original_raw[TARGET],helper)
        for filename,pin in json.loads((stage/'addons'/r.UI/'CONTROLLER-PREIMAGES.json').read_text()).items():
            i.require('"'+filename+'"' in helper and '"'+pin+'"' in helper,'Compiled verifier lost a controller pin')
        rejected=0
        for changed in (modified,original_raw[TARGET].replace(OLD_PIN,'0'*64),
                        original_raw[TARGET].replace('.registers 13','.registers 14')):
            try:merge_router(changed,helper)
            except i.IntegrationError:rejected+=1
        i.require(rejected==3,'Startup source guard accepted an invalid/repeated patch')
        modified_root=work/'modified-smali';shutil.copytree(original_smali,modified_root)
        (modified_root/TARGET).write_text(modified)
        artifact=out/'component';artifact.mkdir()
        final=artifact/name
        subprocess.run(['java','-cp',cp,'org.jf.smali.Main','assemble','--api',str(api),str(modified_root),'-o',str(final)],check=True)
        i.require(final.is_file() and final.read_bytes().startswith(b'dex\n'),'No valid assembled DEX component')
        decoded=work/'verified-smali'
        subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(final),'-o',str(decoded)],check=True)
        after_raw={p.relative_to(decoded).as_posix():p.read_text() for p in decoded.rglob('*.smali')}
        normalize=normalize_module()
        before={n:normalize(t) for n,t in original_raw.items()}
        after={n:normalize(t) for n,t in after_raw.items()}
        record_differences(before,after)
        preservation=i.verify_dex_class_maps(before,after)
        new_methods=methods(after_raw[TARGET]);old_methods=methods(original_raw[TARGET])
        i.require(set(new_methods)==set(old_methods)|{HELPER},'Assembled startup class method set changed')
        i.require(normalize(new_methods[HELPER])==normalize(helper),'Compiled verifier changed during assembly')
        for method in old_methods:
            if method!=APPLY:i.require(normalize(old_methods[method])==normalize(new_methods[method]),'Protected startup method changed during assembly')
        i.require(r.sha(apk.read_bytes())==r.APK_SHA,'Original signed APK changed')
        report=dict(state='ANDROID_DEX_COMPONENT_INTEGRATED_NOT_A_SIGNED_APK',
            source_commit=os.environ.get('GITHUB_SHA',''),run_id=os.environ.get('GITHUB_RUN_ID',''),
            source_apk_sha256=r.APK_SHA,min_android_api=api,original_dex_sha256=dex_map[name],
            component_dex_name=name,component_dex_sha256=r.sha(final.read_bytes()),
            total_original_runtime_classes=len(classes_seen),shard_runtime_classes=len(original_raw),
            protected_classes_in_changed_shard=preservation['protected_classes'],
            other_dex_shards={n:h for n,h in dex_map.items() if n!=name},
            other_dex_shards_must_be_copied_byte_identically=True,
            only_runtime_class_changed=TARGET,helper=helper_proof,route=route_proof,
            invalid_reapplication_and_preimage_cases_rejected=rejected,
            decoded_protected_instructions_identical=True,
            original_apk_unchanged=True,native_engine_compiled=False,new_signed_apk=False,
            android_art_verifier_executed=False,android_process_tested=False,
            physical_fold_verified=False,final_lock=False,
            requires_matched_native_engine_and_addons_before_installation=True)
        (out/'STARTUP-DEX-INTEGRATION.json').write_bytes(i.json_bytes(report))
        (out/'reviewed-helper.smali.txt').write_text(helper)
        (out/'original-startup-router.smali.txt').write_text(original_raw[TARGET])
        (out/'integrated-startup-router.smali.txt').write_text(after_raw[TARGET])
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
        return report
    except BaseException:
        component=out/'component'
        if component.exists():shutil.rmtree(component)
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True);p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--android-jar',type=Path,required=True)
    p.add_argument('--build-tools',type=Path,required=True);p.add_argument('--classpath-file',type=Path,required=True)
    a=p.parse_args();build(a.apk,a.stage,a.out,a.android_jar,a.build_tools,a.classpath_file.read_text().strip())
