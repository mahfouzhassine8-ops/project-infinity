"""Independent background starts survive foreground-only retirement."""
import json
from pathlib import Path
import unittest
from test_task_ownership import loading, context, begin

class CancelOwnership(unittest.TestCase):
    def test_foreground_cancel_keeps_delayed_same_profile_background(self):
        state=loading.LoadingState();ctx=context()
        state.event(dict(begin('a',ctx,1),foreground=True),1,ctx)
        changed=context(window=10025)
        state.tick(2,changed)
        state.event(begin('b',ctx,.5),2.1,changed)
        self.assertIn('b'*32,state.jobs)
        self.assertEqual(state.tick(2.2,changed)['Global'],'true')
        # The same older foreground start must still be rejected, even after
        # returning to an identical screen/control. No provider is re-executed.
        state.event(dict(begin('c',ctx,.7),foreground=True),2.3,ctx)
        self.assertIsNone(state.action)
        state.event(dict(token='b'*32,state='ready'),2.4,changed)
        self.assertEqual(state.tick(2.5,changed)['Global'],'false')

if __name__=='__main__':
    scope=json.loads((Path(__file__).resolve().parents[1]/'SCOPE.json').read_text())
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([CancelOwnership(scope['selected_cancellation_test'])]))
    raise SystemExit(not result.wasSuccessful())
