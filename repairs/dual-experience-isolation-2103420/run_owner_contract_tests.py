import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from inventory import HERE, ROOT, digest, save
from prepare_runtime import wiring

CASES=('independent_state','pending_cobra_write','pending_shell_write','failed_durability',
       'accepted_continuation','late_write_revokes_receipt','wrong_receipt',
       'retained_cobra_keeps_writing','new_cobra_entry_revokes_kill','begin_is_atomic',
       'all_locks_held_during_callback','cancel_and_reentry',
       'retained_coordinator_can_close_again','retained_failure_not_erased','overlapping_cobra_leases')


def run(out):
    original=ROOT/'repairs/essential-first-2103377/runtime/android/tools/android/packaging/xbmc/src/InfinityJavaWriteBarrier.java.in'
    source=original.read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi')
    accessors='''
  public static Object ownerLock(){return LOCK;}
  public static boolean canBegin(String ticket){return !closing||session.equals(ticket);}
'''
    source=source[:source.rindex('}')]+accessors+'}\n'
    with tempfile.TemporaryDirectory(prefix='infinity-owner-contract-') as tmp:
        root=Path(tmp);java=root/'java';java.mkdir();classes=root/'classes';classes.mkdir()
        for owner in ('Infinity','Cobra','Shell'):
            (java/(owner+'JavaWriteBarrier.java')).write_text(source.replace('InfinityJavaWriteBarrier',owner+'JavaWriteBarrier'))
        for name in ('CombinedDurability.java','CobraRuntimeLease.java'):
            shutil.copyfile(HERE/'runtime'/name,java/name)
        shutil.copyfile(HERE/'tests/OwnerDurabilityTest.java',java/'OwnerDurabilityTest.java')
        (java/'OwnerDurabilityWiring.java').write_text(wiring())
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:all,-try,-options','-d',str(classes),*map(str,sorted(java.glob('*.java')))],check=True)
        for case in CASES:
            subprocess.run(['java','-cp',str(classes),'com.projectinfinity.kodi.OwnerDurabilityTest',case],check=True,timeout=30)
    report={'status':'PASS_OWNER_DURABILITY_CONTRACT','cases':list(CASES),
            'unchanged_barrier_source_sha256':digest(original.read_bytes()),
            'combined_source_sha256':digest((HERE/'runtime/CombinedDurability.java').read_bytes()),
            'application_executed':False,'termination_callback':'assertions_only_no_process_termination',
            'test_authority':'SCOPED-CORRECTION-TESTS.json'}
    save(out,report)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True,type=Path)
    run(**vars(parser.parse_args()))
