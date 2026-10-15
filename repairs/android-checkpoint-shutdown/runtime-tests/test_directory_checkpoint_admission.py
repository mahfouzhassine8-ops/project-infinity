#!/usr/bin/env python3
"""Compile real latent directory adapter and verify actual dispatch admission site."""
from pathlib import Path
import argparse
import subprocess
import tempfile
from test_job_checkpoint import function

PEERS=r'''
#include <cassert>
#include <chrono>
#include <memory>
#include <string>
using namespace std::chrono_literals;
class CJob{public:virtual~CJob()=default;virtual bool DoWork()=0;enum{PRIORITY_HIGH};};
namespace Test{inline bool active=false;inline int dispatch=0;}
namespace InfinityAndroidCheckpoint{class CheckpointWriteGuard{public:explicit CheckpointWriteGuard(const char*){}explicit operator bool()const{return !Test::active;}};}
class CURL{};class CFileItemList{public:void SetURL(const CURL&){}void Clear(){}void Copy(const CFileItemList&){} };
class CEvent{bool ready=false;public:explicit CEvent(bool){}void Set(){ready=true;}template<class T>bool Wait(T){return ready;}};
class IDirectory{public:bool GetDirectory(const CURL&,CFileItemList&){++Test::dispatch;return true;}};
class CJobManager{public:unsigned int AddJob(CJob*job,void*,int){delete job;return 0;}void CancelJob(unsigned int){}};
class CServiceBroker{public:static CJobManager*GetJobManager(){static CJobManager m;return &m;}};
'''
TEST=r'''
int main(){std::shared_ptr<IDirectory>impl=std::make_shared<IDirectory>();CURL url;CFileItemList out;
 {CGetDirectory adapter(impl,url,url);assert(adapter.Wait(0));assert(adapter.GetDirectory(out));assert(Test::dispatch==1);}
 Test::active=true;{CGetDirectory adapter(impl,url,url);assert(adapter.Wait(0));assert(!adapter.GetDirectory(out));assert(Test::dispatch==1);}
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args();source=(a.runtime/'xbmc/filesystem/Directory.cpp').read_text()
 marker='bool CDirectory::GetDirectory(const CURL& url,\n                              const std::shared_ptr<IDirectory>& pDirectory,'
 body=function(source,marker)
 assert body.index('CheckpointWriteGuard admission("directory-work")')<body.index('pDirectory->GetDirectory(authUrl, items)')
 assert 'if (!admission)\n    return false;' in body
 adapter=function(source,'class CGetDirectory')+';'
 with tempfile.TemporaryDirectory(prefix='directory-checkpoint-') as tmp:
  tmp=Path(tmp);(tmp/'test.cpp').write_text(PEERS+adapter+TEST)
  subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror',str(tmp/'test.cpp'),'-o',str(tmp/'test')],check=True)
  subprocess.run([str(tmp/'test')],check=True)
 print('PASS: actual latent adapter preserves legacy fallback, rejects checkpoint fallback, signals failed result; live directory dispatch gate bound')
if __name__=='__main__':main()
