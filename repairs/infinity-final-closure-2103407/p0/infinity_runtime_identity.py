"""Read-only Kodi-resolved inventory, including authenticated consolidated code."""
import hashlib, importlib.util, json, os, time
from pathlib import Path
import xbmc, xbmcaddon, xbmcgui, xbmcvfs

CC = 'script.infinity.commandcenter'
IDS = (CC, 'script.infinity.uirepair', 'script.infinity.watchedbridge',
       'skin.infinity.diggz', 'script.infinity.rails', 'script.kodihealthcenter',
       'service.infinity.compat', 'plugin.infinity.latestreleases')
BOOTSTRAP_SHA = '759e60439fae0b1bf0f8a2ff6895209ac848101b9544ac6c0e297b9c73df1267'
MIGRATED = {
    'script.infinity.uirepair': ('uirepair', ('home_option_b.py', 'latest_identity.py', 'runtime.py', 'controller_access.py', 'plugin.py')),
    'script.infinity.watchedbridge': ('watchedbridge', ('controller.py',)),
    'script.infinity.rails': ('rails', ('runtime.py', 'catalog.py', 'store.py', 'dialog.py', 'input_status.py')),
}

def _root(aid):
    addon = xbmcaddon.Addon(aid)
    raw = addon.getAddonInfo('path')
    return addon, raw, Path(xbmcvfs.translatePath(raw)).absolute()

def _signed_inventory():
    addon, _, root = _root(CC)
    path = root / 'module_contract.py'
    if path.is_symlink() or path.resolve() != path or path.stat().st_size > 4194304:
        raise RuntimeError('Unverified module bootstrap path')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BOOTSTRAP_SHA:
        raise RuntimeError('Unverified module bootstrap source')
    # load_contract performs the existing native original-signature/source
    # verification. It does not install import guards, writers or services.
    spec = importlib.util.spec_from_loader('_infinity_health_inventory', loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    contract = module.load_contract(root, addon.getAddonInfo('version'))
    return contract

def collect():
    result = dict(schema=2, pid=os.getpid(), epoch_ms=int(time.time()*1000),
                  runtime_resolved=True, read_only=True, proves_physical_acceptance=False, addons=[])
    contract = None
    try:
        contract = _signed_inventory()
        result['module_signature'] = dict(state='NATIVE_ORIGINAL_SIGNATURE_VERIFIED',
            manifest_sha256=contract.identity.manifest_sha256,
            package_version=contract.identity.package_version, protocol_api=contract.identity.protocol_api)
    except Exception as error:
        result['module_signature'] = dict(state='UNVERIFIED', error_type=type(error).__name__)
    for aid in IDS:
        row = {'id': aid}; result['addons'].append(row)
        try:
            addon, raw_root, root = _root(aid)
            row.update(version=addon.getAddonInfo('version'), resolved_directory=raw_root,
                enabled=xbmc.getCondVisibility('System.AddonIsEnabled('+aid+')'), files={}, state='OBSERVED')
            names = {'addon.xml': (root/'addon.xml', aid+'/addon.xml')}
            leaves = {
                CC: ('checkpoint_runtime.py','common.py','context.py','default.py','experience.py',
                     'infinity_search.py','infinity_settings.py','infinity_trakt.py','persistence_participant.py',
                     'plugin.py','resources/settings.xml','resume_hub.py','runtime_visibility.py','service.py',
                     'skin_upgrade.py','view_mode.py'),
                'plugin.infinity.latestreleases': ('default.py','identity.py'),
                'script.kodihealthcenter': ('default.py','service.py','khc_lifecycle.py','khc_diagnostics.py','infinity_runtime_identity.py'),
                'skin.infinity.diggz': ('unified/Home.xml','Infinity-Protected-Manifest.json','infinity-skin.json'),
                'service.infinity.compat': ('runtime_service.py','compat_runtime.py','checkpoint_runtime.py','resources/settings.xml'),
                # Genuine installed extension-point shims/resources remain here.
                'script.infinity.uirepair': ('default.py','plugin.py',
                    'resources/skins/Default/1080i/InfinityHomeOptionB.xml'),
                'script.infinity.watchedbridge': ('default.py','context.py','PROVIDER-CONTRACTS.json'),
                'script.infinity.rails': ('default.py','plugin.py','context_add.py'),
            }.get(aid, ())
            for leaf in leaves:
                names[leaf] = (root/leaf, aid+'/'+leaf)
            if aid in MIGRATED:
                family, members = MIGRATED[aid]
                _, _, owner = _root(CC)
                row['implementation_owner'] = CC
                if contract:
                    prefix = CC+'/infinity_modules/'+family+'/'
                    members = tuple(relative[len(prefix):] for relative in contract.files if relative.startswith(prefix))
                for leaf in members:
                    relative = CC+'/infinity_modules/'+family+'/'+leaf
                    names['infinity_modules/'+family+'/'+leaf] = (owner/'infinity_modules'/family/leaf, relative)
            for logical, (path, relative) in sorted(names.items()):
                if path.is_symlink() or path.resolve() != path or not path.is_file() or path.stat().st_size > 4194304:
                    row['files'][logical] = {'state': 'MISSING_OR_UNVERIFIED'}; continue
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                file = {'sha256': digest, 'resolved_path': str(path)}
                if relative.split('/')[0] in (CC,'script.infinity.uirepair','script.infinity.watchedbridge','script.infinity.rails'):
                    expected = contract.files.get(relative) if contract else None
                    file.update(state='AUTHENTICATED' if expected == digest else 'UNVERIFIED',
                                authenticated_source=relative, expected_sha256=expected)
                row['files'][logical] = file
            dependencies = __import__('xml.etree.ElementTree',fromlist=['fromstring']).fromstring((root/'addon.xml').read_bytes())
            row['dependencies'] = [dict(e.attrib) for e in dependencies.findall('requires/import')]
        except Exception as error:
            row.update(state='UNVERIFIED', error_type=type(error).__name__)
    try:
        owner = xbmcaddon.Addon(CC); home = xbmcgui.Window(10000)
        result['settings'] = {key: owner.getSetting(key) for key in ('ambient_home','motion_mode')}
        result['home'] = {key: home.getProperty(key) for key in ('Infinity.AmbientHome.Mode','Infinity.MotionModeUser',
            'Infinity.MotionModeEffective','Infinity.EffectiveViewMode','Infinity.SystemTheme','Infinity.NativeSystemTheme')}
    except Exception as error:
        result['settings_error'] = type(error).__name__
    return result
