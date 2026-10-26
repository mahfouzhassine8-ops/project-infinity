import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import stress_resume_card as card
import android_stress_dispatcher as dispatcher
import sys


class StressResumeCardTests(unittest.TestCase):
    def test_empty_or_wrong_card_not_counted_and_exact_real_card_is_counted(self):
        key='b'*64;entry=dict(key=key,media='movie',identity={'kind':'movie','ids':{'tmdb':'603'}},
            source='special://profile/infinity-final-qa.mp4',stable_source='special://profile/infinity-final-qa.mp4',
            position=60,duration=180)
        prefix='Container(8830).ListItem.'
        actual={prefix+'Property(Infinity.Selection.Snapshot)':json.dumps({k:entry[k] for k in ('key','identity','source','stable_source')}),
            prefix+'PercentPlayed':'33',
            prefix+'Property(Infinity.ResumeHub.Watched)':'false','Container(8830).NumItems':'1'}
        count=[0]
        def rpc(method,params=None):
            if method=='XBMC.GetInfoBooleans':return {'Control.IsVisible(8830)':True}
            if method=='XBMC.GetInfoLabels':
                count[0]+=1
                if count[0]==1:return {'Container(8830).NumItems':'0'}
                if count[0]==2:return dict(actual,**{prefix+'Property(Infinity.Selection.Snapshot)':json.dumps({'key':'wrong'})})
                return actual
            if method=='Files.GetDirectory':return {'files':[{'resume':{'position':60,'total':180}}]}
            if method=='Player.GetActivePlayers':return []
            raise AssertionError(method)
        def until(fn,seconds):
            for _ in range(4):
                value=fn()
                if value:return value
            raise RuntimeError('No actual correct card')
        device=SimpleNamespace(rpc=rpc,until=until)
        with patch.object(card.dispatch,'launch') as launch,patch.object(card.dispatch,'verify_dispatch'), \
                patch('resume_native_rpc.read',return_value={'files':[{'resume':{'position':60,'total':180}}]}):
            result=card.observe(device,{'items':{key:entry}},'movie')
            self.assertTrue(result['exact_usable_card']);self.assertFalse(result['poster_paint_verified'])
            self.assertEqual(count[0],3);launch.assert_called_once_with(device,'home-resume-movie')
        with self.assertRaises(ValueError):card.observe(device,{},'movie')

    def test_fixed_tab_selection_requires_actual_home_and_matches_requested_media(self):
        selected=[0];calls=[]
        def builtin(command,wait):selected[0]=int(command.split(',')[1]);calls.append(command)
        xbmc=SimpleNamespace(executebuiltin=builtin,getInfoLabel=lambda key:'3' if key.endswith('NumItems') else
                            ['other','movies','tvshows'][selected[0]])
        gui=SimpleNamespace(getCurrentWindowId=lambda:10000)
        with patch.dict(sys.modules,{'xbmc':xbmc,'xbmcgui':gui}):
            dispatcher.select_resume_tab('movie');self.assertEqual(selected[0],1)
            dispatcher.select_resume_tab('tv');self.assertEqual(selected[0],2)
            gui.getCurrentWindowId=lambda:10025;before=list(calls)
            with self.assertRaises(ValueError):dispatcher.select_resume_tab('movie')
            self.assertEqual(calls,before)
            with self.assertRaises(ValueError):dispatcher.select_resume_tab('unreviewed')


if __name__=='__main__':unittest.main(verbosity=2)
