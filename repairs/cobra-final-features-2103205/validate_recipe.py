"""Validate immutable workflow, inherited gates and explicit freeze contract."""
from pathlib import Path
import argparse
import ast
import json
import subprocess
import yaml
from apply import ROOT, checked_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-frozen', action='store_true')
    args = parser.parse_args()
    repo = ROOT.parents[1]
    prior = repo / 'repairs/cobra-oled-blue-2103204'
    for path in ROOT.glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    inherited = json.loads((ROOT / 'inherited-android-cases.json').read_text())
    assert inherited == (json.loads((prior / 'inherited-android-cases.json').read_text()) |
                         json.loads((prior / 'new-android-cases.json').read_text()))
    assert len(inherited) == 53 and sum(map(len, inherited.values())) == 500
    text = (repo / '.github/workflows/infinity-2103205-final-features.yml').read_text()
    old_text = (repo / '.github/workflows/infinity-2103204-oled-blue.yml').read_text()
    workflow = yaml.safe_load(text)
    job = workflow['jobs']['audit-package']
    assert job['strategy'] == {'fail-fast': False, 'matrix': {'replica': [1, 2]}}
    assert workflow['concurrency']['cancel-in-progress'] is False
    assert workflow['permissions'] == {'contents': 'read', 'actions': 'read'}
    assert 'ref: 166cf9dad40a8a0333563830a3c0965ce4e81da6, path: audit204' in text
    assert 'run-id: 35570386274' in text and 'path: baseline204' in text
    parent_upgrade = 'python3 audit204/repairs/cobra-oled-blue-2103204/ci.py upgrade'
    upgrade = 'python3 audit205/repairs/cobra-final-features-2103205/ci.py upgrade'
    assert text.count(parent_upgrade) == text.count(upgrade) == 1
    assert text.index(parent_upgrade) < text.index(upgrade) < text.index('id: build205')
    adapter_gate = 'python3 audit205/repairs/cobra-final-features-2103205/test_host_fixture_adapter.py --fixture audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift.py --out audit205/host-fixture-adapter-guards.json'
    adapter_run = 'python3 audit205/repairs/cobra-final-features-2103205/host_timeshift_adapter.py --fixture audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift.py'
    assert text.count(adapter_gate) == text.count(adapter_run) == 1
    assert text.index(adapter_gate) < text.index(upgrade) < text.index(adapter_run) < text.index('id: build205')
    for phase in ['verify', 'deliver']:
        assert text.count('python3 audit205/repairs/cobra-final-features-2103205/ci.py ' + phase) == 1
    assert 'steps.build205.outcome' in text and 'steps.build204.outcome' not in text
    assert '--base-apk baseline168native/Infinity-1.0.9-Cobra-Status-Bar-PythonInvoker-Stability-RC1.apk' in text
    assert '--build-dir repair202-build' in text
    for line in old_text.splitlines():
        if "'--tests'," in line:
            assert line in text, 'Inherited runner selector removed: ' + line
        if 'adapt_inherited_tests.py' in line:
            assert line in text, 'Inherited adapter removed: ' + line
    assert "'--tests','com.projectinfinity.kodi.Cobra2103205*'" in text
    for key in ['INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS']:
        assert '${{ secrets.' + key + ' }}' in text
    for step in job['steps']:
        if 'run' not in step:
            continue
        result = subprocess.run(['bash', '-n'], input=step['run'], capture_output=True, text=True)
        assert result.returncode == 0, (step.get('name'), result.stderr)
        inside, lines = False, []
        for line in step['run'].splitlines():
            if "python3 - <<'PY'" in line:
                inside, lines = True, []
            elif inside and line == 'PY':
                compile('\n'.join(lines), str(step.get('name')), 'exec')
                inside = False
            elif inside:
                lines.append(line)
        assert not inside, 'Unclosed Python heredoc'
    reviewed = json.loads((ROOT / 'reviewed.json').read_text())
    if args.require_frozen:
        checked_review()
        new = json.loads((ROOT / 'new-android-cases.json').read_text())
        assert new and not (set(inherited) & set(new))
        assert reviewed['new_android_cases'] == sum(map(len, new.values()))
    elif reviewed.get('status') != 'frozen':
        try:
            checked_review()
        except RuntimeError as error:
            assert 'blocked until review' in str(error)
        else:
            raise AssertionError('Unfrozen recipe must fail closed')
    print(json.dumps({'passed': True, 'workflow_steps': len(job['steps']), 'inherited_cases': 500,
                      'all_parent_runner_selectors_preserved': True, 'two_replicas': True,
                      'review_status': reviewed.get('status'), 'physical_device_verified': False}))


if __name__ == '__main__':
    main()
