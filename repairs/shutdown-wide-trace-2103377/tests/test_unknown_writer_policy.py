"""Require cooperative-only unknown-writer policy without touching save authority."""
from pathlib import Path
import importlib.util,sys,unittest
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE));import extend_trace
PARENT=HERE.parent/'android-checkpoint-shutdown/runtime/native/overlay/xbmc/interfaces/generic/ScriptInvocationManager.cpp'
# The CI checkout has its preserved targeted module; local verification uses
# the same already-staged result before the new policy transform.
class PolicyTest(unittest.TestCase):
    def test_checkpoint_unknowns_do_not_reach_async_escalation(self):
        base=PARENT.read_text().replace('    const bool retired = InfinityScriptPersistence::TakeInterpreterRetirement(scriptId);',
          '    const bool retired = InfinityScriptPersistence::TakeInterpreterRetirement(scriptId);\n    InfinityVfsOpenTrace::Milestone(scriptId,"vfs.python.interpreter_retired",\n      retired?"durability_receipt_taken":"no_durability_receipt",true);')
        changed=extend_trace.extend('xbmc/interfaces/generic/ScriptInvocationManager.cpp',base)
        start=changed.index('void CScriptInvocationManager::PumpAndroidCheckpointRetirement(bool force)')
        end=changed.index('std::size_t CScriptInvocationManager::AndroidCheckpointEscalationsActive()',start)
        method=changed[start:end]
        protection=method.index('if (InfinityAndroidCheckpoint::IsActive())')
        guard_end=method.index('#endif',protection)
        self.assertIn('return;',method[protection:guard_end])
        self.assertLess(guard_end,method.index('item.thread->Stop(true)'))
        self.assertIn('CScriptInvocationManager::BeginAndroidCheckpoint()',changed)
        self.assertIn('invoker->Stop(false)',changed)
        self.assertIn('TakeInterpreterRetirement(scriptId)',changed)
        self.assertIn('RecordFailure(',changed)
        self.assertNotIn('SAFE_TO_TERMINATE',changed)
if __name__=='__main__':unittest.main()
