import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('action_loading',ROOT/'overlay/script.infinity.commandcenter/action_loading.py')
loading=importlib.util.module_from_spec(spec);spec.loader.exec_module(loading)

def context(**kw):
    value=dict(allowed=True,window=10000,control=9000,item='1',profile='Main',geometry='1080|2400',
               dialog=0,playback='',busy=False,framed=True)
    value.update(kw);return value

def start(token='a'*32, foreground=True, owner=None, **extra):
    value=dict(token=token,born=0.0,state='preparing',target='d'*64,foreground=foreground,
               owner=context() if owner is None else owner)
    value.update(extra);return value

class LoadingOwnershipTest(unittest.TestCase):
    def test_fast_and_completed_empty_never_flash(self):
        s=loading.LoadingState();c=context();s.event(start(),0,c)
        self.assertEqual('pending',s.action['state'])
        s.event(dict(token='a'*32,state='ready'),.03,c)
        self.assertEqual('false',s.tick(.5,c)['Active'])
        self.assertEqual('false',s.presentation(.5)['Global'])
        self.assertEqual('ready',s.retired['a'*32])

    def test_slow_exact_item_and_failed_state_retire(self):
        s=loading.LoadingState();c=context();s.event(start(),0,c)
        visible=s.tick(.2,c)
        self.assertEqual(('true','false','9000','1'),tuple(visible[k] for k in ('Active','Global','Control','Item')))
        s.event(dict(token='a'*32,state='failed'),1,c)
        self.assertEqual('failed',s.retired['a'*32]);self.assertEqual('false',s.tick(1,c)['Active'])

    def test_superseded_completion_cannot_clear_new_action(self):
        s=loading.LoadingState();c=context();s.event(start(),0,c);s.event(start('b'*32,born=.1),.1,c)
        s.event(dict(token='a'*32,state='ready'),.2,c)
        self.assertEqual('b'*32,s.tick(.5,c)['Token'])
        s.event(start(),.6,c);self.assertEqual('b'*32,s.action['token'])

    def test_back_context_focus_profile_fold_and_new_playback_clear(self):
        for changed in (dict(window=10025),dict(control=9200),dict(item='2'),dict(profile='Kids'),
                        dict(geometry='2208|1840'),dict(dialog=10100),dict(playback='playing-new-title'),dict(allowed=False)):
            with self.subTest(changed=changed):
                s=loading.LoadingState();c=context();s.event(start(),0,c)
                self.assertEqual('false',s.tick(.5,context(**changed))['Active'])
                self.assertIsNone(s.action)
                s.event(start(),1,context(**changed));self.assertIsNone(s.action)

    def test_existing_background_playback_is_not_canceled(self):
        c=context(playback='existing-title');s=loading.LoadingState();s.event(start(owner=c),0,c)
        self.assertEqual('true',s.tick(.5,c)['Active'])
        self.assertEqual('false',s.tick(1,context(playback='new-title'))['Active'])

    def test_busy_dialog_does_not_steal_owner_native_end_clears_navigation(self):
        s=loading.LoadingState();c=context();s.event(start(navigation=True),0,c)
        busy=context(dialog=10138,busy=True)
        self.assertEqual('true',s.tick(.5,busy)['Active'])
        self.assertEqual('false',s.tick(1,c)['Active'])

    def test_background_overlap_drawer_and_primary_precedence(self):
        s=loading.LoadingState();c=context();s.event(start(foreground=False),0,c);s.event(start('b'*32,False),0,c)
        self.assertEqual('true',s.tick(.5,c)['Global']);s.event(dict(token='a'*32,state='ready'),.6,c)
        self.assertEqual('true',s.tick(.7,c)['Global'])
        s.event(start('c'*32,born=.7),.7,c);self.assertEqual(('true','false'),tuple(s.tick(1,c)[k] for k in ('Active','Global')))
        s.event(dict(token='c'*32,state='canceled'),1,c);self.assertEqual('true',s.tick(1.1,c)['Global'])
        s.event(dict(token='b'*32,state='ready'),1.2,c);self.assertEqual('false',s.tick(1.3,c)['Global'])

    def test_no_suitable_item_frame_uses_truthful_global_cue(self):
        c=context(framed=False);s=loading.LoadingState();s.event(start(owner=c),0,c)
        self.assertEqual(('false','true'),tuple(s.tick(.5,c)[k] for k in ('Active','Global')))

    def test_stale_owner_never_becomes_a_global_job(self):
        s=loading.LoadingState();s.event(start(),0,context(item='9'))
        self.assertIsNone(s.action);self.assertEqual({},s.jobs)
        self.assertEqual('false',s.tick(.5,context(item='9'))['Global'])

    def test_cancellation_before_start_and_duplicate_start_are_idempotent(self):
        s=loading.LoadingState();c=context();s.event(dict(token='a'*32,state='canceled'),0,c)
        s.event(start(),.1,c);self.assertIsNone(s.action)
        s.event(start('b'*32,False),0,c);s.event(start('b'*32,False),1,c)
        self.assertEqual(1,len(s.jobs));self.assertEqual(0,s.jobs['b'*32]['started'])

    def test_evicted_terminal_token_still_cannot_revive_old_work(self):
        s=loading.LoadingState();c=context()
        for i in range(400):
            born=float(i);token='%032x'%i
            s.event(start(token,False,born=born),born,c)
            s.event(dict(token=token,state='ready',sent=born+.1),born+.1,c)
        self.assertNotIn('%032x'%0,s.retired)
        s.event(start('%032x'%0,False,born=0),401,c)
        self.assertEqual(0,len(s.jobs))
        s.event(start('f'*32,False,born=401),401,c)
        self.assertEqual(1,len(s.jobs))

    def test_observation_budget_bounds_memory_without_work_or_fake_success(self):
        s=loading.LoadingState();c=context()
        for i in range(400):s.event(start('%032x'%i,False),0,c)
        self.assertEqual(loading.MAX_JOBS,len(s.jobs))
        s.tick(loading.OBSERVATION_LIMIT+.1,c)
        self.assertEqual(0,len(s.jobs));self.assertLessEqual(len(s.retired),loading.MAX_RETIRED)
        self.assertNotIn('ready',s.retired.values())

if __name__=='__main__':unittest.main()
