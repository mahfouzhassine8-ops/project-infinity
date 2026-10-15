#!/usr/bin/env python3
"""Compile and exercise the exact patched C++ methods, not Python substitutes."""
from pathlib import Path
import argparse, subprocess, tempfile
from container_reflow import transform

def method(s,name):
    start=s.index('void '+name+'()'); brace=s.index('{',start);depth=1;i=brace+1
    while depth:
        depth+=(s[i]=='{')-(s[i]=='}');i+=1
    return s[start:i]

STUB=r'''
#include <algorithm>
#include <cassert>
#include <iostream>
#include <vector>
enum ORIENTATION{HORIZONTAL,VERTICAL};
struct CGUIListItemLayout {float w=100,h=100;float Size(ORIENTATION o){return o==HORIZONTAL?w:h;}};
struct Scroller{float value=0; void SetValue(float v){value=v;}};
struct CGUIBaseContainer{
 CGUIListItemLayout layout,focus; CGUIListItemLayout *m_layout=&layout,*m_focusedLayout=&focus;
 ORIENTATION m_orientation=VERTICAL;int m_itemsPerPage=1,offset=0,cursor=0;float m_width=100,m_height=100;
 std::vector<int> m_items;Scroller m_scroller;
 virtual ~CGUIBaseContainer()=default;
 void GetCurrentLayouts(){} float Size(){return m_orientation==VERTICAL?m_height:m_width;}
 int GetOffset(){return offset;}void SetOffset(int o){offset=o;}void SetCursor(int c){cursor=c;}
 virtual int GetSelectedItem(){return offset+cursor;}
 virtual void SelectItem(int item){
  offset=std::max(0,std::min(offset,int(m_items.size())-m_itemsPerPage));
  if(item<0||item>=int(m_items.size()))return;
  if(item<offset)offset=item;
  if(item>=offset+m_itemsPerPage)offset=item-m_itemsPerPage+1;
  cursor=item-offset;
 }
 virtual void CalculateLayout();
};
struct CGUIPanelContainer:CGUIBaseContainer{
 int m_itemsPerRow=1;
 int GetSelectedItem()override{return offset*m_itemsPerRow+cursor;}
 unsigned GetRows(){return (m_items.size()+m_itemsPerRow-1)/m_itemsPerRow;}
 void CalculateLayout()override;
};
'''
TEST=r'''
int main(){
 long checks=0;
 for(auto o:{HORIZONTAL,VERTICAL}){
  for(int count=0;count<=101;count+=7)for(int oldCols=1;oldCols<=6;oldCols++)
  for(int newCols=1;newCols<=6;newCols++)for(int oldPages=1;oldPages<=5;oldPages++)
  for(int newPages=1;newPages<=5;newPages++)for(int sel=0;sel<std::max(count,1);sel++){
   CGUIPanelContainer c;c.m_orientation=o;c.m_items.resize(count);c.m_itemsPerRow=oldCols;c.m_itemsPerPage=oldPages;
   c.offset=std::max(0,std::min(sel/oldCols-oldPages/2,(count+oldCols-1)/oldCols-oldPages));c.cursor=sel-c.offset*oldCols;
   if(o==VERTICAL){c.m_width=100*newCols;c.m_height=100*newPages;}
   else{c.m_width=100*newPages;c.m_height=100*newCols;}
   c.CalculateLayout();assert(c.m_itemsPerRow==newCols);assert(c.m_itemsPerPage==newPages);
   if(count){assert(c.GetSelectedItem()==sel);assert(c.cursor>=0&&c.cursor<newCols*newPages);}
   assert(c.offset>=0);assert(c.offset<=std::max(0,int(c.GetRows())-newPages));
   if(o==VERTICAL){c.m_width=100*oldCols;c.m_height=100*oldPages;}
   else{c.m_width=100*oldPages;c.m_height=100*oldCols;}
   c.CalculateLayout();if(count)assert(c.GetSelectedItem()==sel);checks++;
  }
  for(int pages=1;pages<15;pages++)for(int next=1;next<15;next++)for(int sel=0;sel<80;sel++){
   CGUIBaseContainer c;c.m_orientation=o;c.m_items.resize(80);c.m_itemsPerPage=pages;c.offset=std::max(0,std::min(sel-pages/2,80-pages));c.cursor=sel-c.offset;
   if(o==VERTICAL)c.m_height=next*100;else c.m_width=next*100;
   c.CalculateLayout();assert(c.m_itemsPerPage==next);assert(c.GetSelectedItem()==sel);checks++;
  }
 }
 std::cout<<"PASS "<<checks<<" C++ resize/round-trip state scenarios\n";
}
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
 pieces=[]
 for name,klass in [('GUIBaseContainer.cpp','CGUIBaseContainer'),('GUIPanelContainer.cpp','CGUIPanelContainer')]:
  path=a.source/'xbmc/guilib'/name
  if not path.exists():path=a.source/name
  s=transform('xbmc/guilib/'+name,path.read_text())
  pieces.append(method(s,klass+'::CalculateLayout'))
 with tempfile.TemporaryDirectory() as d:
  f=Path(d)/'test.cpp';f.write_text(STUB+'\n'.join(pieces)+TEST)
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-O2',str(f),'-o',d+'/test'],check=True)
  subprocess.run([d+'/test'],check=True)
if __name__=='__main__':main()

# Execute the opt-in dimension method itself over cover/inner/landscape bounds.
from container_reflow import ITEM_METHOD
ITEM_STUB=r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
struct Group{float w=0,h=0;int reflows=0;void SetWidth(float v){w=v;}void SetHeight(float v){h=v;}void ReflowResponsiveLayout(float,float){reflows++;}};
struct CGUIListItemLayout{
 float m_width=310,m_height=594,m_responsiveAspect=310.0f/594.0f;
 std::string m_responsiveWidth,m_responsiveHeight;Group m_group;int focusedChild=17;bool invalid=false;
 void SetInvalid(){invalid=true;}bool ReflowResponsiveSize(float,float);
};
'''
ITEM_TEST=r'''
int main(){
 int checks=0;
 for(float width:{240.f,640.f,940.f,1361.f,2320.f})for(float height:{80.f,210.f,424.f,616.f,980.f}){
  CGUIListItemLayout l;l.m_responsiveWidth="auto";l.m_responsiveHeight="100%";
  l.ReflowResponsiveSize(width,height);
  assert(l.m_width<=width&&l.m_height<=height+0.01f);
  assert(std::abs(l.m_width/l.m_height-l.m_responsiveAspect)<0.001f);
  assert(l.focusedChild==17);auto count=l.m_group.reflows;
  assert(!l.ReflowResponsiveSize(width,height));assert(l.m_group.reflows==count);
  l.ReflowResponsiveSize(940,600);assert(l.focusedChild==17);checks++;
  CGUIListItemLayout row;row.m_responsiveWidth="100%";row.ReflowResponsiveSize(width,height);
  assert(row.m_width==width&&row.m_height==594);checks++;
  CGUIListItemLayout fixed;assert(!fixed.ReflowResponsiveSize(width,height));assert(fixed.m_width==310&&fixed.m_height==594);checks++;
 }
 std::cout<<"PASS "<<checks<<" compiled item size/preservation scenarios\n";
}
'''
if __name__=='__main__':
 with tempfile.TemporaryDirectory() as d:
  f=Path(d)/'items.cpp';f.write_text(ITEM_STUB+ITEM_METHOD+ITEM_TEST)
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-O2',str(f),'-o',d+'/items'],check=True)
  subprocess.run([d+'/items'],check=True)
