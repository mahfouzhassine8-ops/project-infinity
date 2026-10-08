#include "InfinityPythonAbort.h"
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <future>
#include <iostream>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
using namespace std::chrono_literals;
struct Gate {
  std::mutex mutex;
  std::condition_variable cv;
  bool opened=false, cleanup=false;
  PyThreadState* target=nullptr;
  std::promise<void> entered, returned;
  std::atomic<int> saves{0};
  std::atomic<bool> systemExit{false};
};
Gate gates[4];
bool normal=false;
int targets=1;
std::string outdir;
PyObject* gate_wait(PyObject*,PyObject* args) {
  int i; if(!PyArg_ParseTuple(args,"i",&i))return nullptr;
  auto& g=gates[i];g.target=PyThreadState_Get();g.entered.set_value();
  Py_BEGIN_ALLOW_THREADS
  {std::unique_lock<std::mutex> lock(g.mutex);g.cv.wait(lock,[&g]{return g.opened;});}
  Py_END_ALLOW_THREADS
  Py_RETURN_NONE;
}
PyObject* save(PyObject*,PyObject* args) {
  int i;if(!PyArg_ParseTuple(args,"i",&i))return nullptr;
  ++gates[i].saves;
  {std::ofstream f(outdir+"/saved-"+std::to_string(i));f<<"saved in finally";}
  Py_RETURN_NONE;
}
PyMethodDef methods[]={{"wait",gate_wait,METH_VARARGS,nullptr},{"save",save,METH_VARARGS,nullptr},{nullptr,nullptr,0,nullptr}};
PyModuleDef mod={PyModuleDef_HEAD_INIT,"_exit_test",nullptr,-1,methods,nullptr,nullptr,nullptr,nullptr};
PyMODINIT_FUNC PyInit__exit_test(){return PyModule_Create(&mod);}

// Same operation as the exact parent CPythonInvoker abort branch.
void parent_request(PyThreadState* helper) {
  PyThreadState* state=PyInterpreterState_ThreadHead(PyThreadState_GetInterpreter(helper));
  while(state) {
    Py_XDECREF(state->async_exc);
    state->async_exc=PyExc_SystemExit;
    Py_XINCREF(state->async_exc);
    state=PyThreadState_Next(state);
  }
}
void repaired_request(PyThreadState* helper) {
  int count=0;
  InfinityPythonAbort::RequestSystemExit(helper,[&](unsigned long id,int matched){
    assert(id!=helper->thread_id && matched==1);++count;
  });
  assert(count==targets);
}
void request(bool repaired) {
  PyThreadState* helper=PyThreadState_New(PyThreadState_GetInterpreter(gates[0].target));assert(helper);
  PyEval_RestoreThread(helper);
  if(repaired)repaired_request(helper);else parent_request(helper);
  assert(gates[1].target->async_exc==nullptr); // unrelated sub-interpreter untouched
  if(repaired)assert(helper->async_exc==nullptr); // never abort the helper
  PyThreadState_Clear(helper);PyThreadState_DeleteCurrent();
}
void worker(int i) {
  PyThreadState* main=PyThreadState_New(PyInterpreterState_Main());assert(main);
  PyEval_RestoreThread(main);
  PyThreadState* child=nullptr;
  if(i<2) { child=Py_NewInterpreter();assert(child); }
  else {
    // The owner holds interpreter lifetime until these child threads join.
    child=PyThreadState_New(PyThreadState_GetInterpreter(gates[0].target));assert(child);
    PyThreadState_Swap(child);
  }
  std::string code="import _exit_test\ntry:\n    _exit_test.wait("+std::to_string(i)+")\n";
  code+=((i!=1 && !normal)?"    while True:\n        pass\n":"    pass\n");
  code+="finally:\n    _exit_test.save("+std::to_string(i)+")\n";
  PyObject* globals=PyModule_GetDict(PyImport_AddModule("__main__"));
  PyObject* ret=PyRun_StringFlags(code.c_str(),Py_file_input,globals,globals,nullptr);
  gates[i].systemExit=PyErr_ExceptionMatches(PyExc_SystemExit);Py_XDECREF(ret);PyErr_Clear();
  PyEval_SaveThread();gates[i].returned.set_value();
  {std::unique_lock<std::mutex> lock(gates[i].mutex);gates[i].cv.wait(lock,[i]{return gates[i].cleanup;});}
  PyEval_RestoreThread(child);
  if(i<2)Py_EndInterpreter(child);
  else {PyThreadState_Clear(child);PyThreadState_Swap(main);PyThreadState_Delete(child);}
  PyThreadState_Swap(main);PyThreadState_Clear(main);PyThreadState_DeleteCurrent();
}
void open(int i) {
  {std::lock_guard<std::mutex> l(gates[i].mutex);gates[i].opened=true;}gates[i].cv.notify_all();
}
void cleanup(int i) {
  {std::lock_guard<std::mutex> l(gates[i].mutex);gates[i].cleanup=true;}gates[i].cv.notify_all();
}
void savedOnce(int i,bool exited) {
  assert(gates[i].systemExit==exited && gates[i].saves==1);
  std::ifstream f(outdir+"/saved-"+std::to_string(i));std::string s;std::getline(f,s);
  assert(s=="saved in finally");
}
int main(int argc,char**argv){
  assert(argc==3);const std::string mode=argv[1];const bool repaired=mode!="parent";
  normal=mode=="normal";bool group=mode=="group";outdir=argv[2];targets=group?3:1;
  assert(mode=="parent" || mode=="repair" || mode=="group" || normal);
  PyImport_AppendInittab("_exit_test",PyInit__exit_test);
  PyConfig config;PyConfig_InitIsolatedConfig(&config);config.site_import=0;
  PyStatus init=Py_InitializeFromConfig(&config);PyConfig_Clear(&config);
  if(PyStatus_Exception(init))Py_ExitStatusException(init);
  PyThreadState* master=PyEval_SaveThread();
  std::future<void> entered[4],returned[4];
  for(int i=0;i<4;++i){entered[i]=gates[i].entered.get_future();returned[i]=gates[i].returned.get_future();}
  std::thread a(worker,0),b(worker,1);entered[0].wait();entered[1].wait();
  std::thread c,d;
  if(group){c=std::thread(worker,2);d=std::thread(worker,3);entered[2].wait();entered[3].wait();}
  if(!normal)request(repaired);
  open(0);
  const bool finished=returned[0].wait_for(500ms)==std::future_status::ready;
  std::cout<<"Python "<<PY_VERSION<<" mode="<<mode<<" finished_without_rescue="<<finished<<std::endl;
  if(repaired)assert(finished);
  else {assert(!finished);request(true);assert(returned[0].wait_for(3s)==std::future_status::ready);}
  savedOnce(0,!normal);
  if(group) {
    // Staggered reacquisition: first thread consumes its interrupt before the
    // remaining threads leave native waits. Each must still receive its own.
    for(int i=2;i<4;++i){open(i);assert(returned[i].wait_for(3s)==std::future_status::ready);savedOnce(i,true);}
    cleanup(2);cleanup(3);c.join();d.join();
  }
  assert(returned[1].wait_for(0ms)==std::future_status::timeout && gates[1].saves==0);
  open(1);assert(returned[1].wait_for(3s)==std::future_status::ready);savedOnce(1,false);
  cleanup(0);cleanup(1);a.join();b.join();PyEval_RestoreThread(master);
  // Empty target set: the calling thread must not interrupt itself.
  int count=0;InfinityPythonAbort::RequestSystemExit(master,[&](unsigned long,int){++count;});
  assert(count==0 && master->async_exc==nullptr);
  assert(PyThreadState_SetAsyncExc(0,PyExc_SystemExit)==0);
  assert(Py_FinalizeEx()==0);
  std::cout<<"PASS: finally persistence, interpreter isolation, helper exclusion, real joins and finalization\n";
}
