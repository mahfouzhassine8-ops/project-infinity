#include <Python.h>
#include "InfinityPromotionalDialog.h"
#include <vector>
static std::vector<std::pair<std::string,bool>> observed;
static int closed=0;
static bool pending=false;
static PyObject* capture(const char* surface,InfinityPromotionalDialog::Surface type) {
  if(pending){PyErr_SetString(PyExc_ValueError,"original-pending-error");errno=EDOM;}
  const bool matched=InfinityPromotionalDialog::Capture(type);
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
static PyMethodDef methods[]={{"reset",reset,METH_O,nullptr},{"results",results,METH_NOARGS,nullptr},{"reenter",reenter,METH_NOARGS,nullptr},{nullptr}};
static PyModuleDef definition={PyModuleDef_HEAD_INIT,"promotion_probe",nullptr,-1,methods};
PyMODINIT_FUNC PyInit_promotion_probe() {
  PyObject* module=PyModule_Create(&definition);if(!module)return nullptr;
  PyObject* surface=PyType_FromSpec(&surfaceSpec);
  if(!surface || PyModule_AddObject(module,"Surface",surface)!=0){Py_XDECREF(surface);Py_DECREF(module);return nullptr;}
  return module;
}
