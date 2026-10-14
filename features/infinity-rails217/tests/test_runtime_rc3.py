"""Simulated Kodi contracts. These do not establish actual device rendering."""
import json, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
WORK=Path(__file__).resolve().parents[1];ADDON=WORK/'addons/script.infinity.rails'
sys.path.insert(0,str(ADDON/'resources'))
from lib import runtime, store, dialog

class Item:
    def __init__(self,label='',label2='',path='',offscreen=False):self.label=label;self.path=path;self.props={};self.art={};self.context=[]
    def setArt(self,a):self.art.update(a)
    def setProperty(self,k,v):self.props[k]=v
    def getProperty(self,k):return self.props.get(k,'')
    def getPath(self):return self.path
    def addContextMenuItems(self,i):self.context.extend(i)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.profile=Path(self.tmp.name)/'profile';self.fixture=Path(self.tmp.name)/'fixture';self.fixture.mkdir()
        (self.fixture/'addon.xml').write_text('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource"><provides>video</provides></extension></addon>')
        self.props={};self.listing=[];self.calls=[];self.dialogs=[];self.answers=[];self.enabled=True;self.aborting=False;self.failed=False;self.version='1.0.5.217';self.focus=9200;self.actualkeys=[];self.waits=0;test=self
        class Window:
            def setProperty(s,k,v):test.props[k]=v
            def getProperty(s,k):return test.props.get(k,'')
            def clearProperty(s,k):test.props.pop(k,None)
            def getFocusId(s):return test.focus
        class Dialog:
            def ok(s,*a):test.dialogs.append(a)
            def notification(s,*a,**kw):test.dialogs.append(a)
        class Addon:
            def __init__(s,aid):s.aid=aid
            def getAddonInfo(s,k):return {'path':str(ADDON if s.aid==runtime.ADDON_ID else test.fixture),'profile':str(test.profile),'name':'Fixture','icon':'special://home/fixture.png','version':test.version}[k]
            def openSettings(s):test.calls.append(('settings',s.aid))
        def rpc(req):test.calls.append(json.loads(req));return json.dumps({'result':{'addons':[{'addonid':'plugin.video.fixture','name':'Fixture'}]}})
        def info(label):
            import re
            if label.endswith('.NumItems'):return str(len(test.actualkeys))
            match=re.search(r'ListItemAbsolute\((\d+)\)',label)
            if match:
                i=int(match[1]);return test.actualkeys[i] if i<len(test.actualkeys) else ''
            return ''
        def wait(timeout):test.waits+=1;test.aborting=True;return True
        monitor=types.SimpleNamespace(abortRequested=lambda:test.aborting,waitForAbort=wait)
        self.xbmc=types.SimpleNamespace(Monitor=lambda:monitor,getCondVisibility=lambda v:test.enabled,log=lambda *a:None,LOGDEBUG=0,LOGERROR=3,LOGWARNING=2,executebuiltin=lambda c:test.calls.append(c),executeJSONRPC=rpc,getInfoLabel=info)
        self.xa=types.SimpleNamespace(Addon=Addon);self.gui=types.SimpleNamespace(Window=lambda _:Window(),Dialog=Dialog,ListItem=Item);self.vfs=types.SimpleNamespace(translatePath=lambda p:p)
        def add(h,items,totalItems=0):
            if test.failed:return False
            test.listing.extend(items);return True
        self.xp=types.SimpleNamespace(setContent=lambda *a:None,addDirectoryItems=add,endOfDirectory=lambda h,**kw:test.calls.append(('end',h,kw)))
        self.modules=patch.dict(sys.modules,{'xbmc':self.xbmc,'xbmcaddon':self.xa,'xbmcgui':self.gui,'xbmcvfs':self.vfs,'xbmcplugin':self.xp});self.modules.start()
        def select(title,labels,subtitle=''):test.dialogs.append((title,labels,subtitle));return test.answers.pop(0) if test.answers else -1
        self.selector=patch.object(runtime,'select',side_effect=select);self.selector.start()
    def tearDown(self):self.selector.stop();self.modules.stop();self.tmp.cleanup()
    def plugin(self,sec='movies'):runtime.plugin(['plugin://script.infinity.rails','1','?section='+sec])
    def add(self,sec='movies'):store.Store(self.profile).add('plugin.video.fixture',[sec],{})
    def row(self):return self.listing[-1][1]
    def test_original_deep_links_and_folder_launch(self):
        self.plugin();self.assertEqual(len(self.listing),10);self.assertIn('movieNavigator',self.listing[1][0]);self.assertTrue(all(f for _,_,f in self.listing));self.assertTrue(all(i.props['node.target']=='videos' for _,i,_ in self.listing))
    def test_listing_never_opens_dialog_or_launches(self):self.plugin();self.assertFalse(self.dialogs);self.assertFalse(any(isinstance(c,str) for c in self.calls))
    def test_context_contains_specific_actions(self):
        self.add();self.plugin();ctx=dict(self.row().context);self.assertIn('Open Add-on · Fixture',ctx);self.assertIn('Move / Reorder',ctx);self.assertIn('Remove from Movie Add-ons',ctx);self.assertEqual(ctx['Cancel'],'noop')
    def test_builtin_context_has_no_remove(self):self.plugin();self.assertFalse(any('Remove from' in l for _,i,_ in self.listing for l,_ in i.context))
    def test_settings_only_if_file_present(self):
        self.add();self.plugin();self.assertNotIn('Add-on Settings',dict(self.row().context));(self.fixture/'resources').mkdir();(self.fixture/'resources/settings.xml').write_text('<settings/>');self.listing=[];self.plugin();self.assertIn('Add-on Settings',dict(self.row().context))
    def test_add_both_atomic_and_refresh_two_rails(self):
        self.answers=[2];runtime.do_add(explicit_id='plugin.video.fixture');d,w=store.Store(self.profile).load();self.assertFalse(w);self.assertEqual([d['rails'][s]['custom'] for s in store.SECTIONS],[['plugin.video.fixture']]*2);self.assertEqual(self.props['Infinity.Rails.movies.Revision'],'1');self.assertEqual(self.props['Infinity.Rails.tvshows.Revision'],'1')
    def test_add_movie_refreshes_only_movie(self):self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');self.assertNotIn('Infinity.Rails.tvshows.Revision',self.props)
    def test_add_tv_refreshes_only_tv(self):self.answers=[1];runtime.do_add(explicit_id='plugin.video.fixture');self.assertNotIn('Infinity.Rails.movies.Revision',self.props)
    def test_duplicate_add_does_not_refresh(self):self.add();self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse(self.props)
    def test_cancel_is_explicit_and_does_not_save(self):self.answers=[3];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse(self.profile.exists());self.assertEqual(self.dialogs[0][1][-1],'Cancel')
    def test_back_in_chooser_does_not_save(self):self.answers=[-1];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse(self.profile.exists())
    def test_remove_is_shortcut_only_selected_rail(self):
        s=store.Store(self.profile);s.add('plugin.video.fixture',list(store.SECTIONS),{});runtime.remove_card('movies','c:plugin.video.fixture');d,_=s.load();self.assertEqual(d['rails']['movies']['custom'],[]);self.assertEqual(d['rails']['tvshows']['custom'],['plugin.video.fixture']);self.assertTrue((self.fixture/'addon.xml').exists())
    def test_default_remove_refused(self):self.assertRaises(store.RailError,runtime.remove_card,'movies','b:0123456789abcdef')
    def test_move_before_builtin(self):
        self.add();self.answers=[0];runtime.move_card('movies','c:plugin.video.fixture');self.plugin();self.assertEqual(self.listing[0][1].props['Infinity.Rails.Key'],'c:plugin.video.fixture')
    def test_move_cancel_no_revision(self):self.add();self.answers=[-1];runtime.move_card('movies','c:plugin.video.fixture');self.assertFalse(self.props)
    def test_stale_move_refused(self):self.assertRaises(store.RailError,runtime.move_card,'movies','c:plugin.video.missing')
    def test_open_builtin_retains_movie_deep_link(self):
        row=runtime.defaults(ADDON)['movies'][1];runtime.card_action('open','movies',row['key']);self.assertEqual(self.calls, ['ActivateWindow(Videos,"'+row['uri']+'",return)'])
    def test_open_custom_launches_root(self):self.add();runtime.card_action('open','movies','c:plugin.video.fixture');self.assertEqual(self.calls,['ActivateWindow(Videos,"plugin://plugin.video.fixture",return)'])
    def test_disabled_card_refuses_launch_keeps_state(self):self.add();self.enabled=False;self.assertRaises(store.RailError,runtime.card_action,'open','movies','c:plugin.video.fixture');self.assertEqual(store.Store(self.profile).load()[0]['rails']['movies']['custom'],['plugin.video.fixture'])
    def test_settings_supported_opens_correct_addon(self):
        self.add();(self.fixture/'resources').mkdir();(self.fixture/'resources/settings.xml').write_text('<settings/>');runtime.card_action('settings','movies','c:plugin.video.fixture');self.assertEqual(self.calls,[('settings','plugin.video.fixture')])
    def test_settings_unsupported_refused(self):self.add();self.assertRaises(store.RailError,runtime.card_action,'settings','movies','c:plugin.video.fixture')
    def test_unavailable_card_hidden_preferences_kept(self):self.add();self.enabled=False;self.plugin();self.assertEqual(len(self.listing),10);self.assertEqual(store.Store(self.profile).load()[0]['rails']['movies']['custom'],['plugin.video.fixture'])
    def test_failed_listing_restores_fallback(self):self.failed=True;self.props['Infinity.Rails.movies.Ready']='true';self.plugin();self.assertNotIn('Infinity.Rails.movies.Ready',self.props)
    def test_abort_no_work(self):self.aborting=True;self.plugin();self.assertFalse(self.listing);self.assertFalse(self.profile.exists())
    def test_empty_plugin_root_only_explicit_setup(self):runtime.plugin(['plugin://script.infinity.rails','1','']);self.assertTrue(self.dialogs);self.assertEqual(len(self.listing),3)
    def test_older_skin_requests_normal_zip_and_never_patches(self):self.version='1.0.5.216';runtime.main(args=[]);self.assertIn('complete Infinity',self.dialogs[0][1]);self.assertFalse(self.calls)
    def test_loaded_revision_published_after_handoff(self):self.add();self.plugin();self.assertEqual(self.props['Infinity.Rails.movies.LoadedRevision'],'1');self.assertIn(('end',1,{'succeeded':True,'cacheToDisc':False}),self.calls)
    def test_remove_focus_prefers_next_neighbor(self):self.actualkeys=['b:first','c:plugin.video.fixture','b:next'];self.assertEqual(runtime.capture_focus(self.xbmc,self.gui,'c:plugin.video.fixture',True),(9200,'b:next'))
    def test_last_card_focus_prefers_previous(self):self.actualkeys=['b:first','c:plugin.video.fixture'];self.assertEqual(runtime.capture_focus(self.xbmc,self.gui,'c:plugin.video.fixture',True),(9200,'b:first'))
    def test_focus_restored_only_after_local_revision_loaded(self):
        self.actualkeys=['b:first','b:next'];self.props.update({'Infinity.Rails.movies.Revision':'2','Infinity.Rails.movies.LoadedRevision':'2'});runtime.restore_focus((9200,'b:next'),'movies',self.xbmc,self.gui,self.xbmc.Monitor());self.assertEqual(self.calls,['SetFocus(9200,1,absolute)']);self.assertEqual(self.waits,0)
    def test_focus_not_stolen_after_navigation(self):self.focus=9000;runtime.restore_focus((9200,'b:next'),'movies',self.xbmc,self.gui,self.xbmc.Monitor());self.assertEqual(self.calls,[]);self.assertEqual(self.waits,0)
    def test_pending_focus_wait_cancels_on_shutdown(self):runtime.restore_focus((9200,'b:next'),'movies',self.xbmc,self.gui,self.xbmc.Monitor());self.assertEqual(self.calls,[]);self.assertEqual(self.waits,1)
    def test_add_refresh_never_calls_home_reload_player_shutdown(self):self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse(any(isinstance(c,str) for c in self.calls))
    def test_addon_context_missing_item_no_mutation(self):runtime.context_add(None);self.assertFalse(self.profile.exists())
    def test_repeated_250_add_remove_no_duplicates(self):
        for _ in range(250):
            self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');runtime.remove_card('movies','c:plugin.video.fixture')
        d,w=store.Store(self.profile).load();self.assertFalse(w);self.assertEqual(d['revision'],500);self.assertEqual(d['rails']['movies']['custom'],[])

class ModalTests(unittest.TestCase):
    def run_dialog(self,mode):
        trace=[]
        class List:
            def reset(s):trace.append('reset')
            def addItems(s,items):trace.append([i.label for i in items])
            def getSelectedPosition(s):return 1
        class XMLDialog:
            def __init__(s,*a,**kw):trace.append(a)
            def setProperty(s,*a):trace.append(a)
            def getControl(s,c):return List()
            def setFocusId(s,c):trace.append(('focus',c))
            def close(s):trace.append('close')
            def doModal(s):
                s.onInit()
                if mode=='click':s.onClick(6)
                elif mode=='x':s.onClick(7)
                else:s.onAction(types.SimpleNamespace(getId=lambda:mode))
        gui=types.SimpleNamespace(WindowXMLDialog=XMLDialog,ListItem=Item)
        with patch.dict(sys.modules,{'xbmcgui':gui,'xbmcaddon':types.SimpleNamespace(Addon=lambda a:types.SimpleNamespace(getAddonInfo=lambda k:str(ADDON))),'xbmcvfs':types.SimpleNamespace(translatePath=lambda p:p)}):result=dialog.choose('Title',['a','b'],'Selected')
        self.assertEqual(trace[0][0],'script-infinity-rails-select.xml');self.assertEqual(trace[-1],'close');return result
    def test_select_returns_row(self):self.assertEqual(self.run_dialog('click'),1)
    def test_x_dismisses(self):self.assertEqual(self.run_dialog('x'),-1)
    def test_back_dismisses(self):self.assertEqual(self.run_dialog(92),-1)
    def test_previousmenu_dismisses(self):self.assertEqual(self.run_dialog(10),-1)
    def test_context_dismisses(self):self.assertEqual(self.run_dialog(117),-1)
