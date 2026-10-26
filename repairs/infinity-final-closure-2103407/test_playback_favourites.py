"""Execute exact candidate functions with the actual typed native API contract."""
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import patch_playback_favourites as correction
import readonly_resume_observer


def functions(raw,names,scope):
    tree=ast.parse(raw)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-candidate.py','exec'),scope)
    return scope


class NativeTag:
    def __init__(self,**values):
        self.values=dict(type='movie',title='The Matrix',showtitle='',season=-1,episode=-1,
                         uniqueid={'tmdb':'603','imdb':'tt0133093'},plot='Full\noriginal synopsis',
                         duration=180,year=1999,cast='Actor as Character',trailer='https://example.test/trailer')
        self.values.update(values)

    def getUniqueID(self,name):return self.values['uniqueid'].get(name,'')

    def __getattr__(self,name):
        key={'getMediaType':'type','getTitle':'title','getTVShowTitle':'showtitle','getSeason':'season',
             'getEpisode':'episode','getPlot':'plot','getDuration':'duration','getYear':'year',
             'getCast':'cast','getTrailer':'trailer'}.get(name)
        if key:return lambda:self.values.get(key)
        raise AttributeError(name)


class PlaybackFavouritesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(os.environ['INFINITY_PLAYBACK_PARENT_APK']) as z:
            cls.raw={n:z.read('assets/addons/'+correction.CC+'/'+n) for n in
                     ('service.py','plugin.py','addon.xml','resume_hub.py','title_metadata.py','experience.py')}
        cls.updated={n:correction.patch(n,cls.raw[n]) for n in ('service.py','plugin.py','addon.xml')}
        scope={};exec(readonly_resume_observer.source(cls.raw['resume_hub.py'])[0],scope)
        functions(cls.raw['resume_hub.py'],['identity_key'],scope)
        cls.hub=SimpleNamespace(**scope)
        metadata=ModuleType('title_metadata');exec(cls.raw['title_metadata.py'],metadata.__dict__)
        cls.metadata=metadata
        experience=ModuleType('experience')
        from urllib.parse import urlsplit
        functions(cls.raw['experience.py'],['stable_route'],dictscope:=dict(re=re,urlsplit=urlsplit))
        experience.stable_route=dictscope['stable_route'];cls.experience=experience

    def native(self,item=None,tags=None,files=None,playing=None,skin='skin.infinity.diggz'):
        tags=iter(tags or [NativeTag()]*3);files=iter(files or ['/actual/local.mp4']*2)
        playing=iter(playing or [True,True]);calls=[]
        player=SimpleNamespace(isPlayingVideo=lambda:next(playing),getPlayingFile=lambda:next(files),
                               getVideoInfoTag=lambda:next(tags))
        def ctor():calls.append('Player');return player
        scope=dict(xbmc=SimpleNamespace(Player=ctor,getSkinDir=lambda:skin),hub=self.hub)
        functions(self.updated['service.py'],['_continue_native_item'],scope)
        with patch.dict(sys.modules,{'title_metadata':self.metadata,'experience':self.experience}):
            result=scope['_continue_native_item'](item or dict(type='unknown',file='/actual/local.mp4',id=99))
        return result,calls

    def test_exact_inverse_and_unowned_source_rejected(self):
        for name in self.updated:
            inverse=self.updated[name].decode()
            for old,new in reversed(correction.substitutions(name)):inverse=inverse.replace(new,old,1)
            self.assertEqual(inverse.encode(),self.raw[name])
            with self.assertRaises(ValueError):correction.patch(name,self.raw[name]+b'\n')
        with self.assertRaises(ValueError):correction.patch('resume_hub.py',self.raw['resume_hub.py'])

    def test_movie_restores_exact_typed_identity_metadata_without_library_id(self):
        result,_=self.native()
        self.assertEqual(result['type'],'movie');self.assertEqual(result['uniqueid']['tmdb'],'603')
        self.assertEqual(result['title'],'The Matrix');self.assertNotIn('id',result)
        information=self.metadata.from_player_item(result)
        self.assertEqual(information['plot'],'Full\noriginal synopsis')
        self.assertEqual(information['cast'],'Actor as Character');self.assertEqual(information['duration'],180)
        self.assertNotIn('infinity_transient_playback_source',result)

    def test_native_capture_enters_original_identity_path_and_library_write_guard(self):
        for remote in (False,True):
            source='https://stream.invalid/expired' if remote else '/actual/local.mp4'
            result,_=self.native(item=dict(type='unknown',file=source,id=99),files=[source]*2)
            scope=dict(xbmc=SimpleNamespace(getInfoLabel=lambda _:''),hub=self.hub,
                       source_identity=lambda *args:None,setting_bool=lambda *args:True,
                       _continue_show_identity=lambda *args:{})
            functions(self.updated['service.py'],['_continue_identity'],scope)
            with patch.dict(sys.modules,{'title_metadata':self.metadata}):
                entry=scope['_continue_identity'](result)
            self.assertEqual(entry['identity']['ids'],{'tmdb':'603','imdb':'tt0133093'})
            self.assertEqual(entry['dbid'],-1)
            self.assertEqual(entry['information']['plot'],'Full\noriginal synopsis')
            self.assertEqual(entry['source'],'' if remote else source)

    def test_episode_requires_native_type_ids_and_exact_coordinates(self):
        tag=NativeTag(type='episode',showtitle='Verified series',season=2,episode=3,uniqueid={'tvdb':'123456'})
        result,_=self.native(tags=[tag]*3)
        self.assertEqual(self.hub.media_identity('tv',result['uniqueid'],result['season'],result['episode']),
                         {'schema':1,'kind':'episode','scope':'episode','ids':{'tvdb':'123456'},'season':2,'episode':3})
        for bad in (NativeTag(type='unknown'),NativeTag(uniqueid={}),NativeTag(uniqueid={'tmdb':'guess'}),
                    NativeTag(type='episode',season=-1,episode=3)):
            self.assertEqual(self.native(tags=[bad]*3)[0],{})

    def test_source_and_same_file_identity_races_or_conflicts_fail_closed(self):
        self.assertEqual(self.native(files=['/actual/local.mp4','/other.mp4'])[0],{})
        self.assertEqual(self.native(tags=[NativeTag(),NativeTag(),NativeTag(uniqueid={'tmdb':'604'})])[0],{})
        self.assertEqual(self.native(playing=[True,False])[0],{})
        self.assertEqual(self.native(item=dict(file='/other.mp4'))[0],{})
        self.assertEqual(self.native(item=dict(file='/actual/local.mp4',uniqueid={'tmdb':'604'}))[0],{})
        self.assertEqual(self.native(item=dict(file='/actual/local.mp4',uniqueid={'imdb':'tt9999999'}))[0],{})
        self.assertEqual(self.native(skin='skin.cobra')[0],{})
        self.assertEqual(self.native(skin='skin.cobra')[1],[])

    def test_untyped_stream_retains_identity_and_verified_route_but_not_replay_url(self):
        raw=dict(type='unknown',file='https://stream.invalid/expired?token=x',infinity_original_route='plugin://verified/route')
        result,_=self.native(item=raw,files=[raw['file']]*2)
        self.assertTrue(result['infinity_transient_playback_source'])
        self.assertEqual(result['infinity_original_route'],raw['infinity_original_route'])
        self.assertEqual(result['uniqueid']['tmdb'],'603')
        source=ast.parse(self.updated['service.py'])
        node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='_continue_identity')
        assigns=[]
        for n in node.body:
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets):assigns.append(n)
            elif isinstance(n,ast.If) and "infinity_transient_playback_source" in ast.unparse(n):assigns.append(n)
        scope=dict(item=result,xbmc=SimpleNamespace(getInfoLabel=lambda _:raw['file']))
        exec(compile(ast.Module(body=assigns,type_ignores=[]),'actual-source-selection','exec'),scope)
        self.assertEqual(scope['source'],'')

    def test_original_typed_json_path_is_exact_and_no_native_constructor(self):
        calls=[];item=dict(type='movie',id=27,title='Library movie',file='file:///original',uniqueid={'tmdb':'603'})
        scope=dict(jsonrpc=lambda *args:dict(result=dict(item=item)),
                   _continue_native_item=lambda _:calls.append('unexpected fallback'))
        functions(self.updated['service.py'],['_continue_player_item'],scope)
        self.assertIs(scope['_continue_player_item'](1),item);self.assertEqual(calls,[])

    def favourite(self,response,folder=False):
        scope=dict(_rpc=lambda *args:response,hub=SimpleNamespace(entry_identity=lambda _:{'kind':'tvshow' if folder else 'movie'}))
        functions(self.updated['plugin.py'],['_favourite'],scope)
        return scope['_favourite'](dict(label='Actual title',poster='poster.jpg'),{},'watchlist',target='plugin://verified/route')

    def test_native_null_and_empty_favourites_offer_add(self):
        for response in (dict(favourites=None,limits=dict(start=0,end=0,total=0)),dict(favourites=[])):
            spec,exists=self.favourite(response)
            self.assertFalse(exists);self.assertEqual(spec['path'],'plugin://verified/route')
            self.assertEqual(spec['title'],'Actual title')

    def test_existing_exact_removal_duplicate_and_malformed_fail_closed(self):
        row=dict(title='Original title',type='media',path='plugin://verified/route',thumbnail='original.jpg')
        self.assertEqual(self.favourite(dict(favourites=[row])),(row,True))
        folder=dict(title='Original show',type='window',window='10025',windowparameter='plugin://verified/route')
        self.assertEqual(self.favourite(dict(favourites=[folder]),folder=True),(folder,True))
        for response in (dict(favourites=[row,row]),dict(favourites='malformed'),dict(favourites=[None]),None,[]):
            self.assertEqual(self.favourite(response),(None,None))


if __name__=='__main__':unittest.main(verbosity=2)
