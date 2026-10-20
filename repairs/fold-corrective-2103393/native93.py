#!/usr/bin/env python3
"""Bind the minimal corrective delta AFTER the unchanged 9404-file 2103392 binder.

The original producer, build links, source verification and compiler are reused.
Every unrelated source, classifier variant and Essential-First guard is retained.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import corrective as c

CONTRACT = 'xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
COORDINATOR = 'xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp'
CONTAINER = 'xbmc/guilib/GUIBaseContainer.cpp'
INPUT = 'xbmc/input/InputManager.cpp'
WINDOW = 'xbmc/guilib/GUIWindow.cpp'
PATHS = {CONTRACT,COORDINATOR,CONTAINER,INPUT,WINDOW}
MARKER = b'    // FOLD_CORRECTIVE_CC23_EXACT_IDENTITY_V1\n'

def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj
    before=sys.path[:]
    try:
        sys.path.insert(0,str(Path(path).parent));spec.loader.exec_module(obj)
    finally:
        sys.path[:]=before
    return obj

def old_adapters():
    path=c.ROOT/'repairs/2103390-bugfixes/group7/finish92'
    sys.path.insert(0,str(path))
    import delivery92, release, integration
    return delivery92,release,integration

def classifier(raw, original, final):
    d,r,i=old_adapters()
    c.require(c.sha(raw)==i.FINAL_NATIVE[CONTRACT], 'wrong complete CC22 classifier')
    coherence=r.coherence
    before_pins=json.loads(original[c.UI+'/CONTROLLER-PREIMAGES.json'])
    after_pins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
    c.require(len(before_pins)==len(after_pins)==13, 'incomplete CC classifier')
    additions=[]
    for endpoint in coherence.ENDPOINTS:
        variants=[v for v in coherence.contracts(raw.decode()) if v['script']==c.CC+'/'+endpoint and
                  v['pins']=={c.CC+'/'+n:h for n,h in before_pins.items()}]
        c.require(len(variants)==1, 'ambiguous complete CC22 classifier endpoint '+endpoint)
        block=variants[0]['block'].encode()
        for name,pin in before_pins.items():
            if after_pins[name]!=pin:
                block=c.once(block,pin.encode(),after_pins[name].encode())
        additions.append(block)
    insertion=MARKER+b'\n'.join(additions)+b'\n'
    anchor=b'  };\n  return *contracts;'
    after=c.once(raw,anchor,insertion+anchor)
    c.require(after.replace(insertion,b'',1)==raw, 'legacy classifier modified')
    for endpoint in coherence.ENDPOINTS:
        variants=coherence.matching_variants(after.decode(),c.CC,c.CC+'/'+endpoint,
                     {n:c.sha(b) for n,b in final.items()})
        c.require(len(variants)==1 and len(variants[0]['pins'])==13, 'CC23 classification incomplete')
    return after

def patches(before, original, final):
    c.require(set(before)==PATHS, 'wrong native correction scope')
    after=dict(before)
    old=module('corrective93_original_option_b',c.ROOT/'repairs/2103390-bugfixes/group3/native_option_b_patch.py')
    method=old.METHOD.encode()
    updated=c.once(method,b'(GetID() != 8101 && GetID() != 8102)',
        b'(GetID() != 8101 && GetID() != 8102 && GetID() != 8601 && GetID() != 8602 &&\n'
        b'       GetID() != 8701 && GetID() != 8702 && GetID() != 8801 && GetID() != 8802)')
    # Android's ACTION_DOWN gesture query sets m_waitForScrollEnd before any
    # actual movement. Rejecting that pending query also rejected stationary
    # holds. Preserve the m_gestureActive rejection for real panning; the
    # successful isolated hold already clears m_waitForScrollEnd below.
    updated=c.once(updated,b'!HasProcessed() || m_gestureActive || m_waitForScrollEnd)',
                           b'!HasProcessed() || m_gestureActive)')
    after[CONTAINER]=c.once(before[CONTAINER],method,updated)
    after[INPUT]=c.once(before[INPUT],b'for (const int mediaID : {8101, 8102})',
                        b'for (const int mediaID : {8101, 8102, 8601, 8602, 8701, 8702, 8801, 8802})')
    # Native settings retain their existing Kodi constructors and controls.
    # Route only the named three dialogs of the exact Infinity skin to the
    # compact resource. Explicit third-party file paths always bypass this.
    old_path=b'''    std::string strFileNameLower = strFileName;
    StringUtils::ToLower(strFileNameLower);
    strLowerPath =  g_SkinInfo->GetSkinPath(strFileNameLower, &m_coordsRes);
    strPath = g_SkinInfo->GetSkinPath(strFileName, &m_coordsRes);'''
    new_path=b'''    // FOLD_CORRECTIVE_PLAYER_SETTINGS_V1: no global dialog/style replacement.
    const bool infinityPlayerSettings = g_SkinInfo->ID() == "skin.infinity.diggz" &&
        StringUtils::EqualsNoCase(strFileName, "DialogSettings.xml") &&
        (GetID() == WINDOW_DIALOG_VIDEO_OSD_SETTINGS ||
         GetID() == WINDOW_DIALOG_AUDIO_OSD_SETTINGS ||
         GetID() == WINDOW_DIALOG_SUBTITLE_OSD_SETTINGS);
    const std::string selectedFile = infinityPlayerSettings ? "InfinityPlayerSettings.xml" : strFileName;
    std::string strFileNameLower = selectedFile;
    StringUtils::ToLower(strFileNameLower);
    strLowerPath =  g_SkinInfo->GetSkinPath(strFileNameLower, &m_coordsRes);
    strPath = g_SkinInfo->GetSkinPath(selectedFile, &m_coordsRes);'''
    after[WINDOW]=c.once(before[WINDOW],old_path,new_path)
    after[CONTRACT]=classifier(before[CONTRACT],original,final)
    _,_,i=old_adapters()
    c.require(c.sha(before[COORDINATOR])==i.FINAL_NATIVE[COORDINATOR], 'wrong Essential-First CC22 coordinator')
    test=b'active["addon_version"].asString() != "0.3.5.22"'
    after[COORDINATOR]=c.once(before[COORDINATOR],test,test+b' && active["addon_version"].asString() != "0.3.5.23"')
    c.require({n for n in after if after[n]!=before[n]}==PATHS, 'incomplete corrective native delta')
    return after

def save(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

def bind(producer, parent, stage, source_commit):
    d,r,i=old_adapters()
    native=producer/'kodi';checkpoint=producer/'checkpoint-build'
    expected=json.loads((checkpoint/'COHERENT92-NATIVE-SOURCE-MAP.json').read_text())
    c.require(len(expected)==9404, 'complete protected source inventory required')
    links=d.native_build_inventory(native,expected,Path(os.environ['DEPENDS']))
    original=c.read_parent(parent)
    final=c.components(original)
    c.require(c.ledger(original,final)==json.loads((c.HERE/'MEMBER-DELTA.json').read_text()), 'unreviewed add-on payload')
    for n,b in final.items():
        c.require((stage/n).read_bytes()==b, 'stage differs '+n)
    before={n:(native/n).read_bytes() for n in PATHS}
    c.require(all(c.sha(b)==expected[n] for n,b in before.items()), 'native correction preimage drift')
    after=patches(before,original,final)
    after_map=dict(expected,**{n:c.sha(b) for n,b in after.items()})
    driver=d.module('corrective93_immutable_driver',producer/'repairs/four-repair-20261018/native_ci.py')
    ordering=driver.parent.parent.parent.parent.parent.parent.parent
    compiler=Path(ordering.native_manifest(ordering.stable())).resolve()
    paths=[checkpoint/'FOUR-REPAIR-INPUT-DELTA.json',compiler,checkpoint/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json']
    replacements={native/n:b for n,b in after.items()}
    for path in paths:
        value=json.loads(path.read_text())
        c.require(isinstance(value.get('after'),dict) and len(value['after'])>=4500, 'incomplete compiler ledger')
        c.require(PATHS.issubset(value['after']) and all(expected.get(n)==h for n,h in value['after'].items()), 'compiler ledger mismatch')
        value=copy.deepcopy(value)
        value['after'].update({n:after_map[n] for n in PATHS})
        value['changed']=sorted(set(value.get('changed',[]))|PATHS)
        value['source_commit']=source_commit
        value['fold_corrective_2103393_delta']=sorted(PATHS)
        replacements[path]=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    rollback=checkpoint/'FOLD93-ORIGINAL-INPUTS';c.require(not rollback.exists(),'corrective binding already exists')
    rollback.mkdir()
    backup={p:p.read_bytes() for p in replacements}
    for index,(p,b) in enumerate(backup.items()):
        (rollback/(str(index)+'.original')).write_bytes(b)
    save(rollback/'INDEX.json',{str(index):{'path':str(p),'sha256':c.sha(b)} for index,(p,b) in enumerate(backup.items())})
    try:
        for p,b in replacements.items():p.write_bytes(b)
        c.require(d.native_build_inventory(native,after_map,Path(os.environ['DEPENDS']))==links, 'build links/protected sources changed')
        proof={'source_commit':source_commit,'parent_source_commit':c.COMMIT,
               'original_source_count':9404,'final_source_count':9404,'protected_source_count':9404-len(PATHS),
               'before':{n:expected[n] for n in sorted(PATHS)},'after':{n:after_map[n] for n in sorted(PATHS)},
               'all_other_sources_byte_identical':True,'unchanged_build_links':links,
               'essential_first_guards_unchanged':True,'cobra_changed':False,'physical_fold_verified':False,
               'original_sigsegv_fixed':False,'final_lock':False}
        save(checkpoint/'FOLD93-NATIVE-BINDING.json',proof)
        save(checkpoint/'FOLD93-NATIVE-SOURCE-MAP.json',after_map)
        return proof
    except BaseException:
        for p,b in backup.items():p.write_bytes(b)
        raise
