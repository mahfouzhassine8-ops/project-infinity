// The test runner inserts the actual production SendMouseEvent body below.
#include <vector>
#include <cassert>
#include <iostream>
struct CPoint { float x,y; CPoint(float a=0,float b=0):x(a),y(b){}
  CPoint operator-(const CPoint& p)const{return {x-p.x,y-p.y};} };
namespace MOUSE { struct CMouseEvent {}; }
using EVENT_RESULT=int;
constexpr int EVENT_RESULT_UNHANDLED=0,VERTICAL=1,HORIZONTAL=0;
struct Transform { void InverseTransformPosition(float&,float&){} };
struct Scroll {float offset=0;float GetValue()const{return offset;}};
struct CGUIControl {
  float w=100,h=60; int delivered=0;
  bool CanFocus(){return true;} bool IsVisible(){return true;}
  EVENT_RESULT SendMouseEvent(const CPoint& p,const MOUSE::CMouseEvent&) {
    if(p.x>=0&&p.x<w&&p.y>=0&&p.y<h){++delivered;return 1;}return 0;
  }
};
struct CGUIControlGroupList:CGUIControl {
  using ciControls=std::vector<CGUIControl*>::iterator;
  std::vector<CGUIControl*> m_children;Transform m_transform;Scroll m_scroller;
  float m_posX=10,m_posY=20,m_width=100,m_height=100,m_itemGap=0,alignment=0;
  int m_orientation=VERTICAL,m_focusedControl=0;
  float GetAlignOffset(){return alignment;}
  float Size()const{return m_orientation==VERTICAL?m_height:m_width;}
  float Size(CGUIControl* c)const{return m_orientation==VERTICAL?c->h:c->w;}
  bool IsControlOnScreen(float p,CGUIControl* c){return p>=m_scroller.GetValue()&&p+Size(c)<=m_scroller.GetValue()+Size();}
  bool HitTest(CPoint p){return p.x>=m_posX&&p.y>=m_posY&&p.x<m_posX+m_width&&p.y<m_posY+m_height;}
  EVENT_RESULT OnMouseEvent(CPoint,const MOUSE::CMouseEvent&){return 0;}
  EVENT_RESULT SendMouseEvent(const CPoint&,const MOUSE::CMouseEvent&);
};
// PRODUCTION_METHOD
int main(){
  for(int orientation:{VERTICAL,HORIZONTAL}) {
    CGUIControlGroupList list;list.m_orientation=orientation;list.m_scroller.offset=30;
    CGUIControl first,second,third;
    if(orientation==HORIZONTAL){first.w=second.w=third.w=60;first.h=second.h=third.h=100;}
    list.m_children={&first,&second,&third};
    auto touch=[&](float axis,float cross=50){return list.SendMouseEvent(
      orientation==VERTICAL?CPoint(10+cross,20+axis):CPoint(10+axis,20+cross),{});};
    assert(touch(1)==1&&first.delivered==1);   // visible part of first row
    assert(touch(50)==1&&second.delivered==1);// complete middle row
    assert(touch(99)==1&&third.delivered==1); // visible part of last row
    assert(touch(-1)==0&&touch(100)==0);     // clipped portions must not activate
    assert(touch(50,-1)==0&&touch(50,100)==0);// perpendicular clipping too
    list.m_scroller.offset=60;
    assert(touch(1)==1&&second.delivered==2);
    assert(first.delivered==1);             // completely hidden row untouched
    list.m_height=list.m_width=40;          // resize to smaller viewport
    assert(touch(39,20)==1&&touch(40,20)==0);
  }
  std::cout<<"PASS: production scrolling-row dispatch, both axes, partial rows, clipping and resize\n";
}
