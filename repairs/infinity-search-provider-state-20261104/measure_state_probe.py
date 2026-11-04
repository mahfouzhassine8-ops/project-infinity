"""Bounded host-only sampler cost; synthetic files, no Kodi or provider run."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import tracemalloc

import infinity_search_state_probe as probe
from test_state_probe import Reader


def measure(name, entries, mutate):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        paths = [root/'addon_data'/aid/'settings.xml' for aid in probe.PROVIDERS]
        def content(generation):
            return ('<settings>' + ''.join(
                '<setting id="fixture.%04d">%s:%03d</setting>' % (i, 'x' * 24, generation)
                for i in range(entries)) + '</settings>').encode()
        raw = content(0)
        assert len(raw) <= probe.MAX_SETTINGS_BYTES
        for path in paths:
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
        reader = Reader(root)
        if mutate:
            def change():
                updated = content(reader.tick)
                for path in paths: path.write_bytes(updated)
            reader.change = change
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        tracemalloc.start()
        started = time.perf_counter()
        report = probe.observe(reader, clock=reader.clock)
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        after = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        assert report['samples'] == 121
        assert mutate or before == after
        return dict(case=name, settings_bytes_each=len(raw), settings_files=3,
                    settings_writes_by_fixture=360 if mutate else 0,
                    samples=report['samples'], simulated_observation_seconds=60,
                    measured_host_seconds_including_tracemalloc_and_fixture_writes=round(elapsed, 6),
                    peak_traced_python_bytes_including_fixture=peak,
                    report_bytes=len(json.dumps(report).encode()),
                    reported_events=len(report['events']), event_limit_reached=report['event_limit_reached'])


if __name__ == '__main__':
    print(json.dumps(dict(
        evidence='HOST_SYNTHETIC_ONLY',
        cases=[measure('unchanged_250_entries', 250, False),
               measure('changed_every_sample_250_entries', 250, True),
               measure('unchanged_near_size_cap', 3500, False)],
        limits=['No real sleeps: 60 seconds is a simulated clock, not an Android run.',
                'Tracemalloc instrumentation and fixture rewrites are included in elapsed time and peak memory.',
                'Identity APIs are stubbed; Android file/API latency and source-hash overhead are unmeasured.',
                'This does not establish production overhead, native allocation pressure or device stability.']), indent=2))
