import ast
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import native_tv_fixture as fixture
import android17_candidate_probe as candidate
from android17_reference_observation import OLD


class NativeTVFixtureTests(unittest.TestCase):
    def test_real131_schema_views_exact_parent_episode_coordinates_and_existing_db_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            path=fixture.database(Path(temp)/'MyVideos131.db')
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('pragma integrity_check').fetchone(),('ok',))
                self.assertEqual(db.execute('select idVersion from version').fetchone(),(131,))
                self.assertEqual(db.execute('select idShow,c00,uniqueid_value,totalCount from tvshow_view').fetchall(),
                                 [(1,'Breaking Bad','1396',2)])
                self.assertEqual(db.execute('select idEpisode,idShow,c12,c13,strPath,strFilename from episode_view order by idEpisode').fetchall(),
                    [(dbid,1,str(season),str(ep),fixture.FOLDER,file) for dbid,season,ep,file,_ in fixture.EPISODES])
                self.assertEqual(db.execute('select count(*) from movie').fetchone(),(0,))
            with self.assertRaises(ValueError):fixture.database(path)

    def device(self,qemu='1',sdk='37',engine=None,corrupt=False):
        files={};dirs=set();events=[]
        def shell(*args,**kwargs):
            events.append(('shell',args))
            if args==('getprop','ro.kernel.qemu'):return qemu
            if args==('getprop','ro.build.version.sdk'):return sdk
            if args[0]=='pidof':return ''
            if args[:3]==('test','!','-e') or args[:3]==('test','!','-L'):
                if args[3] in files or args[3] in dirs:raise RuntimeError('Existing target')
                return ''
            if args[:2]==('mkdir','-p'):dirs.add(args[2]);return ''
            raise AssertionError(args)
        def adb(*args,check=True,binary=False):
            events.append(('adb',args[:1]))
            if args[0]=='push':
                local=Path(args[1]);target=str(args[2])
                if local.is_dir():
                    for p in local.rglob('*'):
                        if p.is_file():files[target+'/'+p.relative_to(local).as_posix()]=p.read_bytes()
                else:files[target]=local.read_bytes()
                return 'pushed'
            if args[:2]==('exec-out','cat'):
                self.assertTrue(binary);key=str(args[2]).replace('/storage/emulated/0/','/sdcard/')
                return b'wrong' if corrupt else files[key]
            raise AssertionError(args)
        device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',PROFILE=fixture.PROFILE,
            shell=shell,adb=adb,running_engine=lambda:engine)
        return device,events,files

    def setup(self,path):
        args=SimpleNamespace(case='final-continue',out=path)
        (path/'final-profile').mkdir();(path/'final-profile/infinity-final-qa.mp4').write_bytes(b'format-only transport fixture')
        expected=dict(candidate_apk_sha256='a'*64,verify_tv_completion=True)
        (path/'INSTALL-OVER-EVIDENCE.json').write_text(json.dumps(dict(candidate_sha256='a'*64,
            baseline_launched=False,test_sentinel_preserved=True,uninstall_or_data_clear=False)))
        return args,expected,dict(generated_clip_format={'fps':24})

    def test_only_fresh_disposable_installover_can_seed_and_actual_bytes_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            args,expected,report=self.setup(Path(temp));device,events,files=self.device()
            fixture.stage(device,args,report,expected)
            self.assertTrue(report['native_TV_fixture']['before_first_launch'])
            self.assertFalse(report['native_TV_fixture']['replaced_existing_database'])
            self.assertEqual(len(report['native_TV_fixture']['readback_sha256']),3)
        for options in (dict(qemu='0'),dict(sdk='36'),dict(engine={'pid':1})):
            with tempfile.TemporaryDirectory() as temp:
                args,expected,report=self.setup(Path(temp));device,events,files=self.device(**options)
                with self.assertRaises(ValueError):fixture.stage(device,args,report,expected)
                self.assertFalse(files);self.assertFalse(any(e[0]=='adb' for e in events))
        with tempfile.TemporaryDirectory() as temp:
            args,expected,report=self.setup(Path(temp));device,_,_=self.device(corrupt=True)
            with self.assertRaises(ValueError):fixture.stage(device,args,report,expected)

    def test_wrong_case_or_existing_target_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            args,expected,report=self.setup(Path(temp));device,_,files=self.device()
            args.case='final-actions'
            with self.assertRaises(ValueError):fixture.stage(device,args,report,expected)
            args.case='final-continue';target=fixture.PROFILE+'/Database/MyVideos131.db';files[target]=b'preexisting sentinel'
            with self.assertRaises(RuntimeError):fixture.stage(device,args,report,expected)
            self.assertEqual(files[target],b'preexisting sentinel')

    def test_optional_extension_retains_each_original_assertion_and_full_inverse(self):
        raw=(OLD/'tracking/final-eight/android_selected.py').read_bytes()
        with patch.dict(candidate.EXPECTED,verify_tv_completion=True):
            updated=candidate.fixture(raw).decode()
        self.assertIn(fixture.TAIL,updated)
        from android17_reference_observation import restore_fixture
        self.assertEqual(restore_fixture(candidate.restore_candidate_fixture(updated)).encode(),raw)
        def predicates(text):
            return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
                    and n.func.value.id=='ui' and n.func.attr=='require']
        self.assertEqual(predicates(restore_fixture(updated)),predicates(raw))
        observer=(Path(fixture.__file__).with_name('native_tv_observer.py')).read_text()
        self.assertNotIn('controller_access',observer);self.assertNotIn('import resume_hub',observer)
        for forbidden in ('write_text','write_bytes','sqlite3','force-stop','CLOSE_KODI'):
            self.assertNotIn(forbidden,observer)


if __name__=='__main__':unittest.main(verbosity=2)
