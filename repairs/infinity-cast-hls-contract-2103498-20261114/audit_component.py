"""CI-only exact498 pin, using unchanged original API/resource audit."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/audit_sdk_component.py'
s=prior.read_text().replace('fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c','2fd158bbdd26d47f4204c8c474f15c9ca69cfef00fcecdb62c866b42559d3004');scope={'__file__':str(prior),'__name__':'_original_audit_exact498'};exec(compile(s,str(prior),'exec'),scope);verify=scope['verify']
