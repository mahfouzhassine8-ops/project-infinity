"""Measure actual verifier allocation/work with unchanged capability outcomes."""
import ast
from copy import deepcopy
import gc
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
import tracemalloc
import types
import unittest
from unittest.mock import patch

import review_exact_sources as review

ROOT=Path(__file__).parent
SIGNED=Path(os.environ.get('INFINITY_SIGNED407_SOURCES','/workspace/scratch/9491f79db5c3/baseline-2103407/ownership-local/sources'))/'script.infinity.commandcenter'
PROVIDERS=Path(os.environ.get('SEARCH_PROVIDER_SOURCE_ROOT','/workspace/scratch/9491f79db5c3/android407-evidence/candidate-search01/feature-results/fixture'))


class ExactSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=json.loads((SIGNED/'NAVIGATION-CONTRACTS.json').read_text())
        cls.proof=json.loads((ROOT/'EXACT-SOURCE-REVIEW.json').read_text())
        cls.after=cls.proof['contracts']
        cls.rows=cls.proof['reviewed']
        cls.tree=ast.parse((SIGNED/'provider_inventory.py').read_bytes())
        cls.fn=next(n for n in cls.tree.body if isinstance(n,ast.FunctionDef) and n.name=='_verify')

    def verify(self,contracts,rows=None):
        calls={'read':0,'fingerprint':0};out=[]
        def source(root,name):
            calls['read']+=1;return (root/name).read_bytes()
        def fingerprint(raw,addon):
            calls['fingerprint']+=1;return review.fingerprint(raw,addon)
        scope=dict(hashlib=hashlib,deepcopy=deepcopy,MEDIA=('movie','tv','anime','cartoon'),
                   NAVIGATION_FAMILIES={'mode-list-v1','action-list-v1','json-args-list-v1'})
        exec(compile(ast.Module(body=[self.fn],type_ignores=[]),'actual-signed-verifier','exec'),scope)
        with patch.dict(sys.modules,{'saved_navigation':types.SimpleNamespace(_source=source,fingerprint=fingerprint)}):
            for row in (self.rows if rows is None else rows):
                root=PROVIDERS/row['observed_provider'];spec=contracts['contracts'][row['contract']]
                out.append(scope['_verify'](row['observed_provider'],root,[spec],(root/'addon.xml').read_bytes()))
        return out,calls

    def test_exact_byte_shortcut_preserves_routes_raw_pins_and_source_reads(self):
        self.assertEqual(len(self.rows),3)
        rows=[r for r in self.rows if r["observed_provider"]!="plugin.video.pov"]
        before,a=self.verify(self.before,rows);after,b=self.verify(self.after,rows)
        self.assertEqual(before,after)
        self.assertEqual(a['read'],b['read']);self.assertEqual(a['read'],14)
        self.assertEqual(a['fingerprint'],14);self.assertEqual(b['fingerprint'],0)
        for row in rows:
            self.assertEqual(self.after['contracts'][row['contract']]['sources'],self.before['contracts'][row['contract']]['sources'])

    def test_review_reproduces_only_existing_shapes_and_keeps_unknown_version_fallback(self):
        value,proof=review.review(self.before,[PROVIDERS/r['observed_provider'] for r in self.rows])
        self.assertEqual(value,self.after);self.assertEqual(proof,self.rows)
        altered=deepcopy(self.before);altered['contracts'][self.rows[0]['contract']]['sources'][next(iter(self.rows[0]['source_pins']))]='0'*64
        value,proof=review.review(altered,[PROVIDERS/self.rows[0]['observed_provider']])
        self.assertEqual(proof,[])
        self.assertNotIn('exact_sources',value['contracts'][self.rows[0]['contract']])
        # Existing code already falls back to structural verification on an
        # unrecognized byte hash. No new hardcoded provider/version ceiling.
        changed=deepcopy(self.after)
        for row in self.rows:changed['contracts'][row['contract']]['exact_sources']={k:'0'*64 for k in row['source_pins']}
        result,calls=self.verify(changed)
        original,_=self.verify(self.after)
        self.assertEqual(result,original);self.assertEqual(calls['fingerprint'],21)

    def test_pov_empty_type_parameters_are_serialization_only_not_executable_changes(self):
        row=next(r for r in self.rows if r['observed_provider']=='plugin.video.pov')
        old=self.before['contracts'][row['contract']];new=self.after['contracts'][row['contract']]
        changed=0
        for name,expected in old['sources'].items():
            raw=(PROVIDERS/row['observed_provider']/name).read_bytes()
            self.assertIn(expected,(review.fingerprint(raw,row['observed_provider']),review.fingerprint(raw,row['observed_provider'],python312=True)))
            self.assertEqual(new['sources'][name],review.fingerprint(raw,row['observed_provider']))
            changed+=expected!=new['sources'][name]
        self.assertGreater(changed,0)
        result,_=self.verify(self.after,[row])
        self.assertIn(('movie','search'),result[0]);self.assertIn(('tv','search'),result[0])

    def test_measured_temporary_allocation_and_duration(self):
        results={}
        rows=[r for r in self.rows if r["observed_provider"]!="plugin.video.pov"]
        for label,contracts in [('before',self.before),('after',self.after)]:
            gc.collect();tracemalloc.start();samples=[]
            for _ in range(5):
                started=time.perf_counter();result,calls=self.verify(contracts,rows)
                samples.append((time.perf_counter()-started)*1000)
                del result
            current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            results[label]=dict(median_ms=statistics.median(samples),samples_ms=samples,
                                traced_peak_bytes=peak,traced_current_bytes=current,work_per_two_providers=calls)
        self.assertLess(results['after']['traced_peak_bytes'],results['before']['traced_peak_bytes'])
        output=os.environ.get('EXACT_SOURCE_MEASUREMENT')
        if output:Path(output).write_text(json.dumps(dict(scope='Host signed verifier body, five two-provider batches with Python3.11 AST serialization; Python3.12 host.  Not Android/Fold memory, RSS/PSS, Home or frame performance.',results=results,Android17='NOT RUN',physical_Fold='NOT RUN'),indent=2)+'\n')


if __name__=='__main__':unittest.main(verbosity=2)
