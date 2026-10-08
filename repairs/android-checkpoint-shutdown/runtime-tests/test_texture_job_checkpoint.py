#!/usr/bin/env python3
"""Actual cache-job bodies against controlled DB/cache peers; no SQLite bypass."""
from pathlib import Path
import argparse
import subprocess
import tempfile
import shutil
from test_job_checkpoint import function

PEERS=r'''
#include "TextureCacheJob.h"
#include <cassert>
#include <cstring>
#include <typeinfo>
namespace Test {inline bool active=false,cancel=false,cached=false,recache=false,already=false,cacheOk=false;inline int scopes=0,opens=0,commits=0;}
namespace InfinityAndroidCheckpoint {class CheckpointWriteGuard{bool admitted;public:explicit CheckpointWriteGuard(const char*owner):admitted(!Test::active){assert(std::string(owner)=="optional-cache-work");if(admitted)++Test::scopes;}~CheckpointWriteGuard(){if(admitted)--Test::scopes;}explicit operator bool()const{return admitted;}};}
class CTexture{};
class CTextureDatabase{public:CTextureDatabase(){assert(Test::scopes==1);}~CTextureDatabase(){assert(Test::scopes==1);}bool Open(){++Test::opens;return true;}void BeginTransaction(){}void IncrementUseCount(const CTextureDetails&){}void CommitTransaction(){++Test::commits;}};
class CTextureCache:public IJobCallback{public:void OnJobComplete(unsigned int,bool,CJob*)override{}static std::string GetCacheFile(const std::string&){return "cache";}std::string CheckCachedImage(const std::string&,bool&recache){recache=Test::recache;return Test::cached?"cached":"";}bool StartCacheImage(const std::string&){return !Test::already;}};
class CServiceBroker{public:static CTextureCache*GetTextureCache(){static CTextureCache c;return &c;}};
bool CJob::ShouldCancel(unsigned int,unsigned int)const{return Test::cancel;}
bool CTextureCacheJob::CacheTexture(std::unique_ptr<CTexture>*){return Test::cacheOk;}
class Callback:public IJobCallback{void OnJobComplete(unsigned int,bool,CJob*)override{}};
class DerivedCache:public CTextureCache{};
class DerivedJob:public CTextureUseCountJob{public:DerivedJob():CTextureUseCountJob({}){}};
'''
TEST=r'''
int main(){
 CTextureUseCountJob job({});CTextureCache cache;Callback other;DerivedCache derivedCache;DerivedJob derivedJob;
 using R=CJob::CheckpointResponsibility;
 assert(job.GetCheckpointResponsibility(nullptr)==R::NonPersistent);
 assert(job.GetCheckpointResponsibility(&cache)==R::NonPersistent);
 assert(job.GetCheckpointResponsibility(&other)==R::Unknown);
 assert(job.GetCheckpointResponsibility(&derivedCache)==R::Unknown);
 assert(derivedJob.GetCheckpointResponsibility(nullptr)==R::Unknown);
 Test::active=true;assert(job.DoWork());assert(Test::opens==0&&Test::commits==0&&Test::scopes==0);
 Test::active=false;assert(job.DoWork());assert(Test::opens==1&&Test::commits==1&&Test::scopes==0);
 CTextureCacheJob image("image");
 Test::cached=true;assert(!image.DoWork());assert(image.CheckpointSucceeded(false));
 Test::cached=false;Test::already=true;assert(!image.DoWork());assert(image.CheckpointSucceeded(false));
 Test::already=false;Test::cacheOk=false;assert(!image.DoWork());assert(!image.CheckpointSucceeded(false));
 Test::cancel=true;assert(!image.DoWork());assert(!image.CheckpointSucceeded(false));
 Test::cancel=false;Test::cacheOk=true;assert(image.DoWork());assert(image.CheckpointSucceeded(true));
 assert(image.GetCheckpointResponsibility(&cache)==R::Unknown);
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args();root=a.runtime/'xbmc'
 source=(root/'TextureCacheJob.cpp').read_text();markers=['CTextureCacheJob::CTextureCacheJob(', 'bool CTextureCacheJob::operator==(', 'bool CTextureCacheJob::CheckpointSucceeded(', 'bool CTextureCacheJob::DoWork()', 'CTextureUseCountJob::CTextureUseCountJob(', 'bool CTextureUseCountJob::operator==(', 'CJob::CheckpointResponsibility CTextureUseCountJob::GetCheckpointResponsibility(', 'bool CTextureUseCountJob::DoWork()']
 methods=[function(source,m) for m in markers]
 with tempfile.TemporaryDirectory(prefix='texture-job-checkpoint-') as temp:
  temp=Path(temp)
  for rel in ['TextureCacheJob.h','utils/Job.h','pictures/PictureScalingAlgorithm.h']:
   target=temp/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,target)
  (temp/'test.cpp').write_text(PEERS+'\nCTextureCacheJob::~CTextureCacheJob()=default;\n'+'\n'.join(methods)+TEST)
  subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-I',str(temp),str(temp/'test.cpp'),'-o',str(temp/'test')],check=True)
  subprocess.run([str(temp/'test')],check=True)
 print('PASS: actual texture job methods; no SQL when optional scope denied, exact callback contracts, benign false vs real failure')
if __name__=='__main__':main()
