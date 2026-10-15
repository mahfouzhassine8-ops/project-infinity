#!/usr/bin/env python3
"""Reuse the signed-test factory for an internal, non-deliverable Android probe.

The pinned native source is compiled by the full production workflow. This
driver changes only the reviewed build identity; it cannot relax preservation,
ABI, resource, source or permanent signing checks in the existing factory.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'repairs/essential-first-2103377/package_signed_fold_test.py'
NATIVE='f8be4d05e474ca425074d7e1bb5d49f624015d37'

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('java','package'))
    for name in ('parent','source','gradle-dir','donor','native','android','out'):
        p.add_argument('--'+name,type=Path,required=name in ('parent','out'))
    args=p.parse_args()
    subprocess.run(['git','diff','--exit-code',NATIVE,'--',
        'repairs/essential-first-2103377/runtime','repairs/essential-first-2103377/apply_runtime.py',
        'repairs/essential-first-2103377/stage_experiment.py'],cwd=ROOT,check=True)
    spec=importlib.util.spec_from_file_location('essential_signed_factory',SOURCE)
    factory=importlib.util.module_from_spec(spec);sys.modules[spec.name]=factory;spec.loader.exec_module(factory)
    factory.PINNED_NATIVE_COMMIT=NATIVE
    factory.NEW_NAME='1.0.9-Essential-First-PROBE-RC01'
    assert len(factory.NEW_NAME)==len(factory.OLD_NAME)
    if args.mode=='java':
        assert args.source and args.gradle_dir
        factory.prepared_java(args)
    else:
        assert args.native and args.donor and args.android
        args.out.mkdir(parents=True,exist_ok=True)
        factory.signed_package(args)
        old=args.out/'Infinity-2103377-Essential-First-Signed-Fold-TEST1.apk'
        final=args.out/'Infinity-2103377-Essential-First-Internal-Probe.apk'
        old.rename(final)
        receipt=args.out/'ESSENTIAL-FIRST-SIGNED-TEST-PRESERVATION.json'
        row=json.loads(receipt.read_text())
        row.update(status='INTERNAL ANDROID RUNTIME PROBE; NOT FOR DELIVERY; NOT LOCKED',file=final.name,
                   native_host_cases=34,apk_deliverable=False,physical_device_acceptance_required=True)
        # These legacy TEST1 limitations predate this exact native build.
        # Replace them with explicit current verification boundaries.
        row.pop('known_fail_closed_native_encoder_route',None)
        row.pop('unverified_other_native_descriptor_aliases',None)
        row['runtime_boundary']='Host write-path checks passed; Android process/reopen probe has not yet run.'
        receipt.write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
        (args.out/'SHA256SUMS').write_text(row['apk_sha256']+'  '+final.name+'\n')
        (args.out/'TEST-LIMITATIONS.md').write_text('Internal emulator probe only. No Fold delivery or lock is authorized by this package. Actual engine death, whole-package death and data-preserving reopening must be observed separately.\n')

if __name__=='__main__':main()
