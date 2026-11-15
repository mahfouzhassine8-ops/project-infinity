// Disposable Android fixture. No persistence implementation is copied here.
// Every operation below resolves to the actual authenticated libkodi.so.
#include <jni.h>
#include <android/log.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cstdint>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <vector>
#include "bridge_types.h"
#include "bridge_symbols.h"

struct _object; struct _ts; struct _is;
using Object = _object; using Thread = _ts; using Interpreter = _is;
using Evidence = InfinityScriptPersistence::Evidence;
using Proof = InfinityScriptPersistence::EssentialWriteProof;
static_assert(sizeof(void*)==8,"Actual ARM64 fixture required");
#ifndef __aarch64__
#error Actual ARM64 fixture required
#endif
static void* engine;

template<class T> T bind(const char* name) {
  void* symbol = dlsym(engine, name);
  Dl_info info{};
  if (!symbol || !dladdr(symbol, &info) || !info.dli_fname ||
      std::string(info.dli_fname).find("libkodi.so") == std::string::npos)
    throw std::runtime_error(std::string("actual_engine_symbol_missing:") + name);
  return reinterpret_cast<T>(symbol);
}
static std::string text(JNIEnv* env, jstring value) {
  const char* raw = env->GetStringUTFChars(value, nullptr);
  if (!raw) throw std::runtime_error("JNI string unavailable");
  std::string result(raw); env->ReleaseStringUTFChars(value, raw); return result;
}
static std::string quote(const std::string& value) {
  std::string result="\"";
  for (unsigned char c:value) {
    if(c=='"'||c=='\\') { result+='\\';result+=c; }
    else if(c=='\n') result+="\\n";
    else if(c=='\r') result+="\\r";
    else if(c=='\t') result+="\\t";
    else if(c>=32 && c<127) result+=c;
    else result+='?';
  }
  return result+'"';
}
static void require(bool condition, const std::string& message) {
  if (!condition) throw std::runtime_error(message);
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_projectinfinity_observerqa_ProbeActivity_runNative(
    JNIEnv* env, jclass, jstring directory, jstring pythonPath,
    jstring caseName, jstring pythonCode, jboolean corrected) {
  std::string stage="load", result;
  try {
    require(!engine,"one_engine_per_process_required");
    const std::string root=text(env,directory), mode=text(env,caseName);
    const std::string library="libkodi.so";
    engine=dlopen(library.c_str(),RTLD_NOW|RTLD_LOCAL);
    require(engine!=nullptr,"engine_dlopen_failed");
    auto initialize=bind<void(*)()>("Py_Initialize");
    auto append=bind<int(*)(const char*,Object*(*)())>("PyImport_AppendInittab");
    auto initVfs=bind<Object*(*)()>(SYM_VFS);
    auto setPath=bind<void(*)(const wchar_t*)>("Py_SetPath");
    auto threadGet=bind<Thread*(*)()>("PyThreadState_Get");
    auto interpreterGet=bind<Interpreter*(*)(Thread*)>("PyThreadState_GetInterpreter");
    auto newInterpreter=bind<Thread*(*)()>("Py_NewInterpreter");
    auto endInterpreter=bind<void(*)(Thread*)>("Py_EndInterpreter");
    auto swap=bind<Thread*(*)(Thread*)>("PyThreadState_Swap");
    auto finalize=bind<int(*)()>("Py_FinalizeEx");
    auto run=bind<int(*)(const char*)>("PyRun_SimpleString");
    auto printError=bind<void(*)()>("PyErr_Print");
    auto errorOccurred=bind<Object*(*)()>("PyErr_Occurred");
    auto snapshot=bind<Evidence(*)()>(SYM_SNAPSHOT);
    auto admit=bind<void(*)(int,const std::string&)>(SYM_ADMIT);
    auto start=bind<void*(*)(int,Interpreter*)>(SYM_START);
    auto finish=bind<void(*)(void*,Thread*,bool)>(SYM_FINISH);
    auto end=bind<void(*)(void*,Interpreter*)>(SYM_END);
    auto begin=bind<bool(*)(uint64_t,const std::vector<std::string>&,const std::vector<std::string>&)>(SYM_BEGIN);
    auto close=bind<bool(*)(uint64_t)>(SYM_CLOSE);
    auto seal=bind<bool(*)(uint64_t)>(SYM_SEAL);
    auto authorized=bind<bool(*)(uint64_t)>(SYM_AUTHORIZED);
    auto active=bind<std::size_t(*)()>(SYM_ACTIVE);
    auto protectedProof=bind<Proof(*)()>(SYM_PROOF);
    stage="python_initialize";
    const std::string paths=text(env,pythonPath);
    const std::wstring wide(paths.begin(),paths.end());
    setPath(wide.c_str());
    require(append("xbmcvfs",initVfs)==0,"real_xbmcvfs_registration_failed");
    initialize();
    Thread* mainThread=threadGet();
    Thread* thread=newInterpreter();
    require(thread!=nullptr,"subinterpreter_unavailable");
    Interpreter* interpreter=interpreterGet(thread);
    auto execute=[&](const std::string& code) {
      if(run(code.c_str())!=0) {printError();throw std::runtime_error("python_case_failed");}
    };
    execute("import sys\nsys.dont_write_bytecode=True\nroot="+quote(root)+"\n");
    stage="actual_native_observer_start";
    admit(701,"optional.integration.fixture:case.py");
    void* context=start(701,interpreter);
    if(errorOccurred()) printError();
    auto ready=snapshot();
    require(context && ready.observed==1 && ready.failure.empty(),
            "observer_not_observed:"+ready.failure+":"+ready.failureDetail);
    require(ready.initialization.size()==1 && ready.initialization[0].current.stage=="complete",
            "observer_initialization_incomplete");
    stage="real_python_io_case";
    execute(text(env,pythonCode));
    auto after=snapshot();
    const bool closed=mode.rfind("closed_",0)==0;
    const bool failed=mode=="flush_error"||mode=="sqlite_pending"||mode=="dirty_buffer";
    if(closed) {
      require(after.blockingCount==(corrected?0u:1u),"closed_flush_callback_count");
      if(!corrected) require(after.failure.find("flush_failed")!=std::string::npos,"baseline_missing_flush_failure");
    }
    if(mode=="flush_error") require(after.failure.find("flush_failed")!=std::string::npos,"real_flush_error_lost");
    if(mode=="sqlite_pending"||mode=="dirty_buffer") require(active()>0,"unfinished_resource_not_accounted");
    stage="finish_and_protected_write_proof";
    // Dirty resources are examined before fixture cleanup. No automatic commit
    // or rollback is supplied by the observer or by this admission check.
    if(mode=="sqlite_pending") {
      finish(context,thread,false);
      auto pending=snapshot();
      require(pending.failure.find("sqlite_pending_transaction")!=std::string::npos,
              "uncommitted_sqlite_retirement_was_accepted");
      execute("assert connection.in_transaction\nconnection.rollback()\nconnection.close()\n");
    }
    if(mode=="dirty_buffer") {
      finish(context,thread,false);
      require(snapshot().blockingCount>0,"dirty_flush_failure_lost");
      execute("raw.write=original_write\nhandle.flush()\nhandle.close()\n");
    }
    if(mode=="flush_error") execute("del raw.flush\n");
    // Actual missing durability is induced only on this disposable fixture.
    if(mode=="durability_denied") require(::chmod((root+"/profile/value").c_str(),0)==0,"fixture_chmod_failed");
    require(begin(17,{root+"/profile"},{root+"/cache"}),"protection_begin_failed");
    require(close(17),"protection_close_failed");
    if(mode=="durability_denied") require(protectedProof().blockers.empty(),"preexisting_blocker_invalidates_durability_case");
    const bool sealed=seal(17);
    const bool expected=(!closed||corrected)&&!failed&&mode!="durability_denied";
    require(sealed==expected && authorized(17)==expected,"incorrect_native_seal_outcome");
    if(mode=="durability_denied") {
      bool durabilityFailure=false;
      for(const auto& blocker:protectedProof().blockers)
        if(blocker.rfind("protected_durability_failed:",0)==0) durabilityFailure=true;
      require(durabilityFailure,"missing_actual_native_durability_failure");
    }
    if(mode=="late_write") {
      const auto denied=protectedProof().denied;
      execute("try:\n open(root+'/profile/late','wb')\nexcept PermissionError:\n pass\nelse:\n raise AssertionError('late protected write admitted')\n");
      require(protectedProof().denied>denied && ::access((root+"/profile/late").c_str(),F_OK)!=0,
              "native_denial_or_absent_target_not_proven");
    }
    if(mode=="durability_denied") ::chmod((root+"/profile/value").c_str(),0600);
    stage="interpreter_retirement";
    finish(context,thread,false);
    const auto beforeEnd=snapshot();
    endInterpreter(thread);
    end(context,interpreter);
    swap(mainThread);
    require(finalize()==0,"main_python_finalization_failed");
    const auto final=snapshot();
    if(expected && mode!="late_write")
      require(final.retired==1 && final.failure.empty(),"successful_interpreter_not_retired");
    result="{\"status\":\"PASS\",\"case\":"+quote(mode)+
           ",\"observer_complete\":true,\"actual_engine_callbacks\":true,\"sealed\":"+(sealed?"true":"false")+
           ",\"failure_before_finalization\":"+quote(beforeEnd.failure)+
           ",\"full_application_startup_shutdown\":\"NOT_TESTED\",\"physical_Fold\":false}";
  } catch(const std::exception& error) {
    result="{\"status\":\"FAIL\",\"stage\":"+quote(stage)+",\"reason\":"+quote(error.what())+"}";
  }
  __android_log_print(ANDROID_LOG_INFO,"InfinityObserverQA","%s",result.c_str());
  return env->NewStringUTF(result.c_str());
}
