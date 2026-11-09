"""Execute actual observer guards compiled with optimize=1, using host SDK doubles.

This does not authenticate a native module or execute a player/provider. Original
public-key and actual module verification evidence remains separate.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'tracking_android_observer.py'
ROOT = Path('/workspace/scratch/tracking69-modules-42555855742/pair/2103470/modules')
CC = 'script.infinity.commandcenter'

def require(ok, label):
    if not ok: raise RuntimeError(label)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    raw = SOURCE.read_text()
    require(not any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(raw))), 'No strippable observer assertions')
    manifest = ROOT / CC / 'INFINITY-MODULES.v1'
    expected = dict(manifest_sha256=sha(manifest), module_sources={}, provider_sources={})
    for line in manifest.read_text().splitlines():
        fields = line.split('\t')
        if fields[0] == 'file': expected['module_sources'][fields[2]] = sha(ROOT / fields[2])
    require(len(expected['module_sources']) == 80, 'Full real signed fixture input required')
    xbmc = ModuleType('xbmc');xbmc.Player = object
    labels = {}
    xbmc.getInfoLabel = lambda name: labels.get(name, '')
    xbmc.executebuiltin = lambda *args: None
    def forbidden_rpc(*args): raise RuntimeError('HOST_CONTROL_REACHED_FORBIDDEN_CLICK')
    xbmc.executeJSONRPC = forbidden_rpc
    xbmc.getSkinDir = lambda: 'skin.infinity.diggz'
    addon = ModuleType('xbmcaddon')
    addon.Addon = lambda aid: SimpleNamespace(getAddonInfo=lambda field: str(ROOT / CC) if field == 'path' else '0.3.5.68')
    vfs = ModuleType('xbmcvfs');vfs.translatePath = lambda path: path
    contract = ModuleType('module_contract')
    contract.installed_identity = lambda *args: SimpleNamespace(manifest_sha256=sha(manifest), package_version='0.3.5.68')
    modules = dict(xbmc=xbmc, xbmcaddon=addon, xbmcgui=ModuleType('xbmcgui'), xbmcvfs=vfs, module_contract=contract)
    rows = []
    with tempfile.TemporaryDirectory() as temporary, patch.dict(sys.modules, modules):
        tmp = Path(temporary)
        ns = dict(__name__='host_optimized_guard_control', __file__=str(tmp / 'observer.py'))
        exec(compile(raw, str(SOURCE), 'exec', optimize=1), ns)
        ns['controller'] = lambda: SimpleNamespace(__file__='host-controller-read-only-double')
        def set_expected(value): (tmp / 'expected.json').write_text(json.dumps(value))
        set_expected(expected)
        identity = ns['identity']()
        require(identity['module_files'] == expected['module_sources'], 'Positive validator control failed')
        require(identity['Python_optimization'] == 1, 'Run host control itself with python -O')
        rows.append(dict(case='exact_map_host_control', status='PASS_OPTIMIZED_PYTHON_VALIDATOR_ONLY'))
        def refusal(name, label, fn):
            try: fn()
            except RuntimeError as error: require(str(error).startswith(label), name + ': wrong refusal ' + str(error))
            else: raise RuntimeError(name + ': disabled guard accepted control')
            rows.append(dict(case=name, status='REFUSED_UNDER_OPTIMIZE1_AS_REQUIRED'))
        bad = copy.deepcopy(expected);bad['manifest_sha256'] = '0' * 64;set_expected(bad)
        refusal('wrong_manifest', 'EXACT_NATIVE_FIXTURE_MANIFEST_REQUIRED', ns['identity'])
        bad = copy.deepcopy(expected);bad['module_sources'][next(iter(bad['module_sources']))] = '0' * 64;set_expected(bad)
        refusal('wrong_source_map', 'EXACT_AUTHENTICATED80_SOURCE_SET_REQUIRED', ns['identity'])
        request = dict(action='click', control=50, index=0, file='plugin://plugin.video.watchnixtoons2/?action=host-control', label='Host guard control')
        labels.update({'Container(50).ListItem.FileNameAndPath':'wrong-path','Container(50).ListItem.Label':request['label']})
        refusal('wrong_UI_path_before_click', 'LIVE_NATIVE_SELECTED_PATH_REQUIRED', lambda: ns['action'](request))
        labels.update({'Container(50).ListItem.FileNameAndPath':request['file'],'Container(50).ListItem.Label':'wrong-label'})
        refusal('wrong_UI_label_before_click', 'LIVE_NATIVE_SELECTED_LABEL_REQUIRED', lambda: ns['action'](request))
        bad_request = dict(request, control=999)
        refusal('invalid_control_before_input', 'EXACT_SELECTED_NATIVE_CONTROL_AND_INDEX_REQUIRED', lambda: ns['action'](bad_request))
    report = dict(status='PASS_SIX_OPTIMIZE1_OBSERVER_VALIDATOR_CONTROLS_ONLY', cases=rows,
        observer_sha256=sha(SOURCE), test_sha256=sha(Path(__file__)), selection_sha256=sha(HERE/'OBSERVER-OPTIMIZATION-TEST-SELECTION.json'),
        target_compile_optimization=1, host_python_optimization=sys.flags.optimize, actual_Kodi_SDK_execution=False,
        native_module_authentication_acceptance=False, player_or_provider_acceptance=False,
        previous40_13_17_5_tests_rerun=False)
    (HERE/'OBSERVER-OPTIMIZATION-HOST.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'])

if __name__ == '__main__': run()
