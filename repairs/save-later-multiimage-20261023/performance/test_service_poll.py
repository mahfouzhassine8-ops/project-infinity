"""Narrow actual-method measurements for the resident stability no-op gate.

Kodi property access and the persistence boundary are in-memory instruments;
the original service class and original common decorator are executed. No app,
checkpoint or shutdown scenario is run. Wall times are host microbenchmarks,
not Android frame pacing or physical Fold CPU measurements.
"""
import argparse
import ast
import copy
from contextlib import contextmanager
from functools import wraps
import hashlib
import json
from pathlib import Path
import statistics
import time
from types import SimpleNamespace


class Harness:
    def __init__(self, source, common):
        self.clock = 0.0
        self.values = {'Infinity.MotionModeEffective': 'full',
                       'Infinity.RefreshGranted': 'false', 'Infinity.RefreshActiveHz': '60'}
        self.records = {}
        self.reset_metrics()
        @contextmanager
        def scope():
            self.scope_entries += 1
            if self.depth == 0:
                self.admissions += 1
            self.depth += 1
            try:
                yield
            finally:
                self.depth -= 1
        def prop(name, default=''):
            self.property_reads += 1
            return self.values.get(name, default)
        def publish(name, value):
            text = str(value)
            if self.values.get(name) != text:
                self.property_changes += 1
                self.values[name] = text
        def read(path, default):
            self.json_reads += 1
            return copy.deepcopy(self.records.get(str(path), default))
        def atomic(path, value):
            self.json_writes += 1
            self.records[str(path)] = copy.deepcopy(value)
        ns = {'wraps': wraps, 'persistence_scope': scope, 'Path': Path,
              'time': SimpleNamespace(monotonic=lambda: self.clock, time=lambda: self.clock),
              '_prop': prop, '_set': publish, 'read_json': read, 'atomic_json': atomic,
              'log': lambda *args: None, 'BOOT_HISTORY': 'boot-history.json',
              'BOOT_MARKER': 'boot-marker.json'}
        decorator = next(node for node in ast.parse(common).body if isinstance(node, ast.FunctionDef)
                         and node.name == 'persistence_serialized')
        cls = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
                   and node.name == 'StabilityController')
        exec(compile(ast.fix_missing_locations(ast.Module(body=[decorator, cls], type_ignores=[])),
                     'actual_stability_controller', 'exec'), ns)
        self.controller = ns['StabilityController'].__new__(ns['StabilityController'])
        self.controller.__dict__.update(profile=Path('/instrumented-profile'), started=0.0, stage='core',
            ready_marked=False, primary_ready=False, secondary_ready=False, primary_timeout=False,
            secondary_timeout=False, _last_policy=None)

    def reset_metrics(self):
        self.admissions = self.scope_entries = self.depth = 0
        self.json_reads = self.json_writes = self.property_reads = self.property_changes = 0

    def tick(self, optimized):
        getattr(self.controller, 'poll' if optimized else 'tick')()

    def outcome(self):
        return {'state': self.controller.__dict__, 'properties': self.values, 'records': self.records}

    def metrics(self):
        return {name: getattr(self, name) for name in ('admissions', 'scope_entries', 'json_reads',
                'json_writes', 'property_reads', 'property_changes')}


def preserved(original, candidate):
    before = ast.parse(original)
    after = ast.parse(candidate)
    old_class = next(node for node in before.body if isinstance(node, ast.ClassDef) and node.name == 'StabilityController')
    new_class = next(node for node in after.body if isinstance(node, ast.ClassDef) and node.name == 'StabilityController')
    addition = next(node for node in new_class.body if isinstance(node, ast.FunctionDef) and node.name == 'poll')
    lines = candidate.splitlines(keepends=True)
    # The new method is the only class-body insertion; decorators and every
    # prior method retain their exact source bytes, including persistence.
    assert lines[addition.end_lineno] == '\n'
    stripped = ''.join(lines[:addition.lineno-1] + lines[addition.end_lineno+1:])
    assert stripped.replace('        stability.poll()\n', '        stability.tick()\n') == original
    old_methods = {node.name: ast.dump(node) for node in old_class.body if isinstance(node, ast.FunctionDef)}
    new_methods = {node.name: ast.dump(node) for node in new_class.body if isinstance(node, ast.FunctionDef) and node.name != 'poll'}
    assert old_methods == new_methods
    assert original.count('        stability.tick()\n') == candidate.count('        stability.poll()\n') == 1


def run(before, after, common, out):
    original, candidate, shared = before.read_text(), after.read_text(), common.read_text()
    preserved(original, candidate)
    baseline, corrected = Harness(original, shared), Harness(candidate, shared)
    for moment in (0.0, .5, 1.0, 2.0, 4.0, 8.0, 16.0, 28.0, 45.0):
        for harness, optimized in ((baseline, False), (corrected, True)):
            harness.clock = moment
            harness.tick(optimized)
        assert baseline.outcome() == corrected.outcome()
    cold = {'before': baseline.metrics(), 'after': corrected.metrics()}
    samples = 120  # One foreground minute at the original 0.5-second cadence.
    for harness in (baseline, corrected):
        harness.reset_metrics()
    for index in range(samples):
        baseline.clock = corrected.clock = 60.0 + index * .5
        baseline.tick(False)
        corrected.tick(True)
        assert baseline.outcome() == corrected.outcome()
    warm = {'before': baseline.metrics(), 'after': corrected.metrics()}
    assert warm['before']['admissions'] == samples and warm['after']['admissions'] == 0
    assert warm['before']['json_writes'] == warm['after']['json_writes'] == 0
    policies = [dict(Hz='120', granted='true', motion='full', expected='performance'),
                dict(Hz='120', granted='true', motion='reduced', expected='grace'),
                dict(Hz='120', granted='true', motion='off', expected='still'),
                dict(Hz='60', granted='false', motion='full', expected='balanced')]
    for policy in policies:
        for harness, optimized in ((baseline, False), (corrected, True)):
            harness.values.update({'Infinity.RefreshActiveHz': policy['Hz'],
                                   'Infinity.RefreshGranted': policy['granted'],
                                   'Infinity.MotionModeEffective': policy['motion']})
            harness.clock += .5
            harness.tick(optimized)
            assert harness.controller._last_policy == policy['expected']
        assert baseline.outcome() == corrected.outcome()
    # Incomplete startup flags must never use the no-op shortcut, even when
    # every other field says ready. Compare the exact existing writer path.
    for flag in ('ready_marked', 'primary_ready', 'secondary_ready', 'primary_timeout', 'secondary_timeout'):
        b, a = Harness(original, shared), Harness(candidate, shared)
        for harness, optimized in ((b, False), (a, True)):
            harness.clock = 100.0
            harness.tick(optimized)
            setattr(harness.controller, flag, False)
            harness.reset_metrics()
            harness.tick(optimized)
            assert harness.admissions == 1
        assert b.outcome() == a.outcome()
    timing = {}
    for label, harness, optimized in (('before', baseline, False), ('after', corrected, True)):
        values = []
        for repeat in range(7):
            started = time.perf_counter_ns()
            for _ in range(10000):
                harness.tick(optimized)
            values.append((time.perf_counter_ns() - started) / 10000)
        timing[label] = {'median_ns_per_call': round(statistics.median(values), 1),
                         'samples_ns_per_call': [round(value, 1) for value in values]}
    report = {'host': 'PASS', 'source_sha256': hashlib.sha256(original.encode()).hexdigest(),
              'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
              'cold_actual_method_sequence': cold, 'warm_60_seconds_120_ticks': warm,
              'all_four_live_policies_match': True, 'five_incomplete_flag_paths_match': True,
              'prior_methods_byte_identical': True, 'host_microbenchmark': timing,
              'timing_limit': 'In-memory boundary; no synthetic delays, not Android CPU/frame pacing',
              'android': 'NOT RUN', 'physical_fold': 'NOT RUN', 'shutdown': 'NOT RUN; independent'}
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'common', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
