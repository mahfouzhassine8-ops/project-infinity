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
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'repairs/essential-first-2103377/package_signed_fold_test.py'
NATIVE='04f9fb1b60d63a4579253cb2e58113b273dadfcc'

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('java','verify-java','package'))
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
        baseline=args.source/'tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in'
        candidate=ROOT/'repairs/essential-first-2103377/runtime/android/tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in'
        expected=candidate.read_text()
        # The only guard delta is truthful essential-first diagnostic fields.
        # Preserve the locked entry/removal lease and advisory notice exactly.
        for field in ('exit_policy','process_death_confirmed','exit_kind','optional_data_recovery_guaranteed'):
            expected,count=re.subn(r'(?m)^      row\.put\("'+field+r'"[^\n]*\n','',expected)
            assert count==1,field
        assert expected==baseline.read_text(),'Guard no longer preserves the exact approved Android source'
        factory.prepared_java(args)
        with (args.gradle_dir/'xbmc/build.gradle').open('a') as stream:
            stream.write("\nconfigurations { preservationTools }\ndependencies { preservationTools 'org.smali:baksmali:2.5.2' }\ntasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }\n")
    else:
        assert args.donor and args.gradle_dir
        args.out.mkdir(parents=True,exist_ok=True)
        # Source/class inventories alone cannot establish that unrelated Java
        # behaviour survived rebuilding an older complete donor source export.
        # Reuse the repository's decoded-instruction preservation gate with
        # only the two authorized shutdown class families exempted.
        spec=importlib.util.spec_from_file_location('essential_dex_guard',ROOT/'repairs/cobra-clean-restart/bytecode_guard.py')
        guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
        guard.ALLOWED=re.compile(r'com/projectinfinity/kodi/(?:InfinityCheckpointProtocol|InfinityCloseGuardService)(?:\$[^/]*)?\.smali$')
        normalize=guard.normalize
        guard.normalize=lambda text: normalize(re.sub(r'(?m)^\s*\.line \d+\s*$', '', text))
        guard.compare(args.parent,args.donor,(args.gradle_dir/'preservation-classpath.txt').read_text(),args.out)
        if args.mode=='verify-java': return
        assert args.native and args.android
        factory.signed_package(args)
        old=args.out/'Infinity-2103377-Essential-First-Signed-Fold-TEST1.apk'
        final=args.out/'Infinity-2103377-Essential-First-Internal-Probe.apk'
        old.rename(final)
        receipt=args.out/'ESSENTIAL-FIRST-SIGNED-TEST-PRESERVATION.json'
        row=json.loads(receipt.read_text())
        row.update(status='INTERNAL ANDROID RUNTIME PROBE; NOT FOR DELIVERY; NOT LOCKED',file=final.name,
                   native_host_cases=51,apk_deliverable=False,physical_device_acceptance_required=True)
        # These legacy TEST1 limitations predate this exact native build.
        # Replace them with explicit current verification boundaries.
        row.pop('known_fail_closed_native_encoder_route',None)
        row.pop('unverified_other_native_descriptor_aliases',None)
        row['runtime_boundary']='Host write-path checks passed; Android process/reopen probe has not yet run.'
        receipt.write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
        (args.out/'SHA256SUMS').write_text(row['apk_sha256']+'  '+final.name+'\n')
        (args.out/'TEST-LIMITATIONS.md').write_text('Internal emulator probe only. No Fold delivery or lock is authorized by this package. Actual engine death, whole-package death and data-preserving reopening must be observed separately.\n')

if __name__=='__main__':main()
