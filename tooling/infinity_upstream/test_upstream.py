"""Offline regression tests; real same-base source replay is a separate CI job."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import port
import watch


def release(tag, number=1, **kw):
    data = {'tag_name':tag, 'id':number, 'draft':False, 'prerelease':False,
            'published_at':'2026-09-16T00:00:00Z'}
    data.update(kw)
    return data


class ReleaseTests(unittest.TestCase):
    def test_numeric_order_not_strings(self):
        rows = [release('21.9-Omega'),release('22.0-Piers'),release('21.10-Omega'),release('21.3-Omega')]
        self.assertEqual([r['tag_name'] for r in watch.stable_releases(rows,[21,3,0])],
                         ['21.9-Omega','21.10-Omega','22.0-Piers'])
    def test_draft_prerelease_nightly_never_stable(self):
        rows = [release('22.0-Piers',draft=True), release('23.0-Q',prerelease=True),
                release('22.0b2-Piers'),release('22.0rc1-Piers'),release('master'),
                release('22.0a3-Piers'),release('Piers'),release('22.0-Piers',published_at=None)]
        self.assertEqual(watch.stable_releases(rows,[21,3,0]), [])
    def test_schema_missing_flags_is_not_stable(self):
        row = release('22.0-Piers');del row['prerelease']
        self.assertEqual(watch.stable_releases([row],[21,3,0]), [])
    def test_v_and_patch_version(self):
        self.assertEqual(watch.version('v22.0.1-Piers'),(22,0,1))
    def test_unsafe_tags(self):
        for tag in ['../main','--upload-pack=evil','22.0-Piers\nrun','$(touch x)', '22.0;rm', 'refs/heads/main']:
            with self.subTest(tag=tag), self.assertRaises(RuntimeError):
                watch.resolve_target(tag)
    def test_dedupe(self):
        rows = [release('21.4-Omega'),release('21.4-Omega')]
        self.assertEqual(len(watch.stable_releases(rows,[21,3,0])), 1)
    def test_tag_lookup_not_target_commitish(self):
        row=release('22.0-Piers'); row['target_commitish']='master'
        with patch.object(watch,'api',side_effect=[row,{'object':{'type':'commit','sha':'a'*40}}]) as mock:
            self.assertEqual(watch.resolve_target('22.0-Piers')['commit'],'a'*40)
            self.assertIn('/git/ref/tags/22.0-Piers',mock.call_args_list[-1].args[0])
    def test_annotated_tag_peeled(self):
        with patch.object(watch,'api',side_effect=[{'object':{'type':'tag','sha':'b'*40}},
                                                 {'object':{'type':'commit','sha':'a'*40}}]):
            self.assertEqual(watch.tag_commit('21.3-Omega'),'a'*40)
    def test_unpublished_tag_fails(self):
        with patch.object(watch,'api',return_value=release('22.0-Piers',draft=True)), self.assertRaises(RuntimeError):
            watch.resolve_target('22.0-Piers')
    def test_beta_opt_in_only(self):
        row=release('22.0b2-Piers',prerelease=True)
        with patch.object(watch,'api',return_value=row), self.assertRaises(RuntimeError):
            watch.resolve_target('22.0b2-Piers')
        with patch.object(watch,'api',side_effect=[row,{'object':{'type':'commit','sha':'a'*40}}]):
            self.assertTrue(watch.resolve_target('22.0b2-Piers',True)['prerelease'])
    def test_base_newer_or_same_not_notified(self):
        self.assertEqual(watch.stable_releases([release('20.5-Nexus'),release('21.3-Omega')],[21,3,0]),[])
    def test_full_pagination(self):
        with patch.object(watch,'api',side_effect=[[{}]*100,[{}]*7]):
            self.assertEqual(len(watch.pages('/repos/xbmc/xbmc/releases')),107)
    def test_pagination_limit_not_no_updates(self):
        with patch.object(watch,'api',return_value=[{}]*100), self.assertRaises(RuntimeError):
            watch.pages('/repos/xbmc/xbmc/releases',maximum=2)
    def test_api_failure_propagates(self):
        with patch.object(watch,'api',side_effect=RuntimeError('403')), self.assertRaises(RuntimeError):
            watch.pages('/repos/xbmc/xbmc/releases')
    def test_closed_issue_deduplicated(self):
        target={'tag':'22.0-Piers','commit':'a'*40}
        row={'state':'closed','number':4,'body':watch.marker(target['tag'])+'\n<!-- upstream-commit:'+'a'*40+' -->'}
        self.assertEqual(watch.existing_issue([row],target)['number'],4)
    def test_moved_tag_rejected(self):
        target={'tag':'22.0-Piers','commit':'b'*40}
        row={'body':watch.marker(target['tag'])+'\n<!-- upstream-commit:'+'a'*40+' -->'}
        with self.assertRaises(RuntimeError): watch.existing_issue([row],target)
    def test_pr_not_mistaken_for_update_issue(self):
        self.assertIsNone(watch.existing_issue([{'pull_request':{'url':'x'},'body':watch.marker('22.0-Piers')}],
                                             {'tag':'22.0-Piers','commit':'b'*40}))
    def test_notify_rejects_branch_and_other_repo(self):
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':watch.REPOSITORY,'GITHUB_REF':'refs/heads/test'}), self.assertRaises(RuntimeError):
            watch.notify({},Path('/missing'))


class PortTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.source=self.root/'source';self.source.mkdir()
        port.git(self.source,'init','-q')
        port.git(self.source,'config','user.name','Test')
        port.git(self.source,'config','user.email','test@example.invalid')
        (self.source/'shared.txt').write_text('base\n')
        (self.source/'upstream-only.txt').write_text('base\n')
        port.git(self.source,'add','.')
        port.git(self.source,'commit','-qm','Base')
        self.base=port.revision(self.source)
        self.out=self.root/'out';self.out.mkdir();(self.out/'patches').mkdir()
    def tearDown(self): self.tmp.cleanup()
    def make_patch(self):
        (self.source/'shared.txt').write_text('Infinity\n')
        (self.source/'helper.txt').write_text('New Infinity helper\n')
        return port.checkpoint(self.source,'01-test',self.out/'patches')
    def test_same_base_roundtrip(self):
        row=self.make_patch(); expected=port.revision(self.source,'HEAD^{tree}')
        result=port.replay(self.source,self.base,[row],self.out)
        self.assertEqual(result['candidate_tree'],expected)
        self.assertFalse(result['build_allowed'])
        self.assertFalse(result['runtime_tested'])
    def test_upstream_only_fix_retained(self):
        row=self.make_patch()
        port.git(self.source,'checkout','--detach',self.base)
        (self.source/'upstream-only.txt').write_text('Upstream security fix\n')
        port.git(self.source,'add','.');port.git(self.source,'commit','-qm','Upstream fix')
        result=port.replay(self.source,port.revision(self.source),[row],self.out)
        self.assertEqual(result['result'],'textual_replay_complete_review_required')
        self.assertEqual((self.root/'candidate/upstream-only.txt').read_text(),'Upstream security fix\n')
        self.assertEqual((self.root/'candidate/helper.txt').read_text(),'New Infinity helper\n')
    def test_conflict_stops_and_does_not_emit_candidate_zip(self):
        row=self.make_patch()
        port.git(self.source,'checkout','--detach',self.base)
        (self.source/'shared.txt').write_text('Conflicting upstream fix\n')
        port.git(self.source,'add','.');port.git(self.source,'commit','-qm','Upstream conflicting')
        result=port.replay(self.source,port.revision(self.source),[row],self.out)
        self.assertEqual(result['result'],'blocked_on_conflict')
        self.assertIn('shared.txt',result['stages'][0]['conflict_files'])
        self.assertFalse((self.out/'candidate-source.zip').exists())
    def test_corrupt_patch_fails_closed(self):
        row=self.make_patch();(self.out/'patches'/row['patch']).write_text('tampered')
        with self.assertRaises(RuntimeError): port.replay(self.source,self.base,[row],self.out)
    def test_no_existing_workspace_erased(self):
        p=self.root/'production';p.mkdir();(p/'important').write_text('keep')
        with self.assertRaises(RuntimeError): port.safe_new_directory(p)
        self.assertEqual((p/'important').read_text(),'keep')
    def test_renamed_owned_file_includes_old_and_new_paths(self):
        (self.source/'shared.txt').rename(self.source/'moved.txt')
        port.git(self.source,'add','-A');port.git(self.source,'commit','-qm','rename')
        self.assertEqual(port.changed_paths(self.source,self.base,'HEAD'),['moved.txt','shared.txt'])
    def test_more_than_300_files_not_truncated(self):
        for i in range(310): (self.source/f'f{i}.txt').write_text(str(i))
        port.git(self.source,'add','.');port.git(self.source,'commit','-qm','Large upstream release')
        self.assertEqual(len(port.changed_paths(self.source,self.base,'HEAD')),310)
    def test_ownership_and_risk_domains(self):
        self.assertEqual(port.classify('tools/android/packaging/xbmc/src/Main.java.in'),'android-runtime-and-packaging')
        self.assertEqual(port.classify('xbmc/guilib/GUIFontCache.cpp'),'native-engine-delta')
        domains=port.risk_domains(['xbmc/guilib/GUIFontCache.cpp','tools/depends/target/python3/Makefile'])
        self.assertIn('renderer-font-cache',domains);self.assertIn('toolchain-and-dependencies',domains)
    def test_locked_baseline_policy(self):
        data=json.loads((Path(__file__).parent/'baseline.json').read_text())
        self.assertFalse(data['candidate_build']['enabled'])
        self.assertEqual(len(data['protected_artifacts']['apk']['sha256']),64)
        self.assertEqual(data['runtime']['source_commit'],'5f7d9b311568cca053d9c0e082463baca1bd99e0')
        self.assertEqual(data['companions']['skin'],'1.0.5.141')
        self.assertEqual(data['companions']['health_center'],'2.5.6')
        self.assertFalse(data['policy']['automatic_install'])
        self.assertFalse(data['policy']['automatic_merge'])
        self.assertFalse(data['policy']['automatic_baseline_promotion'])
        self.assertEqual(len(data['runtime']['source_receipt_sha256']),7)


if __name__=='__main__': unittest.main()
