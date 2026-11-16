"""Compile actual lock-owner functions against explicit GUI/JNI test adapters."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'native/xbmc/platform/android/activity/InfinityVideoLock.cpp'
SELECTED = ['initial failure versus established readiness revocation',
            'stale and duplicate unlock request preserve current grant/pending ownership',
            'current shared-item control block distinguishes replay and stop',
            'unknown transient playing state does not retire a lock',
            'skin switch retires only the existing lock',
            'committed lock metadata cleanup does not hide restored OSD',
            'confirmed owner destruction clears input even when callback is delayed and preserves GUI cleanup',
            'owner destruction wins bounded queue space without retiring newer session or successful commit']


def function(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    source = SOURCE.read_text()
    selected = ROOT / 'NATIVE-PROTOCOL-SELECTION.json'
    selected.write_text(json.dumps({'selected_before_execution': SELECTED,
                                   'scope': 'Actual extracted source functions; fake GUI/JNI adapters, not Android acceptance'}, indent=2) + '\n')
    signatures = ['bool ConsumeOwnerGone(std::uint32_t token)', 'void ClearMetadata()', 'bool Active()',
                  'void Retire(bool notifyJava)', 'Context Current()', 'void Handle(const Event& event)',
                  'jboolean JNICALL OwnerGone(JNIEnv*, jclass, jlong token)']
    extracted = '\n\n'.join(function(source, s) for s in signatures)
    prefix = r'''
#include "InfinityVideoLockGate.h"
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include <deque>
#include <mutex>
#include <iostream>
#include <cstdlib>
using InfinityVideoLock::Gate;
using jlong = long long;
using jint = int;
using jboolean=bool; using JNIEnv=void; using jclass=void*;
#define JNICALL
constexpr bool JNI_TRUE=true,JNI_FALSE=false;
constexpr int LOCK_WINDOW=11199, WINDOW_DIALOG_VIDEO_OSD=12901, LOGWARNING=2;
enum Operation {READY=1,REVOKE=2,UNLOCK=3,VALIDATE=4,OWNER_GONE=5,ENTRY_FAILED=6};
struct Event {std::uint32_t session; int operation; std::uint64_t epoch,request;};
enum class Context {CURRENT,UNKNOWN,RETIRED};
struct Item {std::string path="opaque-existing-source"; std::string GetPath() const {return path;}};
struct CApplicationPlayer {bool playing=true; bool IsPlayingVideo() {return playing;}};
struct App {
 std::shared_ptr<Item> item;
 std::shared_ptr<CApplicationPlayer> player=std::make_shared<CApplicationPlayer>();
 bool stopping=false;
 std::shared_ptr<Item> CurrentFileItemPtr(){return item;}
 bool IsStopping(){return stopping;}
 template<class T> std::shared_ptr<T> GetComponent(){return player;}
} g_application;
bool skin=true, checkpoint=false, process=true;
struct CServiceBroker {static int* GetGUI(){static int gui=1;return &gui;}};
struct InfinityAndroidCheckpoint {static bool IsActive(){return checkpoint;}};
struct CLog {template<class... A> static void Log(A...) {}};
Gate gate;
std::uint32_t session=0, counter=0;
std::weak_ptr<Item> itemOwner;
std::uint64_t readyEpoch=0,pendingRequest=0;
bool ready=false,everReady=false,restoredOSD=false;
std::mutex queueMutex;
std::deque<Event> queue;
std::uint32_t pendingOwnerGoneToken=0;
constexpr int TMSG_CALLBACK=800;
int callback=0;
struct CApplicationMessenger {void PostMsg(int,int,int,void*){}};
std::weak_ptr<CApplicationMessenger> messengerOwner;
std::vector<int> closed;
std::vector<std::vector<jlong>> replies;
int shown=0;
bool ProcessThread(){return process;}
bool InfinitySkin(){return skin;}
int Theme(){return 0;}
void CloseOwnedWindow(int id){closed.push_back(id);}
bool ShowOSD(){++shown;return true;}
template<class... A> bool Java(const char*,const char*,A...args){replies.push_back({static_cast<jlong>(args)...});return true;}
'''
    suffix = r'''
unsigned checks=0;
void require(bool v){++checks;if(!v){std::cerr<<"FAIL protocol "<<checks<<"\n";std::exit(1);}}
void fresh(){gate.Retire(session);ClearMetadata();pendingOwnerGoneToken=0;queue.clear();session=++counter;gate.Begin(session);skin=true;checkpoint=false;
 g_application.stopping=false;g_application.player->playing=true;g_application.item=std::make_shared<Item>();itemOwner=g_application.item;
 closed.clear();replies.clear();shown=0;}
int main(){
 fresh(); auto initial=session;Handle({session,ENTRY_FAILED,0,0});require(!gate.Value());require(shown==1);require(!replies.empty()&&replies.back()[0]==initial);
 fresh();Handle({session,READY,1,0});require(ready&&everReady);Handle({session,REVOKE,1,0});require(!ready&&everReady);
 Handle({session,ENTRY_FAILED,0,0});require(gate.Value()!=0);require(shown==0);
 Handle({session,READY,2,0});Handle({session,UNLOCK,2,20});auto grant=gate.Value();require(pendingRequest==20 && (grant&1));
 Handle({session,UNLOCK,1,10});require(pendingRequest==20 && gate.Value()==grant);
 Handle({session,UNLOCK,3,30});require(pendingRequest==20 && gate.Value()==grant);
 auto count=replies.size();Handle({session,UNLOCK,2,20});require(replies.size()==count && pendingRequest==20 && gate.Value()==grant);
 Handle({session,REVOKE,1,10});require(pendingRequest==20 && gate.Value()==grant);
 Handle({session,REVOKE,2,20});require(!pendingRequest && gate.Value()!=grant && !gate.Commit(session,grant));
 Handle({session,READY,3,0});Handle({session,UNLOCK,3,30});auto next=gate.Value();require(next!=grant && pendingRequest==30);
 require(gate.Commit(session,next));count=closed.size();require(!Active());require(closed.size()==count && session==0);

 fresh();auto stale=session;auto old=g_application.item;g_application.item=std::make_shared<Item>();require(Current()==Context::RETIRED);require(!gate.Value());
 fresh();Handle({stale,VALIDATE,0,0});require(gate.Value()!=0);Handle({session,VALIDATE,0,0});require(gate.Value()!=0);
 g_application.item->path="same-lifetime-metadata-update";require(Current()==Context::CURRENT);
 g_application.player->playing=false;require(Current()==Context::UNKNOWN && gate.Value()!=0);
 g_application.item->path.clear();require(Current()==Context::RETIRED && !gate.Value());
 fresh();skin=false;require(Current()==Context::RETIRED && !gate.Value());
 fresh();Handle({session,READY,1,0});Handle({session,UNLOCK,1,4});grant=gate.Value();
 g_application.player->playing=false;Handle({session,UNLOCK,1,5});require(pendingRequest==4 && gate.Value()==grant);
 fresh();Handle({session,READY,1,0});Handle({session,UNLOCK,1,4});auto departed=session;
 for(int i=0;i<32;++i)queue.push_back({session,VALIDATE,0,0});
 require(OwnerGone(nullptr,nullptr,session));require(!gate.Value() && pendingOwnerGoneToken==departed);
 require(queue.size()==1 && queue.front().operation==OWNER_GONE);
 count=closed.size();require(!Active());require(closed.size()==count+2 && !pendingOwnerGoneToken && !session);
 fresh();auto live=session;Handle({departed,OWNER_GONE,0,0});require(session==live && gate.Value());
 require(!OwnerGone(nullptr,nullptr,departed) && session==live && gate.Value());
 Handle({session,READY,1,0});Handle({session,UNLOCK,1,7});grant=gate.Value();require(gate.Commit(session,grant));
 require(!OwnerGone(nullptr,nullptr,session) && pendingOwnerGoneToken==0);
 count=closed.size();require(!Active());require(closed.size()==count);
 fresh();Handle({session,READY,1,0});departed=session;require(OwnerGone(nullptr,nullptr,session));
 Handle(queue.front());require(!session && !pendingOwnerGoneToken && !gate.Value());
 std::cout<<"PASS native lock protocol "<<checks<<" assertions\n";
}
'''
    with tempfile.TemporaryDirectory(prefix='infinity502-lock-protocol-') as directory:
        path = Path(directory)
        (path / 'probe.cpp').write_text(prefix + extracted + suffix)
        command = ['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                   '-I', str(ROOT / 'native/xbmc/platform/android/activity'), str(path/'probe.cpp'), '-o', str(path/'probe')]
        subprocess.run(command, check=True)
        result = subprocess.run([str(path/'probe')], capture_output=True, text=True, check=True)
    receipt = {'status': 'PASS_HOST_ACTUAL_OWNER_FUNCTIONS_ONLY', 'output': result.stdout.strip(),
               'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
               'function_sha256': {s: hashlib.sha256(function(source, s).encode()).hexdigest() for s in signatures},
               'selected': SELECTED,
               'adapters': ['Kodi GUI/window opens', 'JNI callback dispatch', 'current application item/player'],
               'not_verified': ['real Android threading/JNI', 'actual Kodi render', 'ARM64 link', 'Fold acceptance']}
    output = ROOT / 'NATIVE-PROTOCOL-HOST.json'
    if output.exists() and not (ROOT / 'NATIVE-PROTOCOL-HOST-PREVIOUS.json').exists():
        (ROOT / 'NATIVE-PROTOCOL-HOST-PREVIOUS.json').write_bytes(output.read_bytes())
    output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(result.stdout.strip())


if __name__ == '__main__':
    main()
