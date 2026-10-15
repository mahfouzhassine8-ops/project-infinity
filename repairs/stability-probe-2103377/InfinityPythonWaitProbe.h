#pragma once
#include "Python.h"
#include "threads/InfinityStabilityProbe.h"
#include <cstring>

namespace InfinityPythonWaitProbe
{
struct Frame { const char* unused{nullptr};std::string operation,location;int64_t since{0};int event{0}; };
struct Context { std::atomic<int> invoker{-1};std::atomic<bool> live{false}; };
inline std::array<Context,8> contexts;
struct Stack { std::array<Frame,12> frames;unsigned size{0},overflow{0}; };
inline thread_local Stack stack;
inline bool Interesting(const char* n)
{
  if(!n)return false;
  for(const char* value:{"connect","connect_ex","recv","recv_into","send","sendall","read","write",
      "do_handshake","wait","join","waitForAbort","getInfoLabel","getCondVisibility","executeJSONRPC",
      "execute","executemany","commit","rollback","close","getProperty","setProperty"})
    if(std::strcmp(n,value)==0)return true;
  return false;
}
inline void Publish(Context* context)
{
  if(stack.size) {
    const auto& f=stack.frames[stack.size-1];
    InfinityStabilityProbe::Python(context->invoker,f.operation.c_str(),f.location.c_str(),f.since);
  }else InfinityStabilityProbe::Python(context->invoker,"","",0);
}
inline int Event(Context* context,PyFrameObject* frame,int event,PyObject* arg)
{
  if(!context || !context->live.load())return 0;
  const bool call=event==PyTrace_CALL || event==PyTrace_C_CALL;
  const bool done=event==PyTrace_RETURN || event==PyTrace_C_RETURN || event==PyTrace_C_EXCEPTION;
  if(!call && !done)return 0;
  PyCodeObject* code=nullptr;const char* name=nullptr;
  if(event==PyTrace_C_CALL || event==PyTrace_C_RETURN || event==PyTrace_C_EXCEPTION) {
    if(PyCFunction_Check(arg))name=reinterpret_cast<PyCFunctionObject*>(arg)->m_ml->ml_name;
  }else {
    code=PyFrame_GetCode(frame);
    if(code)name=PyUnicode_AsUTF8(code->co_name);
  }
  if(!Interesting(name)){Py_XDECREF(code);return 0;}
  if(call) {
    if(stack.size>=stack.frames.size()){++stack.overflow;Py_XDECREF(code);return 0;}
    if(!code)code=PyFrame_GetCode(frame);
    const char* file=code?PyUnicode_AsUTF8(code->co_filename):nullptr;
    auto& f=stack.frames[stack.size++];f.operation=name;
    // No arguments, SQL text, account tokens, local variables or URL values.
    f.location=std::string(file?file:"")+":"+std::to_string(PyFrame_GetLineNumber(frame));
    f.since=InfinityStabilityProbe::Now();f.event=event;
  }else {
    if(stack.overflow){--stack.overflow;Py_XDECREF(code);return 0;}
    if(stack.size && stack.frames[stack.size-1].operation==name)--stack.size;
  }
  Publish(context);Py_XDECREF(code);return 0;
}
inline int Profile(PyObject* capsule,PyFrameObject* frame,int event,PyObject* arg)
{
  auto* c=static_cast<Context*>(PyCapsule_GetPointer(capsule,"infinity.wait.probe"));
  if(!c){PyErr_Clear();return 0;}
  // Preserve a pending application exception across diagnostic API calls.
  PyObject *type=nullptr,*value=nullptr,*trace=nullptr;PyErr_Fetch(&type,&value,&trace);
  try{Event(c,frame,event,arg);}catch(...){++InfinityStabilityProbe::overflow;}
  PyErr_Clear();PyErr_Restore(type,value,trace);return 0;
}
inline PyObject* ChildProfile(PyObject* capsule,PyObject* args)
{
  PyObject *frame=nullptr,*arg=nullptr;const char* event=nullptr;
  if(!PyArg_ParseTuple(args,"OsO",&frame,&event,&arg)){PyErr_Clear();Py_RETURN_NONE;}
  int what=std::strcmp(event,"call")==0?PyTrace_CALL:std::strcmp(event,"return")==0?PyTrace_RETURN:
    std::strcmp(event,"c_call")==0?PyTrace_C_CALL:std::strcmp(event,"c_return")==0?PyTrace_C_RETURN:
    std::strcmp(event,"c_exception")==0?PyTrace_C_EXCEPTION:-1;
  if(what>=0)Profile(capsule,reinterpret_cast<PyFrameObject*>(frame),what,arg);
  Py_RETURN_NONE;
}
inline PyMethodDef childDefinition={"_infinity_wait_profile",ChildProfile,METH_VARARGS,nullptr};
inline Context* Start(int invoker)
{
  PyObject* sys=PyImport_ImportModule("sys");if(!sys){PyErr_Clear();return nullptr;}
  PyObject* old=PyObject_CallMethod(sys,"getprofile",nullptr);Py_DECREF(sys);
  if(!old){PyErr_Clear();return nullptr;}
  const bool free=old==Py_None;Py_DECREF(old);if(!free)return nullptr;
  Context* c=nullptr;
  for(auto& candidate:contexts) {bool expected=false;if(candidate.live.compare_exchange_strong(expected,true)){c=&candidate;break;}}
  if(!c){++InfinityStabilityProbe::overflow;return nullptr;}
  c->invoker=invoker;
  PyObject* capsule=PyCapsule_New(c,"infinity.wait.probe",nullptr);
  if(!capsule){c->live.store(false);PyErr_Clear();return nullptr;}
  PyObject* threading=PyImport_ImportModule("threading");
  PyObject* child=PyCFunction_New(&childDefinition,capsule);
  if(threading && child) {
    PyObject* hook=PyObject_GetAttrString(threading,"_profile_hook");
    if(hook==Py_None) {PyObject* result=PyObject_CallMethod(threading,"setprofile","O",child);Py_XDECREF(result);}
    Py_XDECREF(hook);
  }
  Py_XDECREF(child);Py_XDECREF(threading);PyErr_Clear();
  stack.size=stack.overflow=0;PyEval_SetProfile(Profile,capsule);Py_DECREF(capsule);return c;
}
// Called on the owning interpreter with GIL before its bytecode leaves.
inline void BodyReturned() {PyEval_SetProfile(nullptr,nullptr);}
inline void Retired(int invoker)
{
  bool owned=false;
  for(auto& c:contexts)if(c.invoker.load()==invoker && c.live.load()){c.live.store(false);owned=true;}
  if(owned)InfinityStabilityProbe::Python(invoker,"","",0);
}
} // namespace InfinityPythonWaitProbe
