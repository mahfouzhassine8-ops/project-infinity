#pragma once
// Test-candidate observations only. No lock, save, cancellation or exit authority.
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <fcntl.h>
#include <string>
#include <sys/syscall.h>
#include <unistd.h>

namespace InfinityStabilityProbe
{
inline int64_t Now() { return std::chrono::duration_cast<std::chrono::milliseconds>(
    std::chrono::steady_clock::now().time_since_epoch()).count(); }
inline long Tid() { static thread_local long tid=::syscall(SYS_gettid);return tid; }
struct Lock
{
  std::atomic<uintptr_t> address{0}, site{0};
  std::atomic<long> owner{0};
  std::atomic<unsigned> depth{0}, sequence{0};
  std::atomic<int64_t> since{0};
  std::atomic<const char*> operation{nullptr};
};
struct Thread
{
  std::atomic<long> tid{0};
  std::atomic<int> waiting{-1}, invoker{-1};
  std::atomic<int64_t> waitSince{0}, pythonSince{0};
  std::atomic<unsigned> pythonSequence{0};
  std::array<std::atomic<char>,80> operation{};
  std::array<std::atomic<char>,192> location{};
};
inline std::array<Lock,65> locks;
inline std::array<Thread,128> threads;
inline std::atomic<uintptr_t> graphics{0}, imageBase{0};
inline std::atomic<long> guiThread{0};
inline std::atomic<int64_t> until{0}, closeAt{0}, lastSample{0};
inline std::atomic<unsigned> samples{0}, written{0}, overflow{0};
inline std::atomic<bool> configured{false};
inline std::atomic<bool> manualSnapshot{false};
struct RenderEvent {std::atomic<int> control{0};std::atomic<int64_t> at{0};std::atomic<unsigned> items{0};};
inline std::array<RenderEvent,32> renderHistory;
inline std::atomic<unsigned> renderSerial{0};
inline void Rendered(int control,unsigned items)
{
  int index=-1;const int ids[]={8720,8820,9200,19601,8830,8831};
  for(int i=0;i<6;++i)if(ids[i]==control)index=i;
  if(index<0)return;
  static std::array<int64_t,6> previous{};static std::array<unsigned,6> counts{};
  const auto now=Now();
  if(now-previous[index]>200 || counts[index]!=items) {
    auto& e=renderHistory[renderSerial.fetch_add(1)%renderHistory.size()];
    e.at.store(0);e.control.store(control);e.items.store(items);e.at.store(now);
  }
  previous[index]=now;counts[index]=items;
}
inline std::array<char,1024> output{};
inline thread_local int directorySlot=-1;
inline thread_local const char* directoryOperation=nullptr;

inline Thread* Current()
{
  struct Registration {Thread* pointer{nullptr};~Registration(){if(pointer){pointer->waiting.store(-1);pointer->operation[0].store(0);pointer->tid.store(0);}}};
  static thread_local Registration cached;
  if(cached.pointer)return cached.pointer;
  const long tid=Tid();
  for(auto& t:threads) {
    long empty=0;
    if(t.tid.load()==tid || t.tid.compare_exchange_strong(empty,tid))return cached.pointer=&t;
  }
  ++overflow;return nullptr;
}
inline void RegisterGraphics(const void* pointer)
{
  graphics.store(reinterpret_cast<uintptr_t>(pointer));
  locks[0].address.store(reinterpret_cast<uintptr_t>(pointer));
  guiThread.store(Tid());
}
inline int Slot(const void* pointer)
{
  const auto p=reinterpret_cast<uintptr_t>(pointer);
  if(graphics.load(std::memory_order_relaxed)==p && p)return 0;
  return directorySlot>=1 && locks[directorySlot].address.load()==p ? directorySlot : -1;
}
class DirectoryScope
{
  int previous;const char* previousOperation;
public:
  DirectoryScope(const void* pointer,const char* operation):previous(directorySlot),previousOperation(directoryOperation)
  {
    directorySlot=-1;directoryOperation=operation;
    const auto p=reinterpret_cast<uintptr_t>(pointer);
    for(unsigned i=1;i<locks.size();++i) {
      uintptr_t empty=0;
      if(locks[i].address.load()==p || locks[i].address.compare_exchange_strong(empty,p)) {
        directorySlot=i;return;
      }
    }
    ++overflow;
  }
  ~DirectoryScope() { directorySlot=previous;directoryOperation=previousOperation; }
};
inline void Waiting(const void* pointer)
{
  const int slot=Slot(pointer);if(slot<0)return;
  if(auto* t=Current()) {t->waitSince.store(Now());t->waiting.store(slot);}
}
inline void Acquired(const void* pointer,unsigned depth,uintptr_t site)
{
  const int slot=Slot(pointer);if(slot<0)return;
  auto& r=locks[slot];r.sequence.fetch_add(1);
  if(depth==1 || r.owner.load()!=Tid()) {
    r.since.store(Now());r.site.store(site);r.operation.store(directoryOperation);
  }
  r.depth.store(depth);r.owner.store(Tid());r.sequence.fetch_add(1);
  if(auto* t=Current())t->waiting.store(-1);
}
inline void Released(const void* pointer,unsigned remaining)
{
  const int slot=Slot(pointer);if(slot<0)return;
  auto& r=locks[slot];r.sequence.fetch_add(1);r.depth.store(remaining);
  if(!remaining){r.owner.store(0);r.operation.store(nullptr);}
  r.sequence.fetch_add(1);
}
inline void Arm(int seconds=300) { closeAt.store(0);until.store(Now()+seconds*1000);samples.store(0);lastSample.store(0); }
inline void CloseRequested() { Arm(35);closeAt.store(Now()); }
inline void Configure(const std::string& path,uintptr_t base=0)
{
  bool expected=false;if(!configured.compare_exchange_strong(expected,true))return;
  if(path.empty() || path.size()>=output.size())return;
  // Only this test probe's own previous log is rotated; no profile/settings file.
  ::rename(path.c_str(),(path+".previous").c_str());
  std::snprintf(output.data(),output.size(),"%s",path.c_str());imageBase.store(base);
}
template<size_t N> inline void Store(std::array<std::atomic<char>,N>& dst,const char* text)
{
  size_t i=0;for(;i+1<N && text && text[i];++i)dst[i].store(text[i]);dst[i].store(0);
}
template<size_t N> inline std::string Load(const std::array<std::atomic<char>,N>& src)
{
  std::string out;for(size_t i=0;i<N;++i){char c=src[i].load();if(!c)break;out+=c;}return out;
}
inline std::string Quote(const std::string& s)
{
  std::string r="\"";for(unsigned char c:s) {
    if(c=='"' || c=='\\'){r+='\\';r+=c;}else if(c>=32)r+=c;
  }return r+'"';
}
inline void Python(int invoker,const char* operation,const char* location,int64_t started)
{
  if(auto* t=Current()) {
    t->pythonSequence.fetch_add(1);t->invoker.store(invoker);
    Store(t->operation,operation);Store(t->location,location);t->pythonSince.store(started);
    t->pythonSequence.fetch_add(1);
  }
}
inline void Snapshot(const char* reason)
{
  if(!configured.load() || !output[0] || samples.fetch_add(1)>=8)return;
  const auto now=Now();
  std::string row="{\"schema\":1,\"kind\":\"stability_probe\",\"reason\":"+Quote(reason)+
      ",\"pid\":"+std::to_string(::getpid())+",\"monotonic_ms\":"+std::to_string(now)+
      ",\"gui_tid\":"+std::to_string(guiThread.load())+",\"overflow\":"+std::to_string(overflow.load())+",\"locks\":[";
  bool comma=false;
  for(size_t i=0;i<locks.size();++i) {
    auto& r=locks[i];const auto seq=r.sequence.load();if(seq&1)continue;
    const auto tid=r.owner.load();if(!tid)continue;
    const auto since=r.since.load();const auto site=r.site.load();const auto op=r.operation.load();const auto depth=r.depth.load();
    if(r.sequence.load()!=seq)continue;
    if(comma)row+=',';comma=true;
    row+="{\"slot\":"+std::to_string(i)+",\"domain\":"+Quote(i==0?"graphics":"directory")+
      ",\"owner_tid\":"+std::to_string(tid)+",\"held_ms\":"+std::to_string(now-since)+
      ",\"depth\":"+std::to_string(depth)+",\"elf_pc\":"+std::to_string(site>=imageBase.load()?site-imageBase.load():0)+
      ",\"operation\":"+Quote(op?op:"")+"}";
  }
  row+="],\"threads\":[";comma=false;
  for(auto& t:threads) {
    const auto tid=t.tid.load();if(!tid)continue;
    const auto waiting=t.waiting.load();const auto seq=t.pythonSequence.load();
    if(seq&1)continue;
    const auto op=Load(t.operation),location=Load(t.location);const auto pySince=t.pythonSince.load();const auto id=t.invoker.load();
    if(t.pythonSequence.load()!=seq || t.tid.load()!=tid || (waiting<0 && op.empty()))continue;
    if(comma)row+=',';comma=true;
    row+="{\"tid\":"+std::to_string(tid)+",\"waiting_slot\":"+std::to_string(waiting)+
      ",\"wait_ms\":"+std::to_string(waiting>=0?now-t.waitSince.load():0)+",\"invoker\":"+std::to_string(id)+
      ",\"python_operation\":"+Quote(op)+",\"python_location\":"+Quote(location)+
      ",\"operation_age_ms\":"+std::to_string(op.empty()?0:now-pySince)+"}";
  }
  row+="],\"render_history\":[";comma=false;
  for(auto& e:renderHistory) {
    const auto at=e.at.load();if(!at)continue;
    const auto control=e.control.load();const auto items=e.items.load();if(e.at.load()!=at)continue;
    if(comma)row+=',';comma=true;
    row+="{\"control\":"+std::to_string(control)+",\"monotonic_ms\":"+std::to_string(at)+",\"items\":"+std::to_string(items)+"}";
  }
  row+="]}\n";
  const auto before=written.fetch_add(row.size());if(before+row.size()>512*1024)return;
  const int fd=::open(output.data(),O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC,0600);
  if(fd>=0){const auto ignored=::write(fd,row.data(),row.size());(void)ignored;::close(fd);}
}
inline void Observe(int64_t heartbeat)
{
  if(manualSnapshot.exchange(false)){Snapshot("manual_export");return;}
  const auto now=Now();if(now>until.load())return;
  const auto close=closeAt.load();const bool shutting=close && now-close>=2500;
  const bool stalled=heartbeat && now-heartbeat>=3000;
  if(!shutting && !stalled)return;
  auto previous=lastSample.load();
  if(now-previous<3000 || !lastSample.compare_exchange_strong(previous,now))return;
  Snapshot(shutting?"close_pending":"gui_heartbeat_stall");
}
} // namespace InfinityStabilityProbe
