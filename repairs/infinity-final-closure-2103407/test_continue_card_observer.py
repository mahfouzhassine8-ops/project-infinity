import json
import unittest
import continue_card_observer as observer


class ContinueCardObserverTests(unittest.TestCase):
    def test_exact_source_identity_position_episode_and_no_autoplay_required(self):
        prefix='Container(8831).ListItem.'
        entry=dict(key='d'*64,identity={'kind':'episode','ids':{'tmdb':'1396'},'season':1,'episode':2},
                   source='special://profile/test.mp4',stable_source='special://profile/test.mp4',
                   media='tv',season=1,episode=2,position=60.125,duration=180)
        capsule={k:entry[k] for k in ('key','identity','source','stable_source')}
        labels={prefix+'Property(Infinity.Selection.Snapshot)':json.dumps(capsule),
                prefix+'Property(ResumeTime)':'60.125',prefix+'Property(StartOffset)':'60.125',
                prefix+'Property(TotalTime)':'180',prefix+'Property(Infinity.ResumeHub.Watched)':'false',
                prefix+'Season':'1',prefix+'Episode':'2'}
        observer.verify_card(entry,labels,prefix,False)
        for field,value in [('Property(ResumeTime)','60'),('Property(StartOffset)','0'),
                            ('Property(TotalTime)','nan'),('Property(Infinity.ResumeHub.Watched)','true'),
                            ('Season','2'),('Episode','3'),
                            ('Property(Infinity.Selection.Snapshot)',json.dumps(dict(capsule,key='e'*64)))]:
            with self.assertRaises(AssertionError):observer.verify_card(entry,dict(labels,**{prefix+field:value}),prefix,False)
        with self.assertRaises(AssertionError):observer.verify_card(entry,labels,prefix,True)


if __name__=='__main__':unittest.main(verbosity=2)
