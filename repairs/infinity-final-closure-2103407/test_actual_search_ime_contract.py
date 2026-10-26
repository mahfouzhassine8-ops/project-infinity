import ast
import inspect
from pathlib import Path
from unittest import TestCase,main
import android17_candidate_probe as candidate
import android_input_readiness as readiness


class ActualSearchIMEContractTests(TestCase):
    def test_actual_app_keyboard_proof_and_original_deadline_remain(self):
        install=inspect.getsource(candidate.install_over)
        self.assertNotIn('android_input_preparation',install)
        self.assertIn("status='NOT RUN'",install)
        driver=(candidate.OLD/'universal/android_search_input.py').read_text()
        waits=[n for n in ast.walk(ast.parse(driver)) if isinstance(n,ast.Call) and
               isinstance(n.func,ast.Attribute) and n.func.attr=='until' and n.args and
               isinstance(n.args[0],ast.Name) and n.args[0].id=='keyboard']
        self.assertEqual(len(waits),1)
        self.assertEqual(ast.literal_eval(waits[0].args[1]),45)
        self.assertIn('_candidate_ime_ready',readiness.DRIVER_AFTER)
        probe=Path(candidate.__file__).read_text()
        self.assertIn('android_input_readiness.instrument(driver',probe)


if __name__=='__main__':main(verbosity=2)
