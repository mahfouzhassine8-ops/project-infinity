"""Source-bound counterexample for the independently reviewed native observer lifetime.

Uses the exact502 constructor/destructor/GetState bodies with a minimal JNI carrier.
Pauses the next base constructor, the same ordering boundary as CXBMCApp's receiver
base. This is a host mechanism reproduction, not an Android/owner-stack replay.
"""
from pathlib import Path
import argparse,hashlib,json,resource,signal,subprocess

CPP='89c5f43f69fb1bdb5d1d7d2fd39b05b4bcfa3e076e6b31873ae949748d9f8a8f'
HEADER='488e2204749cb581a3030a3b0a8eef982c98da5745976b8f746cb635d01b5853'

def definition(text,start):
 begin=text.index(start);brace=text.index('{',begin);depth=1;end=brace+1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[begin:end]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
 source=(args.source/'JNIMainActivity.cpp').read_bytes();header=(args.source/'JNIMainActivity.h').read_bytes()
 assert hashlib.sha256(source).hexdigest()==CPP and hashlib.sha256(header).hexdigest()==HEADER
 assert b'virtual std::array<int64_t, 16> infinityGetState() const = 0;' in header
 assert not args.work.exists();args.work.mkdir(parents=True)
 text=source.decode();methods='\n'.join(definition(text,s) for s in ('CJNIMainActivity::CJNIMainActivity(', 'CJNIMainActivity::~CJNIMainActivity()', 'jlongArray CJNIMainActivity::_infinityGetState('))
 harness=r'''#include <array>
#include <cstdint>
#include <algorithm>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <iostream>
using jlong=int64_t;using jobject=void*;using jlongArray=std::array<jlong,16>*;
struct ANativeActivity{};
struct JNIEnv {jlongArray NewLongArray(int n){if(n!=16)std::abort();return new std::array<jlong,16>{};}
 void SetLongArrayRegion(jlongArray a,int first,int count,const jlong*v){std::copy(v,v+count,a->begin()+first);}};
struct CJNIActivity{explicit CJNIActivity(const ANativeActivity*){}virtual ~CJNIActivity()=default;};
class CJNIMainActivity:public CJNIActivity {
public:explicit CJNIMainActivity(const ANativeActivity*);~CJNIMainActivity() override;
static jlongArray _infinityGetState(JNIEnv*,jobject);
private:static CJNIMainActivity* m_appInstance;
protected:virtual std::array<int64_t,16> infinityGetState() const=0;
};
CJNIMainActivity* CJNIMainActivity::m_appInstance=nullptr;
''' + methods + r'''
std::mutex barrierMutex;std::condition_variable barrierCV;bool constructing=false,release=false;
struct ReceiverBase {
 ReceiverBase(){std::unique_lock<std::mutex> lock(barrierMutex);constructing=true;barrierCV.notify_all();barrierCV.wait(lock,[]{return release;});}
};
struct App:public CJNIMainActivity,public ReceiverBase {
 App():CJNIMainActivity(nullptr){}
 std::array<int64_t,16> infinityGetState() const override{return {{5,15,1}};}
};
int main(){
 std::thread worker([]{App app;});
 {std::unique_lock<std::mutex> lock(barrierMutex);barrierCV.wait(lock,[]{return constructing;});}
 std::cerr<<"ENTER_EXACT502_GETSTATE_WITH_BASE_PUBLISHED_DERIVED_NOT_CONSTRUCTED\n";
 JNIEnv env;auto result=CJNIMainActivity::_infinityGetState(&env,nullptr);delete result;
 {std::lock_guard<std::mutex> lock(barrierMutex);release=true;}barrierCV.notify_all();worker.join();return 0;
}
'''
 cpp=args.work/'counterexample.cpp';cpp.write_text(harness)
 command=['g++','-std=c++17','-O0','-pthread',str(cpp),'-o',str(args.work/'counterexample')]
 compiled=subprocess.run(command,capture_output=True,text=True,timeout=30);assert compiled.returncode==0,compiled.stderr
 def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 result=subprocess.run([str(args.work/'counterexample')],capture_output=True,text=True,timeout=5,preexec_fn=no_core)
 assert result.returncode==-signal.SIGABRT and 'pure virtual' in result.stderr.lower(),(result.returncode,result.stderr)
 receipt={'status':'REPRODUCED_BASELINE_PURE_VIRTUAL_CONSTRUCTION_WINDOW','baseline':2103502,'source_sha256':{'JNIMainActivity.cpp':CPP,'JNIMainActivity.h':HEADER},'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'harness_sha256':hashlib.sha256(cpp.read_bytes()).hexdigest(),'extracted_bodies_sha256':hashlib.sha256(methods.encode()).hexdigest(),'returncode':result.returncode,'stderr':result.stderr,'production_modified':False,'Android':'NOT_RUN','owner_incident':'Mechanism consistent with sanitized triage; exact mapped build/offset correlation unavailable','reproduction':'Real virtual dispatch using exact constructor/destructor/GetState bodies; test-only next-base barrier creates an admitted construction interleaving'}
 args.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])

if __name__=='__main__':main()
