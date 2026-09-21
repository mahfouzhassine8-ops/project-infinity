"""Local parser/source/guard checks only; never claim Android or device results."""
from pathlib import Path
import importlib.util
import json
import subprocess
import tempfile
import shutil
from contract import *
import ci

ROOT = Path(__file__).resolve().parent

def main():
    reviewed = ci.review()
    candidate = ROOT.parent / 'cobra-2103208-work'
    for name, digest in reviewed['parent_inventory'].items():
        expected = reviewed['files'].get(name, {}).get('after', digest)
        require(sha(candidate / name) == expected, 'Candidate drift after freeze: ' + name)
    parser = ROOT.parent / 'cobra-2103207-recipe/ParseJava.java'
    subprocess.run(['java', str(parser), str(candidate / SOURCE_ROOT)], check=True)
    subprocess.run(['java', str(parser), str(ROOT / 'tests')], check=True)
    subprocess.run(['python3', str(ROOT / 'test_guards.py')], check=True)
    ci.protect(candidate, ROOT.parent / 'cobra-ci-inputs/audit206/repairs/cobra-original-player-menu-2103197/apply.py')
    # Adapter is exercised against already-adapted 207 fixtures, not raw 206.
    parent_fixtures = ROOT.parent / 'cobra-207-delivery/evidence-1/audit207'
    with tempfile.TemporaryDirectory(prefix='cobra208-fixtures-') as temporary:
        folder = Path(temporary)
        for path in (parent_fixtures / 'repairs/cobra-final-features-2103205/tests').glob('*.java'):
            shutil.copy2(path, folder / path.name)
        shutil.copy2(parent_fixtures / 'repairs/cobra-feature-refinement-2103207/tests/Cobra2103207RefinementUiTest.java', folder / 'Cobra2103207RefinementUiTest.java')
        shutil.copy2(parent_fixtures / 'repairs/cobra-theme-runtime-2103160/tests/CobraVisualRuntimeTest.java', folder / 'CobraVisualRuntimeTest.java')
        adapted = ci.module('adapt208_check', ROOT / 'adapt_tests.py')
        adapted.adapt(folder, folder / 'supersessions.json')
        subprocess.run(['java', str(parser), str(folder)], check=True)
        try:
            adapted.adapt(folder, folder / 'second.json')
        except RuntimeError:
            pass
        else:
            raise RuntimeError('Adapter must reject changed source anchors')
    print('PASS local 208: reviewed patch/assets, all 49 protected members, Java syntax and negative payload guards. Android/device tests NOT run locally.')

if __name__ == '__main__':
    main()
