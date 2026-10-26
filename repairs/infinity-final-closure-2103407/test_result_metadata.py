"""Actual aggregation/capture/presentation functions, no provider or device mocks claiming playback."""
import ast
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch as mock_patch

import patch_result_metadata as correction

ROOT = Path(os.environ.get('INFINITY_SIGNED407_SOURCES',
    Path(__file__).resolve().parents[3]/'baseline-2103407/ownership-local/sources'))/correction.CC


def module(name, text):
    value = types.ModuleType(name)
    exec(compile(text,name,'exec'),value.__dict__)
    return value


class ResultMetadataTests(unittest.TestCase):
    def setUp(self):
        self.meta = module('title_metadata',correction.patch('title_metadata.py',(ROOT/'title_metadata.py').read_bytes()))
        self.modules = mock_patch.dict(sys.modules, {'title_metadata':self.meta})
        self.modules.start();self.addCleanup(self.modules.stop)
        self.info = module('corrected_information',correction.patch('information.py',(ROOT/'information.py').read_bytes()))
        self.search = correction.patch('infinity_search.py',(ROOT/'infinity_search.py').read_bytes()).decode()

    def publish(self, row):
        emitted = []
        class Item:
            def __init__(self,*args,**kw):self.info={};self.path=kw.get('path');self.ids={}
            def setProperty(self,*args):pass
            def setInfo(self,kind,values):self.info=values
            def setUniqueIDs(self,values):self.ids=values
            def setArt(self,values):self.art=values
            def addContextMenuItems(self,*args):pass
            def getVideoInfoTag(self):
                fields={'getTrailer':'trailer','getPremieredAsW3C':'premiered','getRating':'rating',
                        'getPlot':'plot','getYear':'year','getDuration':'runtime'}
                tag=types.SimpleNamespace(**{getter:(lambda key=key:self.info.get(key)) for getter,key in fields.items()})
                # Match the actual retained Kodi implementation: the old
                # getter localizes dates; the W3C getter returns ISO metadata.
                tag.getPremiered=lambda:'23/11/2005' if self.info.get('premiered')=='2005-11-23' else self.info.get('premiered')
                return tag
        nodes = ast.parse(self.search).body
        fn = next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name=='_publish_result')
        ns = {'xbmcgui':types.SimpleNamespace(ListItem=Item),'xbmcplugin':types.SimpleNamespace(
            addDirectoryItem=lambda handle,path,item,**kw:emitted.append((path,item))), 'MAX_RESULTS':40}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-publish','exec'),ns)
        ns['_publish_result'](1,{'id':'plugin.video.fixture','name':'Fixture'},'completed',
            {'result':{'files':[row]}},'plugin://plugin.video.fixture/?search=original')
        return emitted[1]

    def test_original_trailer_release_rating_identity_complete_transport(self):
        row = dict(file='plugin://plugin.video.fixture/?action=movie&id=123',filetype='directory',
                   title='Just Friends',type='movie',year=2005,uniqueid={'tmdb':'10033'},
                   plot='Complete original plot',rating=6.19999809265137,
                   trailer='plugin://plugin.video.youtube/play/?video_id=exact',premiered='2005-11-23')
        before=deepcopy(row);target,item=self.publish(row)
        entry=dict(title=row['title'],uniqueids=item.ids,information=self.meta.capture(item))
        original=deepcopy(entry);view=self.info.presentation(entry)
        self.assertEqual(view['trailer'],row['trailer'])
        self.assertIn('Release: 2005-11-23',view['details'])
        self.assertIn('Rating: 6.2',view['details'])
        self.assertNotIn('6.19999',view['details'])
        self.assertEqual(target,row['file']);self.assertEqual(item.ids,row['uniqueid'])
        self.assertEqual(row,before);self.assertEqual(entry,original)
        self.assertEqual(entry['information']['rating'],row['rating'])

    def test_no_guessed_trailer_and_unsafe_builtin_not_forwarded(self):
        for trailer in (None,'','RunScript(evil)','plugin://fixture/\ncommand','file:///private/secret'):
            target,item=self.publish(dict(file='plugin://plugin.video.fixture/?id=exact',trailer=trailer))
            self.assertNotIn('trailer',item.info)
            self.assertEqual(self.info.presentation({'information':self.meta.capture(item)})['trailer'],'')
        for trailer in ('https://example.test/exact-trailer.mp4','plugin://plugin.video.fixture/?trailer=original'):
            _,item=self.publish(dict(file='plugin://plugin.video.fixture/?id=exact',trailer=trailer))
            self.assertEqual(item.info['trailer'],trailer)

    def test_localized_legacy_getter_does_not_hide_a_valid_original_release(self):
        _,item=self.publish(dict(file='plugin://plugin.video.fixture/?id=exact',premiered='2005-11-23'))
        original=module('original_title_metadata',(ROOT/'title_metadata.py').read_text())
        legacy=original.capture(item)
        self.assertEqual(legacy['premiered'],'23/11/2005')
        self.assertNotIn('Release:',self.info.presentation({'information':legacy})['details'])
        captured=self.meta.capture(item)
        self.assertEqual(captured['premiered'],'2005-11-23')
        self.assertIn('Release: 2005-11-23',self.info.presentation({'information':captured})['details'])

    def test_invalid_calendar_and_epoch_hidden_without_raw_mutation(self):
        for value in ('1601-01-01','0000-00-00','2026-02-30','01/01/1601','2026-13-01','',None):
            entry={'information':{'premiered':value}}
            before=deepcopy(entry)
            self.assertNotIn('Release:',self.info.presentation(entry)['details'])
            self.assertEqual(entry,before)
        for value in ('1878-06-15','2000-02-29','2028-10-26'):
            self.assertIn('Release: '+value,self.info.presentation({'information':{'premiered':value}})['details'])

    def test_only_metadata_boundaries_change_clicks_and_concurrency_preserved(self):
        for name in ('infinity_search.py','information.py','title_metadata.py'):
            original=(ROOT/name).read_bytes();candidate=correction.patch(name,original)
            restored=candidate.decode()
            for old,new in reversed(correction.edits(name)):restored=restored.replace(new,old,1)
            self.assertEqual(restored.encode(),original)
            with self.assertRaises(ValueError):correction.patch(name,original+b'\n')
        self.assertIn("elif ident == 102 and trailer:",correction.patch('information.py',(ROOT/'information.py').read_bytes()).decode())
        tree=ast.parse(self.search);assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROPERTIES' for t in n.targets))
        self.assertTrue({'trailer','premiered'}<=set(ast.literal_eval(assignment.value)))
        self.assertIn('Trailer unavailable',correction.patch('information.py',(ROOT/'information.py').read_bytes()).decode())


if __name__=='__main__':unittest.main(verbosity=2)
