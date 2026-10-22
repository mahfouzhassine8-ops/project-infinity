"""Exercise the actual fixture's VFS actions/checks at Python optimization 0/1/2.

The backend below is a test peer. This verifies fixture execution and refusal of
false success, not Kodi's binding, native durability, or physical device behavior.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    source = (HERE/'android_future_service.py').read_text()
    tree = ast.parse(source)
    if any(isinstance(n, ast.Assert) for n in ast.walk(tree)):
        raise RuntimeError('Fixture contains checks that Python can remove')
    require = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'require')
    begin = source.index('vfs_writes=[]')
    end = source.index('errors=[]', begin)
    selected = ast.Module(body=[require, *ast.parse(source[begin:end]).body], type_ignores=[])
    original = "assert f.write('text') is True\nassert f.write(b'bytes') is True\nassert f.write(bytearray(b'array')) is True\n"
    rows = []
    for optimization in (0, 1, 2):
        for variant in ('original', 'corrected', 'false-result', 'false-success'):
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder)/'state'
                calls = []
                class Backend:
                    def __init__(self): self.handle = open(target, 'w+b', buffering=0)
                    def write(self, payload):
                        calls.append(type(payload).__name__)
                        if variant == 'false-result': return False
                        if variant != 'false-success':
                            self.handle.write(payload.encode() if isinstance(payload, str) else bytes(payload))
                        return True
                    def size(self): return os.fstat(self.handle.fileno()).st_size
                    def seek(self, *args): return self.handle.seek(*args)
                backend = Backend()
                namespace = dict(f=backend, essential_vfs=str(target), os=os, json=json,
                                 xbmc=SimpleNamespace(LOGINFO=1, log=lambda *args:None))
                failed = None
                try:
                    code = compile(original if variant == 'original' else selected,
                                   'actual-fixture-vfs-excerpt', 'exec', optimize=optimization)
                    exec(code, namespace)
                except AssertionError as error:
                    failed = str(error)
                finally:
                    backend.handle.close()
                actual = target.read_text()
                if variant == 'original':
                    expected = 'textbytesarray' if optimization == 0 else ''
                    if failed or actual != expected or len(calls) != (3 if optimization == 0 else 0):
                        raise RuntimeError('Original optimization control differed')
                elif variant == 'corrected':
                    if failed or actual != 'textbytesarray' or calls != ['str', 'bytes', 'bytearray']:
                        raise RuntimeError('Corrected fixture did not perform and verify all writes')
                elif not failed or len(calls) != 1:
                    raise RuntimeError('Fixture accepted a failed or falsely successful write')
                rows.append(dict(optimization=optimization, variant=variant,
                                 write_calls=calls, readback=actual, rejected=failed))
    a.out.write_text(json.dumps(dict(passed=True, scope=__doc__, cases=len(rows),
        fixture_sha256=hashlib.sha256(source.encode()).hexdigest(),
        no_removable_assertions=True, results=rows), indent=2)+'\n')
    print('PASS: 12 fixture execution and false-success controls across optimization 0/1/2')


if __name__ == '__main__': main()
