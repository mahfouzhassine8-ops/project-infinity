"""Policy/routing contracts only: no SDK, provider network, APK build or device.

Run: PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/test_infinity_focused_policy.py
Requires PyYAML. Mocks deliberately do not constitute Android acceptance.
"""
import ast
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import yaml

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'repairs/save-later-multiimage-20261023'
sys.path.insert(0,str(HERE))
import android_feature_device as device
import android_feature_probe as feature
import android_probe as staging

FEATURE='infinity-saved-navigation-android.yml'
SHUTDOWN='infinity-shutdown-verification.yml'
BUILD='infinity-saved-navigation-multiimage.yml'

def workflow(name):
    return yaml.load((ROOT/'.github/workflows'/name).read_text(),Loader=yaml.BaseLoader)

class WorkflowIsolation(unittest.TestCase):
    def test_independent_jobs_and_authorized_build_trigger(self):
        groups=[]
        for name in (FEATURE,SHUTDOWN,BUILD):
            with self.subTest(workflow=name):
                w=workflow(name)
                self.assertEqual(set(w['on']),{'workflow_dispatch','push'} if name==BUILD else {'workflow_dispatch'})
                if name==BUILD:
                    push=w['on']['push']
                    self.assertEqual(push['branches'],['work/infinity-saved-route-correction-20261023'])
                    self.assertIn('.github/workflows/infinity-saved-navigation-multiimage.yml',push['paths'])
                    self.assertIn('repairs/save-later-multiimage-20261023/tracking/overlay/**',push['paths'])
                    self.assertIn('repairs/save-later-multiimage-20261023/build.py',push['paths'])
                    self.assertTrue(all(p.startswith('repairs/save-later-multiimage-20261023/') or p=='.github/workflows/infinity-saved-navigation-multiimage.yml' for p in push['paths']))
                self.assertEqual(len(w['jobs']),1)
                groups.append(w['concurrency']['group'])
                job=next(iter(w['jobs'].values()))
                self.assertNotIn('needs',job)
                self.assertNotIn('strategy',job)
                self.assertNotIn('continue-on-error',job)
                for step in job['steps']:self.assertNotIn('continue-on-error',step)
        self.assertEqual(len(set(groups)),3)

    def test_explicit_scope_and_non_executable_default(self):
        for name,key,valid in ((FEATURE,'feature',feature.CASES),
                              (SHUTDOWN,'scenario',('safe','pending','opaque','native-opaque','lost-file',*feature.CASES[1:5]))):
            w=workflow(name);inputs=w['on']['workflow_dispatch']['inputs']
            self.assertEqual(inputs['authorization']['required'],'true')
            self.assertNotIn(inputs[key]['default'],valid)
            self.assertEqual(set(inputs[key]['options'])-{inputs[key]['default']},set(valid))
            steps=next(iter(w['jobs'].values()))['steps']
            # Scope admission precedes even signed-artifact retrieval.
            self.assertIn("os.environ['AUTHORIZED_SCOPE'].strip()",steps[1]['run'])
            self.assertIn("os.environ['SELECTED_CASE'] in allowed",steps[1]['run'])

    def test_feature_has_no_shutdown_entrypoint_or_fixture(self):
        w=workflow(FEATURE);job=next(iter(w['jobs'].values()))
        execution=[s for s in job['steps'] if s.get('uses','').startswith('reactivecircus/')]
        self.assertEqual(len(execution),1)
        script=execution[0]['with']['script']
        self.assertIn('android_feature_probe.py',script)
        for forbidden in ('android_probe.py','android_binding.py','--mode','close_trace'):
            self.assertNotIn(forbidden,script)
        downloaded=[s['with']['name'] for s in job['steps'] if s.get('uses','').startswith('actions/download-artifact')]
        self.assertEqual(downloaded,['Infinity-Saved-Navigation-MultiImage-INTERNAL-QA-NOT-ACCEPTED'])
        source=(HERE/'android_feature_probe.py').read_text()
        # All imported staging entrypoints are setup, never the old main runner.
        tree=ast.parse(source)
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name) and n.func.value.id=='staging'}
        self.assertEqual(calls,{'extra','admit_runtime'})

    def test_approved_push_scope_is_a_build_only_gate(self):
        build=workflow(BUILD)
        code=build['jobs']['build']['steps'][1]['run']
        for expected in ("os.environ['GITHUB_EVENT_NAME']=='push'",
                         "os.environ['GITHUB_REF']=='refs/heads/work/infinity-saved-route-correction-20261023'",
                         "tracking/SCOPE.json", "scope['authorization']",
                         "scope['cobra_modifications'] is False", "'shutdown'"):
            self.assertIn(expected,code)
        self.assertEqual(set(workflow(FEATURE)['on']),{'workflow_dispatch'})
        self.assertEqual(set(workflow(SHUTDOWN)['on']),{'workflow_dispatch'})
        self.assertNotIn('workflow_run',build['on'])
        self.assertNotIn('needs',build['jobs']['build'])
        self.assertNotIn('continue-on-error',build['jobs']['build'])

    def test_packaging_requires_integrity_not_behavior_reports(self):
        commands='\n'.join(s.get('run','') for s in workflow(BUILD)['jobs']['build']['steps'])
        for forbidden in ('test_navigation','test_native','test_retained','android_probe.py','android_feature_probe.py','pytest'):
            self.assertNotIn(forbidden,commands)
        for required in ('build.py prepare','build.py compile','build.py package','sha256sum -c','dex_binding.py prepare'):
            self.assertIn(required,commands)
        code=ast.parse((HERE/'build.py').read_text())
        package=next(n for n in code.body if isinstance(n,ast.FunctionDef) and n.name=='package')
        constants=[n.value for n in ast.walk(package) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        self.assertNotIn('RETAINED-PERSISTENCE.json',constants)
        self.assertFalse(any(v.startswith('HOST-') for v in constants))
        self.assertIn('NOT_RUN_IN_PACKAGING',constants)
        self.assertIn('VERIFICATION-STATUS.json',constants)
        self.assertIn('Permanent signer required; no fallback',constants)
        self.assertIn('Compiler output drift',constants)
        calls=[n.func.attr for n in ast.walk(package) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertGreaterEqual(calls.count('verify_signature'),2)

    def test_embedded_python_and_shell_parse(self):
        import subprocess
        for name in (FEATURE,SHUTDOWN,BUILD):
            for step in next(iter(workflow(name)['jobs'].values()))['steps']:
                script=step.get('run') or step.get('with',{}).get('script')
                if not script:continue
                result=subprocess.run(['bash','-n'],input=script,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
                import re
                for match in re.finditer(r"python3 - <<'(\w+)'\n(.*?)\n\1(?:\n|$)",script,re.S):
                    ast.parse(match.group(2))

class TransportBoundary(unittest.TestCase):
    def test_rejects_termination_and_reset(self):
        for command in ('am broadcast -a CLOSE_KODI','am start InfinityPowerControlActivity',
                        'am force-stop com.projectinfinity.kodi','Application.Quit',
                        'System.Shutdown','Powerdown()','Quit()','pm clear package','pm uninstall package','reboot'):
            with self.subTest(command=command),self.assertRaises(RuntimeError):device.guard([command])
        device.guard(['am','start','-n',device.PACKAGE+'/.Splash'])
        device.guard(['Files.GetDirectory',{'directory':'plugin://selected/'}])

    def test_invalid_selection_does_not_contact_device(self):
        with patch.object(device,'adb',side_effect=AssertionError('Device contacted')):
            for case,authorization in [('select-a-feature','approved'),('multiimage',' '),('safe','approved')]:
                with self.assertRaises(ValueError):feature.execute(NS(case=case,authorization=authorization))

    def simulate(self,case='multiimage',result=None,sdk='37',installed=False):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);apk=root/'fixture.apk'
            with ZipFile(apk,'w') as archive:
                archive.writestr('assets/addons/script.infinity.commandcenter/addon.xml','fixture')
            args=NS(case=case,authorization='policy contract mock only',apk=apk,
                    expected_sha=hashlib.sha256(apk.read_bytes()).hexdigest(),out=root/'out')
            mode='safe' if case=='saved-navigation' else 'feature-multiimage' if case=='multiimage' else case
            result=result or dict(passed=True,pid=42,selected_mode=mode,
                                 selected_features=['multiimage'] if case=='multiimage' else ['navigation'])
            calls=[]
            def adb(*args,**kwargs):
                device.guard(args);calls.append(args)
                return 'Success' if args[0]=='install' else ''
            def shell(*args,**kwargs):
                device.guard(args);calls.append(args)
                if args[0]=='getprop':return {'ro.kernel.qemu':'1','ro.build.version.sdk':sdk,'ro.build.version.release':'17','ro.product.cpu.abilist':'arm64-v8a'}[args[1]]
                if args[:3]==('pm','list','packages'):return device.PACKAGE if installed else ''
                if args[0]=='stat':return '10001'
                if args[0]=='getenforce':return 'Enforcing'
                return ''
            with ExitStack() as stack:
                for name,replacement in [('adb',adb),('shell',shell),('enable_features',lambda out:None),
                                         ('rpc',lambda *a,**k:{'addon':{'enabled':True}}),
                                         ('running_engine',lambda:{'pid':42}),('until',lambda fn,seconds:fn()),
                                         ('read_json',lambda p:result)]:
                    stack.enter_context(patch.object(device,name,replacement))
                setup=stack.enter_context(patch.object(staging,'extra'))
                stack.enter_context(patch.object(staging,'admit_runtime'))
                report=feature.execute(args)
                self.assertEqual(report,json.loads((args.out/'FEATURE-RESULT.json').read_text()))
                self.assertEqual(report['shutdown'],{'status':'NOT_RUN','required_for_feature_result':False})
                self.assertFalse(report['release_accepted']);self.assertFalse(report['final_lock'])
                self.assertFalse(report['app_termination_requested_by_harness'])
                return report,calls,setup.call_count

    def test_selected_feature_success_does_not_close_or_reopen(self):
        for case in feature.CASES:
            with self.subTest(case=case):
                report,calls,setup_count=self.simulate(case)
                self.assertTrue(report['passed']);self.assertEqual(setup_count,1)
                self.assertEqual(sum(c[:2]==('am','start') for c in calls),1)

    def test_failed_or_wrong_family_result_cannot_pass(self):
        for result in [dict(passed=False,pid=42,selected_mode='feature-multiimage',selected_features=['multiimage']),
                       dict(passed=True,pid=42,selected_mode='safe',selected_features=['navigation']),
                       dict(passed=True,pid=43,selected_mode='feature-multiimage',selected_features=['multiimage'])]:
            with self.subTest(result=result):self.assertFalse(self.simulate(result=result)[0]['passed'])

    def test_wrong_platform_or_existing_profile_never_install(self):
        for options in ({'sdk':'36'},{'installed':True}):
            report,calls,setup_count=self.simulate(**options)
            self.assertFalse(report['passed']);self.assertEqual(setup_count,0)
            self.assertFalse(any(c[0]=='install' for c in calls))

    def test_feature_fixture_never_loads_persistence_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);stage=root/'stage';fixture=stage/staging.FUTURE
            (fixture/'resources').mkdir(parents=True)
            (fixture/'resources/settings.xml').write_text('<settings default="safe"/>')
            apk=root/'fixture.apk'
            with ZipFile(apk,'w') as archive:archive.writestr('test.png',b'fixture'*30)
            report={};args=NS(mode='feature-multiimage',feature_only=True,out=root,apk=apk)
            # No provider archive or retained shutdown service exists here.
            with patch.object(staging,'ROOT',root),patch.object(staging,'OLD',root/'absent'),patch.dict(staging.__dict__,runtime={'probe':NS(adb=lambda *a:None,PROFILE='/disposable')}):
                staging.extra(stage,args,report)
            tree=ast.parse((fixture/'service.py').read_text())
            run=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run']
            self.assertEqual(len(run),1)
            self.assertEqual(ast.literal_eval(run[0].keywords[0].value),['multiimage'])
            self.assertFalse((fixture/'android_close_trace.py').exists())
            self.assertIsNone(report['future_provider_fixture_only'])

class RuntimeRouting(unittest.TestCase):
    def exercise(self,features):
        with tempfile.TemporaryDirectory() as temporary,ExitStack() as stack:
            root=Path(temporary);log=root/'kodi.log';log.write_text('')
            rows={k*64:dict(key=k*64,source='plugin://original/'+k,media='movie' if k=='b' else 'tv') for k in 'abcd'}
            data={'later':rows,'items':{'f'*64:{'source':'plugin://original/f'}},'watched':{'w':True},'watchlist':{'w':True}}
            (root/'continue-watching.json').write_text(json.dumps(data))
            (root/'navigation-start-cycle.json').write_text('{}')
            calls=[];home=NS(getProperty=lambda name:'1')
            class Dialog:
                def __init__(self,*args):calls.append('image-dialog')
                def show(self):log.write_text('INFINITY_MULTIIMAGE_BEGIN token=1 job=2 control=941;\nINFINITY_MULTIIMAGE_RETIRED token=1 job=2 control=941; unchanged_receipt=true\n')
                def close(self):calls.append('image-dialog-close')
            fake_xbmc=NS(getSkinDir=lambda:'skin.infinity.diggz',executebuiltin=lambda *a:None,Monitor=lambda:NS(abortRequested=lambda:False))
            fake_addon=NS(Addon=lambda *a:NS(getAddonInfo=lambda k:{'path':str(root),'profile':str(root),'version':'0.3.5.31'}[k]))
            providers=[{'id':x} for x in ('plugin.video.pov','plugin.video.umbrella','plugin.video.seren')]
            nav=NS(available=lambda media:(providers,None),resolve=lambda entry,provider,*a:'plugin://'+provider['id']+'/'+entry['key'],Unavailable=RuntimeError)
            modules={'xbmc':fake_xbmc,'xbmcaddon':fake_addon,'xbmcgui':NS(Window=lambda *a:home,WindowXMLDialog=Dialog),
                'xbmcvfs':NS(translatePath=lambda p:str(log) if p=='special://logpath/kodi.log' else p),
                'saved_navigation':nav,'resume_hub':NS(load_view=lambda p:data,entries=lambda *a:rows.values()),'infinity_search':NS()}
            stack.enter_context(patch.dict(sys.modules,modules))
            spec=importlib.util.spec_from_file_location('policy_runtime_checks',HERE/'android_runtime_checks.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.__file__=str(root/'android_runtime_checks.py')
            (root/'EXPECTED-COMPONENTS.json').write_text(json.dumps({name:'0.3.5.31' for name in ('script.infinity.commandcenter','script.infinity.uirepair','script.infinity.watchedbridge')}))
            def rpc(method,params):
                if method=='Settings.GetSettingValue':return {'value':2}
                calls.append(method+':'+params.get('addonid',''))
                if features==['multiimage']:raise AssertionError('Unselected navigation RPC')
                if method=='Addons.GetAddonDetails':return {'addon':{'enabled':True}}
                if method=='Files.GetDirectory':
                    key='f' if 'bucket=continue' in params['directory'] else 'b'
                    return {'files':[{'file':'plugin://original/'+key}]}
                raise AssertionError(method)
            stack.enter_context(patch.object(module,'rpc',rpc))
            stack.enter_context(patch.object(module,'until',lambda fn,*a:fn() or (_ for _ in ()).throw(AssertionError('Incomplete observation'))))
            setup=stack.enter_context(patch.object(module,'complete_first_use'))
            stack.enter_context(patch.object(module,'first_provider_home',return_value=[{}]))
            stack.enter_context(patch.object(module,'verify_open_folder',return_value={'count':1}))
            module.run(root,'cycle','provider-pov',features)
            return json.loads((root/'navigation-ready-cycle.json').read_text()),calls,setup

    def test_navigation_excludes_multiimage_and_unselected_provider_checks(self):
        report,calls,setup=self.exercise(['navigation'])
        self.assertTrue(report['passed']);self.assertNotIn('image-dialog',calls)
        self.assertNotIn('multiimage_control_exercised',report)
        self.assertEqual(setup.call_args.kwargs['providers'],['plugin.video.pov','plugin.video.future.navigation.7fa29'])
        self.assertFalse(any('seren' in c or 'umbrella' in c for c in calls))

    def test_multiimage_excludes_navigation(self):
        report,calls,setup=self.exercise(['multiimage'])
        self.assertTrue(report['passed']);self.assertTrue(report['multiimage_control_exercised'])
        self.assertEqual(report['cases'],[]);self.assertFalse(setup.called)
        self.assertEqual(calls,['image-dialog','image-dialog-close'])

    def test_legacy_explicit_shutdown_scenario_retains_both_features(self):
        report,calls,setup=self.exercise(None)
        self.assertTrue(report['passed']);self.assertTrue(report['multiimage_control_exercised'])
        self.assertTrue(report['cases']);self.assertIsNone(setup.call_args.kwargs['providers'])

if __name__=='__main__':unittest.main(verbosity=2)
