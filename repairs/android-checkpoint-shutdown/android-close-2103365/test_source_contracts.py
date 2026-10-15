#!/usr/bin/env python3
"""2103365 Android Close handoff contracts (source-level, not device acceptance)."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "runtime/android/overlay/tools/android/packaging/xbmc/src"


class AndroidCloseHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (SRC / "Main.java.in").read_text()
        cls.guard = (SRC / "InfinityCloseGuardService.java.in").read_text()

    def test_native_activity_not_redirected_during_checkpoint(self):
        resume = self.main[self.main.index("  public void onResume()"):]
        start = resume.index("if(mInfinityExitPlan.pending())")
        owner = resume.index("if(mInfinityExitPlan.checkpointPending())", start)
        chooser = resume.index('startActivity(new Intent(this,Splash.class)', start)
        recents = resume.index("infinitySetCurrentTaskExcludedFromRecents(true)", start)
        self.assertLess(start, owner)
        self.assertLess(owner, recents)
        self.assertLess(owner, chooser)
        self.assertIn("return;", resume[owner:recents])
        self.assertIn("resumedDuringSave.ownerRetained", resume[owner:recents])

    def test_close_does_not_leave_kodi_while_saving(self):
        start = self.guard.index("  @Override public int onStartCommand(")
        end = self.guard.index("  static Intent homeIntent()", start)
        during = self.guard[start:end]
        self.assertNotIn("startActivity(homeIntent())", during)
        self.assertIn("navigation.deferred_until_confirmed_death", during)
        self.assertIn("bindService(", during)
        self.assertIn('transition("QUIESCE","")', during)
        self.assertIn("ui.post(poll)", during)

    def test_home_requires_persisted_complete_and_process_death(self):
        start = self.guard.index("  private void checkOwner()")
        end = self.guard.index("  private void deadline()", start)
        finish = self.guard[start:end]
        self.assertEqual(finish.count("startActivity(homeIntent())"), 1)
        home = finish.index("startActivity(homeIntent())")
        for token in (
            'if(checkpointSaved&&consumed&&!revoked&&"ENGINE_TERMINATING".equals(phase))',
            'if(completing)return',
            "InfinityCheckpointProtocol.confirmedComplete(",
            "InfinityCheckpointProtocol.atomic(",
            'phase="COMPLETE"',
        ):
            self.assertLess(finish.index(token), home, token)
        self.assertIn('fail("completion_receipt_commit_failed")', finish)
        self.assertIn("if(ended||session!=target)return", finish)

    def test_failure_remains_fail_closed(self):
        for token in ("gate.consume(", 'fail("checkpoint_deadline_exceeded")',
                      'fail("engine_ended_without_consumed_termination_authorization")',
                      'fail("invalid_completion_evidence")',
                      "stopForeground(true)", "checkpointSaved=true"):
            self.assertIn(token, self.guard)
        self.assertIn('if(owner.isDestroyed()', "if(owner.isDestroyed()")
        self.assertIn("super.onDestroy()", self.main)

    def test_only_two_android_source_postimages_changed(self):
        manifest = json.loads((ROOT / "runtime/android/manifest.json").read_text())
        for name in ("Main.java.in", "InfinityCloseGuardService.java.in"):
            path = "tools/android/packaging/xbmc/src/" + name
            self.assertIn(path, manifest["changed"])
            self.assertEqual(
                hashlib.sha256((SRC / name).read_bytes()).hexdigest(),
                manifest["after"][path],
            )
        self.assertFalse(manifest["deleted"])

    def test_resume_and_identity_preserved(self):
        package = Path("tools/checkpoint-apk/package.py").read_text()
        self.assertIn("VERSION = 2103365", package)
        self.assertIn("1.0.9-Android-Close-RC1", package)
        for name in ("plugin.py", "resume_hub.py", "service.py"):
            self.assertTrue((ROOT / "runtime/commandcenter/overlay" / name).is_file())
        self.assertIn("REQUIRED_OWNER_NAMES", (SRC / "InfinityCheckpointProtocol.java.in").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
