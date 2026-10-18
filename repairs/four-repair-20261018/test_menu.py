import importlib.util
from pathlib import Path
import sys
import types
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'addon'))
from menu_model import addon_rows, hidden_setting, valid_id

class MenuTests(unittest.TestCase):
    def setUp(self):
        self.settings=set();self.calls=[];self.rpc_calls=[];self.properties={}
        self.selected='plugin.video.fixture'
        self.token='plugin.video.fixture'
        self.window_id=11193
        def builtin(s,*args):
            self.calls.append(s)
            if s.startswith('Skin.SetBool('):self.settings.add(s[13:-1])
            elif s.startswith('Skin.Reset('):self.settings.discard(s[11:-1])
        self.dialog=mock.Mock();self.dialog.yesno.return_value=False
        window=mock.Mock();window.setProperty.side_effect=lambda k,v:self.properties.update({k:v})
        self.xbmc=types.SimpleNamespace(executebuiltin=builtin,getCondVisibility=lambda s:s[16:-1] in self.settings,
            getInfoLabel=lambda s:self.selected if s=='Container(50).ListItem.Property(Addon.ID)'
                else self.token if s=='Container(50).ListItem.Property(Infinity.UI.Token)' else '')
        modules={'xbmc':self.xbmc,'xbmcgui':types.SimpleNamespace(Window=lambda *a:window,Dialog=lambda:self.dialog,
                 getCurrentWindowId=lambda:self.window_id),
                 'xbmcaddon':types.SimpleNamespace(Addon=mock.Mock()),'xbmcvfs':types.SimpleNamespace(exists=lambda p:True,translatePath=str),
                 'popup':types.SimpleNamespace(choose=mock.Mock(return_value=None))}
        with mock.patch.dict(sys.modules,modules):
            spec=importlib.util.spec_from_file_location('ui_runtime_test',HERE/'addon/runtime.py')
            self.runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.runtime)
        self.runtime.rpc=mock.Mock(side_effect=lambda *a:self.rpc_calls.append(a))

    def test_rails_026_027_only_and_disabled_rails_is_hidden(self):
        # #6 integration may not silently remove #4's Add to Infinity Rails.
        state={'enabled':True,'version':'0.2.6'}
        with mock.patch.object(self.xbmc,'getCondVisibility',side_effect=lambda _condition:state['enabled']):
            with mock.patch.object(self.runtime.xbmcaddon,'Addon') as addon:
                addon.return_value.getAddonInfo.side_effect=lambda field: state['version'] if field=='version' else ''
                for version in ('0.2.6','0.2.7','0.2.5','0.2.8','0.3.0',''):
                    state['version']=version
                    expected=version in ('0.2.6','0.2.7')
                    with self.subTest(version=version):
                        self.assertEqual(self.runtime.rails_supported(),expected)
                        labels=[name for name,_ in addon_rows(True,self.runtime.rails_supported())]
                        self.assertEqual('Add to Infinity Rails' in labels,expected)
                state['enabled']=False
                state['version']='0.2.7'
                self.assertFalse(self.runtime.rails_supported())
                self.assertNotIn('Add to Infinity Rails',
                                 [name for name,_ in addon_rows(True,self.runtime.rails_supported())])
        self.assertEqual(self.calls,[])
        self.assertEqual(self.rpc_calls,[])

    def test_precise_order_and_capabilities(self):
        self.assertEqual([s for s,_ in addon_rows(True,True)], ['Open','Add-on Information','Add-on Settings','Add to Favourites','Add to Infinity Rails','Hide from This View','More / Manage Add-on'])
        self.assertEqual([s for s,_ in addon_rows(False,False)], ['Open','Add-on Information','Add to Favourites','Hide from This View','More / Manage Add-on'])
        self.assertNotIn('Disable Add-on',[s for s,_ in addon_rows(True,True)])

    def test_hide_restore_never_disables_or_deletes(self):
        aid='plugin.video.fixture'
        self.runtime.set_hidden(aid,True)
        self.assertIn(hidden_setting(aid),self.settings)
        self.runtime.set_hidden(aid,False)
        self.assertNotIn(hidden_setting(aid),self.settings)
        self.assertEqual(self.rpc_calls,[])
        self.assertEqual(self.calls,['Skin.SetBool('+hidden_setting(aid)+')','Skin.Reset('+hidden_setting(aid)+')'])

    def test_disable_requires_management_activation_and_confirmation(self):
        aid='plugin.video.fixture';row={'name':'Harmless Fixture'}
        self.runtime.choose.return_value=None
        self.runtime.manage(aid,row);self.dialog.yesno.assert_not_called();self.assertEqual(self.rpc_calls,[])
        self.runtime.choose.return_value='disable'
        self.runtime.manage(aid,row);self.assertEqual(self.rpc_calls,[])
        self.assertIn('disables it everywhere',self.dialog.yesno.call_args.args[1])
        self.dialog.yesno.return_value=True
        self.runtime.addon_info=mock.Mock(return_value=row)
        self.runtime.manage(aid,row)
        self.assertEqual(self.rpc_calls,[('Addons.SetAddonEnabled',{'addonid':aid,'enabled':False})])

    def test_cancel_menu_does_not_launch_or_mutate(self):
        self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture'})
        self.runtime.settings_available=lambda aid:True
        self.runtime.rails_supported=lambda:True
        self.runtime.choose.return_value=None
        self.runtime.addon_menu('plugin.video.fixture')
        self.assertEqual(self.calls,[]);self.assertEqual(self.rpc_calls,[])

    def test_first_favourite_accepts_kodi_null_collection_and_keeps_destination(self):
        aid='plugin.video.fixture';path='plugin://'+aid+'/'
        self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture','thumbnail':'icon.png'})
        self.runtime.settings_available=lambda aid:True
        self.runtime.rails_supported=lambda:True
        self.runtime.destination=lambda aid:('plugin',path)
        self.runtime.choose.return_value='favourite'
        for entries in (None, []):
            with self.subTest(entries=entries):
                self.runtime.rpc=mock.Mock(side_effect=[{'favourites':entries},'OK'])
                self.runtime.addon_menu(aid)
                self.assertEqual(self.runtime.rpc.call_args_list[-1],mock.call('Favourites.AddFavourite',
                    {'title':'Fixture','thumbnail':'icon.png','type':'window','window':'videos','windowparameter':path}))
        self.runtime.rpc=mock.Mock(return_value={'favourites':[{'windowparameter':path}]})
        self.runtime.addon_menu(aid)
        self.assertEqual(self.runtime.rpc.call_count,1)
        self.dialog.notification.assert_called_once()

    def test_rejects_command_injection_and_unsafe_ids(self):
        for value in ('plugin.video.good),Quit(', '../plugin.video.x','',None):
            self.assertFalse(valid_id(value))
            with self.assertRaises(ValueError):hidden_setting(value)

    def test_video_capability_preserves_nonstandard_ids_script_and_multicontent(self):
        with tempfile.TemporaryDirectory() as temp:
            self.runtime.xbmcaddon.Addon.return_value.getAddonInfo.return_value=temp
            manifest=Path(temp)/'addon.xml'
            aid='plugin.program.video-capable'
            manifest.write_text('<addon id="'+aid+'"><extension point="xbmc.python.pluginsource"><provides>video audio</provides></extension></addon>')
            self.assertEqual(self.runtime.destination(aid),('plugin','plugin://'+aid+'/?content_type=video'))
            aid='script.video-capable'
            manifest.write_text('<addon id="'+aid+'"><extension point="xbmc.python.script"><provides>video</provides></extension></addon>')
            self.assertEqual(self.runtime.destination(aid),('script',aid))
            manifest.write_text('<addon id="'+aid+'"><extension point="xbmc.python.script"><provides>executable</provides></extension></addon>')
            self.assertIsNone(self.runtime.destination(aid))

    def test_first_party_recovery_cannot_be_hidden_or_disabled(self):
        self.assertNotIn(('Hide from This View','hide'),addon_rows(True,True,manageable=False))
        with self.assertRaises(ValueError):self.runtime.set_hidden('script.infinity.commandcenter',True)
        self.runtime.manage('script.infinity.commandcenter',{'name':'Command Center'})
        self.assertEqual(self.calls,[]);self.assertEqual(self.rpc_calls,[])


    def test_hide_rejected_when_grid_moves_during_popup(self):
        aid='plugin.video.fixture'
        self.runtime.addon_info=mock.Mock(return_value={'name':'Harmless Fixture'})
        self.runtime.settings_available=lambda _aid:False
        self.runtime.rails_supported=lambda:False
        self.runtime.choose.side_effect=lambda title, rows: (
            setattr(self,'selected','plugin.video.different') or 'hide')
        with self.assertRaisesRegex(RuntimeError,'selected Video Source changed'):
            self.runtime.addon_menu(aid)
        self.assertFalse(self.settings)
        self.assertFalse(self.calls)
        self.assertEqual(self.rpc_calls,[])

    def test_favourite_open_and_rails_blocked_after_focus_change(self):
        for action in ('open','favourite','rails','manage','settings','info'):
            with self.subTest(action=action):
                self.selected=self.token='plugin.video.fixture'
                self.calls.clear()
                self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture'})
                self.runtime.settings_available=lambda _aid:True
                self.runtime.rails_supported=lambda:True
                self.runtime.choose.side_effect=lambda title, rows: (
                    setattr(self,'token','plugin.video.other') or action)
                with self.assertRaisesRegex(RuntimeError,'selected Video Source changed'):
                    self.runtime.addon_menu('plugin.video.fixture')
                self.assertFalse(self.calls)
                self.assertEqual(self.rpc_calls,[])

    def test_invalid_window_prevents_menu_instead_of_launching(self):
        self.window_id=10000
        self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture'})
        self.runtime.choose.return_value='open'
        with self.assertRaisesRegex(RuntimeError,'selected Video Source changed'):
            self.runtime.addon_menu('plugin.video.fixture')
        self.runtime.choose.assert_not_called()
        self.runtime.addon_info.assert_not_called()

    def test_rejected_stale_settings_and_rails_capabilities_not_noop(self):
        for action, capability in (('settings','settings_available'),('rails','rails_supported')):
            with self.subTest(action=action):
                self.selected=self.token='plugin.video.fixture'
                self.calls.clear()
                self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture'})
                times=iter((True,False))
                setattr(self.runtime,capability,lambda *a:next(times))
                setattr(self.runtime,'rails_supported' if action=='settings' else 'settings_available',
                        (lambda :False) if action=='settings' else (lambda _aid:False))
                self.runtime.choose.return_value=action
                with self.assertRaisesRegex(RuntimeError,'no longer available'):
                    self.runtime.addon_menu('plugin.video.fixture')
                self.assertEqual(self.calls,[])
                self.assertEqual(self.rpc_calls,[])

    def test_manage_confirmation_cannot_disable_item_if_selection_changes(self):
        aid='plugin.video.fixture'
        row={'name':'Harmless Fixture'}
        self.runtime.choose.return_value='disable'
        def confirm(*a, **kw):
            self.selected='plugin.video.other'
            return True
        self.dialog.yesno.side_effect=confirm
        with self.assertRaisesRegex(RuntimeError,'selected Video Source changed'):
            self.runtime.manage(aid,row)
        self.assertEqual(self.rpc_calls,[])
        self.assertFalse(self.calls)

    def test_hide_stays_only_view_setting_when_selection_is_correct(self):
        aid='plugin.video.fixture'
        self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture'})
        self.runtime.settings_available=lambda _aid:False
        self.runtime.rails_supported=lambda:False
        self.runtime.choose.return_value='hide'
        self.runtime.addon_menu(aid)
        self.assertIn(hidden_setting(aid),self.settings)
        self.assertFalse(self.rpc_calls)
        self.runtime.set_hidden(aid,False)
        self.assertNotIn(hidden_setting(aid),self.settings)
        self.assertFalse(self.rpc_calls)

    def test_valid_info_and_rails_keep_original_handlers(self):
        aid='plugin.video.fixture'
        self.runtime.addon_info=mock.Mock(return_value={'name':'Fixture'})
        self.runtime.settings_available=lambda _aid:True
        self.runtime.rails_supported=lambda:True
        self.runtime.choose.return_value='info'
        self.runtime.addon_menu(aid)
        self.assertEqual(self.calls,['Action(Info,11193)'])
        self.calls.clear()
        self.runtime.choose.return_value='rails'
        self.runtime.addon_menu(aid)
        self.assertEqual(self.calls,['RunScript(script.infinity.rails,add,'+aid+')'])

if __name__=='__main__':unittest.main()
