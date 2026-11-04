"""Privacy, input safety and bounded read-only behavior; no Kodi/device run."""
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import infinity_search_state_probe as probe


class Reader:
    def __init__(self, root):
        self.root = root; self.now = 0.0; self.props = {}; self.tick = 0
        self.change = lambda: None; self.stop = False
    def profile(self): return str(self.root)
    def progress_profile(self): return str(self.root / 'actual-command-center-profile')
    def identity(self, aid): return {'id': aid, 'version': '1', 'enabled': True}
    def revision(self, name): return self.props.get(name, '')
    def wait(self, duration):
        self.now += duration; self.tick += 1; self.change()
        return self.stop
    def clock(self): return self.now


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.reader = Reader(self.root)
        self.settings = self.root / 'addon_data/plugin.video.watchnixtoons2/settings.xml'
        self.settings.parent.mkdir(parents=True)
        self.write({'searchHistory': 'PRIVATE-QUERY-ALPHA', 'trakt.token': 'PRIVATE-TOKEN-ALPHA'})
    def write(self, values):
        root = ET.Element('settings')
        for key, value in values.items(): ET.SubElement(root, 'setting', id=key).text = value
        self.settings.write_bytes(ET.tostring(root))
    def run_probe(self, seconds=2):
        return probe.observe(self.reader, seconds, self.reader.clock)

    def test_private_values_paths_tokens_and_unknown_keys_never_enter_report(self):
        def change():
            if self.reader.tick == 1:
                self.write({'searchHistory': 'PRIVATE-QUERY-BETA', 'trakt.token': 'PRIVATE-TOKEN-BETA', 'PRIVATE-KEY-NAME': 'PRIVATE-VALUE'})
                self.reader.props['Infinity.ResumeHub.PresentationSnapshot'] = 'PRIVATE-MEDIA-TITLE'
        self.reader.change = change
        report = self.run_probe(); encoded = json.dumps(report)
        for secret in ('PRIVATE-', str(self.root), 'trakt.token', 'searchHistory'):
            self.assertNotIn(secret, encoded)
        row = next(e for e in report['events'] if e['kind'] == 'settings_changed')
        self.assertEqual(row['changed_key_categories'], {'search_history': 1, 'credential_related': 1, 'configuration_or_other': 1})
        self.assertTrue(any(e['kind'] == 'global_revision_changed' for e in report['events']))

    def test_identical_rewrite_reports_stamp_change_without_content_change(self):
        def change():
            if self.reader.tick == 1:
                st = self.settings.stat(); os.utime(self.settings, ns=(st.st_atime_ns, st.st_mtime_ns + 1000000))
        self.reader.change = change
        row = next(e for e in self.run_probe()['events'] if e['kind'] == 'settings_changed')
        self.assertTrue(row['file_stamp_changed']); self.assertFalse(row['content_changed'])
        self.assertEqual(row['changed_key_categories'], {})

    def test_observation_does_not_modify_input_files_or_dispatch_provider(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        report = self.run_probe()
        after = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(report['provider_invocations'], 0)
        self.assertEqual(report['token_reads_or_writes'], 0)
        self.assertEqual(report['events'], [])
        self.assertEqual(report['settings_initial_states']['plugin.video.watchnixtoons2'], 'readable')
        self.assertEqual(report['settings_initial_states']['plugin.video.thecrew'], 'absent')
        self.assertEqual(report['native_request_outcome'], 'NOT_OBSERVABLE_WITHOUT_REQUEST_HOOK')

    def test_malformed_oversized_and_entity_input_stays_unparsed_without_output_values(self):
        for raw, expected in [(b'<settings><broken', 'unparsed'),
                              (b'<!DOCTYPE settings [<!ENTITY x "PRIVATE-X">]><settings/>', 'unparsed'),
                              ('<!DOCTYPE settings [<!ENTITY x "PRIVATE-X">]><settings/>'.encode('utf-16'), 'unparsed'),
                              (b'x' * (probe.MAX_SETTINGS_BYTES + 1), 'size_limit'),
                              (b'<settings><setting id="a"/><setting id="a"/></settings>', 'unparsed')]:
            with self.subTest(expected=expected, length=len(raw)):
                self.settings.write_bytes(raw)
                state = probe.snapshot_settings(str(self.settings), b'x' * 32)
                self.assertEqual(state['state'], expected)
                self.assertNotIn('entries', state)
                self.reader = Reader(self.root)
                report = self.run_probe()
                self.assertEqual(report['settings_initial_states']['plugin.video.watchnixtoons2'], expected)
                self.assertNotIn('PRIVATE-', json.dumps(report))

    def test_file_symlink_and_outside_profile_directory_are_not_read(self):
        target = self.root / 'secret.xml'; target.write_text('<settings/>')
        self.settings.unlink(); self.settings.symlink_to(target)
        self.assertEqual(probe.snapshot_settings(str(self.settings), b'x' * 32)['state'], 'unreadable')
        with tempfile.TemporaryDirectory() as external:
            outside = Path(external); (outside/'settings.xml').write_text('<settings/>')
            self.settings.unlink(); self.settings.parent.rmdir(); self.settings.parent.symlink_to(outside, target_is_directory=True)
            report = self.run_probe()
            self.assertTrue(any(e.get('state') == 'outside_profile' for e in report['events']))
            self.assertNotIn(external, json.dumps(report))

    def test_bounded_samples_abort_event_cap_and_oversized_revision(self):
        self.reader.change = lambda: self.reader.props.update({name: str(self.reader.tick) for name in probe.REVISIONS})
        report = self.run_probe(60)
        self.assertEqual(report['samples'], 121); self.assertEqual(report['elapsed_seconds'], 60)
        self.assertEqual(len(report['events']), probe.MAX_EVENTS)
        self.assertTrue(report['event_limit_reached'])
        self.reader = Reader(self.root); self.reader.stop = True
        self.reader.props['widgetreload'] = 'PRIVATE-' * 10000
        aborted = self.run_probe()
        self.assertEqual(aborted['samples'], 1); self.assertTrue(aborted['aborted'])
        self.assertIn('widgetreload', aborted['unobservable_revisions'])
        with self.assertRaises(ValueError): self.run_probe(61)

    def test_report_exclusive_create_preserves_existing_files(self):
        report = self.run_probe(); out = self.root/'reports'; out.mkdir()
        with patch.object(probe.uuid, 'uuid4', return_value=SimpleNamespace(hex='a'*32)), patch.object(probe.time, 'strftime', return_value='fixed'):
            path = Path(probe.write_report(str(out), report)); before = path.read_bytes()
            with self.assertRaises(FileExistsError): probe.write_report(str(out), report)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(list(out.iterdir())), 1)

    def test_actual_reader_source_identity_is_read_only_and_version_sanitized(self):
        addon = self.root/'addon'; addon.mkdir(); (addon/'addon.xml').write_text('<addon id="test"/>')
        apis = SimpleNamespace(Addon=lambda _: SimpleNamespace(getAddonInfo=lambda key: {'path': str(addon), 'version': 'private value / path', 'profile': str(self.root/'cc-profile')}[key]))
        runtime = SimpleNamespace(Monitor=lambda: self.reader, getCondVisibility=lambda _: True)
        reader = probe.KodiReader(runtime, apis, SimpleNamespace(Window=lambda _: self.reader), SimpleNamespace(translatePath=lambda p: p))
        result = reader.identity('plugin.video.otaku')
        self.assertEqual(result['version'], 'unreported')
        self.assertEqual(result['sources']['addon.xml']['sha256'], hashlib.sha256((addon/'addon.xml').read_bytes()).hexdigest())
        self.assertNotIn(str(addon), json.dumps(result))
        self.assertEqual(reader.progress_profile(), str(self.root/'cc-profile'))

    def test_continue_watching_uses_actual_command_center_profile(self):
        target = Path(self.reader.progress_profile()) / 'continue-watching.json'
        target.parent.mkdir()
        def change():
            if self.reader.tick == 1: target.write_text('PRIVATE-MEDIA-DATA')
        self.reader.change = change
        report = self.run_probe()
        self.assertEqual(report['continue_watching_initial_state'], 'absent')
        self.assertTrue(any(e['kind'] == 'continue_watching_file_changed' for e in report['events']))
        self.assertNotIn(str(target), json.dumps(report))
        self.assertNotIn('PRIVATE-', json.dumps(report))

    def test_profile_switch_is_explicit_without_exposing_either_path(self):
        other = self.root/'other'; other.mkdir()
        self.reader.change = lambda: setattr(self.reader, 'root', other)
        report = self.run_probe()
        self.assertTrue(any(e['kind'] == 'profile_changed' for e in report['events']))
        self.assertNotIn(str(self.root), json.dumps(report))


if __name__ == '__main__':
    unittest.main(verbosity=2)
