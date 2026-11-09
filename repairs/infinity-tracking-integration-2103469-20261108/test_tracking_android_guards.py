"""Selected source/routing/RPC refusal controls; never launches an application."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import admit_tracking_android as admission
import verify_tracking_android as feature


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    rows = []
    request = admission.load(admission.REQUEST)
    admission.checked_request()
    admission.workflow_shape()
    rows.append(dict(case='actual19bindings_unchanged_reviewed_source40evidence_and_old_workflow_bodies', status='PASS_HOST_SOURCE_GUARD_ONLY'))
    original_load = admission.load
    for case, reason in [('missing_binding', 'EXACT_SELECTED_INPUT_BINDING_SET'),
            ('changed_binding', 'FROZEN_ANDROID_INPUT:'), ('wrong_image', 'REUSE_EXACT_QUALIFIED_STOCK_RUNTIME'),
            ('repeat_baseline', 'REUSE_VALID_UNCHANGED69_STARTUP_PASS'),
            ('unselected_application', 'EXACT_SELECTED_TRACKING_TESTS_ONLY'),
            ('omitted_mandatory', 'ALL_MANDATORY_GATES_REMAIN_VISIBLE')]:
        control = copy.deepcopy(request)
        if case == 'missing_binding': control['source_bindings'].pop(next(iter(control['source_bindings'])))
        if case == 'changed_binding': control['source_bindings'][next(iter(control['source_bindings']))] = '0' * 64
        if case == 'wrong_image': control['image_revision'] = 8
        if case == 'repeat_baseline': control['startup_qualification_repeated'] = True
        if case == 'unselected_application': control['application_tests'] = False
        if case == 'omitted_mandatory': control['mandatory_checks'].pop()
        with patch.object(admission, 'load', lambda path: control if Path(path) == admission.REQUEST else original_load(path)):
            try: admission.checked_request()
            except RuntimeError as error: assert str(error).startswith(reason), (case, str(error))
            else: raise AssertionError('Guard accepted ' + case)
        rows.append(dict(case=case, status='PASS_EXPECTED_HOST_REFUSAL'))
    workflow = yaml.safe_load((ROOT / admission.WORKFLOW).read_text())
    condition = workflow['jobs']['tracking_integration_android']['if']
    facts = {'github.repository': 'mahfouzhassine8-ops/project-infinity',
        'github.ref': 'refs/heads/' + admission.BRANCH, 'github.event_name': 'push',
        'github.event.head_commit.message': 'Verify tracking integration: selected', 'inputs.feature': ''}
    for case, changes, expected in [('selected_push', {}, True),
            ('unselected_prefix', {'github.event.head_commit.message': 'Record results'}, False),
            ('wrong_branch', {'github.ref': 'refs/heads/unselected'}, False),
            ('wrong_repository', {'github.repository': 'unselected/repository'}, False),
            ('selected_manual', {'github.event_name': 'workflow_dispatch', 'inputs.feature': 'tracking-integration-android'}, True),
            ('wrong_manual', {'github.event_name': 'workflow_dispatch', 'inputs.feature': 'tracking-baseline-android'}, False)]:
        expression = condition
        for key, value in sorted(dict(facts, **changes).items(), key=lambda pair: -len(pair[0])):
            expression = expression.replace(key, repr(value))
        expression = expression.replace('&&', ' and ').replace('||', ' or ')
        assert eval(expression, {'__builtins__': {}}, {'startsWith': lambda value, prefix: value.startswith(prefix)}) is expected, case
        rows.append(dict(case=case, status='PASS_HOST_ROUTING_ONLY'))
    device = feature.FeatureDevice.__new__(feature.FeatureDevice)
    with patch.object(feature.socket, 'create_connection', side_effect=AssertionError('RPC refusal reached socket')):
        for method, params in [('System.Shutdown', None), ('Input.ExecuteAction', {'action': 'quit'}),
                ('Addons.ExecuteAddon', {'addonid': 'unselected.addon'}),
                ('Player.Seek', {'playerid': 1, 'value': {'percentage': 10}})]:
            try: device.rpc(method, params)
            except RuntimeError: pass
            else: raise AssertionError('Unselected RPC accepted: ' + method)
            rows.append(dict(case='refuse_unselected_' + method, status='PASS_REFUSED_BEFORE_SOCKET'))
    receipt = dict(status='PASS_SELECTED_TRACKING_ANDROID_HOST_GUARDS_ONLY', cases=rows,
        selected_tests_sha256=sha(HERE / 'TRACKING-GUARD-SELECTION.json'),
        source_bindings={name: sha(HERE / name) for name in ['admit_tracking_android.py',
            'stage_tracking_android.py', 'tracking_android_observer.py', 'verify_tracking_android.py', Path(__file__).name]},
        workflow_sha256=sha(ROOT / admission.WORKFLOW), request_sha256=sha(admission.REQUEST),
        application_execution=False, provider_response_simulated=False, actual_Android_SDK_execution=False,
        prior40_rerun=False, prior13_installer_rerun=False, signing=False, release_acceptance=False)
    (HERE / 'TRACKING-GUARD-HOST.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], len(rows), 'selected controls')


if __name__ == '__main__': run()
