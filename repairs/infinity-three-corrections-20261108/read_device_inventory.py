"""Read-only report from an already authorized ADB connection.

No installation, app launch/stop, settings/database reads, phone writes,
permission changes or remote provider execution. This does not clear a release.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--serial')
    parser.add_argument('--out', type=Path, default=Path('INFINITY-INSTALLED-INVENTORY.json'))
    parser.add_argument('--sources-out', type=Path,
                        help='New folder on this computer for selected code/manifests only; no full add-on/profile export')
    args = parser.parse_args()
    if args.sources_out and args.sources_out.exists():
        parser.error('--sources-out must name a new folder on this computer')
    source_copies = {}
    command = [args.adb] + (['-s', args.serial] if args.serial else [])
    def call(*arguments):
        result = subprocess.run(command + list(arguments), capture_output=True, timeout=60)
        if result.returncode:
            raise RuntimeError('ADB read failed; do not change permissions or bypass access controls')
        return result.stdout
    package = call('shell', 'dumpsys', 'package', 'com.projectinfinity.kodi').decode()
    versions = sorted(set(re.findall(r'\bversionCode=(\d+)\b', package)))
    if len(versions) != 1:
        raise RuntimeError('Could not identify one installed Infinity APK version code')
    apk_identity = {}
    try:
        installed = call('shell', 'pm', 'path', 'com.projectinfinity.kodi').decode().splitlines()
        if len(installed) != 1 or not installed[0].startswith('package:'):
            raise RuntimeError('Expected one installed combined APK')
        apk_path = installed[0][len('package:'):]
        if not re.fullmatch(r'/data/app/[A-Za-z0-9/._~+=-]+\.apk', apk_path):
            raise RuntimeError('Unrecognized installed APK path')
        apk_hash = call('exec-out', 'sha256sum', apk_path).decode().split()[0]
        if not re.fullmatch('[0-9a-f]{64}', apk_hash):
            raise RuntimeError('Invalid APK hash response')
        apk_identity = dict(sha256=apk_hash)
    except RuntimeError:
        apk_identity = dict(status='APK_HASH_UNREADABLE_NO_BYPASS_ATTEMPTED')
    root = '/sdcard/Android/data/com.projectinfinity.kodi/files/.kodi/addons/'
    cc = 'script.infinity.commandcenter/'
    def read(relative, limit):
        raw = call('exec-out', 'head', '-c', str(limit + 1), root + relative)
        if len(raw) > limit:
            raise RuntimeError('Owned metadata exceeds its size bound')
        if args.sources_out:
            source_copies[relative] = raw
        return raw
    manifest = read(cc + 'INFINITY-MODULES.v1', 131072)
    signature = read(cc + 'INFINITY-MODULES.v1.sig', 512)
    owned = ('script.infinity.commandcenter', 'script.infinity.rails',
             'script.infinity.uirepair', 'script.infinity.watchedbridge')
    names = []
    for line in manifest.decode('ascii').splitlines():
        fields = line.split('\t')
        if fields[0] != 'file':
            continue
        if (len(fields) != 3 or not re.fullmatch('[0-9a-f]{64}', fields[1]) or
                not re.fullmatch(r'[A-Za-z0-9/._-]+', fields[2]) or
                fields[2].split('/')[0] not in owned or
                Path(fields[2]).suffix not in ('.py', '.xml', '.json', '.v1', '.po') or
                any(p.casefold() in ('addon_data', 'userdata', 'database', 'profile')
                    for p in fields[2].split('/')) or
                any(p in ('', '.', '..') for p in fields[2].split('/'))):
            raise RuntimeError('Invalid module record; report collection stopped')
        names.append(fields[2])
    if not 1 <= len(names) <= 256 or len(set(names)) != len(names):
        raise RuntimeError('Invalid module inventory count')
    hashes = call('exec-out', 'sha256sum', *[root + n for n in names]).decode()
    # Snapshot metadata again; do not report a mixed manifest/signature pair.
    if (manifest != read(cc + 'INFINITY-MODULES.v1', 131072) or
            signature != read(cc + 'INFINITY-MODULES.v1.sig', 512)):
        raise RuntimeError('Installed generation changed during read; no report issued')
    providers = {}
    for aid in ('plugin.video.umbrella', 'plugin.video.pov', 'script.module.tmdbhelper.sync.trakt'):
        try:
            raw = read(aid + '/addon.xml', 131072)
            providers[aid] = dict(manifest_base64=base64.b64encode(raw).decode(),
                                  manifest_sha256=hashlib.sha256(raw).hexdigest())
        except RuntimeError:
            providers[aid] = dict(status='UNREADABLE_AT_STANDARD_EXTERNAL_ADDON_PATH')
    provider_sources = {}
    for aid, names in (
            ('plugin.video.umbrella', ('umbrella.py', 'resources/lib/modules/router.py',
                                      'resources/lib/menus/movies.py', 'resources/lib/menus/tvshows.py')),
            ('plugin.video.pov', ('resources/lib/router.py', 'resources/lib/modules/entry.py',
                                 'resources/lib/menus/movies.py', 'resources/lib/menus/tvshows.py'))):
        provider_sources[aid] = {}
        for relative in names:
            try:
                raw = read(aid + '/' + relative, 512 * 1024)
                provider_sources[aid][relative] = hashlib.sha256(raw).hexdigest()
            except RuntimeError:
                provider_sources[aid][relative] = 'UNREADABLE'
    trakt_sources = {}
    for relative in (
            'resources/script.py', 'resources/settings.xml',
            'resources/language/resource.language.en_gb/strings.po',
            'resources/lib/tmdbhelper_sync_trakt/account.py',
            'resources/lib/tmdbhelper_sync_trakt/api/api.py',
            'resources/lib/tmdbhelper_sync_trakt/api/authenticator.py',
            'resources/lib/tmdbhelper_sync_trakt/api/token.py',
            'resources/lib/tmdbhelper_sync_trakt/api/recovery.py'):
        try:
            raw = read('script.module.tmdbhelper.sync.trakt/' + relative, 512 * 1024)
            trakt_sources[relative] = hashlib.sha256(raw).hexdigest()
        except RuntimeError:
            trakt_sources[relative] = 'UNREADABLE'
    inspection_sources = {}
    for aid, names in (
            ('script.infinity.commandcenter', ('addon.xml', 'provider_inventory.py', 'native_search_compatibility.py')),
            ('script.kodihealthcenter', ('addon.xml', 'default.py', 'khc_exports.py', 'khc_safety.py'))):
        inspection_sources[aid] = {}
        for relative in names:
            try:
                raw = read(aid + '/' + relative, 512 * 1024)
                inspection_sources[aid][relative] = hashlib.sha256(raw).hexdigest()
            except RuntimeError:
                inspection_sources[aid][relative] = 'UNREADABLE'
    report = dict(status='READ_ONLY_COLLECTION_NOT_INSTALLATION_CLEARANCE',
                  apk_version_code=int(versions[0]),
                  installed_apk_identity=apk_identity,
                  module_manifest_base64=base64.b64encode(manifest).decode(),
                  module_signature_base64=base64.b64encode(signature).decode(),
                  module_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
                  installed_source_hash_output=hashes, providers=providers,
                  trakt_source_hashes=trakt_sources,
                  provider_source_hashes=provider_sources,
                  inspection_source_hashes=inspection_sources,
                  phone_writes=False, settings_or_database_reads=False,
                  Android_functionality_verified=False)
    if args.sources_out:
        args.sources_out.mkdir(parents=True, exist_ok=False)
        for relative, raw in source_copies.items():
            destination = args.sources_out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        report['source_copies_on_computer'] = {
            relative: hashlib.sha256(raw).hexdigest()
            for relative, raw in sorted(source_copies.items())}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print('Read-only inventory written to ' + str(args.out))


if __name__ == '__main__':
    main()
