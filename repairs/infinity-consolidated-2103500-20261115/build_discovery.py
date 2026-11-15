"""Reuse the existing private Cast builder/auditor against exact signed500.

Only a CI component/probe is produced. No owner installer, version allocation,
native replacement or release signing occurs here.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CAST = ROOT / 'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
BASE = '224d5f808587ce4004a96a003331abe7c71cbe7bd08ec6b1d3ec288c6c75cf40'
OLD_PIN = 'fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c'


def main():
    mode = sys.argv.pop(1)
    sys.path.insert(0, str(CAST))
    if mode == 'component':
        import audit_sdk_component
        assert audit_sdk_component.BASE == OLD_PIN
        audit_sdk_component.BASE = BASE
        source = CAST / 'build_sdk_component.py'
        code = source.read_text()
        assert OLD_PIN in code
        code = code.replace(OLD_PIN, BASE)
    elif mode == 'probe':
        source = CAST / 'build_probe.py'
        code = source.read_text()
        target = "list((HERE/'android').glob('*.java'))"
        assert code.count(target) == 1
        code = code.replace(target, "list((Path(" + repr(str(HERE)) + ")/'android').glob('*.java'))")
    else:
        raise ValueError('component or probe required')
    exec(compile(code, str(source), 'exec'), {'__file__': str(source), '__name__': '__main__'})


if __name__ == '__main__':
    main()
