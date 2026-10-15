#include "InfinityVfsOpenTrace.h"
#include <filesystem>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <iostream>
#include <vector>
namespace T=InfinityShutdownTrace;
namespace V=InfinityVfsOpenTrace;
int main(int argc,char** argv)
{
  if(argc!=3)return 2;
  std::filesystem::create_directories(argv[2]);T::Configure(argv[2]);
  const std::string test=argv[1];
  if(test=="late_after_noise")
  {
    int file=0;std::mutex mutex;std::condition_variable cv;bool active=false,finish=false;
    std::thread worker([&]{
      V::Invoker invoker(5,true);
      V::Open operation(V::Scheme::Https);operation.Bind(&file,V::Backend::Curl,true);
      V::Mark(V::Stage::CurlPoll);
      {std::unique_lock<std::mutex> lock(mutex);active=true;cv.notify_all();cv.wait(lock,[&]{return finish;});}
      V::CancelFlagSeen();operation.Returned(false);
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return active;});}
    T::Begin();V::CheckpointBegin(1);
    for(unsigned i=0;i<20000;++i){T::Scope sql("sqlite.commit");}
    for(unsigned i=0;i<50000;++i){
      T::Event("milestone","vfs.detail.noise");
      T::Event("milestone","vfs.native.scope_return");
    }
    V::Request(5,"cooperative_stop_called");
    {V::Callback callback(&file);callback.FlagSet();
      {std::lock_guard<std::mutex> lock(mutex);finish=true;cv.notify_all();}
      worker.join();}
    V::Milestone(5,"vfs.python.interpreter_retired","no_durability_receipt");
    V::CheckpointOutcome(1,false);
    V::OwnerStatus(1,"native_databases",4,3,true,false,true,1);
    V::FlushCheckpoint();
    if(T::fastScopes[1].calls.load()<19000)return 3;
  }
  else if(test=="lanes_independent")
  {
    T::Begin();
    const char* phases[]={"vfs.checkpoint.noise","vfs.backend.cancellation","vfs.python.noise",
      "vfs.shutdown.request","vfs.native.scope_return","scripts.noise"};
    std::vector<std::thread> workers;
    for(unsigned i=0;i<6;++i)workers.emplace_back([&,i]{
      for(unsigned n=0;n<12000;++n)T::Event("milestone",phases[i]);
    });
    for(auto& t:workers)t.join();
    for(unsigned i=0;i<6;++i)
      if(T::retainedBytes[i].load()>T::LANE_BYTES[i] || !T::droppedRows[i].load())return 4;
  }
  else if(test=="native_slow_after_noise")
  {
    std::mutex mutex;std::condition_variable cv;bool active=false,finish=false;
    T::Begin();
    std::thread worker([&]{
      T::Scope sql("sqlite.commit");
      {std::unique_lock<std::mutex> lock(mutex);active=true;cv.notify_all();cv.wait(lock,[&]{return finish;});}
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return active;});}
    for(unsigned i=0;i<20000;++i)T::Event("milestone","vfs.detail.noise");
    V::CheckpointOutcome(2,false);V::FlushCheckpoint();
    {std::lock_guard<std::mutex> lock(mutex);finish=true;cv.notify_all();}
    worker.join();
  }
  else return 5;
  std::cout<<"PASS "<<test<<"\n";
}
