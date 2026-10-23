"""Only the authorized shared recovery/memory contract; no Android/shutdown claims."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

HERE=Path(__file__).resolve().parent
REPAIR=HERE.parent
BASE=None

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result)
    return result

class Item:
    def __init__(self,**kwargs):self.properties={};self.path=kwargs.get('path','')
    def setProperty(self,k,v):self.properties[k]=v
    def setInfo(self,*a):pass
    def setUniqueIDs(self,*a):pass
    def setArt(self,*a):pass
    def addContextMenuItems(self,*a):pass
    def setPath(self,path):self.path=path

class Recovery(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.props={};self.calls=[];self.lock=threading.RLock()
        self.home=types.SimpleNamespace(getProperty=lambda k:self.props.get(k,''),setProperty=self.props.__setitem__,clearProperty=lambda k:self.props.pop(k,None))
        @contextmanager
        def scope():
            with self.lock:yield
        def read(path,default):
            try:return json.loads(Path(path).read_text())
            except (OSError,ValueError):return default
        def atomic(path,data):Path(path).write_text(json.dumps(data,sort_keys=True))
        modules={n:types.ModuleType(n) for n in ('xbmc','xbmcaddon','xbmcgui','xbmcplugin','xbmcvfs','common','persistence_participant','experience')}
        self.xbmc=modules['xbmc'];self.xbmc.getSkinDir=lambda:'skin.infinity.diggz';self.xbmc.getCondVisibility=lambda *a:True
        self.xbmc.Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:False)
        self.xbmc.LOGINFO=1;self.xbmc.log=lambda *a:None;self.xbmc.executebuiltin=lambda *a:self.calls.append(a)
        self.xbmc.Player=lambda:types.SimpleNamespace(play=lambda target,item:self.calls.append((target,item)))
        gui=modules['xbmcgui'];gui.Window=lambda *a:self.home;gui.ListItem=Item;gui.getCurrentWindowId=lambda:10025
        self.selection=0;gui.Dialog=lambda:types.SimpleNamespace(select=lambda *a:self.selection,ok=lambda *a:self.calls.append(('notice',a)))
        gui.DialogProgress=lambda:types.SimpleNamespace(create=lambda *a:None,close=lambda:None,iscanceled=lambda:False)
        common=modules['common'];common.read_json=read;common.atomic_json=atomic;common.persistence_scope=scope
        common.addon_profile=lambda:self.root;common.setting_bool=lambda *a:True
        modules['persistence_participant'].AdmissionClosed=RuntimeError
        exp=modules['experience'];exp.artwork=lambda *a:a[0];exp.commands=lambda *a:[];exp.stable_route=lambda p:p
        exp.number=lambda v,default=0:float(v or default);exp.verified_source=lambda e,r:r or ''
        self.patch=patch.dict(sys.modules,modules);self.patch.start();self.addCleanup(self.patch.stop)
        self.hub=load('resume_hub',BASE/'script.infinity.commandcenter/resume_hub.py');self.hub.publish_home=lambda d:None
        self.search=load('infinity_search',BASE/'script.infinity.commandcenter/infinity_search.py')
        self.nav=load('saved_navigation',REPAIR/'saved_navigation.py')
        with patch.object(sys,'argv',['plugin.py','1','']):self.plugin=load('policy_controller_plugin',HERE/'overlay/script.infinity.commandcenter/plugin.py')
        self.entry=dict(key='a'*64,media='tv',title='Love After Lockup: Relationship Rehab',season=-1,episode=-1,
                       identity=self.hub.show_identity('tvshow',{'tmdb':'330430','imdb':'tt48447471'}),
                       source='plugin://plugin.video.pov/?mode=build_episode_list&season=all&tmdb_id=330430',stable_source='plugin://plugin.video.pov/?mode=build_episode_list&season=all&tmdb_id=330430')
        self.data=dict(schema=2,revision=3,later={self.entry['key']:deepcopy(self.entry)},watchlist={self.entry['key']:deepcopy(self.entry)},
                       items={'f'*64:dict(self.entry,key='f'*64,position=72)},watched={'old':{'unchanged':True}},sources={},
                       collection={'c':{'retained':True}},ratings={'r':{'rating':8}},lists={'old-list':{'x':{'kept':True}}},unknown_extension={'keep':[1,2,3]})
        self.path=self.root/self.hub.CONTINUE_FILE;atomic(self.path,self.data)
        self.provider=dict(id='plugin.video.umbrella',name='Umbrella',family='action-list-v1',root='/provider',contract={'pins':{'addon.xml':'1'*64},'params':{}})
        self.route='plugin://plugin.video.umbrella/?action=seasons&tmdb=330430&imdb=tt48447471'
        self.token='b'*32
        self.props['Infinity.SavedNavigation.Protocol']='2'

    def memory(self):return self.nav.remembered(json.loads(self.path.read_text()),self.entry['identity'])
    def pending(self,folder=True):
        identity=self.entry['identity'] if folder else self.hub.media_identity('movie',{'tmdb':'603'})
        entry=self.entry if folder else dict(self.entry,media='movie',identity=identity)
        if not folder:
            for bucket in ['later','watchlist']:self.data[bucket][entry['key']]=entry
            self.path.write_text(json.dumps(self.data))
        p=dict(key=entry['key'],token=self.token,bucket='later',identity=identity,route=self.route,
               original=entry['source'],provider=self.provider,source_snapshot=self.nav._source_snapshot(entry))
        success=dict(schema=2,key=entry['key'],token=self.token,bucket='later',folder=folder,
                     original_sha256=self.nav._hash(entry['source']),destination_sha256=self.nav._hash(self.route),
                     phase='directory_opened' if folder else 'media_resolved',identity_verified=True,epoch_ms=int(time.time()*1000))
        self.props['Infinity.SavedNavigation.Pending']=json.dumps(p);self.props['Infinity.SavedNavigation.Success']=json.dumps(success)
        return p,success
    def confirm(self,**kwargs):
        with patch.object(self.nav,'_provider_current',return_value=self.provider):return self.nav.confirm_saved(self.root,self.entry['key'],self.token,**kwargs)

    def test_working_originals_do_not_discover_or_change_route(self):
        movie=dict(self.entry,media='movie',identity=self.hub.media_identity('movie',{'tmdb':'603'}))
        for entry in (self.entry,movie):
            for bucket in ('later','watchlist','continue'):
                with self.subTest(media=entry['media'],bucket=bucket),patch.object(self.nav,'available',side_effect=AssertionError('unrequested discovery')):
                    self.assertEqual(self.nav.navigation_target(entry,self.data,entry['source'],bucket),entry['source'])
        before=self.path.read_bytes()
        with patch.object(self.nav,'navigation_target',side_effect=AssertionError('original route imported recovery')):
            target,_=self.plugin._list_item(self.entry,self.data,'later')
        self.assertEqual(target,self.entry['source']);self.assertEqual(self.path.read_bytes(),before)

    def test_native_failure_uses_same_explicit_recovery_for_each_list(self):
        for bucket in ('later','watchlist'):
            with self.subTest(bucket=bucket):
                failure=dict(schema=1,key=self.entry['key'],token=self.token,bucket=bucket,
                    original_sha256=self.nav._hash(self.entry['source']),failed_sha256=self.nav._hash(self.entry['source']),
                    folder=True,reason='provider_directory_failed',epoch_ms=int(time.time()*1000),attempted=['plugin.video.pov'])
                self.props['Infinity.SavedNavigation.Failure']=json.dumps(failure)
                with patch.object(self.nav,'available',return_value=([self.provider],[])),patch.object(self.nav,'direct_destination',return_value=self.route),patch.object(self.search,'route',return_value=self.route):
                    self.nav.recover_saved(self.root,self.entry['key'],self.token,lambda *a:self.entry['source'],bucket)
                candidate=json.loads(self.props['Infinity.SavedNavigation.Pending'])
                self.assertEqual(candidate['bucket'],bucket);self.assertEqual(candidate['route'],self.route)
                self.assertNotIn('route',self.memory())  # Selection is not success.
                self.assertEqual(json.loads(self.path.read_text())[bucket],self.data[bucket])

    def test_success_is_remembered_across_fresh_store_read_and_lists(self):
        self.pending();self.assertTrue(self.confirm());data=json.loads(self.path.read_text())
        for bucket in ('later','watchlist'):
            with patch.object(self.nav,'_provider_current',return_value=self.provider),patch.object(self.nav,'available',side_effect=AssertionError('repeated provider discovery')):
                self.assertEqual(self.nav.navigation_target(self.entry,data,self.entry['source'],bucket),self.route)
        for name,value in self.data.items():
            if name!='revision':self.assertEqual(data[name],value)

    def test_failed_preference_is_retained_and_never_falls_back_to_pov(self):
        self.pending();self.assertTrue(self.confirm())
        self.nav._mark_failed(self.root,self.entry,'watchlist',self.route)
        record=self.memory();self.assertEqual(record['route'],self.route);self.assertTrue(record['failed'])
        target=self.nav.navigation_target(self.entry,json.loads(self.path.read_text()),self.entry['source'],'later')
        self.assertIn('action=saved-recovery',target);self.assertNotEqual(target,self.entry['source'])

    def test_remembered_route_skips_old_provider_and_validates_cached_destinations(self):
        self.pending();self.assertTrue(self.confirm());data=json.loads(self.path.read_text())
        with patch.object(self.plugin, '_target', side_effect=AssertionError('Old provider must not be inspected')), patch.object(self.nav,'_provider_current',return_value=self.provider):
            self.assertEqual(self.plugin.navigation_target(self.entry,data,'watchlist'),self.route)
        record=self.memory();cache={(self.provider['id'],json.dumps(self.provider['contract'],sort_keys=True)):self.provider}
        bad=dict(record,route='plugin://plugin.video.unrelated/?action=seasons')
        self.assertIsNone(self.nav._provider_current(bad,{'navigation_providers':cache}))

    def test_unknown_or_conflicting_identity_never_reuses_memory(self):
        self.pending();self.confirm();data=json.loads(self.path.read_text())
        for ids in ({'tmdb':'999','imdb':'tt48447471'},{'tmdb':'330430','imdb':'tt9999999'}):
            e=dict(self.entry,identity=self.hub.show_identity('tvshow',ids))
            self.assertIsNone(self.nav.remembered(data,e['identity']))
        episode=dict(self.entry,season=1,episode=2,identity=self.hub.media_identity('tv',{},1,2,{'tmdb':'330430'}))
        self.assertIsNone(self.nav.remembered(data,episode['identity']))

    def test_no_success_cancel_wrong_token_identity_or_stale_receipt_never_commits(self):
        for mutation in ('missing','token','path','identity','stale','phase','removed','changed-action'):
            with self.subTest(mutation=mutation):
                self.path.write_text(json.dumps(self.data));pending,success=self.pending()
                if mutation=='missing':success={}
                elif mutation=='token':success['token']='c'*32
                elif mutation=='path':success['destination_sha256']='0'*64
                elif mutation=='identity':success['identity_verified']=False
                elif mutation=='stale':success['epoch_ms']-=600000
                elif mutation=='phase':success['phase']='media_resolved'
                elif mutation=='removed':
                    d=deepcopy(self.data);d['later']={};self.path.write_text(json.dumps(d))
                elif mutation=='changed-action':
                    d=deepcopy(self.data);d['later'][self.entry['key']]['source']='other';self.path.write_text(json.dumps(d))
                self.props['Infinity.SavedNavigation.Success']=json.dumps(success)
                try:self.assertFalse(self.confirm())
                except self.nav.Cancelled:self.assertEqual(mutation,'changed-action')
                self.assertIsNone(self.memory())

    def test_resolved_movie_requires_actual_matching_playback_start(self):
        pending,_=self.pending(folder=False)
        self.assertFalse(self.confirm());self.assertIsNone(self.memory())
        self.assertFalse(self.confirm(playback={'type':'movie','infinity_original_route':'unrelated'}))
        self.assertTrue(self.confirm(playback={'type':'movie','infinity_original_route':pending['route']}))
        record=self.nav.remembered(json.loads(self.path.read_text()),pending['identity'])
        self.assertTrue(record['success_verified'])

    def test_concurrent_progress_and_large_existing_buckets_survive_commit(self):
        self.pending();current=deepcopy(self.data)
        current['items']['f'*64]['position']=312
        current['watched'].update({str(i):{'history':i} for i in range(750)})
        self.path.write_text(json.dumps(current));self.assertTrue(self.confirm())
        result=json.loads(self.path.read_text())
        self.assertEqual(result['items'],current['items']);self.assertEqual(result['watched'],current['watched'])
        for name in ('watchlist','later','sources','lists','ratings','collection','unknown_extension'):self.assertEqual(result[name],current[name])

    def test_incompatible_remembered_provider_requires_explicit_choice(self):
        self.pending();self.confirm()
        with patch.object(self.nav,'_provider_current',return_value=None):
            target=self.nav.navigation_target(self.entry,json.loads(self.path.read_text()),self.entry['source'],'watchlist')
        self.assertIn('action=saved-recovery',target);self.assertEqual(self.memory()['route'],self.route)

    def test_preserve_resume_offset_on_selected_recovery_playback(self):
        entry=dict(self.entry,media='movie',identity=self.hub.media_identity('movie',{'tmdb':'603'}))
        self.data['items'][entry['key']]=entry;self.path.write_text(json.dumps(self.data))
        with patch.object(self.nav,'available',return_value=([self.provider],[])),patch.object(self.nav,'direct_destination',return_value=None),patch.object(self.nav,'resolve',return_value=self.route),patch.object(self.search,'route',return_value=self.route):
            self.nav.recover_saved(self.root,entry['key'],'',lambda *a:'','continue',item_builder=lambda *a:('',Item()),resume_offset=147.356)
        target,item=self.calls[-1];self.assertEqual(target,self.route)
        self.assertEqual(item.properties['StartOffset'],'147.356');self.assertEqual(item.properties['ResumeTime'],'147.356')

    def test_original_valid_route_refuses_manually_injected_recovery_action(self):
        before=self.path.read_bytes()
        with patch.object(self.nav,'available',side_effect=AssertionError('unexpected chooser')):
            self.nav.recover_saved(self.root,self.entry['key'],'',lambda *a:self.entry['source'])
        self.assertEqual(self.path.read_bytes(),before);self.assertFalse(self.calls)

    def test_changed_persisted_route_cannot_reuse_old_success_proof(self):
        self.pending();self.confirm();data=json.loads(self.path.read_text())
        record=self.nav.remembered(data,self.entry['identity']);record['route']+='&tmdb=999'
        with patch.object(self.nav,'_provider_current',return_value=self.provider):
            self.assertIn('action=saved-recovery',self.nav.navigation_target(self.entry,data,self.entry['source'],'later'))

    def test_conflicting_primary_id_cannot_overwrite_existing_choice(self):
        self.pending();self.confirm();before=self.path.read_bytes()
        conflict=dict(self.entry,identity=self.hub.show_identity('tvshow',{'tmdb':'330430','imdb':'tt9999999'}))
        data=json.loads(before);data['watchlist'][conflict['key']]=conflict;self.path.write_text(json.dumps(data))
        before=self.path.read_bytes()
        with self.assertRaisesRegex(self.nav.Unavailable,'Conflicting verified'):
            self.nav._mark_failed(self.root,conflict,'watchlist',conflict['source'])
        self.assertEqual(before,self.path.read_bytes())

    def test_unrelated_provider_destination_rejected(self):
        with self.assertRaises(self.nav.Unavailable):
            self.nav.destination(self.provider,dict(file='plugin://plugin.video.pov/?action=seasons&tmdb=330430',type='tvshow',uniqueid=self.entry['identity']['ids'],filetype='directory'))

class NativeCorrelation(unittest.TestCase):
    def test_success_receipt_only_for_selected_uncancelled_current_attempt(self):
        code=r'''
#include "InfinitySavedNavigationState.h"
#include <cassert>
using namespace InfinitySavedNavigation;
Ticket make(){Ticket t;t.token="one";t.key=std::string(64,'a');t.bucket="watchlist";t.originalPath=t.path="plugin://pov/";t.attempted={"pov"};return t;}
int main(){Correlation c;c.Begin(make());assert(!c.Finish("one","plugin://pov/",true,"failed"));assert(!c.Read());
 c.Begin(make());assert(c.Finish("one","plugin://pov/",false,"failed"));assert(c.Next("one","plugin://umbrella/","umbrella"));
 assert(!c.Finish("old","plugin://umbrella/",true,"failed"));
 auto result=c.Finish("one","plugin://umbrella/",true,"failed");assert(result&&result->succeeded&&result->recovering);assert(result->bucket=="watchlist");assert(!c.Read());
 c.Begin(make());assert(c.Finish("one","plugin://pov/",false,"failed"));assert(c.Next("one","plugin://seren/","seren"));c.Cancelled("one");assert(!c.Finish("one","plugin://seren/",true,"failed"));
 c.Begin(make());assert(c.Finish("one","plugin://pov/",false,"failed"));assert(c.Next("one","plugin://umbrella/","umbrella"));auto newer=make();newer.token="new";c.Begin(newer);assert(!c.Finish("one","plugin://umbrella/",true,"failed"));assert(c.Read()->token=="new");}
'''
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'case.cpp').write_text(code)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-I',str(REPAIR),str(root/'case.cpp'),'-o',str(root/'case')],check=True,capture_output=True,text=True)
            subprocess.run([str(root/'case')],check=True,timeout=10)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();BASE=args.base
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    report=dict(scope='item 1 only: shared failure-triggered recovery, exact identity, memory and data preservation',
        passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        actual_android='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN',apk_rebuilt=False)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
