"""Avoid the proved disabled-addon constructor exception; preserve defaults."""
import hashlib
import json
from pathlib import Path

CC='script.infinity.commandcenter'
ROOT=Path(__file__).parent


def patch(name,raw):
    pins=json.loads((ROOT/'REFRESH-ENABLED-414-PLAN.json').read_text())['source_preimages']
    if hashlib.sha256(raw).hexdigest()!=pins.get(name):
        raise ValueError('Exact signed413 refresh source required')
    text=raw.decode()
    if name=='addon.xml':old,new='version="0.3.5.43"','version="0.3.5.44"'
    elif name in ('default.py','service.py'):
        old='System.HasAddon(service.infinity.refresh)'
        new='System.AddonIsEnabled(service.infinity.refresh)'
    else:raise ValueError('Unowned disabled-refresh source')
    if text.count(old)!=1:raise ValueError('Original refresh guard boundary differs')
    result=text.replace(old,new,1)
    if result.replace(new,old,1)!=text:raise ValueError('Unrelated source changed')
    if name.endswith('.py'):compile(result,name,'exec',dont_inherit=True)
    return result.encode()
