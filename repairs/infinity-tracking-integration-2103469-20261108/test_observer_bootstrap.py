"""Python bootstrap controls with native ABI doubles, never Android acceptance."""
import ctypes
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'tracking_android_observer.py'
MODULES = Path('/workspace/scratch/tracking69-modules-42555855742/pair/2103470/modules')
CC = 'script.infinity.commandcenter'

def require(ok, message):
    if not ok: raise RuntimeError(message)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def child(case):
    root = MODULES / CC
    manifest = root / 'INFINITY-MODULES.v1'
    expected = dict(cc_version='0.3.5.68',manifest_sha256=sha(manifest),module_sources={},provider_sources={})
    for line in manifest.read_text().splitlines():
        row=line.split('\t')
        if row[0]=='file': expected['module_sources'][row[2]]=row[1]
    require(len(expected['module_sources'])==80,'Full real signed fixture required')
    calls=[]
    def native(encoded, version, version_cap, digest, digest_cap, protocol):
        calls.append('existing_native_ABI_double')
        require(encoded.decode()==str(root),'Exact installed root')
        require(version_cap==49 and digest_cap==65,'Exact original buffer capacities')
        if case=='native_reject': return 0
        version.value=b'0.3.5.68';digest.value=sha(manifest).encode()
        protocol._obj.value=2 if case=='wrong_protocol' else 1
        return 1
    def library(path,mode):
        require(path.endswith('/libkodi.so') and mode & os.RTLD_NOLOAD and mode & os.RTLD_NOW,'Only already loaded original engine')
        return SimpleNamespace(InfinityCommandCenterIdentityV1=native)
    xbmc=ModuleType('xbmc');xbmc.Player=object
    mods=dict(xbmc=xbmc,xbmcaddon=ModuleType('xbmcaddon'),xbmcgui=ModuleType('xbmcgui'),xbmcvfs=ModuleType('xbmcvfs'))
    with tempfile.TemporaryDirectory() as temporary, patch.dict(sys.modules,mods), patch.dict(os.environ,{'KODI_ANDROID_LIBS':'/host-native-ABI-double'}), patch.object(ctypes,'CDLL',library):
        tmp=Path(temporary)
        if case=='wrong_manifest': expected['manifest_sha256']='0'*64
        if case=='wrong_map': expected['module_sources'][next(iter(expected['module_sources']))]='0'*64
        (tmp/'expected.json').write_text(json.dumps(expected))
        ns=dict(__name__='host_bootstrap_control',__file__=str(tmp/'observer.py'))
        exec(compile(SOURCE.read_text(),str(SOURCE),'exec',optimize=1),ns)
        if case=='foreign_cache':
            foreign=ModuleType('module_contract');foreign.__file__='/foreign/bootstrap.py';sys.modules['module_contract']=foreign
        failures=dict(native_reject='NATIVE_ORIGINAL_RSA_FULL80_IDENTITY_REQUIRED',wrong_protocol='EXPECTED_NATIVE_VERSION_PROTOCOL_MANIFEST_REQUIRED',wrong_manifest='EXPECTED_NATIVE_VERSION_PROTOCOL_MANIFEST_REQUIRED',wrong_map='EXACT_EXPECTED_AUTHENTICATED80_MAP_REQUIRED',foreign_cache='CONFLICTING_BOOTSTRAP_CACHE_PATH_REJECTED')
        if case in failures:
            try: ns['authenticated_bootstrap'](root,'0.3.5.68')
            except RuntimeError as error: require(str(error).startswith(failures[case]),case+': '+str(error))
            else: raise RuntimeError('Bootstrap guard accepted '+case)
            require('controller_access' not in sys.modules,'Helper executed before rejected bootstrap')
            if case=='foreign_cache': require(sys.modules['module_contract'] is foreign,'Foreign module was removed/replaced')
            else: require('module_contract' not in sys.modules,'First-party Python executed before rejected native/map proof')
        else:
            contract=ns['authenticated_bootstrap'](root,'0.3.5.68')
            module=sys.modules['module_contract']
            require(module.__file__==str(root/'module_contract.py'),'Original installed source bootstrap')
            require(contract.identity.manifest_sha256==sha(manifest),'Correct original contract identity')
            require('controller_access' not in sys.modules,'Helper preceded guard activation')
            sys.path.insert(0,str(root/'infinity_modules/uirepair'))
            helper=importlib.import_module('controller_access')
            require(isinstance(helper.__loader__,module._SourceLoader),'Original authenticated loader owns helper')
            require(helper.__loader__.contract is contract,'Helper uses original active contract')
            require(ns['BOOTSTRAP_PHASES'][-1]['phase']=='ORIGINAL_IMPORT_GUARD_ACTIVE_BEFORE_CONTROLLER_IMPORT','Phase order')
            require(calls and calls[0]=='existing_native_ABI_double','Native API first')
    print(json.dumps(dict(case=case,status='PASS_HOST_BOOTSTRAP_CONTROL_ONLY',compile_optimization=1,native_ABI_double=True,real_original_source_loader_used=case=='valid')))

def run():
    rows=[]
    for case in ('valid','native_reject','wrong_protocol','wrong_manifest','wrong_map','foreign_cache'):
        result=subprocess.run([sys.executable,'-O',str(Path(__file__).resolve()),'--case',case],check=True,capture_output=True,text=True,timeout=30)
        rows.append(json.loads(result.stdout))
    report=dict(status='PASS_SIX_OPTIMIZED_BOOTSTRAP_ORDER_REFUSAL_CONTROLS_ONLY',cases=rows,
        observer_sha256=sha(SOURCE),test_sha256=sha(Path(__file__)),selection_sha256=sha(HERE/'OBSERVER-BOOTSTRAP-TEST-SELECTION.json'),
        actual_Android_native_authentication=False,actual_Kodi_or_provider_execution=False,previous40_13_17_5_6_rerun=False)
    (HERE/'OBSERVER-BOOTSTRAP-HOST.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'])

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--case': child(sys.argv[2])
    else: run()
