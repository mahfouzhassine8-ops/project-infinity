/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// Observation only: no backend cancellation calls, authority, GIL, mutexes,
// waits or resource strings. Native language-hook addresses stay in memory.
#include "InfinityShutdownTrace.h"
#include <array>
#include <limits>
namespace XFILE { class IFile; }
namespace InfinityVfsOpenTrace
{
enum class Backend : unsigned char
{
  Unknown, Addon, Apk, Zip, Xbt, MusicDb, VideoDb, Plugin, Special, MultiPath,
  Image, Posix, Windows, TvOs, WinLibrary, Cdda, Iso, Udf, AndroidApp, Pipe,
  Bluray, Resource, Curl, Dav, Shoutcast, Smb, WinSmb, Nfs, Upnp, FileCache
};
enum class Stage : unsigned char
{
  Enter, Reopen, SubstitutePath, DirectoryCache, CacheOpen, Factory,
  WakeOnAccess, AddonLookup, BackendConstruction, Authentication, BackendOpen,
  Redirect, StreamBufferCheck, StreamBufferAttach, BitrateSetup,
  CurlSetup, CurlConnect, CurlPerform, CurlPoll, Returned, BackendCall,
  CacheWorker, CacheWait, CurlCancelCheck
};
enum class Scheme : unsigned char
{ Other, Local, Special, Http, Https, Ftp, Ftps, Dav, Davs, Smb, Nfs, Zip, Apk, Plugin, Resource };
enum class Kind : unsigned char
{ Open, OpenForWrite, Exists, Stat, Read, Write, Close, Flush, Seek, Truncate, GetLength, GetPosition,
  ReadString, Delete, Rename, SetHidden, IoControl, GetChunkSize, CacheProcess };
inline const char* Name(Backend b) noexcept
{
  constexpr const char* names[]={"unselected_or_unknown","addon_vfs","apk","zip","xbt",
    "music_database","video_database","plugin","special","multipath","image",
    "posix_file","windows_file","tvos_file","windows_library","cdda","iso",
    "udf","android_app","pipe","bluray","resource","curl","dav","shoutcast",
    "smb","windows_smb","nfs","upnp","file_cache"};
  const auto i=static_cast<unsigned>(b);
  return i<sizeof(names)/sizeof(names[0])?names[i]:"invalid";
}
inline const char* Name(Stage s) noexcept
{
  constexpr const char* names[]={"enter","reopen","path_substitution","directory_cache",
    "cache_open","factory","wake_on_access","addon_lookup","backend_construction",
    "authentication","backend_open","redirect","stream_buffer_check",
    "stream_buffer_attach","bitrate_setup","curl_setup","curl_connect",
    "curl_multi_perform","curl_multi_poll","returned","backend_call",
    "cache_worker","cache_wait","curl_cancel_check"};
  const auto i=static_cast<unsigned>(s);
  return i<sizeof(names)/sizeof(names[0])?names[i]:"invalid";
}
inline const char* Name(Scheme s) noexcept
{
  constexpr const char* names[]={"other","local","special","http","https","ftp",
    "ftps","dav","davs","smb","nfs","zip","apk","plugin","resource"};
  const auto i=static_cast<unsigned>(s);
  return i<sizeof(names)/sizeof(names[0])?names[i]:"invalid";
}
inline const char* Name(Kind k) noexcept
{
  constexpr const char* names[]={"CFile.Open","CFile.OpenForWrite","CFile.Exists","CFile.Stat",
    "CFile.Read","CFile.Write","CFile.Close","CFile.Flush","CFile.Seek","CFile.Truncate",
    "CFile.GetLength","CFile.GetPosition","CFile.ReadString","CFile.Delete","CFile.Rename",
    "CFile.SetHidden","CFile.IoControl","CFile.GetChunkSize","CFileCache.Process"};
  const auto i=static_cast<unsigned>(k);
  return i<sizeof(names)/sizeof(names[0])?names[i]:"invalid";
}
inline const char* Support(Backend b, bool verified) noexcept
{
  if(!verified || b==Backend::Unknown) return "unobservable";
  if(b==Backend::Curl || b==Backend::Dav || b==Backend::Shoutcast) return "existing_Curl_Cancel";
  if(b==Backend::FileCache) return "worker_StopThread_only";
  if(b==Backend::Addon) return "no_public_cancel_private_unknown";
  return "no_generic_IFile_cancel_API";
}
template<class Url> inline Scheme Protocol(const Url& u) noexcept
{
  const auto& p=u.GetProtocol();
  if(p.empty() || p=="file") return Scheme::Local;
  if(p=="special") return Scheme::Special;
  if(p=="http") return Scheme::Http;
  if(p=="https") return Scheme::Https;
  if(p=="ftp") return Scheme::Ftp;
  if(p=="ftps") return Scheme::Ftps;
  if(p=="dav") return Scheme::Dav;
  if(p=="davs") return Scheme::Davs;
  if(p=="smb") return Scheme::Smb;
  if(p=="nfs") return Scheme::Nfs;
  if(p=="zip") return Scheme::Zip;
  if(p=="apk") return Scheme::Apk;
  if(p=="plugin") return Scheme::Plugin;
  if(p=="resource") return Scheme::Resource;
  return Scheme::Other;
}
// Implemented beside the factory with the same platform feature guards.
Backend Identify(const XFILE::IFile*) noexcept;
constexpr unsigned CAPACITY=128;
constexpr auto INITIALIZING=std::numeric_limits<unsigned long long>::max();
struct Record
{
  std::atomic<unsigned long long> id{0},parent{0},cancelForId{0},cancelData{0},generation{0};
  std::atomic<long long> invoker{-1},start{0},stageStart{0},end{0},tid{0};
  std::atomic<unsigned> state{0},kind{0},verified{0},stageRevision{0};
  std::atomic<std::uintptr_t> file{0};
};
struct Subject
{
  std::atomic<long long> invoker{-1};
  std::atomic<unsigned long long> executionId{0};
  std::atomic<long long> started{0},tid{0};
  std::atomic<unsigned> phase{0};
  std::atomic<std::uintptr_t> hook{0};
  std::array<std::atomic<char>,96> addon{};
  Record last;
};
struct FileOwner
{
  std::atomic<std::uintptr_t> file{0};
  std::atomic<long long> invoker{-1};
  std::atomic<unsigned long long> parent{0};
};
inline std::array<Record,CAPACITY> operations;
inline std::array<Subject,CAPACITY> subjects;
inline std::array<FileOwner,CAPACITY> fileOwners;
inline std::atomic<unsigned long long> checkpointGeneration{0},checkpointResult{0},pendingCheckpointResult{0};
inline std::atomic<long long> checkpointObservedNs{0};
inline thread_local long long currentInvoker=-1;
inline thread_local unsigned long long inheritedParent=0;
inline thread_local Record* current=nullptr;
inline thread_local bool captureEnabled=true;
struct Snapshot
{
  unsigned long long id{},parent{},generation{};
  long long invoker{-1},start{},stageStart{},end{},tid{};
  unsigned state{},cancelCalls{},cancelBits{},kind{},verified{};
  std::uintptr_t file{};
};
inline unsigned Pack(Backend b,Stage s,Scheme p) noexcept
{return static_cast<unsigned>(b)|(static_cast<unsigned>(s)<<8)|(static_cast<unsigned>(p)<<16);}
inline Snapshot Read(const Record& r) noexcept
{
  for(unsigned attempt=0;attempt<3;++attempt)
  {
    const auto first=r.id.load(std::memory_order_acquire);
    if(first==0)return {};
    if(first==INITIALIZING)continue;
    const auto revision=r.stageRevision.load(std::memory_order_acquire);
    if(revision&1)continue;
    Snapshot s;
    s.id=first;s.parent=r.parent.load();s.generation=r.generation.load();
    s.invoker=r.invoker.load();s.start=r.start.load();s.stageStart=r.stageStart.load();
    s.end=r.end.load();s.tid=r.tid.load();s.state=r.state.load();s.kind=r.kind.load();
    s.file=r.file.load();s.verified=r.verified.load();
    const auto cancellation=r.cancelData.load();
    s.cancelBits=(cancellation>>8)==first?static_cast<unsigned>(cancellation&255):0;
    s.cancelCalls=r.cancelForId.load()==first?1U:0U;
    if(first==r.id.load(std::memory_order_acquire) &&
       revision==r.stageRevision.load(std::memory_order_acquire)) return s;
  }
  InfinityShutdownTrace::Event("milestone","vfs.snapshot_gap",-1,0,0,0,
    nullptr,"bounded_concurrent_snapshot_unavailable");
  return {};
}
inline Subject* FindSubject(long long id) noexcept
{
  if(id<0)return nullptr;
  for(auto& s:subjects)if(s.invoker.load(std::memory_order_acquire)==id)return &s;
  return nullptr;
}
inline void Addon(long long id,char* result,std::size_t size) noexcept
{
  if(auto* s=FindSubject(id))
  {
    for(std::size_t i=0;i+1<size && i<s->addon.size();++i)
    {result[i]=s->addon[i].load();if(!result[i])return;}
  }
  result[size-1]=0;
}
inline void Emit(const Snapshot& s,const char* phase,const char* outcome) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(InfinityShutdownTrace::descriptor.load(std::memory_order_acquire)<0)return;
  char addon[96]{};Addon(s.invoker,addon,sizeof(addon));
  const auto b=static_cast<Backend>(s.state&255);
  const auto* subject=FindSubject(s.invoker);
  InfinityShutdownTrace::OperationMetadata m{
    s.id,s.parent,s.generation,s.start,s.stageStart,s.end,s.tid,
    s.id?Name(b):"not_a_VFS_operation",s.id?Name(static_cast<Stage>((s.state>>8)&255)):"no_active_vfs_operation",
    Name(static_cast<Scheme>((s.state>>16)&255)),s.id?Name(static_cast<Kind>(s.kind)):"not_a_VFS_operation",
    s.id?Support(b,s.verified!=0):"not_applicable",s.cancelCalls,s.cancelBits,s.verified,
    subject?subject->executionId.load():0,subject?subject->started.load():0,
    subject?subject->tid.load():0,subject?"python_invoker":"native_or_unmapped"};
  m.checkpointObservedMonotonicNs=checkpointObservedNs.load();
  InfinityShutdownTrace::Event("milestone",phase,s.invoker,s.id,s.parent,
    s.start?InfinityShutdownTrace::Clock(CLOCK_MONOTONIC)-s.start:0,
    addon[0]?addon:nullptr,outcome,nullptr,&m);
}
inline void SubjectEvent(long long id,const char* phase,const char* outcome) noexcept
{
  if(auto* s=FindSubject(id))
  {
    auto last=Read(s->last);
    if(last.invoker==id){Emit(last,phase,outcome);return;}
  }
  Snapshot blank;blank.invoker=id;blank.generation=checkpointGeneration.load();
  Emit(blank,phase,outcome);
}
inline void Remember(const Snapshot& s) noexcept
{
  auto* subject=FindSubject(s.invoker);
  if(!subject || !s.id)return;
  auto& r=subject->last;
  auto old=r.id.load();
  // Concurrent child calls never race on a non-atomic history object.
  if(old==INITIALIZING || !r.id.compare_exchange_strong(old,INITIALIZING))
  {SubjectEvent(s.invoker,"vfs.history_gap","concurrent_last_return_not_retained");return;}
  r.parent.store(s.parent);r.generation.store(s.generation);r.invoker.store(s.invoker);
  r.start.store(s.start);r.stageStart.store(s.stageStart);r.end.store(s.end);r.tid.store(s.tid);
  r.state.store(s.state);r.kind.store(s.kind);r.verified.store(s.verified);r.file.store(0);
  r.cancelForId.store(s.cancelCalls?s.id:0);r.cancelData.store((s.id<<8)|s.cancelBits);
  r.id.store(s.id,std::memory_order_release);
}
class Invoker
{
public:
  Invoker(long long id,bool selected,const char* addon="plugin.video.playlistbrowser") noexcept
    :previous(currentInvoker),previousOperation(current),previousCapture(captureEnabled)
  {
    InfinityShutdownTrace::PreserveErrno keep;
    current=nullptr;currentInvoker=selected?id:-1;captureEnabled=selected;
    if(!selected)return;
    for(auto& s:subjects)
    {
      if(s.invoker.load()==id)
      {s.executionId.store(InfinityShutdownTrace::ids.fetch_add(1)+1);
        s.started.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
        s.tid.store(static_cast<long long>(::syscall(SYS_gettid)));s.phase.store(1);return;}
      long long empty=-1;
      if(!s.invoker.compare_exchange_strong(empty,-2))continue;
      char safe[96]{};InfinityShutdownTrace::Token(addon,safe,sizeof(safe));
      for(unsigned i=0;i<s.addon.size();++i)s.addon[i].store(safe[i]);
      s.executionId.store(InfinityShutdownTrace::ids.fetch_add(1)+1);
      s.started.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
      s.tid.store(static_cast<long long>(::syscall(SYS_gettid)));s.phase.store(1);
      s.hook.store(0);s.last.id.store(0);s.invoker.store(id,std::memory_order_release);return;
    }
    currentInvoker=-1;SubjectEvent(id,"vfs.capture_limit","subject_capacity_exhausted");
  }
  ~Invoker() noexcept{currentInvoker=previous;current=previousOperation;captureEnabled=previousCapture;}
  Invoker(const Invoker&)=delete;
  Invoker& operator=(const Invoker&)=delete;
private:long long previous;Record* previousOperation{};bool previousCapture;
};
inline void AttachLanguageHook(long long id,const void* hook) noexcept
{if(auto* s=FindSubject(id))s->hook.store(reinterpret_cast<std::uintptr_t>(hook));}
class ThreadContext
{
public:
  explicit ThreadContext(const void* hook) noexcept:previous(currentInvoker)
  {
    if(!hook)return;
    for(auto& s:subjects)
      if(s.hook.load()==reinterpret_cast<std::uintptr_t>(hook) && s.invoker.load()>=0)
      {currentInvoker=s.invoker.load();return;}
  }
  ~ThreadContext() noexcept{currentInvoker=previous;}
private:long long previous;
};
inline void RegisterFile(const void* file) noexcept
{
  if(!file || !captureEnabled)return;
  const auto pointer=reinterpret_cast<std::uintptr_t>(file);
  for(auto& owner:fileOwners)
  {
    auto expected=std::uintptr_t{0};
    if(owner.file.load()==pointer)return;
    if(!owner.file.compare_exchange_strong(expected,1))continue;
    owner.invoker.store(currentInvoker);owner.parent.store(current?Read(*current).id:0);
    owner.file.store(pointer,std::memory_order_release);return;
  }
  SubjectEvent(currentInvoker,"vfs.capture_limit","file_owner_capacity_exhausted");
}
inline void ForgetFile(const void* file) noexcept
{
  const auto pointer=reinterpret_cast<std::uintptr_t>(file);
  for(auto& owner:fileOwners)
    if(owner.file.load()==pointer){owner.file.store(1);owner.invoker.store(-1);
      owner.parent.store(0);owner.file.store(0,std::memory_order_release);}
}
class FileContext
{
public:
  explicit FileContext(const void* file) noexcept:previous(currentInvoker),parent(inheritedParent)
  {
    const auto pointer=reinterpret_cast<std::uintptr_t>(file);
    for(auto& owner:fileOwners)if(pointer && owner.file.load()==pointer)
    {currentInvoker=owner.invoker.load();inheritedParent=owner.parent.load();return;}
  }
  ~FileContext() noexcept{currentInvoker=previous;inheritedParent=parent;}
private:long long previous;unsigned long long parent;
};
class Open
{
public:
  explicit Open(Scheme scheme,Kind kind=Kind::Open) noexcept
    :previous(current),exceptions(std::uncaught_exceptions())
  {
    InfinityShutdownTrace::PreserveErrno keep;
    if(!captureEnabled)return;
    restoreContext=true;
    for(auto& entry:operations)
    {
      unsigned long long empty=0;
      if(!entry.id.compare_exchange_strong(empty,INITIALIZING))continue;
      record=&entry;const auto id=InfinityShutdownTrace::ids.fetch_add(1)+1;
      entry.parent.store(previous?Read(*previous).id:
        inheritedParent?inheritedParent:InfinityShutdownTrace::parentId);
      entry.invoker.store(currentInvoker);
      const auto now=InfinityShutdownTrace::Clock(CLOCK_MONOTONIC);
      entry.start.store(now);entry.stageStart.store(now);entry.end.store(0);
      entry.tid.store(static_cast<long long>(::syscall(SYS_gettid)));entry.generation.store(checkpointGeneration.load());
      entry.state.store(Pack(Backend::Unknown,Stage::Enter,scheme));
      entry.kind.store(static_cast<unsigned>(kind));entry.verified.store(0);entry.stageRevision.store(0);
      entry.cancelForId.store(0);entry.cancelData.store(0);entry.file.store(0);
      entry.id.store(id,std::memory_order_release);current=record;
      Emit(Read(entry),"vfs.open.start","observed");return;
    }
    current=nullptr;SubjectEvent(currentInvoker,"vfs.capture_limit","operation_capacity_exhausted");
  }
  void Returned(bool value) noexcept{returned=true;result=value?"true":"false";}
  void Returned(long long value) noexcept{returned=true;result=value<0?"negative":value==0?"zero":"positive";}
  void Returned() noexcept{returned=true;result="void_return";}
  ~Open() noexcept
  {
    InfinityShutdownTrace::PreserveErrno keep;
    if(!record){if(restoreContext)current=previous;return;}
    record->end.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
    const auto s=Read(*record);
    // Keep the last executing stage rather than replacing it by "returned".
    Emit(s,"vfs.open.return",returned?result:
      (std::uncaught_exceptions()>exceptions?"exception_unwound":"unclassified"));
    Remember(s);record->id.store(0,std::memory_order_release);current=previous;
  }
  Open(const Open&)=delete;Open& operator=(const Open&)=delete;
  void Bind(const void* file,Backend backend=Backend::Unknown,bool verified=false) noexcept
  {
    if(!record)return;
    record->stageRevision.fetch_add(1,std::memory_order_acq_rel);
    record->file.store(reinterpret_cast<std::uintptr_t>(file));
    const auto old=record->state.load();
    record->state.store((old&~255U)|static_cast<unsigned>(backend));
    const bool identified=verified && backend!=Backend::Unknown && file;
    record->verified.store(identified?1:0);
    record->stageRevision.fetch_add(1,std::memory_order_release);
    Emit(Read(*record),"vfs.backend.identity",identified?"concrete_type_observed":
      file?"unclassified_concrete_type":"no_backend_object");
  }
private:
  Record* previous{};Record* record{};int exceptions{};
  bool returned{false},restoreContext{false};const char* result="unclassified";
};
class VoidCompletion
{
public:
  explicit VoidCompletion(Open& operation) noexcept:operation(operation),exceptions(std::uncaught_exceptions()){}
  ~VoidCompletion() noexcept
  {if(std::uncaught_exceptions()==exceptions)operation.Returned();}
private:Open& operation;int exceptions;
};
inline void Mark(Stage stage) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;if(!current)return;
  const auto old=current->state.load();
  if(((old>>8)&255)==static_cast<unsigned>(stage))return;
  const auto previousStage=static_cast<Stage>((old>>8)&255);
  if(previousStage!=Stage::CurlPoll && previousStage!=Stage::CurlPerform &&
     previousStage!=Stage::CurlCancelCheck)
    Emit(Read(*current),"vfs.stage.transition","previous_stage_ending");
  current->stageRevision.fetch_add(1,std::memory_order_acq_rel);
  current->stageStart.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
  current->state.store((old&~0xff00U)|(static_cast<unsigned>(stage)<<8));
  current->stageRevision.fetch_add(1,std::memory_order_release);
  // Poll/check stages are sampled, never write on every loop iteration.
}
inline void Select(Backend backend) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;if(!current)return;
  const auto old=current->state.load();
  current->stageRevision.fetch_add(1,std::memory_order_acq_rel);
  current->state.store((old&~0xffffU)|Pack(backend,Stage::BackendConstruction,Scheme::Other));
  current->stageStart.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
  current->verified.store(0);current->stageRevision.fetch_add(1,std::memory_order_release);
  Emit(Read(*current),"vfs.backend.selected","factory_choice_not_concrete_identity");
}
inline void TransferResult(int code) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;if(!current)return;
  char outcome[32]{};const auto ignored=std::snprintf(outcome,sizeof(outcome),"curl_result_code_%d",code);
  (void)ignored;Emit(Read(*current),"vfs.backend.transfer_result",outcome);
}
inline void Request(long long id,const char* outcome) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(!FindSubject(id))return;
  bool active=false;
  for(auto& r:operations)
  {const auto s=Read(r);if(s.id && s.invoker==id){active=true;Emit(s,"vfs.shutdown.request",outcome);}}
  if(!active)SubjectEvent(id,"vfs.shutdown.request","no_active_operation_observed");
}
inline void ObserveCancellation(Record& r,unsigned long long id) noexcept
{
  auto prior=r.cancelForId.load();
  for(unsigned attempt=0;attempt<3 && prior<id;++attempt)
    if(r.cancelForId.compare_exchange_weak(prior,id))return;
}
inline void CancellationBits(Record& r,unsigned long long id,unsigned bits) noexcept
{
  auto prior=r.cancelData.load();
  for(unsigned attempt=0;attempt<8;++attempt)
  {
    if((prior>>8)>id)return;
    const auto next=(id<<8)|bits|((prior>>8)==id?(prior&255):0);
    if(r.cancelData.compare_exchange_weak(prior,next))return;
  }
}
inline void BackendCancellation(const void* file,const char* outcome,bool entered=false) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;if(!file)return;
  for(auto& r:operations)
  {
    auto s=Read(r);
    if(s.id && s.file==reinterpret_cast<std::uintptr_t>(file))
    {
      const auto id=s.id;if(entered)ObserveCancellation(r,id);
      unsigned bits=entered?1U:0U;
      if(std::strcmp(outcome,"existing_flag_set")==0)bits=2;
      if(std::strcmp(outcome,"callback_returned")==0)bits=4;
      if(std::strcmp(outcome,"cancel_flag_seen_by_loop")==0)bits=8;
      CancellationBits(r,id,bits);s=Read(r);
      if(s.id==id && s.file==reinterpret_cast<std::uintptr_t>(file))
        Emit(s,"vfs.backend.cancellation",outcome);
    }
  }
}
inline void CancelFlagSeen() noexcept
{
  if(!current)return;
  const auto s=Read(*current);
  CancellationBits(*current,s.id,8);Emit(Read(*current),"vfs.backend.cancellation","cancel_flag_seen_by_loop");
}
class Callback
{
public:
  explicit Callback(const void* file) noexcept:target(file),exceptions(std::uncaught_exceptions())
  {
    InfinityShutdownTrace::PreserveErrno keep;
    for(auto& r:operations)
    {auto s=Read(r);if(s.id && s.file==reinterpret_cast<std::uintptr_t>(file))saved[size++]=s;}
    BackendCancellation(file,"callback_entered",true);
  }
  void FlagSet() noexcept
  {BackendCancellation(target,"existing_flag_set");for(unsigned i=0;i<size;++i)saved[i].cancelBits|=3;}
  ~Callback() noexcept
  {
    InfinityShutdownTrace::PreserveErrno keep;
    for(unsigned i=0;i<size;++i)
    {
      auto s=saved[i];bool active=false;
      for(auto& r:operations)
      {const auto now=Read(r);if(now.id==s.id){CancellationBits(r,s.id,4);s=Read(r);active=true;break;}}
      if(!active){s.cancelCalls=1;s.cancelBits|=4;}
      Emit(s,"vfs.backend.callback_return",
        std::uncaught_exceptions()>exceptions?"callback_exception_unwound":
        active?"callback_returned_operation_still_active":"callback_returned_operation_no_longer_active");
    }
    if(!size)
    {Snapshot s;s.generation=checkpointGeneration.load();Emit(s,"vfs.backend.callback_unmapped",
      "callback_observed_no_matching_active_operation");}
  }
private:const void* target;int exceptions;unsigned size{0};std::array<Snapshot,CAPACITY> saved{};
};
inline void Milestone(long long id,const char* phase,const char* outcome,bool release=false) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(auto* s=FindSubject(id))
  {
    if(std::strcmp(phase,"vfs.python.bytecode_return")==0)s->phase.store(2);
    else if(std::strcmp(phase,"vfs.python.children_wait")==0)s->phase.store(3);
    else if(std::strcmp(phase,"vfs.python.children_retired")==0)s->phase.store(4);
    else if(std::strcmp(phase,"vfs.python.interpreter_finalize")==0)s->phase.store(5);
    else if(std::strcmp(phase,"vfs.python.interpreter_end_return")==0)s->phase.store(6);
    else if(std::strcmp(phase,"vfs.python.stopped_event")==0)s->phase.store(7);
    else if(std::strcmp(phase,"vfs.python.interpreter_retired")==0)s->phase.store(8);
    else if(std::strcmp(phase,"vfs.python.native_exit_callback")==0)s->phase.store(9);
  }
  SubjectEvent(id,phase,outcome);
  if(release)if(auto* s=FindSubject(id))
  {
    long long expected=id;
    if(s->invoker.compare_exchange_strong(expected,-2))
    {s->hook.store(0);s->last.id.store(0);s->invoker.store(-1,std::memory_order_release);}
  }
}
inline void CheckpointBegin(unsigned long long generation) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;checkpointGeneration.store(generation);checkpointResult.store(0);
  for(auto& r:operations)
  {
    auto s=Read(r);if(!s.id)continue;
    r.generation.store(generation);s=Read(r);
    Emit(s,"vfs.checkpoint.active_operation","snapshot_at_request");
    Emit(s,"vfs.shutdown.request","checkpoint_request_not_backend_cancel");
  }
  Snapshot s;s.generation=generation;Emit(s,"vfs.checkpoint.request","native_request_accepted");
  constexpr const char* stages[]={"unknown","executing","bytecode_returned","waiting_child_states",
    "child_states_retired","interpreter_finalizing","interpreter_end_returned","stopped_event_set",
    "retirement_ledger_read","native_exit_callback"};
  for(auto& subject:subjects)
  {
    const auto id=subject.invoker.load();const auto phase=subject.phase.load();
    if(id>=0)SubjectEvent(id,"vfs.python.active_invoker",phase<10?stages[phase]:"unknown");
  }
}
inline void CheckpointOutcome(unsigned long long generation,bool safe) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  const auto result=(generation<<2)|(safe?1U:2U);
  if(checkpointResult.exchange(result)==result)return;
  checkpointObservedNs.store(InfinityShutdownTrace::Clock(CLOCK_MONOTONIC));
  pendingCheckpointResult.store(result,std::memory_order_release);
}
constexpr const char* OWNER_NAMES[]={"native_admission","python_services","background_jobs",
  "playback","command_center","compat","kodi_settings","profiles","skin_settings","addon_settings",
  "favourites","peripherals","audio_policy","deferred_dialog_state","xml_files","native_databases","pvr"};
struct PendingOwner
{
  std::atomic<unsigned long long> checkpoint{0},generation{0},durable{0},activeWrites{0};
  std::atomic<unsigned> flags{0};
  std::atomic<bool> ready{false};
};
inline std::array<PendingOwner,17> pendingOwners;
inline void OwnerStatus(unsigned long long checkpoint,const char* owner,
  unsigned long long generation,unsigned long long durable,bool dirty,bool complete,
  bool error,unsigned long long activeWrites) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  // Called under the existing coordinator lock: atomics only, no append I/O.
  for(unsigned i=0;i<17;++i)if(std::strcmp(owner,OWNER_NAMES[i])==0)
  {
    auto& p=pendingOwners[i];p.checkpoint.store(checkpoint);p.generation.store(generation);
    p.durable.store(durable);p.activeWrites.store(activeWrites);
    p.flags.store((dirty?1U:0U)|(complete?2U:0U)|(error?4U:0U));
    p.ready.store(true,std::memory_order_release);return;
  }
}
inline void FlushCheckpoint() noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  const auto result=pendingCheckpointResult.exchange(0,std::memory_order_acq_rel);
  if(result)
  {
    const bool safe=(result&3)==1;Snapshot s;s.generation=result>>2;
    Emit(s,"vfs.checkpoint.result",safe?"SAFE_TO_TERMINATE":"CHECKPOINT_FAILED");
    for(auto& r:operations)
    {auto active=Read(r);if(active.id)Emit(active,"vfs.checkpoint.pending_operation",safe?"native_safe_observed":"native_failure_observed");}
  }
  for(unsigned i=0;i<17;++i)
  {
    auto& p=pendingOwners[i];if(!p.ready.exchange(false,std::memory_order_acq_rel))continue;
    const auto generation=p.generation.load(),durable=p.durable.load(),activeWrites=p.activeWrites.load();
    const auto flags=p.flags.load();
  char outcome[160]{};
  const auto ignored=std::snprintf(outcome,sizeof(outcome),
    "gen_%llu_durable_%llu_dirty_%u_complete_%u_error_%u_active_writes_%llu",
    generation,durable,flags&1?1:0,flags&2?1:0,flags&4?1:0,activeWrites);
  (void)ignored;
  InfinityShutdownTrace::OperationMetadata m{0,0,p.checkpoint.load(),0,0,0,0,
    "not_a_VFS_operation","checkpoint_owner","other","checkpoint.durability",
    "not_applicable",0,0,0,0,0,0,"checkpoint_owner"};
  m.checkpointObservedMonotonicNs=checkpointObservedNs.load();
  InfinityShutdownTrace::Event("milestone","vfs.checkpoint.owner",-1,0,0,0,
    nullptr,outcome,OWNER_NAMES[i],&m);
  }
}
class CheckpointFlush
{
public:~CheckpointFlush() noexcept{FlushCheckpoint();}
};
static_assert(std::atomic<unsigned long long>::is_always_lock_free &&
  std::atomic<long long>::is_always_lock_free && std::atomic<std::uintptr_t>::is_always_lock_free &&
  std::atomic<char>::is_always_lock_free,"Diagnostics require lock-free atomics on this ABI");
}
