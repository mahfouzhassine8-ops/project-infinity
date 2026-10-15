"""Stage observations only atop exact locked RC02 native sources."""
from pathlib import Path
import hashlib,json,re

HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def once(s,a,b):
    if s.count(a)!=1:raise RuntimeError('Missing/ambiguous source anchor: '+a[:90])
    return s.replace(a,b,1)

def apply(root):
    pins=json.loads((HERE/'RC02-HASHES.json').read_text()); before={};after={}
    def change(name,fn):
        p=root/name;raw=p.read_bytes()
        if sha(raw)!=pins[name]:raise RuntimeError('RC02 source mismatch '+name+': '+sha(raw))
        before[name]=sha(raw);data=fn(raw.decode()).encode();p.write_bytes(data);after[name]=sha(data)
    for name in ['InfinityStabilityProbe.h','InfinityPythonWaitProbe.h','InfinityProbeExport.h']:
        target='xbmc/threads/'+name;p=root/target
        if p.exists():raise RuntimeError('Refuse duplicate probe '+target)
        data=(HERE/name).read_bytes();p.write_bytes(data);after[target]=sha(data)
    inc='''#if defined(TARGET_ANDROID)
#include "threads/InfinityStabilityProbe.h"
#endif
'''
    def locks(s):
        s=once(s,'#pragma once','#pragma once\n'+inc)
        return once(s,'''    inline void lock() { mutex.lock(); count++; }
    inline bool try_lock() { return mutex.try_lock() ? count++, true : false; }
    inline void unlock() { count--; mutex.unlock(); }''','''    inline void lock() {
#if defined(TARGET_ANDROID)
      InfinityStabilityProbe::Waiting(this);
#endif
      mutex.lock(); count++;
#if defined(TARGET_ANDROID)
      InfinityStabilityProbe::Acquired(this,count,reinterpret_cast<uintptr_t>(__builtin_return_address(0)));
#endif
    }
    inline bool try_lock() {
      if(!mutex.try_lock())return false;
      ++count;
#if defined(TARGET_ANDROID)
      InfinityStabilityProbe::Acquired(this,count,reinterpret_cast<uintptr_t>(__builtin_return_address(0)));
#endif
      return true;
    }
    inline void unlock() { --count;
#if defined(TARGET_ANDROID)
      InfinityStabilityProbe::Released(this,count);
#endif
      mutex.unlock();
    }''')
    change('xbmc/threads/Lockables.h',locks)
    def health(s):
        s=once(s,'#pragma once','#pragma once\n#include "threads/InfinityStabilityProbe.h"')
        return once(s,'    if(sequence.load()==before)return true;','    if(sequence.load()==before){InfinityStabilityProbe::Observe(out[1]);return true;}')
    change('xbmc/platform/android/activity/InfinityResponsiveness.h',health)
    def manager(s):
        return once(s,'    InfinityHealth::Publish({1, now, GetActiveWindow()', '''    InfinityStabilityProbe::RegisterGraphics(static_cast<const CCriticalSection*>(&gfx));
    static bool probeStarted=false;
    if(!probeStarted){InfinityStabilityProbe::Arm(90);probeStarted=true;
      if(home)home->SetProperty("Infinity.Stability.ProbeVersion","1");}
    if(home && home->GetProperty("Infinity.Stability.ProbeArm").asString()=="true") {
      home->ClearProperty("Infinity.Stability.ProbeArm");InfinityStabilityProbe::Arm(300);
    }
    if(home && home->GetProperty("Infinity.Stability.ProbeSnapshot").asString()=="true") {
      home->ClearProperty("Infinity.Stability.ProbeSnapshot");InfinityStabilityProbe::manualSnapshot.store(true);
    }
    InfinityHealth::Publish({1, now, GetActiveWindow()''')
    change('xbmc/guilib/GUIWindowManager.cpp',manager)
    def directory(s):
        s=once(s,'#include "DirectoryProvider.h"','#include "DirectoryProvider.h"\n'+inc)
        def add(m):
            indent=m[1];return indent+'#if defined(TARGET_ANDROID)\n'+indent+'InfinityStabilityProbe::DirectoryScope probeScope(&m_section,__func__);\n'+indent+'#endif\n'+m[0]
        s,n=re.subn(r'(?m)^( +)std::unique_lock<CCriticalSection> lock\(m_section\);',add,s)
        if n<10:raise RuntimeError('Directory lock coverage incomplete')
        return s
    change('xbmc/guilib/listproviders/DirectoryProvider.cpp',directory)
    def container(s):
        s=once(s,'#include "GUIBaseContainer.h"','#include "GUIBaseContainer.h"\n'+inc)
        return once(s,'void CGUIBaseContainer::Render()\n{','void CGUIBaseContainer::Render()\n{\n#if defined(TARGET_ANDROID)\n  InfinityStabilityProbe::Rendered(GetID(),m_items.size());\n#endif')
    change('xbmc/guilib/GUIBaseContainer.cpp',container)
    def python(s):
        s=once(s,'#include "PythonInvoker.h"','#include "PythonInvoker.h"\n#if defined(TARGET_ANDROID)\n#include "threads/InfinityPythonWaitProbe.h"\n#include "threads/InfinityProbeExport.h"\n#include "utils/URIUtils.h"\n#include <dlfcn.h>\n#endif')
        s=once(s,'        executeScript(fp, realFilename, moduleDict);','''#if defined(TARGET_ANDROID)
        InfinityPythonWaitProbe::Context* waitProbe=nullptr;
        Dl_info identity{};dladdr(reinterpret_cast<void*>(&InfinityStabilityProbe::Configure),&identity);
        try {
          InfinityStabilityProbe::Configure(CSpecialProtocol::TranslatePath("special://temp/infinity-stability-probe.jsonl"),reinterpret_cast<uintptr_t>(identity.dli_fbase));
          InfinityProbeExport::Install();
        }catch(...){/* Evidence must not prevent an add-on from running. */}
        if(m_addon && m_addon->ID()=="plugin.video.umbrella" && URIUtils::GetFileName(realFilename)=="service.py") {
          waitProbe=InfinityPythonWaitProbe::Start(GetId());
        }
        try {
#endif
          executeScript(fp, realFilename, moduleDict);
#if defined(TARGET_ANDROID)
        }catch(...){if(waitProbe)InfinityPythonWaitProbe::BodyReturned();throw;}
        if(waitProbe)InfinityPythonWaitProbe::BodyReturned();
#endif''')
        return once(s,'      Py_EndInterpreter(m_threadState);','''      Py_EndInterpreter(m_threadState);
#if defined(TARGET_ANDROID)
      InfinityPythonWaitProbe::Retired(GetId());
#endif''')
    change('xbmc/interfaces/python/PythonInvoker.cpp',python)
    def checkpoint(s):
        s=once(s,'#include "InfinityAndroidCheckpoint.h"','#include "InfinityAndroidCheckpoint.h"\n'+inc)
        return once(s,'  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();',
            '  InfinityStabilityProbe::CloseRequested();\n  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();')
    change('xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp',checkpoint)
    def timings(s):
        s=once(s,"(value[0] != 'n' && value[0] != 'p')","(value[0] != 'n' && value[0] != 'p' && value[0] != 'r')")
        old='''    if (url.compare(0, prefix.size(), prefix) != 0) return;
    m_request = "n" + std::to_string(++serial);
    m_media = url.find("media=tv") != std::string::npos ? "tv" :
              (url.find("media=movie") != std::string::npos ? "movie" : "all");'''
        new='''    const bool rails=url.compare(0,31,"plugin://script.infinity.rails/")==0;
    if (!rails && url.compare(0, prefix.size(), prefix) != 0) return;
    m_request = std::string(rails?"r":"n") + std::to_string(++serial);
    m_media = rails ? (url.find("section=tvshows")!=std::string::npos?"rails_tv":"rails_movie") :
              (url.find("media=tv") != std::string::npos ? "tv" :
              (url.find("media=movie") != std::string::npos ? "movie" : "all"));'''
        return once(s,old,new)
    change('xbmc/guilib/listproviders/InfinityResumeTiming.h',timings)
    # No persistence/classifier/foreign-writer waiver or runtime policy change.
    for name in ['xbmc/platform/android/activity/InfinityScriptPersistence.h','xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp','xbmc/interfaces/generic/ScriptInvocationManager.cpp']:
        if sha((root/name).read_bytes())!=pins[name]:raise RuntimeError('Protected gate altered '+name)
    return {'before':before,'after':after,'changed':sorted(after),'observations_only':True,'required_save_gates_changed':False,'candidate_is_fix':False,'physical_capture_required':True}
