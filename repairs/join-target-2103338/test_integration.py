#!/usr/bin/env python3
"""Exercise diagnostic integration and reject input drift without compiling Android."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('join_diagnostic_native_test', HERE / 'native_ci.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

def fixture(root, tag='infinity-shutdown-2103334-v1'):
    shutil.copytree(HERE / 'diagnostic/parent', root)
    trace = root / native.TRACE
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text('/* fixture trace identity only */\nconst char* tag="' + tag + '";\n')
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}

def check():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        source = folder / 'source'
        before = fixture(source)
        result = native.apply_diagnostic(source, before, folder / 'output')
        assert result['before'] == before and len(result['changed']) == 4
        assert len(result['after']) == len(before) + 1
        native.verify(source, result['after'])
        for name in ('LanguageInvokerThread.cpp', 'LanguageInvokerThread.h', 'InfinityInvokerTarget.h'):
            assert (source / 'xbmc/interfaces/generic' / name).read_bytes() == (
                HERE / 'diagnostic/prepared/xbmc/interfaces/generic' / name).read_bytes()
        assert native.TAG in (source / native.TRACE).read_text()
        for name in before:
            assert result['after'][name] != before[name]
        assert json.loads((folder / 'output/SOURCE-MANIFEST.json').read_text()) == result
        drift = folder / 'drift'
        expected = fixture(drift)
        path = drift / 'xbmc/interfaces/generic/LanguageInvokerThread.cpp'
        path.write_text(path.read_text() + '\n// changed parent\n')
        original = path.read_bytes()
        try:
            native.apply_diagnostic(drift, expected, folder / 'reject')
        except ValueError:
            pass
        else:
            raise AssertionError('Changed source parent was admitted')
        assert path.read_bytes() == original and not (folder / 'reject').exists()
        wrong_tag = folder / 'wrong-tag'
        expected = fixture(wrong_tag, 'unrecognized-engine')
        path = wrong_tag / 'xbmc/interfaces/generic/LanguageInvokerThread.cpp'
        original = path.read_bytes()
        try:
            native.apply_diagnostic(wrong_tag, expected, folder / 'reject-tag')
        except ValueError:
            pass
        else:
            raise AssertionError('Unrecognized engine identity was admitted')
        assert path.read_bytes() == original
        assert not (wrong_tag / 'xbmc/interfaces/generic/InfinityInvokerTarget.h').exists()
    print('PASS: exact prepared files integrated; source drift and wrong engine tag rejected before source mutation')

if __name__ == '__main__':
    check()
