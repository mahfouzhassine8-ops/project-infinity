#include <Python.h>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <mutex>
#include <new>
#include <stdexcept>
#include <unistd.h>
static std::atomic<int> readMode{0};
static std::atomic<bool> readEntered{false};
static std::mutex readMutex;
static std::condition_variable readSignal;
static bool readReleased=false;
// Fixture-only delay/exception around the real local read. Production has no
// injected path; this checks GIL ownership and fd cleanup during blocked I/O.
static ssize_t fixture_read(int fd,void* bytes,size_t size) {
  if(readMode.load()==2) throw std::bad_alloc();
  if(readMode.load()==1 && !readEntered.exchange(true)) {
    readSignal.notify_all();
    std::unique_lock<std::mutex> lock(readMutex);
    if(!readSignal.wait_for(lock,std::chrono::seconds(2),[]{return readReleased;}))
      throw std::runtime_error("another Python thread could not acquire GIL");
    readMode.store(0);
  }
  return ::read(fd,bytes,size);
}
#define read fixture_read
#include "InfinityPromotionalDialog.h"
#undef read
#include <vector>
static std::vector<std::pair<std::string,bool>> observed;
static int closed=0;
static bool pending=false;
static PyObject* capture(const char* surface,InfinityPromotionalDialog::Surface type) {
  PyThreadState* originalThread=PyThreadState_Get();
  if(pending){PyErr_SetString(PyExc_ValueError,"original-pending-error");errno=EDOM;}
  const bool matched=InfinityPromotionalDialog::Capture(type);
  if(PyThreadState_Get()!=originalThread) {
    PyErr_Clear();return PyErr_Format(PyExc_AssertionError,"original interpreter thread state changed");
  }
  if(pending) {
    if(!PyErr_ExceptionMatches(PyExc_ValueError) || errno!=EDOM) {
      PyErr_Clear();return PyErr_Format(PyExc_AssertionError,"existing error/errno changed");
    }
    PyErr_Clear();
  }
  observed.emplace_back(surface,matched);Py_RETURN_TRUE;
}
static PyObject* show(PyObject*,PyObject*) {return capture("qr",InfinityPromotionalDialog::Surface::QrWindow);}
static PyObject* ok(PyObject*,PyObject*) {return capture("ok",InfinityPromotionalDialog::Surface::OkDialog);}
static PyObject* closeSurface(PyObject*,PyObject*) {++closed;Py_RETURN_NONE;}
static PyMethodDef surfaceMethods[]={{"show",show,METH_NOARGS,nullptr},{"ok",ok,METH_VARARGS,nullptr},{"close",closeSurface,METH_NOARGS,nullptr},{nullptr}};
static PyType_Slot surfaceSlots[]={{Py_tp_methods,surfaceMethods},{Py_tp_new,reinterpret_cast<void*>(PyType_GenericNew)},{0,nullptr}};
static PyType_Spec surfaceSpec={"promotion_probe.Surface",sizeof(PyObject),0,Py_TPFLAGS_DEFAULT,surfaceSlots};
static PyObject* reset(PyObject*,PyObject* value) {observed.clear();closed=0;pending=PyObject_IsTrue(value)==1;Py_RETURN_NONE;}
static PyObject* results(PyObject*,PyObject*) {
  PyObject* values=PyList_New(0);
  for(const auto& item:observed) {
    PyObject* pair=Py_BuildValue("(sO)",item.first.c_str(),item.second?Py_True:Py_False);
    PyList_Append(values,pair);Py_DECREF(pair);
  }
  PyObject* result=Py_BuildValue("{s:O,s:i}","events",values,"closed",closed);Py_DECREF(values);return result;
}
static PyObject* reenter(PyObject*,PyObject*) {
  if(InfinityPromotionalDialog::Capture(InfinityPromotionalDialog::Surface::OkDialog))
    return PyErr_Format(PyExc_AssertionError,"reentry classified as suppressible");
  Py_RETURN_NONE;
}
static PyObject* setReadMode(PyObject*,PyObject* value) {
  const long mode=PyLong_AsLong(value);if(PyErr_Occurred())return nullptr;
  std::lock_guard<std::mutex> lock(readMutex);readReleased=false;readEntered.store(false);readMode.store(mode);Py_RETURN_NONE;
}
static PyObject* entered(PyObject*,PyObject*) {return PyBool_FromLong(readEntered.load());}
static PyObject* releaseRead(PyObject*,PyObject*) {
  std::lock_guard<std::mutex> lock(readMutex);readReleased=true;readSignal.notify_all();Py_RETURN_NONE;
}
static PyMethodDef methods[]={{"reset",reset,METH_O,nullptr},{"results",results,METH_NOARGS,nullptr},{"reenter",reenter,METH_NOARGS,nullptr},
  {"read_mode",setReadMode,METH_O,nullptr},{"read_entered",entered,METH_NOARGS,nullptr},{"release_read",releaseRead,METH_NOARGS,nullptr},{nullptr}};
static PyModuleDef definition={PyModuleDef_HEAD_INIT,"promotion_probe",nullptr,-1,methods};
PyMODINIT_FUNC PyInit_promotion_probe() {
  PyObject* module=PyModule_Create(&definition);if(!module)return nullptr;
  PyObject* surface=PyType_FromSpec(&surfaceSpec);
  if(!surface || PyModule_AddObject(module,"Surface",surface)!=0){Py_XDECREF(surface);Py_DECREF(module);return nullptr;}
  return module;
}
