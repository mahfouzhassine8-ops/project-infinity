#define INFINITY_CORE_OUTCOMES_QA 1 // Internal QA only.
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
// Internal QA only. No admission, mutation, teardown or persistence authority.
#if defined(INFINITY_CORE_OUTCOMES_QA)
#include "InfinityCoreOutcomeSource.h"
#include <atomic>
#include <chrono>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <openssl/evp.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#if !defined(INFINITY_CORE_OUTCOMES_HOST)
#include <android/log.h>
#endif
namespace InfinityCoreQA {
inline std::atomic<unsigned> records{0};
inline std::atomic<uint64_t> tickets{0};
inline std::atomic<bool> limitReported{false};
inline bool Owned() noexcept { return InfinityStartupTrace::InfinityProcess(); }
inline bool Active() noexcept {
  if(!Owned())return false;
  static const auto began=std::chrono::steady_clock::now();
  return std::chrono::steady_clock::now()-began<std::chrono::minutes(30);
}
struct Errors {
  int saved=errno; PyObject *type=nullptr,*value=nullptr,*trace=nullptr;
  Errors(){PyErr_Fetch(&type,&value,&trace);}
  ~Errors(){PyErr_Clear();PyErr_Restore(type,value,trace);errno=saved;}
};
inline void Log(int id,const char* json) noexcept {
  const int saved=errno;
  if(!Active()){errno=saved;return;}
  const unsigned row=records.fetch_add(1,std::memory_order_relaxed);
  if(row>=8192) {
    if(limitReported.exchange(true)){errno=saved;return;}
    json="{\"v\":1,\"event\":\"coverage.native_limit\",\"completion_proof\":false}";
  }
  char line[3500]{};
  const int length=std::snprintf(line,sizeof(line),"{\"native_pid\":%ld,\"invoker\":%d,\"data\":%s}",
                               static_cast<long>(::getpid()),id,json);
  if(length>0 && static_cast<std::size_t>(length)<sizeof(line)) {
#if defined(INFINITY_CORE_OUTCOMES_HOST)
    InfinityCoreQaHostLog(line);
#else
    __android_log_write(ANDROID_LOG_INFO,"InfinityCoreQA",line);
#endif
  }
  errno=saved;
}
inline void Maps(int id,const char* moment) noexcept {
  const int saved=errno;
  if(!Active() || records.load(std::memory_order_relaxed)>=8192){errno=saved;return;}
  errno=0;
  FILE* stream=std::fopen("/proc/self/maps","r");
  const int openError=stream?0:errno;
  const bool opened=stream!=nullptr;
  unsigned count=0,chunks=0;int readError=0;
  bool executable=false,complete=stream!=nullptr,truncated=false,capped=false,readFailed=false;
  char text[4096]{};
  if(stream) {
    // Count bounded fgets buffer records, not presumed physical map lines.
    // One additional read detects cap exhaustion; its contents are discarded.
    while(true) {
      errno=0;
      if(!std::fgets(text,sizeof(text),stream)) {
        const int observed=errno;
        if(std::ferror(stream)){readFailed=true;readError=observed;complete=false;}
        break;
      }
      if(chunks>=4096){capped=true;complete=false;break;}
      ++chunks;
      if(!std::strchr(text,'\n')){truncated=true;complete=false;}
      if(std::strstr(text,"libadulthideout_core.so")) {
        ++count;char permissions[5]{};
        if(std::sscanf(text,"%*s %4s",permissions)==1 && permissions[2]=='x')executable=true;
      }
    }
    std::fclose(stream);
  }
  char json[700]{};
  std::snprintf(json,sizeof(json),"{\"v\":1,\"event\":\"core.maps\",\"moment\":\"%s\",\"map_entries\":%u,\"executable_mapping\":%s,\"complete\":%s,\"buffer_chunks_scanned\":%u,\"chunk_limit\":4096,\"limit_reached\":%s,\"line_truncated\":%s,\"open_succeeded\":%s,\"open_errno\":%d,\"read_failed\":%s,\"read_errno\":%d,\"completion_proof\":false}",
                moment,count,executable?"true":"false",complete?"true":"false",chunks,
                capped?"true":"false",truncated?"true":"false",opened?"true":"false",openError,readFailed?"true":"false",readError);
  Log(id,json);errno=saved;
}
inline int SelfId(PyObject* self) noexcept {
  return PyLong_CheckExact(self)?static_cast<int>(PyLong_AsLong(self)):-1;
}
inline std::string TargetJson(PyObject* value) {
  const char* text=PyUnicode_CheckExact(value)?PyUnicode_AsUTF8(value):
                   PyBytes_CheckExact(value)?PyBytes_AS_STRING(value):nullptr;
  if(!text || text[0]!='/' || std::strstr(text,"://") || std::strchr(text,'?') || std::strlen(text)>512)return "\"<unavailable-target>\"";
  std::string out="\"";
  for(const unsigned char* at=reinterpret_cast<const unsigned char*>(text);*at;++at) {
    if(*at<32 || *at>126)return "\"<non-ascii-target>\"";
    if(*at=='"' || *at=='\\'){out+='\\';}
    out+=static_cast<char>(*at);
  }
  return out+'"';
}
inline PyObject* Emit(PyObject* self,PyObject* row) {
  Errors errors;
  try {
    if(Active() && PyDict_CheckExact(row)) {
      auto* line=PyDict_GetItemString(row,"line");
      if(line && PyUnicode_CheckExact(line)) {
        Py_ssize_t size=0;const char* text=PyUnicode_AsUTF8AndSize(line,&size);
        if(text && size>1 && size<3100 && text[0]=='{' && text[size-1]=='}' &&
           !std::memchr(text,'\n',size) && !std::memchr(text,'\r',size))Log(SelfId(self),text);
      }
    }
  } catch(...) {}
  Py_RETURN_NONE;
}
inline bool CoreName(PyObject* value) {
  const char* text=PyUnicode_CheckExact(value)?PyUnicode_AsUTF8(value):
                   PyBytes_CheckExact(value)?PyBytes_AS_STRING(value):nullptr;
  if(!text)return false;
  const auto* slash=std::strrchr(text,'/');
  return std::strcmp(slash?slash+1:text,"libadulthideout_core.so")==0;
}
inline PyObject* LoadEvent(PyObject* self,PyObject* args) {
  Errors errors;uint64_t ticket=0;
  try {
    const char* event=nullptr;PyObject *name=nullptr,*detail=nullptr;
    if(Active() && PyArg_ParseTuple(args,"sOO",&event,&name,&detail) && CoreName(name)) {
      const int id=SelfId(self);
      if(std::strcmp(event,"begin")==0) {
        ticket=tickets.fetch_add(1,std::memory_order_relaxed)+1;
        char json[1100]{};const auto target=TargetJson(name);
        std::snprintf(json,sizeof(json),"{\"v\":1,\"event\":\"core.load.begin\",\"ticket\":%llu,\"target\":%s,\"completion_proof\":false}",static_cast<unsigned long long>(ticket),target.c_str());
        Log(id,json);Maps(id,"before_load");
      } else if(PyTuple_CheckExact(detail) && PyTuple_GET_SIZE(detail)==2) {
        auto* number=PyTuple_GET_ITEM(detail,0);auto* result=PyTuple_GET_ITEM(detail,1);
        if(PyLong_CheckExact(number))ticket=PyLong_AsUnsignedLongLong(number);
        if(std::strcmp(event,"returned")==0) {
          char json[300]{};
          std::snprintf(json,sizeof(json),"{\"v\":1,\"event\":\"core.load.returned\",\"ticket\":%llu,\"handle_is_integer\":%s,\"completion_proof\":false}",static_cast<unsigned long long>(ticket),PyLong_CheckExact(result)?"true":"false");
          Log(id,json);Maps(id,"load_returned");
        } else if(std::strcmp(event,"error")==0) {
          bool namespaceDenied=false;
          if(Py_TYPE(result)==reinterpret_cast<PyTypeObject*>(PyExc_OSError)) {
            auto* message=PyObject_Str(result);
            const char* text=message && PyUnicode_CheckExact(message)?PyUnicode_AsUTF8(message):nullptr;
            namespaceDenied=text && std::strstr(text,"not accessible for the namespace");
            Py_XDECREF(message);
          }
          char json[330]{};
          std::snprintf(json,sizeof(json),"{\"v\":1,\"event\":\"core.load.error\",\"ticket\":%llu,\"namespace_rejected\":%s,\"completion_proof\":false}",static_cast<unsigned long long>(ticket),namespaceDenied?"true":"false");
          Log(id,json);Maps(id,"load_error");
        }
      }
    }
  } catch(...) {}
  return PyLong_FromUnsignedLongLong(ticket);
}
inline void BindLoadSink(int id,PyObject* globals) noexcept {
  Errors errors;
  try {
    if(!Active())return;
    static PyMethodDef method={"core_load_event",LoadEvent,METH_VARARGS,nullptr};
    auto* number=PyLong_FromLong(id);
    auto* callback=number?PyCFunction_NewEx(&method,number,nullptr):nullptr;
    if(callback)PyDict_SetItemString(globals,"_INFINITY_CORE_NATIVE_EVENT",callback);
    Py_XDECREF(callback);Py_XDECREF(number);
  } catch(...) {}
}
inline std::string SourceHash(const std::string& path) {
  const int fd=::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0)return {};
  struct stat before{},after{};std::string bytes;char data[8192];bool ok=::fstat(fd,&before)==0 && S_ISREG(before.st_mode) && before.st_size<=65536;
  while(ok) {const auto count=::read(fd,data,sizeof(data));if(count<0 && errno==EINTR)continue;
    if(count<0){ok=false;break;}if(count==0)break;bytes.append(data,static_cast<std::size_t>(count));if(bytes.size()>65536)ok=false;}
  ok=ok && ::fstat(fd,&after)==0 && before.st_dev==after.st_dev && before.st_ino==after.st_ino && before.st_size==after.st_size && before.st_mtime==after.st_mtime;
  ::close(fd);if(!ok)return {};
  unsigned char digest[EVP_MAX_MD_SIZE]{};unsigned size=0;
  if(EVP_Digest(bytes.data(),bytes.size(),digest,&size,EVP_sha256(),nullptr)!=1 || size!=32)return {};
  static constexpr char hex[]="0123456789abcdef";std::string result;
  for(unsigned n=0;n<size;++n){result+=hex[digest[n]>>4];result+=hex[digest[n]&15];}return result;
}
inline void Install(int id,const std::string& addon,const std::string& source,PyObject* persistenceGlobals) noexcept {
  Errors errors;
  try {
    if(!Active() || !persistenceGlobals || (addon!="service.adulthideout.core" && addon!="plugin.video.adulthideout"))return;
    if(PyDict_GetItemString(persistenceGlobals,"_INFINITY_CORE_OUTCOMES_GLOBALS"))return;
    const std::string digest=SourceHash(source);
    if(digest!="2e1b79adc352129696ccfa48a3b5b16f85ebf812026fdd26c3e55d67f34b43b3") {
      Log(id,"{\"v\":1,\"event\":\"coverage.source_identity_mismatch\",\"completion_proof\":false}");return;
    }
    auto* globals=PyDict_New();auto* name=PyUnicode_FromString("_infinity_core_outcomes_qa");
    if(!globals || !name){Py_XDECREF(globals);Py_XDECREF(name);return;}
    PyDict_SetItemString(globals,"__name__",name);Py_DECREF(name);
    auto* loaded=PyRun_String(INFINITY_CORE_OUTCOME_SOURCE,Py_file_input,globals,globals);
    if(loaded) {
      Py_DECREF(loaded);
      static PyMethodDef method={"core_outcome_event",Emit,METH_O,nullptr};
      auto* number=PyLong_FromLong(id);auto* callback=number?PyCFunction_NewEx(&method,number,nullptr):nullptr;
      auto* install=PyDict_GetItemString(globals,"install");
      auto* state=install && callback?PyObject_CallFunction(install,"OsssO",callback,source.c_str(),digest.c_str(),"core_service",Py_False):nullptr;
      if(state) {PyDict_SetItemString(globals,"state",state);Py_DECREF(state);PyDict_SetItemString(persistenceGlobals,"_INFINITY_CORE_OUTCOMES_GLOBALS",globals);Maps(id,"observer_installed");}
      else Log(id,"{\"v\":1,\"event\":\"coverage.install_failed\",\"completion_proof\":false}");
      Py_XDECREF(callback);Py_XDECREF(number);
    } else Log(id,"{\"v\":1,\"event\":\"coverage.source_setup_failed\",\"completion_proof\":false}");
    Py_DECREF(globals);
  } catch(...) {}
}
inline void BeforeFinish(PyObject* persistenceGlobals,PyThreadState* owner) noexcept {
  Errors errors;
  try {
    if(!persistenceGlobals || !Owned())return;
    for(auto* thread=PyInterpreterState_ThreadHead(owner->interp);thread;thread=PyThreadState_Next(thread))if(thread!=owner)return;
    auto* globals=PyDict_GetItemString(persistenceGlobals,"_INFINITY_CORE_OUTCOMES_GLOBALS");
    auto* state=globals?PyDict_GetItemString(globals,"state"):nullptr;
    if(state) {auto* result=PyObject_CallMethod(state,"uninstall",nullptr);Py_XDECREF(result);}
  } catch(...) {}
}
} // namespace InfinityCoreQA
#else
namespace InfinityCoreQA {
inline void BindLoadSink(int,PyObject*) noexcept {}
inline void Install(int,const std::string&,const std::string&,PyObject*) noexcept {}
inline void BeforeFinish(PyObject*,PyThreadState*) noexcept {}
}
#endif
