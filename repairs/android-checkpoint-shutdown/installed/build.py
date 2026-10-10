#!/usr/bin/env python3
"""Build code-only installers for exact installed versions from the verified source ZIP."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
VERSIONS = {'script.infinity.commandcenter': '0.3.5.20', 'service.infinity.compat': '0.8.2'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sources(addon):
    parent = {p.name: p.read_bytes() for p in (HERE / 'parent' / addon).iterdir() if p.is_file()}
    final = dict(parent)
    final.update({p.name: p.read_bytes() for p in (HERE / 'overlay' / addon).iterdir() if p.is_file()})
    expected = json.loads((HERE / 'manifest.json').read_text())[addon]
    for label, values in [('before', parent), ('after', final)]:
        if {n: sha(data) for n, data in values.items()} != expected[label]:
            raise ValueError('Installed source preservation mismatch: '+addon+' '+label)
    return parent, final


def build(addon):
    parent, final = sources(addon)
    changed = sorted(n for n in final if parent.get(n) != final[n])
    manifest = dict(schema=1, addon_id=addon, addon_version=VERSIONS[addon],
                    addon_xml_sha256=sha(parent['addon.xml']),
                    files=[dict(path=n, before=sha(parent[n]) if n in parent else None,
                                after=sha(final[n])) for n in changed])
    if addon == 'script.infinity.commandcenter':
        green = json.loads((HERE.parent / 'resume-speed/GREEN-2103362.json').read_text())
        for entry in manifest['files']:
            entry['previous'] = green['commandcenter20'][entry['path']]
    entries = {'manifest.json': (json.dumps(manifest, sort_keys=True, separators=(',', ':'))+'\n').encode()}
    entries.update({'payload/'+n: final[n] for n in changed})
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for n, data in sorted(entries.items()):
            entry = zipfile.ZipInfo(n, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return output.getvalue()


def stage(assets):
    result = {}
    for addon, name in [('script.infinity.commandcenter', 'checkpoint-controller-20.zip'),
                        ('service.infinity.compat', 'checkpoint-compat-82.zip')]:
        data = build(addon)
        target = assets / 'infinity' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        result['assets/infinity/'+name] = sha(data)
    return result


def materialize(target):
    for addon in VERSIONS:
        _, final = sources(addon)
        destination = Path(target) / addon
        destination.mkdir(parents=True, exist_ok=True)
        for name, data in final.items():
            (destination / name).write_bytes(data)
