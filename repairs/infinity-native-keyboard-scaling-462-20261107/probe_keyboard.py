"""Compile exact pinned native method bodies with explicit host platform boundaries."""
from pathlib import Path
import hashlib,json,os,subprocess
def method(raw,signature):
 start=raw.index(signature);end=raw.index('\n}\n',start)+3
 return raw[start:end]
def run(root,out):
 previous=root/'previous-review/sources'
 source_root=out/'sources'
 def read(name):
  p=source_root/name
  if not p.is_file():p=previous/name
  raw=p.read_text()
  expected=json.loads((root/'previous-review/NATIVE-SOURCE-MAP.json').read_text())
  assert hashlib.sha256(p.read_bytes()).hexdigest()==expected[name],name
  return raw
 android=read('xbmc/platform/android/activity/AndroidKeyboard.cpp')
 touch=read('xbmc/dialogs/GUIDialogKeyboardTouch.cpp')
 factory=read('xbmc/guilib/GUIKeyboardFactory.cpp')
 selected=[
 method(android,'std::shared_ptr<InfinityKeyboardState> CAndroidKeyboard::State()'),
 method(android,'bool CAndroidKeyboard::ShowAndGetInput(char_callback_t callback'),
 method(android,'void CAndroidKeyboard::Cancel()'),
 method(touch,'bool CGUIDialogKeyboardTouch::ShowAndGetInput(char_callback_t pCallback'),
 method(touch,'void CGUIDialogKeyboardTouch::Cancel()'),
 method(touch,'void CGUIDialogKeyboardTouch::Process()'),
 method(factory,'void CGUIKeyboardFactory::keyTypedCB('),
 method(factory,'bool CGUIKeyboardFactory::ShowAndGetInput(std::string& aTextString,')]
 state=android[android.index('struct InfinityKeyboardState'):android.index('\nnamespace')]
 work=out/'host-uaf-proof';work.mkdir()
 inc=work/'include';(inc/'guilib').mkdir(parents=True)
 (inc/'platform/android/activity').mkdir(parents=True)
 (inc/'platform/android/activity/AndroidKeyboard.h').write_text(read('xbmc/platform/android/activity/AndroidKeyboard.h'))
 (inc/'guilib/GUIKeyboard.h').write_text(r'''
#pragma once
#include <string>
enum FILTERING{FILTERING_NONE=0,FILTERING_CURRENT,FILTERING_SEARCH};
class CGUIKeyboard;
using char_callback_t=void(*)(CGUIKeyboard*,const std::string&);
class CGUIKeyboard{public:
 virtual ~CGUIKeyboard()=default;
 virtual bool ShowAndGetInput(char_callback_t,const std::string&,std::string&,const std::string&,bool)=0;
 virtual void Cancel()=0;
 virtual int GetWindowId()const{return 0;}
 virtual bool SetTextToKeyboard(const std::string&,bool=false){return false;}
 void startAutoCloseTimer(unsigned int){}
 void resetAutoCloseTimer(){}
};
''')
 (inc/'jni.h').write_text(r'''
#pragma once
using jclass=void*;using jmethodID=void*;using jstring=void*;using jlong=long long;using jboolean=unsigned char;
constexpr jboolean JNI_TRUE=1;
void NativeEditorOpened();
struct JNIEnv{
 bool ExceptionCheck(){return false;}
 void DeleteLocalRef(jstring){}
 template<class... Args>void CallStaticVoidMethod(Args...){NativeEditorOpened();}
};
''')
 prefix=r'''
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <memory>
#include <thread>
#include <unordered_map>
#include <chrono>
#include <cstdlib>
#include <cassert>
#include <iostream>
#include <type_traits>
#include "platform/android/activity/AndroidKeyboard.h"
using namespace std::chrono_literals;
static std::mutex gateMutex;static std::condition_variable gate;
static bool javaOpened=false,secondEntered=false,releaseSecond=false,closed=false;
void NativeEditorOpened(){std::lock_guard<std::mutex> lock(gateMutex);javaOpened=true;gate.notify_all();}
static JNIEnv env;
JNIEnv* xbmc_jnienv(){return &env;}
jclass keyboardClass=reinterpret_cast<void*>(1);jmethodID openMethod=reinterpret_cast<void*>(2);
static std::atomic<uint64_t> nextToken{1};static std::mutex registryMutex;
static std::unordered_map<uint64_t,std::weak_ptr<InfinityKeyboardState>> editors;
jstring ToJava(JNIEnv*,const std::string&){return reinterpret_cast<void*>(1);}
bool JavaFailed(JNIEnv*){return false;}
void CloseJava(uint64_t){}
int CAndroidKeyboard::InputKind(){return 0;}
bool CAndroidKeyboard::UseAndroidIME(){return true;}
bool CAndroidKeyboard::SetTextToKeyboard(const std::string&,bool){return false;}
class CVariant{std::string value;public:CVariant(const char*s):value(s){}bool isString()const{return true;}
 std::string asString()const{return value;}bool isInteger()const{return false;}long asInteger()const{return 0;}};
struct Localize{std::string Get(uint32_t){return "fixture";}}g_localizeStrings;
enum{WINDOW_DIALOG_KEYBOARD=1,WINDOW_DIALOG_KEYBOARD_TOUCH=2,GUI_MSG_NOTIFY_ALL=3,GUI_MSG_SEARCH_UPDATE=4,GUI_MSG_FILTER_ITEMS=5};
class CGUIMessage{public:CGUIMessage(int,int,int){}void SetParam1(int){}void SetStringParam(const std::string&){}};
struct Messenger{void SendGUIMessage(CGUIMessage&,int=0){}};
class CGUIDialogKeyboardTouch:public CGUIKeyboard{
public:
 char_callback_t m_pCharCallback=nullptr;
 std::string m_initialString,m_typedString,m_heading;
 bool m_bHiddenInput=false;std::unique_ptr<CGUIKeyboard>m_keyboard;
 bool m_confirmed=false,m_search=false;int m_inputKind=0;
 std::thread worker;std::atomic<int>initializations{0};
 bool ShowAndGetInput(char_callback_t,const std::string&,std::string&,const std::string&,bool)override;
 void Cancel()override;
 void Process();
 void SetInputMode(bool s,int k){m_search=s;m_inputKind=k;}
 void Initialize(){
  if(++initializations==2){std::unique_lock<std::mutex>lock(gateMutex);secondEntered=true;gate.notify_all();
   gate.wait(lock,[]{return releaseSecond;});}
 }
 void Open(){worker=std::thread([this]{Process();});
  std::unique_lock<std::mutex> lock(gateMutex);gate.wait(lock,[]{return closed;});}
 void Close(bool=false,int=0,bool=false,bool=false){std::lock_guard<std::mutex>lock(gateMutex);closed=true;gate.notify_all();}
 void StopThread(bool){if(worker.joinable())worker.join();}
 int GetWindowId()const override{return 10138;}
};
class CGUIDialogKeyboardGeneric:public CGUIKeyboard{
public:bool ShowAndGetInput(char_callback_t,const std::string&,std::string&,const std::string&,bool)override{return false;}
 void Cancel()override{}
};
static CGUIDialogKeyboardTouch touchDialog;static CGUIDialogKeyboardGeneric generic;
struct Windows{
 template<class T>T*GetWindow(int){
  if constexpr(std::is_same_v<T,CGUIDialogKeyboardTouch>)return &touchDialog;else return &generic;}
 int GetActiveWindow(){return 10025;}
};
struct GUI{Windows&GetWindowManager(){static Windows w;return w;}};
struct CServiceBroker{
 static GUI*GetGUI(){static GUI g;return &g;}
 static Messenger*GetAppMessenger(){static Messenger m;return &m;}
};
class CGUIKeyboardFactory{public:
 static CGUIKeyboard*g_activeKeyboard;static FILTERING m_filtering;
 static void keyTypedCB(CGUIKeyboard*,const std::string&);
 static bool ShowAndGetInput(std::string&,const CVariant&,bool,bool,unsigned int);
};
CGUIKeyboard*CGUIKeyboardFactory::g_activeKeyboard=nullptr;
FILTERING CGUIKeyboardFactory::m_filtering=FILTERING_NONE;
'''
 main=r'''
int main(){
 std::thread first([]{std::string text;CGUIKeyboardFactory::ShowAndGetInput(text,CVariant{"fixture"},true,false,0);});
 std::shared_ptr<InfinityKeyboardState> old;
 {
  std::unique_lock<std::mutex>lock(gateMutex);
  if(!gate.wait_for(lock,3s,[]{return javaOpened;}))return 3;
 }
 {std::lock_guard<std::mutex>lock(registryMutex);assert(editors.size()==1);old=editors.begin()->second.lock();assert(old);}
 std::thread second([]{std::string text;CGUIKeyboardFactory::ShowAndGetInput(text,CVariant{"fixture"},true,false,0);});
 {
  std::unique_lock<std::mutex>lock(gateMutex);
  if(!gate.wait_for(lock,3s,[]{return secondEntered;}))return 4;
 }
 // Second native ShowAndGetInput has already replaced/freed the editor,
 // before its Initialize/Open/StopThread. Wake the original real native loop.
 {std::lock_guard<std::mutex>lock(old->mutex);old->text="fixture";++old->revision;old->finished=true;old->accepted=true;}
 old->ready.notify_one();
 std::this_thread::sleep_for(2s);
 std::cerr<<"EXPECTED_ASAN_UAF_NOT_DETECTED\n";std::_Exit(5);
}
'''
 cpp=prefix+'\n'+state+'\n'+'\n'.join(selected)+'\n'+main
 source=work/'actual_keyboard_owner.cpp';source.write_text(cpp)
 binary=work/'keyboard-owner-before'
 compile_result=subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-fsanitize=address','-fno-omit-frame-pointer',
   '-g','-O1','-pthread','-I',str(inc),str(source),'-o',str(binary)],capture_output=True,text=True)
 (work/'COMPILE.txt').write_text(compile_result.stdout+compile_result.stderr)
 assert compile_result.returncode==0,compile_result.stderr
 result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=12,
   env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1'))
 (work/'BEFORE.txt').write_text(result.stdout+result.stderr)
 assert result.returncode!=0 and 'heap-use-after-free' in result.stderr,result.stdout+result.stderr
 assert 'CAndroidKeyboard::ShowAndGetInput' in result.stderr,result.stderr
 report=dict(status='PASS_HOST_DEMONSTRATED_NATIVE_EDITOR_REENTRANCY_UAF',
   source=os.environ['GITHUB_SHA'],native_patch=False,host_compiled=True,ARM64='NOT_RUN',Android='NOT_RUN',
   actual_method_hashes=[hashlib.sha256(s.encode()).hexdigest() for s in selected],
   platform_boundaries=['JNI notification','window lookup','modal Open/Initialize scheduling','timer stubs'],
   reproduction='second native factory entry replaces unique editor before Initialize/Open; old native loop reads freed m_owner',
   historical_incident_causality='CONSISTENT_WITH_POINTER_FAULT_AND_OVERLAP_NOT_EXCLUSIVE_PROOF',
   native_repair='NOT_IMPLEMENTED')
 (out/'HOST-KEYBOARD-COUNTEREXAMPLE.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS host ASan: exact native editor/factory/dialog method bodies reproduce reentrant editor use-after-free; Android/ARM64 NOT_RUN')
 print(result.stderr[:12000])
