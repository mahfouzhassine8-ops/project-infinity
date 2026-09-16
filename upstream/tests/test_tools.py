"""Offline regression tests. Real Git is used for patch/add/delete/conflict tests."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import watch
import port

BASELINE = json.loads((ROOT/'baseline.json').read_text())
BASE = BASELINE['upstream']['commit']


class Releases(unittest.TestCase):
    def test_stable_numeric_order(self):
        self.assertGreater(watch.stable_version('21.10-Omega'), watch.stable_version('21.9-Omega'))
        self.assertGreater(watch.stable_version('22.0-Piers'), watch.stable_version('21.99-Omega'))
        self.assertEqual(watch.stable_version('21.3.1-Omega'), (21, 3, 1))

    def test_beta_rc_alpha_and_injection_rejected(self):
        for tag in ['22.0b2-Piers', '22.0rc1-Piers', '22.0a3-Piers', 'v22.0',
                    '22.0-Piers;touch/tmp/x', '22.0-beta', '22.0-nightly',
                    '22.0-rc1', '$(id)', '../x', '22.0-Piers\nX=1', 'main']:
            with self.subTest(tag=tag):
                self.assertIsNone(watch.stable_version(tag))

    def test_no_update_still_sees_newer_beta(self):
        rows = {'21.3-Omega': BASE, '21.2-Omega': '1'*40, '22.0b2-Piers': '2'*40}
        report = watch.detect(rows, BASELINE, lambda tag: self.fail('No release lookup needed'))
        self.assertEqual(report['status'], 'no_new_stable_source_tag')

    def test_missing_or_moved_pinned_tag_is_error(self):
        for tags in [{}, {'21.3-Omega': 'f'*40}]:
            with self.assertRaises(RuntimeError):
                watch.detect(tags, BASELINE, lambda tag: None)

    def test_source_tag_not_assumed_binary_release(self):
        report = watch.detect({'21.3-Omega': BASE, '22.0-Piers': 'b'*40}, BASELINE, lambda tag: None)
        self.assertEqual(report['latest_candidate']['publication'], 'source_tag_only')
        self.assertFalse(report['build_started'])
        self.assertFalse(report['installed_app_modified'])

    def test_release_metadata_can_exclude_stable_shaped_tag(self):
        for metadata in [{'draft': True}, {'prerelease': True}]:
            report = watch.detect({'21.3-Omega': BASE, '22.0-Piers': 'b'*40}, BASELINE, lambda tag: metadata)
            self.assertFalse(report['candidates'])

    def test_errors_are_not_up_to_date(self):
        def bad_lookup(_):
            raise RuntimeError('rate limited')
        with self.assertRaises(RuntimeError):
            watch.detect({'21.3-Omega': BASE, '22.0-Piers': 'b'*40}, BASELINE, bad_lookup)

    def test_annotated_tags_use_peeled_commit(self):
        stdout = '1'*40+'\trefs/tags/21.3-Omega\n' + BASE+'\trefs/tags/21.3-Omega^{}\n'
        with patch('watch.subprocess.run', return_value=subprocess.CompletedProcess([], 0, stdout, '')):
            self.assertEqual(watch.read_official_tags()['21.3-Omega'], BASE)

    def test_all_new_stable_releases_sorted(self):
        report = watch.detect({'21.3-Omega': BASE, '21.4-Omega': '4'*40, '22.0-Piers': 'a'*40}, BASELINE, lambda tag: {})
        self.assertEqual([r['tag'] for r in report['candidates']], ['21.4-Omega','22.0-Piers'])


class FakeAPI:
    def __init__(self):
        self.issues = []
        self.writes = []
    def pages(self, path):
        return list(self.issues)
    def request(self, path, method, body):
        row = dict(body, number=len(self.issues)+1, state='open')
        self.issues.append(row)
        self.writes.append((path, method, body))
        return row


class Notifications(unittest.TestCase):
    def setUp(self):
        self.report = watch.detect({'21.3-Omega': BASE, '22.0-Piers': 'b'*40}, BASELINE, lambda _:None)
    def test_once_only_even_when_issue_closed(self):
        api = FakeAPI()
        self.assertEqual(len(watch.notify(self.report, BASELINE, api, 'test-run')), 1)
        api.issues[0]['state'] = 'closed'
        self.assertEqual(watch.notify(self.report, BASELINE, api, 'test-run'), [])
        self.assertEqual(len(api.writes), 1)
    def test_moved_tag_alert_not_auto_analyzed(self):
        api=FakeAPI()
        watch.notify(self.report, BASELINE, api, 'test-run')
        self.report['candidates'][0]['commit']='c'*40
        self.assertEqual(watch.notify(self.report, BASELINE, api, 'test-run'), [])
        self.assertIn('WARNING', api.writes[-1][2]['body'])
    def test_wrong_repo_cannot_write(self):
        bad=copy.deepcopy(BASELINE);bad['repository']='other/repo'
        with self.assertRaises(RuntimeError):
            watch.notify(self.report, bad, FakeAPI(), 'test-run')
    def test_issue_mentions_owner_not_external_destination(self):
        body=watch.notification_body(self.report['candidates'][0], BASELINE, 'test-run')
        self.assertIn('@mahfouzhassine8-ops',body)
        self.assertIn('NOT changed',body)
        self.assertIn('source_tag_only',body)
    def test_token_redirect_refused(self):
        with self.assertRaises(RuntimeError):
            watch.NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'https://attacker.invalid')
    def test_api_writes_restricted(self):
        with self.assertRaises(RuntimeError):
            watch.API().request('/repos/other/repo/issues', 'POST', {})
    def test_pagination_exhaustive(self):
        api=watch.API()
        with patch.object(api,'request',side_effect=[[{}]*100,[{}]*2]) as req:
            self.assertEqual(len(api.pages('/repos/x/y/issues')),102)
            self.assertIn('page=2',req.call_args[0][0])
    def test_empty_tag_response_errors(self):
        with patch('watch.subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')):
            with self.assertRaises(RuntimeError):watch.read_official_tags()


class RealGit(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.repo=self.root/'repo';self.repo.mkdir()
        port.git(self.repo,'init','--quiet')
        (self.repo/'code.txt').write_text('one\ntwo\nthree\n')
        (self.repo/'deleted.txt').write_text('old\n')
        (self.repo/'binary.dat').write_bytes(b'\x00\xffbase')
        port.git(self.repo,'add','-A');port.git(self.repo,'commit','-m','base')
        self.base=port.text(self.repo,'rev-parse','HEAD')
        self.patches=self.root/'patches';self.patches.mkdir()
        self.logs=self.root/'logs';self.logs.mkdir()
    def tearDown(self):self.tmp.cleanup()
    def candidate(self, sha):
        path=self.root/'candidate'
        port.git(self.repo,'worktree','add','--detach',path,sha)
        return path
    def test_binary_add_delete_modify_exact_roundtrip(self):
        (self.repo/'code.txt').write_text('one\nInfinity\nthree\n')
        (self.repo/'new.txt').write_text('new file\n')
        (self.repo/'deleted.txt').unlink()
        (self.repo/'binary.dat').write_bytes(b'\x00\xffnew')
        phase=port.snapshot(self.repo,'01',self.patches)
        candidate=self.candidate(self.base)
        results,clean=port.replay(candidate,[phase],self.patches,self.logs)
        self.assertTrue(clean)
        self.assertEqual(port.text(self.repo,'rev-parse','HEAD^{tree}'),port.text(candidate,'rev-parse','HEAD^{tree}'))
    def test_conflict_blocks_dependent_phases(self):
        (self.repo/'code.txt').write_text('one\nInfinity\nthree\n')
        first=port.snapshot(self.repo,'01',self.patches)
        (self.repo/'new.txt').write_text('dependent file\n')
        second=port.snapshot(self.repo,'02',self.patches)
        candidate=self.candidate(self.base)
        (candidate/'code.txt').write_text('one\nUPSTREAM CONFLICT\nthree\n')
        port.git(candidate,'add','-A');port.git(candidate,'commit','-m','upstream')
        results,clean=port.replay(candidate,[first,second],self.patches,self.logs)
        self.assertFalse(clean)
        self.assertEqual(len(results),1)
        self.assertFalse((candidate/'new.txt').exists())
    def test_patch_tampering_refused(self):
        (self.repo/'code.txt').write_text('changed\n')
        first=port.snapshot(self.repo,'01',self.patches)
        (self.patches/first['patch']).write_text('bad patch')
        candidate=self.candidate(self.base)
        with self.assertRaises(RuntimeError):port.replay(candidate,[first],self.patches,self.logs)
    def test_empty_phase_is_not_fake_patch(self):
        phase=port.snapshot(self.repo,'empty',self.patches)
        self.assertIsNone(phase['patch'])
        _,clean=port.replay(self.candidate(self.base),[phase],self.patches,self.logs)
        self.assertTrue(clean)
    def test_full_diff_has_more_than_300_files(self):
        for i in range(305):(self.repo/('file-%03d.txt'%i)).write_text('new')
        port.git(self.repo,'add','-A');port.git(self.repo,'commit','-m','many')
        self.assertEqual(len(port.diff_names(self.repo,self.base,'HEAD')),305)
    def test_user_changes_on_disjoint_line_preserved_by_threeway(self):
        # Enough context separation to exercise a clean 3-way merge.
        long=''.join('line%d\n'%i for i in range(100))
        (self.repo/'code.txt').write_text(long)
        port.git(self.repo,'add','-A');port.git(self.repo,'commit','-m','large base')
        base=port.text(self.repo,'rev-parse','HEAD')
        (self.repo/'code.txt').write_text(long.replace('line4\n','INFINITY\n'))
        first=port.snapshot(self.repo,'01',self.patches)
        candidate=self.candidate(base)
        (candidate/'code.txt').write_text(long.replace('line80\n','UPSTREAM\n'))
        port.git(candidate,'add','-A');port.git(candidate,'commit','-m','upstream')
        _,clean=port.replay(candidate,[first],self.patches,self.logs)
        self.assertTrue(clean)
        self.assertIn('INFINITY\n',(candidate/'code.txt').read_text())
        self.assertIn('UPSTREAM\n',(candidate/'code.txt').read_text())


class Contracts(unittest.TestCase):
    def test_pin_delivered_rc3_not_alternative_or_rc2(self):
        self.assertEqual(BASELINE['runtime']['source_commit'],'5f7d9b311568cca053d9c0e082463baca1bd99e0')
        self.assertEqual(BASELINE['runtime']['version_code'],2103138)
        self.assertEqual(BASELINE['skin']['version'],'1.0.5.141')
        self.assertEqual(BASELINE['health_center']['version'],'2.5.6')
    def test_required_source_hashes_match_published_receipt(self):
        checks=json.loads((ROOT/'rc3-source-checks.json').read_text())
        self.assertEqual(checks['files']['tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'],
                         '89160ac6e5f532faf5963fb34012afa3db55297d2673e755f0c248f4eee9e5d2')
        self.assertEqual(len(checks['files']),7)
    def test_recipe_includes_lifecycle_as_last_layer(self):
        phases=json.loads((ROOT/'recipe.json').read_text())['phases']
        self.assertEqual(len(phases),11)
        self.assertIn('infinity_async_lifecycle_repair.py',' '.join(phases[-1]['argv']))
        for p in phases:
            for arg in p['argv']:
                arg.format_map(dict(source='/tmp/a',evidence='/tmp/b',recipe='/tmp/c',python='python3'))
    def test_never_approves_a_build_from_clean_replay(self):
        gates=port.review_gates()
        self.assertFalse(gates['automatic_build_allowed'])
        self.assertFalse(gates['automatic_install_allowed'])
        self.assertFalse(gates['release_ready'])
        self.assertEqual(gates['native_compile'],'not_run')
    def test_cross_file_api_changes_are_not_treated_as_safe(self):
        report=port.impact_report(['xbmc/guilib/new.cpp','tools/depends/foo'],['tools/android/a'])
        self.assertFalse(report['owned_file_intersections'])
        self.assertTrue(report['watch_areas']['renderer_fonts_graphics'])
        self.assertIn('NOT prove',report['note'])
    def test_workflows_have_no_signer_or_write_contents_or_auto_install(self):
        paths=list((ROOT.parent/'.github/workflows').glob('infinity-kodi-*.yml'))
        self.assertEqual(len(paths),3)
        for p in paths:
            txt=p.read_text()
            for forbidden in ['contents: write','secrets: inherit','INFINITY_KEYSTORE','pull_request_target','adb install']:
                self.assertNotIn(forbidden,txt)
            self.assertIn('persist-credentials: false',txt)
    def test_notification_scope_is_isolated(self):
        watcher=(ROOT.parent/'.github/workflows/infinity-kodi-watch.yml').read_text()
        self.assertEqual(watcher.count('issues: write'),1)
        self.assertIn("cron: '17 13 * * *'",watcher)
        self.assertIn("github.ref == 'refs/heads/main'",watcher)
    def test_recipe_checkout_is_pinned_to_delivered_rc3(self):
        self.assertRegex(BASELINE['runtime']['source_commit'], r'^[0-9a-f]{40}$')
        self.assertEqual(BASELINE['runtime']['source_commit'],
                         '5f7d9b311568cca053d9c0e082463baca1bd99e0')


if __name__ == '__main__':unittest.main()
