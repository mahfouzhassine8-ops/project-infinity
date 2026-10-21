#!/usr/bin/env python3
"""Add exact CC25 verification and scoped Search/evidence hooks to signed 2103394.

Preserve all original field definitions and all 7,852 other class definitions.
The two UI/evidence hooks reverse exactly; the startup route is additive.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile
import components95 as c
import native95 as n

BASELINE='a0ce34e047168b9e5c3a4bc253eafe87a1b080c9f0a1bdd93535512ed942189a'
SHARD2='d4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca'
TARGET='com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'
CLASS='L'+TARGET.removesuffix('.smali')+';'
HELPER='verifyReviewedController25(Ljava/io/File;)Z'
APPLY='applyBeforeNative(Landroid/content/Context;)Z'

def previous():
    n.old_adapters()
    import startup_dex
    return startup_dex

def java_router(original, final):
    pins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
    c.require(len(pins)==17,'all seventeen controller fingerprints required')
    pairs=',\n'.join('      {"'+name+'","'+pin+'"}' for name,pin in sorted(pins.items()))
    helper=('  private static boolean verifyReviewedController25(File addons) throws Exception {\n'
            '    File root = new File(addons,"script.infinity.commandcenter").getAbsoluteFile();\n'
            '    if (!root.equals(root.getCanonicalFile()) || !root.isDirectory()) return false;\n'
            '    String[][] pins = {\n'+pairs+'\n    };\n'
            '    for (String[] pin : pins) {\n'
            '      File file = new File(root,pin[0]).getAbsoluteFile();\n'
            '      if (!file.equals(file.getCanonicalFile()) || !file.isFile()) return false;\n'
            '      MessageDigest digest=MessageDigest.getInstance("SHA-256");\n'
            '      int size=0; byte[] buffer=new byte[8192];\n'
            '      try (FileInputStream stream=new FileInputStream(file)) {\n'
            '        int count; while ((count=stream.read(buffer))!=-1) {\n'
            '          size+=count; if (size>4194304) return false; digest.update(buffer,0,count);\n'
            '        }\n'
            '      }\n'
            '      StringBuilder hash=new StringBuilder();\n'
            '      for (byte value : digest.digest()) hash.append(String.format(java.util.Locale.ROOT,"%02x",value&255));\n'
            '      if (!hash.toString().equals(pin[1])) return false;\n'
            '    }\n'
            '    return true;\n  }\n').encode()
    return helper,helper

def merge_router(original, helper, pin):
    old=previous().methods(original)
    c.require(set(old)=={'<init>()V',APPLY,'hash(Ljava/io/File;)Ljava/lang/String;',
                        'verifyReviewedController22(Ljava/io/File;)Z', 'verifyReviewedController23(Ljava/io/File;)Z', 'verifyReviewedController24(Ljava/io/File;)Z'},'unrecognized signed startup class')
    c.require(original.startswith('.class final '+CLASS+'\n') and 'verifyReviewedController25' not in original,'wrong/already corrected class')
    c.require(set(previous().methods(helper))=={HELPER} and pin in helper,'incomplete compiled verifier')
    block=old[APPLY]
    anchor='    const-string v6, "3e2e182758a890d1ad98992a8cb11ea704c54eaab41b940dde03ab6bd68fa39c"\n'
    c.require(block.count(anchor)==1 and '    .registers 13\n' in block and
              block.count('    :goto_1\n')==1 and block.count('    :catch_1\n')==1,'original register/route/catch drift')
    selector=('    const-string v6, "'+pin+'"\n'
              '    invoke-virtual {v6, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n'
              '    move-result v6\n'
              '    if-nez v6, :infinity_cc25_route\n\n')
    tail=('    :infinity_cc25_route\n'
          '    const-string v2, "0.3.5.25"\n'
          '    :infinity_cc25_try_start\n'
          '    invoke-static {v5}, '+CLASS+'->'+HELPER+'\n'
          '    move-result v6\n'
          '    :infinity_cc25_try_end\n'
          '    .catch Ljava/lang/Exception; {:infinity_cc25_try_start .. :infinity_cc25_try_end} :catch_1\n'
          '    goto/16 :goto_1\n')
    patched=block.replace(anchor,selector+anchor,1).replace('.end method',tail+'.end method',1)
    c.require(patched.replace(selector,'',1).replace(tail,'',1)==block,'original startup route altered')
    result=original.replace(block,patched,1)+'\n'+helper.rstrip()+'\n'
    c.require(result.removesuffix('\n'+helper.rstrip()+'\n').replace(patched,block,1)==original,'changes outside additive CC23 route')
    return result

def build(apk, stage, out, android, tools, cp):
    old=previous()
    original=c.read_parent(apk);final=c.components(original)
    c.require(c.ledger(original,final)==json.loads((c.HERE/'MEMBER-DELTA.json').read_text()),'unreviewed source')
    c.require(not out.exists(),'DEX output exists')
    out.mkdir();work=out/'work';work.mkdir()
    badging=subprocess.check_output([str(tools/'aapt'),'dump','badging',str(apk)],text=True)
    minimum=re.search(r"(?m)^sdkVersion:'(\d+)'",badging)
    c.require(minimum is not None and int(minimum.group(1))>=19,'unknown/unsupported original Android API')
    api=minimum.group(1)
    (c.ROOT/'integration-preflight-output').mkdir(exist_ok=True)
    java,helper=java_router(original,final)
    source=work/'java'/TARGET.replace('.smali','.java');source.parent.mkdir(parents=True)
    source.write_bytes(b'package com.projectinfinity.kodi;\nimport java.io.*;\nimport java.security.MessageDigest;\n'
                       b'final class InfinityInstalledCheckpointInstaller {\n'+helper+b'}\n')
    classes=work/'javac';classes.mkdir()
    subprocess.run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',str(classes),str(source)],check=True)
    produced=list(classes.rglob('*.class'))
    c.require(len(produced)==1 and produced[0].relative_to(classes).as_posix()==TARGET.replace('.smali','.class'),'unapproved helper dependency')
    helperdex=work/'helper-dex';helperdex.mkdir()
    subprocess.run([str(tools/'d8'),'--release','--min-api',api,'--lib',str(android),'--output',str(helperdex),str(produced[0])],check=True)
    helper_smali=work/'helper-smali'
    subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(helperdex/'classes.dex'),'-o',str(helper_smali)],check=True)
    compiled=old.methods((helper_smali/TARGET).read_text())
    c.require(set(compiled)=={'<init>()V',HELPER},'helper emitted extra methods')
    with ZipFile(apk) as z:
        before_bytes=z.read('classes.dex');second=z.read('classes2.dex')
        c.require(c.sha(before_bytes)==BASELINE and c.sha(second)==SHARD2,'wrong protected DEX shards')
    original_dex=work/'original.dex';original_dex.write_bytes(before_bytes)
    original_smali=work/'original-smali'
    subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(original_dex),'-o',str(original_smali)],check=True)
    before_raw={p.relative_to(original_smali).as_posix():p.read_text() for p in original_smali.rglob('*.smali')}
    pin=c.sha(final[c.CC+'/addon.xml'])
    merged=merge_router(before_raw[TARGET],compiled[HELPER],pin)
    for name,digest in json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json']).items():
        c.require('"'+name+'"' in compiled[HELPER] and digest in compiled[HELPER],'missing compiled pin')
    rejected=0
    for invalid in (merged,before_raw[TARGET].replace('.registers 13','.registers 14'),
                    before_raw[TARGET].replace('3e2e182758a890d1ad98992a8cb11ea704c54eaab41b940dde03ab6bd68fa39c','0'*64)):
        try:merge_router(invalid,compiled[HELPER],pin)
        except ValueError:rejected+=1
    c.require(rejected==3,'startup guards accepted malformed/repeated input')
    modified=work/'modified-smali';shutil.copytree(original_smali,modified)
    (modified/TARGET).write_text(merged)
    import java95
    added, java_proof = java95.build_and_patch(before_raw, modified, work, android, tools, cp, int(api))
    component=out/'component';component.mkdir();candidate=component/'classes.dex'
    subprocess.run(['java','-cp',cp,'org.jf.smali.Main','assemble','--api',api,str(modified),'-o',str(candidate)],check=True)
    fields=java95.preserve_fields(original_dex,candidate,work,int(api),cp)
    decoded=work/'verified-smali'
    subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(candidate),'-o',str(decoded)],check=True)
    after_raw={p.relative_to(decoded).as_posix():p.read_text() for p in decoded.rglob('*.smali')}
    normalize=old.normalize_module()
    before={n:normalize(b) for n,b in before_raw.items()};after={n:normalize(b) for n,b in after_raw.items()}
    old.record_differences(before,after)
    preservation=java95.verify_class_maps(before,after,added)
    c.require(fields['protected_class_definitions_from_original']==preservation['protected_classes'],'class/field proof mismatch')
    methods=old.methods(after_raw[TARGET]);old_methods=old.methods(before_raw[TARGET])
    c.require(set(methods)==set(old_methods)|{HELPER},'changed startup method inventory')
    c.require(normalize(methods[HELPER])==normalize(compiled[HELPER]),'compiled verifier drift')
    for name,body in old_methods.items():
        if name!=APPLY:c.require(normalize(body)==normalize(methods[name]),'existing startup method changed')
    report={'source_commit':os.environ['GITHUB_SHA'],'source_apk_sha256':c.PARENT,
            'original_dex_sha256':BASELINE,'component_dex_name':'classes.dex','component_dex_sha256':c.digest(candidate),
            'runtime_classes_changed':sorted(java95.TARGETS),'added_classes':sorted(added),'java_ui_evidence':java_proof,'protected_classes_in_changed_shard':preservation['protected_classes'],
            'decoded_protected_instructions_identical':True,'fields':fields,'invalid_inputs_rejected':rejected,
            'other_dex_shards':{'classes2.dex':SHARD2},'native_engine_compiled':False,
            'physical_fold_verified':False,'final_lock':False,'reviewed_helper_source_sha256':c.sha(java)}
    (out/'STARTUP-DEX-INTEGRATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (out/'reviewed-helper.smali.txt').write_text(compiled[HELPER])
    (out/'integrated-startup-router.smali.txt').write_text(after_raw[TARGET])
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('apk','stage','out','android-jar','build-tools','classpath-file'):
        p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.apk,a.stage,a.out,a.android_jar,a.build_tools,a.classpath_file.read_text().strip()),indent=2))
