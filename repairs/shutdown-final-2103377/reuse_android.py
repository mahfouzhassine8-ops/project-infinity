#!/usr/bin/env python3
"""Reuse fresh 274-test Java only after exact current runtime reconstruction."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tarfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
TESTED_COMMIT='73da8981e7bd8c4e060a0dd7c095c29a88f0d47d'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(root):return {str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}

def verify(folder,green):
    folder=Path(folder)
    r=json.loads((folder/'ANDROID-VERIFICATION.json').read_text())
    assert r['source_commit']==TESTED_COMMIT
    assert r['totals']==dict(tests=274,failures=0,errors=0,skipped=0)
    for key in ['previous_234_case_names_preserved','previous_234_test_sources_unchanged',
                'new_test_matches','runtime_source_matches_candidate','compiled_java_inputs_match_candidate']:
        assert r[key]
    proof=json.loads((folder/'SOURCE-PRESERVATION.json').read_text())
    # The artifact folder transfer omits some ancillary source files by default.
    # Recover any missing bytes only from the original pinned full source tar,
    # requiring each original/compiled-map digest to match. Never weaken the map.
    archives=list(Path(green).rglob('tested-runtime-source.tar.gz'))
    assert len(archives)==1 and digest(archives[0])=='ba5a7c59659e4796c16358332b4fd99dcf84a8bde5ff71b291079b9afbcff9b3'
    recovered=[]
    with tarfile.open(archives[0]) as archive:
        for directory,key in [('green-source/source','before'),('source','after')]:
            for name,expected in proof[key].items():
                target=folder/directory/name
                if target.exists():continue
                assert name in proof['before'] and expected==proof['before'][name]
                data=archive.extractfile('source/'+name).read()
                assert hashlib.sha256(data).hexdigest()==expected
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                recovered.append(directory+'/'+name)
    assert snapshot(folder/'green-source/source')==proof['before']
    assert snapshot(folder/'source')==proof['after']
    module_path=ROOT/'repairs/shutdown-recents-2103377/lifecycle/apply_candidate.py'
    spec=importlib.util.spec_from_file_location('approved_android_delta',module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    copy=folder/'current-source-replay';assert not copy.exists()
    shutil.copytree(folder/'green-source/source',copy)
    current=module.apply_android(copy,proof['before'])
    assert current['after']==proof['after']==snapshot(copy)
    shutil.rmtree(copy)
    suites={};cases=set()
    for path in (folder/'junit').glob('TEST-*.xml'):
        tree=ET.parse(path).getroot()
        suites[tree.get('name')]={k:int(tree.get(k,0)) for k in ['tests','failures','errors','skipped']}
        for case in tree.findall('testcase'):
            key=(case.get('classname'),case.get('name'));assert key not in cases;cases.add(key)
    assert len(cases)==274 and suites==r['suites']
    donor=folder/'donor.apk';assert donor.is_file()
    receipt={'source_commit':os.environ['GITHUB_SHA'],'tested_source_commit':TESTED_COMMIT,
             'original_test_run':38415112606,'original_test_artifact':11824906073,
             'tests':274,'fresh_test_results_preserved':True,
             'runtime_source_byte_identical':True,'all_current_runtime_files_verified':len(proof['after']),
             'donor_sha256':digest(donor),'new_java_tests_claimed':False,
             'full_map_files_recovered_from_pinned_archive':len(recovered),
             'reason':'Native-only trace oracle repair; current Android delta reconstructs byte-identically to the freshly compiled/tested runtime.'}
    (folder/'ANDROID-REUSE-PROOF.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('PASS: 274 fresh results and donor preserved; complete current Android runtime reconstructed byte-identically. No repeat test run claimed.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--green',type=Path,required=True)
    a=p.parse_args();verify(a.folder,a.green)
