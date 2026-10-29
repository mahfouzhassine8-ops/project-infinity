"""Selected P0 before/after checks, never app/shutdown or unrelated suites.

The signed29 interaction case must genuinely FAIL at its final route assertion,
not fail from a fixture/translation error. Its raw failed JUnit record remains.
The final candidate must then pass the identical case and focused regressions.
"""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

BUTTON = 'CobraPlayerButtonDispatchTest'
BEFORE = 'initialProEntryActualVisualButtonsHaveSeparateActions'
ADJACENT = ('moreMovesOnlyItselfAndProOrderRestoresOnRetainedPreview+'
            'actualPreviewReuseKeepsCallbacksAndRestoresProOrder+'
            'existingProSportsAndOtherModeStripsKeepTheirExactOrder')


def execute(folder, selector):
    result = subprocess.run(['mvn', '-B', '-q', '-f', str(folder/'pom.xml'),
                             '-Dtest='+selector, 'test'], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (folder/'TEST-OUTPUT.txt').write_text(result.stdout)
    print(result.stdout, end='')
    return result.returncode


def main(candidate, previous):
    before = execute(previous, BUTTON+'#'+BEFORE)
    report = previous/'target/surefire-reports'/('TEST-com.projectinfinity.kodi.'+BUTTON+'.xml')
    suite = ET.parse(report).getroot()
    assert before != 0 and suite.get('tests') == '1' and suite.get('failures') == '1' and suite.get('errors') == '0', 'Expected original route assertion failure, never a fixture error'
    assert suite.find('testcase').get('name') == BEFORE
    assert 'COBRA_VISUAL_BUTTON_ROUTES [pip, pip, fullscreen]' in (previous/'TEST-OUTPUT.txt').read_text(), 'Exact physical-reported wrong routes were not reproduced'
    assert 'expected:' in suite.find('testcase/failure').get('message','')
    after = execute(candidate, BUTTON+',CobraArrangeIntegrationTest#'+ADJACENT)
    assert after == 0, 'Candidate focused interaction/regression failure'
    assert 'COBRA_VISUAL_BUTTON_ROUTES [fullscreen, pip, more]' in (candidate/'TEST-OUTPUT.txt').read_text(), 'Candidate correct routes not observed'
    summary = {'status':'PASS_SELECTED_P0_BEFORE_AFTER',
               'before':'SIGNED29_REAL_VIEW_DISPATCH_ASSERTION_FAIL_EXPECTED; [pip,pip,fullscreen]',
               'after':'CANDIDATE_REAL_VIEW_DISPATCH_PASS; [fullscreen,pip,more]',
               'candidate_selection':BUTTON+',CobraArrangeIntegrationTest#'+ADJACENT,
               'physical_Fold':'NOT_RUN', 'shutdown':'NOT_RUN',
               'terminal_boundaries':'Fullscreen/menu/platform PiP are explicitly recorded host spies; native buttons/scroll/touch/dispatcher run'}
    (candidate/'FOLLOWUP-RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--previous',type=Path,required=True)
    main(**vars(p.parse_args()))
