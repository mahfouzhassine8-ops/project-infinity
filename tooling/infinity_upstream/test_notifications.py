"""Notification delivery-contract tests, without writing fake upstream alerts."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import watch
import port


class TransportTests(unittest.TestCase):
    def test_disposable_git_never_spawns_background_maintenance(self):
        # Git 2.55 auto maintenance can race TemporaryDirectory cleanup.
        # Prevent the writer rather than hiding cleanup errors or skipping tests.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(port.git(root, 'config', '--get', 'maintenance.auto').strip(), b'false')
            self.assertEqual(port.git(root, 'config', '--get', 'gc.auto').strip(), b'0')

    def test_write_outside_notification_thread_rejected(self):
        for path in ('/repos/xbmc/xbmc/issues', '/repos/'+watch.REPOSITORY+'/issues',
                     '/repos/'+watch.REPOSITORY+'/issues/4/comments', '/repos/'+watch.REPOSITORY+'/git/refs'):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                watch.api(path, {'body':'never send'})

    def test_ambiguous_post_not_retried(self):
        for error in (URLError('response lost'), HTTPError('test',503,'temporary',{},None)):
            with self.subTest(error=error), patch.object(watch,'urlopen',side_effect=error) as mock:
                with self.assertRaises(RuntimeError): watch.api(watch.NOTICE_PATH, {'body':'test'})
                self.assertEqual(mock.call_count,1)

    def test_transient_get_retried(self):
        with patch.object(watch,'urlopen',side_effect=URLError('offline')) as mock, patch.object(watch.time,'sleep'):
            with self.assertRaises(RuntimeError): watch.api('/repos/xbmc/xbmc/releases')
            self.assertEqual(mock.call_count,3)

    def test_post_has_json_content_type(self):
        response=io.BytesIO(b'{"id":9}')
        response.url=watch.API+watch.NOTICE_PATH
        with patch.object(watch,'urlopen',return_value=response) as mock:
            result=watch.api(watch.NOTICE_PATH,{'body':'test'})
            request=mock.call_args.args[0]
            self.assertEqual(request.get_method(),'POST')
            self.assertEqual(request.get_header('Content-type'),'application/json')
            self.assertEqual(json.loads(request.data)['body'],'test')
            self.assertEqual(result['id'],9)

    def test_unrelated_public_comments_cannot_suppress_alerts(self):
        rows=[{'user':{'login':'other-user'},'body':'marker'},
              {'user':{'login':'github-actions[bot]'},'body':'official'}]
        with patch.object(watch,'pages',return_value=rows) as mock:
            self.assertEqual(watch.notification_history(),[rows[1]])
            mock.assert_called_once_with(watch.NOTICE_PATH)


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.baseline=json.loads((Path(__file__).parent/'baseline.json').read_text())
        self.target={'tag':'22.0-Piers','commit':'a'*40,'url':'https://github.com/xbmc/xbmc/releases/tag/22.0-Piers'}
        watch.save(self.root/'watch.json',{'baseline_id':self.baseline['id'],
                  'latest_stable':'22.0-Piers','new_stable_updates':[self.target]})
        self.setup_notice={'body':'<!-- infinity-upstream-watcher-activated:'+self.baseline['id']+' -->'}
        self.env=patch.dict(os.environ,{'GITHUB_REPOSITORY':watch.REPOSITORY,
                                      'GITHUB_REF':'refs/heads/main','GITHUB_RUN_ID':'1234'})
        self.env.start()
    def tearDown(self):
        self.env.stop();self.temp.cleanup()
    def invoke(self, issues=None, setup_exists=True):
        rows=list(issues or []) + ([self.setup_notice] if setup_exists else [])
        with patch.object(watch,'notification_history',return_value=rows), patch.object(watch,'resolve_target',return_value=self.target), patch.object(watch,'api',return_value={'html_url':'https://github.com/'+watch.REPOSITORY+'/pull/6#issuecomment-99'}) as mock:
            watch.notify(self.baseline,self.root)
            return mock.call_args_list
    def test_report_mentions_owner_and_approval_gate(self):
        report={'target':self.target,'upstream_changed_count':1000,'direct_overlap':['xbmc/example.cpp'],
                'replay':{'result':'blocked_on_conflict'}}
        watch.save(self.root/self.target['tag']/'impact.json',report)
        calls=self.invoke()
        self.assertEqual(len(calls),1)
        path,payload=calls[0].args
        self.assertEqual(path,watch.NOTICE_PATH)
        self.assertEqual(set(payload),{'body'})
        self.assertIn('@mahfouzhassine8-ops',payload['body'])
        self.assertIn('blocked_on_conflict',payload['body'])
        self.assertIn('No APK was built or installed',payload['body'])
        self.assertIn('must approve',payload['body'])
    def test_analysis_failure_still_alerts_truthfully(self):
        self.assertIn('Analysis did not complete',self.invoke()[0].args[1]['body'])
    def test_existing_notice_suppresses_repeat(self):
        notice={'body':watch.marker(self.target['tag'])+'\n<!-- upstream-commit:'+'a'*40+' -->'}
        self.assertEqual(self.invoke([notice]),[])
    def test_report_for_other_target_rejected_before_post(self):
        watch.save(self.root/self.target['tag']/'impact.json',{'target':{'commit':'b'*40}})
        with self.assertRaises(RuntimeError): self.invoke()
    def test_setup_notice_once_not_fake_update(self):
        watch.save(self.root/'watch.json',{'baseline_id':self.baseline['id'],
                  'latest_stable':'21.3-Omega','new_stable_updates':[]})
        calls=self.invoke(setup_exists=False)
        self.assertEqual(len(calls),1)
        self.assertIn('setup complete',calls[0].args[1]['body'])
        self.assertIn('not a new Kodi update',calls[0].args[1]['body'])
        self.assertEqual(self.invoke(),[])


if __name__ == '__main__': unittest.main()
