"""Verified source overlay over all 9,404 signed 2103394 compiler inputs."""
from pathlib import Path
import hashlib,json,os,sys,copy
import components95 as c
import native94 as previous
from native94 import once,require
HERE=Path(__file__).resolve().parent
SOURCE94_SHA256='669c5f654e2495e85005c4b9e8b4f4dcbbb978523a541b43e7b52ee2cafe5a1b'
CONTAINER='xbmc/guilib/GUIBaseContainer.cpp';INPUT='xbmc/input/InputManager.cpp'
CONTRACT=previous.CONTRACT;COORDINATOR=previous.COORDINATOR;OBSERVER=previous.OBSERVER
AUDIT='xbmc/interfaces/python/InfinityPythonPersistence.h'
PATHS={CONTAINER,INPUT,CONTRACT,COORDINATOR,OBSERVER,AUDIT}

def checked_sources(root,expected):
 require(len(expected)==9404 and c.sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())==SOURCE94_SHA256,'exact signed 2103394 source map mandatory')
 for n,h in expected.items():require(c.digest(Path(root)/n)==h,'baseline source drift '+n)

def patches(before,original,final):
 require(set(before)==PATHS,'native95 scope differs');out=dict(before)
 raw=out[CONTAINER];start=raw.index(b'bool CGUIBaseContainer::OnInfinityOptionBLongPress(');end=raw.index(b'bool CGUIBaseContainer::OnInfinityRailLongPress(',start);body=raw[start:end]
 body=once(body,b'(GetID() != 8101 && GetID() != 8102 && GetID() != 8601 && GetID() != 8602 &&\n       GetID() != 8701 && GetID() != 8702 && GetID() != 8801 && GetID() != 8802)',b'(GetID() != 8101 && GetID() != 8102 && GetID() != 8801 && GetID() != 8802)')
 body=once(body,b'  // GROUP3_OPTION_B_V1:',b'''  const auto trace = [this](const char* phase,const char* outcome) {
    CLog::Log(LOGINFO,"[InfinityTouch] {{\\"event\\":\\"touch.option_b\\",\\"phase\\":\\"{}\\",\\"outcome\\":\\"{}\\",\\"control\\":{},\\"index\\":{}}}",phase,outcome,GetID(),GetSelectedItem());
  };
  trace("native.entry","received");
  // GROUP3_OPTION_B_V1:''')
 # Keep exact conditions and restore behavior, attach discriminating diagnostics.
 body=once(body,b'    return false;\n  for (const CGUIControl* owner',b'    { trace("native.guard","parent_control_processed_or_gesture"); return false; }\n  for (const CGUIControl* owner')
 body=once(body,b'    if (!owner->IsVisible() || owner->IsDisabled())\n      return false;',b'    if (!owner->IsVisible() || owner->IsDisabled())\n      { trace("native.guard","hidden_or_disabled"); return false; }')
 body=once(body,b'  if (!CanFocusFromPoint(point))\n    return false;',b'  if (!CanFocusFromPoint(point))\n    { trace("native.hit","outside"); return false; }')
 body=once(body,b'  if (!SelectItemFromPoint(point - CPoint(m_posX, m_posY)))\n    return false;',b'  if (!SelectItemFromPoint(point - CPoint(m_posX, m_posY)))\n    { trace("native.hit","no_item"); return false; }')
 for phase in ('not_file_item','provider_or_metadata_mismatch','window_or_modal_changed','home_missing','focus_changed'):
  body=once(body,b'    return restore();',('    { trace("native.validate","'+phase+'"); return restore(); }').encode()) if body.count(b'    return restore();')==1 else body.replace(b'    return restore();',('    { trace("native.validate","'+phase+'"); return restore(); }').encode(),1)
 require(b'    return restore();' not in body,'untraced validation')
 out[CONTAINER]=raw[:start]+body+raw[end:]
 out[INPUT]=once(out[INPUT],b'for (const int mediaID : {8101, 8102, 8601, 8602, 8701, 8702, 8801, 8802})',b'for (const int mediaID : {8101, 8102, 8801, 8802})')
 out[INPUT]=once(out[INPUT],b'      // INFINITY_RAIL_HOLD_V2:',b'''#if defined(TARGET_ANDROID)
      if (newEvent.touch.action == ACTION_TOUCH_LONGPRESS &&
          CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") == "skin.infinity.diggz")
        CLog::Log(LOGINFO,"[InfinityTouch] {{\\"event\\":\\"touch.option_b\\",\\"phase\\":\\"gesture.dispatch\\",\\"outcome\\":\\"received\\",\\"pointers\\":{},\\"window\\":{},\\"modal\\":{}}}",newEvent.touch.pointers,CServiceBroker::GetGUI()->GetWindowManager().GetActiveWindow(),CServiceBroker::GetGUI()->GetWindowManager().GetTopmostModalDialog());
#endif
      // INFINITY_RAIL_HOLD_V2:''')
 # New complete contracts are additive. Never edit historical contract pins.
 _,r,_=previous.old_adapters();coherence=r.coherence
 pins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json']);oldpins=json.loads(original[c.UI+'/CONTROLLER-PREIMAGES.json'])
 additions=[]
 for endpoint in (*coherence.ENDPOINTS,'default.py'):
  variants=[v for v in coherence.contracts(out[CONTRACT].decode()) if v['script']==c.CC+'/'+endpoint and v['pins']=={c.CC+'/'+n:h for n,h in oldpins.items()}]
  require(len(variants)==1,'exact CC24 contract absent '+endpoint)
  block=variants[0]['block'].encode()
  for n,h in oldpins.items():
   if pins[n]!=h:block=once(block,h.encode(),pins[n].encode())
  extra=b''.join(('      {"'+c.CC+'/'+n+'", "'+pins[n]+'"},\n').encode() for n in sorted(set(pins)-set(oldpins)))
  block=once(block,b'    }},',extra+b'    }},');additions.append(block)
 insertion=b'    // INFINITY_2103395_CC25_EXACT_SOURCES\n'+b'\n'.join(additions)+b'\n'
 out[CONTRACT]=once(out[CONTRACT],b'  };\n  return *contracts;',insertion+b'  };\n  return *contracts;')
 out[COORDINATOR]=once(out[COORDINATOR],b'active["addon_version"].asString() != "0.3.5.24"',b'active["addon_version"].asString() != "0.3.5.24" && active["addon_version"].asString() != "0.3.5.25"')
 out[AUDIT]=once(out[AUDIT],b'InfinityScriptPersistence::Fail(context->id,"unclassified_native_persistence_operation");',b'InfinityScriptPersistence::Fail(context->id,"unclassified_native_persistence_operation",event);')
 out[OBSERVER]=once(out[OBSERVER],b"'vfs_write_exception', target=self._infinity_path)",b"'vfs_write_exception', detail='value_type=' + type(value).__name__[:60], target=self._infinity_path)")
 return out

def old_adapters():return previous.old_adapters()
def module(name,path):return previous.module(name,path)
def bind(producer,parent,stage,source_commit):
 d,_,_=old_adapters();native=producer/'kodi';checkpoint=producer/'checkpoint-build';expected=json.loads((checkpoint/'FOLD94-NATIVE-SOURCE-MAP.json').read_text())
 checked_sources(native,expected);links=d.native_build_inventory(native,expected,Path(os.environ['DEPENDS']))
 original=c.read_parent(parent);final=c.components(original)
 require(c.ledger(original,final)==json.loads((HERE/'MEMBER-DELTA.json').read_text()),'unreviewed component delta')
 for name,body in final.items():require((stage/name).read_bytes()==body,'staged mismatch '+name)
 before={p:(native/p).read_bytes() for p in PATHS};after=patches(before,original,final);after_map=dict(expected,**{p:c.sha(b) for p,b in after.items()})
 driver=d.module('critical95_immutable_driver',producer/'repairs/four-repair-20261018/native_ci.py');ordering=driver.parent.parent.parent.parent.parent.parent.parent
 compiler=Path(ordering.native_manifest(ordering.stable())).resolve();paths=[checkpoint/'FOUR-REPAIR-INPUT-DELTA.json',compiler,checkpoint/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json']
 locked=json.loads((checkpoint/'LOCKED-2103384-SOURCE-MAP.json').read_text());records=[json.loads(p.read_text()) for p in paths]
 require(len({p.resolve() for p in paths})==3 and dict(locked,**records[0]['after'])==expected and all(v['after']==expected for v in records[1:]),'complete source ledgers required')
 updated=[]
 for record in records:
  value=copy.deepcopy(record);value['after'].update({p:after_map[p] for p in PATHS});value['changed']=sorted(set(value.get('changed',[]))|PATHS);value['source_commit']=source_commit;value['fold_critical_2103395_delta']=sorted(PATHS);updated.append(value)
 require(dict(locked,**updated[0]['after'])==after_map and all(v['after']==after_map for v in updated[1:]),'full ledger mismatch')
 replacements={native/p:b for p,b in after.items()};replacements.update({p:(json.dumps(v,indent=2,sort_keys=True)+'\n').encode() for p,v in zip(paths,updated)})
 backup={p:p.read_bytes() for p in replacements};rollback=checkpoint/'FOLD95-ORIGINAL-INPUTS';require(not rollback.exists(),'already bound');rollback.mkdir()
 for i,(p,b) in enumerate(backup.items()):(rollback/(str(i)+'.original')).write_bytes(b)
 previous.previous().save(rollback/'INDEX.json',{str(i):{'path':str(p),'sha256':c.sha(b)} for i,(p,b) in enumerate(backup.items())})
 try:
  for p,b in replacements.items():p.write_bytes(b)
  require(d.native_build_inventory(native,after_map,Path(os.environ['DEPENDS']))==links,'source/link drift')
  proof=dict(source_commit=source_commit,parent_source_commit=c.COMMIT,original_source_count=9404,final_source_count=9404,protected_source_count=9404-len(PATHS),before={p:expected[p] for p in sorted(PATHS)},after={p:after_map[p] for p in sorted(PATHS)},all_other_sources_byte_identical=True,unchanged_build_links=links,essential_first_guards_unchanged=True,cobra_changed=False,physical_fold_verified=False,original_sigsegv_fixed=False,final_lock=False)
  for file,value in [('FOLD95-NATIVE-BINDING.json',proof),('FOLD95-NATIVE-SOURCE-MAP.json',after_map)]:previous.previous().save(checkpoint/file,value)
  return proof
 except BaseException:
  for p,b in backup.items():p.write_bytes(b)
  raise
