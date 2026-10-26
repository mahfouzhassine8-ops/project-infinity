"""Additional observability cannot acknowledge a failure or alter a test assertion."""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import android17_reference_observation as observation


class ReferenceObservationTests(unittest.TestCase):
    def test_exact_fixture_inverse_diff_and_every_original_assertion_are_preserved(self):
        path=observation.OLD/'tracking/final-eight/android_selected.py'
        before=path.read_bytes();after=observation.instrument_fixture(before).decode()
        self.assertEqual(observation.restore_fixture(after),before.decode())
        with self.assertRaises(ValueError):observation.instrument_fixture(before+b'\n')
        self.assertEqual(after.count('ui.require('),before.decode().count('ui.require('))

    def test_failed_assertion_and_failed_original_export_cannot_become_success(self):
        lines=[]
        class Output:
            def write_text(self,text):raise PermissionError('fixture export denied')
        result={'passed':False,'failure':'RuntimeError: original assertion failed','traceback':'original context'}
        scope={'result':result,'xbmc':SimpleNamespace(log=lambda *args:lines.append(args[0]),LOGERROR=4),
               'json':json,'os':os,'mode':'final-search-all-enter','output':Output()}
        # Use the actual parsed finally body, retaining nested try/raise.
        tree=ast.parse('def fixture():\n    try:\n        pass\n'+observation.AFTER+'\n')
        statements=tree.body[0].body[0].finalbody
        executable=ast.fix_missing_locations(ast.Module(body=statements,type_ignores=[]))
        with self.assertRaises(PermissionError):exec(compile(executable,'fixture-finally','exec'),scope)
        self.assertFalse(result['passed'])
        original=observation.failed_observation('\n'.join(lines),os.getpid())
        self.assertEqual(original['failure'],'RuntimeError: original assertion failed')
        self.assertIn('INFINITY_FEATURE_FIXTURE_EXPORT_FAILED PermissionError',lines)

    def test_only_exact_pid_selected_failure_is_reported_never_a_pass(self):
        row={'pid':37,'selected_mode':'final-search-all-enter','passed':False,'failure':'original failure'}
        prefix='2026-10-26 info INFINITY_FEATURE_FIXTURE_FAILURE '
        self.assertEqual(observation.failed_observation(prefix+json.dumps(row),37),row)
        for change in ({'pid':38},{'selected_mode':'final-continue'},{'passed':True}):
            self.assertIsNone(observation.failed_observation(prefix+json.dumps(dict(row,**change)),37))
        self.assertIsNone(observation.failed_observation(prefix+'malformed',37))

    def test_real_setup_observation_never_sets_feature_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            source=observation.instrument_fixture((observation.OLD/'tracking/final-eight/android_selected.py').read_bytes())
            run=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run')
            record=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='record_setup')
            result={'passed':False,'first_use_observation':{'finite_startup_task_bodies':{'runMaintenance':{'body_completed':False}}}}
            scope=dict(path=Path(directory),cycle='37',mode='final-search-all-enter',os=os,json=json,result=result)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[record],type_ignores=[])),'record','exec'),scope)
            scope['record_setup']('provider-first-use')
            row=json.loads((Path(directory)/'search-setup-37.json').read_text())
            self.assertFalse(row['passed']);self.assertFalse(result['passed'])
            self.assertEqual(row['first_use_observation'],result['first_use_observation'])
            self.assertFalse((Path(directory)/'navigation-ready-37.json').exists())

    def test_only_exact_retained_prepared_wait_contains_existing_setup_bounds(self):
        scope={}
        exec(compile('def prepared(): pass',str(observation.OLD/'universal/android_search_input.py'),'exec'),scope)
        prepared=scope['prepared']
        self.assertEqual(observation.preparation_seconds(prepared,600),1800)
        for seconds in (10,45,90,180,900,1800):
            self.assertEqual(observation.preparation_seconds(prepared,seconds),seconds)
        self.assertEqual(observation.preparation_seconds(lambda:None,600),600)
        exec(compile('def prepared(): pass','other-driver.py','exec'),scope)
        self.assertEqual(observation.preparation_seconds(scope['prepared'],600),600)

    def test_debug_setup_is_original_recipe_and_refuses_existing_configuration(self):
        calls=[]
        device=SimpleNamespace(PROFILE='/disposable',shell=lambda *a,**kw:'',adb=lambda *a:calls.append(a))
        with tempfile.TemporaryDirectory() as directory:
            observation.setup_logging(device,Path(directory))
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][0],'push')
            self.assertEqual(calls[0][-1],'/disposable/advancedsettings.xml')
            raw=calls[0][1].read_text()
            self.assertIn(raw,(observation.OLD/'android_probe.py').read_text())
            device.shell=lambda *a,**kw:'regular file'
            with self.assertRaises(ValueError):observation.setup_logging(device,Path(directory))
            self.assertEqual(len(calls),1)


class FixtureOwnershipTests(unittest.TestCase):
    def device(self,owner='0',qemu='1'):
        class Device:
            PACKAGE='com.projectinfinity.kodi'
            PRIVATE='/data/user/0/com.projectinfinity.kodi'
            PROFILE='/sdcard/Android/data/com.projectinfinity.kodi/files/.kodi/userdata'
            def __init__(self):self.calls=[];self.owner=owner
            def shell(self,*args,**kwargs):
                self.calls.append(args)
                if args==('getprop','ro.kernel.qemu'):return qemu
                if args==('getprop','ro.build.version.sdk'):return '37'
                if args[:3]==('stat','-c','%u'):return '10234' if args[-1]==self.PRIVATE else self.owner
                if args[0]=='chown':self.owner='10234'
                if args==('getenforce',):return 'Enforcing'
                return ''
        return Device()

    def test_root_owned_disposable_fixture_only_gets_original_app_uid(self):
        device=self.device();result=observation.owned_fixture_profile(device,'service.future.persistence.7fa29')
        self.assertEqual((result['before_uid'],result['after_uid']),('0','10234'))
        mutation=[args for args in device.calls if args[0] in ('chown','restorecon')]
        exact='/data/media/0/Android/data/com.projectinfinity.kodi/files/.kodi/userdata/addon_data/service.future.persistence.7fa29'
        self.assertEqual(mutation,[('chown','-R','10234:10234',exact),('restorecon','-RF',exact)])
        self.assertFalse(result['permissions_relaxed'])
        self.assertFalse(any(args[0] in ('chmod','setenforce','rm') for args in device.calls))

    def test_already_owned_profile_keeps_ownership_and_permissions(self):
        device=self.device(owner='10234');observation.owned_fixture_profile(device,'service.future.persistence.7fa29')
        self.assertFalse(any(args[0] in ('chown','restorecon','chmod') for args in device.calls))

    def test_real_device_wrong_profile_or_unexpected_owner_are_refused(self):
        for device,name in ((self.device(qemu='0'),'service.future.persistence.7fa29'),
                            (self.device(),'script.infinity.commandcenter'),
                            (self.device(owner='11111'),'service.future.persistence.7fa29')):
            with self.assertRaises(ValueError):observation.owned_fixture_profile(device,name)
            self.assertFalse(any(args[0] in ('chown','restorecon','chmod') for args in device.calls))


if __name__=='__main__':unittest.main(verbosity=2)
