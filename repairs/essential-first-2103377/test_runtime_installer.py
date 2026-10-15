#!/usr/bin/env python3
"""Reuse the production installer/SQLite/filesystem harness with real admission code.

Only Kodi service peers and the coordinator state container are adapters. The
DoWork body, admission constructor/destructor, receipts, and filesystem install
bodies are extracted from the actual prepared production sources.
"""
import argparse
import ctypes.util
import importlib.util
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', required=True, type=Path)
    args = p.parse_args()
    path = ROOT / 'repairs/android-checkpoint-shutdown/integration-2103367/test_installer_work.py'
    spec = importlib.util.spec_from_file_location('essential_existing_installer', path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    source = (args.runtime / 'xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp').read_text()
    guard = '\n'.join(old.function(source, name) for name in (
        'CheckpointWriteGuard::CheckpointWriteGuard(', 'CheckpointWriteGuard::~CheckpointWriteGuard()'))
    peers = old.PEERS.replace('// @PRODUCTION@', r'''
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
namespace InfinityAndroidCheckpoint {
struct Owner {unsigned generation=0;bool dirty=false,complete=false;};
struct State {std::mutex mutex;std::atomic<bool> active{false};bool sealed=false;
 std::string phase="RUNNING";unsigned activeWrites=0;std::map<std::string,Owner> owners;};
inline State& Get(){static State s;return s;}
thread_local unsigned acceptedPlaybackDepth=0,permissionDepth=0;
''' + guard + '\n}\n// @PRODUCTION@')
    # The peer triggers Close only after the real guard admitted this DoWork.
    peers = peers.replace('void SetTitle(const std::string&){}', 'void SetTitle(const std::string&);')
    peers = peers.replace('// @PRODUCTION@', r'''
void CAddonInstallJob::SetTitle(const std::string&) {
 if(mode=="admitted-before-close") {
  auto& state=InfinityAndroidCheckpoint::Get();assert(state.activeWrites==1);
  state.active=true;state.phase="QUIESCE";
 }
}
// @PRODUCTION@''')
    peers = peers.replace('#include <thread>', '#include <thread>\n#include <atomic>')
    peers = peers.replace(' bool result;\n', r'''
 if(mode=="late-install" || mode=="sealed-install") {
  auto& state=InfinityAndroidCheckpoint::Get();state.active=true;
  state.sealed=(mode=="sealed-install");state.phase=state.sealed?"SAFE_TO_TERMINATE":"QUIESCE";
 }
 bool result;
''')
    peers = peers.replace(' assert(JobCheckpoint::GetSnapshot().required==1); // same outer', r'''
 assert(InfinityAndroidCheckpoint::Get().activeWrites==0);
 if(mode=="late-install" || mode=="sealed-install") {
  assert(!result && job.m_completionVerified && errors==0);
  assert(!fs::exists(root/"addon.db") && fs::is_empty(root/"addons/packages"));
  std::ifstream original(root/"addons/addon-a/addon.xml");std::string data;
  std::getline(original,data);assert(data=="original addon");
  assert(record->durability==CJobDurability::VerifiedUnchanged);
  JobCheckpoint::Complete(record,true);record.reset();
  assert(JobCheckpoint::GetSnapshot().required==0);
  std::cout<<"PASS actual installer admission rejects mutation "<<mode<<"\n";return 0;
 }
 if(mode=="admitted-before-close")assert(InfinityAndroidCheckpoint::Get().active);
 assert(JobCheckpoint::GetSnapshot().required==1); // same outer''')
    peers = peers.replace('mode=="success"||mode=="callback"', 'mode=="success"||mode=="admitted-before-close"||mode=="callback"')
    root = args.runtime / 'xbmc'
    installer = (root / 'addons/AddonInstaller.cpp').read_text()
    bodies = [old.function(installer, 'class CAddonOperationReceipt') + ';']
    bodies += [old.function(installer, name) for name in (
        'bool DeletePackage(', 'bool CAddonInstallJob::DoWork()',
        'bool CAddonInstallJob::DownloadPackage(', 'bool CAddonInstallJob::Install(',
        'void CAddonInstaller::OnJobComplete(', 'void CAddonInstaller::PrunePackageCache()',
        'int64_t CAddonInstaller::EnumeratePackageFolder(')]
    start = installer.index('bool CAddonInstaller::CheckDependencies(const AddonPtr& addon,\n                                        std::pair')
    bodies.append(old.function(installer[start:], 'bool CAddonInstaller::CheckDependencies('))
    bodies.append(old.function(installer, 'bool CAddonInstaller::CheckDependencies(const AddonPtr &addon,'))
    filesystem = (root / 'addons/FilesystemInstaller.cpp').read_text()
    bodies += [old.function(filesystem, name) for name in (
        'bool CFilesystemInstaller::InstallToFilesystem(', 'bool CFilesystemInstaller::UnInstallFromFilesystem(')]
    modes = ('success', 'resolve', 'dependency', 'dependency-committed', 'database-open',
             'download', 'download-cleanup', 'hash', 'database-write', 'archive', 'cancel',
             'unpack', 'move', 'backup-cleanup', 'unload', 'reload', 'origin-write', 'callback',
             'package-prune', 'package-prune-db', 'package-prune-file',
             'late-install', 'sealed-install', 'admitted-before-close')
    assert modes[:-3] in old.main.__code__.co_consts, 'Existing installer cases changed; review extension'
    library = ctypes.util.find_library('sqlite3')
    if not library:
        raise RuntimeError('Real SQLite is required; it is never mocked')
    linker = library if Path(library).is_absolute() else '-l:' + library
    with tempfile.TemporaryDirectory(prefix='essential-installer-') as work:
        work = Path(work)
        (work / 'test.cpp').write_text(peers.replace('// @PRODUCTION@', '\n'.join(bodies)))
        subprocess.run(['g++', '-std=c++17', '-DTARGET_ANDROID', '-DINFINITY_DATABASE_BARRIER_TEST',
                        '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-pthread',
                        '-I', str(root), str(work/'test.cpp'), linker, '-o', str(work/'test')], check=True)
        for mode in modes:
            subprocess.run([str(work/'test'), mode, str(work/mode)], check=True, timeout=30)


if __name__ == '__main__':
    main()
