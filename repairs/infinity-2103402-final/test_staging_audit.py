import os
from pathlib import Path
import shutil
import tempfile
import unittest

import audit_staging


class StagingTests(unittest.TestCase):
    def test_exact_candidate_files_and_negative_mutations(self):
        apk = os.environ['INFINITY_BASELINE_APK']
        report = audit_staging.audit(apk)
        self.assertEqual(len(report['members']), 19)
        self.assertEqual(report['production_apk_audit'], 'NOT RUN')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'overlay'
            shutil.copytree(audit_staging.ROOT / 'overlay', root)
            unowned = root / 'unrelated.py'
            unowned.write_text('not authorized')
            with self.assertRaisesRegex(ValueError, 'Unexplained'):
                audit_staging.audit(apk, root)
            unowned.unlink()
            target = root / 'script.infinity.commandcenter/service.py'
            target.write_bytes(target.read_bytes() + b'\n# unrelated edit\n')
            with self.assertRaisesRegex(ValueError, 'exact authorized transform'):
                audit_staging.audit(apk, root)


if __name__ == '__main__': unittest.main(verbosity=2)
