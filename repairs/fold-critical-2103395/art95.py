#!/usr/bin/env python3
"""Execute the actual newly integrated startup DEX on disposable Android 17 ART.

Extend the passed verifier matrix to 45 cases for all seventeen exact CC25
fixtures. This is component execution, not physical Fold/app acceptance.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
from zipfile import ZipFile
import components95 as c
import dex95 as d
import native95 as n

def old_runner():
    return n.module('corrective93_prior_art_parser',c.ROOT/'audits/2103392-art-component/run.py')

def expected(pins):
    from pathlib import PurePosixPath
    c.require(len(pins)==17,'all seventeen pins required')
    result=['component_fingerprint','fixture_fingerprints','reviewed_cc25_accepted']
    for name in sorted(pins):
        c.require(re.fullmatch(r'[a-z0-9_./-]+',name) and not PurePosixPath(name).is_absolute() and
                  all(v not in ('','.','..') for v in name.split('/')) and re.fullmatch('[0-9a-f]{64}',pins[name]),'invalid fingerprint')
        result+=['changed:'+name,'missing:'+name]
    return result+['symlinked_file_rejected','symlinked_controller_root_rejected',
                  'oversized_file_rejected','missing_controller_root_rejected','legacy_cc21_rejected',
                  'restored_cc25_accepted','fixture_and_sentinel_unchanged','component_still_identical']

def probe_source(component_sha):
    c.require(re.fullmatch('[0-9a-f]{64}',component_sha) is not None,'invalid tested component hash')
    java=(c.ROOT/'audits/2103392-art-component/Controller22ArtProbe.java').read_text()
    # Name the declarations, not just their old values: the old candidate is
    # now the new negative baseline and deliberately has the same fingerprint.
    for name,before,after in (('CANDIDATE',old_runner().CANDIDATE,component_sha),
                              ('BASELINE',old_runner().BASELINE,d.BASELINE)):
        java=c.once(java,'private static final String '+name+' = "'+before+'";',
                         'private static final String '+name+' = "'+after+'";')
    return java.replace('Controller22ArtProbe','Controller25ArtProbe').replace('verifyReviewedController22','verifyReviewedController25').replace('cc22','cc25').replace('CC22','CC25').replace('0.3.5.22','0.3.5.25').replace('original.size() == 13','original.size() == 17').replace('PASSED.size() == 37','PASSED.size() == 45')

def prepare(apk,component,out,android,tools):
    c.require(not out.exists(),'ART output exists')
    proof=json.loads((component/'STARTUP-DEX-INTEGRATION.json').read_text())
    dex=component/'component/classes.dex'
    c.require(proof['source_commit']==os.environ['GITHUB_SHA'] and proof['source_apk_sha256']==c.PARENT,'wrong DEX provenance')
    c.require(proof['decoded_protected_instructions_identical'] and proof['runtime_classes_changed']==sorted(__import__('java95').TARGETS),'DEX class preservation missing')
    c.require(proof['fields']['encoded_values_and_presence_preserved'] and proof['fields']['exact_field_definitions_verified']==25870,'field preservation missing')
    c.require(c.digest(dex)==proof['component_dex_sha256'] and proof['original_dex_sha256']==d.BASELINE,'component fingerprint mismatch')
    source=c.read_parent(apk);final=c.components(source)
    pins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json']);cases=expected(pins)
    c.require(len(cases)==45,'incomplete ART matrix')
    inputs=out/'inputs';inputs.mkdir(parents=True)
    for name,pin in pins.items():
        body=final[c.CC+'/'+name];c.require(c.sha(body)==pin,'fixture mismatch')
        path=inputs/'controller-input'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
    (inputs/'pins.tsv').write_text(''.join(name+'\t'+pin+'\n' for name,pin in sorted(pins.items())))
    shutil.copyfile(dex,inputs/'candidate.dex')
    with ZipFile(apk) as z:
        (inputs/'baseline.dex').write_bytes(z.read('classes.dex'))
        (inputs/'classes2.dex').write_bytes(z.read('classes2.dex'))
    c.require(c.digest(inputs/'baseline.dex')==d.BASELINE and c.digest(inputs/'classes2.dex')==d.SHARD2,'protected baseline changed')
    java=probe_source(proof['component_dex_sha256'])
    src=out/'Controller25ArtProbe.java';src.write_text(java)
    classes=out/'probe-classes';classes.mkdir()
    subprocess.run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',str(classes),str(src)],check=True)
    files=list(classes.rglob('*.class'))
    c.require(len(files)==1 and files[0].name=='Controller25ArtProbe.class','unexpected probe class')
    output=out/'probe-dex';output.mkdir()
    subprocess.run([str(tools/'d8'),'--release','--min-api','26','--lib',str(android),'--output',str(output),str(files[0])],check=True)
    shutil.copyfile(output/'classes.dex',inputs/'probe.dex')
    report={'source_commit':os.environ['GITHUB_SHA'],'controller_pins':pins,'component_sha256':proof['component_dex_sha256'],
            'expected_cases':cases,'input_hashes':{p.relative_to(inputs).as_posix():c.digest(p) for p in inputs.rglob('*') if p.is_file()},
            'physical_fold_verified':False,'final_lock':False}
    import ui_android95
    ui_android95.prepare(out, android, tools, dex, inputs/'classes2.dex')
    (out/'ART-INPUTS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')

def android(out,adb='adb'):
    proof=json.loads((out/'ART-INPUTS.json').read_text());inputs=out/'inputs'
    c.require(proof['source_commit']==os.environ['GITHUB_SHA'],'wrong ART source')
    c.require({p.relative_to(inputs).as_posix():c.digest(p) for p in inputs.rglob('*') if p.is_file()}==proof['input_hashes'],'ART input changed')
    cases=expected(proof['controller_pins']);c.require(cases==proof['expected_cases'],'case drift')
    token=os.environ['GITHUB_RUN_ID'];attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1')
    c.require(token.isdecimal() and attempt.isdecimal(),'invalid disposable ID')
    device='/data/local/tmp/infinity-cc25-art-'+token+'-'+attempt
    report={'source_commit':os.environ['GITHUB_SHA'],'passed':False,'component_sha256':proof['component_sha256'],
            'source_apk_sha256':c.PARENT,'native_engine_loaded':False,'installed_app_started':False,
            'whole_process_shutdown_tested':False,'physical_fold_verified':False,'final_lock':False,'cases':[]}
    try:
        rows=subprocess.check_output([adb,'devices'],text=True).splitlines()[1:]
        devices=[line.split()[0] for line in rows if line.strip().endswith('\tdevice')]
        c.require(len(devices)==1 and devices[0].startswith('emulator-'),'only disposable emulator permitted')
        def shell(cmd):
            return subprocess.check_output([adb,'-s',devices[0],'shell',cmd],text=True,stderr=subprocess.STDOUT)
        api=int(shell('getprop ro.build.version.sdk').strip());release=shell('getprop ro.build.version.release').strip()
        c.require(api==37 and release.split('.')[0]=='17','Android 17/API37 required')
        report['platform']={'api':api,'release':release,'abi':shell('getprop ro.product.cpu.abi').strip()}
        shell('test ! -e '+shlex.quote(device)+' && mkdir '+shlex.quote(device))
        subprocess.run([adb,'-s',devices[0],'push',str(inputs)+'/.',device],check=True)
        shell('chmod 444 '+' '.join(shlex.quote(device+'/'+name) for name in ('candidate.dex','baseline.dex','classes2.dex','probe.dex')))
        for variant,matrix in (('baseline',['baseline_has_no_cc25_verifier']),('candidate',cases)):
            classpath=':'.join(device+'/'+name for name in ('probe.dex',variant+'.dex','classes2.dex'))
            command='CLASSPATH='+shlex.quote(classpath)+' /system/bin/app_process -Xverify:all /system/bin Controller25ArtProbe '+variant+' '+shlex.quote(device)+' 37'
            result=subprocess.run([adb,'-s',devices[0],'shell',command],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
            (out/(variant+'-art.log')).write_text(result.stdout);print(result.stdout,flush=True)
            c.require(result.returncode==0,'ART execution failed '+variant)
            report['cases'].append(old_runner().parse_result(result.stdout,variant,matrix,37))
        import ui_android95
        ui = ui_android95.run(out, adb, devices[0])
        report.update(passed=True,android_art_component_executed=True,candidate_cases_passed=45,baseline_control_cases_passed=1,integrated_search_android=ui)
    finally:
        (out/'ART-COMPONENT-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','android'])
    p.add_argument('--out',type=Path,required=True)
    for arg in ('apk','component','android-jar','build-tools'):p.add_argument('--'+arg,type=Path)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.apk,a.component,a.out,a.android_jar,a.build_tools)
    else:print(json.dumps(android(a.out),indent=2))
