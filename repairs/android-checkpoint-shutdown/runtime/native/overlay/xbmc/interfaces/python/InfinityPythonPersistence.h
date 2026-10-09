#pragma once
// Python.h is included by the invoker before this header.
#include "InfinityPythonPersistenceSource.h"
#include "platform/android/activity/InfinityScriptPersistence.h"
#if !defined(INFINITY_SCRIPT_OBSERVER_HOST)
#include "filesystem/SpecialProtocol.h"
#endif
#include <cstdlib>
#include <cstring>
#include <frameobject.h>
#include <map>
#include <mutex>
#include <string>

namespace InfinityPythonPersistence
{
struct Context
{
  int id{-1};
  PyObject* globals{nullptr};
  PyObject* observer{nullptr};
  PyObject* connectionType{nullptr};
  bool retiring{false};
  bool finalized{false};
  bool preservePending{false};
  bool waitingWorkers{false};
  std::map<PyThreadState*,unsigned> checkedOpens;
  std::map<PyThreadState*,unsigned> readonlyChildren;
};
inline std::map<PyInterpreterState*,Context*>& Contexts()
{static auto* contexts=new std::map<PyInterpreterState*,Context*>;return *contexts;}
inline std::string Path(PyObject* value)
{
  if(PyLong_Check(value)) {
    const long fd=PyLong_AsLong(value);if(fd<0 || PyErr_Occurred()){PyErr_Clear();return {};}
    char target[PATH_MAX];const auto name="/proc/self/fd/"+std::to_string(fd);
    const auto size=::readlink(name.c_str(),target,sizeof(target)-1);
    if(size<=0)return {};
    target[size]='\0';
    struct stat info{};
    if(::fstat(static_cast<int>(fd),&info)==0 && S_ISREG(info.st_mode) && info.st_nlink==0)
      return {}; // Anonymous temporary files/memfd have no persistent namespace.
    // Sockets/pipes/stdout carry no persistent file contents.
    if(target[0]!='/')return {};
    return target;
  }
  PyObject* filesystem=PyOS_FSPath(value);if(!filesystem){PyErr_Clear();return {};}
  PyObject* bytes=PyUnicode_Check(filesystem)?PyUnicode_EncodeFSDefault(filesystem):filesystem;
  if(bytes!=filesystem)Py_DECREF(filesystem);
  if(!bytes){PyErr_Clear();return {};}
  std::string result;
  if(PyBytes_Check(bytes))result.assign(PyBytes_AS_STRING(bytes),static_cast<std::size_t>(PyBytes_GET_SIZE(bytes)));
  Py_DECREF(bytes);
#if !defined(INFINITY_SCRIPT_OBSERVER_HOST)
  result=CSpecialProtocol::TranslatePath(result);
#endif
  return result;
}
inline void Touch(Context* context,PyObject* path,bool present=true,bool directory=false)
{
  if(context->retiring){InfinityScriptPersistence::Fail(context->id,"write_during_interpreter_retirement");return;}
  const auto value=Path(path);
  if(value.empty() && PyLong_Check(path)) {
    struct stat info{};const long fd=PyLong_AsLong(path);
    if(fd<0 || PyErr_Occurred() || ::fstat(static_cast<int>(fd),&info)!=0 ||
       (S_ISREG(info.st_mode) && info.st_nlink!=0)) {
      PyErr_Clear();InfinityScriptPersistence::Fail(context->id,"persistent_descriptor_identity_unconfirmed");
    }
    return;
  }
  InfinityScriptPersistence::Touch(context->id,value,present,directory);
}
inline bool ReadonlyCommand(PyObject* executable,PyObject* command)
{
  if(!PyUnicode_Check(executable) || (!PyList_Check(command) && !PyTuple_Check(command)))return false;
  const auto count=PySequence_Size(command);
  const auto executableName=Path(executable);
  std::vector<std::string> expected;
  if(executableName=="/system/bin/logcat")
    expected={"/system/bin/logcat","--uid="+std::to_string(::getuid()),"-b","crash","-d","-t","200","-v","threadtime"};
#if defined(INFINITY_SCRIPT_OBSERVER_HOST)
  else if(executableName=="/bin/echo")expected={"/bin/echo","infinity-diagnostic-fixture"};
#endif
  else return false;
  if(count!=static_cast<Py_ssize_t>(expected.size()))return false;
  for(Py_ssize_t i=0;i<count;++i) {
    PyObject* item=PySequence_GetItem(command,i);
    const bool matches=item && PyUnicode_Check(item) && Path(item)==expected[i];
    Py_XDECREF(item);if(!matches)return false;
  }
  return true;
}

inline bool ApprovedBundledPythonExtension(const char* module,const std::string& filename)
{
  // Importing a native module is not itself a persistence write. Only the
  // exact Pillow images shipped by the signed Infinity APK may cross this
  // gate; all other add-on native extensions remain fail-closed.
  const char* libraries=std::getenv("KODI_ANDROID_LIBS");
  if(!module || !libraries || libraries[0]!='/' || filename.empty())return false;
  std::string root(libraries);
  while(root.size()>1 && root.back()=='/')root.pop_back();
  struct Extension{const char* module;const char* library;};
  static constexpr Extension approved[]={
    {"PIL._imaging","lib_imaging.so"},{"_imaging","lib_imaging.so"},
    {"PIL._imagingft","lib_imagingft.so"},{"_imagingft","lib_imagingft.so"},
    {"PIL._imagingmath","lib_imagingmath.so"},{"_imagingmath","lib_imagingmath.so"},
    {"PIL._imagingmorph","lib_imagingmorph.so"},{"_imagingmorph","lib_imagingmorph.so"},
    {"PIL._imagingtk","lib_imagingtk.so"},{"_imagingtk","lib_imagingtk.so"},
  };
  for(const auto& item:approved)
    if(std::strcmp(module,item.module)==0 && filename==root+"/"+item.library)return true;
  return false;
}
inline std::string NativeExtensionEvidence(const char* module,const std::string& filename)
{
  return "module="+std::string(module?module:"unknown").substr(0,256)+
         ";path="+filename.substr(0,1024);
}

inline std::string OpenEvidence(PyObject* path,long flags)
{
  // Diagnostic inspection must preserve any exception pending in the caller.
  PyObject *errorType=nullptr,*errorValue=nullptr,*errorTrace=nullptr;
  PyErr_Fetch(&errorType,&errorValue,&errorTrace);
  std::string result="path="+Path(path).substr(0,512)+";flags="+std::to_string(flags);
  auto* frame=PyEval_GetFrame();Py_XINCREF(frame);
  for(unsigned count=0;frame && count<4;++count) {
    auto* code=PyFrame_GetCode(frame);
    PyObject* filename=code?PyObject_GetAttrString(reinterpret_cast<PyObject*>(code),"co_filename"):nullptr;
    PyObject* name=code?PyObject_GetAttrString(reinterpret_cast<PyObject*>(code),"co_name"):nullptr;
    const char* file=filename && PyUnicode_Check(filename)?PyUnicode_AsUTF8(filename):nullptr;
    const char* function=name && PyUnicode_Check(name)?PyUnicode_AsUTF8(name):nullptr;
    result+=";frame="+std::string(file?file:"unknown").substr(0,160)+":"+
            std::to_string(PyFrame_GetLineNumber(frame))+":"+
            std::string(function?function:"unknown").substr(0,80);
    Py_XDECREF(filename);Py_XDECREF(name);Py_XDECREF(code);
    auto* back=PyFrame_GetBack(frame);Py_DECREF(frame);frame=back;
  }
  Py_XDECREF(frame);PyErr_Clear();PyErr_Restore(errorType,errorValue,errorTrace);
  return result;
}
inline int Audit(const char* event,PyObject* args,void*)
{
  auto* thread=PyThreadState_Get();if(!thread)return 0;
  const auto found=Contexts().find(thread->interp);if(found==Contexts().end())return 0;
  auto* context=found->second;
  const auto count=PyTuple_Check(args)?PyTuple_GET_SIZE(args):0;
  const auto at=[&](Py_ssize_t n){return n<count?PyTuple_GET_ITEM(args,n):Py_None;};
  if(std::strcmp(event,"open")==0 && count>=3) {
    const auto flags=PyLong_Check(at(2))?PyLong_AsLong(at(2)):0;
    if((flags&(O_WRONLY|O_RDWR|O_CREAT|O_TRUNC|O_APPEND))!=0) {
      if(!context->checkedOpens[thread])
        InfinityScriptPersistence::Fail(context->id,"file_open_bypassed_checked_buffer_observer",
                                        OpenEvidence(at(0),flags));
      // A checked adapter registers the actual returned descriptor. This also
      // handles custom openers and anonymous temporary files without a fake path.
      if(!context->checkedOpens[thread])Touch(context,at(0));
    }
  }
  else if(std::strcmp(event,"os.rename")==0 && count>=2) {
    if(count>2 && ((PyLong_Check(at(2)) && PyLong_AsLong(at(2))!=-1) ||
                   (PyLong_Check(at(3)) && PyLong_AsLong(at(3))!=-1)))
      InfinityScriptPersistence::Fail(context->id,"unobserved_directory_relative_rename");
    Touch(context,at(0),false);Touch(context,at(1));
  }
  else if(std::strcmp(event,"os.remove")==0 || std::strcmp(event,"os.rmdir")==0) {
    if(count>1 && PyLong_Check(at(1)) && PyLong_AsLong(at(1))!=-1)
      InfinityScriptPersistence::Fail(context->id,"unobserved_directory_relative_deletion");
    if(count)Touch(context,at(0),false);
  }
  else if(std::strcmp(event,"os.mkdir")==0) {
    if(count>2 && PyLong_Check(at(2)) && PyLong_AsLong(at(2))!=-1)
      InfinityScriptPersistence::Fail(context->id,"unobserved_directory_relative_directory_creation");
    if(count)Touch(context,at(0),true,true);
  }
  else if(std::strcmp(event,"os.truncate")==0) {if(count)Touch(context,at(0));}
  else if(std::strcmp(event,"sys.unraisablehook")==0)
    InfinityScriptPersistence::Fail(context->id,"unraisable_python_cleanup_or_write_failure");
  else if(std::strcmp(event,"import")==0 && count>=2) {
    const auto filename=at(1)==Py_None?std::string{}:Path(at(1));
    const char* module=PyUnicode_Check(at(0))?PyUnicode_AsUTF8(at(0)):nullptr;
    if(module && (std::strcmp(module,"_dbm")==0 || std::strcmp(module,"_gdbm")==0))
      InfinityScriptPersistence::Fail(context->id,"unobserved_dbm_persistence_backend");
    if(filename.size()>=3 && filename.compare(filename.size()-3,3,".so")==0 &&
       filename.find("/lib-dynload/")==std::string::npos &&
       !ApprovedBundledPythonExtension(module,filename))
      InfinityScriptPersistence::Fail(context->id,"unclassified_addon_native_extension",
                                      NativeExtensionEvidence(module,filename));
  }
  else if(std::strcmp(event,"os.chmod")==0 || std::strcmp(event,"os.chown")==0 ||
          std::strcmp(event,"os.utime")==0 || std::strcmp(event,"os.setxattr")==0 ||
          std::strcmp(event,"os.removexattr")==0 || std::strcmp(event,"os.link")==0 ||
          std::strcmp(event,"os.symlink")==0 || std::strcmp(event,"mmap.__new__")==0 ||
          std::strcmp(event,"sqlite3.load_extension")==0 ||
          std::strcmp(event,"sqlite3.enable_load_extension")==0)
    InfinityScriptPersistence::Fail(context->id,"unclassified_native_persistence_operation");
  else if(std::strcmp(event,"sqlite3.connect/handle")==0) {
    if(!context->connectionType || count!=1 || PyObject_IsInstance(at(0),context->connectionType)!=1)
      InfinityScriptPersistence::Fail(context->id,"sqlite_connection_bypassed_checked_commit_observer");
  }
  else if(std::strcmp(event,"subprocess.Popen")==0) {
    if(!context->readonlyChildren[thread] || count<4 || !ReadonlyCommand(at(0),at(1)) || at(3)!=Py_None)
      InfinityScriptPersistence::Fail(context->id,"external_or_opaque_writer_requires_explicit_participant");
  }
  else if(std::strcmp(event,"os.posix_spawn")==0) {
    if(!context->readonlyChildren[thread] || count<2 || !ReadonlyCommand(at(0),at(1)))
      InfinityScriptPersistence::Fail(context->id,"external_or_opaque_writer_requires_explicit_participant");
  }
  else if(std::strcmp(event,"os.system")==0 ||
          std::strcmp(event,"os.fork")==0 || std::strcmp(event,"os.posix_spawn")==0 ||
          std::strcmp(event,"os.exec")==0 || std::strcmp(event,"os.forkpty")==0 ||
          std::strcmp(event,"ctypes.dlopen")==0 || std::strcmp(event,"ctypes.dlsym")==0 ||
          std::strcmp(event,"ctypes.dlsym/handle")==0 || std::strcmp(event,"ctypes.call_function")==0)
    InfinityScriptPersistence::Fail(context->id,"external_or_opaque_writer_requires_explicit_participant");
  // An audit observer does not alter original add-on operations or clear their
  // Python exceptions. Its failure persists in the native owner ledger.
  return 0;
}
inline Context* Capsule(PyObject* self)
{return static_cast<Context*>(PyCapsule_GetPointer(self,"Infinity.Persistence.Observer"));}
inline PyObject* Error(PyObject* self,PyObject* args)
{
  auto* context=Capsule(self);const char* reason=nullptr;
  if(!context || !PyArg_ParseTuple(args,"s",&reason))return nullptr;
  InfinityScriptPersistence::Fail(context->id,reason);Py_RETURN_NONE;
}
inline PyObject* Mutation(PyObject* self,PyObject* args)
{
  auto* context=Capsule(self);PyObject* path=nullptr;const char* kind=nullptr;
  if(!context || !PyArg_ParseTuple(args,"Os",&path,&kind))return nullptr;
  if(std::strcmp(kind,"readonly-child-begin")==0) {
    ++context->readonlyChildren[PyThreadState_Get()];Py_RETURN_NONE;
  }
  if(std::strcmp(kind,"readonly-child-end")==0) {
    auto& depth=context->readonlyChildren[PyThreadState_Get()];
    if(depth)--depth;else InfinityScriptPersistence::Fail(context->id,"unbalanced_readonly_child_scope");
    Py_RETURN_NONE;
  }
  if(std::strcmp(kind,"checked-open-begin")==0) {
    ++context->checkedOpens[PyThreadState_Get()];Py_RETURN_NONE;
  }
  if(std::strcmp(kind,"checked-open-end")==0) {
    auto& depth=context->checkedOpens[PyThreadState_Get()];
    if(depth)--depth;else InfinityScriptPersistence::Fail(context->id,"unbalanced_checked_open_scope");
    Py_RETURN_NONE;
  }
  Touch(context,path,std::strcmp(kind,"delete")!=0,std::strcmp(kind,"directory")==0);
  if(std::strcmp(kind,"sqlite")==0)InfinityScriptPersistence::SQLiteCompanions(context->id,Path(path));
  Py_RETURN_NONE;
}
inline Context* Start(int id,PyInterpreterState* interpreter)
{
  if(!InfinityScriptPersistence::Pending(id))return nullptr;
  static bool installed=false;
  if(!installed) {
    if(PySys_AddAuditHook(Audit,nullptr)!=0){InfinityScriptPersistence::Fail(id,"native_python_audit_hook_unavailable");return nullptr;}
    installed=true;
  }
  const auto existing=Contexts().find(interpreter);
  if(existing!=Contexts().end())return existing->second; // Reusable interpreter keeps all admitted writes.
  auto* context=new Context;context->id=id;Contexts()[interpreter]=context;
  context->globals=PyDict_New();
  PyObject* name=PyUnicode_FromString("_infinity_native_persistence_observer");
  PyDict_SetItemString(context->globals,"__name__",name);Py_DECREF(name);
  PyObject* result=PyRun_String(INFINITY_PYTHON_PERSISTENCE_SOURCE,Py_file_input,context->globals,context->globals);
  if(result)Py_DECREF(result);
  static PyMethodDef errorMethod={"record_failure",Error,METH_VARARGS,nullptr};
  static PyMethodDef mutationMethod={"record_mutation",Mutation,METH_VARARGS,nullptr};
  PyObject* capsule=PyCapsule_New(context,"Infinity.Persistence.Observer",nullptr);
  PyObject* error=PyCFunction_NewEx(&errorMethod,capsule,nullptr);
  PyObject* mutation=PyCFunction_NewEx(&mutationMethod,capsule,nullptr);
  PyObject* vfs=PyImport_ImportModule("xbmcvfs");
#if defined(INFINITY_SCRIPT_OBSERVER_HOST)
  if(!vfs){PyErr_Clear();vfs=Py_None;Py_INCREF(vfs);}
#endif
  PyObject* klass=PyDict_GetItemString(context->globals,"Observer");
  PyObject* hostProbe=Py_False;
#if defined(INFINITY_SCRIPT_OBSERVER_HOST)
  hostProbe=Py_True;
#endif
  if(klass && !PyErr_Occurred() && vfs)
    context->observer=PyObject_CallFunctionObjArgs(klass,error,mutation,vfs,hostProbe,nullptr);
  Py_XDECREF(vfs);Py_XDECREF(error);Py_XDECREF(mutation);Py_XDECREF(capsule);
  if(context->observer)context->connectionType=PyObject_GetAttrString(context->observer,"connection_type");
  if(!context->observer || !context->connectionType || PyErr_Occurred())
    InfinityScriptPersistence::Fail(id,"checked_python_observer_initialization_failed");
  else InfinityScriptPersistence::Observed(id);
  return context;
}
inline void Finish(Context* context,PyThreadState* owner)
{
  if(!context)return;
  context->waitingWorkers=false;
  for(auto* thread=PyInterpreterState_ThreadHead(owner->interp);thread;thread=PyThreadState_Next(thread))
    if(thread!=owner){context->waitingWorkers=true;return;}
  if(context->observer) {
    PyObject* result=PyObject_CallMethod(context->observer,"finish",nullptr);
    if(result) {
      context->finalized=PyObject_IsTrue(result)==1;Py_DECREF(result);
      if(!context->finalized)context->preservePending=true;
    }
    else {
      InfinityScriptPersistence::Fail(context->id,"checked_python_observer_finalization_failed");
      context->preservePending=true;
    }
  }
  if(context->preservePending)return;
  context->retiring=true;
  Py_CLEAR(context->observer);Py_CLEAR(context->connectionType);Py_CLEAR(context->globals);
}
inline void End(Context* context,PyInterpreterState* interpreter)
{
  if(!context)return;
  Contexts().erase(interpreter);
  if(context->finalized)InfinityScriptPersistence::Retired(context->id);
  delete context;
}
} // namespace InfinityPythonPersistence
