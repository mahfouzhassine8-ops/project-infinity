"""Actual reviewed Crew sources, independent Search categories and negative controls."""
import ast
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('reviewed_capabilities',ROOT/'isolated-python/provider_capabilities.py')
cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
SOURCE=Path(os.environ.get('CREW_SOURCE_ROOT','/workspace/scratch/ea870406277a/upstream-sources'))


class AutomaticCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.plugin=self.work/'plugin.video.thecrew';self.plugin.mkdir()
        for name in ('addon.xml','thecrew.py'):shutil.copyfile(SOURCE/'plugin.video.thecrew'/name,self.plugin/name)
        self.dep=self.work/'script.module.thecrew';self.dep.mkdir()
        self.profile=json.loads((ROOT/'SEARCH-STRUCTURES.json').read_text())['profiles']
        files={'addon.xml',self.profile[0]['router']}|{r['path'] for r in self.profile[0]['receivers'].values()}
        for name in files:
            p=self.dep/name;p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(SOURCE/'script.module.thecrew'/name,p)
        def source(root,name):
            path=root/name
            if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(root):raise ValueError()
            if any(p.is_symlink() for p in (path,*path.parents) if p!=root.parent):raise ValueError()
            raw=path.read_bytes()
            if len(raw)>512*1024:raise ValueError()
            return raw
        self.modules=patch.dict(sys.modules,{'saved_navigation':types.SimpleNamespace(_source=source)})
        self.modules.start();self.addCleanup(self.modules.stop)
        self.resolve=lambda aid:(self.dep,'3.2.26') if aid=='script.module.thecrew' else (_ for _ in ()).throw(ValueError('unknown dependency'))

    def recognize(self,aid='plugin.video.thecrew'):
        return cap.recognize(aid,self.plugin,(self.plugin/'addon.xml').read_bytes(),self.resolve,self.profile)

    def test_actual_router_receivers_separate_categories_and_search_only(self):
        result=self.recognize()
        self.assertEqual(set(result),{('movie','search'),('tv','search')})
        for media,action in [('movie','movieSearchterm'),('tv','tvSearchterm')]:
            proof=result[(media,'search')]
            self.assertEqual(proof['contract']['params'],{'action':action})
            self.assertEqual(proof['contract']['query_key'],'name')
            self.assertEqual(set(proof['contract']['pins']),{'addon.xml','thecrew.py'})
            cap.verify_dependencies(proof['contract'],self.resolve)

    def test_comments_versions_and_unrelated_lazy_actions_auto_recognized(self):
        router=self.dep/self.profile[0]['router'];text=router.read_text()
        router.write_text(text.replace('    action_map = {','    action_map = {\n        "future_unrelated": lambda: 123,',1)+'\n# compatible routing extension\n')
        xml=self.plugin/'addon.xml';xml.write_text(xml.read_text().replace('version="3.2.2"','version="3.2.3"',1))
        self.assertEqual(len(self.recognize()),2)

    def test_renamed_provider_and_action_are_derived_from_same_structure(self):
        aid='plugin.video.compatiblefork'
        p=self.plugin/'addon.xml';p.write_text(p.read_text().replace('plugin.video.thecrew',aid))
        router=self.dep/self.profile[0]['router'];router.write_text(router.read_text().replace("'movieSearchterm': lambda:","'findMoviesNow': lambda:",1))
        result=self.recognize(aid)
        self.assertEqual(result[('movie','search')]['contract']['params'],{'action':'findMoviesNow'})
        self.assertEqual(result[('movie','search')]['id'],aid)

    def test_eager_values_duplicate_keys_and_ambiguous_routes_rejected(self):
        router=self.dep/self.profile[0]['router'];original=router.read_text()
        for value in ('"new": execute_now(),','"new": lambda x=execute_now(): x,',
                      '"movieSearchterm": lambda: 1,','**dynamic_routes,'):
            with self.subTest(value=value):
                router.write_text(original.replace('    action_map = {','    action_map = {\n        '+value,1))
                with self.assertRaises(ValueError):self.recognize()
        router.write_text(original.replace("'movieSearchterm': lambda:","'second': lambda: call_module('resources.lib.indexers.movies', 'Movies', True, 'search_term', * (p('name'),)),\n        'movieSearchterm': lambda:",1))
        result=self.recognize()
        self.assertNotIn(('movie','search'),result)
        self.assertIn(('tv','search'),result)

    def test_dependency_source_version_and_root_rechecked_after_proof(self):
        proof=self.recognize()[('movie','search')]['contract']
        with self.assertRaises(RuntimeError):cap.verify_dependencies(proof,lambda aid:(self.dep,'3.2.27'))
        with self.assertRaises(RuntimeError):cap.verify_dependencies(proof,lambda aid:(self.work,'3.2.26'))
        router=self.dep/self.profile[0]['router'];router.write_text(router.read_text()+'\n# changed after verification\n')
        with self.assertRaises(RuntimeError):cap.verify_dependencies(proof,self.resolve)

    def test_unknown_receiver_or_changed_dispatch_remains_unverified(self):
        path=self.dep/self.profile[0]['receivers']['movie']['path'];path.write_text(path.read_text().replace('self.get(search_url)','self.play(search_url)',1))
        result=self.recognize();self.assertNotIn(('movie','search'),result);self.assertIn(('tv','search'),result)
        router=self.dep/self.profile[0]['router'];router.write_text(router.read_text().replace('handler = action_map.get(action)','handler = action_map.get("other")',1))
        self.assertEqual(self.recognize(),{})


if __name__=='__main__':unittest.main(verbosity=2)
