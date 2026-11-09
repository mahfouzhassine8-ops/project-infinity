"""Selected missing-case focus guards only; no RPC, provider or app execution."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import admit_tracking_android as guard

HERE = Path(__file__).resolve().parent

class FocusControls(unittest.TestCase):
    def setUp(self):
        self.selected = json.loads((HERE / 'TRACKING-ANDROID-REQUEST.json').read_bytes())

    def test_exact_retained_failed_av_is_accepted_as_failure_only(self):
        guard.checked_focus(self.selected)

    def test_arbitrary_focus_refused(self):
        self.selected['execution_focus'] = 'full-provider-replay'
        with self.assertRaisesRegex(RuntimeError, 'EXACT_MISSING_MOVIE_FOCUS_ONLY'):
            guard.checked_focus(self.selected)

    def test_replay_of_known_failed_tv_refused(self):
        self.selected['retained_actual_evidence']['replay_known_wrong_typed_tv'] = True
        with self.assertRaisesRegex(RuntimeError, 'RETAIN_ACTUAL_EPISODE_FAILURE'):
            guard.checked_focus(self.selected)

    def test_promoting_retained_failure_to_pass_refused(self):
        self.selected['retained_actual_evidence']['queens_blade_status'] = 'PASS'
        with self.assertRaisesRegex(RuntimeError, 'RETAIN_ACTUAL_EPISODE_FAILURE'):
            guard.checked_focus(self.selected)

    def test_absent_real_av_refused(self):
        actual = guard.load(HERE / guard.RETAINED_DIR / 'queens-blade-e4-actual-av.json')
        actual['events'] = []
        with patch.object(guard, 'load', return_value=actual):
            with self.assertRaisesRegex(RuntimeError, 'ACTUAL_RETAINED_AV_IS_PLAYABLE'):
                guard.checked_focus(self.selected)

    def test_different_typed_evidence_cannot_replace_failed_input(self):
        actual = copy.deepcopy(guard.load(HERE / guard.RETAINED_DIR / 'queens-blade-e4-actual-av.json'))
        actual['item'].update(media_type='episode', season=1, episode=4)
        with patch.object(guard, 'load', return_value=actual):
            with self.assertRaisesRegex(RuntimeError, 'ACTUAL_RETAINED_AV_IS_PLAYABLE'):
                guard.checked_focus(self.selected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
