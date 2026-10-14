#!/usr/bin/env python3
"""Compile the actual added container method with controlled Kodi peers.

This is not an Android touch injection or a rendering acceptance test.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import patch_native

HARNESS=r'''
#include <cassert>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <iostream>
constexpr int WINDOW_HOME=10000, LOGINFO=1, TMSG_EXECUTE_BUILT_IN=1;
struct CPoint { float x,y; CPoint(float a,float b):x(a),y(b){} CPoint operator-(CPoint p){return {x-p.x,y-p.y};} };
struct Variant { std::string v; std::string asString()const{return v;} };
struct Item { std::map<std::string,std::string> props; Variant GetProperty(std::string k){return {props[k]};} };
struct CGUIControl {
 bool visible=true,disabled=false; CGUIControl* parent=nullptr;
 bool IsVisible()const{return visible;} bool IsDisabled()const{return disabled;}
 CGUIControl* GetParentControl()const{return parent;}
};
struct Transform { float scale=1,dx=0,dy=0; void InverseTransformPosition(float&x,float&y){x=(x-dx)/scale;y=(y-dy)/scale;} };
struct Messenger { std::vector<std::string> calls; void PostMsg(int,int,int,void*,std::string s){calls.push_back(s);} } messenger;
struct CServiceBroker { static Messenger* GetAppMessenger(){return &messenger;} };
struct CLog { template<class...T>static void Log(int,const char*,T...){} };
struct CGUIBaseContainer:CGUIControl {
 int parentID=10000,id=9200,selected=0; bool processed=true,m_gestureActive=false,m_waitForScrollEnd=true;
 float m_posX=10,m_posY=20; Transform m_cachedTransform;
 std::vector<std::shared_ptr<Item>> m_items;
 int GetParentID(){return parentID;} int GetID(){return id;} bool HasProcessed(){return processed;}
 bool CanFocusFromPoint(CPoint p){return p.x>=10 && p.x<210 && p.y>=20 && p.y<120;}
 int GetSelectedItem(){return selected;} void SelectItem(int i){selected=i;}
 bool SelectItemFromPoint(CPoint p){if(p.x<0||p.x>=200)return false;selected=int(p.x/100);return true;}
 bool OnInfinityRailLongPress(float,float);
};
'''

CASES=r'''
int main(){
 CGUIBaseContainer c;
 for(auto aid: {"plugin.video.first","plugin.video.second"}){
  auto row=std::make_shared<Item>();row->props={{"Infinity.Rails.Item","true"},
   {"Infinity.Rails.HoldVersion","1"},{"Infinity.Rails.Section","tvshows"},
   {"Infinity.Rails.Key",std::string("c:")+aid},{"Addon.ID",aid}};c.m_items.push_back(row);
 }
 assert(c.OnInfinityRailLongPress(160,50));assert(c.selected==1);assert(messenger.calls.size()==1);
 assert(messenger.calls.back()=="RunScript(script.infinity.rails,options,tvshows,c:plugin.video.second,plugin.video.second)");
 assert(!c.m_waitForScrollEnd);
 assert(c.OnInfinityRailLongPress(160,50));assert(messenger.calls.size()==2);
 for(int id:{9200,8820,8720,19601}){c.id=id;assert(c.OnInfinityRailLongPress(60,50));}
 const auto count=messenger.calls.size();
 c.id=19600;assert(!c.OnInfinityRailLongPress(60,50));c.id=9200;
 c.visible=false;assert(!c.OnInfinityRailLongPress(60,50));c.visible=true;
 CGUIControl parent;c.parent=&parent;parent.visible=false;assert(!c.OnInfinityRailLongPress(60,50));parent.visible=true;
 parent.disabled=true;assert(!c.OnInfinityRailLongPress(60,50));parent.disabled=false;
 c.processed=false;assert(!c.OnInfinityRailLongPress(60,50));c.processed=true;
 c.m_gestureActive=true;assert(!c.OnInfinityRailLongPress(60,50));c.m_gestureActive=false;
 c.parentID=10025;assert(!c.OnInfinityRailLongPress(60,50));c.parentID=10000;
 assert(!c.OnInfinityRailLongPress(300,50));assert(messenger.calls.size()==count);
 c.selected=1;c.m_items[0]->props["Infinity.Rails.HoldVersion"]="";
 assert(!c.OnInfinityRailLongPress(60,50));assert(c.selected==1);
 c.m_items[0]->props["Infinity.Rails.HoldVersion"]="1";
 c.m_items[0]->props["Infinity.Rails.Key"]="c:plugin.video.first),Quit(";
 assert(!c.OnInfinityRailLongPress(60,50));assert(c.selected==1);
 c.m_items[0]->props["Infinity.Rails.Key"]="b:0123456789abcdef";
 c.m_cachedTransform={2,100,200};assert(c.OnInfinityRailLongPress(220,300));assert(c.selected==0);
 assert(messenger.calls.back()=="RunScript(script.infinity.rails,options,tvshows,b:0123456789abcdef,plugin.video.first)");
 std::cout<<"PASS actual rail method: changed selection, selected card, four controls, hidden parent, disabled parent, inactive view, pan rejection, outside hit, legacy fallback, command rejection, transformed point, exact identity\n";
}
'''

def verify(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    text=(root/'xbmc/guilib/GUIBaseContainer.cpp').read_text()
    assert patch_native.METHOD in text
    input_text=(root/'xbmc/input/InputManager.cpp').read_text()
    assert patch_native.DISPATCH in input_text
    assert input_text.index('INFINITY_RAIL_HOLD_V1') < input_text.index('m_touchTranslator->TranslateTouchAction',input_text.index('case XBMC_TOUCH:'))
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);cpp=tmp/'test.cpp';binary=tmp/'test'
        cpp.write_text(HARNESS+patch_native.METHOD+CASES)
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(binary)],check=True)
        result=subprocess.check_output([str(binary)],text=True)
    (out/'RAILS-NATIVE-HOST.txt').write_text(result)
    (out/'RAILS-NATIVE-HOST.json').write_text(json.dumps(dict(passed=True,
      actual_method_compiled=True,controlled_peers=True,android_touch_injected=False,
      physical_fold_accepted=False),indent=2)+'\n')
    print(result)

if __name__=='__main__':
    import sys
    verify(sys.argv[1],sys.argv[2])
