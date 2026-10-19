"""Read-only existing in-app Home/Continue Watching diagnostic tests."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from home_reload_correlation import analyze

class HomeCorrelation(unittest.TestCase):
    def zip(self,events=None,requests=()):
        temp=tempfile.NamedTemporaryFile(suffix='.zip',delete=False);temp.close()
        with ZipFile(temp.name,'w') as z:
            if events is not None:z.writestr('skin/continuity.json',json.dumps({'events':events,'process':'private:id'}))
            if requests is not None:z.writestr('resume/timing-current.jsonl','\n'.join(json.dumps(x) for x in requests))
        self.addCleanup(lambda:Path(temp.name).unlink(missing_ok=True))
        return Path(temp.name)

    def test_01_two_home_generations_prove_reinit_not_cause(self):
        one='a'*32;two='b'*32
        z=self.zip(events=[{'event':'state','home_load':one},{'event':'state','home_load':one},
                           {'event':'state','home_load':two}],requests=[{'media':'movie','stage':'native_start'}])
        r=analyze(z)
        self.assertEqual(r['distinct_sequential_home_loads'],2)
        self.assertTrue(r['home_reinitialized_at_least_once'])
        self.assertFalse(r['cause_proven'])
        self.assertEqual(r['starts_by_media'],{'movie':1})

    def test_02_directory_jobs_alone_no_home_claim(self):
        z=self.zip(events=None,requests=[{'media':'movie','stage':'native_start'},
                                             {'media':'tv','stage':'native_start'}])
        r=analyze(z)
        self.assertFalse(r['home_reinitialized_at_least_once'])
        self.assertEqual(r['repeat_directory_starts'],2)
        self.assertFalse(r['cause_proven'])

    def test_03_invalid_or_private_fields_never_echo(self):
        z=self.zip(events=[{'event':'state','home_load':'private-secret', 'source':'plugin://auth?token=secret', 'process':'private:id'},
                           {'event':'state','home_load':'1'*32}],requests=[])
        r=analyze(z);serialized=json.dumps(r)
        self.assertNotIn('secret',serialized);self.assertNotIn('private',serialized)
        self.assertEqual(r['distinct_sequential_home_loads'],1)

    def test_04_missing_sources_report_missing(self):
        z=self.zip(events=None,requests=None)
        r=analyze(z)
        self.assertFalse(r['continuity_export_found'])
        self.assertFalse(r['timing_export_found'])
        self.assertEqual(r['repeat_directory_starts'],0)

if __name__=='__main__':unittest.main(verbosity=2)
