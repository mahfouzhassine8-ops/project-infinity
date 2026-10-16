#!/usr/bin/env python3
"""Actual repository continuations and admission guard, with real SQLite/VFS.

Kodi UI/network peers and the coordinator state container are explicit adapters.
The callback, network/local scope boundaries, guard and write gates are production
source. This is not Android process or physical Fold acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

import apply_runtime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES = ['normal-work', 'normal-callback', 'quiesce-work', 'quiesce-callback',
         'persisting-callback', 'sealed-callback', 'late-schedule', 'network-close',
         'close-after-admission', 'real-read-failure', 'real-write-failure']
CODE = r'''
#define INFINITY_DATABASE_BARRIER_TEST
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include "dbwrappers/InfinitySQLiteVFS.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include <atomic>
#include <cassert>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <iterator>
#include <memory>
using namespace std::chrono_literals;
namespace fs = std::filesystem;
std::string mode, root;
int errors=0, opens=0, writes=0, fetches=0, finished=0, scheduled=0, published=0;
namespace InfinityAndroidCheckpoint {
struct Owner {unsigned generation=0;bool dirty=false,complete=false;};
struct State {std::mutex mutex;std::atomic<bool> active{false};bool sealed=false;
 std::string phase="RUNNING";unsigned activeWrites=0;std::map<std::string,Owner> owners;};
inline State& Get(){static State s;return s;}
thread_local unsigned acceptedPlaybackDepth=0,permissionDepth=0;
void RecordPersistenceFailure(const char*,const char*){++errors;}
bool IsPersistingOnThisThread(){return false;}
// @GUARD@
}
void activate(bool persist=false,bool seal=false) {
 auto& state=InfinityAndroidCheckpoint::Get();state.active=true;
 state.sealed=persist||seal;state.phase=seal?"SAFE_TO_TERMINATE":persist?"PERSISTING":"QUIESCE";
 assert(InfinityScriptPersistence::BeginWriteProtection(1,{root},{}));
 if(persist||seal) {
  assert(InfinityScriptPersistence::CloseParticipantWrites(1));
  assert(InfinityDatabaseBarrier::Begin(1));
 }
 if(seal) {
  assert(InfinityDatabaseBarrier::Seal(1));
  assert(InfinityScriptPersistence::SealEssentialWrites(1));
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(1));
 }
}
void failure(const char* why) {
 InfinityDatabaseBarrier::RecordFailure(why);
 InfinityAndroidCheckpoint::RecordPersistenceFailure("native_databases",why);
}
struct RepositoryDates;
class CAddonDatabase {
 sqlite3* db=nullptr;
public:
 using RepoUpdateData=RepositoryDates;
 bool Open();
 void read();
 ~CAddonDatabase(){if(db)sqlite3_close(db);}
 void SetRepoUpdateData(const std::string&,const struct RepositoryDates&);
 struct RepositoryDates GetRepoUpdateData(const std::string&);
 int GetRepoChecksum(const std::string&,std::string&){read();return 0;}
 template<class... T>void UpdateRepositoryContent(T...){read();}
};
bool CAddonDatabase::Open() {
 ++opens;
 const auto path=root+(mode=="real-read-failure"?"/missing/database.db":"/addons.db");
 const int rc=sqlite3_open_v2(path.c_str(),&db,SQLITE_OPEN_READWRITE,nullptr);
 if(rc!=SQLITE_OK){failure("sqlite.connect");return false;}return true;
}
void CAddonDatabase::read(){
 if(!db||sqlite3_exec(db,"SELECT value FROM metadata",nullptr,nullptr,nullptr)!=SQLITE_OK)
  failure("sqlite.query");
}
struct CDateTimeSpan {CDateTimeSpan(int,int,int,int){};int GetSecondsTotal()const{return 3600;}};
struct CDateTime {
 static CDateTime GetCurrentDateTime(){return {};}
 bool IsValid()const{return false;}
 std::string GetAsLocalizedDateTime()const{return {};}
 bool operator<(const CDateTime&)const{return false;}
 CDateTimeSpan operator-(const CDateTime&)const{return {0,0,0,0};}
 CDateTime operator+(const CDateTimeSpan&)const{return {};}
};
struct RepositoryDates {
 CDateTime lastCheckedAt,nextCheckAt;int lastCheckedVersion=1;
 RepositoryDates()=default;
 RepositoryDates(CDateTime,int,CDateTime){}
};
RepositoryDates CAddonDatabase::GetRepoUpdateData(const std::string&){read();return {};}
void CAddonDatabase::SetRepoUpdateData(const std::string&,const RepositoryDates&) {
 ++writes;
 if(mode=="real-write-failure") {
  assert(InfinityAndroidCheckpoint::Get().activeWrites>0);activate();
 }
 if(sqlite3_exec(db,mode=="real-write-failure"?"INSERT INTO metadata VALUES(-1)":"INSERT INTO metadata VALUES(2)",nullptr,nullptr,nullptr)!=SQLITE_OK)
  failure("sqlite.write");
}
enum {LOGDEBUG,LOGERROR,AUTO_UPDATES_NEVER,AUTO_UPDATES_NOTIFY,AUTO_UPDATES_ON,TOAST_DISPLAY_TIME};
struct CLog {template<class... T>static void Log(T...) {}};
using CCriticalSection=std::recursive_mutex;
struct CJob {virtual ~CJob()=default;virtual bool DoWork(){return false;}};
struct CProgressJob:CJob {void MarkFinished(){++finished;}};
struct Addon {
 std::string ID()const{return "repository.test";}int Version()const{return 1;}
 std::string Icon()const{return {};};std::string Name()const{return {};}
 std::vector<std::string> Screenshots()const{return {};}
 std::map<std::string,std::string> Art()const{return {};}
};
using AddonPtr=std::shared_ptr<Addon>;using AddonInfoPtr=AddonPtr;using VECADDONS=std::vector<AddonPtr>;
enum class AddonType {REPOSITORY};
struct CRepository:Addon {
 enum {STATUS_ERROR,STATUS_NOT_MODIFIED,STATUS_OK};
 int FetchIfChanged(const std::string&,std::string&,std::vector<AddonInfoPtr>&,int& delay) {
  ++fetches;delay=3600;
  assert(InfinityAndroidCheckpoint::Get().activeWrites==0); // Never lease network waiting.
  if(mode=="network-close")activate();
  return STATUS_NOT_MODIFIED;
 }
};
using RepositoryPtr=std::shared_ptr<CRepository>;
struct CAddonMgr {
 VECADDONS GetAvailableUpdates() {
  if(mode=="close-after-admission"||mode=="real-read-failure") {
   assert(InfinityAndroidCheckpoint::Get().activeWrites>0);activate();
  }
  CAddonDatabase db;db.Open();db.read();return {};
 }
 template<class... T>bool FindInstallableById(T...){return false;}
 void CheckAndInstallAddonUpdates(bool){}
 bool HasAddons(AddonType)const{return true;}
 bool GetAddons(VECADDONS& addons,AddonType)const{addons.push_back(std::make_shared<Addon>());return true;}
};
struct CAddonSystemSettings {
 static CAddonSystemSettings& GetInstance(){static CAddonSystemSettings s;return s;}
 int GetAddonAutoUpdateMode()const{return AUTO_UPDATES_NOTIFY;}
};
struct CGUIDialogKaiToast {template<class... T>static void QueueNotification(T...) {}};
struct CAddonManagementEvent {template<class... T>explicit CAddonManagementEvent(T...) {}};
using EventPtr=std::shared_ptr<CAddonManagementEvent>;
struct EventLog {void Add(const EventPtr&) {}};
struct CServiceBroker {
 static CAddonMgr& GetAddonMgr(){static CAddonMgr m;return m;}
 static EventLog* GetEventLog(){static EventLog e;return &e;}
};
struct CTextureDatabase {void Open(){};void BeginMultipleExecute(){};void CommitMultipleExecute(){};void InvalidateCachedTexture(const std::string&){};};
struct Localize {std::string Get(int)const{return {};}} g_localizeStrings;
// @JOB_CLASS@
struct Timer {void Stop(bool){assert(InfinityAndroidCheckpoint::Get().activeWrites==0);}
 template<class T>bool Start(T){++scheduled;return true;}};
struct Event {bool set=false;void Set(){set=true;}};
struct RepositoryUpdated {};
struct Events {void Publish(RepositoryUpdated){++published;}};
class CRepositoryUpdater {
public:
 enum class UpdateScheduleType {First,Regular};
 CCriticalSection m_criticalSection;std::vector<CRepositoryUpdateJob*> m_jobs;
 Event m_doneEvent;CAddonMgr m_addonMgr;Timer m_timer;Events m_events;
 void OnJobComplete(unsigned int,bool,CJob*);
 void ScheduleUpdate(UpdateScheduleType);
 CDateTime ClosestNextCheck()const;
};
// @METHODS@
int main(int argc,char** argv) {
 assert(argc==3);mode=argv[1];root=argv[2];fs::create_directories(root);
 assert(InfinitySQLiteVFS::Install());
 sqlite3* db=nullptr;assert(sqlite3_open((root+"/addons.db").c_str(),&db)==SQLITE_OK);
 assert(sqlite3_exec(db,"CREATE TABLE metadata(value INTEGER CHECK(value>0));INSERT INTO metadata VALUES(1)",nullptr,nullptr,nullptr)==SQLITE_OK);
 assert(sqlite3_close(db)==SQLITE_OK);
 CRepositoryUpdateJob job(std::make_shared<CRepository>());CRepositoryUpdater updater;updater.m_jobs.push_back(&job);
 if(mode=="quiesce-work"||mode=="quiesce-callback")activate();
 if(mode=="persisting-callback")activate(true);
 if(mode=="sealed-callback"||mode=="late-schedule"||mode=="baseline-after-seal")activate(true,true);
 bool result=false;
 if(mode=="late-schedule")updater.ScheduleUpdate(CRepositoryUpdater::UpdateScheduleType::Regular);
 else if(mode.find("callback")!=std::string::npos||mode=="baseline-after-seal"||mode=="close-after-admission"||mode=="real-read-failure") {
  updater.OnJobComplete(1,true,&job);
  assert(updater.m_jobs.empty()&&updater.m_doneEvent.set); // Cleanup is never skipped.
 } else result=job.DoWork();
 assert(InfinityAndroidCheckpoint::Get().activeWrites==0);
 if(mode=="baseline-after-seal")assert(errors>0); // Exact old callback reproduces the real refusal.
 else if(mode=="real-read-failure"||mode=="real-write-failure")assert(errors>0);
 else {
  assert(errors==0);
  if(mode=="normal-work")assert(result&&opens==1&&writes==1&&fetches==1);
  else if(mode=="normal-callback")assert(opens==2&&scheduled==1&&published==1);
  else if(mode=="network-close")assert(!result&&opens==1&&writes==0&&fetches==1&&finished==1);
  else if(mode=="close-after-admission")assert(opens==1&&scheduled==0);
  else {assert(opens==0&&writes==0&&fetches==0&&scheduled==0);if(mode=="quiesce-work")assert(!result&&finished==1);}
  if(!InfinityAndroidCheckpoint::Get().active)activate();
  if(InfinityScriptPersistence::EssentialWrites().phase==1) {
   assert(InfinityScriptPersistence::CloseParticipantWrites(1));
   assert(InfinityDatabaseBarrier::Begin(1));
  }
  if(!InfinityDatabaseBarrier::GetSnapshot().sealed) {
   assert(InfinityDatabaseBarrier::Seal(1));
   assert(InfinityScriptPersistence::SealEssentialWrites(1));
  }
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(1));
 }
 sqlite3* saved=nullptr;assert(sqlite3_open_v2((root+"/addons.db").c_str(),&saved,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
 sqlite3_stmt* rows=nullptr;assert(sqlite3_prepare_v2(saved,"SELECT count(*),sum(value) FROM metadata",-1,&rows,nullptr)==SQLITE_OK);
 assert(sqlite3_step(rows)==SQLITE_ROW);
 assert(sqlite3_column_int(rows,0)==(mode=="normal-work"?2:1));
 assert(sqlite3_column_int(rows,1)==(mode=="normal-work"?3:1));
 sqlite3_finalize(rows);assert(sqlite3_close(saved)==SQLITE_OK);
 std::cout<<"PASS "<<mode<<" opens="<<opens<<" writes="<<writes<<" fetches="<<fetches<<" failures="<<errors<<'\n';
}
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--baseline', type=Path)
    p.add_argument('--sqlite-include', type=Path, default=Path('/usr/include'))
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    spec = importlib.util.spec_from_file_location('repository_extractor', ROOT/'repairs/android-checkpoint-shutdown/integration-2103367/test_installer_work.py')
    extract = importlib.util.module_from_spec(spec);spec.loader.exec_module(extract)
    source = (args.runtime/apply_runtime.REPOSITORY).read_text()
    baseline = args.baseline.read_text() if args.baseline else subprocess.run(
        ['git','-C',str(args.runtime),'show','HEAD:'+apply_runtime.REPOSITORY],check=True,capture_output=True,text=True).stdout
    assert hashlib.sha256(baseline.encode()).hexdigest()==apply_runtime.PINS[apply_runtime.REPOSITORY]
    assert source==apply_runtime.repository(baseline),'Not the complete verified repository-only delta'
    checkpoint = (args.runtime/apply_runtime.CHECKPOINT).read_text()
    guard = '\n'.join(extract.function(checkpoint,name) for name in (
        'CheckpointWriteGuard::CheckpointWriteGuard(', 'CheckpointWriteGuard::~CheckpointWriteGuard()'))
    results=[]
    with tempfile.TemporaryDirectory(prefix='repository-native-') as temp:
        temp=Path(temp)
        for negative,text in [(False,source),(True,baseline)]:
            methods='\n'.join(extract.function(text,name) for name in (
                'bool CRepositoryUpdateJob::DoWork()', 'void CRepositoryUpdater::OnJobComplete(',
                'void CRepositoryUpdater::ScheduleUpdate(', 'CDateTime CRepositoryUpdater::ClosestNextCheck()'))
            job=text[text.index('class CRepositoryUpdateJob :'):text.index('bool CRepositoryUpdateJob::DoWork()')]
            code=CODE.replace('// @GUARD@',guard).replace('// @JOB_CLASS@',job).replace('// @METHODS@',methods)
            cpp=temp/'test.cpp';cpp.write_text(code);binary=temp/'test'
            subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-pthread',
                '-I'+str(HERE/'runtime/xbmc'),'-I'+str(ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'),
                '-I'+str(args.sqlite_include),
                str(cpp),'-l:libsqlite3.so.0','-o',str(binary)],check=True)
            for case in (['baseline-after-seal'] if negative else CASES):
                result=subprocess.run([str(binary),case,str(temp/case)],capture_output=True,text=True,timeout=10)
                results.append(dict(case=case,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
                print(case,result.returncode,result.stderr,flush=True)
    report=dict(scope='Actual repository methods, production native admission and real SQLite VFS; Kodi network/UI and coordinator state container are peers',
                results=results,all_passed=all(r['exit_code']==0 for r in results),android_process_death_verified=False,apk_deliverable=False)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    assert report['all_passed']


if __name__=='__main__':main()
