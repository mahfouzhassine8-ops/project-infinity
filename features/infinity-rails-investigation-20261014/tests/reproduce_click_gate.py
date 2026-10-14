"""Compile unchanged production mouse-click branch; not an Android/UI test."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'native-source/GUIBaseContainer.cpp').read_text()
start = source.index('EVENT_RESULT CGUIBaseContainer::OnMouseEvent')
end = source.index('  else if', start)
method = source[start:end] + '  return EVENT_RESULT_UNHANDLED;\n}\n'
fixture = r'''
#include <cassert>
#include <iostream>
enum {ACTION_MOUSE_LEFT_CLICK=100, ACTION_MOUSE_DOUBLE_CLICK=101, ACTION_MOUSE_RIGHT_CLICK=102};
enum EVENT_RESULT {EVENT_RESULT_UNHANDLED, EVENT_RESULT_HANDLED};
struct CPoint {float x,y; CPoint(float a,float b):x(a),y(b){} CPoint operator-(const CPoint& b)const{return {x-b.x,y-b.y};}};
namespace MOUSE {struct CMouseEvent {int m_id;};}
class CGUIBaseContainer {
public:
 bool m_waitForScrollEnd=true; float m_posX=0,m_posY=0; int selected=0, clicked=0;
 int GetSelectedItem(){return selected;}
 bool SelectItemFromPoint(const CPoint& p){if(p.x<0)return false;selected=(int)p.x;return true;}
 void OnClick(int){++clicked;}
 EVENT_RESULT OnMouseEvent(const CPoint&,const MOUSE::CMouseEvent&);
};
// METHOD
int main(){
 CGUIBaseContainer c;
 assert(c.OnMouseEvent({1,0},{ACTION_MOUSE_RIGHT_CLICK})==EVENT_RESULT_HANDLED);
 assert(c.selected==1 && c.clicked==0); std::cout<<"unselected right-click consumed without callback: PASS\n";
 c.OnMouseEvent({1,0},{ACTION_MOUSE_RIGHT_CLICK}); assert(c.clicked==1);
 std::cout<<"second right-click on selected card calls callback: PASS\n";
 c.OnMouseEvent({2,0},{ACTION_MOUSE_LEFT_CLICK}); assert(c.selected==2 && c.clicked==2);
 std::cout<<"single tap selects and dispatches: PASS\n";
 assert(c.OnMouseEvent({-1,0},{ACTION_MOUSE_RIGHT_CLICK})==EVENT_RESULT_UNHANDLED && c.clicked==2);
 std::cout<<"outside hit area does not dispatch: PASS\n";
}
'''.replace('// METHOD', method)
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / 'click.cpp'; path.write_text(fixture)
    binary = Path(tmp) / 'click'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(path),'-o',str(binary)],check=True)
    result = subprocess.run([str(binary)],check=True,capture_output=True,text=True)
    print(result.stdout)
    print(json.dumps({'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                      'cases':4,'physical_device_verified':False,
                      'limitations':'Hit testing, coordinate transforms and surrounding dispatch are adapters; this reproduces a conditional code path, not the observed device incident.'}))
