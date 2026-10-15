#!/usr/bin/env python3
"""Compile the actual modified recognizer and original gesture detectors.

Only timer scheduling, logging and the platform critical-section adapter are
substituted. Tests explicitly deliver queued callbacks at race boundaries.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

TIMER = r'''
#pragma once
#include <chrono>
class ITimerCallback {public:virtual ~ITimerCallback()=default;virtual void OnTimeout()=0;};
class CTimer {public: explicit CTimer(ITimerCallback*) {} bool running=false;
 bool Start(std::chrono::milliseconds,bool=false){if(running)return false;running=true;return true;}
 bool Stop(bool=false){bool was=running;running=false;return was;}
 bool IsRunning()const{return running;} };
'''
TEST = r'''
#include <array>
#include <memory>
#include <set>
#include <mutex>
#include <chrono>
#include <atomic>
#include <cassert>
#include <iostream>
#define private public
#include "input/touch/generic/GenericTouchInputHandler.h"
#undef private
struct Sink:ITouchActionHandler {
 int taps=0,holds=0,pans=0,aborts=0;
 void OnTap(float,float,int32_t)override{taps++;}
 void OnLongPress(float,float,int32_t)override{holds++;}
 bool OnTouchGesturePan(float,float,float,float,float,float)override{pans++;return true;}
 void OnTouchAbort()override{aborts++;}
};
int main(){
 auto& h=CGenericTouchInputHandler::GetInstance();Sink s;h.RegisterHandler(&s);
 int64_t time=1000000000;
 auto event=[&](TouchInput kind,float x=100,float y=100,int p=0){time+=1000000;h.UpdateTouchPointer(p,x,y,time);h.HandleTouchInput(kind,x,y,time,p);};
 auto expired=[&]{h.m_holdDeadline=std::chrono::steady_clock::now()-std::chrono::milliseconds(1);};
 // Normal tap and duplicate up dispatch one primary action, never a context action.
 event(TouchInputDown);h.OnTimeout();event(TouchInputUp);event(TouchInputUp);
 assert(s.taps==1&&s.holds==0);
 // An old queued timeout cannot turn the next fresh down into a hold.
 event(TouchInputDown);event(TouchInputUp);event(TouchInputDown);h.OnTimeout();
 assert(s.holds==0);event(TouchInputUp);assert(s.taps==3);
 // Intentional hold yields one context action and consumes the release tap.
 event(TouchInputDown);expired();h.OnTimeout();h.OnTimeout();event(TouchInputUp);
 assert(s.holds==1&&s.taps==3);
 // Cancellation invalidates a queued callback and its later up.
 event(TouchInputDown);expired();event(TouchInputAbort);h.OnTimeout();event(TouchInputUp);
 assert(s.holds==1&&s.taps==3&&s.aborts==1);
 // Movement can reach UpdateTouchPointer before HandleTouchInput(Move).
 event(TouchInputDown);h.UpdateTouchPointer(0,180,100,time+1);expired();h.OnTimeout();
 assert(s.holds==1);event(TouchInputMove,180);event(TouchInputUp,180);
 assert(s.pans>0&&s.taps==3);
 // Coalesced movement first appearing at Up must not produce a tap.
 event(TouchInputDown);event(TouchInputUp,180);assert(s.taps==3);
 // A secondary down starts a fresh hold deadline, and movement cancels it.
 event(TouchInputDown);event(TouchInputDown,130,100,1);h.OnTimeout();assert(s.holds==1);
 h.UpdateTouchPointer(1,190,100,time+1);expired();h.OnTimeout();assert(s.holds==1);
 event(TouchInputAbort);h.UnregisterHandler();
 std::cout<<"PASS: seven compiled tap/hold/scroll/cancellation race scenarios\n";
}
'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,required=True);args=ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)
        names=['input/touch/ITouchActionHandler.h','input/touch/ITouchInputHandling.h',
               'input/touch/ITouchInputHandling.cpp','input/touch/ITouchInputHandler.h',
               'input/touch/TouchTypes.h','utils/Vector.h','utils/Vector.cpp']
        names += ['input/touch/generic/'+n for n in ['IGenericTouchGestureDetector.h',
            'GenericTouchSwipeDetector.h','GenericTouchSwipeDetector.cpp',
            'GenericTouchPinchDetector.h','GenericTouchPinchDetector.cpp',
            'GenericTouchRotateDetector.h','GenericTouchRotateDetector.cpp']]
        for name in names:
            p=d/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(args.base/'xbmc'/name,p)
        for name in ['GenericTouchInputHandler.cpp','GenericTouchInputHandler.h']:
            shutil.copy2(args.candidate/'xbmc/input/touch/generic'/name,d/'input/touch/generic'/name)
        (d/'threads').mkdir()
        (d/'threads/Timer.h').write_text(TIMER)
        (d/'threads/CriticalSection.h').write_text('#pragma once\n#include <mutex>\nusing CCriticalSection=std::recursive_mutex;\n')
        (d/'utils/log.h').write_text('#pragma once\n#define LOGDEBUG 0\nstruct CLog{template<class...T>static void Log(T...) {}};\n')
        (d/'test.cpp').write_text(TEST)
        cpp=sorted(str(p) for p in d.rglob('*.cpp'))
        subprocess.run(['c++','-std=c++17','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-pthread','-I'+str(d),*cpp,'-o',str(d/'test')],check=True)
        subprocess.run([str(d/'test')],check=True,timeout=20)

if __name__=='__main__':main()
