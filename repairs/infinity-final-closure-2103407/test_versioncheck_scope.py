"""Execute exact bundled service and distro with controlled external inputs."""
import importlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import patch_versioncheck_scope as correction


class VersionCheckScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(os.environ['INFINITY_SERVICE_PARENT_APK']) as z:
            prefix='assets/addons/service.xbmc.versioncheck/'
            cls.original={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
        if len(cls.original)!=103:raise ValueError('Exact103file bundled service required')
        cls.source=correction.MEMBER[len(prefix):]
        cls.candidate=dict(cls.original);cls.candidate[cls.source]=correction.patch(cls.original[cls.source])

    def execute(self,files,skin='skin.infinity.diggz',android=True,enabled=True):
        calls=[];common=types.ModuleType('version_check.common')
        common.ADDON=types.SimpleNamespace(getSetting=lambda key:'false' if key=='upgrade_apt' or not enabled else 'true')
        common.ADDON_NAME='Version Check';common.ADDON_VERSION='0.5.27+matrix.1'
        for name in ('dialog_yes_no','localise','log','wait_for_abort','message_restart','message_upgrade_success','upgrade_message','upgrade_message2'):
            setattr(common,name,lambda *a,_name=name:calls.append((_name,a)) or False)
        interface=types.ModuleType('version_check.json_interface')
        interface.get_version_file_list=lambda:calls.append(('version_list',)) or {}
        interface.get_installed_version=lambda:calls.append(('installed_version',)) or {}
        versions=types.ModuleType('version_check.versions');versions.compare_version=lambda *a:(False,{},{},{})
        xbmc=types.ModuleType('xbmc');xbmc.getSkinDir=lambda:skin
        xbmc.getCondVisibility=lambda key:android if key=='System.Platform.Android' else not android
        fake={'version_check.common':common,'version_check.json_interface':interface,'version_check.versions':versions,
              'xbmc':xbmc,'xbmcgui':types.ModuleType('xbmcgui')}
        def child(command,*args,**kwargs):
            calls.append(('child',tuple(command)))
            if tuple(command)==('lsb_release','-a'):return b'Distributor ID:\tUbuntu\nDescription:\tUbuntu\nRelease:\t22.04\nCodename:\tjammy\n'
            if tuple(command)==('uname','-rs'):return b'Linux 6.8\n'
            raise AssertionError('Unexpected distro command: '+repr(command))
        saved={k:v for k,v in sys.modules.items() if k=='version_check' or k.startswith('version_check.')}
        for key in saved:del sys.modules[key]
        try:
            with tempfile.TemporaryDirectory() as temp:
                for name,raw in files.items():
                    if name.startswith('resources/lib/'):
                        p=Path(temp)/name[len('resources/lib/'):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
                sys.path.insert(0,temp)
                try:
                    with patch.dict(sys.modules,fake),patch('sys.platform','linux'),patch('subprocess.check_output',child),patch('platform.uname',return_value=('Linux',)):
                        service=importlib.import_module('version_check.service')
                        with patch.object(service,'_check_cryptography'):service.run()
                        return service.DISTRIBUTION,calls
                finally:sys.path.remove(temp)
        finally:
            for key in list(sys.modules):
                if key=='version_check' or key.startswith('version_check.'):del sys.modules[key]
            sys.modules.update(saved)

    def test_exact409_reproduces_desktop_probe_on_android_even_when_disabled(self):
        _,calls=self.execute(self.original,enabled=False)
        self.assertIn(('child',('lsb_release','-a')),calls)
        self.assertIn(('log',('Disabled',)),calls)

    def test_infinity_android_keeps_enabled_version_check_without_desktop_child(self):
        distribution,calls=self.execute(self.candidate)
        self.assertEqual(distribution,'android');self.assertFalse(any(c[0]=='child' for c in calls))
        self.assertIn(('version_list',),calls);self.assertIn(('installed_version',),calls)

    def test_disabled_setting_is_preserved_without_import_probe(self):
        distribution,calls=self.execute(self.candidate,enabled=False)
        self.assertEqual(distribution,'android');self.assertFalse(any(c[0] in ('child','version_list','installed_version') for c in calls))
        self.assertIn(('log',('Disabled',)),calls)

    def test_cobra_android_uses_identical_original_desktop_path(self):
        self.assertEqual(self.execute(self.original,skin='skin.cobra'),self.execute(self.candidate,skin='skin.cobra'))

    def test_other_skin_on_android_is_unchanged(self):
        self.assertEqual(self.execute(self.original,skin='skin.estuary'),self.execute(self.candidate,skin='skin.estuary'))

    def test_infinity_desktop_linux_is_unchanged(self):
        self.assertEqual(self.execute(self.original,android=False),self.execute(self.candidate,android=False))

    def test_unknown_source_is_refused(self):
        with self.assertRaises(ValueError):correction.patch(self.original[self.source]+b'\n')

    def test_exact_inverse_and_every_other_file_preserved(self):
        self.assertEqual([n for n in self.original if self.original[n]!=self.candidate[n]],[self.source])
        self.assertEqual(self.candidate[self.source].replace(correction.AFTER,correction.BEFORE,1),self.original[self.source])


if __name__=='__main__':unittest.main(verbosity=2)
