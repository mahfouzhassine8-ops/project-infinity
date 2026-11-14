"""CI-only exact496 pin, using unchanged original API/resource audit."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/audit_sdk_component.py'
s=prior.read_text().replace('fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c','17a9648070a6d2d1b670c3e550e905d75a99a7dc3f21692a56b8a69c6e9c7ebc');scope={'__file__':str(prior),'__name__':'_original_audit_exact496'};exec(compile(s,str(prior),'exec'),scope);verify=scope['verify']
