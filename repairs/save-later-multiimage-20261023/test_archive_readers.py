"""Execute unchanged APK enumeration/libzip 1.8.0 and XBT reader/manager code."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

from test_native import function

PEERS = r'''
#pragma once
#include <algorithm>
#include <cstdio>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
using CCriticalSection=std::recursive_mutex;
class CURL {
 std::string host,path;
public:
 CURL(std::string h,std::string p="images"):host(std::move(h)),path(std::move(p)){}
 const std::string&GetHostName()const{return host;}
 const std::string&GetFileName()const{return path;}
 const std::string&Get()const{return host;}
 bool IsProtocol(const std::string&p)const{return p=="xbt";}
};
namespace StringUtils {inline bool StartsWith(const std::string&a,const std::string&b){return a.rfind(b,0)==0;}}
namespace URIUtils {inline void AddSlashAtEnd(std::string&p){if(p.empty()||p.back()!='/')p+='/';}}
class CFileItem {
 std::string path;
public:
 explicit CFileItem(std::string s):path(std::move(s)){}
 long long m_dwSize=0,m_dateTime=0;bool m_bIsFolder=false;
 void SetPath(const std::string&s){path=s;}
 const std::string&GetPath()const{return path;}
 void SetLabel(const std::string&){}
};
using CFileItemPtr=std::shared_ptr<CFileItem>;
class CFileItemList {
 std::vector<CFileItemPtr>items;
public:
 bool Contains(const std::string&p)const{for(const auto&i:items)if(i->GetPath()==p)return true;return false;}
 void Add(CFileItemPtr p){items.push_back(std::move(p));}
 size_t Size()const{return items.size();}
};
struct Charset {void unknownToUTF8(std::string&)const{}};
inline Charset g_charsetConverter;
constexpr int LOGERROR=1;
struct CLog {template<class...T>static void Log(T...){}};
namespace XFILE {class CAPKDirectory {public:bool GetDirectory(const CURL&,CFileItemList&);};}
'''

MAIN = r'''
#include "Peers.h"
#include "filesystem/XbtManager.h"
#include <cassert>
#include <iostream>
int main(int argc,char**argv){
 assert(argc==2);std::string root=argv[1];
 for(int repeat=0;repeat<3;++repeat){
  XFILE::CAPKDirectory apk;
  CFileItemList items;assert(apk.GetDirectory(CURL(root+"/valid.apk"),items));assert(items.Size()==2);
  CFileItemList empty;assert(apk.GetDirectory(CURL(root+"/empty.apk"),empty));assert(empty.Size()==0);
  CFileItemList bad;assert(!apk.GetDirectory(CURL(root+"/bad.apk"),bad));
  CFileItemList missing;assert(!apk.GetDirectory(CURL(root+"/missing.apk"),missing));
  auto&manager=XFILE::CXbtManager::GetInstance();std::vector<CXBTFFile>files;
  assert(manager.GetFiles(CURL(root+"/valid.xbt"),files));assert(files.size()==1);
  assert(files[0].GetPath()=="images/one.png");
  assert(manager.HasFiles(CURL(root+"/valid.xbt")));
  manager.Release(CURL(root+"/valid.xbt"));
  files.clear();assert(manager.GetFiles(CURL(root+"/empty.xbt"),files));assert(files.empty());
  manager.Release(CURL(root+"/empty.xbt"));
  assert(!manager.GetFiles(CURL(root+"/bad.xbt"),files));
  assert(!manager.GetFiles(CURL(root+"/missing.xbt"),files));
 }
 std::cout<<"PASS actual APK/libzip and XBT manager/readers: valid, empty, malformed, missing, reopen\n";
}
'''


def run(source, libzip_source, libzip_build, out):
    with tempfile.TemporaryDirectory(prefix='actual-archive-readers-') as directory:
        work=Path(directory)
        def put(name,value):
            target=work/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value)
        put('Peers.h',PEERS)
        paths=['guilib/XBTF.h','guilib/XBTF.cpp','guilib/XBTFReader.h','guilib/XBTFReader.cpp',
               'guilib/TextureFormats.h','utils/EndianSwap.h','filesystem/XbtManager.h','filesystem/XbtManager.cpp']
        for name in paths:put(name,(source/'xbmc'/name).read_text())
        for name in ('URL.h','threads/CriticalSection.h'):put(name,'#include "Peers.h"\n')
        apk_source=source/'xbmc/platform/android/filesystem/APKDirectory.cpp'
        put('apk.cpp','#include "Peers.h"\n#include <zip.h>\nusing namespace XFILE;\n'+
            function(apk_source.read_text(),'bool CAPKDirectory::GetDirectory('))
        put('main.cpp',MAIN)
        exe=work/'test'
        command=['g++','-std=c++17','-DTARGET_POSIX','-Wall','-Wextra','-Werror','-pthread','-include','cstdio',
            '-I',str(work),'-I',str(libzip_source/'lib'),'-I',str(libzip_build),
            str(work/'apk.cpp'),str(work/'guilib/XBTF.cpp'),str(work/'guilib/XBTFReader.cpp'),
            str(work/'filesystem/XbtManager.cpp'),str(work/'main.cpp'),str(libzip_build/'lib/libzip.a'),'-lz','-o',str(exe)]
        build=subprocess.run(command,capture_output=True,text=True)
        if build.returncode:raise RuntimeError(build.stdout+build.stderr)
        fixture=work/'fixture';fixture.mkdir()
        with zipfile.ZipFile(fixture/'valid.apk','w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('images/one.png',b'one');z.writestr('images/two.jpg',b'two');z.writestr('elsewhere/keep',b'keep')
        with zipfile.ZipFile(fixture/'empty.apk','w'):pass
        (fixture/'bad.apk').write_bytes(b'malformed archive')
        (fixture/'valid.xbt').write_bytes(b'XBTF2'+struct.pack('<I',1)+
            b'images/one.png'.ljust(256,b'\0')+struct.pack('<II',0,0))
        (fixture/'empty.xbt').write_bytes(b'XBTF2'+struct.pack('<I',0))
        (fixture/'bad.xbt').write_bytes(b'malformed texture bundle')
        snapshot=lambda:{p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            mtime_ns=p.stat().st_mtime_ns,mode=p.stat().st_mode) for p in fixture.iterdir()}
        before=snapshot();result=subprocess.run([str(exe),str(fixture)],capture_output=True,text=True,timeout=15)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        if before!=snapshot():raise RuntimeError('Archive readers mutated persistent fixture data')
        report=dict(passed=True,cases=24,scope=__doc__,stdout=result.stdout,
            source_sha256={n:hashlib.sha256((source/'xbmc'/n).read_bytes()).hexdigest() for n in paths},
            apk_source_sha256=hashlib.sha256(apk_source.read_bytes()).hexdigest(),
            unchanged_data_and_mtime=True,actual_android=False,physical_fold=False)
        out.write_text(json.dumps(report,indent=2)+'\n');print(result.stdout.strip())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','libzip-source','libzip-build','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.source,a.libzip_source,a.libzip_build,a.out)
