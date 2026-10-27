"""Historical preservation assembler and current guarded original-key signer.

The historical prepare subcommand is not the isolated-module assembler.
build_candidate.py and component_bundles.py produce the current owner payloads.
"""
import argparse
import base64
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from zipfile import ZipFile, ZipInfo

from inventory import APK_SHA, CERT_SHA, SIGNATURE, file_sha, save, validate_names
from release_gate import pre_sign, normalize_manifest, remote_authority, require, Rejected


def prepare(baseline, out, version):
    require(file_sha(baseline) == APK_SHA, 'EXACT_BASELINE_REQUIRED')
    require(type(version) is int and 2103420 < version <= 2100000000, 'APP_ROLLBACK')
    out = Path(out)
    require(not out.exists(), 'FRESH_OUTPUT_REQUIRED')
    with ZipFile(baseline) as source:
        validate_names(source)
        raw = source.read('AndroidManifest.xml')
        normalized, old_version = normalize_manifest(raw)
        expected = struct.pack('<I', old_version)
        positions = [i for i in range(len(raw)) if raw[i:i + 4] == expected and normalized[i:i + 4] == b'\0' * 4]
        require(len(positions) == 1, 'EXACT_TYPED_VERSION_OFFSET_REQUIRED')
        at = positions[0]
        changed = raw[:at] + struct.pack('<I', version) + raw[at + 4:]
        require(normalize_manifest(changed) == (normalized, version), 'MANIFEST_CHANGED_OUTSIDE_VERSION')
        out.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(out, 'w', allowZip64=True) as writer:
            for info in sorted(source.infolist(), key=lambda i: i.filename):
                if info.filename in SIGNATURE:
                    continue
                record = ZipInfo(info.filename, date_time=(2026, 10, 26, 0, 0, 0))
                record.compress_type = info.compress_type
                record.external_attr = info.external_attr
                with writer.open(record, 'w', force_zip64=info.file_size >= 2 ** 31) as target:
                    if info.filename == 'AndroidManifest.xml':
                        target.write(changed)
                    else:
                        with source.open(info) as stream:
                            shutil.copyfileobj(stream, target, 4 * 1024 * 1024)
    return {'status': 'UNSIGNED_REVIEW_ONLY', 'apk_sha256': file_sha(out), 'versionCode': version,
            'runtime_mutations': [], 'manifest_mutation': 'versionCode only', 'isolation_complete': False}


def run(args, env=None):
    result = subprocess.run(list(map(str, args)), text=True, capture_output=True, env=env)
    if result.returncode:
        raise Rejected('TOOL_FAILED:' + Path(str(args[0])).name + ':' + result.stderr[-2000:])
    return result.stdout


def sign(apk, jars, work, repository, expected_head, expected_generation, sdk, out):
    # Every current payload, owner boundary and authority is audited before keys.
    proof = pre_sign(apk, jars, work, repository, expected_head, expected_generation)
    from signer_policy import check
    from inventory import HERE,load
    policy=load(HERE/'signer-policy.json')
    signer_routes=check(policy)
    out, sdk = Path(out), Path(sdk)
    out.mkdir(parents=True, exist_ok=False)
    final = out / ('Infinity-' + str(proof['versionCode']) + '-Combined-Original-Signer.apk')
    with tempfile.TemporaryDirectory(prefix='infinity-combined-sign-') as temporary:
        temp = Path(temporary)
        staged, aligned = temp / 'verified.apk', temp / 'aligned.apk'
        shutil.copyfile(apk, staged)
        require(file_sha(staged) == proof['unsigned_apk_sha256'], 'APK_CHANGED_AFTER_AUDIT')
        run([sdk / 'zipalign', '-P', '16', '-f', '4', staged, aligned])
        # zipalign is allowed to change ZIP layout, never payloads.
        from inventory import apk_members, canonical, digest
        require(apk_members(staged) == apk_members(aligned), 'ALIGNMENT_CHANGED_PAYLOAD')
        registry = remote_authority(repository, expected_head)
        require(digest(canonical(registry)) == proof['registry_sha256'], 'AUTHORITY_CHANGED_BEFORE_SIGN')
        require(check(policy)==signer_routes,'SIGNER_ROUTES_CHANGED')
        key = temp / 'original.jks'
        key.touch(mode=0o600)
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'], validate=True))
        env = {k: os.environ[k] for k in ('PATH', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD')}
        if 'JAVA_HOME' in os.environ:
            env['JAVA_HOME'] = os.environ['JAVA_HOME']
        run([sdk / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', os.environ['INFINITY_KEY_ALIAS'],
             '--ks-pass', 'env:INFINITY_STORE_PASSWORD', '--key-pass', 'env:INFINITY_KEY_PASSWORD',
             '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'true',
             '--out', final, aligned], env)
        cert = run([sdk / 'apksigner', 'verify', '--verbose', '--print-certs', final])
        matches = re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)', cert)
        require(matches == [CERT_SHA], 'PERMANENT_SIGNER_MISMATCH')
        run([sdk / 'zipalign', '-c', '-P', '16', '4', final])
        signed_payload = {k: v for k, v in apk_members(final).items() if k not in SIGNATURE}
        require(signed_payload == apk_members(aligned), 'SIGNED_PAYLOAD_CHANGED')
        # A registry race after signing quarantines the result: no upload step
        # may run until this function succeeds. No automatic acceptance update.
        require(remote_authority(repository, expected_head) == registry, 'AUTHORITY_CHANGED_QUARANTINE_APK')
        require(check(policy)==signer_routes,'SIGNER_ROUTES_CHANGED_QUARANTINE_APK')
        proof.update(signed_apk_sha256=file_sha(final), certificate_sha256=CERT_SHA,
                     physical_Fold='PENDING', accepted_pointer_updated=False)
        save(out / 'BUILD-RECEIPT.json', proof)
        (out / 'SIGNATURE.txt').write_text(cert)
        (out / 'SHA256SUMS').write_text(file_sha(final) + '  ' + final.name + '\n')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--baseline', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--version', required=True, type=int)
    p = commands.add_parser('sign')
    for name in ('apk', 'jars', 'work', 'repository', 'sdk', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--expected-generation', required=True, type=int)
    args = vars(parser.parse_args())
    command = args.pop('command')
    import json
    print(json.dumps((prepare if command == 'prepare' else sign)(**args), indent=2))
