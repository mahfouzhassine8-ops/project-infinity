"""Read-only diagnostic/privacy checks. No device/user collection is read."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
SCRIPT=HERE/'diagnostics/infinity_search_state_probe.py'
spec=importlib.util.spec_from_file_location('favorites_probe',SCRIPT)
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class FavoritesProbe(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.profile=self.root/'PRIVATE-PROFILE';self.profile.mkdir()
        self.system=self.root/'system';self.system.mkdir()
        self.file=self.profile/'favourites.xml'
        self.file.write_text('<favourites><favourite name="PRIVATE-TITLE" thumb="PRIVATE-ART">PlayMedia("PRIVATE-PATH")</favourite></favourites>')
        self.directory={'state':'completed','total':1,'returned':1}
        self.api={'state':'completed','total':1,'returned':1}
        self.ui={'active':True,'container_items':1,'current_item_is_parent':True}
        self.calls=[];self.profile_reads=0;self.switch=False
        def profile():
            self.profile_reads+=1
            return str(self.profile/'other') if self.switch and self.profile_reads>1 else str(self.profile)
        def rpc(method,params):
            self.calls.append((method,params))
            return self.directory if method=='Files.GetDirectory' else self.api
        self.reader=SimpleNamespace(profile=profile,favorites_locations=lambda:(str(self.profile),str(self.system)),favorites_rpc=rpc,favorites_ui=lambda:self.ui)

    def test_nonempty_api_and_only_parent_are_observation_not_repair(self):
        report=probe.observe_favorites(self.reader)
        self.assertIn('API_HAS_ENTRIES_ACTIVE_CONTAINER_SHOWS_ONLY_PARENT',report['observations'])
        self.assertEqual(report['profile_file']['node_count'],1)
        self.assertEqual(report['profile_file']['native_action_validity'],'NOT_TESTED')
        self.assertEqual(report['favorites_writes'],0)

    def test_native_empty_with_file_entries_preserves_cause_ambiguity(self):
        self.directory=self.api={'state':'completed','total':0,'returned':0}
        report=probe.observe_favorites(self.reader)
        self.assertIn('PROFILE_FILE_HAS_ENTRIES_API_EMPTY_CAUSE_UNCONFIRMED',report['observations'])
        self.assertIn('NATIVE_API_COMPLETED_EMPTY_NOT_PROOF_OF_DATA_LOSS',report['observations'])

    def test_api_and_directory_difference_is_not_called_data_loss(self):
        self.directory={'state':'completed','total':2,'returned':1}
        report=probe.observe_favorites(self.reader)
        self.assertIn('API_AND_DIRECTORY_COUNTS_DIFFER_CAUSE_UNCONFIRMED',report['observations'])

    def test_missing_empty_wrong_root_and_malformed_files_are_distinct(self):
        for raw,state in [(None,'absent'),(b'<favourites/>','readable'),(b'<settings/>','wrong_root'),(b'<broken','unparsed')]:
            with self.subTest(state=state):
                if raw is None:self.file.unlink(missing_ok=True)
                else:self.file.write_bytes(raw)
                result=probe.favorites_file(str(self.file));self.assertEqual(result['state'],state)
                if raw==b'<favourites/>':self.assertEqual(result['node_count'],0)

    def test_entities_encodings_size_rows_and_symlinks_fail_without_disclosing_data(self):
        for raw,state in [(b'<!DOCTYPE favourites [<!ENTITY x "PRIVATE-ENTITY">]><favourites/>','unparsed'),
                          ('<favourites/>'.encode('utf-16'),'unparsed'),
                          (b'x'*(probe.MAX_SETTINGS_BYTES+1),'size_limit'),
                          (b'<favourites>'+b'<favourite/>'*(probe.MAX_FAVORITES_ROWS+1)+b'</favourites>','row_limit')]:
            self.file.write_bytes(raw)
            self.assertEqual(probe.favorites_file(str(self.file))['state'],state)
        target=self.profile/'PRIVATE-OTHER';target.write_text('<favourites/>')
        self.file.unlink();self.file.symlink_to(target)
        self.assertEqual(probe.favorites_file(str(self.file))['state'],'unreadable')

    def test_profile_change_and_inactive_window_cannot_claim_presentation_failure(self):
        self.switch=True
        self.assertTrue(probe.observe_favorites(self.reader)['profile_changed'])
        self.profile_reads=0
        self.assertEqual(probe.observe_favorites(self.reader)['observations'],[])
        self.switch=False;self.ui={'active':False}
        self.assertNotIn('API_HAS_ENTRIES_ACTIVE_CONTAINER_SHOWS_ONLY_PARENT',probe.observe_favorites(self.reader)['observations'])

    def test_read_only_rpc_schema_skip_large_api_and_unchanged_files(self):
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        probe.observe_favorites(self.reader)
        self.assertEqual(self.calls,[('Files.GetDirectory',dict(directory='favourites://',media='files',properties=[],limits={'start':0,'end':1})),('Favourites.GetFavourites',dict(properties=[]))])
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.calls=[];self.directory={'state':'completed','total':probe.MAX_FAVORITES_ROWS+1,'returned':1}
        result=probe.observe_favorites(self.reader)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(result['native_api']['state'],'not_queried_without_bounded_directory_count')

    def test_report_never_contains_titles_paths_actions_or_raw_responses(self):
        encoded=json.dumps(probe.observe_favorites(self.reader))
        for secret in ('PRIVATE-',str(self.root),'PlayMedia','favourites.xml'):
            self.assertNotIn(secret,encoded)

    def test_actual_rpc_reader_sanitizes_errors_null_empty_and_response_limit(self):
        replies=[json.dumps({'result':{'favourites':None,'limits':{'total':0}}}),
                 json.dumps({'error':{'message':'PRIVATE-PATH'}}),
                 'PRIVATE-'*(probe.MAX_RPC_CHARS//8+1)]
        api=SimpleNamespace(executeJSONRPC=lambda _:replies.pop(0))
        method=lambda:probe.KodiReader.favorites_rpc(SimpleNamespace(xbmc=api),'Favourites.GetFavourites',{})
        self.assertEqual(method(),{'state':'completed','total':0,'returned':0})
        self.assertEqual(method(),{'state':'unavailable'})
        self.assertEqual(method(),{'state':'response_limit'})

    def test_actual_ui_reader_rejects_private_labels_and_unknown_state(self):
        api=SimpleNamespace(getCondVisibility=lambda name:name!='System.HasActiveModalDialog',getInfoLabel=lambda _:'PRIVATE-TITLE')
        reader=SimpleNamespace(xbmc=api)
        self.assertIsNone(probe.KodiReader.favorites_ui(reader)['container_items'])
        api.getInfoLabel=lambda _:'7'
        self.assertEqual(probe.KodiReader.favorites_ui(reader),{'active':True,'modal_active':False,'container_items':7,'current_item_is_parent':True})
        api.getCondVisibility=lambda _:True
        self.assertEqual(probe.KodiReader.favorites_ui(reader),{'active':True,'modal_active':True})
        api.getCondVisibility=lambda name:name!='System.HasActiveModalDialog'
        def failed(_):raise RuntimeError('PRIVATE-ERROR')
        api.getInfoLabel=failed
        self.assertEqual(probe.KodiReader.favorites_ui(reader),{'active':None,'state':'unavailable'})

    def test_previous_search_sampler_and_readers_are_unchanged(self):
        original=subprocess.check_output(['git','show','99bd0cdc:repairs/infinity-search-provider-state-20261104/infinity_search_state_probe.py'],cwd=HERE)
        def functions(raw):
            tree=ast.parse(raw)
            methods={n.name:ast.dump(n) for n in tree.body if isinstance(n,ast.FunctionDef)}
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='KodiReader')
            methods.update({'KodiReader.'+n.name:ast.dump(n) for n in cls.body if isinstance(n,ast.FunctionDef)})
            return methods
        old,new=functions(original),functions(SCRIPT.read_bytes())
        for name,code in old.items():
            if name!='main':self.assertEqual(code,new[name],name)


if __name__=='__main__':unittest.main(verbosity=2)
