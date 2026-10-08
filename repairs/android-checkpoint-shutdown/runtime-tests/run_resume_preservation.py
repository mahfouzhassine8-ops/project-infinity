"""Run the original 2103292 behavioral suite against the actual candidate modules."""
import argparse
from pathlib import Path
import sys
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', required=True)
arguments = parser.parse_args()
runtime = Path(arguments.runtime).resolve(strict=True)
baseline = Path(__file__).resolve().parents[2] / 'resume-hub-2103292/src/test_resume_hub2.py'
source = baseline.read_text()
source = source.replace("ROOT=Path('/mnt/data/resumehub/work/script.infinity.commandcenter')",
                        'ROOT=Path(' + repr(str(runtime)) + ')')
# The original suite did not need Monitor; the resident checkpoint now defines a
# real Monitor subclass at import. Only add that absent Kodi API double.
source = source.replace('xbmc.log=lambda *a,**k: None',
                        "xbmc.Monitor=type('Monitor', (), {})\nxbmc.log=lambda *a,**k: None")
namespace = {'__name__': 'original_resume_preservation', '__file__': str(baseline)}
exec(compile(source, str(baseline), 'exec'), namespace)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['ResumeHub2Tests'])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
