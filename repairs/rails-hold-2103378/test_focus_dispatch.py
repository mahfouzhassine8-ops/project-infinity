#!/usr/bin/env python3
"""Compile production touch routing with a nonfocused Home rail, preserving fallthrough."""
import json
from pathlib import Path
import subprocess
import tempfile
import patch_native

HARNESS = r'''
#include <cassert>
#include <initializer_list>
#include <map>
#include <string>
#include <iostream>
constexpr int WINDOW_HOME=10000, WINDOW_INVALID=-1, ACTION_TOUCH_LONGPRESS=100;
struct CGUIControl {virtual ~CGUIControl()=default;};
struct CGUIBaseContainer:CGUIControl {
  int id,calls=0;bool hit;float x=0,y=0;
  CGUIBaseContainer(int i,bool h):id(i),hit(h){}
  bool OnInfinityRailLongPress(float X,float Y){x=X;y=Y;++calls;return hit;}
};
struct Home {
  std::map<int,CGUIControl*> controls;CGUIControl* focused=nullptr;
  CGUIControl* GetControl(int id){auto it=controls.find(id);return it==controls.end()?nullptr:it->second;}
  CGUIControl* GetFocusedControl(){return focused;}
};
struct WindowManager {
  int active=WINDOW_HOME,modal=WINDOW_INVALID;Home home;
  int GetActiveWindow(){return active;}
  int GetTopmostModalDialog(){return modal;}
  Home* GetWindow(int id){return id==WINDOW_HOME?&home:nullptr;}
};
struct GUI {WindowManager wm;WindowManager& GetWindowManager(){return wm;}};
struct Settings {std::string skin="skin.infinity.diggz";std::string GetString(const char*){return skin;}};
struct SettingsComponent {Settings settings;Settings* GetSettings(){return &settings;}};
struct CServiceBroker {
  static GUI* GetGUI(){static GUI x;return &x;}
  static SettingsComponent* GetSettingsComponent(){static SettingsComponent x;return &x;}
};
struct Touch {int action,pointers;float x,y;};
struct Event {Touch touch;};
int fallthrough=0;
bool route(Event newEvent)
{
  int old=fallthrough;
  switch(0){case 0:{
__PRODUCTION_RAIL_DISPATCH__
    fallthrough++;break;
  }}
  return fallthrough==old;
}
int main(){
 auto& wm=CServiceBroker::GetGUI()->GetWindowManager();CGUIControl tab;
 CGUIBaseContainer normal(9200,true),compact(8820,false),two(8720,false),cinema(19601,false);
 wm.home.controls={{9200,&normal},{8820,&compact},{8720,&two},{19601,&cinema}};
 wm.home.focused=&tab;
 assert(route({{ACTION_TOUCH_LONGPRESS,1,160,330}}));
 assert(normal.calls==1&&normal.x==160&&normal.y==330&&fallthrough==0);
 normal.hit=false;cinema.hit=true;
 assert(route({{ACTION_TOUCH_LONGPRESS,1,48,500}}));
 assert(cinema.calls==1&&fallthrough==0);
 cinema.hit=false;
 assert(!route({{ACTION_TOUCH_LONGPRESS,1,160,330}}));assert(fallthrough==1);
 wm.modal=1234;normal.hit=true;
 assert(!route({{ACTION_TOUCH_LONGPRESS,1,160,330}}));assert(fallthrough==2);
 wm.modal=WINDOW_INVALID;wm.active=9999;
 assert(!route({{ACTION_TOUCH_LONGPRESS,1,160,330}}));assert(fallthrough==3);
 wm.active=WINDOW_HOME;
 CServiceBroker::GetSettingsComponent()->GetSettings()->skin="other.skin";
 assert(!route({{ACTION_TOUCH_LONGPRESS,1,160,330}}));assert(fallthrough==4);
 CServiceBroker::GetSettingsComponent()->GetSettings()->skin="skin.infinity.diggz";
 assert(!route({{ACTION_TOUCH_LONGPRESS,2,160,330}}));assert(fallthrough==5);
 wm.home.controls.clear();
 assert(!route({{ACTION_TOUCH_LONGPRESS,1,160,330}}));assert(fallthrough==6);
 std::cout<<"PASS: nonfocused rail hit, other rail, miss, modal, Home, skin, multitouch, missing rails, original fallthrough"<<std::endl;
}
'''

def verify(root,out):
    root=Path(root)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    input_cpp=(root/'xbmc/input/InputManager.cpp').read_text()
    assert patch_native.DISPATCH in input_cpp
    assert 'GetFocusedControl()' not in patch_native.DISPATCH
    assert 'INFINITY_RAIL_HOLD_V2' in patch_native.DISPATCH
    assert 'GetControl(railID)' in patch_native.DISPATCH
    cpp=HARNESS.replace('__PRODUCTION_RAIL_DISPATCH__',patch_native.DISPATCH)
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/'focus.cpp';binary=Path(td)/'focus'
        src.write_text(cpp)
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                        str(src),'-o',str(binary)],check=True)
        log=subprocess.check_output([str(binary)],text=True)
    (out/'RAILS-FOCUS-DISPATCH.txt').write_text(log)
    (out/'RAILS-FOCUS-DISPATCH.json').write_text(json.dumps(dict(
        passed=True,production_dispatch_compiled=True,
        focused_control_independent=True,outside_rail_fallthrough=True,
        android_touch_injected=False,physical_fold_accepted=False
    ),indent=2)+'\n')
    print(log.strip())

if __name__=='__main__':
    import sys
    verify(sys.argv[1],sys.argv[2])
