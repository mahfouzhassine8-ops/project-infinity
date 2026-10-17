#!/usr/bin/env python3
"""Bind exact experimental artifacts to all five workstreams and honest gates."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

NATIVE = '093323fbc0ae87cbe2fa2a21abab0c357fdaf754'
SIGNING = '6f585cb5e02fd1c93dfb548dd758a5e4dad7b764'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE_APK = 'bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286'
BASE_SKIN = '557003afc83a2661fec6ccef921979e264ff28e93595fb633340c618ab69bd56'
SKIN = 'e23d5d08c7737f317c2d55ae3f27e8746a019afd02dc20f6fbc73dc48c0c994e'
RECOVERY = 'dba95ad2a74bc220aeb2d6b045ef303ec2b83ec819ae72a09f3d470c9acf4ae8'
WATCHED_HELPER = 'c889693c2572456d0c6a176f5b8425ab0f854678fcd78e76391430f78d37e731'
CAPTURE = '7711cbfeb10e7651fcdfd505922f282086e2384a6ffb45ee7cebe90769ee8b5b'
ENGINE = 'lib/arm64-v8a/libkodi.so'
REPO = 'https://github.com/mahfouzhassine8-ops/project-infinity'


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024): result.update(block)
    return result.hexdigest()


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def text_section(raw):
    if raw[:6] != b'\x7fELF\x02\x01': raise ValueError('Expected little-endian ELF64')
    section_offset = struct.unpack_from('<Q', raw, 40)[0]
    section_size, count, names_index = struct.unpack_from('<HHH', raw, 58)
    names = struct.unpack_from('<IIQQQQIIQQ', raw, section_offset + section_size * names_index)
    strings = raw[names[4]:names[4] + names[5]]
    for index in range(count):
        entry = struct.unpack_from('<IIQQQQIIQQ', raw, section_offset + section_size * index)
        name = strings[entry[0]:].split(b'\0', 1)[0]
        if name == b'.text': return raw[entry[4]:entry[4] + entry[5]]
    raise ValueError('ELF .text unavailable')


def build(delivery, evidence, baseline_skin, handoff, out):
    out.mkdir(parents=True, exist_ok=True)
    signed = load(delivery / 'WATCHED-TOUCH-APK-PRESERVATION.json')
    assert signed['native_source_commit'] == NATIVE and signed['packaging_source_commit'] == SIGNING
    assert signed['native_run'] == 39004549623 and signed['protected_test4_apk_sha256'] == BASE_APK
    assert signed['all_dex_resources_assets_other_libraries_byte_identical']
    assert not signed['final_lock_authorized'] and not signed['physical_fold_verified']
    files = {}
    for artifact in signed['artifacts']:
        path = delivery / artifact['file']
        assert artifact['version_code'] == 2103382 and artifact['signer_sha256'] == CERT
        assert sha(path) == artifact['sha256'] and path.stat().st_size == artifact['bytes']
        files[path.name] = path
    candidate = next(value for value in signed['artifacts'] if not value['rollback'])
    native = load(evidence / 'native/ENGINE-PROOF.json')
    assert native['watched_touch_source_commit'] == NATIVE and native['complete_native_engine_compiled']
    assert sha(evidence / 'native/libkodi.so') == native['native_sha256']
    with zipfile.ZipFile(delivery / candidate['file']) as archive:
        packaged_text = text_section(archive.read(ENGINE))
    raw_text = text_section((evidence / 'native/libkodi.so').read_bytes())
    assert packaged_text == raw_text, 'Debug symbols must match the delivered native code'
    native_row = load(evidence / 'android-native/ANDROID-WATCHED-NATIVE-PROBE.json')
    assert native_row['apk_sha256'] == candidate['sha256'] and native_row['passed'] is True
    assert native_row['native_row_result']['passed'] and len(native_row['native_row_result']['tests']) == 14
    assert native_row['native_row_result']['helper_pipeline_verified']
    assert native_row['native_row_result']['derived_index_recovery_without_data_write']
    assert native_row['integrated_close']['passed'] and native_row['helper_state_retained_after_safe_close_reopen']
    assert native_row['fixture_automatic_addon_updates'] is False
    assert native_row['fixture_network_isolated'] is True
    assert native_row['addon_update_shutdown_verified'] is False
    renderer = {}
    for version in ('before', 'after'):
        result = load(evidence / ('renderer-' + version) / 'watched-runtime-result.json')
        assert result['passed'] and result['real_kodi_api'] and not result['physical_fold_verified']
        assert result['actual_installed_controller_preimages_verified'] == 13
        assert len(result['rendered_images']) == 3 and len(result['row_predicate_checks']) == 21
        assert sha(evidence / ('renderer-' + version) / 'script.infinity.watchedbridge-1.0.0-TEST.zip') == WATCHED_HELPER
        renderer[version] = result
    skin = load(delivery / 'SKIN224-PRESERVATION.json')
    assert skin['sha256'] == SKIN and sha(delivery / skin['file']) == SKIN
    assert skin['parent_sha256'] == BASE_SKIN and sha(baseline_skin) == BASE_SKIN
    assert not skin['removed'] and skin['xml_parsed'] == 2149 and not skin['broad_animations_changed']
    assert skin['existing_native_control_ids_and_actions_retained']
    files[skin['file']] = delivery / skin['file']
    for name in ('script.infinity.watchedbridge-1.0.0-TEST.zip', 'script.infinity.foldcapture-1.0.2-2103382-TEST3.zip', 'script.infinity.addonrecovery-1.0.0-TEST.zip'):
        path = delivery / name
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            if 'foldcapture' in name:
                assert sha(path) == CAPTURE
                identity = json.loads(archive.read('script.infinity.foldcapture/PACKAGE-IDENTITY.json'))
                assert identity['candidate_apk_sha256'] == candidate['sha256']
                assert identity['native_sha256'] == candidate['native_packaged_sha256']
            if 'addonrecovery' in name: assert sha(path) == RECOVERY
            if 'watchedbridge' in name:
                assert sha(path) == WATCHED_HELPER
                expected_helper = {Path(name).name: hashlib.sha256(archive.read(name)).hexdigest()
                                   for name in archive.namelist()}
                assert native_row['native_row_result']['helper_source_sha256'] == expected_helper
        files[name] = path
    recovered = load(evidence / 'recovery/recovery-smoke-result.json')
    assert recovered['passed'] and recovered['retained_settings_byte_identical']
    assert not recovered['actual_otaku_tested'] and not recovered['physical_fold_verified']
    android = {}
    for case in ('fresh', 'cold', 'core-initialized', 'loaded'):
        name = 'ANDROID-PROCESS-PROBE.json' if case == 'fresh' else 'OBSERVER-UPGRADE-PROBE.json'
        value = load(evidence / ('android-' + case) / name)
        actual = value.get('apk_sha256') if case == 'fresh' else value.get('candidate_apk_sha256')
        assert actual == candidate['sha256'] and value.get('physical_fold_accepted') is False
        android[case] = dict(passed=value.get('passed') is True, failure=value.get('failure'))
    status = dict(schema=1, date_utc='2026-10-17', release='2103382 TEST3 + skin .224 + guarded helpers',
        implementation_authorization='FULL_FIVE_WORKSTREAMS_CONTINUES', locked=False, final_lock_authorized=False,
        physical_fold_verified=False, user_phone_or_data_modified_by_agent=False,
        native_source_commit=NATIVE, signing_source_commit=SIGNING, candidate_apk=candidate,
        android_preservation=dict(tests_modified=False, skips_added=False, cases=android,
            overall='PASS' if all(v['passed'] for v in android.values()) else 'FAIL'),
        native_row_gate='PASS; actual signed ARM64 APK on disposable emulator, 14 cases plus real helper pipeline, index recovery and strict Close/reopen; automatic add-on updates disabled in this offline fixture only',
        automatic_addon_update_close_gate='FAIL in prior online fixture: protected_durability_failed for an add-on staging LICENSE.txt during automatic scraper updates; retained as an unresolved native shutdown issue',
        linux_renderer_gate='PASS; actual production 16x9 controls, fonts and assets, three themes per version',
        debug_text_sha256=hashlib.sha256(raw_text).hexdigest(), debug_text_bytes=len(raw_text),
        workstreams=[
            dict(id=1, name='Native Android stability', complete=False, implemented='Causal OnJobComplete retirement correction; original lifecycle/shutdown/admission retained', remaining='Physical return/screensaver/session/PiP/background playback/safe Close; unresolved Android failures shown above'),
            dict(id=2, name='Watched / Resume Hub / Watchlist / Collection', complete=False, implemented='Immutable native badge lookup, explicit Watched/Unwatched, existing checkpointed writer, list/progress preservation and version/hash-pinned episode scopes', remaining='Physical/provider acceptance; broader producer versions and automatic episode callbacks; unknown anime/legacy episode identities remain limited'),
            dict(id=3, name='Add-on touch and recovery', complete=False, implemented='Scoped 1193/50 first-long-press preselection using original context dispatch; visible recovery; read-only discovery and native re-enable without reset', remaining='Physical repeated touch/rail tests and actual Otaku enable/settings retention'),
            dict(id=4, name='Infinity skin refinement', complete=False, implemented='Forward .224 blue watched/legacy tint/recovery refinement; protected design, actions, navigation and motion retained', remaining='Full-skin all-screen, all-theme and physical Fold responsive/overlay/performance audit; broad motion remains gated'),
            dict(id=5, name='Integrated verification', complete=False, implemented='Coordinated signed experimental package, exact symbol/capture identities, same-code TEST4 rollback and independent runtime gates', remaining='Physical 5/20/45/90-minute matrix, playback/PiP/session/screensaver/persistence/provider regressions; explicit user approval before locking')])
    save(out / 'FIVE-WORKSTREAM-STATUS.json', status)
    save(out / 'PHYSICAL-FOLD-TEST-MATRIX.json', dict(schema=1, status='NOT_EXECUTED', candidate_sha256=candidate['sha256'],
        scenarios=[dict(background_minutes=minutes, display=display, playback=playback, screensaver=saver,
                        result=None, process_live_or_reclaimed=None, capture=None)
                   for minutes in (5,20,45,90) for display in ('cover','unfolded')
                   for playback in ('no-video','playing') for saver in ('off','on')],
        additional_checks={name:None for name in ('PiP','background playback','session without autoplay','rotation','split/pop-up','screen off','Home/Recents','network changes','immediate navigation','Essential-First Close/reopen','persistence','provider and rail regressions','Light/Dark/OLED')}))
    files['WATCHED-TOUCH-APK-PRESERVATION.json'] = delivery / 'WATCHED-TOUCH-APK-PRESERVATION.json'
    files['SKIN224-PRESERVATION.json'] = delivery / 'SKIN224-PRESERVATION.json'
    for name in ('FIVE-WORKSTREAM-STATUS.json', 'PHYSICAL-FOLD-TEST-MATRIX.json'):
        files[name] = out / name
    notes = delivery / 'INFINITY-2103382-TEST3-STATUS.md'
    assert notes.is_file(), 'Self-contained installation, rollback and five-workstream status are required'
    files[notes.name] = notes
    provenance = evidence / 'VERIFICATION-PROVENANCE.json'
    assert provenance.is_file(), 'Exact passing and failing run identities are required'
    files['verification/VERIFICATION-PROVENANCE.json'] = provenance
    files['rollback/' + baseline_skin.name] = baseline_skin
    rollback_capture = delivery / 'rollback/Infinity-Fold-Freeze-Capture-1.0.0-TEST.zip'
    assert sha(rollback_capture) == 'd99f5e701a5fe2f0dbac0a8eac8f4af29b8c7cb35d0dd3bd76c9889b9d67e174'
    files['rollback/' + rollback_capture.name] = rollback_capture
    assert sha(handoff) == '15a127d16f4d609a68e141982d1cce6d22507b261b22c6f26dcec8089a6154c9'
    with zipfile.ZipFile(handoff) as archive: assert archive.testzip() is None
    files['references/' + handoff.name] = handoff
    # Retain concise gate results and real screenshots. Full matched native ELF
    # and verbose runtime logs are delivered as separate debug evidence.
    for area in ('native', 'android-native', 'recovery', 'renderer-before', 'renderer-after'):
        for path in sorted((evidence / area).rglob('*')):
            if path.is_file() and path.suffix in ('.json', '.png'):
                files['verification/' + area + '/' + path.relative_to(evidence / area).as_posix()] = path
    for case in android:
        root = evidence / ('android-' + case)
        for path in sorted(root.glob('*.json')):
            files['verification/android-' + case + '/' + path.name] = path
        for path in sorted(root.rglob('close.json')):
            files['verification/android-' + case + '/' + path.relative_to(root).as_posix()] = path
    failed = evidence / 'native-ui-failed/fold-android-evidence'
    assert (failed / 'integrated-close/close.json').is_file()
    for name in ('ANDROID-WATCHED-NATIVE-PROBE.json', 'integrated-close/close.json', 'kodi.log'):
        files['verification/history/native-helper-online-update/' + name] = failed / name
    manifest = {name:dict(sha256=sha(path), bytes=path.stat().st_size) for name,path in files.items()}
    save(out / 'PACKAGE-IDENTITY.json', dict(schema=1, files=manifest, locked=False, native_source=NATIVE, signing_source=SIGNING))
    files['PACKAGE-IDENTITY.json'] = out / 'PACKAGE-IDENTITY.json'
    (out / 'SHA256SUMS').write_text(''.join(value['sha256'] + '  ' + name + '\n' for name,value in sorted(manifest.items())))
    files['SHA256SUMS'] = out / 'SHA256SUMS'
    target = out / 'Infinity-2103382-Consolidated-Five-Workstream-TEST3.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_STORED) as archive:
        for name,path in sorted(files.items()): archive.write(path,name)
    with zipfile.ZipFile(target) as archive: assert archive.testzip() is None
    return dict(file=str(target), bytes=target.stat().st_size, sha256=sha(target), android=status['android_preservation'], all_five_complete=False, locked=False)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    for name in ('delivery','evidence','baseline-skin','handoff','out'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.delivery,args.evidence,args.baseline_skin,args.handoff,args.out),indent=2))
