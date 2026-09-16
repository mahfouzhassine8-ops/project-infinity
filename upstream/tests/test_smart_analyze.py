"""Contracts for the fast Kodi update-analysis path."""
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / 'upstream'
ANALYZE = ROOT / '.github/workflows/infinity-kodi-analyze.yml'
WATCHER = ROOT / '.github/workflows/infinity-kodi-watch.yml'


class SmartAnalysisContracts(unittest.TestCase):
    def test_smart_report_is_report_only(self):
        text = (UPSTREAM / 'smart_analyze.py').read_text()
        self.assertIn("'full_native_compile': 'deferred'", text)
        self.assertIn("'full_apk_build': 'not_started'", text)
        self.assertIn("'production_modified': False", text)
        self.assertIn("'stop_gate': True", text)
        self.assertIn("'title': 'Kodi Update'", text)

    def test_analyzer_uses_fast_java_compile_but_no_native_build(self):
        text = ANALYZE.read_text()
        self.assertIn('python3 upstream/port.py', text)
        self.assertIn('python3 upstream/validate_candidate_java.py', text)
        self.assertIn('python3 upstream/smart_analyze.py', text)
        self.assertIn('system-tray-status.json', text)
        for forbidden in ('make -C', ' cmake ', 'ndk;', 'apk -j', 'apksigner sign', 'adb install'):
            self.assertNotIn(forbidden, text)

    def test_watcher_deduplicates_analysis_and_never_auto_builds_apk(self):
        text = WATCHER.read_text()
        self.assertIn('infinity-kodi-smart-analysis-', text)
        self.assertIn('lookup-only: true', text)
        self.assertIn('uses: ./.github/workflows/infinity-kodi-analyze.yml', text)
        self.assertNotIn('kodi-candidate-builder.yml', text)
        self.assertNotIn('candidate-build:', text)

    def test_report_generation_contract(self):
        import sys
        sys.path.insert(0, str(UPSTREAM))
        import smart_analyze
        port = {
            'baseline': {'upstream': {'tag': '21.3-Omega'}},
            'target': {'tag': '21.4-Omega', 'commit': 'a' * 40},
            'replay_clean': True,
            'impact': {
                'changed_upstream_files': ['xbmc/cores/VideoPlayer.cpp', 'tools/android/build.gradle'],
                'owned_file_intersections': ['xbmc/cores/VideoPlayer.cpp'],
                'watch_areas': {'playback_audio': ['xbmc/cores/VideoPlayer.cpp']},
            },
        }
        report = smart_analyze.build_report(port, {'owned': {}}, {'status': 'passed'})
        self.assertTrue(report['update_available'])
        self.assertEqual(report['state'], 'review_required')
        self.assertEqual(report['targeted_checks']['full_apk_build'], 'not_started')
        self.assertEqual(report['system_tray']['title'], 'Kodi Update')


if __name__ == '__main__':
    unittest.main()
