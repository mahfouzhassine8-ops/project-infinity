"""Execute production DoWork, dependencies, download, install and filesystem paths.

Only external Kodi peers are replaced. The installer bodies are extracted from
the actual compiled overlay; their operation scope uses real files and SQLite.
Full Android compilation and Fold testing remain separate acceptance gates.
"""
from pathlib import Path
import argparse
import ctypes.util
import subprocess
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).parents[1] / 'runtime-tests'))
from test_job_checkpoint import function

PEERS = r'''
#include "addons/InfinityAddonFileReceipt.h"
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include "utils/JobCheckpoint.h"
#if __has_include(<sqlite3.h>)
#include <sqlite3.h>
#else
// Stable C ABI declarations only; all operations execute the host SQLite library.
extern "C" {
struct sqlite3;
int sqlite3_open(const char*, sqlite3**);
int sqlite3_close(sqlite3*);
int sqlite3_exec(sqlite3*, const char*, int (*)(void*, int, char**, char**), void*, char**);
}
constexpr int SQLITE_OK=0;
#endif
#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>
#include <set>
#include <mutex>
namespace fs=std::filesystem;
static fs::path root;
static std::string mode;
static unsigned errors=0;
struct CLog {template<class...T>static void Log(int,const char*,T&&...) {}};
constexpr int LOGERROR=1,LOGDEBUG=2,DIR_FLAG_DEFAULTS=0,DIR_FLAG_NO_FILE_DIRS=1;
struct CAddonVersion {
 int value=1; std::string asString()const{return "1";}
 bool operator>(const CAddonVersion& b)const{return value>b.value;}
 bool operator<(const CAddonVersion& b)const{return value<b.value;}
 bool operator==(const CAddonVersion& b)const{return value==b.value;}
 static void SplitFileName(std::string& addon,std::string& version,const std::string& name){
  auto separator=name.find_last_of('-');addon=name.substr(0,separator);version=name.substr(separator+1);
 }
};
enum class OnlyEnabled {CHOICE_YES,CHOICE_NO};
enum class AddonType {REPOSITORY};
enum class AddonLifecycleState {NORMAL,BROKEN,DEPRECATED};
enum class AddonDisabledReason {USER};
enum class AddonUpdateRule {PIN_OLD_VERSION,PIN_ZIP_INSTALL};
enum class DependencyJob {CHOICE_YES,CHOICE_NO};
enum class AllowCheckForUpdates {CHOICE_YES,CHOICE_NO};
enum class AutoUpdateJob {CHOICE_YES,CHOICE_NO};
const std::string ORIGIN_SYSTEM="system";
struct DependencyInfo {std::string id;CAddonVersion versionMin,version;bool optional=false;};
struct IAddon {
 virtual ~IAddon()=default;
 std::string id="addon-a",path="https://repo.invalid/addon-a.zip",origin="";
 std::vector<DependencyInfo> dependencies;
 const std::string& ID()const{return id;} std::string Name()const{return id;}
 const std::string& Path()const{return path;}const std::string& Origin()const{return origin;}
 CAddonVersion Version()const{return {};}
 bool HasMainType(AddonType)const{return false;}bool HasType(AddonType)const{return false;}
 const auto& GetDependencies()const{return dependencies;}
 bool MeetsVersion(const CAddonVersion&,const CAddonVersion&)const{return true;}
 AddonLifecycleState LifecycleState()const{return AddonLifecycleState::NORMAL;}
 std::string LifecycleStateDescription()const{return "";}
};
struct TypedDigest {int type=1;std::string value;bool Empty()const{return value.empty();}
 bool operator!=(const TypedDigest& b)const{return type!=b.type||value!=b.value;}};
struct CRepository: IAddon {
 struct ResolveResult {std::string location;TypedDigest digest;};
 ResolveResult ResolvePathAndHash(const std::shared_ptr<IAddon>& addon)const{
  return {mode=="resolve"?"":addon->Path(),{1,"expected"}};
 }
};
namespace ADDON {
using AddonPtr=std::shared_ptr<IAddon>;using RepositoryPtr=std::shared_ptr<CRepository>;
inline void OnPreInstall(const AddonPtr&){}inline void OnPostInstall(const AddonPtr&,bool,bool){}
}
using namespace ADDON;
class CAddonDatabase {
 sqlite3* db=nullptr;
public:
 ~CAddonDatabase(){Close();}
 bool Open(){
  if(mode=="database-open")return false;
  return sqlite3_open((root/"addon.db").c_str(),&db)==SQLITE_OK &&
    sqlite3_exec(db,"PRAGMA synchronous=FULL;CREATE TABLE IF NOT EXISTS packages(path TEXT)",nullptr,nullptr,nullptr)==SQLITE_OK;
 }
 void Close(){if(db){assert(sqlite3_close(db)==SQLITE_OK);db=nullptr;}InfinityDatabaseBarrier::ForgetOwner(this);}
 bool Write(const std::string& sql){
  InfinityDatabaseBarrier::Operation operation(this);if(!operation.AllowWrite())return false;
  const int result=sqlite3_exec(db,sql.c_str(),nullptr,nullptr,nullptr);
  if(result!=SQLITE_OK){InfinityDatabaseBarrier::RecordFailure("SQLite fixture write");return false;}
  return InfinityAddonFileReceipt::Existing((root/"addon.db").string(),false);
 }
 bool AddPackage(const std::string&,const std::string&,const std::string&){return Write(mode=="database-write"?"INVALID SQL":"INSERT INTO packages VALUES('addon-a')");}
 bool RemovePackage(const std::string&){return Write(mode=="package-prune-db"?"INVALID SQL":"DELETE FROM packages");}
 bool GetPackageHash(const std::string&,const std::string&,std::string&){return false;}
};
bool WriteManagerState(){CAddonDatabase db;if(!db.Open())return false;return db.Write(mode=="origin-write"?"INVALID SQL":"INSERT INTO packages VALUES('manager')");}
struct CURL {std::string path;explicit CURL(const std::string& p):path(p){}std::string Get()const{return path;}};
struct CFileItem {std::string path;bool m_bIsFolder=false;int64_t m_dwSize=3;
 CFileItem(const std::string& p,bool folder):path(p),m_bIsFolder(folder){}
 std::string GetPath()const{return path;}void Select(bool){}
 std::string GetLabel()const{return fs::path(path).filename().string();}
};
struct CFileItemList {
 std::vector<std::shared_ptr<CFileItem>> rows;
 void Add(std::shared_ptr<CFileItem> row){rows.push_back(row);}int Size()const{return rows.size();}
 auto operator[](int i)const{return rows.at(i);}auto Get(int i)const{return rows.at(i);}
 void Sort(int by,int order){std::sort(rows.begin(),rows.end(),[&](const auto&a,const auto&b){
  const bool less=by==1?a->GetLabel()<b->GetLabel():a->m_dwSize<b->m_dwSize;
  return order==2?less:(by==1?a->GetLabel()>b->GetLabel():a->m_dwSize>b->m_dwSize);
 });}void Clear(){rows.clear();}
};
constexpr int SortByLabel=1,SortBySize=2,SortByDate=3,SortOrderDescending=1,SortOrderAscending=2;
struct CSpecialProtocol {
 static std::string TranslatePath(std::string path){const std::string prefix="special://home/";
  if(path.rfind(prefix,0)==0)return (root/path.substr(prefix.size())).string();
  return path;}
};
struct CFile {
 static bool Exists(const std::string& p){return fs::exists(CSpecialProtocol::TranslatePath(p));}
 static bool Delete(const std::string& p){if(mode=="download-cleanup"||mode=="package-prune-file")return false;return fs::remove(CSpecialProtocol::TranslatePath(p));}
 static bool Rename(const std::string&a,const std::string&b){
  static int moves=0;++moves;
  if(mode=="move"&&moves==2)return false;
  return ::rename(a.c_str(),b.c_str())==0;
 }
};
struct CDirectory {
 static bool Create(const std::string& p){return fs::create_directory(p);}
 static bool Exists(const std::string& p){return fs::is_directory(p);}
 static bool RemoveRecursive(const std::string& p){return mode=="backup-cleanup"?false:fs::remove_all(p)>0;}
 static bool GetDirectory(const CURL&,CFileItemList& list,const char*,int){
  if(mode=="archive")return false;
  list.Add(std::make_shared<CFileItem>((root/"source").string(),true));return true;
 }
 static bool GetDirectory(const char*,CFileItemList& list,const char*,int){
  for(const auto& path:fs::directory_iterator(root/"addons/packages")){
   auto item=std::make_shared<CFileItem>(path.path().string(),path.is_directory());
   item->m_dwSize=path.is_regular_file()?path.file_size():0;list.Add(item);
  }
  return true;
 }
};
struct URIUtils {
 static std::string AddFileToFolder(const std::string&a,const std::string&b){return (fs::path(a)/b).string();}
 static bool HasSlashAtEnd(const std::string& p){return !p.empty()&&p.back()=='/';}
 static void Split(const std::string&p,std::string&a,std::string&b){auto i=p.find_last_of('/');a=p.substr(0,i+1);b=p.substr(i+1);}
 static std::string ChangeBasePath(const std::string&,const std::string&b,const std::string&dest){return dest+b;}
 static std::string GetFileName(const std::string&p){return fs::path(p).filename().string();}
 static CURL CreateArchivePath(const char*,const CURL&p,const char*){return p;}
};
struct StringUtils {
 template<class...T>static std::string Format(const std::string&s,T&&...){return s;}
 static std::string CreateUUID(){static thread_local int n=0;return "stage-"+std::to_string(++n);}
};
struct Localize {std::string Get(int){return "message";}template<class...T>void LoadAddonStrings(T&&...){}}g_localizeStrings;
struct CSettings {
 static constexpr const char* SETTING_LOCALE_LANGUAGE="language",*SETTING_ADDONS_NOTIFICATIONS="notify";
 std::string GetString(const char*){return "en";}bool GetBool(const char*){return false;}
};
struct AdvancedSettings {int m_addonPackageFolderSize=1;};
struct SettingsComponent {auto GetSettings(){static CSettings s;return &s;}auto GetAdvancedSettings(){static AdvancedSettings s;return &s;}};
struct AddonMgr {
 bool LoadAddonDescription(const std::string&,AddonPtr& result){result=std::make_shared<IAddon>();return true;}
 bool UnloadAddon(const std::string&){return mode!="unload";}
 bool LoadAddon(const std::string&,const std::string&,const CAddonVersion&){return mode!="reload";}
 bool GetAddon(const std::string&id,AddonPtr& result,OnlyEnabled){if(id=="missing")return false;result=std::make_shared<IAddon>();result->id=id;return true;}
 bool FindInstallableById(const std::string&,AddonPtr&){return false;}
 bool IsAddonDisabled(const std::string&id){return id=="disabled";}
 bool EnableAddon(const std::string&){return WriteManagerState();}
 bool SetAddonOrigin(const std::string&,const std::string&,bool){return WriteManagerState();}
 auto GetCompatibleVersions(const std::string&){return std::vector<AddonPtr>{};}
 bool RemoveUpdateRuleFromList(const std::string&,AddonUpdateRule){return WriteManagerState();}
 bool AddUpdateRuleToList(const std::string&,AddonUpdateRule){return WriteManagerState();}
 void DisableAddon(const std::string&,AddonDisabledReason){}
 bool IsSystemAddon(const std::string&){return false;}bool IsAddonInstalled(const std::string&){return true;}
};
struct RepositoryUpdater {void CheckForUpdates(std::shared_ptr<CRepository>,bool){}};
struct CAddonManagementEvent {template<class...T>explicit CAddonManagementEvent(T&&...){}};
using EventPtr=std::shared_ptr<CAddonManagementEvent>;
struct EventLog {template<class...T>void Add(T&&...){}};
constexpr int GUI_MSG_NOTIFY_ALL=1,GUI_MSG_UPDATE=2;
struct CGUIMessage {CGUIMessage(int,int,int,int){}};
struct GUIManager {void SendThreadMessage(CGUIMessage&){if(mode=="callback")throw std::runtime_error("callback fixture failure");}};
struct GUI {auto& GetWindowManager(){static GUIManager manager;return manager;}};
struct CServiceBroker {
 static auto& GetAddonMgr(){static AddonMgr m;return m;}static auto GetSettingsComponent(){static SettingsComponent s;return &s;}
 static auto& GetRepositoryUpdater(){static RepositoryUpdater u;return u;}static EventLog* GetEventLog(){return nullptr;}
 static auto* GetGUI(){static GUI gui;return &gui;}
};
struct CUtil {static std::string GetFileDigest(const std::string&,int){return mode=="hash"?"different":"expected";}};
class CFilesystemInstaller {
public:
 std::string m_addonFolder=(root/"addons").string(),m_tempFolder=(root/"addons/temp").string();
 bool InstallToFilesystem(const std::string&,const std::string&);bool UnInstallFromFilesystem(const std::string&);
 bool UnpackArchive(const std::string&,const std::string& dest){
  fs::copy(root/"source",dest,fs::copy_options::recursive|fs::copy_options::overwrite_existing);return mode!="unpack";
 }
};
struct CAddonRepos {bool IsValid(){return true;}bool FindDependency(const std::string&,const std::string&,AddonPtr&,RepositoryPtr&){return false;}};
namespace KODI {namespace TIME {inline void Sleep(std::chrono::milliseconds){}}}
using namespace std::chrono_literals;
struct CFileOperationJob {enum FileAction {ActionReplace};};
struct CJob {virtual ~CJob()=default;};
class CAddonInstallJob : public CJob {
public:
 AddonPtr m_addon;RepositoryPtr m_repo;bool m_isUpdate=false,m_workStarted=false,m_completionVerified=false;
 uint64_t m_databaseFailures=0;std::thread::id m_worker;
 AutoUpdateJob m_isAutoUpdate=AutoUpdateJob::CHOICE_NO;DependencyJob m_dependsInstall=DependencyJob::CHOICE_NO;
 AllowCheckForUpdates m_allowCheckForUpdates=AllowCheckForUpdates::CHOICE_NO;
 static constexpr const char* TYPE_DOWNLOAD="DOWNLOAD",*TYPE_INSTALL="INSTALL";const char* m_currentType=TYPE_DOWNLOAD;
 CAddonInstallJob(AddonPtr a,RepositoryPtr r,AutoUpdateJob):m_addon(a),m_repo(r){}
 bool DoWork();bool Install(const std::string&,const RepositoryPtr&);bool DownloadPackage(const std::string&,const std::string&);
 void SetTitle(const std::string&){}void SetProgress(unsigned){}void SetText(const std::string&){}void MarkFinished(){}
 bool IsModal(){return false;}bool DoModal(){return DoWork();}void SetDependsInstall(DependencyJob d){m_dependsInstall=d;}
 int GetProgressBar(){return 0;}int GetProgressDialog(){return 0;}void SetProgressIndicators(int,int,bool,bool){}
 bool ShouldCancel(unsigned,unsigned){return mode=="cancel";}
 void ReportInstallError(const std::string&,const std::string&,const std::string& message = "");
 bool DoFileOperation(CFileOperationJob::FileAction,CFileItemList&,const std::string& dest,bool){
  auto path=fs::path(CSpecialProtocol::TranslatePath(dest))/"addon-a.zip";
  std::ofstream(path)<<"downloaded archive";return mode!="download"&&mode!="download-cleanup";
 }
};
class CAddonInstaller {
public:
 using CCriticalSection=std::mutex;
 struct CDownloadJob {unsigned jobID=0;};using JobMap=std::map<std::string,CDownloadJob>;
 CCriticalSection m_critSection;JobMap m_downloadJobs;
 struct Idle {void Set(){}}m_idle;
 static auto& GetInstance(){static CAddonInstaller i;return i;}
 bool CheckDependencies(const AddonPtr&,std::pair<std::string,std::string>&,CAddonDatabase* = nullptr);
 bool CheckDependencies(const AddonPtr&,std::vector<std::string>&,CAddonDatabase&,std::pair<std::string,std::string>&);
 bool HasJob(const std::string&){return false;}
 bool InstallOrUpdateDependency(AddonPtr addon,RepositoryPtr repo){CAddonInstallJob job(addon,repo,AutoUpdateJob::CHOICE_NO);return job.DoWork();}
 void OnJobComplete(unsigned,bool,CJob*);void PrunePackageCache();
 int64_t EnumeratePackageFolder(std::map<std::string,std::unique_ptr<CFileItemList>>&);
};
void CAddonInstallJob::ReportInstallError(const std::string&,const std::string&,const std::string&){++errors;}
// @PRODUCTION@
int main(int argc,char**argv){
 assert(argc==3);mode=argv[1];root=argv[2];
 fs::create_directories(root/"addons/temp");fs::create_directories(root/"addons/packages");
 fs::create_directories(root/"addons/addon-a");fs::create_directories(root/"source");
 std::ofstream(root/"source/addon.xml")<<"new addon";std::ofstream(root/"addons/addon-a/addon.xml")<<"original addon";
 if(mode.rfind("package-prune",0)==0)
  for(unsigned version=1;version<=3;++version)
   std::ofstream(root/"addons/packages"/("addon-a-"+std::to_string(version)+".zip"))<<std::string(1024*1024,'x');
 auto addon=std::make_shared<IAddon>();auto repo=std::make_shared<CRepository>();
 if(mode=="dependency")addon->dependencies.push_back({"missing",{},{},false});
 if(mode=="dependency-committed"){addon->dependencies.push_back({"disabled",{},{},false});addon->dependencies.push_back({"missing",{},{},false});}
 CAddonInstallJob job(addon,repo,AutoUpdateJob::CHOICE_NO);
 auto record=JobCheckpoint::Admit(true,false,"native_databases","addon_install","CAddonInstallJob","queued",true,addon->ID());
 bool result;
 {JobCheckpoint::WorkBinding binding(record);result=job.DoWork();}
 assert(JobCheckpoint::GetSnapshot().required==1); // same outer operation, no duplicate inner receipt
 const bool unresolved=mode=="download-cleanup"||mode=="database-write"||mode=="origin-write"||mode=="backup-cleanup";
 assert(job.m_completionVerified==!unresolved);
 assert(result==(mode=="success"||mode=="callback"||mode.rfind("package-prune",0)==0));
 JobCheckpoint::Phase(record,"callback");assert(JobCheckpoint::GetSnapshot().required==1);
 bool callbackVerified=true;
 {JobCheckpoint::WorkBinding binding(record);
  try {CAddonInstaller::GetInstance().OnJobComplete(1,result,&job);}
  catch(const std::exception&) {callbackVerified=false;}
 }
 JobCheckpoint::Complete(record,job.m_completionVerified && callbackVerified,false,callbackVerified);
 record.reset();auto snapshot=JobCheckpoint::GetSnapshot();
 const bool cacheFailure=mode=="package-prune-db"||mode=="package-prune-file";
 assert(snapshot.required==(cacheFailure?2U:((unresolved||mode=="callback")?1U:0U)));
 if(cacheFailure) {
  bool outer=false,cache=false;
  for(const auto& blocker:snapshot.blockers){outer|=blocker.resource=="addon-a";cache|=blocker.resource=="package_cache";}
  assert(outer&&cache); // genuinely independent callback and cache obligations
 }
 if(!result&&job.m_completionVerified){assert(!snapshot.resolvedHistory.empty());assert(errors||mode=="cancel"||mode=="unload"||mode=="reload");}
 if(mode=="dependency-committed"){
  sqlite3* db;assert(sqlite3_open((root/"addon.db").c_str(),&db)==SQLITE_OK);
  int count=-1;
  assert(sqlite3_exec(db,"SELECT count(*) FROM packages",[](void* result,int,char** values,char**)->int{
   *static_cast<int*>(result)=std::stoi(values[0]);return 0;
  },&count,nullptr)==SQLITE_OK);
  assert(count==1);assert(sqlite3_close(db)==SQLITE_OK);
 }
 std::cout<<"PASS production DoWork/dependencies/download/install SQLite/filesystem "<<mode<<"\n";
}
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
    root=a.runtime/'xbmc'; source=(root/'addons/AddonInstaller.cpp').read_text()
    bodies=[function(source,'class CAddonOperationReceipt')+';', function(source,'bool DeletePackage('),
            function(source,'bool CAddonInstallJob::DoWork()'), function(source,'bool CAddonInstallJob::DownloadPackage('),
            function(source,'bool CAddonInstallJob::Install(')]
    bodies += [function(source,name) for name in ('void CAddonInstaller::OnJobComplete(',
                'void CAddonInstaller::PrunePackageCache()', 'int64_t CAddonInstaller::EnumeratePackageFolder(')]
    start=source.index('bool CAddonInstaller::CheckDependencies(const AddonPtr& addon,\n                                        std::pair')
    bodies.append(function(source[start:],'bool CAddonInstaller::CheckDependencies('))
    bodies.append(function(source,'bool CAddonInstaller::CheckDependencies(const AddonPtr &addon,'))
    filesystem=(root/'addons/FilesystemInstaller.cpp').read_text()
    bodies += [function(filesystem,name) for name in ('bool CFilesystemInstaller::InstallToFilesystem(', 'bool CFilesystemInstaller::UnInstallFromFilesystem(')]
    modes=('success','resolve','dependency','dependency-committed','database-open','download','download-cleanup',
           'hash','database-write','archive','cancel','unpack','move','backup-cleanup','unload','reload','origin-write','callback',
           'package-prune','package-prune-db','package-prune-file')
    with tempfile.TemporaryDirectory(prefix='installer-production-') as tmp:
        tmp=Path(tmp);(tmp/'test.cpp').write_text(PEERS.replace('// @PRODUCTION@','\n'.join(bodies)))
        library=ctypes.util.find_library('sqlite3')
        if not library:raise RuntimeError('Real SQLite is required; it is never mocked')
        linker=library if Path(library).is_absolute() else '-l:'+library
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-DINFINITY_DATABASE_BARRIER_TEST','-Wall','-Wextra',
            '-Werror','-Wno-unused-parameter','-pthread','-I',str(root),str(tmp/'test.cpp'),linker,'-o',str(tmp/'test')],check=True)
        for mode in modes:subprocess.run([str(tmp/'test'),mode,str(tmp/mode)],check=True,timeout=30)

if __name__=='__main__':main()
