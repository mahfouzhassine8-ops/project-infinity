"""Run unchanged legacy tests against the packaged helper, with current UI peers."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys,tempfile,unittest
from unittest.mock import Mock

def verify(tests_root,helper,out):
    out.mkdir(parents=True,exist_ok=True)
    before={str(p.relative_to(tests_root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (tests_root/'tests').glob('*.py')}
    with tempfile.TemporaryDirectory(prefix='infinity-candidate-regression-') as directory:
        root=Path(directory);shutil.copytree(tests_root/'tests',root/'tests')
        target=root/'addons/script.infinity.rails';target.parent.mkdir(parents=True)
        shutil.copytree(helper,target,ignore=shutil.ignore_patterns('__pycache__'))
        sys.path.insert(0,str(root/'tests'))
        import test_runtime_rc5
        runtime=test_runtime_rc5.runtime
        original=test_runtime_rc5.RuntimeTests.setUp
        def setup(test):
            original(test)
            # Real Kodi has this type; the legacy fake omitted it. Its .221
            # skin fixture intentionally exercises the protected chooser fallback.
            test.gui.WindowXMLDialog=type('WindowXMLDialog',(),{})
            select=test.gui.Dialog.select
            def current_dialog(obj,*args,**kwargs):
                # Keep the legacy injected dialog failure at the equivalent
                # Kodi chooser boundary used by approved Mocha helper .025.
                if isinstance(runtime.select,Mock):return runtime.select(*args,**kwargs)
                return select(obj,*args,**kwargs)
            test.gui.Dialog.select=current_dialog
        test_runtime_rc5.RuntimeTests.setUp=setup
        try:
            suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_*.py')
            with (out/'CANDIDATE-HELPER-101-TESTS.txt').open('w') as stream:
                result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        finally:test_runtime_rc5.RuntimeTests.setUp=original
    after={str(p.relative_to(tests_root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (tests_root/'tests').glob('*.py')}
    assert before==after
    receipt=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        passed=result.wasSuccessful(),original_test_sources_identical=True,
        current_candidate_helper_tested=True,legacy_ui_peer_adapter=True,
        ui_scope='Legacy .221 fallback fixture; actual Mocha rendering and Android hold require Fold acceptance')
    (out/'CANDIDATE-HELPER-REGRESSIONS.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert result.testsRun==101 and result.wasSuccessful(),receipt
    print(json.dumps(receipt))

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    for name in ['tests-root','helper','out']:cli.add_argument('--'+name,type=Path,required=True)
    args=cli.parse_args();verify(args.tests_root,args.helper,args.out)
