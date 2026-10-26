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
import native_tv_observer as observer
import android17_candidate_probe as candidate
from android17_reference_observation import OLD


class NativeTVFixtureTests(unittest.TestCase):
    def test_only_actual_played_title_may_update_successful_source_memory(self):
        before={'foreign':{'route':'untouched original provider','failures':0,'updated':1}}
        source=observer.FOLDER+'QA.S01E02.mp4'
        after=dict(before,**{'d'*64:dict(route=source,failures=0,updated=2)})
        self.assertTrue(observer.source_memory_preserved(before,after,'d'*64,source))
        for bad in (dict(after,foreign={'route':'changed'}),dict(after,unexpected={'route':source}),
                    dict(before),dict(after,**{'d'*64:dict(route='/stale/other.mp4',failures=0,updated=2)}),
                    dict(after,**{'d'*64:dict(route=source,failures=1,updated=2)})):
            self.assertFalse(observer.source_memory_preserved(before,bad,'d'*64,source))
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

    def test_native_seek_requires_advancing_clock_inside_original_start_deadline(self):
        text=Path(observer.__file__).read_text()
        self.assertIn("'properties':['time','speed']",text)
        self.assertIn("clock.get('speed')==1",text)
        self.assertIn("stamp.get('seconds',0)>=1",text)
        self.assertIn("ui.until(started,'actual typed native TV playback',max(0,20-(time.monotonic()-began)))",text)
        self.assertIn("tracking_ready(state(),old_occurrence)",text)
        self.assertLess(text.index("clock=ui.rpc("),text.index('player.seekTime(70)'))

    def test_new_TV_scene_uses_native_Stop_and_retains_exact_state_checks(self):
        text=Path(observer.__file__).read_text()
        self.assertNotIn('player.stop()',text)
        self.assertEqual(text.count("ui.rpc('Player.Stop',{'playerid':1})"),3)
        self.assertIn("ui.until(lambda:not active(),'native TV stop',20)",text)
        self.assertIn("'native completed TV stopped',20",text)
        self.assertIn("'selected Next stopped',20",text)
        self.assertIn('source_memory_preserved',text)
        self.assertIn("observe(name)",text)

    def test_new_occurrence_requires_native_played_source_without_replacing_original_navigation(self):
        value=dict(items={'d'*64:dict(playback_occurrence='2'*32,show_ids_verified=True,
            identity=dict(schema=1,kind='episode',scope='show_episode',ids={'tmdb':'1396'},season=1,episode=2),
            source='special://profile/original-title-navigation.mp4')},
            sources={'d'*64:dict(route=observer.FOLDER+'QA.S01E02.mp4',failures=0)})
        self.assertTrue(observer.tracking_ready(value,'1'*32))
        self.assertFalse(observer.tracking_ready(value,'2'*32))
        for bucket,field,bad in [('sources','route','/unrelated.mp4'),('sources','failures',1),
                                 ('items','show_ids_verified',False),('items','playback_occurrence','not-a-real-token')]:
            changed=deepcopy(value);changed[bucket]['d'*64][field]=bad
            self.assertFalse(observer.tracking_ready(changed,'1'*32))
        changed=deepcopy(value);changed['items']['d'*64]['identity']['episode']=3
        self.assertFalse(observer.tracking_ready(changed,'1'*32))


if __name__=='__main__':unittest.main(verbosity=2)
