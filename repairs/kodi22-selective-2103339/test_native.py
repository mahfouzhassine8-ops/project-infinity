#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Host tests: exact StopPlaying bodies and actual Kodi POSIX lock/CSingleExit code.
Player/GUI APIs are stubs; this is not a renderer, Android device or ANR test.
"""
from pathlib import Path
import argparse, json, subprocess, tempfile
import native

TEMPLATE = r'''
#include "threads/SingleLock.h"
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <iostream>
#include <mutex>
#include <stdexcept>
#include <thread>
using namespace std::chrono_literals;
constexpr int WINDOW_VISUALISATION=1, WINDOW_FULLSCREEN_VIDEO=2, WINDOW_FULLSCREEN_GAME=3;
struct InspectLock : CCriticalSection { unsigned depth() const { return count; } };
struct Window { int active=2, moves=0, reads=0; int GetActiveWindow(){++reads;return active;} void PreviousWindow(){++moves;} };
struct CGUIComponent { Window w; Window& GetWindowManager(){return w;} };
struct CApplicationPlayer { bool playing=true; int closes=0; std::function<void()> body; bool IsPlaying(){return playing;} void ClosePlayer(){++closes;if(body)body();} };
struct WinSystem { InspectLock gfx; CCriticalSection& GetGfxContext(){return gfx;} };
struct Party { int disables=0; void Disable(){++disables;} } g_partyModeManager;
struct CServiceBroker { static inline CGUIComponent* gui=nullptr; static inline WinSystem* ws=nullptr; static CGUIComponent* GetGUI(){return gui;} static WinSystem* GetWinSystem(){return ws;} };
struct CApplication { InspectLock m_frameMoveGuard; bool m_bStop=false; CApplicationPlayer player; template<class T> CApplicationPlayer* GetComponent(){return &player;} void StopPlaying(); };
@@METHOD@@

bool otherCanLock(CCriticalSection& lock) {
  bool acquired=false;
  std::thread probe([&]{acquired=lock.try_lock(); if(acquired)lock.unlock();});
  probe.join(); return acquired;
}
void releaseRestored(InspectLock& lock, unsigned depth) {
  assert(lock.depth()==depth);
  for(unsigned i=0;i<depth;++i)lock.unlock();
}
void verifyCase(int kind, bool fixed) {
  CGUIComponent gui; WinSystem ws; CApplication app;
  CServiceBroker::gui=&gui; CServiceBroker::ws=&ws; g_partyModeManager.disables=0;
  if(kind==0){ CServiceBroker::gui=nullptr; app.StopPlaying(); assert(app.player.closes==0);return; }
  if(kind==1){ app.player.playing=false;app.StopPlaying();assert(app.player.closes==0&&g_partyModeManager.disables==0);return; }
  unsigned gfxDepth=kind==3?2:kind==2?0:1, frameDepth=kind==3?3:kind==2?0:1;
  for(unsigned i=0;i<gfxDepth;++i)ws.gfx.lock();
  for(unsigned i=0;i<frameDepth;++i)app.m_frameMoveGuard.lock();
  bool threw=false;
  if(kind==4) {
    app.player.body=[] {throw std::runtime_error("fixture close exception");};
    try{app.StopPlaying();}catch(const std::runtime_error&){threw=true;}
    assert(threw&&app.player.closes==1&&g_partyModeManager.disables==0);
  } else if(kind==2) {
    app.StopPlaying(); assert(app.player.closes==1&&g_partyModeManager.disables==1);
  } else {
    std::mutex signal; std::condition_variable cv; bool started=false,done=false; bool progressed=false;
    std::thread worker([&]{
      {std::lock_guard<std::mutex> l(signal);started=true;}cv.notify_all();
      {std::unique_lock<CCriticalSection> a(ws.gfx);std::unique_lock<CCriticalSection> b(app.m_frameMoveGuard);
       gui.w.active=99;}
      {std::lock_guard<std::mutex> l(signal);done=true;}cv.notify_all();
    });
    {std::unique_lock<std::mutex> l(signal);assert(cv.wait_for(l,5s,[&]{return started;}));}
    app.player.body=[&]{
      std::unique_lock<std::mutex> l(signal);
      progressed=cv.wait_for(l, fixed?5s:50ms,[&]{return done;});
    };
    app.StopPlaying();
    // Release only the fixture's own locks; rescue the negative parent test.
    releaseRestored(app.m_frameMoveGuard,frameDepth);frameDepth=0;
    releaseRestored(ws.gfx,gfxDepth);gfxDepth=0;
    worker.join();
    assert(progressed==fixed);assert(app.player.closes==1&&g_partyModeManager.disables==1);
    if(fixed)assert(gui.w.moves==0); // post-close window state, as upstream requires
  }
  releaseRestored(app.m_frameMoveGuard,frameDepth);releaseRestored(ws.gfx,gfxDepth);
  assert(otherCanLock(app.m_frameMoveGuard)&&otherCanLock(ws.gfx));
}
int main(){
  constexpr bool fixed=@@FIXED@@;
  for(int kind=0;kind!=6;++kind)verifyCase(kind,fixed);
  std::cout<<"PASS: exact method / real Kodi lock code; six scenarios; fixed="<<fixed<<"\n";
}
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('kodi'))
    parser.add_argument('--evidence',type=Path,default=Path('engine3339'))
    args=parser.parse_args()
    receipt=json.loads((args.evidence/'source-manifest.json').read_text())
    headers=['xbmc/threads/SingleLock.h','xbmc/threads/CriticalSection.h','xbmc/threads/Lockables.h',
        'xbmc/platform/posix/threads/RecursiveMutex.h','xbmc/platform/posix/threads/RecursiveMutex.cpp']
    for name in headers:
        native.require(native.file_digest(args.source/name)==receipt['before'][name], 'Host lock source drift: '+name)
    records=[]
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for label,fixed in (('parent',False),('patched',True)):
            method=(args.evidence/('StopPlaying-'+label+'.cpp')).read_text().strip()
            text=TEMPLATE.replace('@@METHOD@@',method).replace('@@FIXED@@','true' if fixed else 'false')
            code=root/(label+'.cpp');code.write_text(text);exe=root/label
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-DTARGET_POSIX','-DTARGET_ANDROID',
                '-I'+str((args.source/'xbmc').resolve()),str(code),
                str(args.source/'xbmc/platform/posix/threads/RecursiveMutex.cpp'),'-o',str(exe)],check=True)
            for repetition in range(3):
                result=subprocess.run([str(exe)],check=True,text=True,capture_output=True,timeout=45)
                records.append(dict(variant=label,repetition=repetition+1,scenarios=6,output=result.stdout.strip()))
    # Source admission must reject corruption without producing a partial port.
    bad=(args.evidence/'StopPlaying-parent.cpp').read_text()+'\nchanged'
    try:native.transform(bad)
    except RuntimeError:rejected=True
    else:rejected=False
    native.require(rejected,'Corrupt preimage accepted')
    result=dict(exact_generated_method_tested=True,actual_kodi_posix_locks=True,
        mock_player_and_gui=True,android_runtime_tested=False,physical_device_verified=False,
        repetitions=records,corrupt_source_rejected=rejected)
    (args.evidence/'HOST-TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: parent and patched production methods; six scenarios each, repeated three times; real Kodi lock helpers')

if __name__=='__main__':main()
