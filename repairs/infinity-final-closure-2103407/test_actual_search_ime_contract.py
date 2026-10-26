import ast
import inspect
from pathlib import Path
from unittest import TestCase,main
import android17_candidate_probe as candidate
import android_input_readiness as readiness
import sys
from types import SimpleNamespace
from unittest.mock import patch


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

    def test_stress_requires_current_IME_before_expensive_hierarchy_and_retains_deadline(self):
        raw=Path(candidate.__file__).with_name('android17_stress.py').read_text()
        tree=ast.parse(raw)
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='typing_keyboard')
        events=[];state={'ready':False,'keyboard':None}
        def ready(*args):events.append('actual IME');return state['ready']
        def keyboard():events.append('real hierarchy');return state['keyboard']
        scope=dict(device=object(),out=object(),keyboard=keyboard)
        with patch.dict(sys.modules,{'android_input_readiness':SimpleNamespace(ready=ready)}):
            exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-stress','exec'),scope)
            self.assertIsNone(scope['typing_keyboard']());self.assertEqual(events,['actual IME'])
            state['ready']=True;events.clear()
            self.assertIsNone(scope['typing_keyboard']());self.assertEqual(events,['actual IME','real hierarchy'])
            state['keyboard']=(['actual rows'],'actual EditText')
            self.assertIs(scope['typing_keyboard'](),state['keyboard'])
        waits=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and n.func.attr=='until' and n.args and isinstance(n.args[0],ast.Name) and n.args[0].id=='typing_keyboard']
        self.assertEqual(len(waits),1);self.assertEqual(ast.literal_eval(waits[0].args[1]),45)


if __name__=='__main__':main(verbosity=2)
