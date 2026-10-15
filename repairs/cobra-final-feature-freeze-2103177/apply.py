#!/usr/bin/env python3
"""Assemble the auditable 2103177 patch fragments and execute them as one script."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
code="".join((ROOT/"parts"/f"apply.{i:02d}.pyfrag").read_text() for i in range(8))
exec(compile(code,str(ROOT/"assembled-apply.py"),"exec"),globals(),globals())
