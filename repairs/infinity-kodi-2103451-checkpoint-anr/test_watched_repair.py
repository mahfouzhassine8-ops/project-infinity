"""Actual watched Work/receipt code with real file SQLite and controlled Kodi peers."""
from pathlib import Path
import argparse
import ctypes.util
import hashlib
import importlib.util
import json
import shutil
import sqlite3
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

PEERS = r'''
#pragma once
#include "utils/Job.h"
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include <cassert>
#include <memory>
#include <string>
#include <vector>
// Public SQLite C ABI declarations for the installed host library. No app
// dependency or Kodi database implementation is replaced by this host fixture.
extern "C" {
struct sqlite3;struct sqlite3_stmt;
int sqlite3_open(const char*,sqlite3**);int sqlite3_close(sqlite3*);
int sqlite3_exec(sqlite3*,const char*,int(*)(void*,int,char**,char**),void*,char**);
int sqlite3_prepare_v2(sqlite3*,const char*,int,sqlite3_stmt**,const char**);
int sqlite3_step(sqlite3_stmt*);int sqlite3_column_int(sqlite3_stmt*,int);
int sqlite3_finalize(sqlite3_stmt*);int sqlite3_get_autocommit(sqlite3*);
const char* sqlite3_libversion();
}
inline std::string fixtureMode,fixturePath;
inline int remoteCalls=0;
struct CDateTime {bool valid=false;CDateTime()=default;explicit CDateTime(bool b):valid(b){}bool IsValid()const{return valid;}};
struct CBookmark {enum EType{STANDARD=0,RESUME=1};};
struct VideoInfoTag {std::string path;int count=0;CDateTime m_lastPlayed;
 int GetPlayCount()const{return count;}const std::string& GetPath()const{return path;}};
class CFileItem {public:bool m_bIsFolder=false,pvr=false;std::string path;VideoInfoTag tag;
 explicit CFileItem(std::string p):path(std::move(p)){tag.path=path;}
 const std::string& GetPath()const{return path;}bool HasVideoInfoTag()const{return true;}
 VideoInfoTag* GetVideoInfoTag(){return &tag;}const VideoInfoTag* GetVideoInfoTag()const{return &tag;}
 bool HasPVRRecordingInfoTag()const{return pvr;}int* GetPVRRecordingInfoTag(){static int r;return &r;}
 bool IsSamePath(const CFileItem* other)const{return other && path==other->path;}};
using CFileItemPtr=std::shared_ptr<CFileItem>;
class CFileItemList {std::vector<CFileItemPtr> items;public:void Add(CFileItemPtr i){items.push_back(i);}
 int Size()const{return static_cast<int>(items.size());}CFileItemPtr Get(int i){return items.at(i);}};
namespace XFILE {constexpr int DIR_FLAG_NO_FILE_INFO=0;}
struct CUtil {static void GetRecursiveListing(const std::string&,CFileItemList&,const char*,int){}};
namespace URIUtils {inline bool IsUPnP(const std::string& p){return p.rfind("upnp://",0)==0;}}
namespace UPNP {struct CUPnP {static bool MarkWatched(CFileItem&,bool){++remoteCalls;return true;}};}
struct Profile {bool canWriteDatabases()const{return true;}};
struct CProfileManager {const Profile& GetCurrentProfile()const{static Profile p;return p;}};
struct Settings {std::shared_ptr<CProfileManager> GetProfileManager(){static auto p=std::make_shared<CProfileManager>();return p;}};
struct Recordings {bool MarkWatched(int*,bool){++remoteCalls;return true;}};
struct PVRManager {::Recordings* Recordings(){static ::Recordings r;return &r;}};
struct CServiceBroker {static Settings* GetSettingsComponent(){static Settings s;return &s;}
 static PVRManager& GetPVRManager(){static PVRManager p;return p;}};
class CVideoLibraryQueue:public IJobCallback {public:void OnJobComplete(unsigned int,bool,CJob*)override{}};
inline std::string quote(std::string s){std::string result="'";for(char c:s){result+=c;if(c=='\'')result+='\'';}return result+"'";}
class CVideoDatabase {
 sqlite3* connection=nullptr;
 bool execute(const std::string& sql){InfinityDatabaseBarrier::Operation op(this);
  if(!op.AllowWrite())return false;
  const bool ok=sqlite3_exec(connection,sql.c_str(),nullptr,nullptr,nullptr)==0;
  if(!ok){InfinityDatabaseBarrier::RecordFailure("fixture.sqlite.execute");}
  return ok;}
 int query(const std::string& sql){InfinityDatabaseBarrier::Operation op(this);sqlite3_stmt* statement=nullptr;
  if(sqlite3_prepare_v2(connection,sql.c_str(),-1,&statement,nullptr)!=0){InfinityDatabaseBarrier::RecordFailure("fixture.sqlite.prepare");return -1;}
  const int status=sqlite3_step(statement);const int value=status==100?sqlite3_column_int(statement,0):-1;
  if(status!=100)InfinityDatabaseBarrier::RecordFailure("fixture.sqlite.read");
  if(sqlite3_finalize(statement)!=0){InfinityDatabaseBarrier::RecordFailure("fixture.sqlite.finalize");}
  return value;}
public:
 ~CVideoDatabase(){Close();}
 bool Open(){InfinityDatabaseBarrier::Operation op(this);
  if(sqlite3_open(fixturePath.c_str(),&connection)!=0){InfinityDatabaseBarrier::RecordFailure("fixture.sqlite.open");return false;}return true;}
 void Close(){if(!connection)return;{
  InfinityDatabaseBarrier::Operation op(this);
  if(!sqlite3_get_autocommit(connection))execute("ROLLBACK");
  InfinityDatabaseBarrier::SetTransaction(this,!sqlite3_get_autocommit(connection));
  const int result=sqlite3_close(connection);
  if(result==0)connection=nullptr;else InfinityDatabaseBarrier::RecordFailure("fixture.sqlite.close");
  if(fixtureMode=="close-failure")InfinityDatabaseBarrier::RecordFailure("fixture.injected.close");
 }if(!connection)InfinityDatabaseBarrier::ForgetOwner(this);}
 void BeginTransaction(){if(fixtureMode=="begin-failure"){InfinityDatabaseBarrier::RecordFailure("fixture.injected.begin");return;}
  execute("BEGIN IMMEDIATE");InfinityDatabaseBarrier::SetTransaction(this,!sqlite3_get_autocommit(connection));}
 bool CommitTransaction(){if(fixtureMode=="commit-failure"){InfinityDatabaseBarrier::RecordFailure("fixture.injected.commit");return false;}
  const bool result=execute("COMMIT");InfinityDatabaseBarrier::SetTransaction(this,!sqlite3_get_autocommit(connection));return result;}
 void ClearBookMarksOfFile(const std::string& path,CBookmark::EType){execute("DELETE FROM bookmark WHERE path="+quote(path));}
 CDateTime IncrementPlayCount(const CFileItem& item){const bool ok=execute("UPDATE media SET playCount=playCount+1 WHERE path="+quote(item.GetPath()));return CDateTime(ok);}
 CDateTime SetPlayCount(const CFileItem& item,int value){const bool ok=execute("UPDATE media SET playCount="+std::to_string(value)+" WHERE path="+quote(item.GetPath()));return CDateTime(ok);}
 int GetPlayCount(const CFileItem& item){if(fixtureMode=="count-read-error"){InfinityDatabaseBarrier::RecordFailure("fixture.injected.count_read");return -1;}
  return query("SELECT playCount FROM media WHERE path="+quote(item.GetPath()));}
 bool GetResumeBookMark(const std::string& path,CBookmark&){if(fixtureMode=="resume-read-error"){InfinityDatabaseBarrier::RecordFailure("fixture.injected.resume_read");return false;}
  return query("SELECT COUNT(*) FROM bookmark WHERE path="+quote(path))>0;}
};
'''

MAIN = r'''
#include "test_peers.h"
#include "utils/JobManager.h"
#include "video/jobs/VideoLibraryMarkWatchedJob.h"
#include <iostream>
#include <typeinfo>
namespace InfinityAndroidCheckpoint {bool IsRequiredOwner(const std::string& s){return s=="native_databases"||s=="playback";}}
bool CJob::ShouldCancel(unsigned int,unsigned int)const{return false;}
class ForeignQueue:public CVideoLibraryQueue {};
class ForeignWatched:public CVideoLibraryMarkWatchedJob {public:using CVideoLibraryMarkWatchedJob::CVideoLibraryMarkWatchedJob;};
TRACKING_BODIES
int main(int argc,char** argv){
 assert(argc==3);fixtureMode=argv[1];fixturePath=argv[2];
#if defined(P0_PROTECTED_RESOURCE_PEER)
 if(fixtureMode=="protected-resource-refusal"){
  assert(InfinityDatabaseBarrier::Begin(1));
  assert(InfinityDatabaseBarrier::GetSnapshot().Ready());
  fixtureProtectedResources=1;
  const auto blocked=InfinityDatabaseBarrier::GetSnapshot();
  assert(blocked.protectedResourceBlockers==1 && !blocked.Ready());
  fixtureProtectedResources=0;
  assert(InfinityDatabaseBarrier::GetSnapshot().Ready());
  std::cout<<"HOST_PASS protected-resource-refusal; snapshot predicate only, no shutdown saved\n";
  return 0;
 }
#endif
 const bool remote=fixtureMode=="unknown-upnp",pvr=fixtureMode=="unknown-pvr",folder=fixtureMode=="unknown-folder";
 const bool foreignCallback=fixtureMode=="unknown-callback",foreignJob=fixtureMode=="unknown-job";
 const bool unknown=remote||pvr||folder||foreignCallback||foreignJob;
 const bool expectedSuccess=fixtureMode=="mark-watched"||fixtureMode=="mark-unwatched"||fixtureMode=="unchanged"||remote||pvr||foreignCallback||foreignJob||fixtureMode=="callback-failure";
 CVideoLibraryQueue callback;ForeignQueue foreign;
 auto item=std::make_shared<CFileItem>(remote?"upnp://fixture/movie":"/fixture/movie");
 item->m_bIsFolder=folder;item->pvr=pvr;item->tag.count=fixtureMode=="mark-unwatched"?2:fixtureMode=="unchanged"?1:0;
 CVideoLibraryMarkWatchedJob* job=foreignJob?new ForeignWatched(item,true):new CVideoLibraryMarkWatchedJob(item,fixtureMode!="mark-unwatched");
 CJobManager::TrackCheckpointJob(job,foreignCallback?&foreign:&callback,"queue_pending");
 auto record=CJobManager::CheckpointRecord(job);assert(record && record->unknown==unknown);
 assert(unknown || (record->owner=="native_databases" && record->receiptRequired));
 bool success=false;
 if(!folder){JobCheckpoint::WorkBinding binding(record);success=job->DoWork();assert(success==expectedSuccess);}
 if(unknown && !foreignCallback && !folder)assert(job->CheckpointSucceeded(success)==success);
 const bool callbackSucceeded=fixtureMode!="callback-failure";
 if(!unknown && expectedSuccess && callbackSucceeded){
  assert(job->CheckpointSucceeded(success));assert(record->outcomeReviewed);
  assert(record->durability==(fixtureMode=="unchanged"?CJobDurability::VerifiedUnchanged:CJobDurability::VerifiedCommitted));
 }
 CJobManager::TrackCheckpointPhase(job,"destructor",973);
 JobCheckpoint::Complete(record,callbackSucceeded&&job->CheckpointSucceeded(success),false,callbackSucceeded);
 delete job;record.reset();
 const auto snapshot=CJobManager::AndroidCheckpointSnapshot();
 const bool retired=!unknown && expectedSuccess && callbackSucceeded;
 assert(snapshot.required==(retired?0U:1U));assert(snapshot.unknown==(unknown?1U:0U));
 if(remote||pvr)assert(remoteCalls==1);
 if(folder)assert(remoteCalls==0); // metadata-refusal only, no folder Work simulated
 assert(!InfinityDatabaseBarrier::GetSnapshot().sealed); // fixture never issues a shutdown seal/receipt
 std::cout<<"HOST_PASS "<<fixtureMode<<"; SQLite "<<sqlite3_libversion()<<"; full Kodi database/Android not executed\n";
}
'''


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--cases', nargs='+', help='Run only named remaining cases; retain already-passing evidence separately')
    p.add_argument('--database-barrier', type=Path, help='Use the actual restored native header')
    p.add_argument('--full-native-map', type=Path, help='Bind retained job support to the restored native map')
    p.add_argument('--test-protected-resources', action='store_true', help='Exercise the current snapshot guard with a controlled resource provider')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if (a.out / 'RESULTS.json').exists():
        raise ValueError('Preserve passing evidence; no redundant run')
    candidate = module(HERE / 'stage_watched_repair.py', 'p0_watched_stage')
    reader = module(ROOT / 'repairs/android-checkpoint-shutdown/runtime-tests/test_job_checkpoint.py', 'p0_tracking_reader')
    source = a.out / 'source'
    bindings = {}
    for name in candidate.PINS:
        before = (a.inputs / name).read_bytes()
        assert candidate.transform(name, before) == (a.source / name).read_bytes()
        destination = source / name.removeprefix('xbmc/')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(a.source / name, destination)
        bindings['candidate/' + name] = sha(destination)
    for relative in ('video/jobs/VideoLibraryJob.h', 'video/jobs/VideoLibraryJob.cpp'):
        original = a.inputs / 'xbmc' / relative
        assert sha(original) == {'video/jobs/VideoLibraryJob.h': '40ae24d0709b6b9a3293ae4d7d6529fc77fb15a8439331c23dc29f54d7eaab49',
                                 'video/jobs/VideoLibraryJob.cpp': '67b802726fdbe8501d07069dd7c0daac2ae4df7c2579f7adf807fdc37914a7a2'}[relative]
        destination = source / relative
        shutil.copyfile(original, destination)
        bindings['retained/' + relative] = sha(original)
    manager_root = Path('/tmp/kodi451-p0-host/source/xbmc')
    baseline_report = json.loads(Path('/tmp/kodi451-p0-host/RESULTS.json').read_text())
    manager = manager_root / 'utils/JobManager.cpp'
    assert sha(manager) == baseline_report['source_sha256']['reconstructed_JobManager.cpp']
    native_map = json.loads(a.full_native_map.read_text()) if a.full_native_map else None
    if native_map:
        assert sha(manager) == native_map['xbmc/utils/JobManager.cpp']
    for relative in ('utils/Job.h', 'utils/JobManager.h', 'utils/JobCheckpoint.h', 'threads/Thread.h', 'threads/CriticalSection.h'):
        original = manager_root / relative
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
        bindings['retained/' + relative] = sha(original)
        if native_map and not relative.startswith('threads/'):
            assert sha(original) == native_map['xbmc/' + relative]
    barrier = ROOT / 'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc/dbwrappers/InfinityDatabaseBarrier.h'
    if a.database_barrier:
        barrier = a.database_barrier
        assert native_map and sha(barrier) == native_map['xbmc/dbwrappers/InfinityDatabaseBarrier.h']
    (source / 'dbwrappers').mkdir()
    shutil.copyfile(barrier, source / 'dbwrappers/InfinityDatabaseBarrier.h')
    bindings['actual_database_barrier' if a.database_barrier else str(barrier.relative_to(ROOT))] = sha(barrier)
    if a.test_protected_resources:
        assert a.database_barrier and 'protectedResourceBlockers' in barrier.read_text()
        peer = source / 'platform/android/activity/InfinityProtectedWrites.h'
        peer.parent.mkdir(parents=True, exist_ok=True)
        peer.write_text('#pragma once\n#include <cstddef>\ninline std::size_t fixtureProtectedResources=0;\n'
                        'namespace InfinityScriptPersistence {inline std::size_t ActiveProtectedResources(){return fixtureProtectedResources;}}\n')
    (source / 'test_peers.h').write_text(PEERS)
    wrappers = ['FileItem.h', 'ServiceBroker.h', 'Util.h', 'filesystem/Directory.h',
                'profiles/ProfileManager.h', 'pvr/PVRManager.h', 'pvr/recordings/PVRRecordings.h',
                'settings/SettingsComponent.h', 'utils/URIUtils.h', 'video/VideoDatabase.h',
                'video/VideoLibraryQueue.h', 'network/upnp/UPnP.h']
    for name in wrappers:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('#pragma once\n#include "test_peers.h"\n')
    methods = '\n'.join(reader.function(manager.read_text(), sig) for sig in (
        'void CJobManager::TrackCheckpointJob(', 'void CJobManager::TrackCheckpointPhase(',
        'bool CJobManager::IsRequiredCheckpointJob(', 'JobCheckpoint::Snapshot CJobManager::AndroidCheckpointSnapshot()'))
    unit = a.out / 'test.cpp'
    unit.write_text(MAIN.replace('TRACKING_BODIES', methods))
    library = ctypes.util.find_library('sqlite3')
    if library != 'libsqlite3.so.0':
        raise RuntimeError('Expected existing host SQLite library unavailable; no dependency installation attempted')
    executable = a.out / 'watched'
    command = ['g++', '-std=c++17', '-DTARGET_ANDROID', '-DHAS_UPNP', '-DINFINITY_DATABASE_BARRIER_TEST',
               '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-pthread', '-I', str(source),
               str(source / 'video/jobs/VideoLibraryMarkWatchedJob.cpp'),
               str(source / 'video/jobs/VideoLibraryJob.cpp'), str(unit), '-l:' + library, '-o', str(executable)]
    if a.test_protected_resources:
        command.insert(1, '-DP0_PROTECTED_RESOURCE_PEER')
    built = subprocess.run(command, capture_output=True, text=True)
    (a.out / 'COMPILE.txt').write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError('Compile failed; inspect ' + str(a.out / 'COMPILE.txt'))
    cases = ['mark-watched', 'mark-unwatched', 'unchanged', 'begin-failure', 'commit-failure',
             'resume-read-error', 'count-read-error', 'close-failure', 'unknown-upnp',
             'unknown-folder', 'unknown-callback', 'unknown-job', 'callback-failure', 'unknown-pvr']
    if a.test_protected_resources:
        cases.append('protected-resource-refusal')
    if a.cases:
        assert len(set(a.cases)) == len(a.cases) and set(a.cases).issubset(cases)
        cases = a.cases
    results = []
    for case in cases:
        database = a.out / (case + '.sqlite')
        if database.exists():
            raise ValueError('Refusing to overwrite previous test data: ' + str(database))
        path = 'upnp://fixture/movie' if case == 'unknown-upnp' else '/fixture/movie'
        initial = 2 if case == 'mark-unwatched' else 1 if case == 'unchanged' else 0
        with sqlite3.connect(database) as connection:
            connection.executescript('CREATE TABLE media(path TEXT PRIMARY KEY,playCount INTEGER);CREATE TABLE bookmark(path TEXT,position REAL);')
            connection.execute('INSERT INTO media VALUES(?,?)', (path, initial))
            connection.execute('INSERT INTO bookmark VALUES(?,42)', (path,))
        run = subprocess.run([str(executable), case, str(database)], capture_output=True, text=True, timeout=10)
        if run.returncode:
            (a.out / 'FAILED-CASE.json').write_text(json.dumps({'case': case, 'output': run.stdout + run.stderr, 'exit': run.returncode}, indent=2) + '\n')
            raise RuntimeError('Host watched case failed: ' + case)
        with sqlite3.connect(database) as reopened:
            count = reopened.execute('SELECT playCount FROM media WHERE path=?', (path,)).fetchone()[0]
            bookmarks = reopened.execute('SELECT COUNT(*) FROM bookmark').fetchone()[0]
        untouched = case in ('unchanged', 'begin-failure', 'commit-failure', 'unknown-upnp', 'unknown-folder', 'protected-resource-refusal')
        expected_count = initial if untouched else 0 if case == 'mark-unwatched' else initial + 1
        assert (count, bookmarks) == (expected_count, 1 if untouched or case == 'unknown-pvr' else 0), (case, count, bookmarks)
        results.append({'case': case, 'status': 'HOST_PASS', 'output': run.stdout,
                        'reopened_playcount': count, 'reopened_resume_rows': bookmarks,
                        'full_shutdown_saved_asserted': False})
        print(run.stdout, end='')
    report = {'purpose': 'bounded local watched receipt host verification', 'compiler': command,
              'cases': results, 'source_sha256': bindings,
              'actual_watched_work_and_receipt_code_compiled': True,
              'actual_job_tracking_and_database_observation_code': True,
              'real_file_sqlite_commit_and_reopen': True,
              'full_kodi_database_implementation': False, 'actual_queue_callback_executed': False,
              'final_native_database_checkpoint_fence_executed': False,
              'reported_historical_item_route_confirmed': False,
              'actual_native_support_map_checked': native_map is not None,
              'independent_protected_resource_provider_stubbed': a.test_protected_resources,
              'android_execution': False, 'physical_fold_acceptance': False, 'apk_built_or_signed': False}
    (a.out / 'RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
