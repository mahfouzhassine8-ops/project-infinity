"""New DNS ownership/deadline feasibility checks only; no Kodi/app execution."""
import json
import os
from pathlib import Path
import subprocess
import unittest

BIN = Path(os.environ.get('INFINITY_DNS_PROTOTYPE_BIN',
                         '/workspace/scratch/dns-deadline-correction/prototype'))


class Feasibility(unittest.TestCase):
    def run_probe(self, helper='helper', repetitions=1, cancel=-1, deadline=2000, host='localhost'):
        result = subprocess.run([str(BIN/'probe'), str(BIN/helper), str(repetitions),
                                 str(cancel), str(deadline), host], check=True,
                                capture_output=True, text=True, timeout=15)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def assert_clean(self, rows):
        for row in rows:
            self.assertEqual(row['fd_growth'], 0, row)
            self.assertEqual(row['remaining_children'], 0, row)

    def test_normal_libc_lookup_retains_addresses_and_closes_inherited_fds(self):
        rows = self.run_probe(repetitions=25)
        for row in rows:
            self.assertEqual(row['outcome'], 0, row)
            self.assertEqual(row['gai_error'], 0, row)
            self.assertGreater(row['addresses'], 0, row)
            self.assertEqual(row['inherited_extra_fds'], 0, row)
            self.assertEqual(row['preexec_extra_fds'], 0, row)
        self.assert_clean(rows)

    def test_stalled_lookup_deadline_includes_reap(self):
        rows = self.run_probe('stalled_helper')
        self.assertEqual(rows[0]['outcome'], 1, rows)
        self.assertLessEqual(rows[0]['caller_seconds'], 2.25, rows)
        self.assert_clean(rows)

    def test_cancel_stalled_lookup_includes_reap(self):
        rows = self.run_probe('stalled_helper', cancel=150)
        self.assertEqual(rows[0]['outcome'], 2, rows)
        self.assertLessEqual(rows[0]['caller_seconds'], .5, rows)
        self.assert_clean(rows)

    def test_repeated_cancel_does_not_accumulate_fds_children_or_memory(self):
        rows = self.run_probe('stalled_helper', repetitions=50, cancel=10)
        self.assertTrue(all(r['outcome'] == 2 for r in rows), rows)
        self.assert_clean(rows)
        # Allow allocator warmup; report high-water RSS rather than claim a
        # complete native-memory/leak proof from this single counter.
        self.assertLessEqual(rows[-1]['max_rss_kb'] - rows[9]['max_rss_kb'], 1024, rows)


if __name__ == '__main__':
    unittest.main(verbosity=2)
