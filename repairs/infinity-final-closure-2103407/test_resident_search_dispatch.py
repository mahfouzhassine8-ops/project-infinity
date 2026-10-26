"""Test-only dispatch admission; these checks do not simulate a Search PASS."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import android_stress_dispatcher as dispatch
import android_stress_script as script


class ResidentDispatchTests(unittest.TestCase):
    def test_original_search_pass_and_exact_consecutive_request_required(self):
        ready=dict(passed=True,pid=123,selected_mode='final-search-all-enter')
        dispatch.require_ready(ready,123)
        for changed in ({'passed':False},{'pid':124},{'selected_mode':'other'}):
            with self.assertRaises(ValueError):dispatch.require_ready(dict(ready,**changed),123)
        request=dict(pid=123,sequence=1,action='home-search')
        self.assertTrue(dispatch.accept(request,123,1))
        for changed in ({'pid':124},{'pid':True},{'sequence':2},{'sequence':True},
                        {'sequence':0},{'action':'arbitrary command'},{'extra':True}):
            self.assertFalse(dispatch.accept(dict(request,**changed),123,1))
        self.assertFalse(dispatch.accept(dict(request,sequence=56),123,56))

    def test_exact_observer_body_retained_no_new_service_or_production_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'fixture';target=folder/script.ADDON;target.mkdir(parents=True)
            before="import os,xbmcaddon,xbmcvfs\nfrom pathlib import Path\nimport android_selected\nroot=xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))\nPath(root).mkdir(parents=True,exist_ok=True)\nandroid_selected.run(root,str(os.getpid()),'final-search-all-enter')\n"
            (target/'service.py').write_text(before)
            device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',shell=lambda *a:'1' if a[-1]=='ro.kernel.qemu' else '37')
            report={};args=SimpleNamespace(out=root,case='final-search-all-enter')
            script.stage(folder,args,report,device,script.ADDON)
            self.assertEqual((target/'service.py').read_text(),before+script.TAIL)
            self.assertEqual((target/'android_stress_dispatcher.py').read_bytes(),Path(dispatch.__file__).read_bytes())
            self.assertEqual({p.name for p in folder.iterdir()},{script.ADDON})
            self.assertEqual(report['stress_script_bridge']['extra_invokers_per_request'],0)
            with self.assertRaises(ValueError):script.stage(folder,args,report,device,script.ADDON)


if __name__=='__main__':unittest.main(verbosity=2)
