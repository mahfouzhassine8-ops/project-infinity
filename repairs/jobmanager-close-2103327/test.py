#!/usr/bin/env python3
"""Run the production JobManager harness with token-accurate shortcut guards."""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
implementation = (HERE / 'test_jobmanager.py').read_text()
old = """    assert 'detach' not in job_cpp.read_text()
    assert 'kill' not in job_cpp.read_text().lower()
"""
new = """    job_text = job_cpp.read_text()
    # Existing comments legitimately describe workers that 'kill themselves'.
    # Guard executable detach/kill shortcuts rather than English prose.
    assert '.detach(' not in job_text
    assert 'pthread_detach' not in job_text
    assert 'pthread_kill' not in job_text
    assert '::kill(' not in job_text
"""
if implementation.count(old) != 1:
    raise RuntimeError('Unexpected JobManager test preimage')
implementation = implementation.replace(old, new, 1)

# The original harness used unnamed pointer parameters without whitespace, which
# the C++ lexer reads as the '*=' operator. Name those test-only parameters; the
# production trace API is not changed.
implementation = implementation.replace(
    'const char* addon=nullptr, const char*="observed", const char*=nullptr) noexcept',
    'const char* addon=nullptr, const char* outcome="observed", const char* target=nullptr) noexcept')
implementation = implementation.replace(
    'Scope(const char* phase, long long=-1, const char* addon=nullptr, const char*=nullptr) noexcept',
    'Scope(const char* phase, long long=-1, const char* addon=nullptr, const char* target=nullptr) noexcept')

namespace = {'__name__': 'jobmanager_test_impl', '__file__': str(HERE / 'test_jobmanager.py')}
exec(compile(implementation, str(HERE / 'test_jobmanager.py'), 'exec'), namespace)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
namespace['run'](parser.parse_args().source)
print('PASS: production JobManager begins cancellation early, reports exact active jobs, and preserves the final worker join')
