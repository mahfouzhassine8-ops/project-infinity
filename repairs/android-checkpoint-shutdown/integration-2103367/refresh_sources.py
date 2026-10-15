"""Refresh exact generated postimage pins without replacing protected preimages."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, row):
    path.write_text(json.dumps(row, indent=2, sort_keys=True) + '\n')


def runtime(group):
    folder = ROOT / 'runtime' / group
    path = folder / 'manifest.json'
    row = json.loads(path.read_text())
    for source in (folder / 'overlay').rglob('*'):
        if source.is_file() and '__pycache__' not in source.parts:
            row['after'][source.relative_to(folder / 'overlay').as_posix()] = digest(source.read_bytes())
    row['changed'] = sorted(name for name in row['after'] if row['before'].get(name) != row['after'][name])
    row['added'] = sorted(set(row['after']) - set(row['before']))
    assert not row['deleted']
    write_json(path, row)
    return row


def main():
    bundled = runtime('commandcenter')['after']
    path = ROOT / 'installed/manifest.json'
    row = json.loads(path.read_text())
    for addon, values in row.items():
        for source in (ROOT / 'installed/overlay' / addon).iterdir():
            if source.is_file():
                values['after'][source.name] = digest(source.read_bytes())
        values['changed'] = sorted(n for n in values['after'] if values['before'].get(n) != values['after'][n])
        if 'added' in values:
            values['added'] = sorted(set(values['after']) - set(values['before']))
    write_json(path, row)
    installed = row['script.infinity.commandcenter']['after']
    path = ROOT / 'runtime/native/overlay/xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
    source = path.read_text()
    pattern = r'    \{"script\.infinity\.commandcenter/(?:service|plugin|context)\.py",.*?\n    \}\},'
    blocks = re.findall(pattern, source, re.S)
    # Both supported families retain separate exact source vectors.
    families = [bundled, installed]
    family_index = 0
    new = []
    for block in blocks:
        if '/context.py"' in block.split('\n', 1)[0]:
            continue
        if '/service.py"' in block.split('\n', 1)[0]:
            family_index = 0 if not new else 1
        pins = families[family_index]
        block = re.sub(r'(\{"script\.infinity\.commandcenter/([^"\n]+)", ")[0-9a-f]{64}("\})',
                       lambda m: m[1] + pins[m[2]] + m[3], block)
        if not re.search(r'\{"script\.infinity\.commandcenter/context.py",', block):
            block = block.replace('\n    }},', '\n      {"script.infinity.commandcenter/context.py", "' + pins['context.py'] + '"},\n    }},')
        new.append(block)
        if '/plugin.py"' in block.split('\n', 1)[0]:
            new.append(block.replace('commandcenter/plugin.py", "script.infinity.commandcenter",',
                                     'commandcenter/context.py", "script.infinity.commandcenter",', 1))
    iterator = iter(new)
    # Replace old groups as a pair so intervening non-CC contracts stay in place.
    def replace(match):
        block = match[0]
        if '/context.py"' in block.split('\n', 1)[0]:
            return ''
        replacement = next(iterator)
        if '/plugin.py"' in block.split('\n', 1)[0]:
            replacement += '\n' + next(iterator)
        return replacement
    source = re.sub(pattern, replace, source, flags=re.S)
    source = re.sub(r'(    \}\},\n)\n+', r'\1', source)
    path.write_text(source)
    sys.path.insert(0, str(ROOT))
    import participant_asset
    builder = runpy.run_path(str(ROOT / 'installed/build.py'))
    android = ROOT / 'runtime/android/overlay/tools/android/packaging/xbmc/src'
    for name, payload in [('InfinityCheckpointAddonInstaller.java.in', participant_asset.build()),
                          ('InfinityCheckpointController20Installer.java.in', builder['build']('script.infinity.commandcenter'))]:
        path = android / name
        path.write_text(re.sub(r'(private static final String ASSET_SHA256 = ")[0-9a-f]{64}(";)',
                               lambda m: m[1] + digest(payload) + m[2], path.read_text()))
    path = android / 'InfinityInstalledCheckpointInstaller.java.in'
    source = path.read_text().replace('if(CC20.equals(cc))', 'if(CC20.equals(cc)||CC20_CONTEXT.equals(cc))')
    source = re.sub(r'  private static final String CC20_CONTEXT="[0-9a-f]{64}";\n', '', source)
    source = source.replace('  private static final String CC20=',
                            '  private static final String CC20_CONTEXT="' + installed['addon.xml'] + '";\n  private static final String CC20=')
    path.write_text(source)
    runtime('native')
    runtime('android')
    print('Updated exact CC19/CC20, native classifier and Android asset postimages; original preimages retained')


if __name__ == '__main__':
    main()
