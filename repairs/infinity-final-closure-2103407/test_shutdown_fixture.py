"""Exact source fixture boundaries only, no emulator success claim."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import shutdown_fixture as fixture


class FixtureTests(unittest.TestCase):
    def device(self,qemu='1'):
        return SimpleNamespace(PACKAGE='com.projectinfinity.kodi',
            shell=lambda *a:qemu if a[-1]=='ro.kernel.qemu' else '37')

    def test_all_six_physical_contract_files_are_exact_and_staged_once(self):
        self.assertEqual(set(fixture.source_bytes()),set(fixture.FILES))
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);stage=out/'fixture';stage.mkdir();args=SimpleNamespace(case='final-participant',out=out);report={}
            fixture.stage(stage,args,report,self.device(),'service.future.persistence.7fa29')
            self.assertEqual({p.name:p.read_bytes() for p in (stage/fixture.ADDON).iterdir()},fixture.source_bytes())
            self.assertFalse(report['independent_compat_fixture']['production_APK_changed'])
            with self.assertRaises(ValueError):fixture.stage(stage,args,report,self.device(),'service.future.persistence.7fa29')

    def test_changed_or_linked_actual_contract_and_physical_or_wrong_case_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);values=fixture.source_bytes()
            for name,(location,_) in fixture.FILES.items():
                target=root/location/fixture.ADDON/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(values[name])
            target=root/'parent'/fixture.ADDON/'addon.xml';target.write_bytes(values['addon.xml']+b' ')
            with self.assertRaises(ValueError):fixture.source_bytes(root)
            target.unlink();target.symlink_to(root/'other.xml')
            with self.assertRaises(ValueError):fixture.source_bytes(root)
            out=root/'out';out.mkdir();stage=out/'fixture';stage.mkdir();args=SimpleNamespace(case='final-participant',out=out)
            for device,case in ((self.device('0'),'final-participant'),(self.device(),'final-search-all-enter')):
                args.case=case
                with self.assertRaises(ValueError):fixture.stage(stage,args,{},device,'service.future.persistence.7fa29')
            self.assertFalse((stage/fixture.ADDON).exists())

    def test_existing_linked_stage_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);stage=out/'fixture';stage.mkdir();(stage/fixture.ADDON).symlink_to(out/'unknown')
            with self.assertRaises(ValueError):fixture.stage(stage,SimpleNamespace(out=out,case='final-participant'),{},self.device(),'service.future.persistence.7fa29')


if __name__=='__main__':unittest.main(verbosity=2)
