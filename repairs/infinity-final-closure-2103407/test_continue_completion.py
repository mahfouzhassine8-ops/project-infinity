"""Actual signed415 hub reproduction; exact catalogue progression, no deletes."""
import ast
from copy import deepcopy
import os
import re
import hashlib
import json
from pathlib import Path
from types import ModuleType,SimpleNamespace
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import patch_continue_completion as correction


def pure(raw):
    tree=ast.parse(raw);functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    selected={'next_episodes','progress_shows','record_progress','mark_watched_data','entries','identity_key','media_identity'}
    while True:
        needed={n.id for name in selected for n in ast.walk(functions[name]) if isinstance(n,ast.Name)}&functions.keys()
        if needed<=selected:break
        selected|=needed
    assert not selected & {'save','load','load_view','publish_home','atomic_json','queue_kodi_sync'}
    constants={'SCHEMA','KEY_RE','BUCKET_LIMITS'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected or
           isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
    scope={};exec('from copy import deepcopy\nimport json,re,time,hashlib\n',scope)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-hub.py','exec'),scope)
    return SimpleNamespace(**scope)


class ContinueCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(os.environ['INFINITY_COMPLETION_PARENT_APK']) as z:
            cls.raw={n:z.read('assets/addons/'+correction.CC+'/'+n) for n in ('service.py','resume_hub.py','addon.xml')}
        cls.updated={n:correction.patch(n,raw) for n,raw in cls.raw.items()}
        cls.before=pure(cls.raw['resume_hub.py']);cls.after=pure(cls.updated['resume_hub.py'])

    def entry(self,**extra):
        identity=self.after.media_identity('tv',{},1,2,{'tmdb':'1396'})
        value=dict(key=self.after.identity_key(identity),identity=identity,media='tv',season=1,episode=2,
            title='Breaking Bad',showtitle='Breaking Bad',show_ids_verified=True,show_tmdb='1396',
            position=70,duration=180,updated=1,playback_occurrence='1'*32,
            source='plugin://original/verified-episode-action',stable_source='plugin://original/captured-action',
            verified_next=dict(verified=True,after=[1,2],show_tmdb='1396',season=2,episode=1))
        value.update(extra);return value

    def test_original_bug_reproduces_and_completed_aliases_remain_stored_but_not_next(self):
        entry=self.entry();key=entry['key'];alias='b'*64
        saved=dict(entry,key='c'*64)
        data=dict(schema=2,items={key:entry,alias:dict(entry,key=alias)},
                  watchlist={'c'*64:saved},collection={'c'*64:saved},
                  lists={'later':{'c'*64:saved}},sources={'c'*64:{'route':'plugin://original/retained'}},
                  navigation_recovery={'saved':{'route':'retained'}})
        for hub in (self.before,self.after):
            complete,_=hub.mark_watched_data(deepcopy(data),key,entry,completed=True)
            self.assertEqual(complete['items'],data['items'])
            for bucket in ('watchlist','collection','lists','sources','navigation_recovery'):
                self.assertEqual(complete[bucket],data[bucket])
            self.assertEqual(hub.entries(complete,'tv'),[])
            nxt=hub.next_episodes(complete);progress=hub.progress_shows(complete)
            self.assertEqual(len(nxt),1);self.assertEqual(len(progress),1)
            if hub is self.before:
                self.assertEqual((nxt[0]['season'],nxt[0]['episode']),(1,2))
                self.assertEqual(progress[0]['position'],70)
            else:
                self.assertEqual((nxt[0]['season'],nxt[0]['episode']),(2,1))
                self.assertTrue(nxt[0]['synthetic_next']);self.assertFalse(nxt[0].get('watched'))
                for field in ('source','stable_source','dbid','poster','duration'):
                    self.assertNotIn(field,nxt[0])
                self.assertTrue(progress[0]['watched']);self.assertEqual(progress[0]['percentage'],100)

    def test_existing_exact_aliases_gain_only_verified_catalogue_proof_and_keep_routes(self):
        incoming=self.entry();old=dict(incoming);old.pop('verified_next');old['information']={'plot':'Full saved synopsis','premiered':'2008-01-20'}
        key=old['key'];alias='b'*64;data=dict(schema=2,items={key:old,alias:dict(old,key=alias)})
        before,_=self.before.record_progress(deepcopy(data),incoming)
        self.assertNotIn('verified_next',before['items'][key])
        after,_=self.after.record_progress(deepcopy(data),incoming)
        for k in (key,alias):
            self.assertEqual(after['items'][k]['verified_next'],incoming['verified_next'])
            for field in ('source','stable_source','identity','information'):
                self.assertEqual(after['items'][k][field],data['items'][k][field])

    def test_unverified_conflicting_or_backward_successors_never_gain_authority(self):
        good=self.entry();key=good['key'];old=dict(good);old.pop('verified_next')
        invalids=[dict(verified=False),dict(after=[1,3]),dict(show_tmdb='999'),dict(season=1,episode=1),
                  dict(season=-1),dict(season=0,episode=3)]
        for change in invalids:
            incoming=dict(good,verified_next=dict(good['verified_next'],**change))
            for data in (dict(schema=2,items={key:old}),dict(schema=2,items={})):
                after,_=self.after.record_progress(deepcopy(data),incoming)
                self.assertNotIn('verified_next',after['items'][key])
        for incoming in (dict(good,show_ids_verified=False),dict(good,show_tmdb='999')):
            after,_=self.after.record_progress(dict(schema=2,items={key:old}),incoming)
            self.assertNotIn('verified_next',after['items'][key])

    def test_unfinished_visible_episode_stays_next_and_hidden_no_proof_never_guesses(self):
        e=self.entry();e.pop('verified_next');data=dict(schema=2,items={e['key']:e})
        self.assertEqual(self.after.next_episodes(data)[0]['episode'],2)
        complete,_=self.after.mark_watched_data(data,e['key'],e,completed=True)
        self.assertEqual(self.after.next_episodes(complete),[])

    def test_native_zero_date_only_is_omitted_and_exact_patch_inverse(self):
        for n,raw in self.raw.items():
            inverse=self.updated[n].decode()
            for old,new in reversed(correction.substitutions(n)):inverse=inverse.replace(new,old,1)
            self.assertEqual(inverse.encode(),raw)
            with self.assertRaises(ValueError):correction.patch(n,raw+b'\n')
        tree=ast.parse(self.updated['service.py'])
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_continue_native_item')
        guard=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and "1601-01-01" in ast.unparse(n))
        for date in ('1601-01-01','2008-01-20'):
            scope=dict(information={'premiered':date,'plot':'Full synopsis'})
            exec(compile(ast.Module(body=[guard],type_ignores=[]),'actual-native-date','exec'),scope)
            self.assertEqual(scope['information'].get('premiered'),None if date=='1601-01-01' else date)
            self.assertEqual(scope['information']['plot'],'Full synopsis')


if __name__=='__main__':unittest.main(verbosity=2)
