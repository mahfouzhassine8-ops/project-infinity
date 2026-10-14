import copy
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

WORK=Path(__file__).resolve().parents[1]
ADDON=WORK/'addons/script.infinity.rails'
sys.path.insert(0,str(ADDON/'resources'))
from lib import store, catalog, runtime
import legacy_installer as installer


def add_process(profile, aid):
    store.Store(profile).add(aid,['movies'],{})

class TempCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()

class PreferencesTests(TempCase):
    def setUp(self):
        super().setUp();self.s=store.Store(self.root)
    def test_first_read_creates_no_files(self):
        self.assertEqual(self.s.load(),(store.empty_state(),'')); self.assertFalse(self.s.path.exists())
    def test_add_movies(self):
        added,rev=self.s.add('plugin.video.fixture',['movies'],{});self.assertEqual(added,['movies']);self.assertEqual(rev,1)
        self.assertEqual(self.s.load()[0]['rails']['tvshows']['custom'],[])
    def test_add_tv(self):
        self.s.add('plugin.video.fixture',['tvshows'],{});self.assertEqual(self.s.load()[0]['rails']['movies']['custom'],[])
    def test_both_committed_together(self):
        added,rev=self.s.add('plugin.video.fixture',list(store.SECTIONS),{});self.assertEqual(added,list(store.SECTIONS));self.assertEqual(rev,1)
    def test_duplicate_does_not_rewrite_or_increment(self):
        self.s.add('plugin.video.fixture',['movies'],{});before=self.s.path.read_bytes();result,rev=self.s.add('plugin.video.fixture',['movies'],{})
        self.assertEqual(result,[]);self.assertEqual(rev,1);self.assertEqual(before,self.s.path.read_bytes())
    def test_builtin_duplicate_prevented(self):
        result,rev=self.s.add('plugin.video.fixture',['movies'],{'movies':['plugin.video.fixture']});self.assertEqual(result,[]);self.assertEqual(rev,0)
    def test_both_when_already_in_one(self):
        self.s.add('plugin.video.fixture',['movies'],{});result,rev=self.s.add('plugin.video.fixture',list(store.SECTIONS),{})
        self.assertEqual(result,['tvshows']);self.assertEqual(rev,2)
    def test_remove_one_rail_only(self):
        self.s.add('plugin.video.fixture',list(store.SECTIONS),{});self.s.remove('movies','plugin.video.fixture')
        data,_=self.s.load();self.assertEqual(data['rails']['movies']['custom'],[]);self.assertEqual(data['rails']['tvshows']['custom'],['plugin.video.fixture'])
    def test_remove_missing_is_noop(self):
        self.assertEqual(self.s.remove('movies','plugin.video.none'),(False,0))
    def test_new_interpreter_store_loads_exact_state(self):
        self.s.add('plugin.video.fixture',list(store.SECTIONS),{});self.assertEqual(self.s.load(),store.Store(self.root).load())
    def test_profile_isolation(self):
        self.s.add('plugin.video.fixture',['movies'],{});other=store.Store(self.root/'other');self.assertEqual(other.load()[0],store.empty_state())
    def test_default_order_unchanged_until_move(self):
        self.s.add('plugin.video.fixture',['movies'],{});p=self.s.load()[0]['rails']['movies'];self.assertEqual(store.ordered_tokens(['b:'+'a'*16,'b:'+'b'*16],p),['b:'+'a'*16,'b:'+'b'*16,'c:plugin.video.fixture'])
    def test_custom_move_before_first(self):
        self.s.add('plugin.video.fixture',['movies'],{});d=['b:'+'a'*16,'b:'+'b'*16];self.s.move('movies','c:plugin.video.fixture',d[0],d)
        self.assertEqual(store.ordered_tokens(d,self.s.load()[0]['rails']['movies'])[0],'c:plugin.video.fixture')
    def test_custom_move_between_existing(self):
        self.s.add('plugin.video.fixture',['movies'],{});d=['b:'+'a'*16,'b:'+'b'*16];self.s.move('movies','c:plugin.video.fixture',d[1],d)
        self.assertEqual(store.ordered_tokens(d,self.s.load()[0]['rails']['movies'])[1],'c:plugin.video.fixture')
    def test_custom_move_last(self):
        self.s.add('plugin.video.fixture',['movies'],{});d=['b:'+'a'*16,'b:'+'b'*16];self.s.move('movies','c:plugin.video.fixture',d[0],d);self.s.move('movies','c:plugin.video.fixture',None,d)
        self.assertEqual(store.ordered_tokens(d,self.s.load()[0]['rails']['movies'])[-1],'c:plugin.video.fixture')
    def test_default_cards_can_move_without_removal(self):
        d=['b:'+'a'*16,'b:'+'b'*16];self.s.move('movies',d[1],d[0],d);self.assertEqual(self.s.load()[0]['rails']['movies']['order'],list(reversed(d)))
    def test_move_same_is_noop(self):
        d=['b:'+'a'*16];self.assertEqual(self.s.move('movies',d[0],d[0],d),(False,0))
    def test_stale_move_rejected(self):
        with self.assertRaises(store.RailError):self.s.move('movies','c:plugin.missing',None,[])
    def test_disabled_entries_keep_saved_order(self):
        self.s.add('plugin.video.fixture',['movies'],{});before=self.s.path.read_bytes();self.s.load();self.assertEqual(before,self.s.path.read_bytes())
    def test_backup_is_previous_valid_commit(self):
        self.s.add('plugin.video.one',['movies'],{});old=self.s.path.read_bytes();self.s.add('plugin.video.two',['movies'],{});self.assertEqual(self.s.backup.read_bytes(),old)
    def test_corrupt_primary_recovers_read_only(self):
        self.s.add('plugin.video.one',['movies'],{});self.s.add('plugin.video.two',['movies'],{});self.s.path.write_bytes(b'{bad')
        state,warning=self.s.load();self.assertTrue(warning);self.assertEqual(state['revision'],1);self.assertEqual(self.s.path.read_bytes(),b'{bad')
    def test_corrupt_primary_blocks_mutation(self):
        self.s.path.write_bytes(b'broken')
        with self.assertRaises(store.CorruptStore):self.s.add('plugin.video.one',['movies'],{})
        self.assertEqual(self.s.path.read_bytes(),b'broken')
    def test_bad_primary_and_backup_use_default_without_deletion(self):
        self.s.path.write_bytes(b'bad');self.s.backup.write_bytes(b'worse');state,warn=self.s.load();self.assertEqual(state,store.empty_state());self.assertTrue(warn)
    def test_unknown_schema_preserved(self):
        data=store.empty_state();data['schema']=99;self.s.path.write_text(json.dumps(data));self.assertTrue(self.s.load()[1]);self.assertEqual(json.loads(self.s.path.read_text())['schema'],99)
    def test_boolean_schema_rejected(self):
        data=store.empty_state();data['schema']=True
        with self.assertRaises(store.CorruptStore):store.validate(data)
    def test_oversize_file_bounded(self):
        self.s.path.write_bytes(b' '* (store.MAX_BYTES+1));self.assertTrue(self.s.load()[1])
    def test_injection_ids_rejected(self):
        for aid in ['../bad','plugin.video.x,Quit()','plugin://x','a/b','x\n','',None,'x"y']:
            with self.subTest(aid=aid),self.assertRaises(store.RailError):self.s.add(aid,['movies'],{})
    def test_invalid_destination_rejected(self):
        for dest in [[],['sports'],['movies','bad']]:
            with self.subTest(dest=dest),self.assertRaises(store.RailError):self.s.add('plugin.video.x',dest,{})
    def test_limit_both_is_atomic(self):
        def seed(d):d['rails']['tvshows']['custom']=['plugin.video.x'+str(i) for i in range(store.LIMIT)]
        self.s.change(seed);before=self.s.path.read_bytes()
        with self.assertRaises(store.RailError):self.s.add('plugin.video.new',list(store.SECTIONS),{})
        self.assertEqual(self.s.path.read_bytes(),before)
    def test_abort_blocks_new_work(self):
        with self.assertRaises(store.RailError):store.Store(self.root,lambda:True).add('plugin.video.x',['movies'],{})
        self.assertFalse(self.s.path.exists())
    def test_atomic_replace_failure_preserves_primary(self):
        self.s.add('plugin.video.one',['movies'],{});old=self.s.path.read_bytes();real=store.os.replace
        def fail(src,dst):
            if Path(dst)==self.s.path:raise OSError('simulated disk failure')
            return real(src,dst)
        with patch.object(store.os,'replace',side_effect=fail),self.assertRaises(OSError):self.s.add('plugin.video.two',['movies'],{})
        self.assertEqual(self.s.path.read_bytes(),old);self.assertFalse(list(self.root.glob('.rails.json.*')))
    def test_advisory_lock_has_timeout(self):
        with store.locked(self.root):
            with self.assertRaises(store.RailError):
                with store.locked(self.root,timeout=0.04):pass
    def test_processes_do_not_lose_updates(self):
        ps=[multiprocessing.Process(target=add_process,args=(str(self.root),'plugin.video.'+str(i))) for i in range(4)]
        for p in ps:p.start()
        for p in ps:p.join(4);self.assertEqual(p.exitcode,0)
        data,_=self.s.load();self.assertEqual(len(data['rails']['movies']['custom']),4);self.assertEqual(data['revision'],4)
    def test_unrelated_user_files_preserved(self):
        p=self.root/'settings.xml';p.write_bytes(b'untouched');self.s.add('plugin.video.x',['movies'],{});self.s.remove('movies','plugin.video.x');self.assertEqual(p.read_bytes(),b'untouched')

class Item:
    def __init__(self,path='',props=None):self.path=path;self.props=props or {}
    def getProperty(self,key):return self.props.get(key,'')
    def getPath(self):return self.path

class CatalogTests(TempCase):
    def setUp(self):
        super().setUp();self.raw=(ADDON/'resources/defaults.xml').read_bytes();self.data=catalog.default_catalog(self.raw)
    def test_exact_default_counts(self):self.assertEqual([len(self.data[s]) for s in store.SECTIONS],[10,11])
    def test_movie_and_tv_umbrella_actions_differ(self):self.assertIn('movieNavigator',self.data['movies'][1]['uri']);self.assertIn('tvNavigator',self.data['tvshows'][1]['uri'])
    def test_all_default_actions_roundtrip_exactly(self):
        for sec,rows in self.data.items():
            for r in rows:self.assertEqual(r['action'],'ActivateWindow(Videos,"'+r['uri']+'",return)')
    def test_source_names_art_and_visibilities_retained(self):
        original=ET.fromstring(self.raw).find("./include[@name='skinshortcuts-submenu-2']")
        selected=[x for x in original.findall('item') if catalog.SECTION.search(x.findtext('visible',''))]
        for item,row in zip(selected,self.data['movies']+self.data['tvshows']):
            self.assertEqual(item.findtext('label'),row['label']);self.assertEqual(item.findtext('thumb'),row['thumb']);self.assertEqual(item.findtext('visible'),row['visible'])
    def test_context_prefers_supplied_addon_identity(self):self.assertEqual(catalog.resolve_selected(Item('plugin://wrong',{'Addon.ID':'plugin.video.right'})),'plugin.video.right')
    def test_context_accepts_root_plugin_uri(self):self.assertEqual(catalog.resolve_selected(Item('plugin://plugin.video.x/')),'plugin.video.x')
    def test_context_accepts_installed_addon_browser_path(self):self.assertEqual(catalog.resolve_selected(Item('addons://user/plugin.video.x')),'plugin.video.x')
    def test_context_rejects_episode_and_repository(self):
        for path in ['plugin://plugin.video.x/movies','addons://all/plugin.video.x','https://example.org','plugin://plugin.video.x/episodes?id=1']:
            with self.subTest(path=path),self.assertRaises(store.RailError):catalog.resolve_selected(Item(path))
    def test_xml_entities_rejected(self):
        with self.assertRaises(store.RailError):catalog.default_catalog(b'<!DOCTYPE a [<!ENTITY b "c">]><includes/>')
    def test_unknown_builtin_action_refused(self):
        raw=self.raw.replace(b'ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper",return)',b'Quit()')
        with self.assertRaises(store.RailError):catalog.default_catalog(raw)
    def test_merge_empty_preserves_all_defaults(self):self.assertEqual(catalog.merge(self.data,store.empty_state(),'movies',lambda aid:None),self.data['movies'])
    def test_missing_addon_is_hidden_not_deleted(self):
        state=store.empty_state();state['rails']['movies']['custom']=['plugin.video.missing'];original=copy.deepcopy(state)
        self.assertEqual(catalog.merge(self.data,state,'movies',lambda aid:None),self.data['movies']);self.assertEqual(state,original)
    def test_reinstall_restores_saved_position(self):
        s=store.Store(self.root);s.add('plugin.video.x',['movies'],{});d=[r['key'] for r in self.data['movies']];s.move('movies','c:plugin.video.x',d[0],d)
        state,_=s.load();missing=catalog.merge(self.data,state,'movies',lambda aid:None);restored=catalog.merge(self.data,state,'movies',lambda aid:dict(key='c:'+aid,addon_id=aid))
        self.assertEqual(missing[0]['key'],d[0]);self.assertEqual(restored[0]['key'],'c:plugin.video.x')
    def test_new_builtin_deduplicates_old_custom(self):
        s=store.empty_state();s['rails']['movies']['custom']=[self.data['movies'][0]['addon_id']]
        self.assertEqual(catalog.merge(self.data,s,'movies',lambda a:dict(key='c:'+a)),self.data['movies'])

class InstalledMetadataTests(TempCase):
    def card(self,xml,enabled=True,aid='plugin.video.fixture'):
        self.root.joinpath('addon.xml').write_text(xml)
        class Xbmc:
            def getCondVisibility(self,condition):return enabled
        class Addon:
            def getAddonInfo(obj,key):return {'path':str(self.root),'icon':'special://home/icon.png','name':'Fixture'}[key]
        class XA:
            def Addon(obj,name):return Addon()
        class VFS:
            def translatePath(obj,path):return path
        return catalog.installed_card(aid,Xbmc(),XA(),VFS())
    def test_video_plugin(self):
        c=self.card('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource"><provides>video</provides></extension></addon>');self.assertTrue(c['is_folder']);self.assertEqual(c['uri'],'plugin://plugin.video.fixture')
    def test_multiple_content_plugin_preserves_video_entry(self):
        c=self.card('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource"><provides>video audio</provides></extension></addon>');self.assertTrue(c['uri'].endswith('content_type=video'))
    def test_video_script(self):
        c=self.card('<addon id="plugin.video.fixture"><extension point="xbmc.python.script"><provides>video</provides></extension></addon>');self.assertEqual(c['uri'],'script://plugin.video.fixture');self.assertFalse(c['is_folder'])
    def test_audio_only_excluded(self):self.assertIsNone(self.card('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource"><provides>audio</provides></extension></addon>'))
    def test_service_excluded(self):self.assertIsNone(self.card('<addon id="plugin.video.fixture"><extension point="xbmc.service"><provides>video</provides></extension></addon>'))
    def test_disabled_excluded(self):self.assertIsNone(self.card('<addon id="plugin.video.fixture"/>',False))
    def test_id_mismatch_excluded(self):self.assertIsNone(self.card('<addon id="plugin.video.other"/>'))
    def test_malformed_metadata_excluded(self):self.assertIsNone(self.card('<broken'))
    def test_entities_excluded(self):self.assertIsNone(self.card('<!DOCTYPE test><addon id="plugin.video.fixture"/>'))
    def test_large_metadata_bounded(self):self.assertIsNone(self.card(' '*131073))
    def test_art_uses_installed_addon(self):
        c=self.card('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource"><provides>video</provides></extension></addon>');self.assertEqual(c['thumb'],'special://home/icon.png');self.assertEqual(c['label'],'Fixture')

class InstallerTests(TempCase):
    def setUp(self):
        super().setUp();self.skin=self.root/'skin';self.skin.mkdir();self.profile=self.root/'profile';self.payload=self.root/'payload';(self.payload/'objects').mkdir(parents=True)
        self.before={'addon.xml':b'<addon version="1.0.5.215"/>','unified/Home.xml':b'<window>original</window>'}
        self.after={'addon.xml':b'<addon version="1.0.5.216"/>','unified/Home.xml':b'<window>rails</window>','unified/Includes_InfinityRails.xml':b'<includes/>'}
        files={}
        for n,b in self.before.items():p=self.skin/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for n,b in self.after.items():
            d=installer.digest(b);(self.payload/'objects'/d).write_bytes(b);files[n]={'before':installer.digest(self.before[n]) if n in self.before else None,'after':d,'bytes':len(b)}
        (self.payload/'manifest.json').write_text(json.dumps({'base_version':'1.0.5.215','version':'1.0.5.216','files':files}))
        self.i=installer.Installer(self.skin,self.profile,self.payload)
    def test_refuses_wrong_base_file(self):
        (self.skin/'unified/Home.xml').write_bytes(b'other');
        with self.assertRaises(store.RailError):self.i.apply()
        self.assertEqual((self.skin/'addon.xml').read_bytes(),self.before['addon.xml'])
    def test_apply_verify_and_version(self):self.i.apply();self.assertEqual(self.i.status()[0],'candidate')
    def test_exact_rollback(self):
        self.i.apply();self.i.rollback();self.assertEqual(self.i.status()[0],'parent');self.assertEqual((self.skin/'unified/Home.xml').read_bytes(),self.before['unified/Home.xml'])
    def test_new_file_removed_on_rollback(self):self.i.apply();self.i.rollback();self.assertFalse((self.skin/'unified/Includes_InfinityRails.xml').exists())
    def test_repeat_apply_is_noop(self):self.i.apply();self.assertEqual(self.i.apply(),'already_applied')
    def test_reapply_after_restore(self):self.i.apply();self.i.rollback();self.i.apply();self.assertEqual(self.i.status()[0],'candidate')
    def test_unrelated_files_not_written(self):
        p=self.skin/'CommandCenter.txt';p.write_bytes(b'protected');self.i.apply();self.i.rollback();self.assertEqual(p.read_bytes(),b'protected')
    def test_payload_tamper_refused_before_skin_writes(self):
        row=self.i.entries['unified/Home.xml'];(self.payload/'objects'/row['after']).write_bytes(b'bad')
        with self.assertRaises(store.RailError):self.i.apply()
        self.assertEqual(self.i.status()[0],'parent')
    def test_new_file_collision_refused(self):
        p=self.skin/'unified/Includes_InfinityRails.xml';p.write_bytes(b'unknown')
        with self.assertRaises(store.RailError):self.i.apply()
        self.assertEqual(p.read_bytes(),b'unknown')
    def test_missing_rollback_backup_refused(self):
        self.i.apply();p=self.i._original_path(self.i.entries['addon.xml']['before']);p.unlink()
        with self.assertRaises(store.RailError):self.i.rollback()
        self.assertEqual(self.i.status()[0],'candidate')
    def test_later_skin_never_overwritten(self):
        self.i.apply();(self.skin/'addon.xml').write_bytes(b'<addon version="1.0.5.217"/>')
        with self.assertRaises(store.RailError):self.i.rollback()
        self.assertIn(b'217',(self.skin/'addon.xml').read_bytes())
    def test_interrupted_update_resumes_with_record(self):
        self.i.apply();(self.skin/'addon.xml').write_bytes(self.before['addon.xml']);self.assertEqual(self.i.status()[0],'mixed');self.i.apply();self.assertEqual(self.i.status()[0],'candidate')
    def test_partial_update_without_record_rejected(self):
        (self.skin/'addon.xml').write_bytes(self.after['addon.xml'])
        with self.assertRaises(store.RailError):self.i.apply()
    def test_write_failure_automatic_rollback(self):
        real=installer.atomic_bytes;failed=[]
        def fail(path,data):
            if Path(path)==self.skin/'unified/Home.xml' and data==self.after['unified/Home.xml'] and not failed:
                failed.append(True);raise OSError('disk failure')
            return real(path,data)
        with patch.object(installer,'atomic_bytes',side_effect=fail),self.assertRaises(OSError):self.i.apply()
        self.assertEqual(self.i.status()[0],'parent')
    def test_metadata_written_last(self):
        writes=[];real=installer.atomic_bytes
        def record(path,data):
            if self.skin in Path(path).parents:writes.append(Path(path).relative_to(self.skin).as_posix())
            return real(path,data)
        with patch.object(installer,'atomic_bytes',side_effect=record):self.i.apply()
        self.assertEqual(writes[-1],'addon.xml')
    def test_path_traversal_refused(self):
        for n in ['../evil.xml','/tmp/evil.xml','unified/../../evil.xml','bad.py','bad.ttf']:
            with self.subTest(n=n),self.assertRaises(store.RailError):self.i.target(n)
    def test_symlink_escape_refused(self):
        (self.skin/'outside').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(store.RailError):self.i.target('outside/evil.xml')
    def test_abort_before_apply_preserves_everything(self):
        self.i.abort=lambda:True
        with self.assertRaises(store.RailError):self.i.apply()
        self.assertEqual(self.i.status()[0],'parent')
    def test_preferences_survive_rollback(self):
        prefs=store.Store(self.profile);prefs.add('plugin.video.x',['movies'],{});before=prefs.path.read_bytes();self.i.apply();self.i.rollback();self.assertEqual(prefs.path.read_bytes(),before)

if __name__=='__main__':unittest.main(verbosity=2)
