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
import prepare_tracking_release as releaseprep

HERE = Path(__file__).resolve().parent
QA = 'script.infinity.trackingqa'
CC = base.CC
CONTRACT = HERE / 'INFINITY-ORIGIN-ACCEPTANCE.json'
FIXTURE_PIN = HERE / 'TRACKING-MODULE-FIXTURE-PIN.json'


def selected_focus():
    request_path = HERE / 'TRACKING-ANDROID-REQUEST.json'
    request, contract = base.load(request_path), base.load(CONTRACT)
    relative = CONTRACT.relative_to(base.ROOT).as_posix()
    base.require(request['application_tests'] is True and request['shutdown_tests'] is False and
        request['execution_focus'] == 'infinity-origin-acceptance' and
        request['source_bindings'][relative] == base.sha(CONTRACT) and
        contract['operation'] == 'accept-existing-infinity-origin-playback-tracking' and
        contract['protected_source_checkpoint'] == 'e410f30ba9e38182e4e77810e5237e5442cbd31a' and
        contract['production_source_checkpoint'] == '5787ca4569faa70dec4f10493b08bd8015d542ea' and
        contract['protected_recovery'] == 2103469, 'EXACT_ENABLED_COMMITTED_INFINITY_ORIGIN_ACCEPTANCE_REQUIRED')
    return dict(request_sha256=base.sha(request_path), execution_focus=request['execution_focus'],
        acceptance_contract_sha256=base.sha(CONTRACT), fixture_pin_sha256=base.sha(FIXTURE_PIN),
        protected_source_checkpoint=contract['protected_source_checkpoint'],
        production_source_checkpoint=contract['production_source_checkpoint'])


def stage(apk, sdk, fixture, pins_path, out):
    selection = selected_focus()
    base.require(not out.exists(), 'FRESH_STAGING_DIRECTORY')
    out.mkdir(parents=True)
    proof = base.verify_apk(apk.resolve(), sdk.resolve(), out)
    bundle, _ = base.original_module_tools()
    metadata, approved = base.load(fixture / 'MODULE-FIXTURE.json'), base.load(FIXTURE_PIN)
    admission = base.load(fixture / 'pair/VERSION-ADMISSION.json')
    contract = base.load(CONTRACT)
    base.require(metadata['run_id'] == approved['run'] and metadata['source'] == approved['source'] and
        metadata['production_source'] == contract['production_source_checkpoint'] and
        metadata['source_pins_sha256'] == approved['source_pins_sha256'] and
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
        role = 'recovery' if package['recovery'] is True else 'candidate'
        base.require(type(package['recovery']) is bool and version == admission[role + '_CC'] and
                     package['versionCode'] == admission[role + '_versionCode'], 'EXACT_APPROVED_DYNAMIC_MODULE_PAIR')
        archive = fixture / package['archive']
        base.require(archive.name == package['archive'] and base.sha(archive) == package['sha256'], 'FIXTURE_ZIP_HASH')
        number = str(admission[role + '_versionCode'])
        base.require(package['modules_path'] == 'pair/' + number + '/modules', 'EXACT_APPROVED_MODULE_DIRECTORY')
        root = fixture / package['modules_path']
        payload, files = bundle.build(root)
        manifest = root / CC / bundle.MANIFEST
        base.require(len(files) == 80 and payload == manifest.read_bytes(), 'COMPLETE80_CANONICAL_MANIFEST')
        base.command(['openssl', 'dgst', '-sha256', '-verify', base.FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                      '-signature', str(manifest) + '.sig', manifest])
        base.require(ET.fromstring(files[CC + '/addon.xml']).get('version') == version, 'EXACT_FIXTURE_VERSION')
        for name in ('plugin.py', 'resume_hub.py', 'service.py'):
            expected = (releaseprep.recovery_source(name) if package['recovery'] else
                        (HERE / 'overlay' / CC / name).read_bytes())
            base.require(files[CC + '/' + name] == expected, 'EXACT_FROZEN_THREE_SOURCES:' + name)
            if not package['recovery']:
                base.require(hashlib.sha256(expected).hexdigest() == contract['production_source_sha256'][name],
                             'EXACT_E410_ACCEPTANCE_SOURCE:' + name)
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
        selected_tests=['normal_zip_install_dynamic_e410_full80_auth', 'actual_infinity_tv_watchlist_origin',
            'genuine_saved_parent_child_300_second_actual_clock_stop_progress_next_continue_resume',
            'actual_infinity_movies_watchlist_origin_partial_stop_continue_resume', 'save_alone_no_history'],
        runtime_pending_availability=['actual_public_wnt_movie_source'],
        unselected_or_blocked=['premium_provider_credentials', 'Fold_acceptance', 'shutdown'],
        release_acceptance=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('apk', 'sdk', 'fixture-dir', 'dependency-pins', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    stage(args.apk, args.sdk, args.fixture_dir, args.dependency_pins, args.out)
