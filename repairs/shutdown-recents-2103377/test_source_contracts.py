#!/usr/bin/env python3
"""Static preservation checks for proposed close/Recents candidate. Not a device test."""
import hashlib
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
PREFIX = Path("repairs/android-checkpoint-shutdown/runtime/android/overlay/tools/android/packaging/xbmc/src")
PIN = "808b4acc4d1a6aa1cbc8bc4a1848de88b81103e6"
FILES = {
    "InfinityCloseNativeLease.java.in": ("2db2bcb9a94bb42c594e691cda7deb38b2dbf9afd4c90160a173c7c832cfeec2", "21965ee188ff7b3d28ec223be7a794eb9251067ecaa567bc93ba450c87df71c6"),
    "InfinityCloseGuardService.java.in": ("4c42e3be884e6cea27ddee9c094ca379f408367e9c5d6bfb788a8ccd4fec5050", "790209e1d00f106e8f054fcdaf3dc92f28acc59199ffa42eb6bb6aaca28b79a0"),
}

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def original(name):
    return subprocess.check_output(["git", "show", PIN + ":" + (PREFIX / name).as_posix()], cwd=ROOT).decode()

def span(content, a, b):
    return content[content.index(a):content.index(b, content.index(a))]

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guard=(ROOT / PREFIX / "InfinityCloseGuardService.java.in").read_text()
        cls.lease=(ROOT / PREFIX / "InfinityCloseNativeLease.java.in").read_text()

    def test_pinned_source_and_candidate_identity(self):
        for name, (before, after) in FILES.items():
            self.assertEqual(digest(original(name)), before)
            self.assertEqual(digest((ROOT / PREFIX / name).read_text()), after)

    def test_exact_task_identity_not_global_recents(self):
        self.assertIn('TASK_ID="close_task_id"', self.lease)
        self.assertIn('.putExtra(TASK_ID,owner.getTaskId())', self.lease)
        self.assertIn('started==other.started&&taskId==other.taskId',self.guard)
        task=span(self.guard,'private String retireConfirmedClosedKodiTask','static Intent homeIntent()')
        for required in ('"COMPLETE".equals(phase)', 'checkpointSaved', 'consumed', 'revoked',
                         'session != completed', 'completed.taskId < 0',
                         'observed.pid != completed.pid', '!completed.owner.equals(observed.owner)',
                         'info.taskId!=completed.taskId',
                         '!getPackageName().equals(root.getPackageName())',
                         '!Main.class.getName().equals(root.getClassName())',
                         'return "replacement_engine_observed"', 'return "task_root_mismatch"',
                         'task.finishAndRemoveTask()'):
            self.assertIn(required,task)
        self.assertEqual(self.guard.count('task.finishAndRemoveTask()'),1)

    def test_only_after_durable_completed_close(self):
        path=span(self.guard,'private void checkOwner()','private void deadline()')
        self.assertIn('if(checkpointSaved&&consumed&&!revoked&&"ENGINE_TERMINATING".equals(phase))',path)
        self.assertIn('InfinityCheckpointProtocol.confirmedComplete(done,target.ticket,target.owner,target.pid,false,true)',path)
        self.assertLess(path.index('InfinityCheckpointProtocol.atomic(new File(getFilesDir(),InfinityCheckpointProtocol.RECEIPT),done)'),path.index('retireConfirmedClosedKodiTask(target)'))
        self.assertLess(path.index('phase="COMPLETE"'),path.index('retireConfirmedClosedKodiTask(target)'))
        self.assertNotIn('retireConfirmedClosedKodiTask',span(self.guard,'private void fail(String reason)','private void evidence('))

    def test_lease_is_exactly_two_narrow_edits(self):
        old=original("InfinityCloseNativeLease.java.in")
        new=self.lease.replace(',TASK_ID="close_task_id"', '').replace(
            '.putExtra(PID,android.os.Process.myPid()).putExtra(TOKEN,InfinityKodiShutdown.localOwnerToken())\n        .putExtra(START,started).putExtra(TASK_ID,owner.getTaskId());',
            '.putExtra(PID,android.os.Process.myPid()).putExtra(TOKEN,InfinityKodiShutdown.localOwnerToken()).putExtra(START,started);')
        self.assertEqual(new,old)

    def test_baseline_safety_primitives_preserved(self):
        self.assertIn('if(!gate.arm(generation,safeProof,SystemClock.elapsedRealtime()))',self.guard)
        self.assertIn('evidence("navigation.deferred_until_confirmed_death"',self.guard)
        self.assertIn('if(!InfinityCheckpointProtocol.confirmedComplete(',self.guard)
        self.assertIn('catch(IOException unavailable)',self.guard)

    def test_only_two_existing_source_files_changed(self):
        changed=subprocess.check_output(["git","diff","--name-only",PIN,"HEAD"],cwd=ROOT,text=True).splitlines()
        original_sources={p for p in changed if p.startswith('repairs/android-checkpoint-shutdown/runtime/') }
        self.assertEqual(original_sources,{str(PREFIX / name) for name in FILES})
        self.assertFalse(any(p.startswith("addons/") or p.startswith("repairs/skin-211") or "playlistbrowser" in p.lower() for p in changed))

    def test_observation_and_android_api_failure_paths_are_guarded(self):
        task=span(self.guard,'private String retireConfirmedClosedKodiTask','static Intent homeIntent()')
        for required in ('observed.pid <= 0', 'observed.alive', 'latest.pid<=0', 'latest.alive',
                         'Build.VERSION.SDK_INT>=29', 'info.persistentId!=completed.taskId',
                         'Build.VERSION.SDK_INT>=23', 'completion_authority_changed'):
            self.assertIn(required,task)
        self.assertEqual(task.count('InfinityKodiShutdown.read('),2)
        self.assertEqual(task.count('InfinityKodiShutdown.ownerRetired('),2)
        self.assertLess(task.index('task.getTaskInfo()'),task.index('Snapshot latest='))
        self.assertLess(task.index('Snapshot latest='),task.index('task.finishAndRemoveTask()'))

    def test_saved_coordinator_outside_task_retirement_is_byte_preserved(self):
        saved=subprocess.check_output(['git','show','c727f3964419ec0010b6bf0e9e620c5605980d44:'+(PREFIX/'InfinityCloseGuardService.java.in').as_posix()],cwd=ROOT,text=True)
        start,end='private String retireConfirmedClosedKodiTask','static Intent homeIntent()'
        self.assertEqual(self.guard.replace(span(self.guard,start,end),''),saved.replace(span(saved,start,end),''))

if __name__ == "__main__":
    unittest.main(verbosity=2)
