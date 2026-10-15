#!/usr/bin/env python3
"""Compile actual resolver/label/textbox/cache handlers with small GUI adapters.

No physical-rendering claim: fonts, file-item lookup and GUI dirty-region storage
are adapters. The regression-critical setter order and cache handlers are real.
"""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from text_reflow import transform, method_span

STUB = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
struct CPoint { float x,y; CPoint(float a,float b):x(a),y(b){} };
struct CRect {
 float x1=0,y1=0,x2=0,y2=0;
 CRect()=default; CRect(float a,float b,float c,float d):x1(a),y1(b),x2(c),y2(d){}
 void SetRect(float a,float b,float c,float d){x1=a;y1=b;x2=c;y2=d;}
 CRect& operator+=(CPoint p){x1+=p.x;x2+=p.x;y1+=p.y;y2+=p.y;return *this;}
 bool operator!=(const CRect& r)const{return x1!=r.x1||y1!=r.y1||x2!=r.x2||y2!=r.y2;}
};
struct GUIResponsiveAxisSpec {
 std::string start,end,centerStart,centerEnd,size,legacyPos,sizeMin,sizeMax;
 bool HasAny() const{return !start.empty()||!end.empty()||!centerStart.empty()||!centerEnd.empty()||!size.empty()||!legacyPos.empty();}
};
struct GUIResponsiveHitRectSpec {bool enabled=false;std::string x,y,width,height,right,bottom;};
struct GUIResponsiveLayoutSpec {
 bool enabled=false,legacyPosXSubtractWidth=false;
 GUIResponsiveAxisSpec horizontal,vertical;GUIResponsiveHitRectSpec hitRect;
};
struct CGUIControl {
 float m_posX=0,m_posY=0,m_width=0,m_height=0;CRect m_hitRect;unsigned m_hitColor=0;
 GUIResponsiveLayoutSpec m_responsiveLayoutSpec;int dirty=0,invalid=0;
 virtual ~CGUIControl()=default;
 virtual void SetWidth(float);virtual void SetHeight(float);virtual void SetPosition(float,float);
 virtual bool ReflowResponsiveLayout(float,float);
 void SetHitRect(const CRect& r,unsigned){m_hitRect=r;}
 virtual void SetInvalid(){invalid++;}void MarkDirtyRegion(){dirty++;}
};
constexpr unsigned XBFONT_RIGHT=1,XBFONT_CENTER_X=2;
struct LabelInfo{unsigned align=0;unsigned textColor=0;};
struct LabelAdapter {
 CRect rect;LabelInfo info;bool invalid=false;int selected=1;bool scroll=true;
 const LabelInfo& GetLabelInfo()const{return info;}
 bool SetMaxRect(float x,float y,float w,float h){CRect old=rect;rect=CRect(x,y,x+w,y+h);return old!=rect;}
 void SetInvalid(){invalid=true;}
};
struct CGUIListLabel:CGUIControl {
 LabelAdapter m_label;std::string boundText="selected item";
 void SetWidth(float)override;bool ReflowResponsiveLayout(float,float)override;
};
struct CharsetAdapter {void utf8ToW(const std::string& in,std::wstring& out,bool){out.assign(in.begin(),in.end());}};
CharsetAdapter g_charsetConverter;
struct CGUITextLayout {
 std::string m_lastUtf8Text;bool m_lastUpdateW=false;float lastWrapWidth=0;
 std::vector<int> m_lines;int updates=0;unsigned m_textColor=0;
 bool Update(const std::string&,float,bool=false,bool=false);
 void UpdateCommon(const std::wstring& text,float width,bool){
  lastWrapWidth=width;updates++;const auto cols=std::max(1,static_cast<int>(width/10));
  m_lines.resize((text.size()+static_cast<size_t>(cols)-1)/static_cast<size_t>(cols));
 }
};
struct CGUIListItem {std::string text;};
struct InfoAdapter {
 std::string text;
 std::string GetItemLabel(const CGUIListItem* item)const{return item->text;}
 std::string GetLabel(int)const{return text;}
};
struct FontAdapter {float line=10;float GetLineHeight()const{return line;}float GetTextHeight(size_t n)const{return line*static_cast<float>(n);}};
struct CGUITextBox:CGUIControl,CGUITextLayout {
 LabelInfo m_label;InfoAdapter m_info;int m_parentID=10000;
 bool m_infinityResponsiveTextLayoutDirty=false;
 unsigned m_offset=0,m_itemsPerPage=0;float m_scrollOffset=0,m_scrollSpeed=0;
 float m_itemHeight=10,m_renderHeight=40,m_minHeight=0;
 FontAdapter font;FontAdapter* m_font=&font;int autoResets=0,pages=0;
 void ResetAutoScrolling(){autoResets++;}void UpdatePageControl(){pages++;}
 bool ReflowResponsiveLayout(float,float)override;void UpdateInfo(const CGUIListItem* item=nullptr);
};
#define CLAMP(x,low,high) (((x)>(high))?(high):(((x)<(low))?(low):(x)))
'''

TEST = r'''
bool near(float a,float b){return std::abs(a-b)<0.002f;}
int main(){
 int checks=0;
 const std::vector<CPoint> sizes={{1056,2456},{1528,1696},{2456,1056},{1696,1528},{692,1536},{480,800},{800,480}};
 for(unsigned alignment:{0u,XBFONT_CENTER_X,XBFONT_RIGHT})for(auto start:sizes)for(auto end:sizes){
  CGUIListLabel label;label.m_label.info.align=alignment;
  auto& spec=label.m_responsiveLayoutSpec;spec.enabled=true;
  spec.horizontal.start="3%";spec.horizontal.size="94%";
  spec.vertical.start="72%";spec.vertical.size="24%";
  for(auto size:{start,end,start}){
   label.ReflowResponsiveLayout(size.x,size.y);
   const auto& r=label.m_label.rect;
   assert(near(r.x1,label.m_posX)&&near(r.y1,label.m_posY));
   assert(near(r.x2-r.x1,label.m_width)&&near(r.y2-r.y1,label.m_height));
   assert(near(r.x1,size.x*.03f)&&near(r.y1,size.y*.72f));
   assert(near(label.m_hitRect.x2-label.m_hitRect.x1,label.m_width));
   assert(label.boundText=="selected item"&&label.m_label.selected==1&&label.m_label.scroll);
  }
  label.m_label.invalid=false;const auto invalid=label.invalid;
  assert(!label.ReflowResponsiveLayout(start.x,start.y));
  assert(!label.m_label.invalid&&label.invalid==invalid);checks++;
 }
 // Explicit custom hit rectangles remain the resolver's responsibility.
 CGUIListLabel hit;auto& hs=hit.m_responsiveLayoutSpec;hs.enabled=true;
 hs.horizontal.start="10";hs.horizontal.size="300";hs.vertical.size="80";
 hs.hitRect.enabled=true;hs.hitRect.x="25";hs.hitRect.y="12";hs.hitRect.width="50";hs.hitRect.height="40";
 hit.ReflowResponsiveLayout(500,300);assert(hit.m_hitRect.x1==25&&hit.m_hitRect.x2==75);checks++;
 // No responsive ownership: old SetWidth semantics are unchanged.
 CGUIListLabel legacy;legacy.m_posX=400;legacy.m_label.info.align=XBFONT_RIGHT;
 legacy.SetWidth(100);assert(legacy.m_label.rect.x1==300);
 assert(!legacy.ReflowResponsiveLayout(900,800)&&legacy.m_label.rect.x1==300);checks++;

 for(auto start:sizes)for(auto end:sizes){
  CGUITextBox box;auto& spec=box.m_responsiveLayoutSpec;spec.enabled=true;
  spec.horizontal.start="3%";spec.horizontal.size="50%";
  spec.vertical.start="20%";spec.vertical.size="10%";
  CGUIListItem item{std::string(10000,'x')};
  box.ReflowResponsiveLayout(start.x,start.y);box.UpdateInfo(&item);
  box.m_offset=9;box.m_scrollOffset=92.5f;box.m_scrollSpeed=0;const auto resets=box.autoResets;
  for(auto size:{end,start}){
   box.ReflowResponsiveLayout(size.x,size.y);box.UpdateInfo(&item);
   assert(near(box.lastWrapWidth,box.m_width));
   assert(near(box.m_renderHeight,box.m_height));
   assert(box.m_offset==9&&near(box.m_scrollOffset,92.5f));
   assert(box.autoResets==resets);assert(!box.m_infinityResponsiveTextLayoutDirty);
  }
  const auto updates=box.updates;assert(!box.ReflowResponsiveLayout(start.x,start.y));box.UpdateInfo(&item);
  assert(box.updates==updates);checks++;
  // Real content change still resets the established textbox viewport.
  box.ReflowResponsiveLayout(end.x,end.y);item.text="New item";box.UpdateInfo(&item);
  assert(box.m_offset==0&&box.m_scrollOffset==0&&box.autoResets==resets+1);checks++;
 }
 CGUITextBox tall;auto& ts=tall.m_responsiveLayoutSpec;ts.enabled=true;
 ts.horizontal.size="100";ts.vertical.size="100%";tall.m_info.text=std::string(1000,'x');
 tall.ReflowResponsiveLayout(100,40);tall.UpdateInfo();tall.m_offset=75;tall.m_scrollOffset=750;
 tall.ReflowResponsiveLayout(100,500);tall.UpdateInfo();
 assert(tall.m_renderHeight==500&&tall.m_offset==50&&tall.m_scrollOffset==500);checks++;
 const auto calls=tall.updates;ts.horizontal.start="20%";
 tall.ReflowResponsiveLayout(200,500);tall.UpdateInfo();assert(tall.updates==calls);checks++;
 std::cout<<"PASS "<<checks<<" compiled text cache/geometry/viewport scenarios\n";
}
'''

def extract(source, signature):
    start, end = method_span(source, signature)
    return source[start:end]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    root = args.source
    def read(name):
        path = root / 'xbmc/guilib' / name
        if not path.exists():
            path = root / name
        return path.read_text()
    repair = Path(__file__).resolve().parents[1] / 'inplace-reflow-2103291/inplace_reflow.py'
    spec = importlib.util.spec_from_file_location('inplace', repair)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    control = read('GUIControl.cpp')
    if 'bool CGUIControl::ReflowResponsiveLayout(' not in control:
        control = module.patch_control_cpp(control)
    helper_start = control.index('namespace\n{\nfloat InfinityResponsiveParse')
    helper_end = control.index('} // namespace', helper_start) + len('} // namespace')
    body = [control[helper_start:helper_end]]
    for method in ('void CGUIControl::SetWidth(', 'void CGUIControl::SetHeight(',
                   'void CGUIControl::SetPosition(', 'bool CGUIControl::ReflowResponsiveLayout('):
        body.append(extract(control, method))
    label = transform('xbmc/guilib/GUIListLabel.cpp', read('GUIListLabel.cpp'))
    textbox = transform('xbmc/guilib/GUITextBox.cpp', read('GUITextBox.cpp'))
    layout = read('GUITextLayout.cpp')
    for source, methods in ((label, ('void CGUIListLabel::SetWidth(', 'bool CGUIListLabel::ReflowResponsiveLayout(')),
                            (textbox, ('bool CGUITextBox::ReflowResponsiveLayout(', 'void CGUITextBox::UpdateInfo(')),
                            (layout, ('bool CGUITextLayout::Update(',))):
        body.extend(extract(source, method) for method in methods)
    with tempfile.TemporaryDirectory() as directory:
        cpp = Path(directory) / 'text.cpp'
        cpp.write_text(STUB + '\n'.join(body) + TEST)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-O2', str(cpp), '-o', directory+'/text'], check=True)
        subprocess.run([directory+'/text'], check=True)

if __name__ == '__main__':
    main()
