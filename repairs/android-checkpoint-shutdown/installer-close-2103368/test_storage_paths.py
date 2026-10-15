"""Production installer through searchable, non-listable storage ancestors.

Run as an unprivileged process, including on root CI hosts. Ordinary VFS reads
and writes work below the ancestor; receipt inspection must not require listing
that ancestor. The original production filesystem/receipt assertions are reused.
"""
from pathlib import Path
import argparse
import os
import runpy
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'runtime-tests'))
from test_job_checkpoint import function


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    args = parser.parse_args()
    root = args.runtime.resolve() / 'xbmc'
    fixture = runpy.run_path(str(HERE / 'integration-2103367/test_installer_recovery.py'))['PEERS']
    fixture = fixture.replace('fs::path root=argv[2];', 'fs::path root=fs::path(argv[2])/"gateway/appfiles";')
    fixture = fixture.replace(' const auto before=', '''
 // The app owns its leaf; it may search but cannot enumerate its ancestor.
 assert(::chmod(root.parent_path().c_str(), 0111)==0);
 assert(::open(root.parent_path().c_str(), O_RDONLY|O_DIRECTORY)<0 && errno==EACCES);
 { std::ifstream readable(root/"addons/addon-a/addon.xml");
   std::string value; std::getline(readable,value); assert(value=="original installation"); }
 const auto before=''', 1)
    fixture = fixture.replace(' CFilesystemInstaller installer;', '''
 if(mode=="success") {
   // Path-only handles must never authorize symlink or dot-component walks.
   fs::create_directory_symlink(root/"addons",root/"alias");
   fs::create_symlink(root/"addons/addon-a/addon.xml",root/"linked.xml");
   assert(!InfinityAddonFileReceipt::Capture((root/"alias/addon-a").string()).valid);
   assert(!InfinityAddonFileReceipt::Capture((root/"linked.xml").string()).valid);
   assert(!InfinityAddonFileReceipt::Capture((root/"addons/../addons/addon-a").string()).valid);
   assert(!InfinityAddonFileReceipt::Capture((root/"addons/./addon-a").string()).valid);
   { InfinityAddonFileReceipt::WriteScope proof;
     const auto target=(root/"addons/addon-a/addon.xml").string();
     assert(::chmod((root/"addons/addon-a").c_str(),0111)==0);
     proof.Touch(target);
     assert(!proof.Committed(target,false));
     assert(!proof.Proven());
     assert(proof.FailureDetail()=="open_parent:errno="+std::to_string(EACCES));
     assert(::chmod((root/"addons/addon-a").c_str(),0755)==0);
   }
 }
 CFilesystemInstaller installer;''', 1)
    installer = (root / 'addons/AddonInstaller.cpp').read_text()
    filesystem = (root / 'addons/FilesystemInstaller.cpp').read_text()
    production = function(installer, 'class CAddonOperationReceipt') + ';\n'
    production += '\n'.join(function(filesystem, name) for name in (
        'bool CFilesystemInstaller::InstallToFilesystem(',
        'bool CFilesystemInstaller::UnInstallFromFilesystem('))
    def unprivileged():
        if os.geteuid() == 0:
            os.setgroups([])
            os.setgid(65534)
            os.setuid(65534)
    modes = ('success', 'unpack', 'new-move', 'fsync-restored', 'fsync-unresolved',
             'uninstall-restored', 'partial-delete', 'nested', 'recovery-restored')
    with tempfile.TemporaryDirectory(prefix='installer-storage-') as folder:
        tmp = Path(folder)
        tmp.chmod(0o777)
        (tmp / 'test.cpp').write_text(fixture.replace('// @PRODUCTION@', production))
        subprocess.run(['g++', '-std=c++17', '-DTARGET_ANDROID', '-DINFINITY_DATABASE_BARRIER_TEST',
                        '-Wall', '-Wextra', '-Werror', '-pthread', '-I', str(root),
                        str(tmp / 'test.cpp'), '-o', str(tmp / 'test')], check=True)
        try:
            for mode in modes:
                subprocess.run([str(tmp / 'test'), mode, str(tmp / mode)], check=True,
                               timeout=30, preexec_fn=unprivileged)
        finally:
            for mode in modes:
                gateway = tmp / mode / 'gateway'
                if gateway.exists():
                    gateway.chmod(0o700)
    print('PASS production installer under non-listable storage ancestors; strict failures retained')


if __name__ == '__main__':
    main()
