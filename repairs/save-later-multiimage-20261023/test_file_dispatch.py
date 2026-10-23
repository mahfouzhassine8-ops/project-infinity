"""Execute actual FileDirectoryFactory branches with explicitly opaque mutating peers."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from test_native import function

PEERS=r'''
#include <algorithm>
#include <fstream>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <cassert>
#include "guilib/InfinityMultiImagePersistence.h"
namespace Fixture {inline std::string scenario,root;inline int calls=0;
inline void opaque(){++calls;std::ofstream(root+"/opaque-write")<<"persistent mutation";}}
class CURL {public:bool IsProtocol(const std::string&)const{return false;}bool IsFileType(const std::string&)const{return false;}};
namespace URIUtils {inline std::string GetExtension(const CURL&){return ".pkg";}
inline bool HasSlashAtEnd(const std::string&){return false;}
inline CURL CreateArchivePath(const std::string&,const CURL&u){return u;}}
namespace StringUtils {inline void ToLower(std::string&){}inline bool EndsWith(const std::string&,const char*){return false;}
inline std::vector<std::string>Split(const std::string&s,const char*){return{s};}}
constexpr auto KODI_ADDON_AUDIODECODER_TRACK_EXT=".track";
constexpr int LOGINFO=1,DIR_FLAG_DEFAULTS=0;
struct CLog {template<class...T>static void Log(T...){}};
class CFileItem {public:bool m_bIsFolder=false;int m_idepth=0;
 bool IsRSS()const{return Fixture::scenario=="rss";}bool IsDiscImage()const{return false;}
 bool IsAudioBook()const{return Fixture::scenario=="audiobook";}
 bool HasMusicInfoTag()const{return false;}int GetEndOffset()const{return 0;}
 CURL GetURL()const{return {};}
 std::string GetPath()const{return "folder.pkg";}void SetPath(const std::string&){}void SetURL(const CURL&){}
 void SetLabel(const std::string&){}void SetLabelPreformatted(bool){}
};
class CFileItemList {public:int Size()const{return 0;}std::shared_ptr<CFileItem>operator[](int){return std::make_shared<CFileItem>();}
 std::string GetPath()const{return {};}};
namespace ADDON {
struct AddonInfo{std::string ID()const{return "opaque.fixture";}};
struct Vfs{bool HasFileDirectories()const{return true;}std::string GetExtensions()const{return ".pkg";}};
}
namespace KODI {namespace ADDONS {}}
namespace XFILE {
class IFileDirectory {public:virtual~IFileDirectory()=default;virtual bool GetDirectory(const CURL&,CFileItemList&){Fixture::opaque();return false;}};
class CFileDirectoryFactory {public:static IFileDirectory*Create(const CURL&,CFileItem*,const std::string&);};
class CAudioDecoder:public IFileDirectory {public:explicit CAudioDecoder(std::shared_ptr<ADDON::AddonInfo>){}
 bool CreateDecoder(){Fixture::opaque();return false;}bool ContainsFiles(const CURL&){Fixture::opaque();return false;}};
class CVFSEntryIFileDirectoryWrapper:public IFileDirectory {public:CFileItemList m_items;
 explicit CVFSEntryIFileDirectoryWrapper(std::shared_ptr<ADDON::Vfs>){}
 bool ContainsFiles(const CURL&){Fixture::opaque();return false;}};
class CRSSDirectory:public IFileDirectory{};class CAPKDirectory:public IFileDirectory{};
class CZipDirectory:public IFileDirectory{};class CXbtDirectory:public IFileDirectory{};
class CSmartPlaylistDirectory:public IFileDirectory{};class CPlaylistFileDirectory:public IFileDirectory{};
class CAudioBookFileDirectory:public IFileDirectory{public:bool ContainsFiles(const CURL&){Fixture::opaque();return false;}};
struct CDirectory{static bool GetDirectory(const CURL&,CFileItemList&,const std::string&,int){return false;}};
}
namespace PLAYLIST {
struct CPlayListFactory{static bool IsPlaylist(const CURL&){return Fixture::scenario=="playlist";}};
struct CSmartPlaylist{bool OpenAndReadName(const CURL&){Fixture::opaque();return false;}std::string GetName()const{return {};}};
}
struct CExtsMimeSupportList {
 enum class FilterSelect{hasTracks};
 std::map<int,std::shared_ptr<ADDON::AddonInfo>>GetExtensionSupportedAddonInfos(const std::string&,FilterSelect){
  if(Fixture::scenario=="audio")return{{0,std::make_shared<ADDON::AddonInfo>()}};return {};}
};
struct VfsCache {std::vector<std::shared_ptr<ADDON::Vfs>>GetAddonInstances(){
 if(Fixture::scenario=="vfs")return{std::make_shared<ADDON::Vfs>()};return {};}};
struct CServiceBroker {
 static bool IsAddonInterfaceUp(){return true;}
 static CExtsMimeSupportList&GetExtsMimeSupportList(){static CExtsMimeSupportList s;return s;}
 static VfsCache&GetVFSAddonCache(){static VfsCache v;return v;}
};
using namespace ADDON;using namespace KODI::ADDONS;using namespace XFILE;using namespace PLAYLIST;
'''
CHECKPOINT=r'''
#pragma once
#include <memory>
#include <string>
enum class CJobDurability{Pending,VerifiedUnchanged,Unresolved};
struct CJobCheckpointRecord{bool unknown=false;std::string owner="background_jobs",operation="multiimage-enumeration",failure;
CJobDurability durability=CJobDurability::Pending;};
namespace JobCheckpoint {
inline thread_local std::shared_ptr<CJobCheckpointRecord>currentOperation;
inline void WorkResult(const std::shared_ptr<CJobCheckpointRecord>&r,CJobDurability d,bool,const std::string&f){if(r){r->durability=d;r->failure=f;}}
}
'''
MAIN=r'''
int main(int argc,char**argv){
 assert(argc==3);Fixture::scenario=argv[1];Fixture::root=argv[2];
 auto record=std::make_shared<CJobCheckpointRecord>();JobCheckpoint::currentOperation=record;
 InfinityMultiImagePersistence::Scope scope(record);CFileItem item;
 std::unique_ptr<IFileDirectory> result(CFileDirectoryFactory::Create(CURL(),&item,""));
 bool unchanged=scope.Finish(true);
 assert(unchanged==(Fixture::scenario=="plain"));
 if(Fixture::scenario=="plain")assert(Fixture::calls==0);
 else if(Fixture::scenario!="rss")assert(Fixture::calls==1);
 if(!unchanged)assert(record->failure.find("multiimage_")==0);
}
'''

def run(source,overlay,out):
    original=(source/'xbmc/filesystem/FileDirectoryFactory.cpp').read_text()
    changed=(overlay/'xbmc/filesystem/FileDirectoryFactory.cpp').read_text()
    body=function(changed,'IFileDirectory* CFileDirectoryFactory::Create(')
    with tempfile.TemporaryDirectory(prefix='actual-file-dispatch-') as directory:
        work=Path(directory);(work/'guilib').mkdir();(work/'utils').mkdir()
        (work/'utils/JobCheckpoint.h').write_text(CHECKPOINT)
        (work/'guilib/InfinityMultiImagePersistence.h').write_text((overlay/'xbmc/guilib/InfinityMultiImagePersistence.h').read_text())
        (work/'test.cpp').write_text(PEERS+body+MAIN)
        exe=work/'test';result=subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror',
            '-Wno-misleading-indentation','-I',str(work),str(work/'test.cpp'),'-o',str(exe)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        cases=[]
        for name in ('plain','audio','vfs','rss','playlist','audiobook'):
            target=work/name;target.mkdir()
            result=subprocess.run([str(exe),name,str(target)],capture_output=True,text=True,timeout=10)
            if result.returncode:raise RuntimeError(name+': '+result.stdout+result.stderr)
            mutation=(target/'opaque-write').exists()
            assert mutation==(name not in ('plain','rss'))
            cases.append(dict(case=name,passed=True,opaque_persistent_effect=mutation,verified_unchanged=name=='plain'))
        # No changes to original calls, arguments, returns or control flow:
        # remove added observation statements and include, compare byte-for-byte.
        import re
        cleaned=re.sub(r'#if defined\(TARGET_ANDROID\)\n(?:#include "guilib/InfinityMultiImagePersistence.h"|    InfinityMultiImagePersistence::UnreviewedDispatch\("[^"]+"\);)\n#endif\n','',changed)
        cleaned=cleaned.replace('  if (pItem->IsRSS())\n  {\n    return new CRSSDirectory();\n  }','  if (pItem->IsRSS())\n    return new CRSSDirectory();')
        assert cleaned==original,'Original dispatch semantics changed'
        out.write_text(json.dumps(dict(passed=True,cases=cases,original_dispatch_preserved=True,
            scope=__doc__,actual_android=False),indent=2)+'\n')
        print('PASS',len(cases),'actual file factory dispatch cases')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','overlay','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.source,a.overlay,a.out)
