"""Selected CC35 component, exact CC34 preservation and owner admission checks."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
REPAIR=HERE.parent
CC='script.infinity.commandcenter'


def sha(raw):return hashlib.sha256(raw).hexdigest()

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def run(source,reference,final,native_reference,out):
    component=module('performance_component_contract',REPAIR/'component_contract.py')
    owner=module('performance_owner_binding',REPAIR/'owner_binding.py')
    baseline=json.loads((HERE/'BASE34-CONTROLLER-PINS.json').read_text())
    assert len(baseline)==24
    assert all(sha((reference/CC/n).read_bytes())==h for n,h in baseline.items())
    required=set(baseline)|{'resources/skins/Default/1080i/InfinityItemOptions.xml'}
    pins=json.loads((final/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
    assert len(required)==25 and set(pins)==required
    assert pins==json.loads((final/'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json').read_text())
    assert pins=={n:sha((final/CC/n).read_bytes()) for n in required}
    for addon,(_,version) in component.VERSIONS.items():
        assert ET.parse(final/addon/'addon.xml').getroot().get('version')==version
    generated={a+'/addon.xml' for a in component.VERSIONS}|{
        CC+'/checkpoint_runtime.py',CC+'/infinity_trakt.py',
        'script.infinity.watchedbridge/controller.py',
        'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json',
        'script.infinity.uirepair/CONTROLLER-PREIMAGES.json'}
    allowed=set(json.loads((HERE/'OVERLAY-PREIMAGES.json').read_text()))|generated
    preserved=0
    oldfiles={p.relative_to(reference).as_posix() for p in reference.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    newfiles={p.relative_to(final).as_posix() for p in final.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    assert oldfiles==newfiles, 'Performance release must not add/delete runtime files'
    for n in oldfiles-allowed:
        assert (reference/n).read_bytes()==(final/n).read_bytes(),'Protected signed34 file changed: '+n
        preserved+=1
    assert (reference/CC/'saved_navigation.py').read_bytes()==(final/CC/'saved_navigation.py').read_bytes()
    # Run the real source verifier; each exact admission is independently tampered.
    tree=ast.parse((final/'script.infinity.watchedbridge/controller.py').read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('UnsupportedController','verify')]
    ns={'hashlib':hashlib,'json':json,'Path':Path,'ET':ET,'__file__':str(final/'script.infinity.watchedbridge/controller.py')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'controller.verify','exec'),ns)
    assert ns['verify'](final/CC)==(final/CC).resolve()
    for n in sorted(pins):
        p=final/CC/n;raw=p.read_bytes();p.write_bytes(raw+b'\n')
        try:
            try:ns['verify'](final/CC)
            except ns['UnsupportedController']:pass
            else:raise AssertionError('Tampered source admitted: '+n)
        finally:p.write_bytes(raw)
    tree=ast.parse((final/CC/'infinity_trakt.py').read_text())
    binding=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BRIDGE_PINS' for t in n.targets))
    bridge=ast.literal_eval(binding.value)
    assert all(sha((final/'script.infinity.watchedbridge'/n).read_bytes())==h for n,h in bridge.items())
    # Recover original RC8 bytes from already authenticated signed33 owner files;
    # require exact original digest before applying the current five admissions.
    with tempfile.TemporaryDirectory(prefix='infinity-perf-owner-') as tmp:
        tmp=Path(tmp);native=tmp/'native';overlay=tmp/'overlay'
        for n in owner.BEFORE:
            raw=(native_reference/n).read_bytes()
            if n==owner.CONTRACT:
                start=raw.index(b'    // INFINITY_2103401_SAVED_NAVIGATION_CC31_CC32_CC33_EXACT_SOURCES\n')
                end=raw.index(b'  };\n  return *contracts;',start);raw=raw[:start]+raw[end:]
            else:
                for v in ('0.3.5.31','0.3.5.32','0.3.5.33'):
                    text=(' && active["addon_version"].asString() != "'+v+'"').encode()
                    assert raw.count(text)==1;raw=raw.replace(text,b'',1)
            assert sha(raw)==owner.BEFORE[n]
            p=native/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        ledger=owner.bind(native,source,final,overlay);assert set(ledger)==set(owner.BEFORE)
        text=(overlay/owner.CONTRACT).read_text()
        start=text.index('    // INFINITY_2103401_SAVED_NAVIGATION_CC31_CC32_CC33_CC34_CC35_EXACT_SOURCES\n')
        end=text.index('  };\n  return *contracts;',start)
        assert (text[:start]+text[end:]).encode()==(native/owner.CONTRACT).read_bytes()
        histories=[REPAIR/'tracking/PARENT-CONTROLLER-PINS.json',REPAIR/'tracking/final-eight/BASE32-CONTROLLER-PINS.json',REPAIR/'universal/BASE33-CONTROLLER-PINS.json',HERE/'BASE34-CONTROLLER-PINS.json']
        for inventory in [json.loads(p.read_text()) for p in histories]+[pins]:
            block=''.join('      {"'+CC+'/'+n+'", "'+h+'"},\n' for n,h in sorted(inventory.items()))
            assert text[start:end].count(block)==4
        coordinator=(overlay/owner.COORDINATOR).read_bytes()
        for v in ('0.3.5.31','0.3.5.32','0.3.5.33','0.3.5.34','0.3.5.35'):
            part=(' && active["addon_version"].asString() != "'+v+'"').encode()
            assert coordinator.count(part)==1;coordinator=coordinator.replace(part,b'',1)
        assert coordinator==(native/owner.COORDINATOR).read_bytes()
    report=dict(host='PASS',scope='actual staged CC35 sources and source-verifier functions; no Kodi runtime',
        CC34_original_inventory_retained=True,CC35_named_source_count=25,individual_tamper_rejections=25,
        reference_files_byte_preserved=preserved,TrackIt_entire_saved_navigation_byte_identical=True,
        reciprocal_bridge_UI_pins=True,prior_native_contracts_byte_identical=True,
        versions={a:v[1] for a,v in component.VERSIONS.items()},android='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN; independent')
    out.write_text(json.dumps(report,indent=2)+'\n');return report
