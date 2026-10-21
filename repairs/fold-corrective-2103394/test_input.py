import os,subprocess,tempfile,unittest
from pathlib import Path
import input94

SHIM=r'''
#include <memory>
#include <vector>
#include <string>
#include <map>
#include <chrono>
#include <cstdint>
#include <cmath>
#include <cassert>
#define TARGET_ANDROID 1
const int WINDOW_HOME=10000,WINDOW_VIDEO_NAV=10025,WINDOW_INVALID=-1;
const int GUI_MSG_SETFOCUS=1,ACTION_CONTEXT_MENU=2,ACTION_SELECT_ITEM=3;
struct CPoint {float x,y;CPoint(float a,float b):x(a),y(b){} CPoint operator-(CPoint p){return {x-p.x,y-p.y};}};
struct Property {std::string value;std::string asString()const{return value;}};
struct Tag{std::string m_type="movie";};
struct CGUIListItem {virtual ~CGUIListItem()=default;virtual bool IsFileItem()const{return true;}};
struct CFileItem:CGUIListItem {Tag tag;std::string path="plugin://plugin.video.umbrella/?action=play&id=1",saved;
 bool HasVideoInfoTag()const{return true;} Tag* GetVideoInfoTag(){return &tag;}
 const Tag* GetVideoInfoTag()const{return &tag;} std::string GetPath()const{return path;}
 Property GetProperty(const std::string&)const{return {saved};} bool IsParentFolder()const{return false;}};
struct CGUIControl {bool visible=true,disabled=false;const CGUIControl* parent=nullptr;
 bool IsVisible()const{return visible;}bool IsDisabled()const{return disabled;}
 const CGUIControl* GetParentControl()const{return parent;}};
struct Transform {float scale=2,origin=40;void InverseTransformPosition(float& x,float& y){x=(x-origin)/scale;y=y/scale;}};
struct CGUIMessage {int id;CGUIMessage(int,int,int c):id(c){}};
struct Window {int focused=0,view=55;void OnMessage(const CGUIMessage&m){focused=m.id;}int GetFocusedControlID(){return focused;}int GetViewContainerID(){return view;}};
struct Manager {int active=WINDOW_VIDEO_NAV,modal=WINDOW_INVALID;Window window;
 Window* GetWindow(int){return &window;}int GetActiveWindow(){return active;}int GetTopmostModalDialog(){return modal;}};
struct Gui{Manager manager;Manager& GetWindowManager(){return manager;}};
struct Settings {std::string skin="skin.infinity.diggz";std::string GetString(const std::string&){return skin;}};
struct SettingsComponent {Settings settings;Settings* GetSettings(){return &settings;}};
struct CServiceBroker {static Gui gui;static SettingsComponent settings;
 static Gui* GetGUI(){return &gui;}static SettingsComponent* GetSettingsComponent(){return &settings;}};
Gui CServiceBroker::gui;SettingsComponent CServiceBroker::settings;
auto testNow=std::chrono::steady_clock::time_point(std::chrono::seconds(100));
struct CGUIBaseContainer:CGUIControl {
 int parentID=WINDOW_VIDEO_NAV,id=55,selected=0,scroll=0,opens=0,contexts=0;
 bool processed=true,m_gestureActive=false,m_waitForScrollEnd=true;
 float m_posX=0,m_posY=0;Transform m_cachedTransform;
 std::vector<std::shared_ptr<CGUIListItem>> m_items;
 std::string m_infinityMediaTapKey;
 std::chrono::steady_clock::time_point m_infinityMediaTappedAt{},m_infinityMediaSuppressUntil{};
 CGUIBaseContainer(){for(int i=0;i<4;++i){auto item=std::make_shared<CFileItem>();item->path+=std::to_string(i);m_items.push_back(item);}}
 int GetParentID()const{return parentID;}int GetID()const{return id;}bool HasProcessed()const{return processed;}
 bool CanFocusFromPoint(CPoint p)const{return p.x>=0&&p.x<300&&p.y>=0&&p.y<100;}
 int GetSelectedItem()const{return selected;}void SelectItem(int n){selected=n;}
 bool SelectItemFromPoint(CPoint p){selected=int(p.x/100)+scroll;return true;}
 bool OnClick(int action){if(action==ACTION_CONTEXT_MENU)++contexts;if(action==ACTION_SELECT_ITEM)++opens;return true;}
 bool OnInfinityMediaTouch(float,float,bool);
};
void advance(){testNow+=std::chrono::milliseconds(250);}
int main(){
 CGUIBaseContainer c;
 assert(c.OnInfinityMediaTouch(260,50,false)&&c.selected==1&&c.opens==0);advance();
 assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==1);advance();
 assert(c.OnInfinityMediaTouch(460,50,true)&&c.selected==2&&c.contexts==1&&c.opens==1);
 assert(c.OnInfinityMediaTouch(460,50,false)&&c.opens==1);testNow+=std::chrono::seconds(1);
 assert(c.OnInfinityMediaTouch(460,50,false)&&c.opens==1);advance();
 assert(c.OnInfinityMediaTouch(460,50,false)&&c.opens==2);
 c.scroll=1;advance();assert(c.OnInfinityMediaTouch(260,50,false)&&c.selected==2&&c.opens==2);
 c.m_gestureActive=true;assert(!c.OnInfinityMediaTouch(260,50,false));c.m_gestureActive=false;
 auto item=std::static_pointer_cast<CFileItem>(c.m_items[2]);item->tag.m_type="";
 int old=c.selected;assert(!c.OnInfinityMediaTouch(260,50,true)&&c.selected==old);item->tag.m_type="episode";
 for(auto type:{"movie","tvshow","season","episode"}) {item->tag.m_type=type;assert(c.OnInfinityMediaTouch(260,50,true));}
 CServiceBroker::settings.settings.skin="skin.cobra";assert(!c.OnInfinityMediaTouch(260,50,false));
 CServiceBroker::settings.settings.skin="skin.infinity.diggz";
 item->path="plugin://script.unrelated/?action=run";assert(!c.OnInfinityMediaTouch(260,50,true));
 item->path="plugin://script.infinity.commandcenter/?action=unavailable";item->saved=std::string(64,'a');
 assert(c.OnInfinityMediaTouch(260,50,true));
 c.parentID=WINDOW_HOME;c.id=8830;CServiceBroker::gui.manager.active=WINDOW_HOME;
 assert(!c.OnInfinityMediaTouch(260,50,true)); // original Resume management retained
 testNow+=std::chrono::seconds(2);assert(c.OnInfinityMediaTouch(260,50,false));
 c.id=9200;assert(!c.OnInfinityMediaTouch(260,50,false)); // Rails excluded
 c.id=8101;assert(!c.OnInfinityMediaTouch(260,50,true)); // Option B retains hold
 CServiceBroker::gui.manager.modal=10100;assert(!c.OnInfinityMediaTouch(260,50,false));
 CServiceBroker::gui.manager.modal=WINDOW_INVALID;c.visible=false;assert(!c.OnInfinityMediaTouch(260,50,false));
}
'''

class Touch(unittest.TestCase):
 def test_actual_touch_method_transforms_scroll_identity_context_and_exclusions(self):
  method=input94.METHOD
  self.assertEqual(method.count('std::chrono::steady_clock::now()'),1)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(SHIM.replace('int main(){',method.replace('std::chrono::steady_clock::now()','testNow')+'\nint main(){'))
   subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(p/'test.cpp'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True,timeout=5)
 def test_exact_source_dispatch_order_and_native_api(self):
  root=Path(os.environ['INFINITY_2103393_NATIVE'])
  paths=(input94.CONTAINER,input94.HEADER,input94.INPUT,input94.GUIWINDOW,input94.LABEL)
  before={n:(root/n).read_bytes() for n in paths};after=input94.patches(before)
  s=after[input94.INPUT]
  self.assertLess(s.index(b'OnInfinityRailLongPress'),s.index(b'OnInfinityMediaTouch'))
  self.assertLess(s.index(b'OnInfinityOptionBLongPress'),s.index(b'OnInfinityMediaTouch'))
  self.assertLess(s.index(b'OnInfinityMediaTouch'),s.index(b'// Send a mouse motion event'))
  self.assertIn(b'window->GetViewContainerID()',after[input94.CONTAINER])
  for n in paths:
   with self.assertRaises(ValueError):input94.patches(dict(before,**{n:after[n]}))

if __name__=='__main__':unittest.main()
