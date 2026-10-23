"""Stage ONLY the Infinity Save for Later hook and its exact identity contracts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
PLUGIN_SHA='47ce816e00ca30d8eb77ea4d6e034bdbd40b2a5d6c51bfd4eda8d6c75545edb8'


def once(source,before,after):
    if source.count(before)!=1:raise RuntimeError('Plugin preimage occurrence mismatch')
    return source.replace(before,after)


def plugin(raw):
    if hashlib.sha256(raw).hexdigest()!=PLUGIN_SHA:raise RuntimeError('Exact RC8 plugin required')
    value=raw.decode()
    value=once(value,"    target = _target(entry, data.get('sources', {}), render)\n",
        "    target = (_url(action='open-later', key=key) if bucket == 'later' else\n"
        "              _target(entry, data.get('sources', {}), render))\n")
    value=once(value,"    if action == 'play-saved':\n",
        "    if action == 'open-later':\n"
        "        from saved_navigation import open_saved\n"
        "        open_saved(HANDLE, PROFILE, PARAMS.get('key', '')); return\n"
        "    if action == 'play-saved':\n")
    return value.encode()


def stage(source,output,contracts):
    if output.exists():raise RuntimeError('Component stage already exists')
    cc=source/'script.infinity.commandcenter'
    output.mkdir(parents=True)
    changed={'script.infinity.commandcenter/plugin.py':plugin((cc/'plugin.py').read_bytes()),
             'script.infinity.commandcenter/saved_navigation.py':(HERE/'saved_navigation.py').read_bytes(),
             'script.infinity.commandcenter/NAVIGATION-CONTRACTS.json':contracts.read_bytes()}
    # The existing controller verification is kept strict: update its dependent
    # metadata to the exact new sources, without changing either consumer.
    pins=json.loads((source/'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json').read_text())
    if pins.get('plugin.py')!=PLUGIN_SHA:raise RuntimeError('Unexpected controller binding')
    for name,data in changed.items():pins[name.split('/',1)[1]]=hashlib.sha256(data).hexdigest()
    for consumer in ('script.infinity.watchedbridge','script.infinity.uirepair'):
        old=json.loads((source/consumer/'CONTROLLER-PREIMAGES.json').read_text())
        if old.get('plugin.py')!=PLUGIN_SHA:raise RuntimeError('Unexpected dependent controller')
        changed[consumer+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
    ledger={}
    for name,data in changed.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        old=source/name
        ledger[name]=dict(original_sha256=hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None,
                          final_sha256=hashlib.sha256(data).hexdigest(),
                          defect='Universal Save for Later verified navigation',
                          justification='Later-only identity-keyed action, reviewed installed API contracts, exact dependent source bindings')
    return ledger


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--contracts',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.write_text(json.dumps(stage(a.source,a.output,a.contracts),indent=2,sort_keys=True)+'\n')
