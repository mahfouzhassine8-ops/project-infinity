import ast
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET
import android_stress_script as bridge


class StressScriptDispatchTests(unittest.TestCase):
    def context(self,root):
        folder=root/'fixture';folder.mkdir()
        device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',shell=lambda *a:'1' if a[-1]=='ro.kernel.qemu' else '37')
        return folder,SimpleNamespace(out=root,case='final-search-all-enter'),{},device,'service.future.persistence.7fa29'

    def test_bridge_is_only_exact_original_home_builtin_no_autostart_or_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            folder,args,report,device,aid=self.context(Path(temp));bridge.stage(folder,args,report,device,aid)
            target=folder/bridge.ADDON;manifest=ET.fromstring((target/'addon.xml').read_text())
            extensions=manifest.findall('extension')
            self.assertEqual([e.get('point') for e in extensions],['xbmc.python.script','xbmc.addon.metadata'])
            calls=[];exec(compile((target/'default.py').read_text(),'bridge','exec'),{'__builtins__':dict(__import__=lambda *args:SimpleNamespace(executebuiltin=lambda value:calls.append(value)))})
            self.assertEqual(calls,[bridge.BUILTIN])
            self.assertFalse(report['stress_script_bridge']['automatically_started'])
            self.assertEqual(set(p.name for p in target.iterdir()),{'addon.xml','default.py'})
            with self.assertRaises(ValueError):bridge.stage(folder,args,report,device,aid)

    def test_wrong_stage_case_and_physical_device_refused(self):
        for mode in ('physical','case','folder','aid'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                folder,args,report,device,aid=self.context(Path(temp))
                if mode=='physical':device.shell=lambda *a:'0'
                elif mode=='case':args.case='final-participant'
                elif mode=='folder':folder=folder/'other'
                else:aid='other'
                with self.assertRaises(ValueError):bridge.stage(folder,args,report,device,aid)

    def test_enable_and_launch_only_the_fixed_script_identity(self):
        calls=[]
        def rpc(method,params):
            calls.append((method,params))
            if method=='Addons.GetAddonDetails':return {'addon':{'version':'1.0.0','enabled':False}}
            return 'OK'
        device=SimpleNamespace(rpc=rpc);bridge.enable(device);bridge.launch(device)
        self.assertEqual([x[0] for x in calls],['Addons.GetAddonDetails','Addons.SetAddonEnabled','Addons.ExecuteAddon'])
        self.assertTrue(all(x[1]['addonid']==bridge.ADDON for x in calls))
        self.assertEqual(calls[-1][1],{'addonid':bridge.ADDON,'wait':False})
        with self.assertRaises(ValueError):bridge.enable(SimpleNamespace(rpc=lambda *a:{'addon':{'version':'2.0.0'}}))

    def test_both_stress_openings_use_bridge_and_keep_actual_input_assertions(self):
        path=Path(__file__).parent/'android17_stress.py';source=path.read_text();tree=ast.parse(source)
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='android_stress_script' and n.func.attr=='launch']
        self.assertEqual(len(calls),2)
        self.assertNotIn("'params':['universal-search','movie']",source)
        for retained in ("device.until(typing_keyboard,45)","device.until(keyboard,45)","Actual Search text differs","device.until(results,90)","Stress changed protected tracking records"):
            self.assertIn(retained,source)


if __name__=='__main__':unittest.main(verbosity=2)
