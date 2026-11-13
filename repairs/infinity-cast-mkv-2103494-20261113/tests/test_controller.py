"""Reuse the protected94 controller contracts for the one changed duration hook."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
prior=ROOT/'repairs/infinity-cast-from-2103492-20261112/tests/test_session_cleanup.py'
source=prior.read_text();prefix,tail=source.split('with tempfile.TemporaryDirectory',1)
scope={'__file__':str(prior),'__name__':'__main__'};exec(compile(prefix,str(prior),'exec'),scope)
key='com/projectinfinity/kodi/InfinityCastRelay'
scope['STUBS'][key]=scope['STUBS'][key].replace('String address(){','long durationMs(){return 0;}String address(){')
exec(compile('with tempfile.TemporaryDirectory'+tail,str(prior),'exec'),scope)
