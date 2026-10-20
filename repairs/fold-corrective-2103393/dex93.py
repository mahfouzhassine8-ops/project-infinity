#!/usr/bin/env python3
"""Add the exact CC23 verifier to 2103392's one existing startup class.

Reuse the passed DEX field/instruction preservation machinery. No other class,
method, encoded field, second shard or Cobra bytecode may change.
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
import corrective as c
import native93 as n

BASELINE='2b54ba6ede1461cfcd0e1788de8c35a7cf63df582d9c8e03bb3c583890b8de54'
SHARD2='d4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca'
TARGET='com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'
CLASS='L'+TARGET.removesuffix('.smali')+';'
HELPER='verifyReviewedController23(Ljava/io/File;)Z'
APPLY='applyBeforeNative(Landroid/content/Context;)Z'

def previous():
    n.old_adapters()
    import startup_dex
    return startup_dex

def java_router(original, final):
    _,r,i=n.old_adapters()
    raw=r.java_router((r.JAVA_BASE/r.JAVA_PATH).read_bytes(),original)
    c.require(c.sha(raw)==i.FINAL_JAVA,'CC22 Java source mismatch')
    start=b'  private static boolean verifyReviewedController22(File addons) throws Exception {'
    end=b'  private static String hash(File file)throws Exception {'
    c.require(raw.count(start)==raw.count(end)==1,'wrong original verifier boundaries')
    helper=raw[raw.index(start):raw.index(end)].replace(b'verifyReviewedController22',b'verifyReviewedController23',1)
    before=json.loads(original[c.UI+'/CONTROLLER-PREIMAGES.json'])
    after=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
    for name,pin in before.items():
        if pin!=after[name]:helper=c.once(helper,pin.encode(),after[name].encode())
    pin=c.sha(final[c.CC+'/addon.xml']).encode()
    anchor=b'      if("'+c.sha(original[c.CC+'/addon.xml']).encode()+b'".equals(cc)) {'
    route=(b'      if("'+pin+b'".equals(cc)) {\n'
           b'        controllerVersion="0.3.5.23";\n'
           b'        controller=verifyReviewedController23(addons);\n'
           b'      } else '+anchor.lstrip())
    result=c.once(c.once(raw,anchor,route),end,helper+end)
    return result,helper

def merge_router(original, helper, pin):
    old=previous().methods(original)
    c.require(set(old)=={'<init>()V',APPLY,'hash(Ljava/io/File;)Ljava/lang/String;',
                        'verifyReviewedController22(Ljava/io/File;)Z'},'unrecognized signed startup class')
    c.require(original.startswith('.class final '+CLASS+'\n') and 'verifyReviewedController23' not in original,'wrong/already corrected class')
    c.require(set(previous().methods(helper))=={HELPER} and pin in helper,'incomplete compiled verifier')
    block=old[APPLY]
    anchor='    const-string v6, "af43f2b192337ed4b342a594e980a1095d236e12209168505697cd0245497306"\n'
    c.require(block.count(anchor)==1 and '    .registers 13\n' in block and
              block.count('    :goto_1\n')==1 and block.count('    :catch_1\n')==1,'original register/route/catch drift')
    selector=('    const-string v6, "'+pin+'"\n'
              '    invoke-virtual {v6, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n'
              '    move-result v6\n'
              '    if-nez v6, :infinity_cc23_route\n\n')
    tail=('    :infinity_cc23_route\n'
          '    const-string v2, "0.3.5.23"\n'
          '    :infinity_cc23_try_start\n'
          '    invoke-static {v5}, '+CLASS+'->'+HELPER+'\n'
          '    move-result v6\n'
          '    :infinity_cc23_try_end\n'
          '    .catch Ljava/lang/Exception; {:infinity_cc23_try_start .. :infinity_cc23_try_end} :catch_1\n'
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
                    before_raw[TARGET].replace('af43f2b192337ed4b342a594e980a1095d236e12209168505697cd0245497306','0'*64)):
        try:merge_router(invalid,compiled[HELPER],pin)
        except ValueError:rejected+=1
    c.require(rejected==3,'startup guards accepted malformed/repeated input')
    modified=work/'modified-smali';shutil.copytree(original_smali,modified)
    (modified/TARGET).write_text(merged)
    component=out/'component';component.mkdir();candidate=component/'classes.dex'
    subprocess.run(['java','-cp',cp,'org.jf.smali.Main','assemble','--api',api,str(modified),'-o',str(candidate)],check=True)
    fields=old.preserve_fields(original_dex,candidate,work,int(api),cp)
    decoded=work/'verified-smali'
    subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(candidate),'-o',str(decoded)],check=True)
    after_raw={p.relative_to(decoded).as_posix():p.read_text() for p in decoded.rglob('*.smali')}
    normalize=old.normalize_module()
    before={n:normalize(b) for n,b in before_raw.items()};after={n:normalize(b) for n,b in after_raw.items()}
    old.record_differences(before,after)
    _,_,integration=n.old_adapters()
    preservation=integration.verify_dex_class_maps(before,after)
    c.require(fields['protected_class_definitions_from_original']==preservation['protected_classes'],'class/field proof mismatch')
    methods=old.methods(after_raw[TARGET]);old_methods=old.methods(before_raw[TARGET])
    c.require(set(methods)==set(old_methods)|{HELPER},'changed startup method inventory')
    c.require(normalize(methods[HELPER])==normalize(compiled[HELPER]),'compiled verifier drift')
    for name,body in old_methods.items():
        if name!=APPLY:c.require(normalize(body)==normalize(methods[name]),'existing startup method changed')
    report={'source_commit':os.environ['GITHUB_SHA'],'source_apk_sha256':c.PARENT,
            'original_dex_sha256':BASELINE,'component_dex_name':'classes.dex','component_dex_sha256':c.digest(candidate),
            'only_runtime_class_changed':TARGET,'protected_classes_in_changed_shard':preservation['protected_classes'],
            'decoded_protected_instructions_identical':True,'fields':fields,'invalid_inputs_rejected':rejected,
            'other_dex_shards':{'classes2.dex':SHARD2},'native_engine_compiled':False,
            'physical_fold_verified':False,'final_lock':False,'java_router_sha256':c.sha(java)}
    (out/'STARTUP-DEX-INTEGRATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (out/'reviewed-helper.smali.txt').write_text(compiled[HELPER])
    (out/'integrated-startup-router.smali.txt').write_text(after_raw[TARGET])
    # Inspect only identifiers, never stream URLs/account details.
    hits=[]
    for name,text in before_raw.items():
        if any(word in text.lower() for word in ('moon','crescent','reloadskin','theme_mode','themepolicy')):
            hits.append({'class':name,'matches':[line.strip()[:200] for line in text.splitlines() if any(word in line.lower() for word in ('moon','crescent','reloadskin','theme_mode','themepolicy'))][:25]})
    (out/'THEME-ROUTE-IDENTIFIERS.json').write_text(json.dumps(hits,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('apk','stage','out','android-jar','build-tools','classpath-file'):
        p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.apk,a.stage,a.out,a.android_jar,a.build_tools,a.classpath_file.read_text().strip()),indent=2))
