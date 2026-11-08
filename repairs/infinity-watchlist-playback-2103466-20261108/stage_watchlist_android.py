"""Stage only the approved Watchlist fixture. No emulator/app execution."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from android_watchlist_common import HERE, CC, QA, retained, checked_observer, sha, producer_pins


def safe_extract(z, target, expected=None):
    for item in z.infolist():
        parts = Path(item.filename).parts
        if item.filename.startswith('/') or '\\' in item.filename or '..' in parts or (item.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Unsafe fixture archive member')
        if expected and parts[0] != expected:
            raise ValueError('Unexpected addon root')
    z.extractall(target)


def seed():
    # Execute only the unchanged pure hub identity functions, not tests or a writer.
    names = {'verified_ids', 'media_identity', 'show_identity', 'identity_key', 'episode_number', '_dict'}
    tree = ast.parse((HERE / 'overlay' / CC / 'resume_hub.py').read_text())
    namespace = dict(re=re, hashlib=hashlib)
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'actual-hub-pure-identities', 'exec'), namespace)
    rows = []
    for title, media, ids, kind, route in (
        ('The Matrix', 'movie', {'tmdb': '603'}, 'movie', 'plugin://plugin.video.pov/?mode=play_media&mediatype=movie&tmdb_id=603'),
        ('Breaking Bad', 'tv', {'tmdb': '1396'}, 'tvshow', 'plugin://plugin.video.pov/?mode=build_season_list&tmdb_id=1396')):
        identity = namespace['media_identity']('movie', ids) if media == 'movie' else namespace['show_identity'](kind, ids)
        key = namespace['identity_key'](identity)
        rows.append(dict(key=key, title=title, media=media, identity=identity, source=route, stable_source=route,
                         season=-1, episode=-1, position=0, duration=0, added_at=1, updated=1))
    return dict(schema=2, revision=1, items={}, watched={}, watchlist={r['key']: r for r in rows},
                sources={}, collection={}, ratings={}, lists={}, later={}, resume_hidden={})


def stage(baseline, candidate, recovery, signed_pair, owner_export, sdk, out, port):
    if out.exists(): raise ValueError('Fresh fixture directory required')
    out.mkdir(parents=True)
    pair = json.loads(signed_pair.read_text())
    for version, apk in ((2103466, baseline), (2103468, candidate), (2103469, recovery)):
        if sha(apk) != pair[str(version)]['sha256']: raise ValueError('Exact signed APK hash mismatch')
        sig = subprocess.check_output([str(sdk / 'apksigner'), 'verify', '--verbose', '--print-certs', str(apk)], text=True)
        if re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', sig) != [pair['certificate_sha256']]: raise ValueError('Original certificate mismatch')
        (out / (str(version) + '-SIGNATURE.txt')).write_text(sig)
        badging = subprocess.check_output([str(sdk / 'aapt'), 'dump', 'badging', str(apk)], text=True)
        if not re.search(r"package: name='com.projectinfinity.kodi' versionCode='"+str(version)+r"'", badging): raise ValueError('Package/version mismatch')
    with ZipFile(baseline) as base_zip, ZipFile(recovery) as recovery_zip:
        native = lambda z: {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')}
        if not native(base_zip) or native(base_zip) != native(recovery_zip): raise ValueError('Forward recovery must restore exact baseline66 native bytes')
        manifest = lambda z: {f[2]: f[1] for line in z.read('assets/addons/'+CC+'/INFINITY-MODULES.v1').decode().splitlines() if (f:=line.split('\t'))[0]=='file'}
        before, after = manifest(base_zip), manifest(recovery_zip)
        if any(after.get(name) != digest for name,digest in before.items() if name != CC+'/addon.xml'): raise ValueError('Recovery must restore baseline functional module bytes')
    addons = out / 'home/addons'; addons.mkdir(parents=True)
    with ZipFile(baseline) as z:
        for name in z.namelist():
            if name.startswith('assets/addons/') and any(name.startswith('assets/addons/' + aid + '/') for aid in (CC, 'script.infinity.rails', 'script.infinity.uirepair', 'script.infinity.watchedbridge')) and not name.endswith('/'):
                target = addons / name.removeprefix('assets/addons/'); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(z.read(name))
    # Authenticate outer owner export and the embedded full POV manifest. Never copy owner settings/data.
    if sha(owner_export) != 'e14b1e9c8441e78ce5c930dea8c7a5885053011d531df9ec51377fcb18298b65': raise ValueError('Owner source archive hash mismatch')
    umbrella_owner = {}
    with ZipFile(owner_export) as outer:
        for name in outer.namelist():
            if not name.startswith('device-exports/') or not name.endswith('.zip'): continue
            with ZipFile(io.BytesIO(outer.read(name))) as z:
                if 'KHC_ADDON_EXPORT_MANIFEST.json' in z.namelist():
                    receipt = json.loads(z.read('KHC_ADDON_EXPORT_MANIFEST.json'))
                    if receipt['addon_id'] == CC:
                        extra = CC + '/native_search_compatibility.py'
                        if extra in z.namelist() and not (addons/extra).exists():
                            target=addons/extra;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(extra))
                    if receipt['addon_id'] != 'plugin.video.pov': continue
                    if receipt['includes_saved_data'] is not False: raise ValueError('Settings/data forbidden')
                    for name, info in receipt['files'].items():
                        raw = z.read(name)
                        if len(raw) != info['size'] or hashlib.sha256(raw).hexdigest() != info['sha256']: raise ValueError('POV source pin mismatch')
                        target = addons / name
                        if not target.resolve().is_relative_to(addons.resolve()) or not name.startswith('plugin.video.pov/'): raise ValueError('POV source path mismatch')
                        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
                elif 'UMB-SEARCH-SOURCE-REPORT.json' in z.namelist():
                    receipt = json.loads(z.read('UMB-SEARCH-SOURCE-REPORT.json'))
                    for row in receipt['files']:
                        raw = z.read('plugin.video.umbrella/' + row['path'])
                        if hashlib.sha256(raw).hexdigest() != row['sha256']: raise ValueError('Owner U source mismatch')
                        umbrella_owner[row['path']] = raw
    pins = json.loads(retained('repairs/infinity-three-corrections-20261108/ANDROID-INPUT-PINS.json'))
    if len(pins['archives']) != 12: raise ValueError('Retain exact12 dependency archives')
    for row in pins['archives']:
        with urllib.request.urlopen(row['url'], timeout=90) as response: raw = response.read()
        if hashlib.sha256(raw).hexdigest() != row['sha256']: raise ValueError('Dependency archive mismatch')
        with ZipFile(io.BytesIO(raw)) as z: safe_extract(z, addons, row['addon'])
    if len(umbrella_owner) != 5: raise ValueError('Five actual U emitter/menu samples required')
    for name, raw in umbrella_owner.items():
        if raw.decode().splitlines() != (addons / 'plugin.video.umbrella' / name).read_text().splitlines(): raise ValueError('Public U differs from captured owner source')
    for provider, contract in producer_pins().items():
        for name, wanted in contract['files'].items():
            if sha(addons / provider / name) != wanted: raise ValueError('Reviewed producer source differs: ' + provider + '/' + name)
    qa = addons / QA; qa.mkdir()
    (qa / 'addon.xml').write_text('<addon id="'+QA+'" name="Disposable Watchlist QA" version="1.0.0" provider-name="Infinity engineering"><requires><import addon="xbmc.python" version="3.0.1"/></requires><extension point="xbmc.python.script" library="qa.py"/><extension point="xbmc.addon.metadata"><summary lang="en">Selected Watchlist playback verification only</summary><platform>all</platform></extension></addon>')
    observer = checked_observer((HERE / 'android_watchlist_observer.py').read_text())
    if 'Container(50).ListItem.FileNameAndPath' not in observer: raise ValueError('Live native ListItem observer missing')
    compile(observer, 'qa.py', 'exec', optimize=1)
    (qa / 'qa.py').write_text(observer)
    (qa / 'android_runtime_checks.py').write_bytes(retained('repairs/save-later-multiimage-20261023/android_runtime_checks.py'))
    (qa / 'producer-pins.json').write_text(json.dumps(producer_pins(), indent=2))
    userdata = out / 'home/userdata'; userdata.mkdir()
    (userdata / 'guisettings.xml').write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting></settings>')
    (userdata / 'watchlist-profile-sentinel.txt').write_text('disposable-watchlist-existing-data-v1')
    profile = userdata / 'addon_data' / CC; profile.mkdir(parents=True)
    data = seed(); (profile / 'continue-watching.json').write_text(json.dumps(data))
    report = dict(status='STAGED_NOT_EXECUTED', signed_pair=pair, dependencies=pins['archives'], provider_pins=producer_pins(),
                  seed=data, observer_sha256=hashlib.sha256(observer.encode()).hexdigest(), port=port,
                  provider_source_modified=False, synthetic_media=True, owner_accounts=False, shutdown='NOT_SELECTED')
    (out / 'ANDROID-INPUTS.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','candidate','recovery','signed-pair','owner-export','sdk','out'): p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--port', type=int, default=18766)
    stage(**vars(p.parse_args()))
