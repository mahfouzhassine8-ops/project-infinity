"""Retain passed15/DEX inputs; correct only the failed build-path consumer.

The previous workflow remains FAIL. Its immutable artifact is accepted only
after its individual source/DEX gates and exact current runtime bindings match.
The original-key source/native/JCA checks then run for real, without resigning.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

import module_dex
import sign_module_bundle

ROOT=Path(__file__).parent
REPOSITORY='mahfouzhassine8-ops/project-infinity'
SOURCE='772f10fb95c893264f112a18bb3a62053172f4ec'
RUN=40274233925
ARTIFACT=12629472776
DIGEST='aa3121605ef2ef3b6ec8319eef9cbee580bfb84e47b3bbd0aa249e84767fe19f'


def api(path):
    request=urllib.request.Request('https://api.github.com/repos/'+REPOSITORY+'/'+path,
        headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],
                 'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(request,timeout=60) as response:return json.load(response)


def complete(sources,retained):
    subprocess.run(['git','merge-base','--is-ancestor',SOURCE,'HEAD'],check=True)
    previous=api('actions/runs/'+str(RUN))
    if previous['head_sha']!=SOURCE or previous['conclusion']!='failure':
        raise ValueError('Exact failed completion source required; never relabel it PASS')
    artifact=api('actions/artifacts/'+str(ARTIFACT))
    if artifact['digest']!='sha256:'+DIGEST or artifact['expired']:
        raise ValueError('Retained artifact identity differs')
    jobs=api('actions/runs/'+str(RUN)+'/jobs')['jobs']
    job=next(j for j in jobs if j['name']=='Exact signed407 first-party ownership and selected final regression inputs')
    steps={s['name']:s['conclusion'] for s in job['steps']}
    for name in ('Check original permanent signature and immutable baseline source/component inputs',
                 'Execute only the explicitly selected final correction host checks',
                 'Compile only the owned installer and prove exact protected DEX definitions'):
        if steps.get(name)!='success':raise ValueError('Required retained gate did not pass: '+name)
    failed=[s['name'] for s in job['steps'] if s['conclusion']=='failure']
    if failed!=['Authenticate internal module bundle with existing permanent signer and native verifier']:
        raise ValueError('An unrelated failure must not be resumed as a packaging-only correction')
    retained=retained.resolve()
    log=(retained/'SELECTED-HOST-RESULTS.txt').read_text()
    if list(map(int,re.findall(r'Ran (\d+) tests? in ',log)))!=[6,7,2] or log.count('\nOK\n')!=3:
        raise ValueError('Retained15test evidence differs')
    dex=retained/'module-dex';report=json.loads((dex/'DEX-MODULE-PRESERVATION.json').read_text())
    if (report['runtime_adapter_template_sha256']!=hashlib.sha256((ROOT/'InfinityInstalledModules.java.in').read_bytes()).hexdigest() or
        report['generated_java_sha256']!=hashlib.sha256(module_dex.source().encode()).hexdigest() or
        report['final_dex_sha256']!=hashlib.sha256((dex/'classes.dex').read_bytes()).hexdigest() or
        report['final_dex_sha256']!='d13ea18c00fff17d93d59732b3c4481fa2efcc40a4fd7366b459eeb32abf2b1a' or
        report['all_other_disassemblies_byte_identical'] is not True or
        report['original_string_pool_and_indices_identical'] is not True or
        report['Cobra_classes_changed']!=[]):
        raise ValueError('Runtime source, DEX or preservation binding changed; fresh checks required')
    result=sign_module_bundle.complete(sources,retained/'signed-modules')
    evidence={'previous_run':RUN,'previous_run_status':'FAIL_RETAINED','previous_source':SOURCE,
        'artifact_id':ARTIFACT,'artifact_sha256':DIGEST,'reused_host_checks':15,
        'reused_exact_DEX_audit':report,'only_corrected':'Absolute caller path; native absolute-path requirement preserved',
        'original_key_native_and_JCA_checks':'PASS_THIS_COMPLETION','private_key_access_this_completion':False,
        'Android17':'NOT RUN','physical_Fold':'NOT RUN','APK_produced':False}
    (retained/'COMPLETION-EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return {k:v for k,v in result.items() if k!='composition'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('sources',type=Path);parser.add_argument('retained',type=Path)
    args=parser.parse_args();print(json.dumps(complete(args.sources,args.retained),indent=2))
