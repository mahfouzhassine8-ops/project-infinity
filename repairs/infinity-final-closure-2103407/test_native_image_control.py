from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import unquote,urlsplit
import native_image_control as control


class NativeImageControlTests(unittest.TestCase):
    def actual_format(self):
        lines=[]
        for i in sorted(control.IDS):
            resource='window=13001;control='+str(i)+';multiimage-protocol:image'
            lines+=['log INFINITY_MULTIIMAGE_BEGIN token='+str(i)+' job='+str(i+100)+' resource='+resource,
                    'log CDirectoryFactory::Create - unsupported protocol(image) in '+control.image_path(i),
                    'log INFINITY_MULTIIMAGE_RETIRED token='+str(i)+' job='+str(i+100)+' unchanged_receipt=true phase=completion_receipt_verified reason= resource='+resource]
        return '\n'.join(lines)

    def test_all16_real_log_identities_required_and_unsafe_or_missing_never_pass(self):
        raw=self.actual_format();self.assertEqual(control.verify_log(raw,13001)['actual_native_jobs'],16)
        for bad in (raw.replace('unchanged_receipt=true','unchanged_receipt=false',1),raw.replace('reason= resource','reason=opaque resource',1),raw.replace('phase=completion_receipt_verified','phase=completed_write_failed',1),raw.replace('job=2200 unchanged','job=9999 unchanged',1),raw.replace('control=2100','control=2199'),raw.split('\n',1)[1],raw+'\n'+raw.splitlines()[0],raw.replace('unsupported protocol(image)','unobserved directory'),raw+'\n'+raw.splitlines()[1],raw.replace(control.image_path(2100),'image://relative/')):
            with self.assertRaises(AssertionError):control.verify_log(bad,13001)
        with self.assertRaises(AssertionError):control.verify_log(raw,13002)

    def test_actual16_native_controls_script_only_and_exact_disposable_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'fixture';folder.mkdir();args=SimpleNamespace(out=root,case='final-participant');report={}
            device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',shell=lambda *a:'1' if a[-1]=='ro.kernel.qemu' else '37')
            control.stage(folder,args,report,device,'service.future.persistence.7fa29')
            target=folder/control.ADDON;manifest=ET.parse(target/'addon.xml')
            self.assertEqual([e.get('point') for e in manifest.findall('extension')],['xbmc.python.script','xbmc.addon.metadata'])
            layout=ET.parse(target/'resources/skins/Default/1080i/native-images.xml');widgets=layout.findall('controls/control')
            self.assertEqual({int(w.get('id')) for w in widgets},control.IDS)
            self.assertTrue(all(w.get('type')=='multiimage' for w in widgets))
            for widget in widgets:
                path=urlsplit(widget.find('imagepath').text)
                self.assertEqual(path.scheme,'image')
                self.assertEqual(unquote(path.netloc),'special://profile/addon_data/'+control.ADDON+'/native-directory-'+widget.get('id'))
            self.assertIn('xbmcgui.WindowXML',control.SCRIPT);self.assertIn('window.close()',control.SCRIPT)
            with self.assertRaises(ValueError):control.stage(folder,args,report,device,'service.future.persistence.7fa29')
            with self.assertRaises(ValueError):control.stage(folder,args,report,device,'wrong')
            device.shell=lambda *a:'0'
            with self.assertRaises(ValueError):control.stage(folder,args,report,device,'service.future.persistence.7fa29')

    def test_distinct_refresh_generations_and_verified_unstarted_jobs_are_separate(self):
        raw=self.actual_format()
        extra='\n'.join(raw.splitlines()[:3]).replace('token=2100','token=9991').replace('job=2200','job=9992')
        raw+='\n'+extra
        cancelled='log INFINITY_MULTIIMAGE_RETIRED token=9993 job=9994 unchanged_receipt=true phase=completion_receipt_verified reason= resource=window=13001;control=2100;multiimage-protocol:image'
        result=control.verify_log(raw+'\n'+cancelled,13001)
        self.assertEqual(result['actual_native_jobs'],17)
        self.assertEqual(result['actual_directory_factory_terminals'],17)
        self.assertEqual(result['verified_readonly_receipts'],18)
        self.assertEqual(result['verified_unchanged_without_start'],[dict(token=9993,job=9994,control=2100)])
        for bad in (raw+'\n'+extra,raw.replace('token=9991','token=2100'),
                    raw.replace('job=9992','job=2200'),raw.replace('control=2100','control=2101',1),
                    raw+'\n'+cancelled.replace('unchanged_receipt=true','unchanged_receipt=false')):
            with self.assertRaises(AssertionError):control.verify_log(bad,13001)


if __name__=='__main__':unittest.main(verbosity=2)
