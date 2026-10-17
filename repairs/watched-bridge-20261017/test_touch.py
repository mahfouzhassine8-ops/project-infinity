"""Compile actual production preselection and original right-click branch."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import touch_patch

HARNESS = r'''
#include <cassert>
#include <iostream>
#include <vector>
constexpr int WINDOW_HOME=10000, ACTION_MOUSE_RIGHT_CLICK=101, ACTION_MOUSE_LEFT_CLICK=100,
  ACTION_MOUSE_DOUBLE_CLICK=103, ACTION_MOUSE_LONG_CLICK=104, EVENT_RESULT_HANDLED=1, EVENT_RESULT_UNHANDLED=0;
using EVENT_RESULT=int;
namespace MOUSE { struct CMouseEvent {int m_id;}; }
struct CPoint {float x,y; CPoint(float a,float b):x(a),y(b){} CPoint operator-(CPoint p)const{return {x-p.x,y-p.y};}};
struct CGUIControl {
 bool visible=true,disabled=false; CGUIControl* parent=nullptr;
 bool IsVisible()const{return visible;} bool IsDisabled()const{return disabled;}
 CGUIControl* GetParentControl()const{return parent;}
};
struct Transform {float scale=1,dx=0,dy=0;void InverseTransformPosition(float&x,float&y){x=(x-dx)/scale;y=(y-dy)/scale;}};
struct CGUIBaseContainer:CGUIControl {
 int parentID=11193,id=50,selected=0,offset=0,clicks=0,lastAction=0;
 bool processed=true,m_gestureActive=false,m_waitForScrollEnd=true;
 float m_posX=10,m_posY=20; Transform m_cachedTransform; std::vector<int> m_items{0,1,2,3};
 int GetParentID(){return parentID;} int GetID(){return id;} bool HasProcessed(){return processed;}
 int GetSelectedItem(){return selected;} void SelectItem(int i){selected=i;}
 bool CanFocusFromPoint(CPoint p){return p.x>=10&&p.x<210&&p.y>=20&&p.y<120;}
 bool SelectItemFromPoint(CPoint p){if(p.x<0||p.x>=200||p.y<0||p.y>=100)return false;selected=offset+int(p.x/100);return true;}
 void OnClick(int id){++clicks;lastAction=id;}
 bool PrepareInfinityBrowseLongPress(float,float);
 EVENT_RESULT OnMouseEvent(const CPoint&,const MOUSE::CMouseEvent&);
};
'''

CASES = r'''
int main(){
 CGUIBaseContainer c; const MOUSE::CMouseEvent right{101};
 c.OnMouseEvent({160,50},right);assert(c.selected==1&&c.clicks==0); // actual baseline defect
 c.selected=0;assert(c.PrepareInfinityBrowseLongPress(160,50));c.OnMouseEvent({160,50},right);
 assert(c.selected==1&&c.clicks==1&&c.lastAction==101); // first hold on other column
 assert(c.PrepareInfinityBrowseLongPress(160,50));c.OnMouseEvent({160,50},right);assert(c.clicks==2);
 c.offset=2;c.selected=0;assert(c.PrepareInfinityBrowseLongPress(160,50));c.OnMouseEvent({160,50},right);
 assert(c.selected==3&&c.clicks==3); // after scrolling
 c.offset=0;c.m_cachedTransform={2,100,200};assert(c.PrepareInfinityBrowseLongPress(420,300));
 c.OnMouseEvent({160,50},right);assert(c.clicks==4&&c.selected==1);
 c.m_cachedTransform={1,0,0};assert(c.PrepareInfinityBrowseLongPress(10,50));
 assert(c.selected==0);assert(!c.PrepareInfinityBrowseLongPress(210,50));assert(c.selected==0);
 CGUIControl parent;c.parent=&parent;parent.visible=false;assert(!c.PrepareInfinityBrowseLongPress(160,50));parent.visible=true;
 parent.disabled=true;assert(!c.PrepareInfinityBrowseLongPress(160,50));parent.disabled=false;
 c.m_gestureActive=true;assert(!c.PrepareInfinityBrowseLongPress(160,50));c.m_gestureActive=false;
 c.processed=false;assert(!c.PrepareInfinityBrowseLongPress(160,50));c.processed=true;
 c.parentID=10000;assert(!c.PrepareInfinityBrowseLongPress(160,50));c.parentID=11193;
 c.id=51;assert(!c.PrepareInfinityBrowseLongPress(160,50));c.id=50;
 c.selected=0;c.OnMouseEvent({160,50},right);assert(c.selected==1&&c.clicks==4); // ordinary mouse untouched
 assert(c.PrepareInfinityBrowseLongPress(160,50));assert(c.clicks==4); // preselection itself never dispatches
 std::cout<<"{\"passed\":true,\"actual_right_click_branch_compiled\":true,\"baseline_first_hold_defect_reproduced\":true,\"candidate_single_context_dispatch\":true,\"transformed_scroll_edge_visibility_gesture_controls\":true,\"physical_fold_verified\":false}\n";
}
'''


def verify(root, output):
    root, output = Path(root), Path(output)
    text = (root / "xbmc/guilib/GUIBaseContainer.cpp").read_text()
    if touch_patch.METHOD not in text:
        raise ValueError("Actual staged production method missing")
    signature = "EVENT_RESULT CGUIBaseContainer::OnMouseEvent("
    start = text.index(signature)
    end = text.index("  else if", start)
    branch = text[start:end] + "  return EVENT_RESULT_UNHANDLED;\n}\n"
    input_text = (root / "xbmc/input/InputManager.cpp").read_text()
    assert touch_patch.DISPATCH in input_text
    assert input_text.index("INFINITY_BROWSE_HOLD_V1") > input_text.index("m_touchTranslator->TranslateTouchAction", input_text.index("case XBMC_TOUCH:"))
    with tempfile.TemporaryDirectory() as td:
        cpp, binary = Path(td) / "hold.cpp", Path(td) / "hold"
        cpp.write_text(HARNESS + touch_patch.METHOD + branch + CASES)
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(binary)], check=True)
        result = json.loads(subprocess.check_output([str(binary)], text=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    verify(args.runtime, args.output)
