"""Rerun the original durability suite against the exact candidate module."""
from pathlib import Path
import importlib.util,sys,unittest,json,os
import components101 as c
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage/c.CC))
import persistence_participant
c.require(Path(persistence_participant.__file__).resolve()==stage/c.CC/'persistence_participant.py','wrong tested participant')
path=c.HERE/'test_persistence101_fixture.py'
spec=importlib.util.spec_from_file_location('test_persistence101_fixture',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
 Path(os.environ.get('INFINITY_101_PERSISTENCE','PERSISTENCE-RESULTS.json')).write_text(json.dumps(dict(passed=result.wasSuccessful(),tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),tested_source_sha256=c.digest(stage/c.CC/'persistence_participant.py'),physical_fold_verified=False),indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
