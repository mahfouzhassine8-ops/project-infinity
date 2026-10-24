"""Add only exact CC31 source admission; retain every older owner contract."""
import hashlib
import json
from pathlib import Path
import re

CONTRACT='xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
COORDINATOR='xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp'
BEFORE={CONTRACT:'63dbd73b40f7e70ef9360fae8162173b856622af541dcf2f8804ee79c8bb8ca2',
        COORDINATOR:'b364fb388f31e3522b4383484ca5f18e402e58327e8c658ed525b33397a6b094'}
CC='script.infinity.commandcenter'


def once(value,old,new):
    if value.count(old)!=1:raise RuntimeError('Unexpected owner binding preimage')
    return value.replace(old,new)


def bind(source,assets,stage,overlay):
    before={n:(source/n).read_bytes() for n in BEFORE}
    if {n:hashlib.sha256(b).hexdigest() for n,b in before.items()}!=BEFORE:
        raise RuntimeError('Owner inputs differ from passed RC8')
    oldpins=json.loads((assets/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
    pins=json.loads((stage/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
    baseline33=json.loads((Path(__file__).parent/'universal/BASE33-CONTROLLER-PINS.json').read_text())
    baseline34=json.loads((Path(__file__).parent/'performance/BASE34-CONTROLLER-PINS.json').read_text())
    required34=set(baseline33)|{'provider_inventory.py','title_metadata.py','information.py','selection_contract.py','resources/skins/Default/1080i/InfinityInformation.xml'}
    required=required34|{'resources/skins/Default/1080i/InfinityItemOptions.xml'}
    if len(oldpins)!=17 or len(baseline33)!=19 or set(baseline34)!=required34 or len(required34)!=24 or len(required)!=25 or set(pins)!=required:
        raise RuntimeError('Incomplete exact controller inventories')
    parentpins=json.loads((Path(__file__).parent/'tracking/PARENT-CONTROLLER-PINS.json').read_text())
    if len(parentpins)!=19:raise RuntimeError('Signed CC31 contract incomplete')
    text=before[CONTRACT].decode();additions=[]
    pattern=re.compile(r'    \{"(script\.infinity\.commandcenter/[^"\n]+)", "script\.infinity\.commandcenter", "([^"\n]+)", \{\n(.*?)    \}\},',re.S)
    for endpoint in ('service.py','plugin.py','context.py','default.py'):
        matches=[m for m in pattern.finditer(text) if m[1]==CC+'/'+endpoint and
                 dict(re.findall(r'\{"script\.infinity\.commandcenter/([^"\n]+)", "([a-f0-9]{64})"\}',m[3]))==oldpins]
        if len(matches)!=1:raise RuntimeError('Exact original endpoint owner absent: '+endpoint)
        m=matches[0]
        for inventory in (parentpins, json.loads((Path(__file__).parent/'tracking/final-eight/BASE32-CONTROLLER-PINS.json').read_text()), baseline33, baseline34, pins):
            block='    {"'+m[1]+'", "'+CC+'", "'+m[2]+'", {\n'
            block+=''.join('      {"'+CC+'/'+n+'", "'+h+'"},\n' for n,h in sorted(inventory.items()))
            additions.append(block+'    }},')
    addition='    // INFINITY_2103401_SAVED_NAVIGATION_CC31_CC32_CC33_CC34_CC35_EXACT_SOURCES\n'+'\n'.join(additions)+'\n'
    after={CONTRACT:once(text,'  };\n  return *contracts;',addition+'  };\n  return *contracts;').encode(),
           COORDINATOR:once(before[COORDINATOR],b'active["addon_version"].asString() != "0.3.5.29"',
               b'active["addon_version"].asString() != "0.3.5.29" && active["addon_version"].asString() != "0.3.5.31" && active["addon_version"].asString() != "0.3.5.32" && active["addon_version"].asString() != "0.3.5.33" && active["addon_version"].asString() != "0.3.5.34" && active["addon_version"].asString() != "0.3.5.35"')}
    if after[CONTRACT].decode().replace(addition,'',1)!=text:raise RuntimeError('Older source contracts changed')
    for n,b in after.items():
        path=overlay/n
        if path.exists():raise RuntimeError('Owner overlay already exists')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    return {n:dict(original_sha256=BEFORE[n],final_sha256=hashlib.sha256(b).hexdigest(),
        defect='Universal Save for Later deployment ownership',
        justification='Retain CC31/CC32/CC33/CC34 and add exact twenty-five-file CC35 owner contract and matching version; all prior contracts and barriers retained') for n,b in after.items()}
