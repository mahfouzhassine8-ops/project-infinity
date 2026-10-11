"""Production installer filesystem and receipt methods on real host files.

Kodi VFS adapters below stand in only for copy/rename and presentation. The
production post-operation proof runs against real POSIX descriptors/fsync.
Android device filesystem acceptance is still required.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parents[1] / 'runtime-tests'))
from test_job_checkpoint import function

PEERS = r'''
#include "addons/InfinityAddonFileReceipt.h"
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include "utils/JobCheckpoint.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>
namespace fs = std::filesystem;
struct CLog { template<class... T> static void Log(int, const char*, T&&...){} };
constexpr int LOGERROR=1, LOGWARNING=2;
struct CDirectory {
 static bool Create(const std::string& p){ return fs::create_directory(p); }
 static bool Exists(const std::string& p){ return fs::is_directory(p); }
 static bool RemoveRecursive(const std::string& p){ return fs::remove_all(p)>0; }
};
struct CFile { static bool Rename(const std::string& a,const std::string& b){ return ::rename(a.c_str(),b.c_str())==0; } };
struct URIUtils { static std::string AddFileToFolder(const std::string& a,const std::string& b){ return (fs::path(a)/b).string(); } };
struct StringUtils { static std::string CreateUUID(){ static int n=0;return "temporary-"+std::to_string(++n); } };
class CFilesystemInstaller {
public:
 std::string m_addonFolder,m_tempFolder;
 bool InstallToFilesystem(const std::string&,const std::string&);
 bool UnInstallFromFilesystem(const std::string&);
 bool UnpackArchive(const std::string& from,const std::string& to){
  try {fs::copy(from,to,fs::copy_options::recursive|fs::copy_options::overwrite_existing);return true;} catch(...){return false;}
 }
};
// @PRODUCTION@
int main(int argc,char**argv){
 assert(argc==2);fs::path root=argv[1];fs::create_directories(root);
 fs::path source=root/"source";fs::create_directories(source/"nested");
 {std::ofstream(source/"addon.xml")<<"verified addon";std::ofstream(source/"nested/state.py")<<"code";}
 CFilesystemInstaller installer;installer.m_addonFolder=(root/"addons").string();installer.m_tempFolder=(root/"addons/temp").string();
 fs::create_directories(installer.m_tempFolder);
 assert(installer.InstallToFilesystem(source.string(),"plugin.video.fixture"));
 auto target=root/"addons/plugin.video.fixture";
 assert(fs::exists(target/"nested/state.py"));assert(InfinityAddonFileReceipt::Existing(target.string(),true));
 assert(InfinityAddonFileReceipt::Existing((target/"addon.xml").string(),false));
 assert(installer.InstallToFilesystem(source.string(),"plugin.video.fixture"));
 assert(installer.UnInstallFromFilesystem(target.string()));assert(!fs::exists(target));
 assert(InfinityAddonFileReceipt::Removed(target.string()));
 assert(!InfinityAddonFileReceipt::Existing(target.string(),true));
 assert(!InfinityAddonFileReceipt::Removed(source.string()));
 assert(!installer.InstallToFilesystem((root/"missing-package").string(),"not-installed"));
 fs::create_directory_symlink(source,root/"link");
 assert(!InfinityAddonFileReceipt::Existing((root/"link").string(),true));
 assert(!InfinityAddonFileReceipt::Existing((root/"link/addon.xml").string(),false));
 assert(!InfinityAddonFileReceipt::Existing((source/"../source/addon.xml").string(),false));
 fs::create_symlink(source/"addon.xml",source/"escape");
 assert(!InfinityAddonFileReceipt::Existing(source.string(),true));fs::remove(source/"escape");
 assert(::mkfifo((source/"fifo").c_str(),0600)==0);assert(!InfinityAddonFileReceipt::Existing(source.string(),true));fs::remove(source/"fifo");
 // Success acknowledges work, failures remain, and two resources cannot collide.
 { bool verified=false;CAddonOperationReceipt receipt("install","addon-a",verified);assert(JobCheckpoint::GetSnapshot().required==1);verified=true; }
 assert(JobCheckpoint::GetSnapshot().required==0);
 { bool verified=false;CAddonOperationReceipt receipt("install","addon-a",verified); }
 assert(JobCheckpoint::GetSnapshot().required==1);
 { bool verified=false;CAddonOperationReceipt receipt("install","addon-b",verified);verified=true; }
 assert(JobCheckpoint::GetSnapshot().required==1); // Unrelated success does not erase A.
 { bool verified=false;CAddonOperationReceipt receipt("install","addon-b",verified);InfinityDatabaseBarrier::RecordFailure("injected SQL commit failure");verified=true; }
 assert(JobCheckpoint::GetSnapshot().required==2);
 { bool verified=false;CAddonOperationReceipt receipt("install","addon-c",verified);{bool nested=false;CAddonOperationReceipt dependency("install","dependency",nested);assert(JobCheckpoint::GetSnapshot().required==4);nested=true;}verified=true; }
 assert(JobCheckpoint::GetSnapshot().required==2);
 // A verified replacement of exactly A retires only A, preserving evidence.
 { bool verified=false;CAddonOperationReceipt receipt("addon_install","repair-a",verified); }
 const auto before=JobCheckpoint::GetSnapshot().required;
 { bool verified=false;CAddonOperationReceipt receipt("addon_install","repair-b",verified);verified=true; }
 assert(JobCheckpoint::GetSnapshot().required==before);
 { bool verified=false;CAddonOperationReceipt receipt("addon_install","repair-a",verified);verified=true; }
 assert(JobCheckpoint::GetSnapshot().required==before-1);
 assert(JobCheckpoint::GetSnapshot().resolvedCount==1);
 assert(JobCheckpoint::GetSnapshot().resolvedHistory.back().resource=="repair-a");
 // Pending peer, wrong operation, unknown contract and failed repair cannot clear.
 auto failed=JobCheckpoint::Admit(true,false,"native_databases","addon_install","fixture","work",true,"pending-a");JobCheckpoint::Complete(failed,false);
 auto peer=JobCheckpoint::Admit(true,false,"native_databases","addon_install","fixture","work",true,"pending-a");
 auto repair=JobCheckpoint::Admit(true,false,"native_databases","addon_install","fixture","work",true,"pending-a");JobCheckpoint::Complete(repair,true,true);
 assert(!failed->resolved);JobCheckpoint::Complete(peer,false);
 auto wrong=JobCheckpoint::Admit(true,false,"native_databases","addon_uninstall","fixture","work",true,"pending-a");JobCheckpoint::Complete(wrong,true,true);assert(!failed->resolved);
 auto final=JobCheckpoint::Admit(true,false,"native_databases","addon_install","fixture","work",true,"pending-a");JobCheckpoint::Complete(final,true,true);assert(failed->resolved&&peer->resolved);
 std::cout<<"PASS production install/update/uninstall, nested receipts, failed SQL, missing package, symlink/FIFO/path refusal and independent failure resources\n";
}
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', required=True, type=Path)
    a = p.parse_args()
    n = a.runtime / 'xbmc'
    installer = (n / 'addons/AddonInstaller.cpp').read_text()
    filesystem = (n / 'addons/FilesystemInstaller.cpp').read_text()
    methods = function(installer, 'class CAddonOperationReceipt') + ';\n'
    methods += '\n'.join(function(filesystem, x) for x in (
        'bool CFilesystemInstaller::InstallToFilesystem(', 'bool CFilesystemInstaller::UnInstallFromFilesystem('))
    # Exact result checks are preserved even when the backend API returns void.
    for name in ('CAddonInstallJob', 'CAddonUnInstallJob'):
        body = function(installer, 'bool ' + name + '::DoWork()')
        assert 'CAddonOperationReceipt completion(' in body
        assert body.rindex('m_completionVerified = true;') < body.rindex('return true;')
    assert '!= 0' in function(installer, 'bool CAddonInstaller::UnInstall(')
    assert 'if (!CServiceBroker::GetAddonMgr().SetAddonOrigin(' in installer
    assert 'if (!ClearFavourites())' in installer
    assert 'if (!database.Open())' in function(installer, 'bool CAddonUnInstallJob::DoWork()')
    with tempfile.TemporaryDirectory(prefix='installer-proof-') as tmp:
        tmp = Path(tmp)
        cpp = tmp / 'test.cpp'
        cpp.write_text(PEERS.replace('// @PRODUCTION@', methods))
        subprocess.run(['g++', '-std=c++17', '-DTARGET_ANDROID', '-DINFINITY_DATABASE_BARRIER_TEST',
                        '-Wall', '-Wextra', '-Werror', '-pthread', '-I', str(n), str(cpp), '-o', str(tmp / 'test')], check=True)
        subprocess.run([str(tmp / 'test'), str(tmp / 'files')], check=True, timeout=30)


if __name__ == '__main__':
    main()
