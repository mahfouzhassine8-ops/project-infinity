"""Run actual shipped functions and source pins; no provider code is executed."""
import ast
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch as mock_patch
from urllib.parse import parse_qs,urlsplit,urlencode

import patch_resume_render as correction

SOURCES=Path(os.environ.get('INFINITY_RENDER_PARENT_MODULES',
    '/workspace/scratch/7aaf34f5a62d/signed411-modules'))
PROVIDERS=Path(os.environ.get('INFINITY_RENDER_PROVIDER_FIXTURE',
    '/workspace/scratch/9491f79db5c3/android407-evidence/candidate-search01/feature-results/fixture'))
CC=correction.CC


def load(name,raw):
    value=types.ModuleType(name);exec(compile(raw,name,'exec',dont_inherit=True),value.__dict__);return value


class ResumeRenderCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.provider='plugin.video.umbrella'
        self.before=(SOURCES/CC/'experience.py').read_bytes()
        self.after=correction.patch('experience.py',self.before)
        self.xbmc=types.SimpleNamespace(getCondVisibility=lambda *a:True,LOGINFO=1,log=lambda *a:None)
        self.modules=mock_patch.dict(sys.modules,{
            'xbmc':self.xbmc,
            'xbmcaddon':types.SimpleNamespace(Addon=lambda aid:types.SimpleNamespace(getAddonInfo=lambda key:str(self.root/aid))),
            'xbmcvfs':types.SimpleNamespace(translatePath=lambda path:path),
            'common':types.SimpleNamespace(persistence_scope=lambda *a,**k:nullcontext(),
                                          atomic_json=lambda *a:None,read_json=lambda *a:{}),
        })
        self.modules.start();self.addCleanup(self.modules.stop)
        self.hub=load('resume_hub',(SOURCES/CC/'resume_hub.py').read_bytes())
        sys.modules['resume_hub']=self.hub
        self.addCleanup(sys.modules.pop,'resume_hub',None)
        self.old=load('original_experience',self.before)
        self.new=load('experience',self.after)
        self.modules2=mock_patch.dict(sys.modules,{'experience':self.new})
        self.modules2.start();self.addCleanup(self.modules2.stop)
        self.contract=self.new.CURRENT_SOURCE_CONTRACTS[self.provider]['6.7.94']
        source=PROVIDERS/self.provider;target=self.root/self.provider;target.mkdir()
        # Real reviewed provider source bytes, with an explicitly format-only
        # manifest version fixture; this never claims a device installation.
        for name,pins in self.contract['files'].items():
            raw=(source/name).read_bytes()
            self.assertIn(hashlib.sha256(raw).hexdigest(),pins)
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        raw=(source/'addon.xml').read_text()
        raw=re.sub(r'(<addon\b[^>]*\bversion=")[^"]+',r'\g<1>6.7.94',raw,count=1)
        (target/'addon.xml').write_text(raw)
        bridge=self.root/'script.infinity.watchedbridge';bridge.mkdir()
        shutil.copyfile(SOURCES/'script.infinity.watchedbridge/PROVIDER-CONTRACTS.json',bridge/'PROVIDER-CONTRACTS.json')

    def provider_reads(self,fn):
        reads=[];original=Path.read_bytes
        def read(path):
            if str(path).startswith(str(self.root/self.provider)) and path.suffix=='.py':
                reads.append(path.name)
            return original(path)
        with mock_patch.object(Path,'read_bytes',read):
            result=fn()
        return result,reads

    def test_eleven_cards_reuse_three_real_source_hashes_and_click_reverifies(self):
        old,old_reads=self.provider_reads(lambda:[self.old._source_contract(self.provider) for _ in range(11)])
        cache={}
        new,new_reads=self.provider_reads(lambda:[self.new._source_contract(self.provider,cache) for _ in range(11)])
        self.assertEqual(old,new);self.assertTrue(all(old))
        self.assertEqual(len(old_reads),33);self.assertEqual(len(new_reads),3)
        result,click_reads=self.provider_reads(lambda:self.new._source_contract(self.provider))
        self.assertEqual(result,old[0]);self.assertEqual(len(click_reads),3)
        self.assertEqual(len(cache),1)

    def test_same_size_replacement_changed_manifest_missing_and_symlink_refuse(self):
        cache={};self.assertTrue(self.new._source_contract(self.provider,cache))
        target=self.root/self.provider
        file=target/next(iter(self.contract['files']))
        before=file.stat();raw=file.read_bytes();copy=file.with_suffix('.pending')
        copy.write_bytes(raw.replace(b'import ',b'imporX ',1))
        os.utime(copy,ns=(before.st_atime_ns,before.st_mtime_ns));copy.replace(file)
        self.assertIsNone(self.new._source_contract(self.provider,cache))
        file.write_bytes(raw);self.assertTrue(self.new._source_contract(self.provider,cache))
        manifest=target/'addon.xml';saved=manifest.read_text()
        manifest.write_text(saved.replace('6.7.94','99.99.99',1))
        self.assertIsNone(self.new._source_contract(self.provider,cache))
        manifest.write_text(saved);self.assertTrue(self.new._source_contract(self.provider,cache))
        file.unlink();self.assertIsNone(self.new._source_contract(self.provider,cache))
        elsewhere=self.root/'relocated.py';elsewhere.write_bytes(raw);file.symlink_to(elsewhere)
        # Linked source cannot be reused from the prior cache.
        self.assertIsNone(self.new._source_contract(self.provider,cache))

    def test_hash_mutation_during_verification_never_caches_a_false_generation(self):
        cache={};real=self.new._render_source_stamp;calls=0
        def stamp(*args):
            nonlocal calls
            calls+=1
            return real(*args) if calls==1 else ('changed during read',)
        with mock_patch.object(self.new,'_render_source_stamp',side_effect=stamp):
            self.assertIsNone(self.new._source_contract(self.provider,cache))
        self.assertEqual(cache,{})

    def test_movie_tv_exact_identity_position_and_mismatch_preserved(self):
        cache={}
        verify=lambda aid:self.new._source_contract(aid,cache)
        for media,season,episode in [('movie',-1,-1),('tv',3,7)]:
            identity=self.hub.media_identity(media,{'tmdb':'603'} if media=='movie' else {},season,episode,
                                            {'tmdb':'1399'} if media=='tv' else None)
            entry=dict(media=media,identity=identity,title='Exact original title',season=season,episode=episode,
                       position=417.125,duration=900,percentage=46.35)
            # entry_identity uses the actual persisted typed field.
            entry['media_identity']=entry.pop('identity')
            route='plugin://plugin.video.umbrella/?action=play&tmdb='+('603' if media=='movie' else '1399&season=3&episode=7')
            before=deepcopy(entry)
            for _ in range(11):
                self.assertEqual(self.new.verified_source(entry,route,verify),self.old.verified_source(entry,route))
            self.assertEqual(self.new.verified_source(entry,route.replace('tmdb=','tmdb=99'),verify),'')
            if media=='tv':
                self.assertEqual(self.new.verified_source(entry,route.replace('episode=7','episode=8'),verify),'')
            self.assertEqual(entry,before)

    def test_only_render_route_uses_cache_authoritative_sources_remain_exact(self):
        for name in ('experience.py','plugin.py','addon.xml'):
            raw=(SOURCES/CC/name).read_bytes();result=correction.patch(name,raw)
            text=result.decode()
            for old,new in reversed(correction.edits(name)):text=text.replace(new,old,1)
            self.assertEqual(text.encode(),raw)
        tree=ast.parse(correction.patch('plugin.py',(SOURCES/CC/'plugin.py').read_bytes()))
        before=ast.parse((SOURCES/CC/'plugin.py').read_bytes())
        for name in ('play_saved','recover_entry','mutate','_mutate_locked','_values_for','_list_item'):
            get=lambda t:ast.dump(next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name))
            self.assertEqual(get(tree),get(before),name)


if __name__=='__main__':unittest.main(verbosity=2)
