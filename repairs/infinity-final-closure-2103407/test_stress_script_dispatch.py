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
        target=folder/'service.future.persistence.7fa29';target.mkdir()
        (target/'service.py').write_text("import os,xbmcaddon,xbmcvfs\nfrom pathlib import Path\nimport android_selected\nroot=xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))\nPath(root).mkdir(parents=True,exist_ok=True)\nandroid_selected.run(root,str(os.getpid()),'final-search-all-enter')\n")
        device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',shell=lambda *a:'1' if a[-1]=='ro.kernel.qemu' else '37')
        return folder,SimpleNamespace(out=root,case='final-search-all-enter'),{},device,'service.future.persistence.7fa29'

    def test_bridge_extends_only_original_admitted_service_and_keeps_exact_inverse(self):
        with tempfile.TemporaryDirectory() as temp:
            folder,args,report,device,aid=self.context(Path(temp))
            service=folder/aid/'service.py';original=service.read_text()
            bridge.stage(folder,args,report,device,aid)
            self.assertEqual(service.read_text(),original+bridge.TAIL)
            self.assertEqual((folder/aid/'android_stress_dispatcher.py').read_bytes(),Path(bridge.__file__).with_name('android_stress_dispatcher.py').read_bytes())
            self.assertFalse(report['stress_script_bridge']['production_changes'])
            self.assertEqual(report['stress_script_bridge']['extra_invokers_per_request'],0)
            self.assertTrue(report['stress_script_bridge']['existing_observer_only'])
            with self.assertRaises(ValueError):bridge.stage(folder,args,report,device,aid)

    def test_participant_stage_keeps_original_service_and_has_no_search_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            folder,args,report,device,aid=self.context(Path(temp))
            args.case='final-participant';service=folder/aid/'service.py'
            original=service.read_text().replace("'final-search-all-enter'","'final-participant'")
            service.write_text(original);bridge.stage(folder,args,report,device,aid)
            self.assertEqual(service.read_text(),original+bridge.TAIL)
            self.assertNotIn('RunScript',service.read_text())
            self.assertEqual(report['stress_script_bridge']['extra_invokers_per_request'],0)

    def test_wrong_stage_case_and_physical_device_refused(self):
        for mode in ('physical','case','folder','aid'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                folder,args,report,device,aid=self.context(Path(temp))
                if mode=='physical':device.shell=lambda *a:'0'
                elif mode=='case':args.case='final-actions'
                elif mode=='folder':folder=folder/'other'
                else:aid='other'
                with self.assertRaises(ValueError):bridge.stage(folder,args,report,device,aid)

    def test_admitted_dispatch_requires_same_owner_bounded_action_and_exact_ack(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp,mock.patch.object(bridge,'_context',None):
            root=Path(temp);owner={'pid':123,'owner':'exact-native-token'};pushed=[]
            ready={'pid':123,'max_requests':bridge.MAX_REQUESTS,'first_actual_feature_passed':True,'source':'admitted-native-home-actions','selected_mode':'final-search-all-enter'}
            device=SimpleNamespace(PROFILE='/qa/profile',read_json=lambda p:ready,
                until=lambda fn,seconds:fn(),running_engine=lambda:owner,
                adb=lambda *args:pushed.append(args))
            with self.assertRaises(ValueError):bridge.launch(device)
            bridge.initialize(device,root,owner)
            bridge.launch(device)
            request=__import__('json').loads((root/'dispatch-request.json').read_text())
            self.assertEqual(request,{'pid':123,'sequence':1,'action':'home-search'})
            self.assertEqual(pushed[0][0],'push')
            with self.assertRaises(ValueError):bridge.verify_dispatch(device)
            device.read_json=lambda p:request
            bridge.verify_dispatch(device)
            with self.assertRaises(ValueError):bridge.launch(device,action='arbitrary-action')
            device.running_engine=lambda:{'pid':124,'owner':'exact-native-token'}
            with self.assertRaises(ValueError):bridge.launch(device)
            device.running_engine=lambda:owner;bridge._context['sequence']=bridge.MAX_REQUESTS
            with self.assertRaises(ValueError):bridge.launch(device)

    def test_participant_home_dispatch_refuses_search_without_new_invoker(self):
        from unittest import mock
        import android_stress_dispatcher as dispatcher
        self.assertEqual(dispatcher.require_ready({'passed':True,'pid':123,'selected_mode':'final-participant'},123),'final-participant')
        for wrong in ({'passed':False,'pid':123,'selected_mode':'final-participant'},
                      {'passed':True,'pid':124,'selected_mode':'final-participant'},
                      {'passed':True,'pid':123,'selected_mode':'final-actions'}):
            with self.assertRaises(ValueError):dispatcher.require_ready(wrong,123)
        owner={'pid':123,'owner':'same'}
        with tempfile.TemporaryDirectory() as temp,mock.patch.object(bridge,'_context',
                dict(selected_mode='final-participant',out=Path(temp),owner=owner,target='/qa',sequence=0)):
            pushed=[];device=SimpleNamespace(running_engine=lambda:owner,adb=lambda *a:pushed.append(a))
            with self.assertRaises(ValueError):bridge.launch(device,'home-search')
            self.assertEqual(pushed,[])
            bridge.launch(device,'home-resume-tv');self.assertEqual(len(pushed),1)
            self.assertEqual(bridge._context['sequence'],1)

    def test_both_stress_openings_use_bridge_and_keep_actual_input_assertions(self):
        path=Path(__file__).parent/'android17_stress.py';source=path.read_text();tree=ast.parse(source)
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='android_stress_script' and n.func.attr=='launch']
        self.assertEqual(len(calls),2)
        self.assertNotIn("'params':['universal-search','movie']",source)
        for retained in ("device.until(typing_keyboard,45)","device.until(keyboard,45)","Actual Search text differs","device.until(results,90)","Stress changed protected tracking records"):
            self.assertIn(retained,source)


if __name__=='__main__':unittest.main(verbosity=2)
