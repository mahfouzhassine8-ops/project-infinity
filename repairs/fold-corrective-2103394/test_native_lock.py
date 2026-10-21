"""Execute the captured lock cycle with real CPython GIL manipulation.

The methods under test are extracted from the actual verified Kodi source.
Only the GUI/frame lock and the message-thread entry are narrow host peers.
No profile, provider, Android process or user file participates in this test.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import sysconfig
import sys
import unittest
import native94


def function(source, signature):
    start=source.index(signature)
    opening=source.index('{',start);depth=1;end=opening+1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


class ActualLanguageHookLockCycle(unittest.TestCase):
    def test_original_cycle_and_corrected_lifetime(self):
        root=Path(os.environ['INFINITY_2103393_NATIVE'])
        original=(root/native94.WINDOW).read_bytes()
        corrected=native94.window_language_hook(original)
        signature='Control* Window::getControl(int iControlId)'
        before=function(original.decode(),signature).replace('Window::getControl(', 'Window::getControlBaseline(',1)
        after=function(corrected.decode(),signature)
        selected=function((root/'xbmc/interfaces/legacy/Control.cpp').read_text(),
                          'XBMCAddon::xbmcgui::ListItem* ControlList::getSelectedItem()')
        source=HARNESS.replace('ACTUAL_WINDOW_METHODS',before+'\n'+after).replace('ACTUAL_SELECTED_METHOD',selected)
        with tempfile.TemporaryDirectory(prefix='infinity94-real-gil-') as temp:
            work=Path(temp);(work/'utils').mkdir()
            (work/'utils/log.h').write_text('#pragma once\n#define LOGERROR 4\nstruct CLog{template<class... T> static void Log(T...){}};\n')
            (work/'test.cpp').write_text(source)
            flags=shlex.split(subprocess.check_output(['python3-config','--includes','--embed','--ldflags'],text=True))
            libdirs=[Path(f[2:]) for f in flags if f.startswith('-L')]
            libdirs += [Path(sys.executable).parent.parent/'lib',Path(sysconfig.get_config_var('LIBDIR'))]
            soname=next((p for d in libdirs for p in d.glob('libpython*.so.1.0') if p.is_file()),None)
            libdir=soname.parent if soname else libdirs[0]
            if soname:
                flags=[str(soname) if f.startswith('-lpython') else f for f in flags]
            compiled=subprocess.run(['g++','-std=c++17','-pthread','-DTARGET_ANDROID','-I'+str(work),
                '-I'+str(root/'xbmc'),str(work/'test.cpp'),str(root/'xbmc/interfaces/python/PyContext.cpp'),
                *flags,'-Wl,-rpath,'+str(libdir),'-o',str(work/'test')],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            for variant,skin,expected in [('baseline','infinity','observed_locked_cycle'),
                    ('corrected','infinity','completed_without_lock_cycle'),
                    ('corrected','other','original_other_skin_path_preserved')]:
                result=subprocess.run([str(work/'test'),variant,skin],check=True,capture_output=True,text=True,timeout=6)
                self.assertIn(expected,result.stdout)
        # The ownership fix cannot change other Window methods or any control API.
        self.assertEqual(corrected.replace(after.encode(),function(original.decode(),signature).encode(),1)
                         .replace(b'#if defined(TARGET_ANDROID)\n#include "interfaces/legacy/ModuleXbmc.h"\n#endif\n',b'',1),original)


HARNESS=r'''
#include <Python.h>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include "interfaces/python/PyContext.h"
#define XBMC_TRACE
static std::mutex frame;
static std::atomic<bool> frameHeld{false}, childAtFrame{false}, done{false};
static std::string skin;
namespace XBMCAddon {
struct LanguageHook {
  static thread_local LanguageHook* current;
  static LanguageHook* GetLanguageHook(){return current;}
  void DelayedCallOpen(){Python::PyGILLock::releaseGil();}
  void DelayedCallClose(){Python::PyGILLock::acquireGil();}
};
thread_local LanguageHook* LanguageHook::current=nullptr;
struct SetLanguageHookGuard {
  explicit SetLanguageHookGuard(LanguageHook* value){LanguageHook::current=value;}
  ~SetLanguageHookGuard(){LanguageHook::current=nullptr;}
};
struct DelayedCallGuard {
  LanguageHook* hook;
  explicit DelayedCallGuard(LanguageHook* h):hook(h){if(hook)hook->DelayedCallOpen();}
  ~DelayedCallGuard(){if(hook)hook->DelayedCallClose();}
};
namespace xbmc { std::string getSkinDir(){return skin;} }
struct AddonClass { template<class T> struct Ref {
  T* value; Ref(T* x=nullptr):value(x){} Ref(long):value(nullptr){}
  Ref& operator=(T* x){value=x;return *this;} T* get(){return value;}
};};
}
struct CGUIMessage { CGUIMessage(int,int,int){} int GetParam1(){return 0;} };
#define GUI_MSG_ITEM_SELECTED 1
struct NativeControl { void OnMessage(CGUIMessage&){} };
namespace XBMCAddonUtils {
struct GuiLock {
  XBMCAddon::LanguageHook* hook;
  GuiLock(XBMCAddon::LanguageHook* h,bool):hook(h){
    if(!hook)hook=XBMCAddon::LanguageHook::GetLanguageHook();
    if(hook)hook->DelayedCallOpen();
    childAtFrame=true;frame.lock();
  }
  ~GuiLock(){frame.unlock();if(hook)hook->DelayedCallClose();}
};}
struct WinSystem { int context; int& GetGfxContext(){return context;} };
struct CServiceBroker { static WinSystem* GetWinSystem(){static WinSystem w;return &w;} };
namespace XBMCAddon { namespace xbmcgui {
struct ListItem {};
struct Control { LanguageHook* languageHook=LanguageHook::GetLanguageHook(); virtual ~Control()=default; };
struct ControlList:Control {
  std::vector<ListItem*> vecItems; NativeControl* pGUIControl=nullptr; int iParentId=10000,iControlId=8101;
  ListItem* getSelectedItem();
};
struct Window {
  LanguageHook* languageHook;
  explicit Window(LanguageHook* h):languageHook(h){}
  Control* GetControlById(int,int*){return new ControlList();}
  Control* getControl(int);Control* getControlBaseline(int);
};
ACTUAL_WINDOW_METHODS
ACTUAL_SELECTED_METHOD
}}
int main(int argc,char** argv){
  if(argc!=3)return 2;
  bool corrected=std::string(argv[1])=="corrected",infinity=std::string(argv[2])=="infinity";
  skin=infinity?"skin.infinity.diggz":"skin.protected.other";
  Py_Initialize();XBMCAddon::LanguageHook parent;
  XBMCAddon::xbmcgui::Window window(&parent);
  std::unique_ptr<XBMCAddon::xbmcgui::Control> control(corrected?window.getControl(8101):window.getControlBaseline(8101));
  if((control->languageHook==&parent)!=(corrected&&infinity))return 3;
  if(XBMCAddon::LanguageHook::GetLanguageHook()!=nullptr)return 4;
  auto* selected=dynamic_cast<XBMCAddon::xbmcgui::ControlList*>(control.get());
  if(!infinity){selected->getSelectedItem();control.reset();Py_Finalize();
    std::cout<<"original_other_skin_path_preserved\n";return 0;}
  PyThreadState* state=PyEval_SaveThread();
  std::thread gui([](){
    std::unique_lock<std::mutex> held(frame);frameHeld=true;
    while(!childAtFrame)std::this_thread::yield();
    auto gil=PyGILState_Ensure();PyGILState_Release(gil);
  });
  while(!frameHeld)std::this_thread::yield();
  std::thread child([&](){auto gil=PyGILState_Ensure();selected->getSelectedItem();PyGILState_Release(gil);done=true;});
  auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(700);
  while(!done&&std::chrono::steady_clock::now()<deadline)std::this_thread::yield();
  if(!corrected){
    if(done||!childAtFrame)return 5;
    // End this isolated baseline reproduction; no user data or files exist.
    std::cout<<"observed_locked_cycle\n"<<std::flush;std::_Exit(0);
  }
  if(!done){std::cerr<<"corrected path still blocked\n"<<std::flush;std::_Exit(6);}
  child.join();gui.join();PyEval_RestoreThread(state);control.reset();Py_Finalize();
  std::cout<<"completed_without_lock_cycle\n";return 0;
}
'''

if __name__=='__main__':unittest.main()
