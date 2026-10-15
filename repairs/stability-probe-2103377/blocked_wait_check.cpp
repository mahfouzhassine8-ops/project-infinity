#include "threads/InfinityPythonWaitProbe.h"
#include <cassert>
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
int main(int argc,char** argv)
{
  assert(argc==2);Py_Initialize();InfinityStabilityProbe::Configure(argv[1]);
  auto* context=InfinityPythonWaitProbe::Start(99);assert(context);
  std::thread observer([]{
    bool blocked=false;
    for(unsigned attempt=0;attempt<1000;++attempt) {
      bool sleeping=false,waiting=false;
      for(auto& t:InfinityStabilityProbe::threads) {
        if(!t.tid.load() || t.invoker.load()!=99)continue;
        const auto op=InfinityStabilityProbe::Load(t.operation);
        sleeping|=op=="sleep";waiting|=op=="acquire";
      }
      if(sleeping && waiting){blocked=true;break;}
      std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
    assert(blocked);
    InfinityStabilityProbe::Snapshot("real_python_blocked_wait");
  });
  assert(PyRun_SimpleString("import threading,time\n"
    "t=threading.Thread(target=lambda: time.sleep(2))\n"
    "t.start()\nt.join()\n")==0);
  observer.join();
  InfinityPythonWaitProbe::BodyReturned();InfinityPythonWaitProbe::Retired(99);
  std::ifstream stream(argv[1]);std::string row((std::istreambuf_iterator<char>(stream)),{});
  assert(row.find("\"python_operation\":\"sleep\"")!=std::string::npos);
  assert(row.find("\"python_operation\":\"acquire\"")!=std::string::npos);
  Py_Finalize();std::cout<<"Observed real child sleep and parent synchronization wait while both were blocked\n";
}
