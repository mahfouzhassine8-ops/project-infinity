#!/usr/bin/env python3
"""Compile and execute the production touch router and UI-frame handoff.

Adapters supply JNI/NDK/gesture destinations, not a rewritten coordinate mapper.
This is host source testing, explicitly NOT a Samsung physical-input test.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('repair', ROOT / 'window_input.py')
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)

JNI_STUB = r'''
#pragma once
#include <cstdint>
#include <string>
#include <thread>
#include <cassert>
using jobject=void*; using jclass=void*; using jfieldID=void*; using jmethodID=void*;
using jintArray=void*; using jint=int; using jlong=int64_t; using jboolean=unsigned char;
constexpr jboolean JNI_TRUE=1;
struct JNIEnv {
  int left=0,top=0,width=1080,height=1920,visibility=0,screenLeft=0,screenTop=0;
  bool created=true,hasView=true,exception=false,failLookup=false,failCall=false;
  int calls=0,frames=0; std::thread::id ui=std::this_thread::get_id();
  void check(){assert(ui==std::this_thread::get_id());++calls;}
  bool ExceptionCheck(){check();return exception;}
  void ExceptionClear(){check();exception=false;}
  int PushLocalFrame(int){check();++frames;return 0;}
  jobject PopLocalFrame(jobject o){check();--frames;return o;}
  jclass GetObjectClass(jobject){check();return reinterpret_cast<void*>(1);}
  jfieldID GetFieldID(jclass,const char* n,const char* sig){check();
    if(failLookup){exception=true;return nullptr;}
    if(std::string(n)=="mMainView") {
      assert(std::string(sig)=="Lorg/xbmc/kodi/XBMCMainView;");return reinterpret_cast<void*>(2);
    }
    assert(std::string(n)=="mIsCreated" && std::string(sig)=="Z");return reinterpret_cast<void*>(3);}
  jmethodID GetMethodID(jclass,const char* n,const char*){check();
    std::string s=n;
    if(s=="getWidth")return reinterpret_cast<void*>(4);
    if(s=="getHeight")return reinterpret_cast<void*>(5);
    if(s=="getWindowVisibility")return reinterpret_cast<void*>(6);
    assert(s=="getLocationInWindow");return reinterpret_cast<void*>(7);}
  jobject GetObjectField(jobject,jfieldID f){check();assert(f==reinterpret_cast<void*>(2));
    return hasView?reinterpret_cast<void*>(8):nullptr;}
  jboolean GetBooleanField(jobject,jfieldID f){check();assert(f==reinterpret_cast<void*>(3));return created;}
  jint CallIntMethod(jobject,jmethodID m){check();
    assert(!exception);if(failCall){exception=true;return 0;}
    if(m==reinterpret_cast<void*>(4))return width;
    if(m==reinterpret_cast<void*>(5))return height;
    assert(m==reinterpret_cast<void*>(6));return visibility;}
  jintArray NewIntArray(int n){check();assert(n==2);return reinterpret_cast<void*>(9);}
  void CallVoidMethod(jobject,jmethodID m,jintArray a){check();
    assert(m==reinterpret_cast<void*>(7) && a==reinterpret_cast<void*>(9));}
  void GetIntArrayRegion(jintArray,int start,int len,jint* out){check();
    assert(start==0 && len==2);out[0]=left;out[1]=top;}
};
'''

INPUT_STUB = r'''
#pragma once
#include <cstdint>
#include <cassert>
#include <vector>
constexpr int AMOTION_EVENT_ACTION_MASK=255, AMOTION_EVENT_ACTION_POINTER_INDEX_MASK=65280;
constexpr int AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT=8;
constexpr int AMOTION_EVENT_ACTION_DOWN=0,AMOTION_EVENT_ACTION_UP=1,AMOTION_EVENT_ACTION_MOVE=2;
constexpr int AMOTION_EVENT_ACTION_CANCEL=3,AMOTION_EVENT_ACTION_OUTSIDE=4;
constexpr int AMOTION_EVENT_ACTION_POINTER_DOWN=5,AMOTION_EVENT_ACTION_POINTER_UP=6;
struct AInputEvent {int action;std::vector<float>x,y;int64_t time=1000;};
inline int AMotionEvent_getAction(AInputEvent*e){return e->action;}
inline size_t AMotionEvent_getPointerCount(AInputEvent*e){assert(e->x.size()==e->y.size());return e->x.size();}
inline float AMotionEvent_getX(AInputEvent*e,size_t p){assert(p<e->x.size());return e->x[p];}
inline float AMotionEvent_getY(AInputEvent*e,size_t p){assert(p<e->y.size());return e->y[p];}
inline int64_t AMotionEvent_getEventTime(AInputEvent*e){return e->time;}
'''

GENERIC_STUB = r'''
#pragma once
#include <vector>
#include <cstdint>
enum TouchInput {TouchInputAbort,TouchInputDown,TouchInputUp,TouchInputMove};
struct Record {int type;float x,y;int pointer;};
inline std::vector<Record> actions,updates;
class CGenericTouchInputHandler {public:
  static constexpr int MAX_POINTERS=2;
  static CGenericTouchInputHandler&GetInstance(){static CGenericTouchInputHandler h;return h;}
  void RegisterHandler(void*){} void UnregisterHandler(){} void SetScreenDPI(uint32_t){}
  bool HandleTouchInput(TouchInput t,float x,float y,int64_t,size_t p){actions.push_back({t,x,y,int(p)});return true;}
  void UpdateTouchPointer(size_t p,float x,float y,int64_t){updates.push_back({0,x,y,int(p)});}
};
class CGenericTouchActionHandler {public:
  static CGenericTouchActionHandler&GetInstance(){static CGenericTouchActionHandler a;return a;}
  void QuerySupportedGestures(float x,float y){actions.push_back({99,x,y,0});}
};
'''

TEST = r'''
#include "AndroidTouch.h"
#include "input/touch/generic/GenericTouchInputHandler.h"
#include <cmath>
#include <limits>
#include <iostream>
#include <thread>
class CJNIMainActivity {public:
  static CJNIMainActivity* m_appInstance;
  int frames{0};void doFrame(jlong){++frames;}
  static void _doFrame(JNIEnv*,jobject,jlong);
};
CJNIMainActivity* CJNIMainActivity::m_appInstance=nullptr;
// FRAME_HOOK
int main(int argc,char**){
  JNIEnv env; jobject activity=reinterpret_cast<void*>(10);
  CJNIMainActivity app;CJNIMainActivity::m_appInstance=&app;
  CAndroidTouch input;int cases=0;
  auto reset=[](){actions.clear();updates.clear();};
  auto event=[&](int a,std::vector<float>x,std::vector<float>y){AInputEvent e{a,x,y};return input.onTouchEvent(&e);};
  auto frame=[&](){int f=app.frames;CJNIMainActivity::_doFrame(&env,activity,123);
    assert(app.frames==f+1 && env.frames==0);};
  auto tap=[&](float x,float y){reset();assert(event(0,{x+env.left},{y+env.top}));
    assert(actions.size()==2 && actions[0].type==99 && actions[1].type==TouchInputDown);
    assert(actions[0].x==x && actions[0].y==y && updates[0].x==x && updates[0].y==y);
    assert(event(1,{x+env.left},{y+env.top}));
    assert(actions.back().type==TouchInputUp && actions.back().x==x && actions.back().y==y);++cases;};
  // Optional JNI failure is isolated, retried, and leaves the existing callback usable.
  if(argc>1){env.failLookup=true;frame();assert(!env.exception);tap(9,26);
    env.failLookup=false;env.top=40;frame();tap(9,26);
    env.failCall=true;frame();assert(!env.exception);
    reset();assert(!event(0,{9},{66}));assert(actions.empty());
    env.failCall=false;frame();tap(9,26);
    std::cout<<"PASS optional JNI lookup/call failure and recovery\n";return 0;}
  tap(9,26); // Startup with no snapshot preserves the established coordinate route.
  // Every shape, inset and global pop-up position maps to the same surface point.
  for(auto shape:std::vector<std::pair<int,int>>{{658,1536},{1384,1536},{1536,658},{342,626},{500,400},{100,160}})
    for(auto offset:std::vector<std::pair<int,int>>{{0,0},{0,40},{8,48},{-4,-7}})
      for(auto screen:std::vector<std::pair<int,int>>{{0,0},{292,563},{292,900},{50,100}}){
        env.width=shape.first;env.height=shape.second;env.left=offset.first;env.top=offset.second;
        env.screenLeft=screen.first;env.screenTop=screen.second;frame();
        for(auto pt:std::vector<std::pair<float,float>>{{0,0},{10,26},{30,60},{70,100},{99,159}})
          tap(pt.first,pt.second);
      }
  // The video-like hamburger touch: window y66 -> surface y26, not TV y66.
  env.width=342;env.height=626;env.left=0;env.top=40;frame();tap(9,26);
  // All pointers and gesture-query coordinates get exactly the same transform.
  reset();event(0,{10},{66});event(5|(1<<8),{10,50},{66,140});
  assert(updates.back().pointer==1 && updates.back().x==50 && updates.back().y==100);
  assert(actions[actions.size()-2].type==99 && actions[actions.size()-2].y==100);
  event(2,{20,60},{76,150});assert(actions.back().x==20 && actions.back().y==36);
  event(6|(1<<8),{20,60},{76,150});event(1,{20},{76});++cases;
  // Caption and right/bottom boundaries never become edge control clicks.
  for(auto pt:std::vector<std::pair<float,float>>{{-1,0},{0,-1},{342,0},{0,626},{9,-20}}){
    reset();assert(!event(0,{pt.first},{pt.second+40}));assert(actions.empty());
    assert(!event(2,{pt.first},{pt.second+40}));
    assert(!event(1,{pt.first},{pt.second+40}));assert(actions.empty());++cases;}
  // Moving the phone-global window does not cancel an in-progress gesture.
  reset();event(0,{9},{66});env.screenTop+=200;frame();event(1,{9},{66});
  assert(actions.back().type==TouchInputUp);++cases;
  // Local viewport/inset or dimension changes do cancel, never emit a stale tap.
  for(int mutation=0;mutation<4;++mutation){
    reset();event(0,{9+float(env.left)},{26+float(env.top)});
    if(mutation==0)++env.top;else if(mutation==1)++env.left;
    else if(mutation==2)++env.width;else ++env.height;
    frame();
    event(1,{9+float(env.left)},{26+float(env.top)});
    assert(actions.back().type==TouchInputAbort);tap(9,26);++cases;
  }
  // Zero-pointer CANCEL, bad index and non-finite events abort without reading invalid pointers.
  for(int bad=0;bad<5;++bad){
    reset();event(0,{9+float(env.left)},{26+float(env.top)});
    if(bad==0)event(3,{},{});else if(bad==1)event(4,{},{});
    else if(bad==2)event(5|(3<<8),{1},{1});else if(bad==3)event(2,{},{});
    else event(2,{std::numeric_limits<float>::quiet_NaN()},{1});
    assert(actions.back().type==TouchInputAbort);
    size_t n=actions.size();event(1,{1},{1});assert(actions.size()==n);tap(9,26);++cases;
  }
  // Third finger is ignored without breaking the tracked two-pointer stream.
  reset();event(0,{9+float(env.left)},{26+float(env.top)});size_t n=actions.size();
  event(5|(2<<8),{1,2,3},{50,60,70});assert(actions.size()==n);
  event(1,{9+float(env.left)},{26+float(env.top)});assert(actions.back().type==TouchInputUp);++cases;
  // Surface destruction/hidden window rejects taps; reattachment accepts fresh DOWN.
  for(int absence=0;absence<4;++absence){
    reset();if(absence==0)env.created=false;else if(absence==1)env.visibility=4;
    else if(absence==2)env.hasView=false;else env.width=0;
    frame();
    assert(!event(0,{9},{66}));assert(actions.empty());
    env.created=true;env.visibility=0;env.hasView=true;env.width=342;frame();tap(9,26);++cases;
  }
  // Actual input-thread routing must not touch JNI/Android Views.
  int calls=env.calls;
  std::thread worker([&]{tap(9,26);});worker.join();assert(env.calls==calls);++cases;
  assert(env.frames==0);std::cout<<"PASS production window-input router: "<<cases<<" cases; JNI UI-only; no physical-device claim\n";
}
'''

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--unpatched-fixture', action='store_true')
    args = p.parse_args()
    cpp = (args.source / repair.CPP).read_text()
    header = (args.source / repair.HEADER).read_text()
    jni = (args.source / repair.JNI).read_text()
    if args.unpatched_fixture:
        cpp = repair.transform(repair.CPP, cpp)
        header = repair.transform(repair.HEADER, header)
        jni = repair.transform(repair.JNI, jni)
    assert cpp == (ROOT / 'AndroidTouch.cpp').read_text()
    assert 'CAndroidTouch::RefreshInputViewport(env, context);' in jni
    start = jni.index('void CJNIMainActivity::_doFrame(')
    end = jni.index('\n}', start) + 2
    hook = jni[start:end]
    with tempfile.TemporaryDirectory(prefix='infinity-input-test-') as name:
        d = Path(name)
        files = {'AndroidTouch.cpp':cpp, 'AndroidTouch.h':header, 'jni.h':JNI_STUB,
                 'android/input.h':INPUT_STUB,
                 'input/touch/generic/GenericTouchInputHandler.h':GENERIC_STUB,
                 'input/touch/generic/GenericTouchActionHandler.h':'#pragma once\n#include "GenericTouchInputHandler.h"\n',
                 'CompileInfo.h':'#pragma once\nclass CCompileInfo {public: static const char* GetClass(){return "org/xbmc/kodi";}};\n',
                 'platform/android/activity/XBMCApp.h':'#pragma once\nclass CXBMCApp {public: static void android_printf(const char*,...) {}};\n',
                 'test.cpp':TEST.replace('// FRAME_HOOK',hook)}
        for name, content in files.items():
            f = d / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content)
        for mode, flags in [('normal',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
            exe = d / mode
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread',*flags,
                            '-I'+str(d),str(d/'AndroidTouch.cpp'),str(d/'test.cpp'),'-o',str(exe)],check=True)
            # LeakSanitizer's /proc inspection is unavailable in the managed host.
            # Address/undefined sanitizers stay enabled; leak checking is NOT claimed.
            env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0')
            subprocess.run([str(exe)],check=True,env=env)
            subprocess.run([str(exe),'lookup-failure'],check=True,env=env)

if __name__ == '__main__':
    main()
