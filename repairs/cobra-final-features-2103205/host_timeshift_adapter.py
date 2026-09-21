"""Supply one presentation-only collaborator to the immutable 199 host fixture.

The fixture already replaces UI/network/player collaborators. The 205 ticker
adds a visual refresh; this no-op permits the original timeline assertions to
execute without pretending that a host fake verifies Android presentation.
Neither the historical fixture nor candidate production source is rewritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

# Exact 199 fixture after the already-approved 201 and 202 CI adaptations.
# Those stages run earlier in this workflow and are deliberately unchanged.
FIXTURE_SHA256 = 'e927c5133053952b822d381a0883b50d40dd5d63b8d83644d6a08541fe8356d8'
EXTRACTOR_SHA256 = '2cc0588b667ff86411344a1b786e889d1160e54cc2f1d17fed10c2c88a04688b'
ANCHOR = 'private void cobraUpdatePerformanceOverlay(){}'
ADDED = 'private void cobraRefreshVisualEffects(){}'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def cases(text):
    return re.findall(r'\btest\("([^"\n]+)",', text)


def adapt(text):
    if digest(text.encode()) != FIXTURE_SHA256:
        raise RuntimeError('Pinned inherited timeshift fixture drift')
    if text.count(ANCHOR) != 1 or ADDED in text:
        raise RuntimeError('Presentation collaborator anchor drift')
    adapted = text.replace(ANCHOR, ANCHOR + ADDED, 1)
    if adapted.replace(ADDED, '', 1) != text:
        raise RuntimeError('Unreviewed fixture adaptation')
    if cases(text) != cases(adapted) or len(cases(text)) != 14:
        raise RuntimeError('Inherited timeshift case identity drift')
    # The full assertion/main tail, not merely assertion counts, is immutable.
    marker = ' private static void check(boolean value,String message)'
    if text[text.index(marker):] != adapted[adapted.index(marker):]:
        raise RuntimeError('Inherited timeshift assertions changed')
    return adapted


def read_fixture(fixture):
    before = fixture.read_bytes()
    extractor = fixture.resolve().parents[1] / 'apply_timeshift.py'
    if digest(extractor.read_bytes()) != EXTRACTOR_SHA256:
        raise RuntimeError('Pinned inherited member extractor drift')
    return before, adapt(before.decode())


def main(fixture, source, out):
    before, adapted = read_fixture(fixture)
    source_before = source.read_bytes()
    namespace = {'__file__': str(fixture.resolve()), '__name__': 'cobra205_timeshift_fixture'}
    exec(compile(adapted, str(fixture), 'exec'), namespace)
    result = namespace['compile_run'](source, out)
    if fixture.read_bytes() != before or source.read_bytes() != source_before:
        raise RuntimeError('Fixture adapter must not rewrite production or historical source')
    receipt = {
        'kind': 'Host extracted Java fixture adaptation; not Android or physical verification',
        'scope': 'One no-op presentation collaborator; actual ticker and timeline methods unmodified',
        'historical_source_modified': False, 'candidate_source_modified': False,
        'inherited_case_count': 14, 'inherited_case_names': cases(adapted),
        'all_inherited_assertions_byte_identical': True,
        'fixture_sha256': digest(before), 'extractor_sha256': EXTRACTOR_SHA256,
        'adapted_fixture_sha256': digest(adapted.encode()),
        'candidate_source_sha256': digest(source_before),
        'exit_code': result['exit_code'], 'physical_device_verified': False,
    }
    (out / 'fixture-adapter.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    return result['exit_code']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.fixture, args.source, args.out))
