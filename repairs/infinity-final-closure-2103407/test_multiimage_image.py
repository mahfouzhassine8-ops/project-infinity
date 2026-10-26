"""Compile the actual retained directory factory and observation header.

Peers represent backend dispatches; no Kodi/Android runtime pass is inferred.
The old factory must reproduce the image veto and the candidate must preserve
opaque write, VFS override, exception and unknown-protocol vetoes.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import stage_native_modules as integration
from test_native_integration import block

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(os.environ.get('FINAL_NATIVE_SOURCE_ROOT', ROOT / 'baseline-2103407/foundation40089463702/selected-source-readonly/native'))
FACTORY = integration.DIRECTORY
HEADER = integration.MULTIIMAGE

PEERS = r'''
#include <algorithm>
#include <cassert>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
struct CJobCheckpointRecord {
 bool unknown=false;std::string owner="background_jobs",operation="multiimage-enumeration";
};
enum class CJobDurability { VerifiedUnchanged, Unresolved };
namespace JobCheckpoint {
 inline std::shared_ptr<CJobCheckpointRecord> currentOperation;
 inline bool unchanged=false;
 inline void WorkResult(std::shared_ptr<CJobCheckpointRecord>,CJobDurability d,bool,const std::string&){
  unchanged=d==CJobDurability::VerifiedUnchanged;
 }
}
#include "InfinityMultiImagePersistence.h"
bool opaque=false,vfs=false,throws=false,wake=true;int work=0,probes=0;
class CURL {
 std::string protocol;
 public:explicit CURL(std::string p):protocol(std::move(p)){}
 const std::string&GetProtocol()const{return protocol;}
 bool IsProtocol(const std::string&p)const{return protocol==p;}
 std::string Get()const{return protocol+"://fixture/";}
 std::string GetRedacted()const{return Get();}
};
class CFileItem { public:CFileItem(const std::string&,bool){} };
class IDirectory { public:virtual ~IDirectory()=default; };
class IFileDirectory:public IDirectory {};
class CFileDirectoryFactory {
 public:static IFileDirectory*Create(const CURL&,CFileItem*){
  ++probes;
  if(throws)throw std::runtime_error("opaque probe exception");
  if(opaque){++work;InfinityMultiImagePersistence::UnreviewedDispatch("opaque_write");}
  return nullptr;
 }
};
class VFS {
 public:bool HasDirectories()const{return true;}std::string GetProtocols()const{return "image";}
};
class CVFSEntryIDirectoryWrapper:public IDirectory {
 public:explicit CVFSEntryIDirectoryWrapper(std::shared_ptr<VFS>){++work;}
};
struct Cache {std::vector<std::shared_ptr<VFS>>GetAddonInstances(){
 return vfs?std::vector<std::shared_ptr<VFS>>{std::make_shared<VFS>()}:std::vector<std::shared_ptr<VFS>>{};
}};
struct CServiceBroker {static bool IsAddonInterfaceUp(){return true;}
 static Cache&GetVFSAddonCache(){static Cache cache;return cache;}};
struct CWakeOnAccess {static CWakeOnAccess&GetInstance(){static CWakeOnAccess value;return value;}
 bool WakeUpHost(const CURL&){return wake;}};
struct StringUtils {static std::vector<std::string>Split(const std::string&s,const std::string&){return {s};}};
struct CLog {template<class...Args>static void Log(Args...){}};
constexpr int LOGWARNING=2;
class CDirectoryFactory {public:static IDirectory*Create(const CURL&);};
'''

DRIVER = r'''
int main(int argc,char**argv){
 assert(argc==3);const std::string scenario=argv[1];bool candidate=std::string(argv[2])=="candidate";
 if(scenario=="vfs")vfs=true;
 if(scenario=="opaque")opaque=true;
 if(scenario=="throws")throws=true;
 if(scenario=="wake")wake=false;
 const std::string protocol=scenario=="unknown"?"future":scenario=="local"?"file":"image";
 auto record=std::make_shared<CJobCheckpointRecord>();
 JobCheckpoint::currentOperation=record;
 if(scenario=="no-scope"){
  assert(!InfinityMultiImagePersistence::current);
  std::unique_ptr<IDirectory>directory(CDirectoryFactory::Create(CURL(protocol)));
  assert(!directory);assert(!InfinityMultiImagePersistence::current);return 0;
 }
 InfinityMultiImagePersistence::Scope scope(record);
 bool threw=false,returned=false;
 try {std::unique_ptr<IDirectory>directory(CDirectoryFactory::Create(CURL(protocol)));returned=bool(directory);}
 catch(const std::runtime_error&){threw=true;}
 assert(returned==(scenario=="vfs"||scenario=="local"));
 assert(threw==(scenario=="throws"));
 bool verified=scope.Finish(!threw);
 const bool expected=scenario=="local"||(candidate&&scenario=="image");
 assert(verified==expected);assert(JobCheckpoint::unchanged==expected);
 if(scenario=="vfs"||scenario=="opaque")assert(work==1);else assert(work==0);
 if(scenario=="wake")assert(probes==0);else assert(probes==1);
}
'''


class ImageDirectoryAccountingTests(unittest.TestCase):
    def test_actual_factory_before_after_and_opaque_negative_controls(self):
        raw = (SOURCE / FACTORY).read_bytes()
        header = (SOURCE / HEADER).read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / 'utils').mkdir()
            (directory / 'utils/JobCheckpoint.h').write_text('#pragma once\n')
            for candidate in (False, True):
                name = 'candidate' if candidate else 'baseline'
                text = (integration.patch(FACTORY, raw) if candidate else raw).decode()
                observed = integration.patch(HEADER, header) if candidate else header
                (directory / 'InfinityMultiImagePersistence.h').write_bytes(observed)
                start = text.index('IDirectory* CDirectoryFactory::Create(const CURL& url)')
                opening = text.index('{', start)
                factory = text[start:opening] + block(text, opening)
                import re
                classes = sorted(set(re.findall(r'new (C\w+)\(', factory)) - {'CVFSEntryIDirectoryWrapper'})
                declarations = '\n'.join('class '+c+':public IDirectory{};' for c in classes)
                cpp = directory / (name+'.cpp')
                exe = directory / name
                cpp.write_text(PEERS + declarations + '\n' + factory + DRIVER)
                subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-DTARGET_POSIX',
                                '-Wall','-Wextra','-Werror','-I',str(directory),str(cpp),'-o',str(exe)],check=True)
                for scenario in ('image','vfs','opaque','throws','unknown','wake','no-scope','local'):
                    with self.subTest(candidate=candidate, scenario=scenario):
                        subprocess.run([str(exe),scenario,name],check=True)

    def test_inverse_diff_and_exact_source_guards(self):
        for name in (FACTORY, HEADER):
            raw = (SOURCE / name).read_bytes()
            text = integration.patch(name, raw).decode()
            for old, new in reversed(integration.edits(name)):
                self.assertEqual(text.count(new), 1)
                text = text.replace(new, old, 1)
            self.assertEqual(text.encode(), raw)
            with self.assertRaises(ValueError):
                integration.patch(name, raw+b'\n')
        factory = integration.patch(FACTORY,(SOURCE/FACTORY).read_bytes()).decode()
        self.assertLess(factory.index('return new CVFSEntryIDirectoryWrapper'),
                        factory.index('multiImageFactory.ReviewedNoBackend()'))
        self.assertNotIn('ReviewedNoBackend', (SOURCE/'xbmc/guilib/GUIMultiImage.cpp').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
