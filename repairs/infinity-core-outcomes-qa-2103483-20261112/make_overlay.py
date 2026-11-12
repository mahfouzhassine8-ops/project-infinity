#!/usr/bin/env python3
"""Derive Core-only diagnostic overlay from exact83 source bytes."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PINS={
 'xbmc/interfaces/python/PythonInvoker.cpp':'8765370da585cef37918ebd31a4322035901793e0b0f4275868ca11e2e1ff724',
 'xbmc/interfaces/python/InfinityPythonPersistence.h':'a7513d681cb7ef6dfba5dc49e2210446185ff3c26005415d0f4426648c6ede3b',
 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h':'5ceb321b2a68b5c1b73709a1004a05ad1234bcefdb00bc0ab9a719fed0548aa8',
}


def replace(source,old,new):
 assert source.count(old)==1,old
 return source.replace(old,new,1)


def files(runtime):
 src={}
 for name,pin in PINS.items():
  raw=(runtime/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin,name
  src[name]=raw.decode()
 name='xbmc/interfaces/python/InfinityPythonPersistence.h'
 src[name]=replace(src[name],'#include "InfinityPythonWriteHooks.h"','#include "InfinityPythonWriteHooks.h"\n#include "InfinityCoreOutcomeTrace.h"')
 src[name]=replace(src[name],'  InitializationStage(context,"python.source");','  InfinityCoreQA::BindLoadSink(id,context->globals);\n  InitializationStage(context,"python.source");')
 name='xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
 old='''            return original(name, *args, **kwargs)
        self.patch(native, 'dlopen', loaded)'''
 new='''            # QA observation only: delegate, arguments, result and error stay
            # original. Other image loads retain the original direct path.
            sink = globals().get('_INFINITY_CORE_NATIVE_EVENT')
            selected = sink is not None and type(name) in (str, bytes) and os.fsdecode(name).rsplit('/', 1)[-1] == 'libadulthideout_core.so'
            if not selected:
                return original(name, *args, **kwargs)
            def note(event, detail):
                try: return sink(event, name, detail)
                except BaseException: return None
            ticket = note('begin', None)
            try:
                result = original(name, *args, **kwargs)
            except BaseException as error:
                note('error', (ticket, error))
                raise
            else:
                note('returned', (ticket, result))
                return result
        self.patch(native, 'dlopen', loaded)'''
 src[name]=replace(src[name],old,new)
 name='xbmc/interfaces/python/PythonInvoker.cpp'
 old='  // END INFINITY_PREBYTECODE_OBSERVER'
 new='''  // QA observer has no effect on admission, persistence or the Core path.
  if (m_infinityPersistenceObserver && !PyErr_Occurred() && m_addon)
  {
    std::string coreSource = realFilename;
    if (m_addon->ID() == "plugin.video.adulthideout")
    {
      ADDON::AddonPtr coreAddon;
      if (CServiceBroker::GetAddonMgr().GetAddon("service.adulthideout.core", coreAddon, ADDON::OnlyEnabled::CHOICE_NO))
        coreSource = CSpecialProtocol::TranslatePath(coreAddon->LibPath());
      else
        coreSource.clear();
    }
    InfinityCoreQA::Install(GetId(), m_addon->ID(), coreSource,
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver)->globals);
  }
  // END INFINITY_PREBYTECODE_OBSERVER'''
 src[name]=replace(src[name],old,new)
 old='''      InfinityPythonPersistence::Finish(
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver),'''
 new='''      InfinityCoreQA::BeforeFinish(
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver)->globals, m_threadState);
      InfinityPythonPersistence::Finish(
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver),'''
 src[name]=replace(src[name],old,new)
 src[name]=replace(src[name],'          InfinityPythonPersistence::Finish(persistence, m_threadState, checkpointEscalated);',
   '          InfinityCoreQA::BeforeFinish(persistence->globals, m_threadState);\n          InfinityPythonPersistence::Finish(persistence, m_threadState, checkpointEscalated);')
 text=(HERE/'observer.py').read_text();assert ')coreoutcome"' not in text
 src['xbmc/interfaces/python/InfinityCoreOutcomeSource.h']='#pragma once\ninline constexpr const char* INFINITY_CORE_OUTCOME_SOURCE=R"coreoutcome('+text+')coreoutcome";\n'
 src['xbmc/interfaces/python/InfinityCoreOutcomeTrace.h']='#define INFINITY_CORE_OUTCOMES_QA 1 // Internal QA only.\n'+(HERE/'native/InfinityCoreOutcomeTrace.h').read_text()
 return {name:text.encode() for name,text in src.items()}


def write(runtime,out):
 data=files(runtime);out.mkdir(parents=True,exist_ok=True)
 binding={}
 for name,raw in data.items():
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  binding[name]={'before':PINS.get(name),'after':hashlib.sha256(raw).hexdigest()}
 return binding


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 print(json.dumps(write(a.runtime,a.out),indent=2))
