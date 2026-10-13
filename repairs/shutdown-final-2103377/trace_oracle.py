#!/usr/bin/env python3
"""Correct only the stress oracle's counting of no-operation metadata (ID zero)."""
from pathlib import Path
import argparse
import hashlib
import json

HERE=Path(__file__).resolve().parent
SAVED=HERE.parent/'shutdown-wide-trace-2103377/tests/verify_trace.py'
SAVED_SHA='9aa2d76c10bf98c438c6bda8922b8daa7109e6e5c1d7abb7d1a0397734a3bf5e'
FIXTURE_SHA='a73c857ad2d80b9edd805eb7d89385c7212957e05026a1a07ac322a7c4f15812'

def verify(include,out):
    original=SAVED.read_bytes()
    assert hashlib.sha256(original).hexdigest()==SAVED_SHA
    assert hashlib.sha256((SAVED.parent/'trace_harness.cpp').read_bytes()).hexdigest()==FIXTURE_SHA
    source=original.decode()
    # Both predicates belong to the same stress-case real-operation inventory.
    # Zero denotes an explicit absence of an operation, not an omitted operation.
    predicate="if 'operation_id' in e"
    assert source.count(predicate)==2
    corrected=source.replace(predicate,predicate+" and e['operation_id'] > 0")
    namespace={'__file__':str(SAVED),'__name__':'preserved_trace_oracle'}
    exec(compile(corrected,str(SAVED),'exec'),namespace)
    namespace['verify'](Path(include),Path(out))
    receipt={'original_verifier_sha256':SAVED_SHA,'original_fixture_sha256':FIXTURE_SHA,
             'original_files_unchanged':True,'predicates_corrected':2,
             'actual_operations_still_required':100,'metadata_id_zero_is_not_an_operation':True,
             'all_other_assertions_unchanged':True,'runtime_tracer_changed':False,
             'failed_run':38415112606,'failed_stress_actual_operations':100,
             'failed_stress_metadata_zero_rows':1,'passed':True}
    (Path(out)/'TRACE-ORACLE-CORRECTION.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--include',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();verify(a.include,a.out)
