"""Only the owner-selected controlled host baseline/candidate DNS comparisons."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = TASK.parents[1]
OUT = Path('/workspace/scratch/network-baseline-comparison')
CURL = Path('/workspace/scratch/network-curl810-dns/curl-8.10.0')
STUBS = Path('/workspace/scratch/network-family-host/stubs')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline_sources = OUT/'baseline-sources'
    baseline_sources.mkdir(parents=True, exist_ok=True)
    source_map = json.loads((ROOT/'repairs/infinity-watchlist-playback-2103466-20261108/contract-evidence/BASE466-NATIVE-SOURCE-MAP.json').read_text())
    receipts = {}
    for name in ('DllLibCurl.cpp', 'DllLibCurl.h'):
        source = Path('/workspace/project-infinity/kodi/xbmc/filesystem')/name
        assert digest(source) == source_map['xbmc/filesystem/'+name]
        shutil.copyfile(source, baseline_sources/name)
        receipts['baseline/'+name] = digest(source)
    assert digest(CURL/'lib/asyn-thread.c') == '6c60e80c4a6535564303db5160ff23b5a0aac8ae432b75db7e303405ddfe0ef6'
    subprocess.run(['cc', '-O2', '-shared', '-fPIC', str(HERE/'stall_fixture.c'),
                    '-ldl', '-o', str(OUT/'stall.so')], check=True)
    commands = []
    for variant in ('baseline', 'candidate'):
        source = baseline_sources if variant == 'baseline' else TASK/'native/xbmc/filesystem'
        command = ['g++', '-O2', '-std=c++17', '-pthread', '-I'+str(source),
                   '-I'+str(CURL/'include'), '-I'+str(STUBS)]
        if variant == 'baseline':
            command += ['-DINFINITY_COMPARE_BASELINE=1']
        command += [str(HERE/'compare_probe.cpp'), str(source/'DllLibCurl.cpp'),
                    str(CURL/'lib/.libs/libcurl.so.4.8.0'),
                    '-Wl,-rpath,'+str(CURL/'lib/.libs'), '-o', str(OUT/(variant+'-probe'))]
        subprocess.run(command, check=True)
        commands.append(command)
        receipts[variant+'/host_binary'] = digest(OUT/(variant+'-probe'))
    rows = []
    for scenario in ('deadline', 'cancel'):
        for variant in ('baseline', 'candidate'):
            environment = dict(os.environ, LD_PRELOAD=str(OUT/'stall.so'))
            started = time.monotonic()
            result = subprocess.run([str(OUT/(variant+'-probe')), scenario],
                                    env=environment, text=True, capture_output=True,
                                    check=True, timeout=12)
            row = json.loads(result.stdout)
            row.update(variant=variant, scenario=scenario,
                       process_seconds=time.monotonic()-started,
                       fixture=json.loads(result.stderr.strip()))
            row['previous_2_25s_connect_cleanup_requirement_met'] = row['caller_seconds'] <= 2.25
            row['previous_3_75s_total_return_requirement_met'] = row['process_seconds'] <= 3.75
            rows.append(row)
            print(json.dumps(row), flush=True)
    comparisons = []
    for scenario in ('deadline', 'cancel'):
        baseline, candidate = [r for r in rows if r['scenario'] == scenario]
        assert baseline['result'] == candidate['result'] == (28 if scenario == 'deadline' else 42)
        assert baseline['fixture'] == candidate['fixture']
        regression = (candidate['caller_seconds'] > baseline['caller_seconds']+.25 or
                      candidate['process_seconds'] > baseline['process_seconds']+.25)
        comparisons.append(dict(scenario=scenario,
                                latency_delta_seconds=candidate['caller_seconds']-baseline['caller_seconds'],
                                introduced_regression_observed=regression))
        assert not regression
    report = dict(status='PASS_CONTROLLED_HOST_BASELINE_EQUIVALENCE_ONLY',
                  production_change=False, curl_version='8.10.0 POSIX threaded resolver',
                  comparison='Authenticated baseline pool and shared options versus candidate pool and Automatic policy; identical hostcurl backend and5s stall.',
                  Android_application_result='NOT_RUN_BY_THIS_COMPARISON',
                  old_hard_deadline_result='FAIL_RETAINED_BOTH_VARIANTS', rows=rows,
                  comparisons=comparisons, source_and_binary_hashes=receipts,
                  compile_commands=commands, production_resolver_replacement='NONE')
    (OUT/'RESULT.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS controlled host comparison; Android equivalence not claimed.')


if __name__ == '__main__':
    main()
