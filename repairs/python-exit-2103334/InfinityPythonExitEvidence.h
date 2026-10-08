/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include <Python.h>
#include <frameobject.h>
#include <array>
#include <cstring>

namespace InfinityPythonExitEvidence
{
// Diagnostic only, called with the existing abort helper's GIL. No locals,
// argument values, source lines, full paths or URLs are collected. Bound both
// thread count and stack depth, and preserve the caller's pending exception.
inline const char* Basename(const char* path)
{
  if (!path) return "";
  const char* result=path;
  for (const char* p=path;*p;++p)
    if (*p=='/' || *p=='\\') result=p+1;
  return result;
}
template<class Observer>
inline void Capture(PyThreadState* caller, Observer observe)
{
  if (!caller || PyThreadState_Get()!=caller) return;
  PyObject *errorType=nullptr,*errorValue=nullptr,*errorTrace=nullptr;
  PyErr_Fetch(&errorType,&errorValue,&errorTrace);
  struct Snapshot { unsigned long id{}; PyFrameObject* frame{}; };
  std::array<Snapshot,8> snapshots{};
  size_t count=0;
  for (auto* s=PyInterpreterState_ThreadHead(PyThreadState_GetInterpreter(caller));
       s && count<snapshots.size(); s=PyThreadState_Next(s))
  {
    if (s==caller || s->thread_id==caller->thread_id) continue;
    snapshots[count++]={s->thread_id,PyThreadState_GetFrame(s)};
  }
  for (size_t i=0;i<count;++i)
  {
    auto* frame=snapshots[i].frame;
    if (!frame) observe(snapshots[i].id,"","",0);
    for (unsigned depth=0; frame && depth<4; ++depth)
    {
      PyCodeObject* code=PyFrame_GetCode(frame);
      if (code)
      {
        const char* file=PyUnicode_AsUTF8(code->co_filename);
        const char* function=PyUnicode_AsUTF8(code->co_name);
        observe(snapshots[i].id,Basename(file),function ? function : "",PyFrame_GetLineNumber(frame));
        Py_DECREF(code);
      }
      PyFrameObject* back=PyFrame_GetBack(frame);
      Py_DECREF(frame);frame=back;
    }
    Py_XDECREF(frame);
  }
  PyErr_Clear();PyErr_Restore(errorType,errorValue,errorTrace);
}
} // namespace InfinityPythonExitEvidence
