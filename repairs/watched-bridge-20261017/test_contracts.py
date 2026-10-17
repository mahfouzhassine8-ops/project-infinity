"""Installed producer changes must withhold episode interpretation."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent / 'addon'))
import provider_contracts as contracts


class Contracts(unittest.TestCase):
    def test_exact_source_required_and_version_or_code_change_is_withheld(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'addon.xml').write_text('<addon id="plugin.video.fixture" version="1.2.3"/>')
            (root / 'rows.py').write_text('show_ids = True\n')
            record = dict(version='1.2.3', scope='show_episode', proof='reviewed', files={'rows.py': hashlib.sha256((root / 'rows.py').read_bytes()).hexdigest()})
            with mock.patch.dict(contracts.CATALOG, {'plugin.video.fixture': record}):
                self.assertEqual(contracts.verify('plugin.video.fixture', root), 'reviewed')
                (root / 'rows.py').write_text('episode_ids = True\n')
                self.assertIsNone(contracts.verify('plugin.video.fixture', root))
                (root / 'rows.py').write_text('show_ids = True\n')
                (root / 'addon.xml').write_text('<addon id="plugin.video.fixture" version="1.2.4"/>')
                self.assertIsNone(contracts.verify('plugin.video.fixture', root))
                self.assertIsNone(contracts.verify('plugin.video.otaku', root))

    def test_symlink_outside_addon_and_missing_or_bad_manifest_are_withheld(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'addon'; root.mkdir()
            other = Path(folder) / 'outside.py'; other.write_text('show_ids=True')
            (root / 'rows.py').symlink_to(other)
            (root / 'addon.xml').write_text('<addon id="plugin.video.fixture" version="1"/>')
            record = dict(version='1', scope='show_episode', proof='reviewed', files={'rows.py': hashlib.sha256(other.read_bytes()).hexdigest()})
            with mock.patch.dict(contracts.CATALOG, {'plugin.video.fixture': record}):
                self.assertIsNone(contracts.verify('plugin.video.fixture', root))
                (root / 'addon.xml').write_text('<broken')
                self.assertIsNone(contracts.verify('plugin.video.fixture', root))
                (root / 'addon.xml').unlink()
                self.assertIsNone(contracts.verify('plugin.video.fixture', root))


if __name__ == '__main__':
    unittest.main(verbosity=2)
