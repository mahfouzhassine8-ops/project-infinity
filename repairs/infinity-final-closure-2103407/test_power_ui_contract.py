from io import BytesIO
import tempfile
from pathlib import Path
import unittest
from zipfile import ZipFile
import power_ui_contract as ui


class PowerContractTests(unittest.TestCase):
    def test_exact_visible_route_required_wrong_force_close_or_default_refused(self):
        xml='<window><defaultcontrol>200</defaultcontrol><controls><control id="200"><label>CLOSE KODI</label><onclick condition="System.Platform.Android">SetProperty(Infinity.Close.InProgress,true,Home)</onclick><onclick condition="System.Platform.Android">'+ui.BUILTIN+'</onclick></control></controls></window>'
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'format.apk'
            for text,valid in [(xml,True),(xml.replace(ui.ACTION,ui.ACTION+'OTHER'),False),
                               (xml.replace('<defaultcontrol>200','<defaultcontrol>300'),False),
                               (xml.replace('<label>CLOSE KODI','<label>FORCE CLOSE KODI'),False)]:
                with ZipFile(path,'w') as z:z.writestr(ui.SKIN,text)
                if valid:self.assertTrue(ui.source_route(path)['backend_matches'])
                else:
                    with self.assertRaises(AssertionError):ui.source_route(path)

    def test_recents_or_process_name_never_replaces_real_engine_pid_ownership(self):
        rows=[dict(pid=10,name='com.projectinfinity.kodi:kodi'),dict(pid=11,name='com.projectinfinity.kodi'),
              dict(pid=12,name='a-child-executable')]
        result=ui.partition_processes(rows,{'pid':10})
        self.assertEqual(result['kodi_engine'],[rows[0]])
        self.assertEqual(result['android_coordinator'],[rows[1]])
        self.assertEqual(result['other_owned_processes'],[rows[2]])
        self.assertEqual(ui.partition_processes([],{'pid':10}),
            dict(kodi_engine=[],android_coordinator=[],other_owned_processes=[]))


if __name__=='__main__':unittest.main(verbosity=2)
