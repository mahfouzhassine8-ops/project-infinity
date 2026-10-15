/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// Observation only. No cancellation, authorization, GIL, waits, mutexes or
// resource strings. Fixed-size atomic snapshots survive a pre-Close open.
#include "InfinityShutdownTrace.h"
#include <array>
#include <limits>

namespace InfinityVfsOpenTrace
{
enum class Backend : unsigned char
{
  Unknown, Addon, Apk, Zip, Xbt, MusicDb, VideoDb, Plugin, Special, MultiPath,
  Image, Posix, Windows, TvOs, WinLibrary, Cdda, Iso, Udf, AndroidApp, Pipe,
  Bluray, Resource, Curl, Dav, Shoutcast, Smb, WinSmb, Nfs, Upnp
};
enum class Stage : unsigned char
{
  Enter, Reopen, SubstitutePath, DirectoryCache, CacheOpen, Factory,
  WakeOnAccess, AddonLookup, BackendConstruction, Authentication, BackendOpen,
  Redirect, StreamBufferCheck, StreamBufferAttach, BitrateSetup,
  CurlSetup, CurlConnect, CurlPerform, CurlPoll, Returned
};
enum class Scheme : unsigned char
{
  Other, Local, Special, Http, Https, Ftp, Ftps, Dav, Davs, Smb, Nfs,
  Zip, Apk, Plugin, Resource
};
inline const char* Name(Backend b) noexcept
{
  constexpr const char* names[]={"unselected","addon_vfs","apk","zip","xbt",
    "music_database","video_database","plugin","special","multipath","image",
    "posix_file","windows_file","tvos_file","windows_library","cdda","iso",
    "udf","android_app","pipe","bluray","resource","curl","dav","shoutcast",
    "smb","windows_smb","nfs","upnp"};
  const auto i=static_cast<unsigned>(b);
  return i<sizeof(names)/sizeof(names[0]) ? names[i] : "invalid";
}
inline const char* Name(Stage s) noexcept
{
  constexpr const char* names[]={"enter","reopen","path_substitution","directory_cache",
    "cache_open","factory","wake_on_access","addon_lookup","backend_construction",
    "authentication","backend_open","redirect","stream_buffer_check",
    "stream_buffer_attach","bitrate_setup","curl_setup","curl_connect",
    "curl_multi_perform","curl_multi_poll","returned"};
  const auto i=static_cast<unsigned>(s);
  return i<sizeof(names)/sizeof(names[0]) ? names[i] : "invalid";
}
inline const char* Name(Scheme s) noexcept
{
  constexpr const char* names[]={"other","local","special","http","https","ftp",
    "ftps","dav","davs","smb","nfs","zip","apk","plugin","resource"};
  const auto i=static_cast<unsigned>(s);
  return i<sizeof(names)/sizeof(names[0]) ? names[i] : "invalid";
}
template<class Url> inline Scheme Protocol(const Url& u) noexcept
{
  const auto& protocol=u.GetProtocol();
  if(protocol.empty() || protocol=="file") return Scheme::Local;
  if(protocol=="special") return Scheme::Special;
  if(protocol=="http") return Scheme::Http;
  if(protocol=="https") return Scheme::Https;
  if(protocol=="ftp") return Scheme::Ftp;
  if(protocol=="ftps") return Scheme::Ftps;
  if(protocol=="dav") return Scheme::Dav;
  if(protocol=="davs") return Scheme::Davs;
  if(protocol=="smb") return Scheme::Smb;
  if(protocol=="nfs") return Scheme::Nfs;
  if(protocol=="zip") return Scheme::Zip;
  if(protocol=="apk") return Scheme::Apk;
  if(protocol=="plugin") return Scheme::Plugin;
  if(protocol=="resource") return Scheme::Resource;
  return Scheme::Other;
}
constexpr unsigned CAPACITY=16;
constexpr auto INITIALIZING=std::numeric_limits<unsigned long long>::max();
struct Record
{
  std::atomic<unsigned long long> id{0},parent{0},cancelForId{0};
  std::atomic<long long> invoker{-1},start{0};
  // One word binds backend/stage/protocol; snapshots cannot mix these fields.
  std::atomic<unsigned> state{0};
  std::atomic<std::uintptr_t> file{0};
};
struct Subject
{
  std::atomic<long long> invoker{-1};
  Record last;
};
inline std::array<Record,CAPACITY> operations;
inline std::array<Subject,CAPACITY> subjects;
inline thread_local long long currentInvoker=-1;
inline thread_local Record* current=nullptr;
struct Snapshot
{
  unsigned long long id{},parent{};
  long long invoker{-1},start{};
  unsigned state{},cancelCalls{};
  std::uintptr_t file{};
};
inline unsigned Pack(Backend b,Stage s,Scheme p) noexcept
{ return static_cast<unsigned>(b) | (static_cast<unsigned>(s)<<8) | (static_cast<unsigned>(p)<<16); }
inline Snapshot Read(const Record& r) noexcept
{
  for(unsigned attempt=0;attempt<3;++attempt)
  {
    const auto first=r.id.load(std::memory_order_acquire);
    if(first==0 || first==INITIALIZING) return {};
    Snapshot s{first,r.parent.load(),r.invoker.load(),r.start.load(),r.state.load(),
               r.cancelForId.load()==first?1U:0U,r.file.load()};
    if(first==r.id.load(std::memory_order_acquire)) return s;
  }
  return {};
}
inline Subject* FindSubject(long long id) noexcept
{
  if(id<0) return nullptr;
  for(auto& s:subjects) if(s.invoker.load(std::memory_order_acquire)==id) return &s;
  return nullptr;
}
inline void Remember(const Snapshot& s) noexcept
{
  auto* subject=FindSubject(s.invoker);
  if(!subject || !s.id) return;
  auto& r=subject->last;
  r.id.store(INITIALIZING,std::memory_order_release);
  r.parent.store(s.parent);r.invoker.store(s.invoker);r.start.store(s.start);
  r.state.store(s.state);r.cancelForId.store(s.cancelCalls?s.id:0);r.file.store(0);
  r.id.store(s.id,std::memory_order_release);
}
inline void Emit(const Snapshot& s,const char* phase,const char* outcome) noexcept
{
  if(!s.id) return;
  InfinityShutdownTrace::PreserveErrno keep;
  const auto backend=static_cast<Backend>(s.state&255);
  const auto stage=static_cast<Stage>((s.state>>8)&255);
  const auto scheme=static_cast<Scheme>((s.state>>16)&255);
  InfinityShutdownTrace::OperationMetadata metadata{
    s.id,s.parent,s.start,Name(backend),Name(stage),Name(scheme),s.cancelCalls};
  InfinityShutdownTrace::Event("milestone",phase,s.invoker,s.id,s.parent,
    InfinityShutdownTrace::Clock(CLOCK_MONOTONIC)-s.start,
    "plugin.video.playlistbrowser",outcome,nullptr,&metadata);
}
class Invoker
{
public:
  Invoker(long long id,bool selected) noexcept : previous(currentInvoker),previousOperation(current)
  {
    InfinityShutdownTrace::PreserveErrno keep;
    current=nullptr;
    currentInvoker=selected?id:-1;
    if(!selected) return;
    for(auto& s:subjects)
    {
      long long empty=-1;
      if(s.invoker.compare_exchange_strong(empty,id)) { return; }
      if(empty==id) { return; }
    }
    currentInvoker=-1;
    InfinityShutdownTrace::Event("milestone","vfs.capture_limit",id,0,0,0,
      "plugin.video.playlistbrowser","subject_capacity_exhausted");
  }
  ~Invoker() noexcept { currentInvoker=previous;current=previousOperation; }
  Invoker(const Invoker&)=delete;
  Invoker& operator=(const Invoker&)=delete;
private:
  long long previous;
  Record* previousOperation{};
};
class Open
{
public:
  explicit Open(Scheme scheme) noexcept : previous(current),exceptions(std::uncaught_exceptions())
  {
    InfinityShutdownTrace::PreserveErrno keep;
    if(currentInvoker<0) return;
    restoreContext=true;
    for(auto& entry:operations)
    {
      unsigned long long empty=0;
      if(!entry.id.compare_exchange_strong(empty,INITIALIZING)) continue;
      record=&entry;
      const auto id=InfinityShutdownTrace::ids.fetch_add(1)+1;
      entry.parent.store(previous?Read(*previous).id:0);
      entry.invoker.store(currentInvoker);entry.start.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
      entry.state.store(Pack(Backend::Unknown,Stage::Enter,scheme));
      entry.cancelForId.store(0);entry.file.store(0);entry.id.store(id,std::memory_order_release);
      current=record;Emit(Read(entry),"vfs.open.start","observed");return;
    }
    current=nullptr;
    InfinityShutdownTrace::Event("milestone","vfs.capture_limit",currentInvoker,0,0,0,
      "plugin.video.playlistbrowser","operation_capacity_exhausted");
  }
  void Returned(bool value) noexcept { returned=true;result=value; }
  ~Open() noexcept
  {
    InfinityShutdownTrace::PreserveErrno keep;
    if(!record) {if(restoreContext)current=previous;return;}
    auto s=Read(*record);
    Emit(s,"vfs.open.return",returned?(result?"true":"false"):
      (std::uncaught_exceptions()>exceptions?"exception_unwound":"unclassified"));
    Remember(s);record->id.store(0,std::memory_order_release);current=previous;
  }
  Open(const Open&)=delete;
  Open& operator=(const Open&)=delete;
  void Bind(const void* file) noexcept
  { if(record)record->file.store(reinterpret_cast<std::uintptr_t>(file)); }
private:
  Record* previous{};Record* record{};
  int exceptions{};bool returned{false},result{false},restoreContext{false};
};
inline void Mark(Stage stage) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(!current) return;
  const auto old=current->state.load();
  current->state.store((old&~0xff00U)|(static_cast<unsigned>(stage)<<8));
  // Poll iterations update atomics only. Stop requests sample the current
  // stage; do not flood I/O while an existing backend is waiting.
}
inline void Select(Backend backend) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(!current) return;
  const auto old=current->state.load();
  current->state.store((old&~0xffffU)|Pack(backend,Stage::BackendConstruction,Scheme::Other));
  Emit(Read(*current),"vfs.backend.selected","observed");
}
inline void TransferResult(int code) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(!current) return;
  char outcome[32]{};
  const auto ignored=std::snprintf(outcome,sizeof(outcome),"curl_result_code_%d",code);
  (void)ignored;Emit(Read(*current),"vfs.backend.transfer_result",outcome);
}
inline void Request(long long id,const char* outcome) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  auto* subject=FindSubject(id);
  if(!subject) return;
  bool active=false;
  for(auto& r:operations)
  {
    const auto s=Read(r);
    if(s.id && s.invoker==id) {active=true;Emit(s,"vfs.shutdown.request",outcome);}
  }
  if(!active)
  {
    const auto last=Read(subject->last);
    if(last.invoker==id) Emit(last,"vfs.shutdown.request","no_active_open_observed");
  }
}
inline void ObserveCancellation(Record& r,unsigned long long id) noexcept
{
  // IDs only increase. A delayed callback from an older lease cannot overwrite
  // cancellation evidence already observed for a newer operation.
  auto prior=r.cancelForId.load();
  for(unsigned attempt=0;attempt<3 && prior<id;++attempt)
    if(r.cancelForId.compare_exchange_weak(prior,id)) return;
}
inline void BackendCancellation(const void* file,const char* outcome,bool entered=false) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(!file) return;
  for(auto& r:operations)
  {
    auto s=Read(r);
    if(s.id && s.file==reinterpret_cast<std::uintptr_t>(file))
    {
      const auto observedId=s.id;
      if(entered)ObserveCancellation(r,observedId);
      s=Read(r);
      if(s.id==observedId && s.file==reinterpret_cast<std::uintptr_t>(file))
        Emit(s,"vfs.backend.cancellation",outcome);
    }
  }
}
inline void Milestone(long long id,const char* phase,const char* outcome,bool release=false) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(auto* s=FindSubject(id))
  {
    const auto last=Read(s->last);
    if(last.invoker==id) Emit(last,phase,outcome);
    if(release)
    {
      long long expected=id;
      if(s->invoker.compare_exchange_strong(expected,-2))
      {s->last.id.store(0);s->invoker.store(-1,std::memory_order_release);}
    }
  }
}
static_assert(std::atomic<unsigned long long>::is_always_lock_free &&
              std::atomic<long long>::is_always_lock_free &&
              std::atomic<std::uintptr_t>::is_always_lock_free,
              "VFS trace requires lock-free atomic snapshots on this ABI");
}
