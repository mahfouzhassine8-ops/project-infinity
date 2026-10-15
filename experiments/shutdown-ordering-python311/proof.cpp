// CPython shutdown ordering test, isolated host-only. Never builds Infinity or patches Kodi.
// Compile with: g++ -std=c++17 -O2 proof.cpp -o proof $(python3.11-config --includes --embed --ldflags)
#include <Python.h>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <thread>

static bool Exec(const std::string& source) {
  PyObject* module = PyImport_AddModule("__main__");
  PyObject* globals = module ? PyModule_GetDict(module) : nullptr;
  PyObject* result = globals ? PyRun_StringFlags(source.c_str(), Py_file_input, globals, globals, nullptr) : nullptr;
  if (!result || PyErr_Occurred()) { PyErr_Print(); return false; }
  Py_DECREF(result);
  return true;
}
static int Children(PyThreadState* owner) {
  int result = 0;
  for (PyThreadState* t=PyInterpreterState_ThreadHead(owner->interp); t; t=PyThreadState_Next(t))
    if (t != owner) ++result;
  return result;
}
static void GILSleep(PyThreadState* owner, int milliseconds) {
  PyEval_ReleaseThread(owner);
  std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
  PyEval_AcquireThread(owner);
}
static bool ShutdownThreading() {
  PyObject* modules = PyImport_GetModuleDict();
  PyObject* threading = modules ? PyDict_GetItemString(modules, "threading") : nullptr;
  if (!threading) { std::puts("ERROR_THREADING_MODULE_MISSING"); return false; }
  PyObject* ret = PyObject_CallMethod(threading, "_shutdown", nullptr);
  if (!ret) { std::puts("THREADING_SHUTDOWN_FAILED"); PyErr_Print(); return false; }
  Py_DECREF(ret);
  std::puts("THREADING_SHUTDOWN_COMPLETED");
  return true;
}
static int EndSafely(PyThreadState* mainTs, PyThreadState* subTs) {
  if (Children(subTs) != 0) { std::puts("FAIL_UNRETIRED_WORKERS"); return 60; }
  PyGC_Collect();
  PyObject* modules = PyImport_GetModuleDict();
  if (!modules) return 61;
  PyDict_Clear(modules);
  PyGC_Collect();
  if (PyErr_Occurred()) { PyErr_Print(); return 62; }
  std::puts("EARLY_MODULE_CLEANUP_FINISHED");
  Py_EndInterpreter(subTs);
  PyThreadState_Swap(mainTs);
  int status=Py_FinalizeEx();
  std::printf("PYTHON_FINALIZE_STATUS=%d\n", status);
  return status==0 ? 0 : 63;
}
int main(int argc, char** argv) {
  setvbuf(stdout,nullptr,_IONBF,0);
  if(argc<2) return 2;
  const std::string mode(argv[1]);
  Py_Initialize();
  PyThreadState* mainTs=PyThreadState_Get();
  PyThreadState* subTs=Py_NewInterpreter();
  if(!subTs) { PyErr_Print(); return 3; }
  if(mode=="baseline" || mode=="ordered" || mode=="reuse") {
    if(!Exec(R"PY(
from concurrent.futures import ThreadPoolExecutor
GLOBAL_POOL=ThreadPoolExecutor(max_workers=1)
assert GLOBAL_POOL.submit(lambda: 100).result(timeout=2)==100
print('INITIAL_FUTURE_COMPLETE',flush=True)
)PY")) return 4;
    if(mode=="reuse" && !Exec(R"PY(
assert GLOBAL_POOL.submit(lambda: 101).result(timeout=2)==101
print('REUSE_FUTURE_COMPLETE',flush=True)
)PY")) return 5;
    std::printf("CHILDREN_BEFORE=%d\n",Children(subTs));
    if(mode=="baseline") {
      GILSleep(subTs,350);
      int remain=Children(subTs);
      std::printf("BASELINE_CHILDREN_AFTER_350MS=%d\n",remain);
      std::puts("BASELINE_NOT_CLEANLY_FINALIZED_BY_DESIGN");
      std::_Exit(remain>0 ? 0:10);
    }
  } else if(mode=="sqlite" || mode=="savefail") {
    if(argc<3)return 6;
    const std::string code = std::string(R"PY(
import sqlite3,threading
proof_path=)PY") + "'" + argv[2] + "'" + R"PY(
conn=sqlite3.connect(proof_path)
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('CREATE TABLE IF NOT EXISTS persisted(value INTEGER)')
conn.commit()
conn.execute('INSERT INTO persisted(value) VALUES (2026)')
def persist_at_shutdown():
    print('PERSISTENCE_CALLBACK_ENTERED',flush=True)
    if INJECTED_FAILURE:
        raise OSError('intentional save failure')
    conn.commit()
    conn.close()
    print('PERSISTENCE_CALLBACK_COMMITTED',flush=True)
threading._register_atexit(persist_at_shutdown)
)PY";
    if(!Exec(std::string(mode=="savefail"?"INJECTED_FAILURE=True\n":"INJECTED_FAILURE=False\n")+code))return 7;
  } else if(mode=="hang") {
    if(!Exec(R"PY(
import threading
STUCK=threading.Event()
def bad_shutdown_callback():
    print('STUCK_CALLBACK_ENTERED',flush=True)
    STUCK.wait(60)
threading._register_atexit(bad_shutdown_callback)
)PY")) return 8;
    std::printf("CHILDREN_BEFORE=%d\n",Children(subTs));
  } else if(mode=="moduleclear") {
    if(argc<3) return 9;
    std::string code=std::string(R"PY(
import threading
marker_path=)PY")+"'"+argv[2]+"'"+R"PY(
def callback():
    with open(marker_path,'w') as out: out.write('cleanup ran')
    print('ATEXIT_CALLBACK_EXECUTED',flush=True)
threading._register_atexit(callback)
)PY";
    if(!Exec(code))return 10;
    PyObject* modules=PyImport_GetModuleDict();
    PyDict_Clear(modules);
    std::puts("MODULES_CLEARED_BEFORE_PY_END_INTERPRETER");
    Py_EndInterpreter(subTs);
    PyThreadState_Swap(mainTs);
    int rc=Py_FinalizeEx();
    std::printf("PYTHON_FINALIZE_STATUS=%d\n",rc);
    return rc==0?0:11;
  } else if(mode=="blockedworker") {
    if(!Exec(R"PY(
import threading
from concurrent.futures import ThreadPoolExecutor
RELEASE=threading.Event()
POOL=ThreadPoolExecutor(max_workers=1)
FUT=POOL.submit(RELEASE.wait)
print('BLOCKING_WORKER_STARTED',flush=True)
)PY"))return 12;
    GILSleep(subTs,250);
    int active=Children(subTs);
    std::printf("BLOCKING_WORKER_ACTIVE=%d\n",active);
    if(active==0)return 13;
    std::puts("NO_PERSISTENCE_RECEIPT_WHILE_WORKER_ACTIVE");
    if(!Exec("RELEASE.set()\nassert FUT.result(timeout=2)\nprint('WORKER_RELEASED_COOPERATIVELY',flush=True)\n"))return 14;
  } else return 15;
  if(!ShutdownThreading()) {
    std::puts("NO_CLEAN_RETIREMENT_RECEIPT");
    // Negative subprocess terminates deliberately. This is NOT a clean exit.
    std::_Exit(mode=="savefail" ? 0 : 21);
  }
  std::printf("CHILDREN_AFTER=%d\n",Children(subTs));
  if(Children(subTs)!=0)return 16;
  std::puts("RETIREMENT_PRECONDITIONS_SATISFIED");
  return EndSafely(mainTs,subTs);
}
