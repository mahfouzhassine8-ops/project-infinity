"""Performance corrections only; no app/provider/Android/shutdown execution."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

HERE=Path(__file__).resolve().parent;UNIVERSAL=HERE.parent;REPAIR=UNIVERSAL.parent
sys.path.insert(0,str(UNIVERSAL))
import test_search_inventory as fixture
NEW=REPAIR/'performance/overlay/script.infinity.commandcenter'


class Performance(unittest.TestCase):
    def setUp(self):
        self.case=fixture.Inventory('test_actual_specialty_contracts_and_source_tamper');self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.search=fixture.load('infinity_search',NEW/'infinity_search.py')
        self.inv=fixture.load('provider_inventory',NEW/'provider_inventory.py')
        self.baseline=fixture.load('baseline34_inventory',UNIVERSAL/'overlay/script.infinity.commandcenter/provider_inventory.py')

    def test_actual_reviewed_provider_capabilities_match_committed34(self):
        case=self.case;case.write_contracts(json.loads((UNIVERSAL/'overlay/script.infinity.commandcenter/NAVIGATION-CONTRACTS.json').read_text())['contracts'])
        proofs=json.loads((UNIVERSAL/'SPECIALTY-CONTRACTS.json').read_text())['provenance']
        for proof in proofs:
            root=HERE.parents[4]/'provider-references'/proof['fixture_directory'];aid=proof['addon'];case.paths[aid]=root
            case.rows.append(dict(addonid=aid,name=aid,path=str(root),version=proof['version'],enabled=True))
        root=Path('/workspace/scratch/9207f26886c2/pov22/plugin.video.pov');aid='plugin.video.pov';case.paths[aid]=root
        case.rows.append(dict(addonid=aid,name=aid,path=str(root),version='6.10.22',enabled=True))
        for media in ('movie','tv','anime','cartoon'):
            for operation in ('search','title_navigation','identity_lookup'):
                self.assertEqual(self.inv.eligible(media,operation,force=True),self.baseline.eligible(media,operation,force=True),(media,operation))

    def test_shared_sources_read_and_fingerprinted_once_per_cold_verification(self):
        case=self.case;aid,root=case.provider();first=deepcopy(case.spec);second=deepcopy(first)
        other=b'def operation():\n    return 1\n';(root/'operation.py').write_bytes(other)
        first['sources']['operation.py']='0'*64
        second['sources']['operation.py']=case.nav.fingerprint(other,aid)
        case.write_contracts([first,second])
        reads=[];shapes=[];source=case.nav._source;fingerprint=case.nav.fingerprint
        def read(root,name):reads.append(name);return source(root,name)
        def shape(raw,aid):shapes.append(hashlib.sha256(raw).hexdigest());return fingerprint(raw,aid)
        with patch.object(case.nav,'_source',side_effect=read),patch.object(case.nav,'fingerprint',side_effect=shape):
            ready,_=self.inv.eligible('movie',force=True)
        self.assertEqual(len(ready),1)
        self.assertEqual(reads.count('addon.xml'),1);self.assertEqual(reads.count('main.py'),1);self.assertEqual(reads.count('operation.py'),1)
        self.assertEqual(len(shapes),2)

    def test_refresh_stamps_only_manifest_matched_candidate_sources(self):
        case=self.case;case.provider();other=deepcopy(case.spec);other['entrypoint']='unrelated.py';other['sources']={'unrelated.py':'0'*64}
        case.write_contracts([case.spec,other]);seen=[];stamp=self.inv._stamp
        def record(root,names):seen.append(set(names));return stamp(root,names)
        with patch.object(self.inv,'_stamp',side_effect=record):
            self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
            self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
        self.assertTrue(seen);self.assertTrue(all('unrelated.py' not in names for names in seen))
        self.assertTrue(all('main.py' in names for names in seen))

    def test_same_version_source_manifest_disable_and_removal_still_refresh(self):
        case=self.case;aid,root=case.provider();self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
        (root/'main.py').write_bytes(case.code+b'# compatible comment\n')
        self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
        (root/'main.py').write_bytes(case.code.replace(b'return query',b'return False'))
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        (root/'main.py').write_bytes(case.code)
        (root/'addon.xml').write_text('<addon id="'+aid+'"><extension point="xbmc.python.pluginsource" library="unrelated.py"/></addon>')
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        (root/'addon.xml').write_text('<addon id="'+aid+'"><extension point="xbmc.python.pluginsource" library="main.py"/></addon>')
        self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
        case.rows[0]['enabled']=False;self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        case.rows.clear();self.assertEqual(self.inv.snapshot(force=True)['entries'],[]);self.assertEqual(self.inv._verified,{})

    def test_wrong_identity_symlink_and_changed_exact_source_fail_closed(self):
        case=self.case;aid,root=case.provider();spec=deepcopy(case.spec);spec['exact_sources']={'main.py':hashlib.sha256(case.code).hexdigest()};case.write_contracts([spec])
        self.assertEqual(len(self.inv.eligible('movie')[0]),1)
        manifest=(root/'addon.xml').read_text();(root/'addon.xml').write_text(manifest.replace(aid,'plugin.video.someoneelse'))
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        (root/'addon.xml').write_text(manifest);(root/'main.py').write_bytes(case.code.replace(b'return query',b'return False'))
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        (root/'main.py').unlink();(root/'main.py').symlink_to(case.cc/'NAVIGATION-CONTRACTS.json')
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])

    def test_submission_does_not_hash_before_firstparty_results_dispatch(self):
        case=self.case;aid,root=case.provider();dispatched=[]
        def keyboard(query,heading,hidden):
            data=json.loads(heading.split(':',1)[1]);answer=json.dumps(dict(token=data['token'],provider=aid,query='Exact title'))
            return types.SimpleNamespace(doModal=lambda:None,isConfirmed=lambda:True,getText=lambda:answer)
        sys.modules['xbmc'].Keyboard=keyboard;sys.modules['xbmc'].getInfoLabel=lambda *a:''
        sys.modules['xbmc'].executebuiltin=dispatched.append
        with patch.object(self.search,'route',side_effect=AssertionError('redundant pre-dispatch hash')):
            self.search.open_search('movie')
        self.assertEqual(len(dispatched),1);self.assertIn('plugin://script.infinity.commandcenter/?action=search-provider',dispatched[0]);self.assertIn('provider='+aid,dispatched[0])

    def test_real_request_still_validates_before_and_after_provider_execution(self):
        case=self.case;aid,root=case.provider();provider=self.inv.eligible('movie')[0][0]
        original=self.search.route;calls=[]
        def verify(*args,**kwargs):calls.append('verify');return original(*args,**kwargs)
        def leased(*args):calls.append('request');return 'completed',{'result':{'files':[]}}
        with patch.object(self.search,'route',side_effect=verify),patch.object(self.search,'_leased_directory',side_effect=leased):
            answer=self.search._provider_result(provider,'Exact title',case.home,self.search._Cancellation())
        self.assertEqual(calls,['verify','request','verify']);self.assertEqual(answer[1],'completed')
        (root/'main.py').write_bytes(case.code.replace(b'return query',b'return False'))
        with patch.object(self.search,'_leased_directory',side_effect=AssertionError('changed source must not execute')):
            self.assertEqual(self.search._provider_result(provider,'Other',case.home,self.search._Cancellation())[1],'unavailable')


if __name__=='__main__':unittest.main(verbosity=2)
