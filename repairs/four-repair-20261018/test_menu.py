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
        def builtin(s,*args):
            self.calls.append(s)
            if s.startswith('Skin.SetBool('):self.settings.add(s[13:-1])
            elif s.startswith('Skin.Reset('):self.settings.discard(s[11:-1])
        self.dialog=mock.Mock();self.dialog.yesno.return_value=False
        window=mock.Mock();window.setProperty.side_effect=lambda k,v:self.properties.update({k:v})
        self.xbmc=types.SimpleNamespace(executebuiltin=builtin,getCondVisibility=lambda s:s[16:-1] in self.settings,
            getInfoLabel=lambda s:'plugin.video.fixture')
        modules={'xbmc':self.xbmc,'xbmcgui':types.SimpleNamespace(Window=lambda *a:window,Dialog=lambda:self.dialog),
                 'xbmcaddon':types.SimpleNamespace(Addon=mock.Mock()),'xbmcvfs':types.SimpleNamespace(exists=lambda p:True,translatePath=str),
                 'popup':types.SimpleNamespace(choose=mock.Mock(return_value=None))}
        with mock.patch.dict(sys.modules,modules):
            spec=importlib.util.spec_from_file_location('ui_runtime_test',HERE/'addon/runtime.py')
            self.runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.runtime)
        self.runtime.rpc=mock.Mock(side_effect=lambda *a:self.rpc_calls.append(a))

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

if __name__=='__main__':unittest.main()
