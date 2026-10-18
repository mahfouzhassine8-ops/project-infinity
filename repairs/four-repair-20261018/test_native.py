"""Compile the production gesture/context methods; tests are not Android proof."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('four_ui_patch_test', HERE / 'native_patch.py')
patch = importlib.util.module_from_spec(spec); spec.loader.exec_module(patch)

HARNESS = r'''
#include <cassert>
#include <initializer_list>
#include <map>
#include <memory>
#include <string>
#include <vector>
constexpr int WINDOW_HOME=10000,ACTION_SELECT_ITEM=7,TMSG_EXECUTE_BUILT_IN=1;
struct CPoint {float x,y; CPoint(float a,float b):x(a),y(b){} CPoint operator-(CPoint o)const{return {x-o.x,y-o.y};}};
struct Value {std::string v; std::string asString()const{return v;}};
struct Item {std::map<std::string,Value> p; Value GetProperty(const char* k)const{auto it=p.find(k);return it==p.end()?Value{}:it->second;}};
struct Window:Item {};
struct WM {std::map<int,Window> windows;Window* GetWindow(int id){return &windows[id];}};
struct GUI {WM wm;WM& GetWindowManager(){return wm;}};
struct Messenger {std::vector<std::string> calls;void PostMsg(int,int,int,void*,std::string s){calls.push_back(s);}};
struct CServiceBroker {static GUI* GetGUI(){static GUI x;return &x;}static Messenger* GetAppMessenger(){static Messenger x;return &x;}};
struct CGUIControl {bool visible=true,disabled=false,focus=false;CGUIControl* parent=nullptr;
 bool IsVisible()const{return visible;}bool IsDisabled()const{return disabled;}
 CGUIControl* GetParentControl()const{return parent;}bool OnMouseOver(CPoint){focus=true;return true;}};
struct Transform {float scale=1,dx=0,dy=0;void InverseTransformPosition(float&x,float&y){x=(x-dx)/scale;y=(y-dy)/scale;}};
struct CGUIBaseContainer:CGUIControl {
 int parentID=11193,id=50,selected=0,offset=0,clicks=0,last=0;bool processed=true,m_gestureActive=false,m_waitForScrollEnd=false;
 float m_posX=10,m_posY=20;Transform m_cachedTransform;std::vector<std::shared_ptr<Item>> m_items;
 std::string m_infinityUiTapKey;
 int GetParentID(){return parentID;}int GetID(){return id;}bool HasProcessed(){return processed;}
 int GetSelectedItem(){return selected;}void SelectItem(int n){selected=n;}
 bool CanFocusFromPoint(CPoint p){return p.x>=10&&p.x<210&&p.y>=20&&p.y<120;}
 bool SelectItemFromPoint(CPoint p){if(p.x<0||p.x>=200||p.y<0||p.y>=100)return false;selected=offset+int(p.x/100);return true;}
 void OnClick(int action){assert(action==ACTION_SELECT_ITEM);++clicks;last=selected;}
 bool OnInfinityUiTouch(float,float,bool);bool OnInfinityUiContextMenu();
};
std::shared_ptr<Item> make(std::string kind,std::string key){auto i=std::make_shared<Item>();i->p={{"Infinity.UI.Version",{"1"}},{"Infinity.UI.Kind",{kind}},{"Infinity.UI.Token",{key}},{"Addon.ID",{key}}};return i;}
'''

CASES = r'''
int main(){
 CGUIBaseContainer c;c.m_items={make("addon","plugin.video.left"),make("addon","plugin.video.right"),make("addon","plugin.video.third"),make("addon","plugin.video.fourth")};
 assert(c.OnInfinityUiTouch(160,50,false));assert(c.selected==1&&c.clicks==0&&c.focus); // right first selects
 assert(c.OnInfinityUiTouch(160,50,false));assert(c.clicks==1&&c.last==1); // second launches once
 assert(c.OnInfinityUiTouch(160,50,false));assert(c.clicks==1); // new sequence after returning
 assert(c.OnInfinityUiTouch(60,50,false));assert(c.selected==0&&c.clicks==1); // different tile only selects
 assert(c.OnInfinityUiTouch(60,50,true));assert(c.clicks==1);
 assert(CServiceBroker::GetAppMessenger()->calls.back()=="RunScript(script.infinity.uirepair,addon,plugin.video.left)");
 const auto selection=c.selected;assert(c.selected==selection&&c.offset==0); // modal does not rebuild parent
 c.offset=2;c.m_infinityUiTapKey.clear();assert(c.OnInfinityUiTouch(160,50,false));assert(c.selected==3&&c.clicks==1);
 assert(c.OnInfinityUiTouch(160,50,false));assert(c.clicks==2&&c.last==3);
 c.offset=0;c.m_infinityUiTapKey.clear();c.m_cachedTransform={2,100,200};
 assert(c.OnInfinityUiTouch(420,300,false));assert(c.selected==1&&c.clicks==2);
 assert(c.OnInfinityUiTouch(420,300,false));assert(c.clicks==3);
 c.m_cachedTransform={1,0,0};assert(!c.OnInfinityUiTouch(210,50,false));
 c.processed=false;assert(!c.OnInfinityUiTouch(60,50,false));c.processed=true;
 c.m_gestureActive=true;assert(!c.OnInfinityUiTouch(60,50,false));c.m_gestureActive=false;
 CGUIControl owner;c.parent=&owner;owner.visible=false;assert(!c.OnInfinityUiTouch(60,50,true));owner.visible=true;
 owner.disabled=true;assert(!c.OnInfinityUiTouch(60,50,true));owner.disabled=false;
 c.m_items[0]->p["Infinity.UI.Version"]={""};assert(!c.OnInfinityUiTouch(60,50,true));
 c.parentID=10000;c.id=8830;c.selected=1;c.m_items={make("resume",std::string(64,'a')),make("resume",std::string(64,'b'))};
 assert(!c.OnInfinityUiTouch(60,50,false)); // normal Resume/Play path untouched
 assert(c.OnInfinityUiTouch(60,50,true));assert(c.selected==0);
 assert(CServiceBroker::GetAppMessenger()->calls.back()=="RunScript(script.infinity.uirepair,resume,"+std::string(64,'a')+")");
 c.id=8831;assert(c.OnInfinityUiTouch(160,50,true));assert(c.selected==1); // TV
 c.m_items[1]->p["Infinity.UI.Token"]={"bad),Quit("};assert(!c.OnInfinityUiTouch(160,50,true));
 c.parentID=13000;c.id=50;c.selected=0;c.m_infinityUiTapKey.clear();c.m_items={make("action","0"),make("action","1")};
 CServiceBroker::GetGUI()->wm.windows[13000].p["Infinity.UI.Popup"]={"1"};
 const int prior=c.clicks;assert(c.OnInfinityUiTouch(60,50,false));assert(c.clicks==prior);
 assert(c.OnInfinityUiTouch(160,50,false));assert(c.clicks==prior); // focus is not invocation
 assert(c.OnInfinityUiTouch(160,50,false));assert(c.clicks==prior+1);
 c.OnClick(ACTION_SELECT_ITEM);assert(c.clicks==prior+2); // unchanged explicit D-pad activation
 c.parentID=9999;assert(!c.OnInfinityUiTouch(60,50,false));
}
'''

def verify(root=None, output=None):
    if root:
        root = Path(root)
        assert patch.METHOD in (root / patch.FILES[1]).read_text()
        source = (root / patch.FILES[0]).read_text()
        assert patch.DISPATCH in source
        assert source.index('INFINITY_UI_TOUCH_V1') < source.index('// Send a mouse motion event', source.index('case XBMC_TOUCH:'))
        assert 'm_infinityUiTapKey.clear();' in (root / patch.FILES[1]).read_text()
    with tempfile.TemporaryDirectory() as td:
        cpp, binary = Path(td) / 'input.cpp', Path(td) / 'input'
        cpp.write_text(HARNESS + patch.METHOD + CASES)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    result = dict(passed=True, production_gesture_methods_compiled=True,
                  left_right_columns=True, transformed_scrolled_coordinates=True,
                  first_tap_select_second_activate=True, popup_focus_does_not_invoke=True,
                  original_resume_taps_untouched=True, outside_scope_falls_through=True,
                  android_injection=False, physical_fold_verified=False)
    if output: Path(output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == '__main__': verify()
