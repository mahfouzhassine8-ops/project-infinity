"""Static/test-transport checks only for the new authorized tracking choices."""
import ast,importlib.util,json,re,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPAIR=HERE.parent;ROOT=REPAIR.parents[1]
CASES={'tracking-recovery','tracking-actions','tracking-continue'}
class Routing(unittest.TestCase):
    def test_workflow_and_probe_explicit_choices(self):
        text=(ROOT/'.github/workflows/infinity-saved-navigation-android.yml').read_text()
        self.assertIn('workflow_dispatch:',text);self.assertNotIn('workflow_run:',text)
        for name in CASES:self.assertIn(name,text)
        tree=ast.parse((REPAIR/'android_feature_probe.py').read_text())
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CASES' for t in n.targets))
        self.assertLessEqual(CASES,set(ast.literal_eval(assignment.value)))
    def test_new_service_calls_only_selected_tracking_driver(self):
        tree=ast.parse((HERE/'android_tracking_checks.py').read_text())
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='ui'}
        self.assertLessEqual(calls,{'require','until','select_native_item','gui_snapshot','rpc','folder','complete_first_use','first_provider_home','verify_open_folder','verify_favorites_reference'})
        self.assertNotIn('run',calls)
        text=(HERE/'android_tracking_checks.py').read_text()
        for token in ('Application.Quit','CLOSE_KODI','force-stop','System.Shutdown','Powerdown(','Quit(','pm clear','pm uninstall'):
            self.assertNotIn(token,text)
        self.assertIn("ui.require(mode in CASES",text)
    def test_transport_still_rejects_shutdown_and_reset_commands(self):
        spec=importlib.util.spec_from_file_location('selected_feature_device',REPAIR/'android_feature_device.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for command in ('Application.Quit','CLOSE_KODI','am force-stop package','pm clear package','pm uninstall package','Powerdown()'):
            with self.assertRaises(RuntimeError):m.guard([command])
        m.guard(['shell','am','start','-W','-n','com.projectinfinity.kodi/.Splash'])
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Routing))
    (HERE/'FEATURE-ROUTING-HOST.json').write_text(json.dumps(dict(host='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,scope='new tracking case routing and forbidden-command guards only',application_execution='NOT RUN',shutdown='NOT RUN'),indent=2)+'\n')
    raise SystemExit(not r.wasSuccessful())
