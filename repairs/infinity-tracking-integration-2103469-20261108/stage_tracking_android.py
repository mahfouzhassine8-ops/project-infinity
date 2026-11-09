"""Admit original69 and signed module fixtures; stage normal Kodi ZIP inputs.

Offline preparation/network downloads only. No adb, app dispatch, build, signing,
provider settings or profile/progress seed. The workflow admits official whole
artifact provenance before calling this independent byte/RSA verifier.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import qualify_android_baseline as base

HERE = Path(__file__).resolve().parent
QA = 'script.infinity.trackingqa'
CC = base.CC
FIXTURE_SOURCE = '9d64ffb84404036ce6e02d6cb160fb004a029b33'
FIXTURE_RUN = 42555855742


def selected_focus():
    request_path = HERE / 'TRACKING-ANDROID-REQUEST.json'
    request = base.load(request_path)
    retained = request['retained_actual_evidence']
    base.require(request['execution_focus'] == 'independent-movie' and
        retained['run'] == 42567028842 and retained['source'] == '9b05d1b4bf2283b7adc92f7ef6db0aff3b9fede3' and
        retained['queens_blade_status'] == 'FAIL_ACTUAL_SDK_MOVIE_UNKNOWN_EPISODE' and
        retained['cross_entry_rezero_status'] == 'BLOCKED_UNVERIFIED_METADATA' and
        retained['replay_known_wrong_typed_tv'] is False, 'EXACT_COMMITTED_INDEPENDENT_MOVIE_FOCUS_REQUIRED')
    return dict(request_sha256=base.sha(request_path), execution_focus=request['execution_focus'],
                retained_actual_evidence=retained)


def stage(apk, sdk, fixture, pins_path, out):
    selection = selected_focus()
    base.require(not out.exists(), 'FRESH_STAGING_DIRECTORY')
    out.mkdir(parents=True)
    proof = base.verify_apk(apk.resolve(), sdk.resolve(), out)
    bundle, _ = base.original_module_tools()
    metadata = base.load(fixture / 'MODULE-FIXTURE.json')
    base.require(metadata['run_id'] == FIXTURE_RUN and metadata['source'] == FIXTURE_SOURCE and
        metadata['status'] == 'ORIGINAL_KEY_SIGNED_INTERNAL_MODULE_FIXTURE_NOT_RELEASE_ACCEPTANCE' and
        metadata['original80_source_signatures'] is True and metadata['APK_build'] is False and
        metadata['APK_signing'] is False and metadata['release_acceptance'] is False,
        'EXACT_ORIGINAL_KEY_MODULE_FIXTURE_PRODUCER')
    base.require(base.sha(fixture / 'pair/SOURCE-PINS.json') == metadata['source_pins_sha256'], 'EXACT_FIXTURE_SOURCE_PINS')
    zips = out / 'zips'
    zips.mkdir()
    fixtures, candidate = [], None
    for package in metadata['fixture_packages']:
        version = package['CC']
        base.require(version in ('0.3.5.68', '0.3.5.69') and package['recovery'] is (version == '0.3.5.69'), 'EXACT_MODULE_PAIR')
        archive = fixture / package['archive']
        base.require(archive.name == package['archive'] and base.sha(archive) == package['sha256'], 'FIXTURE_ZIP_HASH')
        number = '2103470' if version == '0.3.5.68' else '2103471'
        root = fixture / 'pair' / number / 'modules'
        payload, files = bundle.build(root)
        manifest = root / CC / bundle.MANIFEST
        base.require(len(files) == 80 and payload == manifest.read_bytes(), 'COMPLETE80_CANONICAL_MANIFEST')
        base.command(['openssl', 'dgst', '-sha256', '-verify', base.FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                      '-signature', str(manifest) + '.sig', manifest])
        base.require(ET.fromstring(files[CC + '/addon.xml']).get('version') == version, 'EXACT_FIXTURE_VERSION')
        for name in ('plugin.py', 'resume_hub.py', 'service.py'):
            expected = (HERE / ('overlay' if version == '0.3.5.68' else 'reference') / CC / name).read_bytes()
            base.require(files[CC + '/' + name] == expected, 'EXACT_FROZEN_THREE_SOURCES:' + name)
        with ZipFile(archive) as z:
            names = [name for name in base.safe_zip(z) if not name.endswith('/')]
            expected = {name: raw for name, raw in files.items() if name.startswith(CC + '/')}
            expected[CC + '/' + bundle.MANIFEST] = payload
            expected[CC + '/' + bundle.MANIFEST + '.sig'] = Path(str(manifest) + '.sig').read_bytes()
            base.require(set(names) == set(expected) and all(z.read(n) == raw for n, raw in expected.items()), 'WHOLE_ORIGINAL_SIGNED_CC_ZIP')
        shutil.copyfile(archive, zips / archive.name)
        row = dict(addon=CC, version=version, archive=archive.name, sha256=package['sha256'], recovery=package['recovery'])
        fixtures.append(row)
        if not row['recovery']:
            candidate = dict(cc_version=version, manifest_sha256=hashlib.sha256(payload).hexdigest(),
                             module_sources={n: hashlib.sha256(raw).hexdigest() for n, raw in files.items()})
    base.require(candidate and len(fixtures) == 2 and len({r['version'] for r in fixtures}) == 2, 'COMPLETE_SIGNED_FIXTURE_PAIR')
    pins = base.load(pins_path)
    base.require(pins['baseline_apk_sha256'] == base.APK_SHA and pins['provider'] == 'plugin.video.watchnixtoons2', 'DEPENDENCY_SCOPE')
    dependencies, provider_sources = [], {}
    by_id = {r['addon']: r for r in pins['archives']}
    base.require(len(by_id) == len(pins['archives']) == len(pins['installation_order']) and set(by_id) == set(pins['installation_order']), 'EXACT_DEPENDENCY_ORDER')
    for index, aid in enumerate(pins['installation_order']):
        pin = by_id[aid]
        target = zips / ('%02d-' % index + aid + '-' + pin['version'] + '.zip')
        base.require(pin['url'].startswith('https://'), 'HTTPS_PUBLISHER_INPUT')
        with urllib.request.urlopen(pin['url'], timeout=45) as source, target.open('xb') as dest:
            total = 0
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                base.require(total <= 64 * 1024 * 1024, 'BOUNDED_PUBLISHER_ARCHIVE')
                dest.write(chunk)
        base.require(base.sha(target) == pin['sha256'], 'EXACT_PUBLISHER_ARCHIVE:' + aid)
        with ZipFile(target) as z:
            names = [n for n in base.safe_zip(z) if not n.endswith('/')]
            base.require(all(n.startswith(aid + '/') for n in names), 'SINGLE_UNMODIFIED_ADDON_ARCHIVE')
            addon = z.read(aid + '/addon.xml')
            node = ET.fromstring(addon)
            base.require(node.get('id') == aid and node.get('version') == pin['version'] and
                         hashlib.sha256(addon).hexdigest() == pin['manifest_sha256'], 'PINNED_PUBLISHER_METADATA')
            if aid == pins['provider']:
                provider_sources[aid] = {n.removeprefix(aid + '/'): hashlib.sha256(z.read(n)).hexdigest() for n in names}
        dependencies.append(dict(addon=aid, version=pin['version'], archive=target.name, sha256=pin['sha256']))
    candidate['provider_sources'] = provider_sources
    observer = HERE / 'tracking_android_observer.py'
    addon = ('<addon id="' + QA + '" name="Tracking engineering observer" version="1.0.0" provider-name="Infinity engineering">'
             '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
             '<extension point="xbmc.python.script" library="default.py"/></addon>')
    qa_zip = zips / (QA + '-1.0.0.zip')
    with ZipFile(qa_zip, 'x', compression=ZIP_DEFLATED) as z:
        z.writestr(QA + '/addon.xml', addon)
        z.writestr(QA + '/default.py', observer.read_bytes())
        z.writestr(QA + '/expected.json', json.dumps(candidate, sort_keys=True))
    # Ordinary settings for this fresh disposable VM; no signature/integrity setting is disabled.
    (out / 'guisettings.xml').write_text('<settings version="2">'
        '<setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
        '<setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting>'
        '<setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
    remote = '/sdcard/Download/infinity-tracking-zips/'
    (out / 'sources.xml').write_text('<sources><files><source><name>Tracking engineering ZIPs</name>'
        '<path pathversion="1">' + remote + '</path><allowsharing>false</allowsharing></source></files></sources>')
    base.save(out / 'STAGED.json', dict(schema=1, status='ADMITTED_INPUTS_ONLY_NOT_ANDROID_PASS',
        selection=selection,
        APK_path=str(apk.resolve()), baseline=proof, fixture=metadata, fixture_packages=fixtures,
        dependency_pins_sha256=base.sha(pins_path), dependencies=dependencies, expected=candidate,
        qa=dict(addon=QA, version='1.0.0', archive=qa_zip.name, sha256=base.sha(qa_zip)),
        observer_sha256=base.sha(observer), stage_source_sha256=base.sha(__file__), remote_zip_directory=remote,
        selected_tests=['normal_zip_module_install_full80_auth', 'actual_typed_parent_save_menu_probe_no_tv_playback',
            'save_browse_only_no_history', 'explicit_restart_persistence',
            'independent_actual_public_wnt_movie_partial_resume_95_percent_completion_replay',
            'independent_existing_theme_viewport_capture'],
        runtime_pending_availability=['actual_public_wnt_movie_source'],
        unselected_or_blocked=['premium_provider_credentials', 'Fold_acceptance', 'shutdown'],
        release_acceptance=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('apk', 'sdk', 'fixture-dir', 'dependency-pins', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    stage(args.apk, args.sdk, args.fixture_dir, args.dependency_pins, args.out)
