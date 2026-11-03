"""Internal native-only unsigned assembly/member comparison; never a release APK."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import shutil
from zipfile import ZipFile
import artifact_preflight as inputs

SOURCE = '765b92bc8af1452ffc2bbb19a03a3de229a90255'
NATIVE_ARCHIVE_SHA = 'cac2281741679eaebbdf167969afdbeccdd0a8e1a1f4e2e5fd7eb529807571e0'
SIGNATURE = {'META-INF/INFINITY.SF', 'META-INF/INFINITY.RSA', 'META-INF/MANIFEST.MF'}
LIBRARY = 'lib/arm64-v8a/libkodi.so'


def hashes(z):
    names = z.namelist()
    inputs.require(len(names) == len(set(names)), 'Duplicate APK member')
    result = {}
    for name in sorted(set(names) - SIGNATURE):
        with z.open(name) as stream:
            result[name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return result


def run(baseline, native_artifact, source_map, out):
    inputs.require(not out.exists(), 'Preservation output already exists')
    inputs.assert_sha(baseline, inputs.APK_SHA)
    inputs.assert_sha(native_artifact, NATIVE_ARCHIVE_SHA)
    out.mkdir()
    unsigned = out / 'INTERNAL-UNSIGNED-NATIVE-ASSEMBLY-NOT-FOR-INSTALL.apk'
    with ZipFile(native_artifact) as native, ZipFile(baseline) as original:
        names = native.namelist()
        inputs.require(len(names) == len(set(names)) and native.testzip() is None,
                       'Native artifact duplicate/CRC failure')
        prefix = 'p0-native-build/'
        proof = json.loads(native.read(prefix + 'ENGINE-PROOF.json'))
        compiled_map = json.loads(native.read(prefix + 'NATIVE-SOURCE-MAP.json'))
        inputs.require(compiled_map == json.loads(source_map.read_text()) and len(compiled_map) == 9411,
                       'Complete compiled source map differs from authenticated candidate')
        inputs.require(proof['source_commit'] == SOURCE and proof['complete_native_engine_compiled'] is True
                       and proof['changed_or_missing_reviewed'] == [] and proof['reviewed_file_count'] == 9411,
                       'Native producer or unchanged-source build proof mismatch')
        abi = native.read(prefix + 'NATIVE-MODULE-ABI.txt').decode()
        inputs.require('InfinityCommandCenterIdentityV1' in abi and 'AArch64' in abi and 'ELF64' in abi,
                       'Protected native-module ABI/target mismatch')
        with native.open(prefix + 'libkodi.so') as stream:
            header = stream.read(20)
            inputs.require(header[:5] == b'\x7fELF\x02' and header[18:20] == b'\xb7\x00', 'Wrong ELF target')
        old = hashes(original)
        inputs.require(old[LIBRARY] == inputs.NATIVE_SHA, 'Original native member mismatch')
        with ZipFile(unsigned, 'w', allowZip64=True) as target:
            for info in original.infolist():
                if info.filename in SIGNATURE:
                    continue
                with target.open(copy.copy(info), 'w', force_zip64=info.file_size >= 2**31) as dest:
                    parent = native if info.filename == LIBRARY else original
                    name = prefix + 'libkodi.so' if info.filename == LIBRARY else info.filename
                    with parent.open(name) as src:
                        shutil.copyfileobj(src, dest, 1024 * 1024)
    with ZipFile(unsigned) as candidate:
        current = hashes(candidate)
    inputs.require(set(old) == set(current), 'APK payload added/removed')
    changed = [n for n in old if old[n] != current[n]]
    inputs.require(changed == [LIBRARY] and current[LIBRARY] == proof['native_sha256'],
                   'Unexpected member difference or native bytes')
    inputs.save(out / 'ALL-APK-MEMBER-HASHES.json', {n: {'baseline': old[n], 'assembly': current[n]} for n in old})
    report = dict(status='PASS_INTERNAL_NATIVE_ONLY_MEMBER_PRESERVATION',
        baseline_apk_sha256=inputs.APK_SHA, compiled_native_artifact_sha256=NATIVE_ARCHIVE_SHA,
        compiled_native_source=SOURCE, compiled_native_sha256=current[LIBRARY],
        compared_payload_members=len(old), unchanged_payload_members=len(old)-1,
        changed_members=changed, added=[], removed=[],
        unchanged_native_libraries=sum(n.startswith('lib/') and n.endswith('.so') and n != LIBRARY for n in old),
        unchanged_dex_members=[n for n in old if n.startswith('classes') and n.endswith('.dex')],
        baseline_manifest_version_and_labels_unchanged=True,
        signature_entries_omitted=sorted(SIGNATURE),
        original_signature_evidence='Actual identical451 bytes verified in Actions41726452356',
        release_apk=False, installable_candidate_delivered=False, app_executed=False,
        Android_runtime='BLOCKED', physical_fold_acceptance=False,
        final_higher_version_and_signed_member_gate='NOT_RUN', final_owner_component_gate='NOT_RUN')
    inputs.save(out / 'NATIVE-ONLY-PRESERVATION.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True, type=Path)
    p.add_argument('--native-artifact', required=True, type=Path)
    p.add_argument('--source-map', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    run(**vars(p.parse_args()))
