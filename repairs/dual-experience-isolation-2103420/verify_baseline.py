"""Actual APK checks plus explicit blocked-signing control; no runtime tests."""
import argparse
import json
from pathlib import Path
import re
import tempfile

from inventory import APK_SHA, CERT_SHA, HERE, apk_members, file_sha, load, save
from release_gate import inspect_candidate, verify_approved_payload, verify_combination, Rejected
from assemble import run


def verify(apk, jars, sdk, out):
    if file_sha(apk) != APK_SHA:
        raise ValueError('Exact approved APK required')
    registry = load(HERE / 'accepted-combined-release.json')
    signature = run([Path(sdk) / 'apksigner', 'verify', '--verbose', '--print-certs', apk])
    if re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)', signature) != [CERT_SHA]:
        raise ValueError('Permanent signer mismatch')
    with tempfile.TemporaryDirectory(prefix='infinity-baseline-audit-') as tmp:
        payload, version = inspect_candidate(apk, jars, Path(tmp) / 'dex')
    if version != 2103420:
        raise ValueError('Wrong baseline version')
    verify_approved_payload(registry, payload)
    # This does not claim a2103421 APK exists. It shows even a monotonically
    # higher package version cannot get permission with unresolved boundaries.
    try:
        verify_combination(registry, payload, version + 1, registry['generation'])
    except Rejected as exc:
        if str(exc) != 'UNRESOLVED_RELEASE_BLOCKERS':
            raise
        refusal = str(exc)
    else:
        raise ValueError('Isolation blocker was bypassed')
    result = {'status': 'PASS_BASELINE_FINGERPRINTS_AND_EXPECTED_SIGNING_REFUSAL',
              'apk_sha256': APK_SHA, 'certificate_sha256': CERT_SHA, 'versionCode': version,
              'payload_identities_verified': len(payload), 'signing_refusal': refusal,
              'signed_candidate_produced': False, 'application_tests': 'NOT_RUN', 'shutdown_tests': 'NOT_RUN'}
    save(out, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'jars', 'sdk', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    print(json.dumps(verify(**vars(parser.parse_args())), indent=2))
