"""Additional observation hooks for all four requested capabilities."""
import re

ACTIVITY='xbmc/platform/android/activity/'
INCLUDE='#if defined(TARGET_ANDROID)\n#include "platform/android/activity/InfinityVfsOpenTrace.h"\n#endif\n'

def once(s,a,b):
    if s.count(a)!=1:raise ValueError('Ambiguous extension anchor '+repr(a[:120]))
    return s.replace(a,b,1)

def block(s,signature):
    start=s.index(signature+'\n{')
    opening=start+len(signature)+1
    # Ignore braces in comments and quoted strings.
    tokens=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]',re.S)
    depth=0
    for t in tokens.finditer(s,opening):
        if t.group()=='{':depth+=1
        elif t.group()=='}':
            depth-=1
            if depth==0:return start,t.end()
    raise ValueError(signature)

def wrap(s,signature,kind,returns,scheme='Scheme::Other',bind=False):
    a,b=block(s,signature);body=s[a:b]
    opening=body.index('\n{')+2
    original='  const char* const infinityOriginalFunction=__FUNCTION__;\n' if '__FUNCTION__' in body else ''
    body=body.replace('__FUNCTION__','infinityOriginalFunction')
    prefix='\n'+original+'#if defined(TARGET_ANDROID)\n  InfinityVfsOpenTrace::Open infinityOpen(InfinityVfsOpenTrace::'+scheme+',InfinityVfsOpenTrace::Kind::'+kind+');\n'
    if bind:prefix+='  infinityOpen.Bind(m_pFile.get(),InfinityVfsOpenTrace::Identify(m_pFile.get()),m_pFile!=nullptr);\n  INFINITY_VFS_STEP(BackendCall);\n'
    prefix+='  '+('const '+returns+' infinityResult = ' if returns!='void' else '')+'[&]() -> '+returns+' {\n#endif\n'
    body=body[:opening]+prefix+body[opening:-1]
    suffix='\n#if defined(TARGET_ANDROID)\n  }();\n  infinityOpen.Returned('+('' if returns=='void' else 'infinityResult' if returns=='bool' else 'static_cast<long long>(infinityResult)')+');\n'
    if returns!='void':suffix+='  return infinityResult;\n'
    body+=suffix+'#endif\n}'
    return s[:a]+body+s[b:]

def metadata(s):
    s=once(s,'inline std::atomic<unsigned> count{0};',"""struct OperationMetadata
{
  unsigned long long id,parent,generation;
  long long startedMonotonicNs,stageStartedMonotonicNs,endedMonotonicNs,workerTid;
  const char* backend;const char* stage;const char* scheme;const char* kind;
  const char* cancellationSupport;
  unsigned cancelObserved,cancelOutcomes,identityVerified;
  unsigned long long subjectExecutionId;
  long long subjectStartedMonotonicNs,subjectWorkerTid;
  const char* ownerKind;
  long long checkpointObservedMonotonicNs{0};
};
inline std::atomic<unsigned> count{0};""")
    # Independent diagnostic retention does not consume the existing critical
    # timeline's 1024-event allowance or change its limit.
    s=once(s,'inline std::atomic<unsigned> count{0};',"""inline std::atomic<unsigned> vfsCount{0};
constexpr unsigned MAX_VFS_EVENTS=4096;
inline std::atomic<unsigned> count{0};""")
    s=once(s,'  if (serial>MAX_EVENTS && criticalSerial>MAX_CRITICAL_EVENTS) return;',"""  const bool vfs=phase && std::strncmp(phase,"vfs.",4)==0;
  const unsigned vfsSerial=vfs?vfsCount.fetch_add(1):MAX_VFS_EVENTS+1;
  if (serial>MAX_EVENTS && criticalSerial>MAX_CRITICAL_EVENTS && vfsSerial>MAX_VFS_EVENTS) return;""")
    s=once(s,'if (critical && criticalSerial<MAX_CRITICAL_EVENTS && criticalFd>=0)',
      'if (((critical && criticalSerial<MAX_CRITICAL_EVENTS) || (vfs && vfsSerial<MAX_VFS_EVENTS)) && criticalFd>=0)')
    s=once(s,'  if (serial==MAX_EVENTS || (critical && criticalSerial==MAX_CRITICAL_EVENTS))',
      '  if (serial==MAX_EVENTS || (critical && criticalSerial==MAX_CRITICAL_EVENTS) || (vfs && vfsSerial==MAX_VFS_EVENTS))')
    s=once(s,'const char* target=nullptr) noexcept\n{','const char* target=nullptr,\n                  const OperationMetadata* operation=nullptr) noexcept\n{')
    s=once(s,'  char row[1024]{};\n',r'''  char extension[1200]{};
  if(operation)
  {
    char backend[33]{},stage[41]{},scheme[17]{},op[33]{},support[49]{},ownerKind[33]{};
    Token(operation->backend,backend,sizeof(backend));Token(operation->stage,stage,sizeof(stage));
    Token(operation->scheme,scheme,sizeof(scheme));Token(operation->kind,op,sizeof(op));
    Token(operation->cancellationSupport,support,sizeof(support));
    Token(operation->ownerKind,ownerKind,sizeof(ownerKind));
    const auto ignored=std::snprintf(extension,sizeof(extension),
      ",\"operation_id\":%llu,\"operation_parent_id\":%llu,\"checkpoint_generation\":%llu,\"operation_start_monotonic_ns\":%lld,\"stage_start_monotonic_ns\":%lld,\"operation_end_monotonic_ns\":%lld,\"operation_worker_tid\":%lld,\"backend_category\":\"%s\",\"backend_identity_observed\":%u,\"operation_kind\":\"%s\",\"operation_stage\":\"%s\",\"resource_category\":\"%s\",\"cancellation_support\":\"%s\",\"backend_cancel_callback_observed\":%u,\"cancellation_outcome_bits\":%u,\"subject_execution_id\":%llu,\"subject_start_monotonic_ns\":%lld,\"subject_worker_tid\":%lld,\"owner_kind\":\"%s\",\"checkpoint_outcome_observed_monotonic_ns\":%lld",
      operation->id,operation->parent,operation->generation,operation->startedMonotonicNs,
      operation->stageStartedMonotonicNs,operation->endedMonotonicNs,operation->workerTid,
      backend,operation->identityVerified,op,stage,scheme,support,operation->cancelObserved,operation->cancelOutcomes,
      operation->subjectExecutionId,operation->subjectStartedMonotonicNs,operation->subjectWorkerTid,ownerKind,
      operation->checkpointObservedMonotonicNs);
    (void)ignored;
  }
  char row[2304]{};
''')
    s=once(s,'\\\"target_thread\\\":\\\"%s\\\"}\\n",','\\\"target_thread\\\":\\\"%s\\\"%s}\\n",')
    s=once(s,'durationNs,outcome,safeTarget);','durationNs,outcome,safeTarget,extension);')
    s=once(s,'inline void Begin() noexcept',r'''struct NativeScopeRecord
{
  std::atomic<unsigned long long> id{0},parent{0};
  std::atomic<long long> started{0},invoker{-1},tid{0};
  std::array<std::atomic<char>,81> phase{};
};
inline std::array<NativeScopeRecord,128> nativeScopes;
inline void NativeScopeEvent(unsigned long long id,unsigned long long parent,
  long long start,long long end,long long invoker,long long tid,const char* phase,
  const char* outcome) noexcept
{
  OperationMetadata m{id,parent,0,start,start,end,tid,
    std::strncmp(phase,"sqlite.",7)==0?"sqlite":
    std::strncmp(phase,"python.",7)==0?"python_runtime":"native_backend_unobserved",
    "native_scope","other","native_scope","unobservable",0,0,0,0,0,0,"native_scope"};
  Event("milestone",end?"vfs.native.scope_return":"vfs.native.scope_pending",
    invoker,id,parent,Clock(CLOCK_MONOTONIC)-start,nullptr,outcome,phase,&m);
}
inline void NativeScopeSnapshots() noexcept
{
  for(auto& r:nativeScopes)
  {
    const auto id=r.id.load(std::memory_order_acquire);
    if(!id || id==std::numeric_limits<unsigned long long>::max())continue;
    char phase[81]{};
    for(unsigned i=0;i<80;++i)phase[i]=r.phase[i].load();
    const auto parent=r.parent.load();const auto start=r.started.load();
    const auto invoker=r.invoker.load(),tid=r.tid.load();
    if(id==r.id.load(std::memory_order_acquire))
      NativeScopeEvent(id,parent,start,0,invoker,tid,phase,"active_at_capture_begin");
    else Event("milestone","vfs.snapshot_gap",-1,0,0,0,nullptr,"native_scope_snapshot_changed");
  }
}
inline void Begin() noexcept''')
    s=once(s,'#include <atomic>','#include <atomic>\n#include <array>\n#include <limits>')
    s=once(s,'  Event("milestone","capture.begin");','  Event("milestone","capture.begin");\n  NativeScopeSnapshots();')
    s=once(s,'    if (descriptor.load(std::memory_order_acquire)<0) return;','''    // Retain active native scopes before Close; append no evidence until Begin.
''')
    anchor='    m_start=Clock(CLOCK_MONOTONIC);m_exceptions=std::uncaught_exceptions();'
    s=once(s,anchor,anchor+'''
    m_tid=static_cast<long long>(::syscall(SYS_gettid));
    for(auto& r:nativeScopes)
    {
      unsigned long long empty=0;
      if(!r.id.compare_exchange_strong(empty,std::numeric_limits<unsigned long long>::max()))continue;
      m_record=&r;char phase[81]{};Token(m_phase,phase,sizeof(phase));
      for(unsigned i=0;i<81;++i)r.phase[i].store(phase[i]);
      r.parent.store(m_parent);r.started.store(m_start);r.invoker.store(m_invoker);r.tid.store(m_tid);
      r.id.store(m_id,std::memory_order_release);break;
    }
    if(!m_record)Event("milestone","vfs.capture_limit",m_invoker,0,0,0,nullptr,"native_scope_capacity_exhausted");
''')
    s=once(s,'    if(parentId==m_id) parentId=m_parent;',r'''    NativeScopeEvent(m_id,m_parent,m_start,Clock(CLOCK_MONOTONIC),m_invoker,m_tid,m_phase,
      std::uncaught_exceptions()>m_exceptions?"scope_unwound_not_success":"scope_returned_not_success");
    if(m_record)m_record->id.store(0,std::memory_order_release);
    if(parentId==m_id) parentId=m_parent;''')
    s=once(s,'  long long m_start{0};','  NativeScopeRecord* m_record{nullptr};\n  long long m_tid{0};\n  long long m_start{0};')
    return s

def extend(name,s):
    if name=='xbmc/filesystem/File.cpp':
        s=s.replace('infinityOpen.Bind(m_pFile.get());','infinityOpen.Bind(m_pFile.get(),InfinityVfsOpenTrace::Identify(m_pFile.get()),m_pFile!=nullptr);')
        s=s.replace('        INFINITY_VFS_BACKEND((void)0,Unknown);\n','')
        a,b=block(s,'bool CFile::Open(const CURL& file, const unsigned int flags)')
        body=s[a:b]
        body=once(body,'  if (m_pFile)\n',"""#if defined(TARGET_ANDROID)
    infinityOpen.Bind(m_pFile.get(),InfinityVfsOpenTrace::Identify(m_pFile.get()),m_pFile!=nullptr);
#endif
  if (m_pFile)
""")
        s=s[:a]+body+s[b:]
        s=once(s,'        m_pFile = std::make_unique<CFileCache>(m_flags);',"""        m_pFile = std::make_unique<CFileCache>(m_flags);
#if defined(TARGET_ANDROID)
        infinityOpen.Bind(m_pFile.get(),InfinityVfsOpenTrace::Identify(m_pFile.get()),true);
#endif""")
        specs=[
          ('bool CFile::OpenForWrite(const CURL& file, bool bOverWrite)','OpenForWrite','bool',False),
          ('bool CFile::Exists(const CURL& file, bool bUseCache /* = true */)','Exists','bool',False),
          ('int CFile::Stat(const CURL& file, struct __stat64* buffer)','Stat','int',False),
          ('int CFile::Stat(struct __stat64 *buffer)','Stat','int',True),
          ('ssize_t CFile::Read(void *lpBuf, size_t uiBufSize)','Read','ssize_t',True),
          ('ssize_t CFile::Write(const void* lpBuf, size_t uiBufSize)','Write','ssize_t',True),
          ('void CFile::Close()','Close','void',True),
          ('void CFile::Flush()','Flush','void',True),
          ('int64_t CFile::Seek(int64_t iFilePosition, int iWhence)','Seek','int64_t',True),
          ('int CFile::Truncate(int64_t iSize)','Truncate','int',True),
          ('int64_t CFile::GetLength()','GetLength','int64_t',True),
          ('int64_t CFile::GetPosition() const','GetPosition','int64_t',True),
          ('bool CFile::ReadString(char *szLine, int iLineLength)','ReadString','bool',True),
          ('bool CFile::Delete(const CURL& file)','Delete','bool',False),
          ('bool CFile::Rename(const CURL& file, const CURL& newFile)','Rename','bool',False),
          ('bool CFile::SetHidden(const CURL& file, bool hidden)','SetHidden','bool',False),
          ('int CFile::IoControl(EIoControl request, void* param)','IoControl','int',True),
          ('int CFile::GetChunkSize()','GetChunkSize','int',True)]
        for signature,kind,ret,bind in specs:
            s=wrap(s,signature,kind,ret,'Protocol(file)' if 'CURL& file' in signature else 'Scheme::Other',bind)
        # Each independent factory/redirect pointer is observed after ownership
        # transfer and before its backend call, including Exists and Stat.
        s=s.replace('std::unique_ptr<IFile> pFile(CFileFactory::CreateLoader(url));',"""std::unique_ptr<IFile> pFile(CFileFactory::CreateLoader(url));
#if defined(TARGET_ANDROID)
    infinityOpen.Bind(pFile.get(),InfinityVfsOpenTrace::Identify(pFile.get()),pFile!=nullptr);
#endif
    INFINITY_VFS_STEP(BackendCall);""")
        s=s.replace('std::unique_ptr<IFile> pImp(pRedirectEx->m_pNewFileImp);',"""std::unique_ptr<IFile> pImp(pRedirectEx->m_pNewFileImp);
#if defined(TARGET_ANDROID)
      infinityOpen.Bind(pImp.get(),InfinityVfsOpenTrace::Identify(pImp.get()),pImp!=nullptr);
#endif
      INFINITY_VFS_STEP(Redirect);""")
        # OpenForWrite is the other persistent loader assignment.
        anchor='    m_pFile.reset(CFileFactory::CreateLoader(url));\n\n'
        s=once(s,anchor,anchor.rstrip('\n')+"""
#if defined(TARGET_ANDROID)
    infinityOpen.Bind(m_pFile.get(),InfinityVfsOpenTrace::Identify(m_pFile.get()),m_pFile!=nullptr);
#endif
    INFINITY_VFS_STEP(BackendCall);

""")
        # Emit the slow stage when that stage returns, not on each poll.
        s=s.replace('    CURL url = URIUtils::SubstitutePath(file);','    INFINITY_VFS_STEP(SubstitutePath);\n    CURL url = URIUtils::SubstitutePath(file);')
        s=s.replace('  CURL url(URIUtils::SubstitutePath(file));','  INFINITY_VFS_STEP(SubstitutePath);\n  CURL url(URIUtils::SubstitutePath(file));')
        s=s.replace('CPasswordManager::GetInstance().AuthenticateURL(authUrl);',
          '(INFINITY_VFS_STEP(Authentication),CPasswordManager::GetInstance().AuthenticateURL(authUrl));')
        return s
    if name=='xbmc/filesystem/FileFactory.cpp':
        s=s.replace('#include "FileFactory.h"','#include "FileFactory.h"\n#include "FileCache.h"\n#include <typeinfo>')
        # Derive every exact concrete branch from the same conditional includes.
        known={'CurlFile':'Curl','DAVFile':'Dav','ShoutcastFile':'Shoutcast','CDDAFile':'Cdda',
          'ISO9660File':'Iso','APKFile':'Apk','XbtFile':'Xbt','ZipFile':'Zip','NFSFile':'Nfs',
          'AndroidAppFile':'AndroidApp','TVOSFile':'TvOs','UPnPFile':'Upnp','BlurayFile':'Bluray',
          'PipeFile':'Pipe','MusicDatabaseFile':'MusicDb','VideoDatabaseFile':'VideoDb',
          'PluginFile':'Plugin','SpecialProtocolFile':'Special','MultiPathFile':'MultiPath',
          'UDFFile':'Udf','ImageFile':'Image','ResourceFile':'Resource','PosixFile':'Posix',
          'Win32File':'Windows','WinLibraryFile':'WinLibrary','Win32SMBFile':'WinSmb','SMBFile':'Smb'}
        classes={'APKFile':'CAPKFile','AndroidAppFile':'CFileAndroidApp','CDDAFile':'CFileCDDA',
          'ISO9660File':'CISO9660File','UDFFile':'CUDFFile'}
        lines=[];seen=False
        for line in s.splitlines():
            if line=='#ifdef TARGET_POSIX':seen=True
            if not seen:continue
            if line=='using namespace ADDON;':break
            if line.startswith(('#if','#elif','#else','#endif')):lines.append(line)
            if line.startswith('#include'):
                quoted=re.search(r'#include "([^"]+)"',line)
                stem=quoted.group(1).split('/')[-1].removesuffix('.h') if quoted else ''
                if stem in known:
                    if stem=='CDDAFile':lines.append('#if defined(HAS_OPTICAL_DRIVE)')
                    lines.append('  if(typeid(*file)==typeid(XFILE::'+classes.get(stem,'C'+stem)+'))return Backend::'+known[stem]+';')
                    if stem=='CDDAFile':lines.append('#endif')
        # The add-on wrapper lives in namespace ADDON (not XFILE).
        body='\n'.join(lines)
        s+='''\n#if defined(TARGET_ANDROID)
namespace InfinityVfsOpenTrace
{
Backend Identify(const XFILE::IFile* file) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  if(!file)return Backend::Unknown;
  if(typeid(*file)==typeid(XFILE::CFileCache))return Backend::FileCache;
  if(typeid(*file)==typeid(ADDON::CVFSEntryIFileWrapper))return Backend::Addon;
'''+body+'''
  return Backend::Unknown;
}
}
#endif
'''
        return s
    if name=='xbmc/filesystem/CurlFile.cpp':
        s=once(s,'  INFINITY_VFS_CANCEL(static_cast<IFile*>(this),"callback_entered",true);',"""#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Callback infinityCancellation(static_cast<IFile*>(this));
#endif""")
        s=once(s,'  INFINITY_VFS_CANCEL(static_cast<IFile*>(this),"existing_flag_set",false);',"""#if defined(TARGET_ANDROID)
  infinityCancellation.FlagSet();
#endif""")
        s=once(s,'    if (m_cancelled)\n',"""#if defined(TARGET_ANDROID)
    if (m_cancelled) InfinityVfsOpenTrace::CancelFlagSeen();
#endif
    if (m_cancelled)
""")
        return s
    if name=='xbmc/interfaces/python/PythonInvoker.cpp':
        s=once(s,'''    m_addon && m_addon->ID()=="plugin.video.playlistbrowser" &&
    URIUtils::GetFileName(script)=="service.py");''','    true,m_addon?m_addon->ID().c_str():nullptr);')
        s=once(s,'  PyObject* sysArgv = PyList_New(0);',"""#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::AttachLanguageHook(GetId(),m_languageHook.get());
#endif
  PyObject* sysArgv = PyList_New(0);""")
        s=once(s,'      if (!s)\n        break;',"""      if (!s)
      {
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.children_retired",
          "no_other_interpreter_thread_states_observed");
#endif
        break;
      }""")
        s=once(s,'      Py_EndInterpreter(m_threadState);',"""      Py_EndInterpreter(m_threadState);
#if defined(TARGET_ANDROID)
      InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.interpreter_end_return",
        "Py_EndInterpreter_returned_not_durability_proof");
#endif""")
        s=once(s,'    m_stoppedEvent.Set();',"""    m_stoppedEvent.Set();
#if defined(TARGET_ANDROID)
    InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.stopped_event",
      "existing_event_set_not_native_thread_death");
#endif""")
        s=once(s,'        old = s;','''        old = s;
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.children_wait","other_interpreter_thread_state_observed");
#endif''')
        s=once(s,'      InfinityShutdownTrace::Scope evidence("python.finalize.end_interpreter", GetId(), nullptr, nullptr);',
          '''      InfinityShutdownTrace::Scope evidence("python.finalize.end_interpreter", GetId(), nullptr, nullptr);
#if defined(TARGET_ANDROID)
      InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.interpreter_finalize","before_Py_EndInterpreter");
#endif''')
        return s
    if name=='xbmc/interfaces/generic/ScriptInvocationManager.cpp':
        return once(s,'retired?"durability_receipt_taken":"no_durability_receipt",true);',
          'retired?"durability_receipt_taken":"no_durability_receipt");')
    raise ValueError(name)

def additional(name,s):
    if name=='xbmc/interfaces/legacy/LanguageHook.h':
        s=once(s,'#include "threads/Event.h"','#include "threads/Event.h"\n'+INCLUDE)
        s=once(s,'    LanguageHook* languageHook;','''    LanguageHook* languageHook;
#if defined(TARGET_ANDROID)
    InfinityVfsOpenTrace::ThreadContext infinityVfsContext;
#endif''')
        for ctor in ['inline explicit DelayedCallGuard(LanguageHook* languageHook_) : languageHook(languageHook_)',
                     'inline DelayedCallGuard() : languageHook(LanguageHook::GetLanguageHook())']:
            s=once(s,ctor,ctor+'''
#if defined(TARGET_ANDROID)
      , infinityVfsContext(languageHook)
#endif''')
        return s
    if name=='xbmc/interfaces/legacy/File.h':
        return once(s,'inline ~File() override { delete file; }',"""inline ~File() override
      {
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::ThreadContext infinityVfsContext(languageHook);
#endif
        delete file;
      }""")
    if name=='xbmc/filesystem/FileCache.cpp':
        s=once(s,'#include "FileCache.h"','#include "FileCache.h"\n'+INCLUDE)
        a,b=block(s,'bool CFileCache::Open(const CURL& url)');body=s[a:b]
        body=once(body,'\n  Close();','''\n  Close();
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::RegisterFile(static_cast<IFile*>(this));
#endif''')
        s=s[:a]+body+s[b:]
        s=once(s,'void CFileCache::Process()\n{',"""void CFileCache::Process()
{
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::FileContext infinityVfsContext(static_cast<IFile*>(this));
  InfinityVfsOpenTrace::Open infinityCacheWorker(InfinityVfsOpenTrace::Scheme::Other,InfinityVfsOpenTrace::Kind::CacheProcess);
  InfinityVfsOpenTrace::VoidCompletion infinityCacheCompletion(infinityCacheWorker);
  infinityCacheWorker.Bind(static_cast<IFile*>(this),InfinityVfsOpenTrace::Backend::FileCache,true);
  InfinityVfsOpenTrace::Mark(InfinityVfsOpenTrace::Stage::CacheWorker);
#endif""")
        s=once(s,'void CFileCache::StopThread(bool bWait /*= true*/)\n{',"""void CFileCache::StopThread(bool bWait /*= true*/)
{
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Callback infinityCancellation(static_cast<IFile*>(this));
#endif""")
        s=once(s,'  m_seekEvent.Set();\n  CThread::StopThread(bWait);','''  m_seekEvent.Set();
#if defined(TARGET_ANDROID)
  infinityCancellation.FlagSet();
#endif
  CThread::StopThread(bWait);
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::BackendCancellation(static_cast<IFile*>(this),
    bWait?"worker_join_returned":"nonblocking_worker_stop_returned");
#endif''')
        s=once(s,'  StopThread();','''  StopThread();
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::ForgetFile(static_cast<IFile*>(this));
#endif''')
        return s
    if name=='xbmc/interfaces/generic/LanguageInvokerThread.cpp':
        s=once(s,'#include "LanguageInvokerThread.h"','#include "LanguageInvokerThread.h"\n'+INCLUDE)
        s=once(s,'    CThread::StopThread(wait);','''    CThread::StopThread(wait);
#if defined(TARGET_ANDROID)
    InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.native_stop_return",
      wait?"blocking_StopThread_returned":"nonblocking_stop_not_join_proof");
#endif''')
        for stage in ['ExitReported','ExceptionReported']:
            anchor='  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::'+stage+');'
            s=once(s,anchor,anchor+'\n  InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.native_exit_callback",\n    "'+stage+'_callback_not_OS_death",true);')
        return s
    if name==ACTIVITY+'InfinityAndroidCheckpoint.cpp':
        s=INCLUDE+s
        s=once(s,'void BlockLocked(State& s,',"""void InfinityDiagnosticOwners(const State& s)
{
  // Called under the existing state lock; only fixed required-owner names and
  // counters leave this snapshot. No blocker details, paths or error text.
  for(const char* name:REQUIRED)
  {
    const auto it=s.owners.find(name);
    if(it==s.owners.end())continue;
    const auto& o=it->second;
    InfinityVfsOpenTrace::OwnerStatus(s.generation,name,o.generation,o.durableGeneration,
      o.dirty,o.complete,!o.error.empty(),s.activeWrites);
  }
}
void BlockLocked(State& s,""")
        # The diagnostic result is read only from the authoritative state path.
        s=once(s,'    s.phase="CHECKPOINT_FAILED";','    s.phase="CHECKPOINT_FAILED";\n    InfinityVfsOpenTrace::CheckpointOutcome(s.generation,false);')
        s=once(s,'\n  s.phase="CHECKPOINT_FAILED";','\n  s.phase="CHECKPOINT_FAILED";\n  InfinityVfsOpenTrace::CheckpointOutcome(s.generation,false);')
        s=once(s,'\n    s.inventoryComplete=true;\n','\n    s.inventoryComplete=true;\n    InfinityDiagnosticOwners(s);\n')
        s=once(s,'  s.safeStatus.clear();\n}\nvoid CheckDeadlineLocked','  s.safeStatus.clear();\n  InfinityDiagnosticOwners(s);\n}\nvoid CheckDeadlineLocked')
        a,b=block(s,'bool Request(const std::string& session, const std::string& owner, int pid)');body=s[a:b]
        body=once(body,'  auto& s = Get();','  auto& s = Get();\n  unsigned long long infinityDiagnosticGeneration=0;')
        body=once(body,'    ++s.generation;','    ++s.generation;\n    infinityDiagnosticGeneration=s.generation;')
        body=once(body,'  InfinityShutdownTrace::Begin();','  InfinityShutdownTrace::Begin();\n  InfinityVfsOpenTrace::CheckpointBegin(infinityDiagnosticGeneration);')
        s=s[:a]+body+s[b:]
        s=once(s,'      s.safeStatus = EncodeStatusLocked(s);','      s.safeStatus = EncodeStatusLocked(s);\n      InfinityVfsOpenTrace::CheckpointOutcome(s.generation,true);')
        s=once(s,'      InfinityVfsOpenTrace::CheckpointOutcome(s.generation,true);',
          '      InfinityVfsOpenTrace::CheckpointOutcome(s.generation,true);\n      InfinityDiagnosticOwners(s);')
        # Destruction follows all existing inner state-lock scopes. Queue only
        # atomics while locked; use the existing append channel after unlock.
        for signature in ['bool Request(const std::string& session, const std::string& owner, int pid)',
                          'std::string Status(const std::string& session, const std::string& owner, int pid)',
                          'void Pump(CApplication& application)',
                          'void RecordFatalFailure(const char* owner,const char* detail)',
                          'void NotifyLegacyTeardown(const char* operation)']:
            s=once(s,signature+'\n{',signature+'\n{\n  InfinityVfsOpenTrace::CheckpointFlush infinityDiagnosticFlush;')
        return s
    raise ValueError(name)
