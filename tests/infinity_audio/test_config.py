#!/usr/bin/env python3
"""Compile real policy + Kodi Variant/JSON parser; fake only filesystem/log I/O.

Requires rapidjson headers (CI: rapidjson-dev). No Android/Samsung runtime claim.
"""
from pathlib import Path
import argparse
import subprocess
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2]
src=a.out/'stubs';(src/'filesystem').mkdir(parents=True,exist_ok=True);(src/'utils').mkdir(parents=True,exist_ok=True)
(src/'filesystem/File.h').write_text('''#pragma once
#include <cstdlib>
#include <cstdint>
#include <fstream>
namespace XFILE { class CFile {
 std::ifstream stream; int64_t length=0;
public:
 bool Open(const char*) {const char* p=std::getenv("INFINITY_TEST_CONFIG");if(!p)return false;stream.open(p,std::ios::binary);if(!stream)return false;stream.seekg(0,std::ios::end);length=stream.tellg();stream.seekg(0);return true;}
 int64_t GetLength(){return length;}
 int64_t Read(void* data,size_t size){stream.read(static_cast<char*>(data),size);return stream.gcount();}
};}
''')
(src/'utils/log.h').write_text('''#pragma once
constexpr int LOGINFO=1,LOGWARNING=2;
struct CLog {template<typename... T> static void Log(int,const char*,T...) {}};
''')
test=a.out/'config-test.cpp'
test.write_text(r'''#include "InfinityAudioPolicy.h"
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <string>
#include <cstdio>
using namespace INFINITY_AUDIO;
void write(const std::string& s){std::ofstream f(std::getenv("INFINITY_TEST_CONFIG"));f<<s;f.close();Reload();}
int main(int argc,char**argv){
 assert(argc==2);setenv("INFINITY_TEST_CONFIG",argv[1],1);std::remove(argv[1]);Reload();
 assert(Resolve(MOVIE)==MOVIE&&Resolve(MUSIC)==MUSIC&&Resolve(SONIFICATION)==SONIFICATION);
 uint32_t old=Revision();Reload();assert(Revision()==old);
 write(R"({"schema":1,"video":"music","music":"music","ui":"music"})");
 assert(Resolve(MOVIE)==MUSIC&&Resolve(SONIFICATION)==MUSIC&&Revision()>old);
 write(R"({"schema":1,"video":"speech","music":"music","ui":"sonification"})");assert(Resolve(MOVIE)==SPEECH);
 write(R"({"schema":1,"video":"invalid","music":true,"ui":99})");assert(Resolve(MOVIE)==MOVIE&&Resolve(MUSIC)==MUSIC&&Resolve(SONIFICATION)==SONIFICATION);
 for(const char* bad:{"{","[]","null",R"({"schema":2,"video":"music"})",R"({"schema":true,"video":"music"})",R"({"schema":"1","video":"music"})"}){
  write(bad);assert(Resolve(MOVIE)==MOVIE);
 }
 write(std::string(4097,' '));assert(Resolve(MOVIE)==MOVIE);
 write("");assert(Resolve(MOVIE)==MOVIE);
 write(R"({"schema":1,"video":"music"})");assert(Resolve(MOVIE)==MUSIC);
 std::remove(argv[1]);Reload();assert(Resolve(MOVIE)==MOVIE);
 NoteTrack(MOVIE);assert(TrackContent()==MOVIE);
 std::puts("PASS: actual native policy + Kodi JSON parser defaults, schema, bounds, bad input, legacy, revision and missing file");
}
''')
exe=a.out/'config-test'
# Upstream Kodi callbacks deliberately name unused parameters. Keep those warnings
# visible without promoting them to errors, only for the two unchanged upstream
# translation units. Infinity policy and test code still compile with -Werror.
common = ['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
          '-I' + str(src), '-I' + str(root / 'patches/infinity-audio-policy'),
          '-I' + str(a.source / 'xbmc')]
objects = []
for filename in ('Variant.cpp', 'JSONVariantParser.cpp'):
    obj = a.out / (filename + '.o')
    subprocess.run(common + ['-Wno-error=unused-parameter', '-c',
                            str(a.source / 'xbmc/utils' / filename),
                            '-o', str(obj)], check=True)
    objects.append(str(obj))
subprocess.run(common + [str(root / 'patches/infinity-audio-policy/InfinityAudioPolicy.cpp'),
                         str(test), *objects, '-o', str(exe)], check=True)
subprocess.run([str(exe.resolve()), str((a.out / 'config.json').resolve())], check=True)
