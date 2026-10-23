"""Actual Home Python route projection; no claim of rendered Fold acceptance."""
import argparse, copy, json, sys, types, unittest
from pathlib import Path
from unittest.mock import patch
import test_recovery as fixture

class Continue(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Recovery('test_unknown_or_conflicting_identity_never_reuses_memory');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.hub=fixture.load('resume_hub',Path(__file__).parent/'overlay/script.infinity.commandcenter/resume_hub.py');self.f.plugin.hub=self.f.hub
        self.data={'schema':2,'items':{},'watched':{},'sources':{}}
    def episode(self,key,ids,episode,updated,**extra):
        value=dict(key=key*64,media='tv',title='Same title',showtitle='Same title',season=1,episode=episode,position=123.456,duration=400,updated=updated,identity=self.f.hub.media_identity('tv',{},1,episode,ids),stable_source='plugin://plugin.video.umbrella/?action=play&tmdb=330430',source='original',**extra)
        self.data['items'][value['key']]=value;return value
    def test_actual_home_route_returns_one_card_newest_resume_keeps_records(self):
        self.episode('a',{'tmdb':'330430'},4,10);recent=self.episode('b',{'tmdb':'330430'},2,20)
        before=copy.deepcopy(self.data);self.f.hub.load_view=lambda p:self.data
        rows=[];pluginapi=sys.modules['xbmcplugin'];pluginapi.setContent=lambda *a:None;pluginapi.endOfDirectory=lambda *a,**kw:None
        pluginapi.addDirectoryItem=lambda h,t,item,**kw:rows.append((t,item))
        with patch.dict(sys.modules,{'controller_access':types.SimpleNamespace(load=lambda:self.f.plugin),'runtime':types.SimpleNamespace(addons=lambda:[],hidden=lambda x:False,destination=lambda x:None)}):
            with patch.object(sys,'argv',['plugin://script.infinity.uirepair/','1','?action=continue&media=tv']):
                route=fixture.load('actual_home_continue_plugin',fixture.BASE/'script.infinity.uirepair/plugin.py');route.main()
        self.assertEqual(len(rows),1);self.assertEqual(rows[0][1].properties['Infinity.ResumeHub.Key'],recent['key']);self.assertEqual(self.data,before)
        skin=fixture.BASE/'skin.infinity.diggz'
        xml=(skin/'unified/Includes_InfinityHomeUnified.xml').read_text();home=(skin/'5x6/Home.xml').read_text()
        self.assertIn('script.infinity.uirepair/?action=continue&amp;media=tv',xml);self.assertIn('$VAR[InfinityCompactContinueTVPath]',home);self.assertIn('home-choice',home)
    def test_conflicting_ids_titles_and_episode_scope_never_merge(self):
        self.episode('a',{'tmdb':'330430','imdb':'tt1111111'},1,20);self.episode('b',{'tmdb':'330430','imdb':'tt2222222'},2,10)
        c=self.episode('c',{'tmdb':'999'},3,30);c['identity']=self.f.hub.media_identity('tv',{'tmdb':'330430'},1,3)
        self.assertEqual(len(self.f.hub.entries(self.data,'tv')),3)
    def test_verified_parent_ids_can_group_native_episode_id_rows(self):
        for key,ep in [('a',1),('b',2)]:
            v=self.episode(key,{},ep,ep,show_ids_verified=True,show_tmdb='330430');v['identity']=self.f.hub.media_identity('tv',{'tmdb':str(100+ep)},1,ep)
        self.assertEqual(len(self.f.hub.entries(self.data,'tv')),1);self.assertEqual(len(self.data['items']),2)
    def test_movies_history_and_membership_lists_stay_individual(self):
        self.episode('a',{'tmdb':'330430'},1,20);self.episode('b',{'tmdb':'330430'},2,10)
        self.data['watched']=copy.deepcopy(self.data['items']);self.data['watchlist']=copy.deepcopy(self.data['items'])
        for key,tmdb in [('c','100'),('d','200')]:self.data['items'][key*64]={'key':key*64,'media':'movie','identity':self.f.hub.media_identity('movie',{'tmdb':tmdb}),'updated':1}
        self.assertEqual(len(self.f.hub.entries(self.data,'all')),3)
        self.assertEqual(len(self.f.hub.entries(self.data,'tv','watched')),2);self.assertEqual(len(self.f.hub.entries(self.data,'tv','watchlist')),2)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();fixture.BASE=a.base.resolve()
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Continue));a.out.write_text(json.dumps(dict(host='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,scope='actual UI Repair Home Continue directory and read-only TV series projection',android='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN'),indent=2)+'\n');sys.exit(not r.wasSuccessful())
