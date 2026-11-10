"""Prepare exact signed77-based owner bundles; no APK signing or registry mutation."""
from pathlib import Path
import argparse
import copy
import json
import re
import shutil
import subprocess
from zipfile import ZipFile
import prepare_modules as prep

NATIVE = 'lib/arm64-v8a/libkodi.so'
ENGINE = '9935873eb1c8563281743e6d4b978f530c9dde3e9d6d777519af70643c4f66db'
LABELS = 'assets/experience-component-updates.properties'
CANONICAL = 'dfee7205dd88abe81db5e263c368f67ece43df02'
MODULE_SOURCE = '148abe9e04e7212eaee17963875aeda5ecd1d843'
MODULE_ARCHIVE = '6fdf88af1c45dff1b9a26f154d59dbfcf7232a661e5cea4c18f5428936859809'
TARGETS = ('INFINITY', 'CHOOSER_SHELL')


def load(path):
    return json.loads(path.read_bytes())


def authority():
    return json.loads(subprocess.check_output(['git', 'show', CANONICAL+':repairs/dual-experience-isolation-2103420/release-authority.json'], cwd=prep.ROOT))


def allowed(recovery):
    cc = 'assets/addons/'+prep.CC+'/'
    skin = 'assets/addons/'+prep.SKIN+'/'
    names = {'AndroidManifest.xml', LABELS, *(cc+n for n in
             ('addon.xml', 'INFINITY-MODULES.v1', 'INFINITY-MODULES.v1.sig')),
             *(skin+n for n in ('addon.xml', 'infinity-skin.json', 'Infinity-Protected-Manifest.json'))}
    if not recovery:
        names |= {NATIVE, *(cc+n for n in ('default.py', 'resources/settings.xml', 'network_connections.py')),
                  skin+prep.HUB}
    return names


def compare(baseline, candidate, proof):
    t = prep.tools()
    assert prep.sha(baseline.read_bytes()) == prep.BASE_APK
    with ZipFile(baseline) as a, ZipFile(candidate) as b:
        old = set(t.validate_names(a))-t.SIGNATURE
        new = set(t.validate_names(b))-t.SIGNATURE
        added = new-old
        assert not old-new
        assert added == (set() if proof['recovery'] else {'assets/addons/'+prep.CC+'/network_connections.py'})
        differences = {}
        for name in sorted(new):
            after = b.read(name)
            if name not in old or a.read(name) != after:
                assert name in allowed(proof['recovery']), name
                assert prep.sha(after) == proof['changed_members'][name], name
                differences[name] = prep.sha(after)
            if name == 'AndroidManifest.xml':
                assert t.normalize_manifest(after) == (t.normalize_manifest(a.read(name))[0], proof['versionCode'])
        assert differences == proof['changed_members']
        assert set(differences) == allowed(proof['recovery'])
        assert prep.sha(b.read(NATIVE)) == (proof['baseline_native_sha256'] if proof['recovery'] else ENGINE)
        dex = {n:prep.sha(b.read(n)) for n in new if re.fullmatch(r'classes\d*\.dex', n)}
        assert dex == {n:prep.sha(a.read(n)) for n in dex}
    return dict(status='PASS_EXACT77_ONLY_DECLARED_NETWORK_OR_FORWARD_RECOVERY_MEMBERS',
                baseline_sha256=prep.BASE_APK, candidate_sha256=prep.sha(candidate.read_bytes()),
                changed_members=differences, added_members=sorted(added), all_DEX_unchanged=dex,
                Cobra_members_unchanged=True, APK_signing='NOT_VERIFIED_BY_THIS_COMPARISON',
                Android='NOT_RUN_BY_PREPARATION', physical_Fold='PENDING')


def prepare(apk, native, module_fixture, components, out, candidate_version, recovery_version):
    assert not out.exists()
    assert candidate_version > 2103477 and recovery_version > candidate_version
    assert prep.sha(apk.read_bytes()) == prep.BASE_APK
    assert prep.sha(native.read_bytes()) == ENGINE
    t = prep.tools()
    source_pins = load(prep.TASK/'SOURCE-PINS.json')
    compiled_pins = json.loads(subprocess.check_output(['git','show',
        'e9248b7813b5a0060e0e2aafab455ebbd1a2cdc5:'+str((prep.TASK/'SOURCE-PINS.json').relative_to(prep.ROOT))],cwd=prep.ROOT))
    assert source_pins['native'] == compiled_pins['native']
    for group, entries in source_pins.items():
        for name, wanted in entries.items():
            assert prep.sha((prep.TASK/group/name).read_bytes()) == wanted, name
    assert prep.sha((module_fixture.parent/'artifact.zip').read_bytes()) == MODULE_ARCHIVE, 'OFFICIAL42761231636_MODULE_ARTIFACT_REQUIRED'
    expected_modules = load(prep.HERE/'MODULE-PREPARE-REQUEST.json')['expected_outputs']
    expected_changes = load(prep.HERE/'APK-PREPARE-REQUEST.json')['expected_changes']
    previous = authority()
    catalog = load(components/'catalog.json')
    assert catalog == previous['bundle_catalog'], 'EXACT_CANONICAL_OFFICIAL75_BUNDLE_CATALOG'
    metas = {o:t.read_bundle(components/row['file'], row) for o,row in catalog['bundles'].items()}
    prepared = module_fixture/'network-module-prepared'
    module_proof = load(prepared/'PREPARATION.json')
    audit_path = module_fixture/'network-module-audit/MODULE-UPGRADE-RECOVERY.json'
    audit = load(audit_path)
    assert audit['status'] == 'PASS_FOUR_AFFECTED_ORIGINAL_INSTALLER_CASES'
    assert audit['original_installer_changed'] is False and len(audit['cases']) == 4
    assert module_proof['baseline'] == 2103477 and module_proof['helper_experiments'] == 'PARKED_EXCLUDED_FROM_RELEASE'
    assert module_proof['source_commit'] == MODULE_SOURCE
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=prep.ROOT, text=True).strip()
    metadata = {}
    with ZipFile(apk) as original:
        baseline_names = set(t.validate_names(original))-t.SIGNATURE
        member_names = {n for m in metas.values() for n in m['members']}
        dex_order = sorted(((o,n) for o,m in metas.items() for n in m['dex']),
                           key=lambda x: (('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA').index(x[0]),x[1]))
        dex_names = ['classes'+(str(i) if i>1 else '')+'.dex' for i in range(1,len(dex_order)+1)]
        assert baseline_names == member_names | set(dex_names)
        for (owner, name), actual in zip(dex_order, dex_names):
            assert prep.sha(original.read(actual)) == metas[owner]['dex'][name], actual
        for owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
            with ZipFile(components/catalog['bundles'][owner]['file']) as z:
                for name in metas[owner]['members']:
                    before, actual = z.read('payload/'+name), original.read(name)
                    assert (t.normalize_manifest(before)[0] == t.normalize_manifest(actual)[0]
                            if name == 'AndroidManifest.xml' else before == actual), name
        for (label, cc_version, skin_version, count), version in zip(prep.PAIRS, (candidate_version,recovery_version)):
            work = out/str(version); bundles = work/'components'; bundles.mkdir(parents=True)
            inputs_path = prepared/label/'INPUTS.json'
            assert prep.sha(inputs_path.read_bytes()) == module_proof['inputs'][label]
            pins = load(inputs_path)
            assert pins['source_commit'] == MODULE_SOURCE
            for key, wanted in expected_modules[label].items():
                assert pins[key] == wanted, key
            modules = prepared/label/'modules'
            current = prep.hashes(modules)
            assert {n:v for n,v in current.items() if n != prep.CC+'/INFINITY-MODULES.v1.sig'} == pins['modules']
            payload, files = t.module_bundle.build(modules)
            assert len(files) == count and prep.sha(payload) == pins['manifest_sha256']
            assert payload == (modules/prep.CC/'INFINITY-MODULES.v1').read_bytes()
            subprocess.run(['openssl','dgst','-sha256','-verify',str(prep.ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                            '-signature',str(modules/prep.CC/'INFINITY-MODULES.v1.sig'),
                            str(modules/prep.CC/'INFINITY-MODULES.v1')],check=True,capture_output=True)
            assert prep.hashes(prepared/label/'skin') == pins['skin_files']
            replacements = {'assets/addons/'+n:p.read_bytes() for n in current for p in [modules/n]}
            replacements.update({'assets/addons/'+prep.SKIN+'/'+n:(prepared/label/'skin'/n).read_bytes() for n in pins['skin_files']})
            replacements[LABELS] = ('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
            if label == 'candidate': replacements[NATIVE] = native.read_bytes()
            actual_changes = {n:prep.sha(raw) for n,raw in replacements.items()
                              if n not in baseline_names or original.read(n) != raw}
            actual_changes['AndroidManifest.xml'] = prep.sha(t.set_version(original.read('AndroidManifest.xml'), version))
            assert set(actual_changes) == allowed(label == 'recovery')
            assert actual_changes == expected_changes[label], 'PAYLOAD_DIFFERS_FROM_EXACT_REVIEWED_MEMBER_HASHES'
            new_catalog = copy.deepcopy(catalog); new_catalog.update(source=source, release_approved=False)
            all_meta = {}
            for owner in metas:
                old = metas[owner]
                if owner not in TARGETS:
                    shutil.copyfile(components/catalog['bundles'][owner]['file'],bundles/catalog['bundles'][owner]['file'])
                    all_meta[owner] = old
                    continue
                meta = copy.deepcopy(old)
                meta.update(version=f'{version}.{owner.lower()}.network.1', approved_source=source)
                extra = {'assets/addons/'+prep.CC+'/network_connections.py'} if owner == 'INFINITY' and label == 'candidate' else set()
                names = set(meta['members']) | extra
                path = bundles/(owner+'.zip')
                with ZipFile(path,'w') as target, ZipFile(components/catalog['bundles'][owner]['file']) as old_bundle:
                    for name in sorted(meta['dex']):target.writestr(t.record(name),old_bundle.read(name))
                    for name in sorted(names):
                        raw = replacements[name] if name in replacements else original.read(name)
                        info = original.getinfo(name) if name in baseline_names else None
                        meta['members'][name] = dict(sha256=prep.sha(raw), compress_type=info.compress_type if info else 8,
                                                     external_attr=info.external_attr if info else 0o100644<<16)
                        normalized = t.normalize_manifest(raw)[0] if name == 'AndroidManifest.xml' else raw
                        meta['payload']['member:'+name] = dict(owner=owner, sha256=prep.sha(normalized))
                        target.writestr(t.record('payload/'+name),raw)
                    meta['digest'] = t.component_digest(meta['payload'],owner)
                    target.writestr(t.record('component.json'),t.canonical(meta))
                row = {k:meta[k] for k in ('version','digest','approved_source','settings_schema')}
                row.update(file=path.name,sha256=prep.sha(path.read_bytes()))
                new_catalog['bundles'][owner] = row
                all_meta[owner] = meta
            prep.save(bundles/'catalog.json',new_catalog)
            unsigned = work/'combined-unsigned.apk'
            assembly = t.combine(bundles,new_catalog,unsigned,version)
            proof = dict(versionCode=version, source_commit=source, baseline_versionCode=2103477,
                         baseline_sha256=prep.BASE_APK, baseline_native_sha256=prep.sha(original.read(NATIVE)),
                         native_sha256=prep.sha(original.read(NATIVE)) if label=='recovery' else ENGINE,
                         CC=cc_version, skin=skin_version, recovery=label=='recovery',
                         changed_members=actual_changes, source_files_added=[] if label=='recovery' else ['assets/addons/'+prep.CC+'/network_connections.py'],
                         source_pins_sha256=prep.sha((prep.TASK/'SOURCE-PINS.json').read_bytes()),
                         original_module_audit_sha256=prep.sha(audit_path.read_bytes()),
                         module_manifest_sha256=pins['manifest_sha256'], module_count=count,
                         unsigned_sha256=assembly['unsigned_apk_sha256'], version_reserved=False,
                         production_resolver='ORIGINAL_KODI', public_release=False, Android='NOT_RUN',
                         physical_Fold='PENDING', original_APK_signing='PENDING_REGISTERED_ORIGINAL_SIGNER')
            prep.save(work/'PREPARATION.json',proof)
            comparison = compare(apk,unsigned,proof)
            prep.save(work/'APK-PRESERVATION.json',comparison)
            metadata[str(version)] = dict(preparation=prep.sha((work/'PREPARATION.json').read_bytes()),
                                         preservation=prep.sha((work/'APK-PRESERVATION.json').read_bytes()),
                                         catalog=prep.sha((bundles/'catalog.json').read_bytes()))
    prep.save(out/'PAIR-PREPARATION.json',dict(status='UNSIGNED_SOURCE_BOUND_77_NETWORK_FORWARD_PAIR',
              baseline=2103477, prior_canonical=CANONICAL, source=source, preparations=metadata,
              registry_mutation=False, APK_signing=False, Android='PENDING', owner_delivery_cleared=False))
    print('PASS unsigned pair from exact signed77; original owner bundles/DEX/Cobra preserved; registry/signing/Android pending')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('apk','native','module-fixture','components','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--candidate-version',type=int,required=True)
    p.add_argument('--recovery-version',type=int,required=True)
    args=vars(p.parse_args());prepare(**{k.replace('-','_'):v for k,v in args.items()})
