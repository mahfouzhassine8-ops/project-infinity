"""Focused local Trakt ingress/actions and reciprocal release contracts. Kodi mocked."""
import argparse, hashlib, json, shutil, sys, types, unittest
from pathlib import Path
from unittest.mock import patch
import test_recovery as fixture

class Tracking(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Recovery('test_unknown_or_conflicting_identity_never_reuses_memory');self.f.setUp();self.addCleanup(self.f.doCleanups)
        f=self.f;self.base=fixture.BASE;cc=self.base/'script.infinity.commandcenter'
        sys.modules['common'].__file__=str(cc/'common.py')
        for name in ('controller','bridge_state','provider_contracts','context'):sys.modules.pop(name,None)
        sys.modules['xbmcvfs'].translatePath=lambda p:p
        versions={'script.infinity.commandcenter':'0.3.5.32','script.infinity.watchedbridge':'1.0.13','script.infinity.uirepair':'0.1.15'}
        sys.modules['xbmcaddon'].Addon=lambda aid:types.SimpleNamespace(getAddonInfo=lambda key:{'id':aid,'path':str(self.base/aid),'version':versions[aid]}[key])
        self.trakt=fixture.load('infinity_trakt',cc/'infinity_trakt.py');self.bridge,self.modules=self.trakt._bridge()
        self.pick=0;sys.modules['infinity_settings']=types.SimpleNamespace(choose=lambda *a:self.pick)
        self.notices=[];self.trakt.notice=lambda *a:self.notices.append(a)
        f.path.write_text(json.dumps({'schema':2,'items':{},'watched':{},'sources':{},'watchlist':{},'later':{},'collection':{}}))
        self.item=self.movie_item();self.entry=self.trakt.selected(self.item,self.bridge,self.modules)
    def movie_item(self):
        tag=types.SimpleNamespace(getMediaType=lambda:'movie',getUniqueID=lambda n:{'tmdb':'123456','imdb':'tt1234567'}.get(n,''),getDbId=lambda:-1,getTitle=lambda:'Exact movie',getPlayCount=lambda:0)
        return types.SimpleNamespace(getVideoInfoTag=lambda:tag,isFolder=lambda:False,getPath=lambda:'plugin://plugin.video.pov/?mode=play&tmdb_id=123456',getLabel=lambda:'Exact movie',getArt=lambda n:'')
    def data(self):return json.loads(self.f.path.read_text())
    def action(self,action):
        self.pick=[a for _,a in self.trakt.ACTIONS].index(action);self.trakt.main(self.item);self.assertFalse(self.notices)
    def test_search_long_press_movie_actions_round_trip(self):
        key=self.entry['key']
        for action,bucket in [('add-watchlist','watchlist'),('save-later','later')]:
            self.action(action);self.assertEqual(self.data()[bucket][key]['source'],self.entry['source'])
            self.assertEqual(self.f.plugin.navigation_target(self.data()[bucket][key],self.data(),bucket),self.entry['source'])
        self.action('mark-watched');self.assertIn(key,self.data()['watched'])
        self.action('mark-unwatched');self.assertNotIn(key,self.data()['watched']);self.assertIn(key,self.data()['infinity_watched_overrides'])
        self.action('remove-watchlist');self.action('remove-later');self.assertNotIn(key,self.data()['watchlist']);self.assertNotIn(key,self.data()['later'])
    def test_show_membership_and_watched_do_not_touch_episode_history(self):
        entry=dict(self.f.entry,key=self.f.hub.identity_key(self.f.entry['identity']))
        for action in ('add-watchlist','save-later','mark-watched','mark-unwatched','remove-watchlist','remove-later'):
            self.assertTrue(self.trakt.apply_local(self.f.root,entry,action))
        self.assertEqual(self.data()['items'],{})
    def test_tracking_add_retains_all_existing_progress_and_history(self):
        data=self.data();data['items']={hashlib.sha256(str(i).encode()).hexdigest():dict(self.entry,position=i,updated=i) for i in range(160)}
        data['watched']={hashlib.sha256(('w'+str(i)).encode()).hexdigest():dict(self.entry,updated=i) for i in range(520)}
        data['navigation_recovery']={'retained':{'route':'original'}};self.f.path.write_text(json.dumps(data))
        self.action('add-watchlist');after=self.data()
        for field in ('items','watched','navigation_recovery'):self.assertEqual(after[field],data[field])
    def test_exact_contract_rejects_tampered_controller_and_old_versions(self):
        with patch.object(self.bridge.controller,'verify',side_effect=self.bridge.controller.UnsupportedController('changed code')):
            with self.assertRaises(RuntimeError):self.trakt._bridge()
        addon=types.SimpleNamespace(getAddonInfo=lambda k:{'id':'script.infinity.commandcenter','path':str(self.base/'script.infinity.commandcenter'),'version':'0.3.5.31'}[k])
        with self.assertRaises(RuntimeError):self.trakt._verified_component(addon,'script.infinity.commandcenter','0.3.5.32')
        cc=self.base/'script.infinity.commandcenter';pins=json.loads((self.base/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
        self.assertEqual(pins,json.loads((self.base/'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json').read_text()))
        self.assertEqual(len(pins),19)
        for name,digest in pins.items():self.assertEqual(hashlib.sha256((cc/name).read_bytes()).hexdigest(),digest)
        for name,digest in self.trakt.BRIDGE_PINS.items():self.assertEqual(hashlib.sha256((self.base/'script.infinity.watchedbridge'/name).read_bytes()).hexdigest(),digest)
    def test_unrelated_saved_identity_and_unreadable_file_never_mutate(self):
        self.f.path.write_text('{broken');before=self.f.path.read_bytes()
        with self.assertRaises(RuntimeError):self.trakt.apply_local(self.f.root,self.entry,'add-watchlist')
        self.assertEqual(self.f.path.read_bytes(),before)
    def test_pending_library_operation_is_retained_and_not_run_by_new_action(self):
        data=self.data();data['pending_kodi_sync']={'old':{'operation':'old'}};self.f.path.write_text(json.dumps(data));before=self.f.path.read_bytes()
        with self.assertRaises(RuntimeError):self.bridge.controller.apply(self.modules,self.f.root,self.entry,'add-watchlist')
        self.assertEqual(before,self.f.path.read_bytes())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();fixture.BASE=a.base.resolve()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tracking))
    a.out.write_text(json.dumps(dict(scope='local Trakt actions and exact release contract',host='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),kodi_api='mocked',android='NOT RUN',physical_fold='NOT RUN',external_trakt='NOT RUN; local tracking only',shutdown='NOT RUN'),indent=2)+'\n');sys.exit(not result.wasSuccessful())
