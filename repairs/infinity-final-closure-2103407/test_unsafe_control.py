"""Strict disposable negative control checks; never a simulated runtime PASS."""
import ast
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET
import unsafe_control as control


class UnsafeControlTests(unittest.TestCase):
    def receipt(self):
        owner={'pid':123,'owner':'actual-owner'}
        native=dict(**owner,essential_writes_durable=False,
            essential_write_blockers=['unverified_protected_writer:'+control.ADDON+':default.py'],
            script_persistence={'blockers':[dict(writer=control.ADDON+':default.py',blocking=True,
                reason='external_or_opaque_writer_requires_explicit_participant')]})
        row=dict(**owner,phase='CHECKPOINT_FAILED',checkpoint_saved=False,authorization_consumed=False,
                 process_death_confirmed=False,last_native_status=native)
        return row,owner,[{'pid':123}]

    def test_saved_authorized_dead_or_unrelated_refusal_never_passes(self):
        row,owner,processes=self.receipt();control.verify_refusal(row,owner,processes)
        for key,value in [('owner','stale'),('pid',124),('phase','COMPLETE'),('checkpoint_saved',True),
            ('authorization_consumed',True),('process_death_confirmed',True)]:
            with self.assertRaises(AssertionError):control.verify_refusal(dict(row,**{key:value}),owner,processes)
        with self.assertRaises(AssertionError):control.verify_refusal(row,owner,[])
        for key,value in [('pid',124),('owner','stale'),('essential_writes_durable',True),
            ('essential_write_blockers',[]),('essential_write_blockers',['unrelated writer'])]:
            changed=deepcopy(row);changed['last_native_status'][key]=value
            with self.assertRaises(AssertionError):control.verify_refusal(changed,owner,processes)
        for key,value in [('writer','service.xbmc.versioncheck:runner.py'),('blocking',False),('reason','unrelated')]:
            changed=deepcopy(row);changed['last_native_status']['script_persistence']['blockers'][0][key]=value
            with self.assertRaises(AssertionError):control.verify_refusal(changed,owner,processes)

    def device(self,qemu='1'):
        return SimpleNamespace(PACKAGE='com.projectinfinity.kodi',
            shell=lambda *a:qemu if a[-1]=='ro.kernel.qemu' else '37')

    def test_stage_only_disposable_namespace_and_no_auto_started_service(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);folder=out/'fixture';folder.mkdir();args=SimpleNamespace(out=out,case='final-participant');report={}
            with self.assertRaises(ValueError):control.stage(folder,args,report,self.device('0'),'service.future.persistence.7fa29')
            control.stage(folder,args,report,self.device(),'service.future.persistence.7fa29')
            target=folder/control.ADDON;xml=ET.parse(target/'addon.xml')
            self.assertEqual(xml.find('extension').get('point'),'xbmc.python.script')
            self.assertFalse(any(n.get('point')=='xbmc.service' for n in xml.findall('extension')))
            self.assertEqual((target/'default.py').read_text(),control.SCRIPT)
            with self.assertRaises(ValueError):control.stage(folder,args,report,self.device(),'service.future.persistence.7fa29')

    def test_controlled_source_is_bounded_and_writes_only_own_profile_marker(self):
        tree=ast.parse(control.SCRIPT)
        popen=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Popen')
        values=popen.args[0].elts
        self.assertEqual(ast.literal_eval(values[0]),'/system/bin/sh')
        command=ast.literal_eval(values[2]);self.assertIn('> "$1"',command);self.assertIn('/system/bin/sleep 12',command)
        self.assertIn("xbmcaddon.Addon().getAddonInfo('profile')",control.SCRIPT)
        self.assertIn('child.communicate(timeout=20)',control.SCRIPT)
        for forbidden in ('CLOSE_KODI','force-stop','kill(','pm clear','uninstall','script.infinity.commandcenter'):
            self.assertNotIn(forbidden,control.SCRIPT)


if __name__=='__main__':unittest.main(verbosity=2)
