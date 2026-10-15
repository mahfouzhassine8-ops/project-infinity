#!/usr/bin/env python3
"""Compile the exact native entry wrapper with controlled JNI/native peers.

Tests callback decisions, not Android ABI/lifecycle or complete engine linkage.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parents[1]
FAKE_ACTIVITY='''#pragma once
#include <jni.h>
#include <cstddef>
// Test-only struct: fields used by the wrapper. This is NOT an Android ABI test.
struct ANativeActivity { JNIEnv* env; jobject clazz; };
'''
HARNESS=r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdarg>
#include <iostream>
#include "InfinityNativeActivityEntry.h"
namespace {
bool pending=false, failClass=false, throwClass=false, failMethod=false, throwMethod=false, throwCall=false;
jboolean answer=JNI_FALSE;
int classes=0,methods=0,calls=0,deletes=0,clears=0,glue=0;
void* stateExpected=nullptr;size_t sizeExpected=0;ANativeActivity* activityExpected=nullptr;
jboolean exceptionCheck(JNIEnv*) { return pending ? JNI_TRUE : JNI_FALSE; }
void exceptionClear(JNIEnv*) { pending=false;++clears; }
jclass objectClass(JNIEnv*,jobject) {
 ++classes;if(throwClass)pending=true;
 return failClass ? nullptr : reinterpret_cast<jclass>(uintptr_t{1});
}
jmethodID methodId(JNIEnv*,jclass,const char* name,const char* signature) {
 ++methods;assert(std::strcmp(name,"infinityPrepareNativeTask")==0);assert(std::strcmp(signature,"()Z")==0);
 if(throwMethod)pending=true;
 return failMethod ? nullptr : reinterpret_cast<jmethodID>(uintptr_t{2});
}
jboolean call(JNIEnv*,jobject,jmethodID,va_list) { ++calls;if(throwCall)pending=true;return answer; }
void deleteRef(JNIEnv*,jobject value) { assert(value!=nullptr);++deletes; }
void reset(){ pending=failClass=throwClass=failMethod=throwMethod=throwCall=false;
 answer=JNI_FALSE;classes=methods=calls=deletes=clears=glue=0; }
}
extern "C" void ANativeActivity_onCreate(ANativeActivity* a,void* state,size_t length) {
 assert(a==activityExpected&&state==stateExpected&&length==sizeExpected);
 assert(!pending&&deletes==1);++glue;
}
int main() {
 JNINativeInterface_ table{};table.ExceptionCheck=exceptionCheck;table.ExceptionClear=exceptionClear;
 table.GetObjectClass=objectClass;table.GetMethodID=methodId;table.CallBooleanMethodV=call;table.DeleteLocalRef=deleteRef;
 JNIEnv env{};env.functions=&table;
 ANativeActivity activity{&env,reinterpret_cast<jobject>(uintptr_t{3})};
 int saved=7;stateExpected=&saved;sizeExpected=sizeof(saved);activityExpected=&activity;
 auto invoke=[&](){ InfinityNativeActivity_onCreate(&activity,&saved,sizeof(saved)); };
 reset();InfinityNativeActivity_onCreate(nullptr,nullptr,0);assert(glue==0&&classes==0);
 reset();activity.env=nullptr;invoke();assert(glue==0&&classes==0);activity.env=&env;
 reset();activity.clazz=nullptr;invoke();assert(glue==0&&classes==0);activity.clazz=reinterpret_cast<jobject>(uintptr_t{3});
 reset();pending=true;invoke();assert(glue==0&&classes==0&&pending);
 reset();failClass=true;invoke();assert(glue==0&&methods==0&&deletes==0);
 reset();throwClass=true;invoke();assert(glue==0&&methods==0&&deletes==1&&clears==1&&!pending);
 reset();failClass=true;throwClass=true;invoke();assert(glue==0&&deletes==0&&clears==1&&!pending);
 reset();failMethod=true;invoke();assert(glue==0&&calls==0&&deletes==1);
 reset();throwMethod=true;invoke();assert(glue==0&&calls==0&&clears==1&&!pending);
 reset();failMethod=true;throwMethod=true;invoke();assert(glue==0&&calls==0&&clears==1&&!pending);
 reset();answer=JNI_FALSE;invoke();assert(glue==0&&calls==1&&deletes==1&&clears==0);
 reset();answer=JNI_TRUE;invoke();assert(glue==1&&calls==1&&deletes==1&&clears==0);
 reset();answer=JNI_TRUE;throwCall=true;invoke();assert(glue==0&&calls==1&&deletes==1&&clears==1&&!pending);
 reset();answer=JNI_FALSE;throwCall=true;invoke();assert(glue==0&&clears==1&&!pending);
 std::cout<<"PASS: 14 native entry decisions with controlled JNI peers\n";
}
'''

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    javac=shutil.which('javac');compiler=shutil.which('g++')
    if not javac or not compiler:raise RuntimeError('JDK and C++ compiler required')
    jhome=Path(javac).resolve().parents[1]
    source=HERE/'InfinityNativeActivityEntry.h'
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp);(folder/'android').mkdir()
        (folder/'android/native_activity.h').write_text(FAKE_ACTIVITY)
        shutil.copyfile(source,folder/source.name);(folder/'test.cpp').write_text(HARNESS)
        result=subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror','-pedantic',
            '-I'+str(jhome/'include'),'-I'+str(jhome/'include/linux'),'-I'+str(folder),
            str(folder/'test.cpp'),'-o',str(folder/'test')],capture_output=True,text=True)
        (args.out/'native-entry-compile.log').write_text(result.stdout+result.stderr)
        if result.returncode:raise RuntimeError('Native wrapper test compilation failed; inspect native-entry-compile.log')
        ran=subprocess.run([str(folder/'test')],capture_output=True,text=True)
        (args.out/'native-entry.log').write_text(ran.stdout+ran.stderr)
        if ran.returncode:raise RuntimeError('Native wrapper test failed')
    report={'tests':14,'failures':0,'errors':0,'skipped':0,'passed':True,
        'wrapper_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope':'Exact wrapper compiled with actual JDK JNI types and controlled Android struct/glue peers; not Android ABI or full-engine compilation.'}
    (args.out/'native-entry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
