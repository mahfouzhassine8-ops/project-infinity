"""Host interface tests. These simulate Kodi APIs; not physical-device tests."""
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

WORK=Path(__file__).resolve().parents[1];ADDON=WORK/'addons/script.infinity.rails'
sys.path.insert(0,str(ADDON/'resources'))
from lib import runtime,store

class ListItem:
    def __init__(self,label='',label2='',path='',offscreen=False):self.label=label;self.label2=label2;self.path=path;self.props={};self.art={};self.context=[]
    def setArt(self,art):self.art.update(art)
    def setProperty(self,key,value):self.props[key]=value
    def getProperty(self,key):return self.props.get(key,'')
    def getPath(self):return self.path
    def addContextMenuItems(self,items,replaceItems=False):self.context.extend(items)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.profile=Path(self.tmp.name)/'profile';self.installed=Path(self.tmp.name)/'fixture';self.installed.mkdir()
        (self.installed/'addon.xml').write_text('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource"><provides>video</provides></extension></addon>')
        self.properties={};self.focus=9200;self.info={};self.listing=[];self.calls=[];self.dialogs=[];self.answers=[];self.enabled=True;self.aborting=False;self.fail_list=False
        test=self
        class Window:
            def getFocusId(obj):return test.focus
            def getProperty(obj,key):return test.properties.get(key,'')
            def setProperty(obj,key,value):test.properties[key]=value
            def clearProperty(obj,key):test.properties.pop(key,None)
        class Dialog:
            def select(obj,heading,items):test.dialogs.append((heading,items));return test.answers.pop(0) if test.answers else -1
            def yesno(obj,*args,**kwargs):return bool(test.answers.pop(0)) if test.answers else False
            def ok(obj,*args,**kwargs):test.dialogs.append(args)
            def notification(obj,*args,**kwargs):test.dialogs.append(args)
            def textviewer(obj,*args,**kwargs):test.dialogs.append(('textviewer',)+args)
        class Addon:
            def __init__(obj,aid):obj.aid=aid
            def openSettings(obj):test.calls.append(('settings',obj.aid))
            def getAddonInfo(obj,key):
                return {'id':obj.aid,'path':str(ADDON if obj.aid==runtime.ADDON_ID else test.installed),'profile':str(test.profile),'name':'Fixture','icon':'special://home/fixture.png','version':'1.0.5.221'}[key]
        def rpc(request):
            test.calls.append(json.loads(request));return json.dumps({'jsonrpc':'2.0','id':1,'result':{'addons':[{'addonid':'plugin.video.fixture','name':'Fixture'}]}})
        self.xbmc=types.SimpleNamespace(Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:test.aborting),getCondVisibility=lambda v:test.enabled,getInfoLabel=lambda v:test.info.get(v,''),log=lambda *a:None,LOGERROR=3,LOGWARNING=2,LOGINFO=1,executebuiltin=lambda x,*args:test.calls.append(x),executeJSONRPC=rpc)
        self.xa=types.SimpleNamespace(Addon=Addon);self.gui=types.SimpleNamespace(Window=lambda _:Window(),Dialog=Dialog,ListItem=ListItem);self.vfs=types.SimpleNamespace(translatePath=lambda p:p)
        def add_items(handle,items,totalItems=0):
            if test.fail_list:return False
            test.listing.extend(items);return True
        def end(handle,succeeded=True,cacheToDisc=True):test.calls.append(('end',handle,succeeded,cacheToDisc));return None
        self.xp=types.SimpleNamespace(setContent=lambda *a:test.calls.append(('content',)+a),addDirectoryItems=add_items,endOfDirectory=end)
        self.modules=patch.dict(sys.modules,{'xbmc':self.xbmc,'xbmcaddon':self.xa,'xbmcgui':self.gui,'xbmcvfs':self.vfs,'xbmcplugin':self.xp});self.modules.start()
        self.inst=patch.object(runtime,'select',side_effect=lambda *args,**kwargs:test.answers.pop(0) if test.answers else None);self.inst.start()
    def tearDown(self):self.inst.stop();self.modules.stop();self.tmp.cleanup()
    def plugin(self,section='movies'):runtime.plugin(['plugin://script.infinity.rails','1','?section='+section])
    def test_directory_launches_preserved_as_folders_not_playmedia(self):
        self.plugin();self.assertEqual(len(self.listing),10)
        for url,li,folder in self.listing:self.assertTrue(folder);self.assertTrue(url.startswith('plugin://'));self.assertEqual(li.props['IsPlayable'],'false');self.assertEqual(li.props['node.target'],'videos')
    def test_manual_inspect_shows_active_provider_without_mutating_preferences(self):
        self.focus=9200
        self.plugin()
        before=dict(self.properties)
        with patch.object(self.gui, 'getCurrentWindowId', return_value=10001, create=True), patch.object(self.gui, 'getCurrentWindowDialogId', return_value=0, create=True):
            runtime.inspect_rails()
        report=[d for d in self.dialogs if d and d[0]=='textviewer'][-1]
        self.assertIn('Infinity Rails Input Status', report[1])
        status = json.loads(report[2])
        self.assertEqual(status['sampling'], 'HOME_INACTIVE_NOT_SAMPLED')
        self.assertEqual(status['controls'], [])
        self.assertEqual(before,self.properties)
        self.assertFalse((self.profile/'rails.json').exists())
    def test_failed_listing_is_reported_and_success_clears_failure(self):
        self.fail_list=True
        self.plugin()
        self.assertEqual(self.properties.get('Infinity.Rails.movies.Failed'),'true')
        self.fail_list=False
        self.plugin()
        self.assertNotIn('Infinity.Rails.movies.Failed',self.properties)
        self.assertEqual(self.properties.get('Infinity.Rails.movies.Ready'),'true')
    def test_static_number_property_retains_evaluated_value(self):
        self.plugin();self.assertEqual(self.listing[0][1].props['id'],'1')
    def test_existing_deep_links_not_collapsed_to_root(self):
        self.plugin();self.assertIn('movieNavigator',self.listing[1][0]);self.assertIn('MovieList',self.listing[2][0])
    def test_add_to_both_flows_and_persists(self):
        self.answers=[2];runtime.do_add(explicit_id='plugin.video.fixture');d,w=store.Store(self.profile).load()
        self.assertFalse(w);self.assertEqual([d['rails'][s]['custom'] for s in store.SECTIONS],[['plugin.video.fixture'],['plugin.video.fixture']])
    def test_cancel_does_not_create_preferences(self):
        self.answers=[-1];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse((self.profile/'rails.json').exists())
    def test_custom_card_art_and_context(self):
        store.Store(self.profile).add('plugin.video.fixture',['movies'],{});self.plugin();url,li,folder=self.listing[-1]
        self.assertEqual(li.art['thumb'],'special://home/fixture.png');self.assertIn('Open Add-on',li.context[0][0]);self.assertIn(',open,movies,c:plugin.video.fixture)',li.context[0][1]);self.assertTrue(any('Remove from Movie Add-ons'==name for name,_ in li.context))
    def test_builtin_has_no_remove_action(self):
        self.plugin();self.assertFalse(any(x[0].startswith('Remove from ') for _,li,_ in self.listing for x in li.context))
    def test_disabled_custom_hidden_and_retained(self):
        s=store.Store(self.profile);s.add('plugin.video.fixture',['movies'],{});self.enabled=False;self.plugin();self.assertEqual(len(self.listing),10);self.assertEqual(s.load()[0]['rails']['movies']['custom'],['plugin.video.fixture'])
    def test_omega_void_endOfDirectory_is_not_misread_as_failure(self):
        self.plugin();self.assertEqual(self.properties.get('Infinity.Rails.movies.Ready'),'true')
        self.assertEqual([x for x in self.calls if isinstance(x,tuple) and x[0]=='end'],[('end',1,True,False)])
    def test_ready_only_after_success(self):
        self.plugin();self.assertEqual(self.properties['Infinity.Rails.movies.Ready'],'true');self.assertIn(('end',1,True,False),self.calls)
    def test_directory_failure_restores_static_fallback(self):
        self.properties['Infinity.Rails.movies.Ready']='true';self.fail_list=True;self.plugin();self.assertNotIn('Infinity.Rails.movies.Ready',self.properties);self.assertIn(('end',1,False,False),self.calls)
    def test_abort_restores_fallback_and_does_no_new_listing(self):
        self.properties['Infinity.Rails.movies.Ready']='true';self.aborting=True;self.plugin();self.assertEqual(self.listing,[]);self.assertNotIn('Infinity.Rails.movies.Ready',self.properties)
    def test_invalid_section_is_empty_no_side_effect(self):
        self.plugin('sports');self.assertEqual(self.listing,[]);self.assertEqual(self.properties,{})
    def test_stale_or_missing_context_item_cannot_add(self):
        runtime.context_add(None);self.assertFalse((self.profile/'rails.json').exists());self.assertTrue(self.dialogs)
    def test_explicit_remove_is_immediate_and_scope_limited(self):
        s=store.Store(self.profile);s.add('plugin.video.fixture',['movies'],{});self.answers=[None];runtime.remove_card('movies','c:plugin.video.fixture');self.assertEqual(s.load()[0]['rails']['movies']['custom'],[])
    def test_remove_only_affects_selected_rail(self):
        s=store.Store(self.profile);s.add('plugin.video.fixture',list(store.SECTIONS),{});self.answers=[True];runtime.remove_card('movies','c:plugin.video.fixture');self.assertEqual(s.load()[0]['rails']['tvshows']['custom'],['plugin.video.fixture'])
    def test_explicit_add_picker_uses_local_kodi_rpc(self):
        self.answers=[0,None];runtime.browse_add();request=[x for x in self.calls if isinstance(x,dict)][0]
        self.assertEqual(request['method'],'Addons.GetAddons');self.assertEqual(request['params']['content'],'video');self.assertTrue(request['params']['enabled'])
    def test_custom_visibility_tracks_addon_enable_state(self):
        store.Store(self.profile).add('plugin.video.fixture',['movies'],{});self.plugin();v=self.listing[-1][1].props['node.visible'];self.assertIn('System.AddonIsEnabled(plugin.video.fixture)',v)
    def test_no_player_shutdown_or_skin_reload_during_add(self):
        self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse([x for x in self.calls if isinstance(x,str)])

if __name__=='__main__':unittest.main(verbosity=2)
