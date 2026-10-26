"""Prelaunch fixture boundaries only; no host result is a device PASS."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import android_stress_fixture as fixture


class StressFixtureTests(unittest.TestCase):
    def context(self, root, **changes):
        expected = dict(candidate_apk_sha256='a'*64, post_feature=dict(fixture.COUNTS))
        receipt = dict(candidate_sha256='a'*64, baseline_launched=False,
                       test_sentinel_preserved=True, uninstall_or_data_clear=False)
        (root/'INSTALL-OVER-EVIDENCE.json').write_text(json.dumps(receipt))
        class Device:
            PACKAGE = fixture.PACKAGE
            PROFILE = fixture.PROFILE
            def __init__(self):
                self.calls = []; self.data = {}; self.qemu = '1'; self.sdk = '37'
                self.pid = ''; self.engine = None; self.exists = False; self.link = False
            def shell(self, *args, **kw):
                self.calls.append(args)
                if args == ('getprop', 'ro.kernel.qemu'): return self.qemu
                if args == ('getprop', 'ro.build.version.sdk'): return self.sdk
                if args[0] == 'pidof': return self.pid
                if args[:2] == ('test', '!'):
                    if (args[2]=='-e' and self.exists) or (args[2]=='-L' and self.link):
                        raise RuntimeError('Existing file or symlink refused')
                if args[0]=='cat': return self.data.get(args[1], '')
                return ''
            def running_engine(self): return self.engine
            def adb(self, *args):
                self.calls.append(args)
                if args[0]=='push': self.data[args[2]]=Path(args[1]).read_text()
        device = Device()
        for key, value in changes.items(): setattr(device, key, value)
        return (device, SimpleNamespace(case='final-search-all-enter', out=root),
                {'apk_sha256':'a'*64}, expected)

    def test_exact_retained_movie_aliases_and_separate_episodes_are_reused(self):
        raw=(fixture.OLD/'tracking/final-eight/android_selected.py').read_bytes()
        state=fixture.retained_state(raw)
        self.assertEqual(set(state['items']), {c*64 for c in 'abcd'})
        self.assertEqual(state['items']['a'*64]['identity']['ids'], {'tmdb':'603','imdb':'tt0133093'})
        self.assertEqual(state['items']['b'*64]['identity']['ids'], {'imdb':'tt0133093'})
        self.assertEqual([state['items'][c*64]['episode'] for c in 'cd'], [3,2])
        self.assertTrue(state['navigation_recovery']['unrelated']['retained_sentinel'])
        with self.assertRaises(ValueError): fixture.retained_state(raw+b'\n')

    def test_prelaunch_seed_reads_back_exact_nonempty_fixture_without_runtime_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);device,args,report,expected=self.context(root)
            fixture.seed(device,args,report,expected)
            path=fixture.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json'
            self.assertEqual(len(json.loads(device.data[path])['items']),4)
            self.assertEqual(device.data[path],(root/'prelaunch-stress-tracking-fixture.json').read_text())
            proof=json.loads((root/'STRESS-FIXTURE-SEED.json').read_text())
            self.assertTrue(proof['readback_matches'])
            self.assertFalse(proof['runtime_writer_authority_added'])
            self.assertFalse(proof['existing_profile_replaced'])
            self.assertEqual(len([c for c in device.calls if c[0]=='push']),1)
            self.assertEqual([c[0] for c in device.calls if c[0] not in ('getprop','pidof','test','mkdir','push','cat')],[])

    def test_physical_wrong_api_live_engine_existing_file_and_link_refused_before_write(self):
        for changes in ({'qemu':'0'},{'sdk':'36'},{'pid':'123'}, {'engine':{'pid':123}},
                        {'exists':True},{'link':True},{'PROFILE':'/other/profile'}, {'PACKAGE':'other'}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temp:
                root=Path(temp);device,args,report,expected=self.context(root,**changes)
                with self.assertRaises((ValueError,RuntimeError)):fixture.seed(device,args,report,expected)
                self.assertFalse(any(c[0]=='push' for c in device.calls))
                self.assertFalse((root/'STRESS-FIXTURE-SEED.json').exists())

    def test_wrong_candidate_selection_and_missing_installover_admission_refused(self):
        for mode in ('sha','case','unselected','launched','sentinel','receipt','missing-sha'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root=Path(temp);device,args,report,expected=self.context(root)
                if mode=='sha':report['apk_sha256']='b'*64
                elif mode=='case':args.case='final-participant'
                elif mode=='unselected':expected.pop('post_feature')
                elif mode=='missing-sha':expected.pop('candidate_apk_sha256');report.pop('apk_sha256')
                elif mode=='receipt':(root/'INSTALL-OVER-EVIDENCE.json').unlink()
                else:
                    p=root/'INSTALL-OVER-EVIDENCE.json';data=json.loads(p.read_text())
                    data['baseline_launched' if mode=='launched' else 'test_sentinel_preserved']=(mode=='launched')
                    p.write_text(json.dumps(data))
                with self.assertRaises((ValueError,FileNotFoundError)):fixture.seed(device,args,report,expected)
                self.assertFalse(any(c[0]=='push' for c in device.calls))


if __name__=='__main__':unittest.main(verbosity=2)
