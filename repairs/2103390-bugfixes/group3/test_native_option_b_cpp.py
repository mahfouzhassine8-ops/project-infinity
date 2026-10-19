#!/usr/bin/env python3
"""Compile the exact new Group #3 C++ method with a controlled Kodi peer ABI.

This is a real C++17 syntax/runtime regression, NOT a rebuilt Android engine
or physical Fold touch injection. Test the unmodified method text verbatim.
"""
from __future__ import annotations
import subprocess
import tempfile
import unittest
from pathlib import Path
from native_option_b_patch import METHOD

PEERS = r'''
#include <cassert>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <iostream>
constexpr int WINDOW_HOME=10000, WINDOW_INVALID=9999, GUI_MSG_SETFOCUS=7,
              TMSG_EXECUTE_BUILT_IN=22;
struct CPoint {
  float x, y;
  CPoint(float a,float b):x(a),y(b){}
  CPoint operator-(CPoint r) const {return {x-r.x,y-r.y};}
};
struct CGUIControl {
  bool visible=true, disabled=false;
  CGUIControl* parent=nullptr;
  bool IsVisible() const {return visible;}
  bool IsDisabled() const {return disabled;}
  const CGUIControl* GetParentControl() const {return parent;}
};
struct Transform {
  float scale=1, dx=0, dy=0;
  void InverseTransformPosition(float& x,float& y) const {
    x=(x-dx)/scale;y=(y-dy)/scale;
  }
};
struct CGUIListItem {
  virtual ~CGUIListItem()=default;
  virtual bool IsFileItem() const {return false;}
};
struct CFileItem:CGUIListItem {
  std::string path,label;
  CFileItem(std::string p,std::string l):path(std::move(p)),label(std::move(l)){}
  bool IsFileItem() const override {return true;}
  std::string GetPath() const {return path;}
  std::string GetLabel() const {return label;}
};
struct CGUIMessage {
  int sender,control;
  CGUIMessage(int,int s,int c):sender(s),control(c){}
};
struct FakeWindow {
  int focused=9000;
  bool denyFocus=false;
  std::map<std::string,std::string> props;
  void OnMessage(CGUIMessage& msg) {
    if (!denyFocus)focused=msg.control;
  }
  int GetFocusedControlID() const {return focused;}
  void SetProperty(std::string key,std::string val){props[std::move(key)]=std::move(val);}
};
struct Manager {
  int active=WINDOW_HOME, modal=WINDOW_INVALID;
  FakeWindow home;
  int GetActiveWindow() const {return active;}
  int GetTopmostModalDialog() const {return modal;}
  FakeWindow* GetWindow(int id){return id==WINDOW_HOME?&home:nullptr;}
};
struct GUI {Manager windows;Manager& GetWindowManager(){return windows;}};
struct Messenger {
  std::vector<std::string> calls;
  void PostMsg(int,int,int,void*,std::string command){calls.push_back(std::move(command));}
};
GUI gui;
Messenger messenger;
struct CServiceBroker {
  static GUI* GetGUI(){return &gui;}
  static Messenger* GetAppMessenger(){return &messenger;}
};
namespace UTILITY {
struct CDigest {
  enum class Type{SHA256};
  static std::string Calculate(Type,const std::string& value) {
    assert(value.find("plugin://plugin.video.umbrella/")!=std::string::npos);
    return std::string(64,'a');
  }
};
}
struct CGUIBaseContainer:CGUIControl {
  int id=8101,parentId=WINDOW_HOME,selected=0;
  float m_posX=10,m_posY=20;
  bool processed=true,m_gestureActive=false,m_waitForScrollEnd=false;
  Transform m_cachedTransform;
  std::vector<std::shared_ptr<CGUIListItem>> m_items;
  int GetParentID() const {return parentId;}
  int GetID() const {return id;}
  bool HasProcessed() const {return processed;}
  bool CanFocusFromPoint(CPoint pt) const {
    return pt.x>=10 && pt.x<210 && pt.y>=20 && pt.y<120;
  }
  int GetSelectedItem() const {return selected;}
  void SelectItem(int i){selected=i;}
  bool SelectItemFromPoint(CPoint p) {
    if(p.x<0||p.x>=200||p.y<0||p.y>=100)return false;
    selected=static_cast<int>(p.x/100);return true;
  }
  bool OnInfinityOptionBLongPress(float,float);
};
'''

CASES = r'''
int main() {
  CGUIBaseContainer c;
  c.m_items.emplace_back(std::make_shared<CFileItem>(
    "plugin://plugin.video.umbrella/?action=movies&id=one","Movie One"));
  c.m_items.emplace_back(std::make_shared<CFileItem>(
    "plugin://plugin.video.umbrella/?action=movies&id=two","Movie Two"));

  assert(c.OnInfinityOptionBLongPress(160,50));
  assert(c.selected==1);
  assert(gui.windows.home.focused==8101);
  assert(messenger.calls.size()==1);
  assert(messenger.calls.back() ==
    "RunScript(script.infinity.uirepair,option-b,8101,1,"+std::string(64,'a')+")");
  assert(gui.windows.home.props["Infinity.HomeOptionB.PendingPath"] ==
    "plugin://plugin.video.umbrella/?action=movies&id=two");
  assert(gui.windows.home.props["Infinity.HomeOptionB.PendingLabel"]=="Movie Two");
  assert(gui.windows.home.props["Infinity.HomeOptionB.PendingIndex"]=="1");

  c.id=8102;
  assert(c.OnInfinityOptionBLongPress(60,50));
  assert(messenger.calls.back().find("option-b,8102,0,") != std::string::npos);
  assert(c.selected==0);
  c.id=8101;
  const auto count=messenger.calls.size();
  auto saved=gui.windows.home.props;

  c.id=9200;assert(!c.OnInfinityOptionBLongPress(160,50));c.id=8101;
  c.parentId=12345;assert(!c.OnInfinityOptionBLongPress(160,50));c.parentId=WINDOW_HOME;
  c.visible=false;assert(!c.OnInfinityOptionBLongPress(160,50));c.visible=true;
  CGUIControl parent;c.parent=&parent;parent.visible=false;
  assert(!c.OnInfinityOptionBLongPress(160,50));parent.visible=true;
  parent.disabled=true;assert(!c.OnInfinityOptionBLongPress(160,50));parent.disabled=false;
  c.processed=false;assert(!c.OnInfinityOptionBLongPress(160,50));c.processed=true;
  c.m_gestureActive=true;assert(!c.OnInfinityOptionBLongPress(160,50));c.m_gestureActive=false;
  c.m_waitForScrollEnd=true;assert(!c.OnInfinityOptionBLongPress(160,50));
  c.m_waitForScrollEnd=false;
  gui.windows.modal=1234;assert(!c.OnInfinityOptionBLongPress(160,50));
  gui.windows.modal=WINDOW_INVALID;
  gui.windows.active=11000;assert(!c.OnInfinityOptionBLongPress(160,50));
  gui.windows.active=WINDOW_HOME;
  assert(!c.OnInfinityOptionBLongPress(330,50));
  gui.windows.home.denyFocus=true;
  gui.windows.home.focused=9000;
  c.selected=0;
  assert(!c.OnInfinityOptionBLongPress(160,50));
  assert(c.selected==0);
  gui.windows.home.denyFocus=false;

  auto item=std::static_pointer_cast<CFileItem>(c.m_items[1]);
  item->path="plugin://plugin.video.other/?action=play";
  assert(!c.OnInfinityOptionBLongPress(160,50));
  assert(c.selected==0);
  item->path="plugin://plugin.video.umbrella/?action=movies&id=two";
  item->label.clear();
  assert(!c.OnInfinityOptionBLongPress(160,50));
  item->label="Movie Two";
  assert(messenger.calls.size()==count);
  assert(gui.windows.home.props==saved);
  assert(!c.OnInfinityOptionBLongPress(60,500));
  c.m_cachedTransform={2,100,200};
  assert(c.OnInfinityOptionBLongPress(220,300));
  assert(c.selected==0);
  std::cout<<"PASS actual Group3 method: Movie/TV hit index, original source identity,"
      <<" fixed proof command, focus, transform, modal/parent/scroll rejection,"
      <<" no Cobra/add-on-rail paths and no unintended dispatch\n";
}
'''

class NativeMethodPeer(unittest.TestCase):
    def test_01_real_group3_cpp_method_compiles_and_guarded_peer_cases_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'group3_test.cpp'
            exe=Path(folder)/'group3_test'
            source.write_text(PEERS+METHOD+CASES)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                            str(source),'-o',str(exe)],check=True,capture_output=True,text=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS actual Group3 method',result.stdout)

if __name__=="__main__":
    unittest.main(verbosity=2)
