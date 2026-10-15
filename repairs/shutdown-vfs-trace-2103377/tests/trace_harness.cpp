#include "InfinityVfsOpenTrace.h"
#include <condition_variable>
#include <filesystem>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <memory>
#include <stdexcept>
namespace V=InfinityVfsOpenTrace;
namespace T=InfinityShutdownTrace;
int main(int argc,char**argv)
{
  if(argc!=3)return 2;
  std::filesystem::create_directories(argv[2]);T::Configure(argv[2]);
  const std::string which=argv[1];
  int file=0;
  if(which=="preclose" || which=="cancel")
  {
    std::mutex mutex;std::condition_variable condition;bool entered=false,finish=false;
    std::thread worker([&]{
      V::Invoker invoker(5,true);V::Open operation(V::Scheme::Https);
      V::Select(V::Backend::Curl);operation.Bind(&file);V::Mark(V::Stage::CurlPoll);
      {std::unique_lock<std::mutex> lock(mutex);entered=true;condition.notify_all();condition.wait(lock,[&]{return finish;});}
      operation.Returned(false);
    });
    {std::unique_lock<std::mutex> lock(mutex);condition.wait(lock,[&]{return entered;});}
    T::Begin();errno=EDOM;V::Request(5,"monitor_notification_sent");
    if(errno!=EDOM)return 3;
    if(which=="cancel")
    {
      V::BackendCancellation(&file,"callback_entered",true);
      V::BackendCancellation(&file,"existing_flag_set",false);
      V::BackendCancellation(&file,"callback_returned",false);
    }
    {std::unique_lock<std::mutex> lock(mutex);if(finish)return 4;finish=true;condition.notify_all();}
    worker.join();V::Milestone(5,"vfs.python.bytecode_return","observed");
    V::Milestone(5,"vfs.python.interpreter_retired","durability_receipt_taken",true);
  }
  else if(which=="nested")
  {
    T::Begin();V::Invoker invoker(5,true);
    {V::Open parent(V::Scheme::Special);V::Select(V::Backend::Special);
      {V::Open child(V::Scheme::Local);V::Select(V::Backend::Posix);child.Returned(true);}
      V::Request(5,"cooperative_stop_called");parent.Returned(true);}
    V::Milestone(5,"vfs.python.interpreter_retired","no_durability_receipt",true);
  }
  else if(which=="inactive")
  {
    T::Begin();V::Invoker unrelated(17,false);V::Open operation(V::Scheme::Https);
    V::Select(V::Backend::Curl);V::Request(17,"cooperative_stop_called");operation.Returned(true);
  }
  else if(which=="exception")
  {
    T::Begin();V::Invoker invoker(5,true);
    try {V::Open operation(V::Scheme::Local);V::Select(V::Backend::Posix);throw std::runtime_error("PRIVATE_URL_PASSWORD");}
    catch(const std::runtime_error&){}
    V::Milestone(5,"vfs.python.interpreter_retired","no_durability_receipt",true);
  }
  else if(which=="capacity")
  {
    T::Begin();V::Invoker invoker(5,true);
    std::vector<std::unique_ptr<V::Open>> operations;
    for(unsigned i=0;i<=V::CAPACITY;++i)operations.push_back(std::make_unique<V::Open>(V::Scheme::Local));
    if(V::current!=nullptr)return 5;
    while(!operations.empty())operations.pop_back();
    if(V::current!=nullptr)return 6;
  }
  else if(which=="reuse")
  {
    T::Begin();V::Invoker invoker(5,true);
    {V::Open first(V::Scheme::Local);first.Bind(&file);V::BackendCancellation(&file,"callback_entered",true);first.Returned(true);}
    {V::Open next(V::Scheme::Https);next.Bind(&file);V::Request(5,"cooperative_stop_called");next.Returned(false);}
  }
  else if(which=="curl_result")
  {
    T::Begin();V::Invoker invoker(5,true);V::Open operation(V::Scheme::Https);
    V::Select(V::Backend::Curl);V::Mark(V::Stage::CurlPerform);V::TransferResult(28);operation.Returned(false);
  }
  else if(which=="stale_cancel")
  {
    T::Begin();V::Record record;
    record.id.store(100);V::ObserveCancellation(record,100);
    V::ObserveCancellation(record,99);if(V::Read(record).cancelCalls!=1)return 8;
    record.id.store(101);record.cancelForId.store(0);
    V::ObserveCancellation(record,100);if(V::Read(record).cancelCalls!=0)return 9;
    V::ObserveCancellation(record,101);V::ObserveCancellation(record,100);
    if(V::Read(record).cancelCalls!=1 || record.cancelForId.load()!=101)return 10;
  }
  else if(which=="stress")
  {
    T::Begin();std::atomic<bool> done{false};
    std::thread reader([&]{for(unsigned i=0;i<200 && !done.load();++i){V::Request(5,"cooperative_stop_called");std::this_thread::yield();}});
    {V::Invoker invoker(5,true);for(unsigned i=0;i<100;++i){V::Open operation(V::Scheme::Https);V::Select(V::Backend::Curl);operation.Bind(&file);operation.Returned(i%2==0);}}
    done.store(true);reader.join();V::Milestone(5,"vfs.python.interpreter_retired","durability_receipt_taken",true);
  }
  else return 7;
  std::cout<<"PASS "<<which<<"\n";return 0;
}
