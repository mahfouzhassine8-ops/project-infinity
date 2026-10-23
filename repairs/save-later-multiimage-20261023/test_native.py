"""Execute production multi-image code, factory, POSIX reader and job manager.

The GUI, network/unknown-directory and service boundaries are explicit host
peers. No provider implementation, native decoder or physical Fold is simulated.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

PEERS=r'''
#pragma once
#include "utils/JobManager.h"
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <sys/stat.h>
#include <dirent.h>

namespace Fixture {
inline std::string root;
inline bool infinity=true;
inline bool opaqueFile=false,overrideSpecial=false,substitute=false;
inline int unknownWork=0, mimeNetwork=0;
inline bool factoryThrows=false;
inline std::function<void()> duringDirectoryRead;
}
namespace InfinityMultiImagePersistence { void UnreviewedDispatch(const char*); }
namespace XBMCAddon {namespace xbmc {inline std::string getSkinDir(){return Fixture::infinity?"skin.infinity.diggz":"skin.cobra";}}}
struct CTextureInfo {};
struct CAspectRatio {};
struct CAction {};
struct CGUIListItem {};
using CDirtyRegionList=std::vector<int>;
constexpr int WINDOW_INVALID=-1,GUI_MSG_REFRESH_THUMBS=1,GUI_MSG_RESET_MULTI_IMAGE=2;
struct CGUIMessage{int GetMessage()const{return 0;}};
class CGUIControl {
public:
 enum{GUICONTROL_MULTI_IMAGE=1,DELAYED=2};
 int ControlType=0,m_visible=0,m_parentID=1;
 float m_posX=0,m_posY=0,m_width=1,m_height=1;
 bool m_bAllocated=false;
 unsigned int m_diffuseColor=0;
 CGUIControl(int p,int,float x,float y,float w,float h):m_parentID(p),m_posX(x),m_posY(y),m_width(w),m_height(h){}
 virtual~CGUIControl()=default;
 virtual CGUIControl*Clone()const{return nullptr;}
 virtual void Process(unsigned int,CDirtyRegionList&){}
 virtual void Render(){}
 virtual void UpdateVisibility(const CGUIListItem*){}
 virtual void UpdateInfo(const CGUIListItem*){}
 virtual bool OnAction(const CAction&){return false;}
 virtual bool OnMessage(CGUIMessage&){return false;}
 virtual void AllocResources(){m_bAllocated=true;}
 virtual void FreeResources(bool=false){m_bAllocated=false;}
 virtual void DynamicResourceAlloc(bool){}
 virtual bool IsDynamicallyAllocated(){return false;}
 virtual void SetInvalid(){}
 virtual bool CanFocus()const{return false;}
 virtual std::string GetDescription()const{return {};}
 bool IsVisible()const{return true;}
 int GetID()const{return 2;}
 int GetParentID()const{return m_parentID;}
 void MarkDirtyRegion(){}
};
class CGUIImage {
public:
 template<class...T>CGUIImage(T...){}
 void SetCrossFade(unsigned int){}
 void SetFileName(const std::string&){}
 bool SetColorDiffuse(unsigned int){return false;}
 void DoProcess(unsigned int,CDirtyRegionList&){}
 void Render(){}
 void FreeResources(bool){}
 void DynamicResourceAlloc(bool){}
 void SetInvalid(){}
 void SetAspectRatio(const CAspectRatio&){}
 std::string GetDescription()const{return {};}
};
namespace KODI {namespace GUILIB {namespace GUIINFO {
class CGUIInfoLabel {
public:
 bool IsConstant()const{return true;}
 std::string GetLabel(int)const{return {};}
 std::string GetItemLabel(const CGUIListItem*,bool)const{return {};}
};}}namespace UTILS {template<class I>void RandomShuffle(I,I){}}}
class CStopWatch{public:void StartZero(){}bool IsRunning()const{return true;}unsigned int GetElapsedMilliseconds()const{return 0;}};
class CURL {
 std::string text,protocol,host;
public:
 explicit CURL(std::string s):text(std::move(s)){
  auto n=text.find("://");if(n!=std::string::npos){protocol=text.substr(0,n);auto p=text.find('/',n+3);host=text.substr(n+3,p==std::string::npos?p:p-n-3);}
 }
 const std::string&Get()const{return text;}
 const std::string&GetProtocol()const{return protocol;}
 const std::string&GetHostName()const{return host;}
 std::string GetRedacted()const{return text;}
 bool IsProtocol(const std::string&p)const{return protocol==p;}
 static bool IsFullPath(const std::string&p){return !p.empty()&&(p[0]=='/'||p.find("://")!=std::string::npos);}
 bool IsFileType(const std::string&)const{return false;}
};
namespace StringUtils {
inline bool StartsWith(const std::string&a,const std::string&b){return a.rfind(b,0)==0;}
inline bool StartsWithNoCase(std::string a,std::string b){std::transform(a.begin(),a.end(),a.begin(),::tolower);return a.rfind(b,0)==0;}
inline std::vector<std::string>Split(const std::string&s,const char*){return {s};}
}
namespace URIUtils {
inline std::string GetExtension(const std::string&p){auto a=p.find_last_of('.'),b=p.find_last_of('/');return a!=std::string::npos&&(b==std::string::npos||a>b)?p.substr(a):"";}
inline std::string GetExtension(const CURL&u){return GetExtension(u.Get());}
inline std::string AddFileToFolder(const std::string&a,const std::string&b){return a+"/"+b;}
inline std::string AddFileToFolder(const std::string&a,const char*b,const std::string&c){return a+"/"+b+"/"+c;}
inline void AddSlashAtEnd(std::string&p){if(p.empty()||p.back()!='/')p+='/';}
inline bool PathHasParent(const std::string&p,const std::string&parent){return p.rfind(parent,0)==0;}
}
class CFileItem {
 std::string path,mime;
public:
 bool m_bIsFolder=false;long long m_dwSize=0;int m_dateTime=0;
 CFileItem(const std::string&p,bool folder=false):path(p),m_bIsFolder(folder){}
 void FillInMimeType(){if(path.rfind("http",0)==0){++Fixture::mimeNetwork;mime="image/jpeg";}}
 bool IsPicture()const{auto e=URIUtils::GetExtension(path);return e==".png"||e==".jpg";}
 const std::string&GetMimeType()const{return mime;}
 const std::string&GetPath()const{return path;}
 const std::string&GetDynPath()const{return path;}
 void SetPath(const std::string&p){path=p;}
 void SetProperty(const char*,bool){}
};
using CFileItemPtr=std::shared_ptr<CFileItem>;
class CFileItemList {
 std::vector<CFileItemPtr>items;
public:
 int Size()const{return static_cast<int>(items.size());}
 CFileItemPtr operator[](int i){return items[i];}
 void Add(CFileItemPtr i){items.push_back(std::move(i));}
 void SetURL(const CURL&){}
};
namespace KODI {namespace TIME {using FileTime=int;inline void TimeTToFileTime(time_t,FileTime*){}inline void FileTimeToLocalFileTime(FileTime*,FileTime*){}}}
class CCharsetConverter{public:static void unknownToUTF8(std::string&){}};
class CServiceBroker;
namespace XFILE {
constexpr int DIR_FLAG_NO_FILE_DIRS=1,DIR_FLAG_NO_FILE_INFO=2,DIR_FLAG_GET_HIDDEN=4;
class CFile{public:static bool Exists(const std::string&p){return std::filesystem::exists(p);}};
class IDirectory{public:int m_flags=DIR_FLAG_NO_FILE_DIRS|DIR_FLAG_NO_FILE_INFO;std::string m_strFileMask;virtual~IDirectory()=default;virtual bool GetDirectory(const CURL&,CFileItemList&){++Fixture::unknownWork;return true;}};
class CPosixDirectory:public IDirectory{public:bool GetDirectory(const CURL&,CFileItemList&)override;};
class CSpecialProtocolDirectory:public IDirectory{public:bool GetDirectory(const CURL&,CFileItemList&)override;};
class CDirectoryFactory{public:static IDirectory*Create(const CURL&);};
class CDirectory {
public:
 static bool GetDirectory(const std::string&p,CFileItemList&i,const std::string&,int){
  auto observation=std::move(Fixture::duringDirectoryRead);if(observation)observation();
  std::unique_ptr<IDirectory>d(CDirectoryFactory::Create(CURL(p)));return d&&d->GetDirectory(CURL(p),i);
 }
 static bool Exists(const std::string&p){
  std::unique_ptr<IDirectory>d(CDirectoryFactory::Create(CURL(p)));return d&&std::filesystem::is_directory(p);
 }
};
class IFileDirectory:public IDirectory{};
class CFileDirectoryFactory {
public:
 static IFileDirectory*Create(const CURL&url,CFileItem*){
  if(Fixture::factoryThrows)throw std::runtime_error("factory peer failure");
  if(Fixture::opaqueFile&&!URIUtils::GetExtension(url).empty()){
    InfinityMultiImagePersistence::UnreviewedDispatch("multiimage_binary_vfs_dispatch_unverified");
    ++Fixture::unknownWork;std::ofstream(Fixture::root+"/opaque-peer")<<"mutation";
  }return nullptr;
 }
};
class VfsAddon{public:std::string GetProtocols()const{return "special";}bool HasDirectories()const{return true;}};
class CVFSEntryIDirectoryWrapper:public IDirectory{public:explicit CVFSEntryIDirectoryWrapper(std::shared_ptr<VfsAddon>){}};
}
namespace ADDON {}
using namespace XFILE;
class VfsCache{public:std::vector<std::shared_ptr<VfsAddon>>GetAddonInstances(){return Fixture::overrideSpecial?std::vector<std::shared_ptr<VfsAddon>>{std::make_shared<VfsAddon>()}:std::vector<std::shared_ptr<VfsAddon>>{};}};
class CWakeOnAccess{public:static CWakeOnAccess&GetInstance(){static CWakeOnAccess w;return w;}bool WakeUpHost(const CURL&){return true;}};
class CSpecialProtocol{public:static std::string TranslatePath(const CURL&u){return Fixture::root+u.Get().substr(std::string("special://fixture").size());}};
class CGUITextureManager {
public:
 CCriticalSection m_section;std::vector<std::string>m_texturePaths;
 std::string GetTexturePath(const std::string&,bool);
 std::vector<std::string>GetBundledTexturesFromPath(const std::string&){return {};}
};
class GUI{public:CGUITextureManager texture;CGUITextureManager&GetTextureManager(){return texture;}};
class Gfx{public:bool SetClipRegion(float,float,float,float){return false;}void RestoreClipRegion(){}};
class WinSystem{public:Gfx gfx;Gfx&GetGfxContext(){return gfx;}};
class TextureCache{public:bool HasCachedImage(const std::string&){return false;}};
class CFileExtensionProvider{public:std::string GetPictureExtensions(){return ".png|.jpg";}};
class CServiceBroker {
public:
 static CJobManager*manager;static GUI gui;
 static CJobManager*GetJobManager(){return manager;}
 static GUI*GetGUI(){return &gui;}
 static bool IsAddonInterfaceUp(){return true;}
 static VfsCache&GetVFSAddonCache(){static VfsCache c;return c;}
 static WinSystem*GetWinSystem(){static WinSystem w;return &w;}
 static TextureCache*GetTextureCache(){static TextureCache c;return &c;}
 static CFileExtensionProvider&GetFileExtensionProvider(){static CFileExtensionProvider e;return e;}
};
constexpr int LOGERROR=1,LOGWARNING=2,LOGDEBUG=3,LOGINFO=4;
class CLog{public:template<class...T>static void Log(T...){}};
inline bool IsAliasShortcut(const std::string&,bool){return false;}
inline void TranslateAliasShortcut(std::string&){}
'''

HARNESS=r'''
#include "Peers.h"
#define protected public
#include "guilib/GUIMultiImage.h"
#undef protected
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include <cassert>
#include <iostream>
#include <typeinfo>
#include <cstdlib>
#include <new>
bool failNextAllocation=false;
void* operator new(std::size_t size){
 if(failNextAllocation){failNextAllocation=false;throw std::bad_alloc();}
 if(void* value=std::malloc(size))return value;
 throw std::bad_alloc();
}
void operator delete(void* value)noexcept{std::free(value);}
void operator delete(void* value,std::size_t)noexcept{std::free(value);}
CJobManager*CServiceBroker::manager=nullptr;
GUI CServiceBroker::gui;
struct DerivedControl:CGUIMultiImage{using CGUIMultiImage::CGUIMultiImage;};
struct DerivedJob:CGUIMultiImage::CMultiImageJob{using CGUIMultiImage::CMultiImageJob::CMultiImageJob;};
struct Spoof: CJob{bool DoWork()override{return true;}const char*GetType()const override{return "multiimage";}};
struct NeutralCallback:IJobCallback{void OnJobComplete(unsigned int,bool,CJob*)override{}};
int main(int argc,char**argv){
 assert(argc==5);std::string scenario=argv[1];Fixture::root=argv[2];
 const bool baseline=std::string(argv[3])=="baseline";
 const bool closed=std::string(argv[4])=="close";
 Fixture::infinity=scenario!="cobra";
 CServiceBroker::manager=new CJobManager;
 CTextureInfo texture;
 CGUIMultiImage owner(1,2,0,0,10,10,texture,100,1,false,true,0);
 DerivedControl derived(1,2,0,0,10,10,texture,100,1,false,true,0);
 NeutralCallback neutral;
 owner.m_directoryStatus=CGUIMultiImage::LOADING;
 std::string path=Fixture::root+"/images/";
 if(scenario=="single")path=Fixture::root+"/images/one.png";
 if(scenario=="special"||scenario=="override")path="special://fixture/images/";
 if(scenario=="unknown")path="plugin://opaque/";
 if(scenario=="network")path="https://fixture.invalid/cover";
 if(scenario=="resource")path="resource://fixture/images/";
 if(scenario=="active-opaque")path="resource://fixture/images/";
 if(scenario=="empty")path="missing-relative";
 if(scenario=="relative")path="images/";
 if(scenario=="extension"){path="folder.pkg";Fixture::opaqueFile=true;}
 if(scenario=="dotted-local")path="folder.pkg";
 if(scenario=="override")Fixture::overrideSpecial=true;
 if(scenario=="throws")Fixture::factoryThrows=true;
 if(scenario=="active-throws")Fixture::factoryThrows=true;
 if(scenario=="relative"||scenario=="extension"||scenario=="dotted-local")CServiceBroker::gui.texture.m_texturePaths={Fixture::root+"/skin"};
 CJob*job=new CGUIMultiImage::CMultiImageJob(path);
 IJobCallback*callback=&owner;
 if(scenario=="derived-job"){delete job;job=new DerivedJob(path);}
 if(scenario=="derived-control")callback=&derived;
 if(scenario=="null")callback=nullptr;
 if(scenario=="spoof"){delete job;job=new Spoof;callback=&neutral;}
 auto id=CServiceBroker::manager->AddJob(job,callback);
 assert(id);
 owner.m_jobID=id;
 auto record=CJobManager::CheckpointRecord(job);
 auto before=CJobManager::AndroidCheckpointSnapshot();assert(before.required==1);
 if(scenario=="cobra"){
  assert(before.unknown==1);
  assert(std::string(job->GetCheckpointPersistenceOwner()).empty());
  assert(std::string(job->GetCheckpointOperation())==job->GetType());
  assert(job->GetCheckpointResource().empty());
  assert(!job->RequiresCheckpointCompletionReceipt());
  assert(!job->RequiresCheckpointCallback());
 }
 if(!baseline && scenario!="cobra" && scenario!="derived-job" && scenario!="derived-control" && scenario!="null" && scenario!="spoof"){
  assert(before.unknown==0);assert(before.blockers[0].owner=="background_jobs");
 }
 bool blocked=baseline||scenario=="cobra"||scenario=="unknown"||scenario=="network"||scenario=="resource"||
  scenario=="extension"||scenario=="override"||scenario=="throws"||scenario=="active-opaque"||scenario=="active-throws"||scenario=="callback-throws"||scenario=="derived-job"||
  scenario=="derived-control"||scenario=="null"||scenario=="spoof";
 InfinityAndroidCheckpoint::active=closed;
 if(scenario=="active-cancel"||scenario=="active-shutdown"||scenario=="active-opaque"||scenario=="active-throws"){
  Fixture::duringDirectoryRead=[&](){
   assert(CJobManager::AndroidCheckpointSnapshot().required==1);
   if(scenario=="active-shutdown")CServiceBroker::manager->BeginShutdown();
   else owner.CancelLoading();
   // A removed GUI callback never retires the running job or its obligations.
   assert(CJobManager::AndroidCheckpointSnapshot().required==1);
   assert(!record->completionRecorded);
  };
 }
 if(scenario=="cancel"){
  CServiceBroker::manager->CancelJob(id);
 }else if(scenario=="late-cancel"||scenario=="callback-throws"){
  auto* manager=CServiceBroker::manager;
  assert(manager->GetNextJob()==job);
  JobCheckpoint::WorkBinding operation(record);
  const bool success=job->DoWork();assert(success);
  assert(CJobManager::AndroidCheckpointSnapshot().required==1);
  if(scenario=="late-cancel")owner.CancelLoading();
  else failNextAllocation=true; // The original callback's vector copy must fail visibly.
  assert(!record->completionRecorded);
  manager->OnJobComplete(success,job);
  if(scenario=="callback-throws"){
   assert(!failNextAllocation); // Both candidates executed the throwing callback.
   if(!baseline)assert(!record->completionCallbackVerified);
   else assert(record->unknown&&!record->completionRecorded);
  }
 }else{
  CJobWorker worker(CServiceBroker::manager);worker.Process();
 }
  std::cerr<<"lifecycle "<<scenario
   <<" reviewed="<<record->outcomeReviewed<<" operation_succeeded="<<record->operationSucceeded
   <<" callback_verified="<<record->completionCallbackVerified<<" phase="<<record->phase<<"\n";
 record.reset(); // Observing must not keep a retired job live in the weak registry.
 auto after=CJobManager::AndroidCheckpointSnapshot();
 assert((after.required!=0)==blocked);
 if(!blocked)assert(after.unknown==0);
 if(!baseline&&blocked&&scenario!="cobra"&&scenario!="derived-job"&&scenario!="derived-control"&&scenario!="null"&&scenario!="spoof"&&scenario!="callback-throws"){
  assert(after.blockers[0].phase=="completed_write_failed");
  assert(after.blockers[0].failureDetail.find("multiimage_")==0);
 }
 if(scenario=="single"&&!blocked)assert(owner.m_files==std::vector<std::string>{path});
 if(scenario=="local"&&!blocked)assert(owner.m_files.size()==2);
 if(scenario=="cobra")assert(owner.m_files.size()==2);
 if(scenario=="special"&&!blocked)assert(owner.m_files.size()==2);
 if(scenario=="extension")assert(Fixture::unknownWork>0);
 if(scenario=="network")assert(Fixture::mimeNetwork==1);
 std::ifstream input(Fixture::root+"/sentinel");std::string value;input>>value;assert(value=="preserved");
 std::cout<<"PASS "<<scenario<<" "<<(closed?"close":"normal")<<" required="<<after.required<<"\n";
}
'''


def function(source, anchor):
    at=source.index(anchor);start=source.index('{',at);depth=0
    # Selected functions do not contain brace-bearing string literals.
    for end in range(start,len(source)):
        if source[end]=='{':depth+=1
        elif source[end]=='}':
            depth-=1
            if depth==0:return source[at:end+1]
    raise RuntimeError('Function boundary not found')


def run(source, overlay, baseline, out):
    legacy=ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/test_job_manager_runtime.py'
    spec=importlib.util.spec_from_file_location('retained_job_peers',legacy)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def data(name):
        candidate=overlay/name
        return (source/name if baseline or not candidate.exists() else candidate).read_text()
    with tempfile.TemporaryDirectory(prefix='actual-multiimage-') as folder:
        work=Path(folder)
        def put(name,content):
            target=work/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
        for name in ('Job.h','JobManager.h','JobManager.cpp','JobCheckpoint.h'):
            content=data('xbmc/utils/'+name)
            # Expose protected lifecycle entry points only in this disposable
            # harness header; CJobManager remains final and its bodies unchanged.
            if name=='JobManager.h':content=content.replace('protected:', 'public:')
            put('utils/'+name,content)
        for name,content in module.STUBS.items():
            if name in ('ServiceBroker.h','utils/log.h'):continue
            if name.endswith('InfinityAndroidCheckpoint.h'):
                content=content.replace('s=="playback"||s=="native_databases"','s=="playback"||s=="native_databases"||s=="background_jobs"')
                content=content.replace('inline bool IsActive(){return active;}',
                    'inline bool IsActive(){return active;}inline bool IsWriteAdmissionActive(){return active;}')
            put(name,content)
        for name in ('GUIMultiImage.h','GUIMultiImage.cpp'):
            put('guilib/'+name,data('xbmc/guilib/'+name))
        put('guilib/InfinityMultiImagePersistence.h',(HERE/'InfinityMultiImagePersistence.h').read_text())
        handler=data('xbmc/filesystem/DirectoryFactory.cpp')
        concrete=sorted(set(__import__('re').findall(r'new (C\w+)\(',handler))-
                        {'CPosixDirectory','CSpecialProtocolDirectory','CVFSEntryIDirectoryWrapper'})
        declarations='\n'.join('namespace XFILE {class '+n+':public IDirectory{};}' for n in concrete)
        put('Peers.h',PEERS+'\n'+declarations)
        for name in ('GUIImage.h','FileItem.h','GUIMessage.h','ServiceBroker.h','TextureCache.h','TextureManager.h',
                     'WindowIDs.h','filesystem/Directory.h','utils/FileExtensionProvider.h','utils/Random.h',
                     'utils/StringUtils.h','utils/URIUtils.h','utils/Stopwatch.h','utils/log.h','URL.h'):
            put(name,'#pragma once\n#include "Peers.h"\n')
            if name=='GUIImage.h':put('guilib/GUIImage.h','#pragma once\n#include "Peers.h"\n')
        put('interfaces/legacy/ModuleXbmc.h','#pragma once\n#include "Peers.h"\n')
        factories='#include "Peers.h"\n#include "guilib/InfinityMultiImagePersistence.h"\nusing namespace XFILE;\n'
        factories+=function(handler,'IDirectory* CDirectoryFactory::Create(const CURL& url)')
        factories+='\n'+function((source/'xbmc/platform/posix/filesystem/PosixDirectory.cpp').read_text(),
                                 'bool CPosixDirectory::GetDirectory(const CURL& url')
        factories+='\n'+function((source/'xbmc/filesystem/SpecialProtocolDirectory.cpp').read_text(),
                                 'bool CSpecialProtocolDirectory::GetDirectory(const CURL& url')
        factories+='\n'+function((source/'xbmc/guilib/TextureManager.cpp').read_text(),
                                 'std::string CGUITextureManager::GetTexturePath(')
        put('factory.cpp',factories)
        put('test.cpp',HARNESS)
        executable=work/'test'
        command=['g++','-std=c++17','-DTARGET_ANDROID','-DTARGET_POSIX','-Wall','-Wextra','-Werror',
                 '-Wno-unused-parameter','-pthread','-I',str(work),str(work/'utils/JobManager.cpp'),
                 str(work/'guilib/GUIMultiImage.cpp'),str(work/'factory.cpp'),str(work/'test.cpp'),'-o',str(executable)]
        build=subprocess.run(command,text=True,capture_output=True)
        if build.returncode:raise RuntimeError(build.stdout+build.stderr)
        fixture=work/'fixture';(fixture/'images').mkdir(parents=True)
        (fixture/'images/one.png').write_bytes(b'one');(fixture/'images/two.jpg').write_bytes(b'two')
        (fixture/'skin/media/images').mkdir(parents=True)
        (fixture/'skin/media/folder.pkg').mkdir()
        (fixture/'skin/media/images/one.png').write_bytes(b'one')
        (fixture/'sentinel').write_text('preserved')
        scenarios=('local','single','special','relative','empty','unknown','network','resource','extension','dotted-local','override',
                   'throws','derived-job','derived-control','null','spoof','cancel','cobra',
                   'active-cancel','active-shutdown','active-opaque','active-throws','late-cancel','callback-throws')
        results=[]
        for scenario in scenarios:
            for phase in ('normal','close'):
                result=subprocess.run([str(executable),scenario,str(fixture),'baseline' if baseline else 'candidate',phase],
                                      text=True,capture_output=True,timeout=10)
                results.append(dict(scenario=scenario,phase=phase,passed=result.returncode==0,
                                    stdout=result.stdout,stderr=result.stderr))
                if result.returncode:
                    out.write_text(json.dumps(dict(passed=False,baseline=baseline,
                        executed_cases=len(results),planned_cases=len(scenarios)*2,
                        results=results,physical_fold_verified=False),indent=2)+'\n')
                    print(json.dumps(results[-1],indent=2));raise RuntimeError('Native contract case failed')
        report=dict(passed=True,baseline=baseline,cases=len(results),scope=__doc__,results=results,
                    executed_production_functions=['complete GUIMultiImage.cpp and header','complete JobManager.cpp',
                        'DirectoryFactory::Create(CURL)','CPosixDirectory::GetDirectory',
                        'CSpecialProtocolDirectory::GetDirectory','CGUITextureManager::GetTexturePath'],
                    physical_fold_verified=False)
        out.write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',len(results),'production-source cases; baseline=',baseline)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--overlay',type=Path,required=True)
    p.add_argument('--baseline',action='store_true');p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.source,a.overlay,a.baseline,a.out)
