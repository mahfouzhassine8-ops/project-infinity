"""Run production filesystem install/uninstall and operation receipts on real files.

Faults are injected at external VFS calls, never by manufacturing receipt results.
The required job ledger remains strict for incomplete restoration and real SQL
failures. Host fsync and VFS peers do not establish physical Android acceptance.
"""
from pathlib import Path
import argparse
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parents[1] / 'runtime-tests'))
from test_job_checkpoint import function

PEERS = r'''
#include <unistd.h>
#include <string>
#include <cerrno>
static bool failSync=false, onceSync=false, movedNew=false;
int FixtureFsync(int fd) {
 if(failSync && movedNew) {if(onceSync)failSync=false;errno=EIO;return -1;}
 return ::fsync(fd);
}
#define fsync FixtureFsync
#include "addons/InfinityAddonFileReceipt.h"
#undef fsync
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include "utils/JobCheckpoint.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>
namespace fs=std::filesystem;
static std::string mode;
static int renames=0;
struct CLog {template<class...T> static void Log(int,const char*,T&&...) {}};
constexpr int LOGERROR=1,LOGWARNING=2;
struct CDirectory {
 static bool Create(const std::string&p){return mode=="create"?false:fs::create_directory(p);}
 static bool Exists(const std::string&p){return fs::is_directory(p);}
 static bool RemoveRecursive(const std::string&p){
  if(mode=="cleanup")return false;
  if(mode=="partial-delete") {fs::remove(fs::path(p)/"addon.xml");return false;}
  return fs::remove_all(p)>0;
 }
};
struct CFile {static bool Rename(const std::string&a,const std::string&b){
 ++renames;
 if((mode=="old-move"&&renames==1)||(mode=="new-move"&&renames==2)||
    (mode=="restore-move"&&renames>=2))return false;
 bool ok=::rename(a.c_str(),b.c_str())==0;
 if(ok && fs::path(b).filename()=="addon-a")movedNew=true;
 return ok;
}};
struct URIUtils {static std::string AddFileToFolder(const std::string&a,const std::string&b){return (fs::path(a)/b).string();}};
struct StringUtils {static std::string CreateUUID(){static thread_local int n=0;return "stage-"+std::to_string(++n);}};
class CFilesystemInstaller {
public:
 std::string m_addonFolder,m_tempFolder;
 bool InstallToFilesystem(const std::string&,const std::string&);
 bool UnInstallFromFilesystem(const std::string&);
 bool UnpackArchive(const std::string&a,const std::string&b){
  fs::copy(a,b,fs::copy_options::recursive|fs::copy_options::overwrite_existing);
  return mode!="unpack" && mode!="unpack-cleanup";
 }
};
// @PRODUCTION@
int main(int argc,char**argv) {
 assert(argc==3);mode=argv[1];fs::path root=argv[2];
 fs::create_directories(root/"source");fs::create_directories(root/"addons/temp");
 fs::create_directories(root/"addons/addon-a");
 std::ofstream(root/"source/addon.xml")<<"new installation";
 std::ofstream(root/"addons/addon-a/addon.xml")<<"original installation";
 const auto before=InfinityAddonFileReceipt::Capture((root/"addons/addon-a").string());
 assert(before.valid);
 CFilesystemInstaller installer;installer.m_addonFolder=(root/"addons").string();installer.m_tempFolder=(root/"addons/temp").string();
 if(mode=="fsync-restored"||mode=="fsync-unresolved"){failSync=true;onceSync=mode=="fsync-restored";}
 bool business=false,durable=false;
 {
  CAddonOperationReceipt receipt("addon_install","addon-a",durable);
  if(mode=="dependency-rejected")business=false;
  else if(mode=="sql-failed") {InfinityDatabaseBarrier::RecordFailure("fixture SQL commit");business=false;}
  else if(mode=="unknown-resource") {receipt.Unknown();business=false;}
  else if(mode=="uninstall-restored"||mode=="partial-delete") {
   if(mode=="uninstall-restored")mode="cleanup";
   business=installer.UnInstallFromFilesystem((root/"addons/addon-a").string());
  }
  else business=installer.InstallToFilesystem((root/"source").string(),"addon-a");
  durable=business; // Production DoWork supplies only its business result here.
 }
 const auto snapshot=JobCheckpoint::GetSnapshot();
 const bool unresolved=mode=="sql-failed"||mode=="unknown-resource"||mode=="restore-move"||
   mode=="cleanup"||mode=="partial-delete"||mode=="fsync-unresolved";
 // Uninstall cleanup failure restored the complete original, while install
 // cleanup failure keeps the new installed tree and a required backup obligation.
 const bool uninstall=(std::string(argv[1])=="uninstall-restored");
 assert(snapshot.required==(unresolved&&!uninstall?1U:0U));
 assert(durable==(!unresolved||uninstall));
 if(std::string(argv[1])=="success")assert(business);
 else assert(!business);
 if(durable && !business && std::string(argv[1])!="sql-failed") {
  assert(snapshot.resolvedHistory.size()==1);
  assert(snapshot.resolvedHistory[0].resource=="addon-a");
  assert(InfinityAddonFileReceipt::Capture((root/"addons/addon-a").string())==before);
 }
 if(unresolved&&!uninstall) {
  // A successful *same-name* or unrelated operation lacks proof for the actual
  // failed scopes, so neither is permitted to discard the old obligation.
  for(const auto& id:{"addon-a","addon-b"}) {
   bool verified=false;{CAddonOperationReceipt receipt("addon_install",id,verified);verified=true;}
   assert(JobCheckpoint::GetSnapshot().required==1);
  }
 }
 std::cout<<"PASS production filesystem/receipt "<<argv[1]<<"\n";
}
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True,type=Path);a=p.parse_args()
    root=a.runtime/'xbmc'
    installer=(root/'addons/AddonInstaller.cpp').read_text()
    filesystem=(root/'addons/FilesystemInstaller.cpp').read_text()
    production=function(installer,'class CAddonOperationReceipt')+';\n'
    production+='\n'.join(function(filesystem, name) for name in (
        'bool CFilesystemInstaller::InstallToFilesystem(', 'bool CFilesystemInstaller::UnInstallFromFilesystem('))
    modes=('success','dependency-rejected','create','unpack','old-move','new-move','restore-move',
           'cleanup','sql-failed','unknown-resource','fsync-restored','fsync-unresolved',
           'uninstall-restored','partial-delete')
    with tempfile.TemporaryDirectory(prefix='installer-recovery-') as tmp:
        tmp=Path(tmp);(tmp/'test.cpp').write_text(PEERS.replace('// @PRODUCTION@',production))
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-DINFINITY_DATABASE_BARRIER_TEST',
            '-Wall','-Wextra','-Werror','-pthread','-I',str(root),str(tmp/'test.cpp'),'-o',str(tmp/'test')],check=True)
        for mode in modes:
            subprocess.run([str(tmp/'test'),mode,str(tmp/mode)],check=True,timeout=30)

if __name__=='__main__':main()
