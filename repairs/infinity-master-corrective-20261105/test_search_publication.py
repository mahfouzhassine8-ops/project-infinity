"""Aggregate rejection versus original provider heading; synthetic requests."""
import ast
import json
import subprocess
from types import SimpleNamespace
import unittest

import test_search_correction as source


class Item:
    def __init__(self,label,*args,**kwargs):self.label=label;self.props={}
    def setProperty(self,key,value):self.props[key]=value


class SearchPublication(unittest.TestCase):
    def setUp(self):
        self.b=source.shipped.StateDiagnosis();self.b.setUp();self.addCleanup(self.b.doCleanups)
        self.logs=[];self.published=[]
        self.b.env['xbmc'].log=lambda value,level:self.logs.append(value)
        self.b.env['xbmc'].LOGINFO=1
        exec(source.CODE,self.b.env)
        node=next(n for n in source.TREE.body if isinstance(n,ast.FunctionDef) and n.name=='_publish_result')
        self.b.env.update(xbmcgui=SimpleNamespace(ListItem=Item),xbmcplugin=SimpleNamespace(addDirectoryItem=lambda h,p,i,isFolder:self.published.append((p,i,isFolder))),MAX_RESULTS=40)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_search_publish','exec'),self.b.env)
        self.b.provider['name']='Fixture Provider'
    def trace(self):
        self.assertEqual(len(self.logs),1)
        self.assertTrue(self.logs[0].startswith('INFINITY_SEARCH_STATE '))
        self.assertLess(len(self.logs[0]),2048)
        return json.loads(self.logs[0].split(' ',1)[1])

    def test_completed_response_discarded_but_heading_retains_exact_provider_route(self):
        original=self.b.env['route'](self.b.provider,'synthetic query')
        self.b.during=lambda:self.b.touch(self.b.settings)
        result=self.b.query()
        self.b.env['_publish_result'](1,*result)
        self.assertEqual(result[1:3],('state_changed',{}))
        self.assertEqual(self.b.calls,1)
        self.assertEqual(len(self.published),1)
        path,item,folder=self.published[0]
        self.assertEqual(path,original);self.assertTrue(folder)
        self.assertIn('State changed; search again',item.label)
        self.assertNotIn('unavailable',item.label)
        trace=self.trace()
        self.assertEqual(trace['original_status'],'completed')
        self.assertEqual(trace['original_result_count'],1)
        self.assertEqual(trace['changed'],['provider_settings_metadata'])

    def test_nixtoons_ordinary_history_records_exact_rejection_category(self):
        f=source.effects.SideEffectDiagnosis();f.setUp();self.addCleanup(f.doCleanups)
        exec(source.CODE,f.b.env)
        f.b.env['xbmc'].log=lambda value,level:self.logs.append(value);f.b.env['xbmc'].LOGINFO=1
        search,_=f.nixtoons()
        f.b.during=lambda:search(dict(searchType='series',query='fixture query',path='/search'))
        self.assertEqual(f.b.query()[1],'state_changed')
        trace=self.trace()
        self.assertEqual(trace['provider'],'plugin.video.watchnixtoons2')
        self.assertEqual(trace['changed'],['provider_settings_metadata'])
        self.assertEqual(f.b.calls,1)

    def test_fresh_widget_change_has_no_rejection_or_diagnostic_spam(self):
        self.b.during=lambda:self.b.props.__setitem__('widgetreload','new')
        self.assertEqual(self.b.query()[1],'completed');self.assertEqual(self.logs,[])

    def test_cache_hit_race_records_cache_reason_without_new_provider(self):
        self.assertEqual(self.b.query()[1],'completed')
        original=self.b.home.getProperty
        def read(key):
            if key.startswith('Infinity.Search.Cache.'):self.b.props['widgetreload']='new'
            return original(key)
        self.b.home.getProperty=read
        self.assertEqual(self.b.query()[1],'state_changed')
        trace=self.trace()
        self.assertTrue(trace['cache_hit']);self.assertEqual(trace['changed'],['home.widgetreload'])
        self.assertEqual(self.b.calls,1)

    def test_logging_cannot_publish_private_query_paths_settings_or_values(self):
        self.b.during=lambda:self.b.settings.write_text('<settings><setting id="PRIVATE-KEY">PRIVATE-TOKEN</setting></settings>')
        self.assertEqual(self.b.query()[1],'state_changed')
        encoded=json.dumps(self.trace())
        for private in ('PRIVATE-','synthetic query',str(self.b.profile),str(self.b.root),'settings.xml'):
            self.assertNotIn(private,encoded)

    def test_logger_failure_cannot_change_rejection_or_replay_request(self):
        def failed(*args):raise RuntimeError('fixture logger failed')
        self.b.env['xbmc'].log=failed
        self.b.during=lambda:self.b.touch(self.b.settings)
        self.assertEqual(self.b.query()[1],'state_changed');self.assertEqual(self.b.calls,1)

    def test_cancellation_source_refusal_and_native_failure_keep_priority(self):
        self.b.during=lambda:setattr(self.b,'canceled',True)
        self.assertEqual(self.b.query()[1],'cancelled');self.assertEqual(self.logs,[])
        self.b.canceled=False;self.b.during=lambda:(self.b.root/'main.py').write_text('# changed source')
        self.assertEqual(self.b.query()[1],'unavailable');self.assertEqual(self.logs,[])

    def test_provider_selected_in_search_form_is_still_guarded_results_handler(self):
        nodes={n.name:n for n in source.TREE.body if isinstance(n,ast.FunctionDef)}
        single=ast.unparse(nodes['search_provider']);all_=ast.unparse(nodes['search_all'])
        self.assertIn('_search_results',single);self.assertIn('_search_results',all_)
        self.assertIn('provider_id=provider_id',single)

    def test_diagnostic_components_reuse_same_metadata_and_file_reads(self):
        files=[];metadata=[]
        original_stamp=self.b.env['_query_file_stamp']
        self.b.env['_query_file_stamp']=lambda path:(files.append(path),original_stamp(path))[1]
        def info(field):
            metadata.append(field)
            return {'profile':str(self.b.progress),'version':'fixture-version'}[field]
        self.b.env['xbmcaddon'].Addon=lambda _:SimpleNamespace(getAddonInfo=info)
        route=self.b.env['route'](self.b.provider,'synthetic query')
        plain=self.b.env['_query_signature'](self.b.provider,route,self.b.home,response=True)
        old_files=list(files);old_metadata=list(metadata)
        files.clear();metadata.clear();components={}
        traced=self.b.env['_query_signature'](self.b.provider,route,self.b.home,response=True,components=components)
        self.assertEqual(plain,traced)
        self.assertEqual(files,old_files);self.assertEqual(metadata,old_metadata)
        self.assertEqual(metadata.count('version'),1)
        self.assertTrue(all(len(value)==64 for value in components.values()))

    def test_cache_and_response_guard_hashes_match_checkpoint62028085(self):
        original=subprocess.check_output(['git','show','62028085:repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py'],cwd=source.HERE)
        node=next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef) and n.name=='_query_signature')
        node.name='_checkpoint_signature'
        exec(compile(ast.Module(body=[node],type_ignores=[]),'checkpoint620_signature','exec'),self.b.env)
        route=self.b.env['route'](self.b.provider,'synthetic query')
        for response in (False,True):
            with self.subTest(response=response):
                old=self.b.env['_checkpoint_signature'](self.b.provider,route,self.b.home,response=response)
                new=self.b.env['_query_signature'](self.b.provider,route,self.b.home,response=response,components={})
                self.assertEqual(old,new)


if __name__=='__main__':unittest.main(verbosity=2)
