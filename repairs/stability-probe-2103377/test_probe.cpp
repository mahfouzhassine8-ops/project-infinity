#include "threads/Lockables.h"
#include <cassert>
#include <condition_variable>
#include <fstream>
#include <mutex>
#include <thread>
#include <iostream>

using Mutex=XbmcThreads::CountingLockable<std::recursive_mutex>;
int main(int argc,char** argv)
{
  assert(argc==2);
  Mutex graphics,directory,ordinary;
  InfinityStabilityProbe::Configure(argv[1]);
  InfinityStabilityProbe::RegisterGraphics(&graphics);
  graphics.lock();graphics.lock();
  assert(InfinityStabilityProbe::locks[0].owner.load()==InfinityStabilityProbe::Tid());
  assert(InfinityStabilityProbe::locks[0].depth.load()==2);
  const auto depth=graphics.exit();assert(depth==2);
  assert(InfinityStabilityProbe::locks[0].owner.load()==0);
  graphics.restore(depth);assert(InfinityStabilityProbe::locks[0].depth.load()==2);
  graphics.unlock();graphics.unlock();
  long owner=0;std::atomic<long> waiter{0};bool acquired=false,release=false;std::mutex gate;std::condition_variable cv;
  std::thread a([&]{InfinityStabilityProbe::DirectoryScope scope(&directory,"owner_operation");directory.lock();
    {std::lock_guard<std::mutex> l(gate);owner=InfinityStabilityProbe::Tid();acquired=true;}cv.notify_all();
    {std::unique_lock<std::mutex> l(gate);cv.wait(l,[&]{return release;});}directory.unlock();});
  {std::unique_lock<std::mutex> l(gate);cv.wait(l,[&]{return acquired;});}
  std::thread b([&]{InfinityStabilityProbe::DirectoryScope scope(&directory,"waiting_operation");waiter=InfinityStabilityProbe::Tid();directory.lock();directory.unlock();});
  bool observed=false;
  for(int i=0;i<1000000 && !observed;++i){
    for(auto& t:InfinityStabilityProbe::threads)if(t.tid.load()==waiter && t.waiting.load()>=1)observed=true;
    if(!observed)std::this_thread::yield();
  }
  assert(observed);
  int slot=-1;for(int i=1;i<65;++i)if(InfinityStabilityProbe::locks[i].owner.load()==owner)slot=i;
  assert(slot>0);assert(InfinityStabilityProbe::locks[slot].operation.load()==std::string("owner_operation"));
  {InfinityStabilityProbe::DirectoryScope scope(&directory,"try");assert(!directory.try_lock());}
  assert(InfinityStabilityProbe::locks[slot].owner.load()==owner);
  InfinityStabilityProbe::Snapshot("controlled_contention");
  {std::lock_guard<std::mutex> l(gate);release=true;}cv.notify_all();a.join();b.join();
  assert(InfinityStabilityProbe::locks[slot].owner.load()==0);
  ordinary.lock();assert(InfinityStabilityProbe::Slot(&ordinary)<0);ordinary.unlock();
  InfinityStabilityProbe::Rendered(8830,0);InfinityStabilityProbe::Rendered(8830,4);
  InfinityStabilityProbe::Snapshot("resolved");
  std::ifstream log(argv[1]);std::string text((std::istreambuf_iterator<char>(log)),{});
  assert(text.find("owner_operation")!=std::string::npos);
  assert(text.find("controlled_contention")!=std::string::npos);
  assert(text.find("render_history")!=std::string::npos);
  std::cout<<"real mutex owner/waiter, recursion, exit/restore, failed try-lock, untracked mutex and render-state checks passed\n";
}
