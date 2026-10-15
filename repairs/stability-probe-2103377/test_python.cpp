#include "threads/InfinityPythonWaitProbe.h"
#include <cassert>
#include <iostream>
int main(int argc,char** argv)
{
  assert(argc==2);Py_Initialize();InfinityStabilityProbe::Configure(argv[1]);
  auto* context=InfinityPythonWaitProbe::Start(42);assert(context);
  // Real CPython call/return and child-profile callbacks; no Kodi mock.
  int result=PyRun_SimpleString("import threading\n"
    "def wait():\n"
    "    sum([1,2,3])\n"
    "def run():\n"
    "    wait()\n"
    "t=threading.Thread(target=run)\n"
    "t.start()\n"
    "t.join()\n"
    "wait()\n");
  assert(result==0);assert(InfinityPythonWaitProbe::stack.size==0);
  InfinityPythonWaitProbe::BodyReturned();InfinityPythonWaitProbe::Retired(42);
  assert(!context->live.load());
  // Never overwrite a pre-existing user profiler.
  assert(PyRun_SimpleString("import sys\nsys.setprofile(lambda *args: None)\n")==0);
  assert(!InfinityPythonWaitProbe::Start(43));
  assert(PyRun_SimpleString("sys.setprofile(None)\n")==0);
  Py_Finalize();std::cout<<"real CPython parent/child profile and existing-profile protection passed\n";
}
