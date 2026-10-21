#!/usr/bin/env python3
"""Cause-based 2103394 overlays, after the unchanged verified 2103393 binder.

No protected-writer exception is excused. Every source preimage is checked
against the complete compiled 2103393 source map before applying this layer.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE93_SHA256 = '3101b59ae974d0c8ad83ebbdc0569543dd403fb50325d8eaf686b14a709e1c86'
WINDOW = 'xbmc/interfaces/legacy/Window.cpp'
OBSERVER = 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'


def require(value, reason):
    if not value:
        raise ValueError('2103394 native correction refused: ' + reason)


def once(raw, old, new):
    require(raw.count(old) == 1, 'missing or ambiguous source anchor: ' + repr(old[:100]))
    return raw.replace(old, new, 1)


def window_language_hook(raw):
    """Preserve a wrapped control's actual window/interpreter ownership.

    SWIG sets the thread-local hook for constructors and free functions, but
    not ordinary member methods. Window.getControl creates ControlList wrappers
    from a member call. Without its parent hook, the wrapper later enters
    GuiLock with no hook and retains the GIL while acquiring the frame guard.
    The observed ControlList.getSelectedItem waiter closes the captured cycle.
    """
    raw = once(raw, b'#include "Window.h"',
               b'#include "Window.h"\n#if defined(TARGET_ANDROID)\n'
               b'#include "interfaces/legacy/ModuleXbmc.h"\n#include <memory>\n#endif')
    old = b'''    Control* Window::getControl(int iControlId)
    {
      XBMC_TRACE;
      DelayedCallGuard dg(languageHook);
      return GetControlById(iControlId,&CServiceBroker::GetWinSystem()->GetGfxContext());
    }'''
    new = b'''    Control* Window::getControl(int iControlId)
    {
      XBMC_TRACE;
      // INFINITY_2103394_CONTROL_LANGUAGE_HOOK: a wrapper created by this
      // member call must inherit the same interpreter hook as its real window.
      // Later ControlList GUI calls can then release their GIL before taking
      // frame/graphics locks. Do not change Cobra or other skins' paths.
#if defined(TARGET_ANDROID)
      std::unique_ptr<XBMCAddon::SetLanguageHookGuard> infinityControlHook;
      if (XBMCAddon::xbmc::getSkinDir() == "skin.infinity.diggz" &&
          languageHook != nullptr && XBMCAddon::LanguageHook::GetLanguageHook() == nullptr)
        infinityControlHook = std::make_unique<XBMCAddon::SetLanguageHookGuard>(languageHook);
#endif
      DelayedCallGuard dg(languageHook);
      return GetControlById(iControlId,&CServiceBroker::GetWinSystem()->GetGfxContext());
    }'''
    return once(raw, old, new)


def observer_detail(raw):
    """Add bounded exception facts to the original sticky native failure.

    Do not include exception messages, SQL, arguments, media titles or full
    paths. Build the traceback from objects already in memory: no imports,
    files, network, background recorder, or new persistence owner is needed.
    """
    old = b"        if target is not None and self.protect is not None and operation in (\n"
    new = b'''        # INFINITY_2103394_FAILURE_CONTEXT: preserve the original exception
        # and all native admission failures; diagnostic gaps never grant safety.
        try:
            error = sys.exc_info()[1]
            if error is not None:
                facts = ['exception=' + type(error).__name__[:80]]
                for field in ('errno', 'sqlite_errorcode'):
                    value = getattr(error, field, None)
                    if type(value) is int:
                        facts.append(field + '=' + str(value))
                frames, tb = [], error.__traceback__
                while tb is not None:
                    code = tb.tb_frame.f_code
                    # Keep only module basenames and identifier-shaped symbols.
                    # No locals, message, URL, title, SQL or private directory.
                    name = str(code.co_filename).replace('\\\\', '/').rsplit('/', 1)[-1]
                    name = name if name.endswith('.py') and all(
                        c.isalnum() or c in '_.-' for c in name) else '<observer>'
                    symbol = str(code.co_name)
                    symbol = symbol if all(c.isalnum() or c == '_' for c in symbol) else '<call>'
                    frames.append(name[:80] + ':' + str(tb.tb_lineno) + ':' + symbol[:80])
                    tb = tb.tb_next
                facts.append('stack=' + ('>'.join(frames[-8:]) if frames else '<missing>'))
                detail = (detail + ';' if detail else '') + ';'.join(facts)
        except Exception:
            detail = (detail + ';' if detail else '') + 'exception_detail_unavailable'
        detail = detail[:1600]
''' + old
    return once(raw, old, new)


def checked_sources(root, expected):
    require(len(expected) == 9404 and hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()).hexdigest() == SOURCE93_SHA256, 'the exact complete signed-baseline source map is mandatory')
    for name, pin in expected.items():
        path = Path(root) / name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == pin,
                'protected native source drift: ' + name)

CONTRACT='xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
COORDINATOR='xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp'
PATHS={WINDOW,OBSERVER,CONTRACT,COORDINATOR,'xbmc/guilib/GUIBaseContainer.cpp',
       'xbmc/guilib/GUIBaseContainer.h','xbmc/input/InputManager.cpp','xbmc/guilib/GUIWindow.cpp',
       'xbmc/guilib/GUIListLabel.cpp','xbmc/interfaces/generic/ScriptRunner.cpp',
       'xbmc/interfaces/generic/ScriptRunner.h','xbmc/filesystem/PluginDirectory.cpp'}


def previous():
    import importlib.util,sys
    path=HERE.parent/'fold-corrective-2103393/native93.py'
    spec=importlib.util.spec_from_file_location('_infinity_native93',path)
    module=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(path.parent));spec.loader.exec_module(module)
    return module


def classifier(raw,original,final):
    import components94 as c
    _,r,_=previous().old_adapters();coherence=r.coherence
    before=json.loads(original[c.UI+'/CONTROLLER-PREIMAGES.json'])
    pins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
    require(len(before)==13 and len(pins)==16 and set(before)<=set(pins),'complete CC24 sources required')
    additions=[]
    for endpoint in coherence.ENDPOINTS:
        variants=[v for v in coherence.contracts(raw.decode()) if v['script']==c.CC+'/'+endpoint and
                  v['pins']=={c.CC+'/'+n:h for n,h in before.items()}]
        require(len(variants)==1,'signed CC23 classifier missing '+endpoint)
        block=variants[0]['block'].encode()
        for name,pin in before.items():
            if pins[name]!=pin:block=once(block,pin.encode(),pins[name].encode())
        extra=b''.join(('      {"'+c.CC+'/'+name+'", "'+pins[name]+'"},\n').encode()
                       for name in sorted(set(pins)-set(before)))
        block=once(block,b'    }},',extra+b'    }},')
        additions.append(block)
        if endpoint=='plugin.py':
            # On-demand Settings/Search now use the exact same admitted client
            # lease as plugin/context invocations, with all sixteen code pins.
            additions.append(once(block,('    {"'+c.CC+'/plugin.py", "'+c.CC+'", "command_center_client", {').encode(),
                                        ('    {"'+c.CC+'/default.py", "'+c.CC+'", "command_center_client", {').encode()))
    insertion=b'    // INFINITY_2103394_CC24_EXACT_SOURCES\n'+b'\n'.join(additions)+b'\n'
    result=once(raw,b'  };\n  return *contracts;',insertion+b'  };\n  return *contracts;')
    require(result.replace(insertion,b'',1)==raw,'legacy classifiers altered')
    hashes={n:c.sha(b) for n,b in final.items()}
    for endpoint in (*coherence.ENDPOINTS,'default.py'):
        variants=coherence.matching_variants(result.decode(),c.CC,c.CC+'/'+endpoint,hashes)
        require(len(variants)==1 and len(variants[0]['pins'])==16,'incomplete CC24 endpoint '+endpoint)
    return result


def patches(before,original,final):
    import input94,search_native94
    require(set(before)==PATHS,'unexpected native delta scope')
    out=input94.patches(search_native94.patches(before))
    out[WINDOW]=window_language_hook(before[WINDOW])
    out[OBSERVER]=observer_detail(before[OBSERVER])
    out[CONTRACT]=classifier(before[CONTRACT],original,final)
    test=b'active["addon_version"].asString() != "0.3.5.23"'
    out[COORDINATOR]=once(before[COORDINATOR],test,test+b' && active["addon_version"].asString() != "0.3.5.24"')
    require({p for p in out if out[p]!=before[p]}==PATHS,'incomplete native correction')
    return out


def compiler_plan(expected,locked,delta,compiler_maps,after_map,source_commit):
    import copy,re
    require(re.fullmatch('[0-9a-f]{40}',source_commit),'full source commit required')
    require(len(expected)==len(locked)==9404 and set(expected)==set(locked),'full inventory required')
    require(delta.get('source_file_count')==9404 and dict(locked,**delta['after'])==expected,
            'sparse compiled-source ledger mismatch')
    require(set(delta.get('fold_corrective_2103393_delta',[]))==previous().PATHS,
            'signed 2103393 native corrections missing')
    require(len(delta.get('group7_extra_native_delta',[]))==8,'seven-group deltas missing')
    require(set(after_map)==set(expected) and {p for p in expected if expected[p]!=after_map[p]}==PATHS,
            'unapproved source change')
    require(len(compiler_maps)==2 and all(v.get('after')==expected for v in compiler_maps),
            'both complete compiler ledgers required')
    result=[]
    for record in [delta]+list(compiler_maps):
        value=copy.deepcopy(record)
        value['after'].update({p:after_map[p] for p in PATHS})
        value['changed']=sorted(set(value.get('changed',[]))|PATHS)
        value['source_commit']=source_commit
        value['fold_corrective_2103394_delta']=sorted(PATHS)
        result.append(value)
    require(dict(locked,**result[0]['after'])==after_map and all(v['after']==after_map for v in result[1:]),
            'full compiler verification changed')
    return result


def bind(producer,parent,stage,source_commit):
    import os
    import components94 as c
    n=previous();d,_,_=n.old_adapters()
    native=producer/'kodi';checkpoint=producer/'checkpoint-build'
    expected=json.loads((checkpoint/'FOLD93-NATIVE-SOURCE-MAP.json').read_text())
    checked_sources(native,expected)
    links=d.native_build_inventory(native,expected,Path(os.environ['DEPENDS']))
    original=c.read_parent(parent);final=c.components(original)
    require(c.ledger(original,final)==json.loads((HERE/'MEMBER-DELTA.json').read_text()),'unreviewed component delta')
    for name,body in final.items():require((stage/name).read_bytes()==body,'staged component drift: '+name)
    before={p:(native/p).read_bytes() for p in PATHS};after=patches(before,original,final)
    after_map=dict(expected,**{p:c.sha(b) for p,b in after.items()})
    driver=d.module('corrective94_immutable_driver',producer/'repairs/four-repair-20261018/native_ci.py')
    ordering=driver.parent.parent.parent.parent.parent.parent.parent
    compiler=Path(ordering.native_manifest(ordering.stable())).resolve()
    paths=[checkpoint/'FOUR-REPAIR-INPUT-DELTA.json',compiler,checkpoint/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json']
    require(len({p.resolve() for p in paths})==3,'distinct compiler ledgers required')
    locked=json.loads((checkpoint/'LOCKED-2103384-SOURCE-MAP.json').read_text())
    records=[json.loads(p.read_text()) for p in paths]
    updated=compiler_plan(expected,locked,records[0],records[1:],after_map,source_commit)
    replacements={native/p:b for p,b in after.items()}
    replacements.update({p:(json.dumps(v,indent=2,sort_keys=True)+'\n').encode() for p,v in zip(paths,updated,strict=True)})
    backup={p:p.read_bytes() for p in replacements};rollback=checkpoint/'FOLD94-ORIGINAL-INPUTS'
    require(not rollback.exists(),'native correction already applied');rollback.mkdir()
    for index,body in enumerate(backup.values()):(rollback/(str(index)+'.original')).write_bytes(body)
    n.save(rollback/'INDEX.json',{str(i):{'path':str(p),'sha256':c.sha(b)} for i,(p,b) in enumerate(backup.items())})
    try:
        for p,b in replacements.items():p.write_bytes(b)
        require(d.native_build_inventory(native,after_map,Path(os.environ['DEPENDS']))==links,'build links or other source changed')
        proof=dict(source_commit=source_commit,parent_source_commit=c.COMMIT,
                   original_source_count=9404,final_source_count=9404,protected_source_count=9404-len(PATHS),
                   before={p:expected[p] for p in sorted(PATHS)},after={p:after_map[p] for p in sorted(PATHS)},
                   all_other_sources_byte_identical=True,unchanged_build_links=links,
                   essential_first_guards_unchanged=True,cobra_changed=False,physical_fold_verified=False,
                   original_sigsegv_fixed=False,final_lock=False)
        n.save(checkpoint/'FOLD94-NATIVE-BINDING.json',proof)
        n.save(checkpoint/'FOLD94-NATIVE-SOURCE-MAP.json',after_map)
        return proof
    except BaseException:
        for p,b in backup.items():p.write_bytes(b)
        raise


def old_adapters():return previous().old_adapters()
def module(name,path):return previous().module(name,path)
