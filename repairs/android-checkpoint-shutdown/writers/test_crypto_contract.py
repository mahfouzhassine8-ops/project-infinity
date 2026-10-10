#!/usr/bin/env python3
"""Check native crypto evidence against signed APK bytes; never execute ARM64 on host."""
import argparse,json,subprocess,sysconfig,tempfile,zipfile,os,sys
from pathlib import Path
HEADER=r'''
#include <Python.h>
#include <cerrno>
#include <climits>
#include <cstring>
#include <cstdlib>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
#include <string>
#include <cassert>
#include <fstream>
namespace InfinityPythonPersistence {std::string Path(PyObject* v){return PyUnicode_Check(v)?PyUnicode_AsUTF8(v):"";}}
#include "InfinityPythonCryptoContract.h"
int main(int argc,char**argv){assert(argc==2);std::string root=argv[1];setenv("KODI_ANDROID_LIBS",root.c_str(),1);
using namespace InfinityPythonPersistence;
for(const auto& image:CryptoImages()){
 const auto path=root+"/"+image.name;
 assert(ApprovedCryptoImage(path));assert(!ApprovedCryptoImage(path,"open"));assert(!ApprovedCryptoImage(root+"/../"+root.substr(root.rfind('/')+1)+"/"+image.name));
 std::ifstream in(path,std::ios::binary);std::string bytes((std::istreambuf_iterator<char>(in)),{});in.close();
 {std::ofstream out(path,std::ios::binary|std::ios::app);out.put('x');}assert(!ApprovedCryptoImage(path));
 {std::ofstream out(path,std::ios::binary|std::ios::trunc);out.write(bytes.data(),bytes.size());}assert(ApprovedCryptoImage(path));
 assert(::rename(path.c_str(),(path+".real").c_str())==0);assert(::symlink((path+".real").c_str(),path.c_str())==0);assert(!ApprovedCryptoImage(path));
 assert(::unlink(path.c_str())==0);assert(::rename((path+".real").c_str(),path.c_str())==0);
}
assert(!ApprovedCryptoImage(root+"/libUnreviewed.so"));
Py_Initialize();auto* a=PyTuple_Pack(1,Py_None);assert(ApprovedNativeLookup("ctypes.dlopen",a));Py_DECREF(a);
a=Py_BuildValue("(s)","/tmp/unreviewed.so");assert(!ApprovedNativeLookup("ctypes.dlopen",a));Py_DECREF(a);
a=Py_BuildValue("(ks)",0UL,"ghash_portable");assert(!ApprovedNativeLookup("ctypes.dlsym/handle",a));Py_DECREF(a);Py_FinalizeEx();
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--apk',type=Path,required=True);a=p.parse_args()
 audit=json.loads((Path(__file__).parent.parent/'CRYPTO-2103362-AUDIT.json').read_text())
 with tempfile.TemporaryDirectory(prefix='crypto-pins-') as tmp:
  tmp=Path(tmp);libs=tmp/'libs';libs.mkdir()
  with zipfile.ZipFile(a.apk) as z:
   for image in audit['libraries']:
    name=image['library'];(libs/name).write_bytes(z.read('lib/arm64-v8a/'+name))
  (tmp/'test.cpp').write_text(HEADER)
  folder=Path(sysconfig.get_config_var('LIBDIR'));lib=folder/sysconfig.get_config_var('LDLIBRARY')
  if not lib.exists():lib=folder/(sysconfig.get_config_var('LDLIBRARY')+'.1.0')
  if not lib.exists():
   folder=Path(sys.prefix)/'lib';lib=folder/sysconfig.get_config_var('LDLIBRARY')
   if not lib.exists():lib=folder/(sysconfig.get_config_var('LDLIBRARY')+'.1.0')
  flags=[str(lib),'-lm','-pthread','-Wl,-rpath,'+str(folder)]
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I'+sysconfig.get_path('include'),'-I'+str(a.runtime/'xbmc/interfaces/python'),str(tmp/'test.cpp'),'-o',str(tmp/'test'),'-lcrypto','-ldl',*flags],check=True)
  subprocess.run([str(tmp/'test'),str(libs)],check=True)
 print('PASS: 18 signed crypto images; tampering, symlinks, path aliases, unknown symbols and invalid handles rejected')
if __name__=='__main__':main()
