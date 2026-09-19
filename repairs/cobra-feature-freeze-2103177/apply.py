#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parts=[(ROOT/f'apply-{i}.py.inc').read_text() for i in range(1,5)]
exec(compile(''.join(parts),str(ROOT/'apply-impl.py'),'exec'),globals(),globals())
