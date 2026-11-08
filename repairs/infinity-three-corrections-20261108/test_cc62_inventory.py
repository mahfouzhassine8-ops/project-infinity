"""Exact shipped CC62 inventory versus the already-approved two-file overlay.

Uses pinned public provider sources without importing or executing them.
SDK adapters supply only add-on paths/enabled state. No native Search is run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CC = 'script.infinity.commandcenter'
IDS = ('plugin.video.umbrella', 'plugin.video.pov')


def worker(cc, fixtures):
    class Addon:
        def __init__(self, aid=CC):
            self.aid = aid
        def getAddonInfo(self, key):
            path = cc if self.aid == CC else fixtures / self.aid
            if self.aid not in (CC, *IDS):
                raise RuntimeError('No installed dependency is assumed by this host adapter')
            return dict(path=str(path), icon='', id=self.aid, version='fixture', profile=str(fixtures / 'unused-profile')).get(key, '')
    xbmc = types.ModuleType('xbmc')
    xbmc.Monitor = type('Monitor', (), {})
    xbmc.LOGINFO, xbmc.LOGWARNING, xbmc.LOGERROR, xbmc.LOGDEBUG = 1, 2, 3, 0
    xbmc.getCondVisibility = lambda _: False
    addon = types.ModuleType('xbmcaddon')
    addon.Addon = Addon
    vfs = types.ModuleType('xbmcvfs')
    vfs.translatePath = lambda value: value
    for name, module in [('xbmc', xbmc), ('xbmcaddon', addon), ('xbmcvfs', vfs),
                         ('xbmcgui', types.ModuleType('xbmcgui')),
                         ('xbmcplugin', types.ModuleType('xbmcplugin'))]:
        sys.modules[name] = module
    sys.path.insert(0, str(cc))
    import provider_inventory as inventory
    specs, digest = inventory._contracts()
    rows = [dict(addonid=aid, enabled=True, name=aid, version='public-source-fixture') for aid in IDS]
    entries, _ = inventory._scan(rows, specs, digest, {})
    print(json.dumps({e['id']: dict(status=e['status'], operations=sorted('/'.join(p) for p in e['operations'])) for e in entries}))


def run(cc, fixtures, out):
    assert hashlib.sha256((cc / 'INFINITY-MODULES.v1').read_bytes()).hexdigest() == '166c994d66503cfe3b3c70b7c4d4a10ce9778cea5e01a9838c9ce83a1a4b34bc'
    assert hashlib.sha256((cc / 'provider_inventory.py').read_bytes()).hexdigest() == 'd9b51790c737f9cfa013806c6bf287ab37bd17cb798644ab0aaaf31ea37ae3e2'
    assert not (cc / 'native_search_compatibility.py').exists()
    results = {}
    with tempfile.TemporaryDirectory(prefix='cc62-inventory-') as temporary:
        patched = Path(temporary) / CC
        shutil.copytree(cc, patched)
        overlay = ROOT / 'repairs/infinity-only-performance-2103425/overlay' / CC
        for name in ('provider_inventory.py', 'native_search_compatibility.py'):
            raw = (overlay / name).read_bytes()
            approved = subprocess.check_output(['git', 'show', '16af10e42265f9f5155efd54849b25871c50aa0f:' + str((overlay / name).relative_to(ROOT))])
            assert raw == approved
            (patched / name).write_bytes(raw)
        for label, source in [('shipped_CC62', cc), ('approved_overlay_CC62', patched)]:
            invocation = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', '--cc', str(source), '--fixtures', str(fixtures)], capture_output=True, text=True)
            assert invocation.returncode == 0, invocation.stderr
            results[label] = json.loads(invocation.stdout)
        assert all(results['shipped_CC62'][aid]['status'] == 'unsupported' for aid in IDS)
        assert all(results['approved_overlay_CC62'][aid] == dict(status='verified', operations=['movie/search', 'tv/search']) for aid in IDS)
    out.mkdir(parents=True, exist_ok=True)
    report = dict(status='PASS_SHIPPED_CC62_REJECTION_AND_APPROVED_SEARCH_ONLY_ADMISSION', results=results,
                  provider_code_executed=False, provider_code_modified=False, APK_built=False,
                  existing_host_matrix_reused=42435806833, installed_Fold_hashes='NOT_COLLECTED',
                  interpretation='Explains the message for the shipped CC62 plus these pinned providers; actual Fold cause requires installed source identities',
                  Android_native_Search_execution=False)
    (out / 'CC62-INVENTORY-EXPLANATION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cc', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker(args.cc.resolve(), args.fixtures.resolve())
    else:
        run(args.cc.resolve(), args.fixtures.resolve(), args.out.resolve())
