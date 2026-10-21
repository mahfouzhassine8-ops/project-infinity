"""Checked native delta over the complete compiled 2103395 source inventory."""
from pathlib import Path
import copy
import json
import os
import sys
import components96 as c
import native95 as prior
from native94 import once, require

CONTRACT = prior.CONTRACT
COORDINATOR = prior.COORDINATOR
CONTAINER = prior.CONTAINER
PATHS = {CONTRACT, COORDINATOR, CONTAINER}
SOURCE95_SHA256 = '681b428e6a80c45d702eaeb79dda22be2d11cd9fb6bbd45f20642e12c2420c25'
old_adapters = prior.old_adapters
module = prior.module


def checked_sources(root, expected):
    require(len(expected) == 9404 and c.sha(json.dumps(expected, sort_keys=True,
        separators=(',', ':')).encode()) == SOURCE95_SHA256, 'exact signed 2103395 native map required')
    for name, pin in expected.items():
        require(c.digest(Path(root) / name) == pin, 'protected source drift ' + name)


def patches(before, original, final):
    require(set(before) == PATHS, 'native corrective scope differs')
    out = dict(before)
    _, release, _ = prior.old_adapters()
    coherence = release.coherence
    previous_pins = json.loads(original[c.UI + '/CONTROLLER-PREIMAGES.json'])
    next_pins = json.loads(final[c.UI + '/CONTROLLER-PREIMAGES.json'])
    require(set(previous_pins) == set(next_pins) and len(next_pins) == 17,
            'all exact controller sources remain mandatory')
    additions = []
    raw = before[CONTRACT]
    for endpoint in (*coherence.ENDPOINTS, 'default.py'):
        matches = [v for v in coherence.contracts(raw.decode())
            if v['script'] == c.CC + '/' + endpoint and
            v['pins'] == {c.CC + '/' + n: h for n, h in previous_pins.items()}]
        require(len(matches) == 1, 'exact signed CC25 variant absent ' + endpoint)
        block = matches[0]['block'].encode()
        for name, pin in previous_pins.items():
            if next_pins[name] != pin:
                block = once(block, pin.encode(), next_pins[name].encode())
        additions.append(block)
    insertion = b'    // INFINITY_2103396_CC26_EXACT_SOURCES\n' + b'\n'.join(additions) + b'\n'
    raw = once(raw, b'  };\n  return *contracts;', insertion + b'  };\n  return *contracts;')
    # Retain both historical memory-only ambient contracts and their exact
    # mapped APK-library check. Add only this reviewed lifecycle revision.
    ambient = c.SKIN + '/resources/lib/infinity_native_ambient.py'
    old_pin = c.sha(original[ambient]).encode()
    new_pin = c.sha(final[ambient]).encode()
    require(old_pin == b'de30a5114302a303638c589342024b348d3070c5aa76ba4a360d2506dd4402f7',
            'unexpected ambient worker preimage')
    raw = once(raw, b'digest == "' + old_pin + b'") &&',
        b'digest == "' + old_pin + b'" ||\n             digest == "' + new_pin + b'") &&')
    out[CONTRACT] = raw
    out[COORDINATOR] = once(before[COORDINATOR],
        b'active["addon_version"].asString() != "0.3.5.25"',
        b'active["addon_version"].asString() != "0.3.5.25" && active["addon_version"].asString() != "0.3.5.26"')
    # The Fold trace combines three conditions. Separate them without changing
    # eligibility, identity proofs, selected item, provider routing or limits.
    # No seventh speculative eligibility repair is included.
    raw = before[CONTAINER]
    needle = b'''  if (path.compare(0, 31, "plugin://plugin.video.umbrella/") != 0 ||
      path.size() > 4096 || label.empty() || label.size() > 512)
    { trace("native.validate","provider_or_metadata_mismatch"); return restore(); }'''
    replacement = b'''  if (path.compare(0, 31, "plugin://plugin.video.umbrella/") != 0)
    { trace("native.validate","provider_mismatch"); return restore(); }
  if (path.size() > 4096)
    { trace("native.validate","provider_path_exceeds_4096"); return restore(); }
  if (label.empty() || label.size() > 512)
    { trace("native.validate","label_empty_or_exceeds_512"); return restore(); }'''
    out[CONTAINER] = once(raw, needle, replacement)
    return out


def bind(producer, parent, stage, source_commit):
    d, _, _ = prior.old_adapters()
    native = producer / 'kodi'
    checkpoint = producer / 'checkpoint-build'
    expected = json.loads((checkpoint / 'FOLD95-NATIVE-SOURCE-MAP.json').read_text())
    checked_sources(native, expected)
    links = d.native_build_inventory(native, expected, Path(os.environ['DEPENDS']))
    original = c.read_parent(parent)
    final = c.components(original)
    require(c.ledger(original, final) == json.loads((c.HERE / 'MEMBER-DELTA.json').read_text()),
            'unreviewed component delta')
    for name, body in final.items():
        require((stage / name).read_bytes() == body, 'component stage mismatch ' + name)
    after = patches({p: (native / p).read_bytes() for p in PATHS}, original, final)
    after_map = dict(expected, **{p: c.sha(b) for p, b in after.items()})
    driver = d.module('targeted96_immutable_driver', producer / 'repairs/four-repair-20261018/native_ci.py')
    ordering = driver.parent.parent.parent.parent.parent.parent.parent
    compiler = Path(ordering.native_manifest(ordering.stable())).resolve()
    paths = [checkpoint / 'FOUR-REPAIR-INPUT-DELTA.json', compiler,
             checkpoint / 'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json']
    locked = json.loads((checkpoint / 'LOCKED-2103384-SOURCE-MAP.json').read_text())
    records = [json.loads(p.read_text()) for p in paths]
    require(len({p.resolve() for p in paths}) == 3 and
        dict(locked, **records[0]['after']) == expected and
        all(v['after'] == expected for v in records[1:]), 'complete compiler ledgers required')
    replacements = {native / p: body for p, body in after.items()}
    for path, record in zip(paths, records):
        value = copy.deepcopy(record)
        value['after'].update({p: after_map[p] for p in PATHS})
        value['changed'] = sorted(set(value.get('changed', [])) | PATHS)
        value['source_commit'] = source_commit
        value['targeted_2103396_delta'] = sorted(PATHS)
        replacements[path] = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    backups = {path: path.read_bytes() for path in replacements}
    try:
        for path, body in replacements.items():
            path.write_bytes(body)
        require(d.native_build_inventory(native, after_map, Path(os.environ['DEPENDS'])) == links,
                'unrelated source or build link drift')
        proof = dict(source_commit=source_commit, parent_source_commit=c.COMMIT,
            original_source_count=9404, final_source_count=9404,
            protected_source_count=9404-len(PATHS),
            before={p: expected[p] for p in sorted(PATHS)},
            after={p: after_map[p] for p in sorted(PATHS)},
            all_other_sources_byte_identical=True, unchanged_build_links=links,
            essential_first_guards_unchanged=True, cobra_changed=False,
            physical_fold_verified=False, final_lock=False,
            option_b_eligibility_changed=False)
        for name, value in [('FOLD96-NATIVE-BINDING.json', proof),
                            ('FOLD96-NATIVE-SOURCE-MAP.json', after_map)]:
            (checkpoint / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
        return proof
    except BaseException:
        for path, body in backups.items():
            path.write_bytes(body)
        raise
