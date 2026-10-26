"""Only the new candidate metadata/install-over fixture boundaries are selected."""
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
from zipfile import ZipFile

import android17_candidate_probe as probe
import android17_reference_observation as observation
import android17_request as dispatch
import candidate_request as request
import prepare_candidate_fixture as metadata


class CandidateVerificationTests(unittest.TestCase):
    def test_exact_source_feature_and_existing_branch_protections_are_required(self):
        head='a'*40;event={'ref':dispatch.BRANCH,'after':head,'repository':{'full_name':'mahfouzhassine8-ops/project-infinity'}}
        result=dispatch.validate(request.EXPECTED,event,head,[dispatch.REQUEST])
        self.assertEqual(result['SELECTED_CASE'],request.EXPECTED['selected_case'])
        self.assertEqual(result['CANDIDATE_BUILD'],str(request.EXPECTED['candidate_build']))
        for field,value in [('selected_case','final-participant'),('candidate_build',40230842944),
            ('candidate_source_commit','b'*40),('candidate_apk_sha256','0'*64),('authorization',''),
            ('request_id','integrated408-participant-installover-01')]:
            with self.assertRaises(ValueError):dispatch.validate(dict(request.EXPECTED,**{field:value}),event,head,[dispatch.REQUEST])
        for changed in ([],[dispatch.REQUEST,'unowned/source.cpp']):
            with self.assertRaises(ValueError):dispatch.validate(request.EXPECTED,event,head,changed)
        with self.assertRaises(ValueError):dispatch.validate(request.EXPECTED,dict(event,ref='refs/heads/main'),head,[dispatch.REQUEST])

    def test_fixture_inverse_preserves_every_original_assertion(self):
        before=(observation.OLD/'tracking/final-eight/android_selected.py').read_bytes()
        after=probe.fixture(before).decode()
        restored=probe.restore_candidate_fixture(after)
        self.assertEqual(observation.restore_fixture(restored).encode(),before)
        self.assertIn(probe.RECEIPT_AFTER,after);self.assertNotIn(probe.RECEIPT_BEFORE,after)
        tree=lambda raw:[ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.Call) and
            isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='ui' and n.func.attr=='require']
        # Undo the separately checked readout callback (lambda -> record),
        # then compare every original assertion including its full predicate.
        self.assertEqual(tree(before),tree(observation.restore_fixture(after)))
        with self.assertRaises(ValueError):probe.fixture(before+b'\n')

    def test_participant_setup_only_reads_real_addon_profile_without_controller_imports(self):
        cc=Path('/test-real-addon-profile');calls=[]
        scope=dict(mode='final-participant',SEARCH_CASES=(),Path=Path,xbmcvfs=SimpleNamespace(translatePath=lambda p:p),
            xbmcaddon=SimpleNamespace(Addon=lambda aid:(calls.append(aid) or SimpleNamespace(getAddonInfo=lambda key:str(cc)))),
            xbmcgui=SimpleNamespace(Window=lambda ident:('home',ident)))
        exec(compile('if True:\n'+probe.PROFILE_AFTER,'participant-profile','exec'),scope)
        self.assertEqual(scope['profile'],cc);self.assertEqual(calls,['script.infinity.commandcenter'])
        self.assertNotIn('plugin',scope);self.assertNotIn('hub',scope)

    def test_search_observes_actual_records_without_importing_or_granting_firstparty_writers(self):
        with tempfile.TemporaryDirectory() as temp:
            cc=Path(temp);state={'schema':2,'items':{'exact-id':{'position':7}},
                'infinity_search_history_v1':[{'query':'The Matrix','provider':'all'}]}
            raw=json.dumps(state);(cc/'continue-watching.json').write_text(raw)
            scope=dict(mode='final-search-all-enter',SEARCH_CASES=('final-search-all-enter',),Path=Path,json=json,
                xbmcvfs=SimpleNamespace(translatePath=lambda p:p),
                xbmcaddon=SimpleNamespace(Addon=lambda aid:SimpleNamespace(getAddonInfo=lambda key:str(cc))),
                xbmcgui=SimpleNamespace(Window=lambda ident:ident))
            exec(compile('if True:\n'+probe.PROFILE_AFTER,'search-readonly','exec'),scope)
            self.assertEqual(scope['hub'].load_view(cc),state)
            exec(compile('if True:\n'+probe.HISTORY_AFTER,'history-readonly','exec'),scope)
            self.assertEqual(scope['history'],state['infinity_search_history_v1'])
            self.assertEqual((cc/'continue-watching.json').read_text(),raw)
            self.assertNotIn('plugin',scope)
            (cc/'continue-watching.json').unlink();(cc/'continue-watching.json').symlink_to(cc/'other.json')
            with self.assertRaises(RuntimeError):scope['hub'].load_view(cc)

    def fake_device(self,qemu='1',new_uid='10234'):
        class Device:
            PACKAGE='com.projectinfinity.kodi';PRIVATE='/data/user/0/com.projectinfinity.kodi'
            PROFILE='/sdcard/Android/data/com.projectinfinity.kodi/files/.kodi/userdata'
            def __init__(self):self.calls=[];self.uid='10234';self.owner='0';self.data={};self.installed=False
            def shell(self,*a,**kw):
                self.calls.append(('shell',*a))
                if a==('getprop','ro.kernel.qemu'):return qemu
                if a==('getprop','ro.build.version.sdk'):return '37'
                if a[:3]==('pm','list','packages'):return self.PACKAGE if self.installed else ''
                if a[:3]==('stat','-c','%u'):return self.uid if a[-1]==self.PRIVATE else self.owner
                if a[0]=='chown':self.owner=self.uid
                if a==('getenforce',):return 'Enforcing'
                if a[0]=='cat':return self.data.get(a[1],'')
                return ''
            def adb(self,*a,**kw):
                self.calls.append(a)
                if a[0]=='install':
                    self.installed=True
                    if '-r' in a:self.uid=new_uid
                    return 'Success\n'
                if a[0]=='push':self.data[a[-1]]=Path(a[1]).read_text()
                return ''
        return Device()

    def test_actual_installover_sequence_preserves_uid_sentinel_and_never_runs_reset_or_close(self):
        device=self.fake_device()
        def digest(path):return probe.BASELINE_SHA if path.name=='baseline.apk' else request.EXPECTED['candidate_apk_sha256']
        with tempfile.TemporaryDirectory() as temp,mock.patch.object(probe,'digest',digest):
            probe.install_over(device,device.adb,Path('baseline.apk'),Path('candidate.apk'),Path(temp),'service.future.persistence.7fa29')
            report=json.loads((Path(temp)/'INSTALL-OVER-EVIDENCE.json').read_text())
            self.assertEqual((report['baseline_uid'],report['candidate_uid']),('10234','10234'))
            self.assertTrue(report['test_sentinel_preserved']);self.assertFalse(report['actual_user_database_acceptance'])
            installs=[a for a in device.calls if a[0]=='install']
            self.assertEqual(installs,[('install','--no-incremental',Path('baseline.apk')),('install','-r','--no-incremental',Path('candidate.apk'))])
            commands=str(device.calls)
            for forbidden in ('uninstall','pm clear','force-stop','CLOSE_KODI','am start'):self.assertNotIn(forbidden,commands)

    def test_real_device_or_changed_uid_can_never_be_acknowledged_as_installover_pass(self):
        for device in (self.fake_device(qemu='0'),self.fake_device(new_uid='11111')):
            with tempfile.TemporaryDirectory() as temp,mock.patch.object(probe,'digest',lambda p:probe.BASELINE_SHA if p.name=='baseline.apk' else request.EXPECTED['candidate_apk_sha256']):
                with self.assertRaises((ValueError,RuntimeError)):
                    probe.install_over(device,device.adb,Path('baseline.apk'),Path('candidate.apk'),Path(temp),'service.future.persistence.7fa29')
                self.assertFalse((Path(temp)/'INSTALL-OVER-EVIDENCE.json').exists())

    def test_metadata_bridge_does_not_modify_apk_and_refuses_mismatched_or_existing_receipts(self):
        # Format-only fixture; the immutable production request SHA and the
        # mandatory original SDK signature step are never replaced in CI.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);nested=root/'input';nested.mkdir();apk=nested/'fixture.apk'
            versions={'script.infinity.commandcenter':'0.3.5.41','script.infinity.uirepair':'0.1.23',
                'script.infinity.watchedbridge':'1.0.21','script.infinity.rails':'0.2.8'}
            with ZipFile(apk,'w') as z:
                for aid,version in versions.items():z.writestr('assets/addons/'+aid+'/addon.xml','<addon id="'+aid+'" version="'+version+'"/>')
            original=apk.read_bytes();actual=hashlib.sha256(original).hexdigest();baseline=root/'baseline.apk';baseline.write_bytes(b'baseline format fixture')
            report={'source_commit':request.EXPECTED['candidate_source_commit'],'build':str(request.EXPECTED['candidate_build']),
                'candidate_APK_sha256':actual,'unexpected_differences':[],'component_sha256':{},
                'original_certificate_sha256':'d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'}
            (nested/'APK-PRESERVATION.json').write_text(json.dumps(report))
            expected=dict(request.EXPECTED,candidate_apk_sha256=actual)
            def digest(path):return probe.BASELINE_SHA if Path(path)==baseline else hashlib.sha256(Path(path).read_bytes()).hexdigest()
            # Keep baseline outside the candidate artifact, as in real CI.
            moved=root.parent/(root.name+'-baseline.apk');baseline.rename(moved)
            try:
                with mock.patch.dict(request.EXPECTED,expected,clear=True),mock.patch.object(metadata,'digest',lambda p:probe.BASELINE_SHA if Path(p)==moved else digest(p)):
                    receipt=metadata.prepare(root,expected,moved)
                    self.assertFalse(receipt['apk_bytes_changed']);self.assertFalse(receipt['release_accepted'])
                    self.assertEqual(apk.read_bytes(),original)
                    with self.assertRaises(ValueError):metadata.prepare(root,expected,moved)
            finally:moved.unlink()


if __name__=='__main__':unittest.main(verbosity=2)
