"""Preparation refusal/transport checks; host results do not count as Android interactions."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import android_input_preparation as preparation
import android_input_readiness


class InputPreparationTests(unittest.TestCase):
    def device(self,**changes):
        calls=[]
        search='<hierarchy><node package="com.android.settings" text="Search settings" enabled="true" bounds="[0,0][100,100]"/></hierarchy>'
        editor='<hierarchy><node package="com.google.android.settings.intelligence" class="android.widget.EditText" enabled="true" bounds="[0,0][100,100]"/></hierarchy>'
        device=SimpleNamespace(PACKAGE=preparation.PACKAGE,qemu='1',sdk='37',installed='',engine=None,tapped=0)
        def shell(*args,**kw):
            calls.append(args)
            if args[:1]==('getprop',):return device.qemu if args[1]=='ro.kernel.qemu' else device.sdk
            if args[:3]==('pm','list','packages'):return device.installed
            if args[:2]==('input','tap'):device.tapped+=1
            if args[:1]==('cat',):return search if device.tapped==0 else editor
            return ''
        device.shell=shell;device.running_engine=lambda:device.engine
        device.until=lambda function,seconds:function() or (_ for _ in ()).throw(RuntimeError('Actual state missing'))
        for key,value in changes.items():setattr(device,key,value)
        return device,calls

    def test_only_normal_settings_actual_ready_and_home_without_typing_or_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            device,calls=self.device()
            def ready(observed,out):
                self.assertIs(observed,device);(out/'IME-READINESS.json').write_text(json.dumps({'ready':True}));return True
            with patch.object(android_input_readiness,'ready',side_effect=ready):result=preparation.warm(device,Path(temp))
            self.assertTrue(result['passed']);self.assertFalse(result['Infinity_launched'])
            self.assertIn(('am','start','-W','-a','android.settings.SETTINGS'),calls)
            self.assertEqual([x for x in calls if x[:2]==('input','tap')],[('input','tap','50','50')]*2)
            self.assertEqual(calls[-1],('input','keyevent','3'))
            self.assertFalse(any(x[:2] in (('input','text'),('settings','put')) for x in calls))

    def test_other_devices_existing_install_and_live_engine_refuse_before_navigation(self):
        for changes in ({'PACKAGE':'other'},{'qemu':'0'},{'sdk':'36'},{'installed':'package:'+preparation.PACKAGE},{'engine':{'pid':123}}):
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as temp:
                device,calls=self.device(**changes)
                with self.assertRaises(ValueError):preparation.warm(device,Path(temp))
                self.assertFalse(any(x[0] in ('am','input','uiautomator') for x in calls))

    def test_missing_control_or_actual_body_does_not_become_preparation_pass(self):
        for mode in ('control','body'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                device,calls=self.device()
                if mode=='control':
                    original=device.shell
                    device.shell=lambda *a,**kw:'<hierarchy/>' if a[0]=='cat' else original(*a,**kw)
                with patch.object(android_input_readiness,'ready',return_value=False):
                    with self.assertRaises(RuntimeError):preparation.warm(device,Path(temp))
                result=json.loads((Path(temp)/'IME-PREPARATION/PREPARATION.json').read_text())
                self.assertFalse(result['passed']);self.assertNotIn(('input','keyevent','3'),calls)

    def test_feature_guard_retained_no_apk_changes_termination_or_text_repair(self):
        source=Path(preparation.__file__).read_text()
        for forbidden in ('force-stop','pm clear','uninstall','CLOSE_KODI','input\',\'text','settings\',\'put','install\''):
            self.assertNotIn(forbidden,source)
        self.assertIn('device.until(prepared_keyboard,90)',source)

    def test_observed_system_utility_replacement_has_one_bounded_ui_reentry(self):
        with tempfile.TemporaryDirectory() as temp:
            device,calls=self.device();checks=[0]
            device.adb=lambda *a,**kw:'ActivityManager: Killing 2239:com.google.android.settings.intelligence/u0a155 (adj 0): change com.google.android.settings.intelligence'
            def until(fn,seconds):
                for _ in range(5):
                    value=fn()
                    if value:return value
                raise RuntimeError('Original readiness budget expired')
            device.until=until
            def ready(observed,out):
                checks[0]+=1
                if checks[0]==1:device.tapped=0
                value=checks[0]>=3
                (out/'IME-READINESS.json').write_text(json.dumps({'ready':value}))
                return value
            with patch.object(android_input_readiness,'ready',side_effect=ready):
                result=preparation.warm(device,Path(temp))
            self.assertTrue(result['passed']);self.assertIn('system_settings_recovery',result)
            self.assertEqual(len([v for v in calls if v[:2]==('input','tap')]),4)


if __name__=='__main__':unittest.main(verbosity=2)
