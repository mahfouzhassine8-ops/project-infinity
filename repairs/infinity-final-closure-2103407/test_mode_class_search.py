"""Read-only actual publisher fixtures; no add-on imported or executed."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('structural_search',ROOT/'structural_search.py')
ss=importlib.util.module_from_spec(spec);spec.loader.exec_module(ss)
SOURCE=Path(os.environ.get('REDLIGHT_SOURCE_ROOT',Path(__file__).resolve().parents[3]/'provider-official-readonly/sources/plugin.video.redlight'))

class ModeClassTests(unittest.TestCase):
 def setUp(self):
  self.policy=json.loads((ROOT/'MODE-CLASS-SEARCH-POLICY.json').read_text())
  self.files={name:(SOURCE/name).read_bytes() for name in self.policy['shapes']}
  self.manifest=(SOURCE/'addon.xml').read_bytes()
 def recognize(self):
  return ss.mode_class_search(lambda n:self.files[n],self.policy['entrypoint'],self.policy)
 def test_actual_movie_tv_query_and_only_search_routes_are_derived(self):
  result=self.recognize();self.assertEqual(set(result),{'movie','tv'})
  for media,mode,action in [('movie','build_movie_list','tmdb_movies_search'),('tv','build_tvshow_list','tmdb_tv_search')]:
   self.assertEqual(result[media]['params'],dict(mode=mode,action=action))
   self.assertEqual(result[media]['query_key'],'query')
   self.assertEqual(set(result[media]['pins']),set(self.files))
   for n,p in result[media]['pins'].items():self.assertEqual(p,hashlib.sha256(self.files[n]).hexdigest())
 def test_comments_docstrings_and_packaging_version_do_not_require_new_adapter(self):
  for n in self.files:self.files[n]=b'"""Compatible packaging documentation."""\n'+self.files[n]+b'\n# source comment\n'
  self.assertEqual(set(self.recognize()),{'movie','tv'})
 def test_unreviewed_router_branch_query_mutation_and_alias_are_not_advertised(self):
  n='resources/lib/modules/router.py';original=self.files[n]
  for old,new in [(b"mode = params.get('mode', 'navigator.main')",b"mode = params.get('other', 'navigator.main')"),
                  (b'\tparams = dict',b'\tif True: return arbitrary_destination()\n\tparams = dict'),
                  (b'return Movies(params).fetch_list()',b'return Movies({}).fetch_list()')]:
   self.files[n]=original.replace(old,new,1);self.assertNotEqual(self.files[n],original)
   with self.subTest(old=old),self.assertRaises(ss.Unverified):self.recognize()
  self.files[n]=original
 def test_media_receiver_verified_independently(self):
  n='resources/lib/indexers/movies.py';self.files[n]=self.files[n].replace(b'function(key_id, page_no)',b'function("wrong", page_no)',1)
  self.assertEqual(set(self.recognize()),{'tv'})
 def test_api_target_and_query_position_must_be_reviewed(self):
  n='resources/lib/apis/tmdb_api.py';original=self.files[n]
  for old,new in [(b'/3/search/movie?',b'/3/discover/movie?'),(b'meta_filter, query, page_no)',b'meta_filter, "wrong", page_no)')]:
   self.files[n]=original.replace(old,new,1);self.assertNotEqual(self.files[n],original)
   with self.subTest(old=old),self.assertRaises(ss.Unverified):self.recognize()
 def test_wrong_entrypoint_policy_and_oversized_source_rejected(self):
  with self.assertRaises(ss.Unverified):ss.mode_class_search(lambda n:self.files[n],'default.py',self.policy)
  self.files[self.policy['entrypoint']]=b' '*(ss.MAX_SOURCE+1)
  with self.assertRaises(ss.Unverified):self.recognize()
 def test_manifest_identity_and_raw_source_pins_preserved_without_execution(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   for n,raw in self.files.items():
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
   def read(r,n):
    p=r/n
    if Path(n).is_absolute() or '..' in Path(n).parts or not p.resolve().is_relative_to(r) or p.is_symlink():raise ValueError('unsafe source')
    return p.read_bytes()
   with patch.dict(sys.modules,{'saved_navigation':types.SimpleNamespace(_source=read)}):
    result=ss.recognize_mode_class('plugin.video.redlight',root,self.manifest,self.policy)
    self.assertEqual(set(result),{('movie','search'),('tv','search')})
    self.assertEqual(result[('movie','search')]['contract']['pins']['addon.xml'],hashlib.sha256(self.manifest).hexdigest())
    self.assertEqual(ss.recognize_mode_class('plugin.video.other',root,self.manifest,self.policy),{})

if __name__=='__main__':unittest.main(verbosity=2)
