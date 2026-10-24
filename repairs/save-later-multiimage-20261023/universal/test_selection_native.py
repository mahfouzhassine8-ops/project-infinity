"""Compile actual patched selection method, with explicit controlled GUI stubs.

This verifies native event/identity decisions and exact source boundaries. It
does not claim Android rendering, touch delivery or physical Fold acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('selection_native_patch', HERE.parent / 'final_eight_native.py')
native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
SOURCE = None
EVIDENCE = {}
PATCH_SHA = hashlib.sha256((HERE.parent / 'final_eight_native.py').read_bytes()).hexdigest()
TEST_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

SHIM = r'''
#include <cassert>
#include <chrono>
#include <cstdint>
#include <initializer_list>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>
#define TARGET_ANDROID 1
const int WINDOW_HOME=10000,WINDOW_VIDEO_NAV=10025,WINDOW_INVALID=-1;
const int GUI_MSG_SETFOCUS=1,ACTION_CONTEXT_MENU=2,ACTION_SELECT_ITEM=3;
struct CPoint {float x,y;CPoint(float a,float b):x(a),y(b){} CPoint operator-(CPoint p){return {x-p.x,y-p.y};}};
struct Property {std::string value;std::string asString()const{return value;}};
struct Tag {
  std::string m_type="movie";int m_iSeason=-1,m_iEpisode=-1;std::map<std::string,std::string> ids;
  std::string GetUniqueID(const std::string& n)const{auto i=ids.find(n);return i==ids.end()?"":i->second;}
};
struct CGUIListItem {virtual ~CGUIListItem()=default;virtual bool IsFileItem()const{return true;}};
struct CFileItem:CGUIListItem {
  Tag tag;std::string path;std::map<std::string,std::string> props;bool parent=false,video=true;
  bool HasVideoInfoTag()const{return video;}Tag* GetVideoInfoTag(){return &tag;}
  const Tag* GetVideoInfoTag()const{return &tag;}std::string GetPath()const{return path;}
  Property GetProperty(const std::string& n)const{auto i=props.find(n);return {i==props.end()?"":i->second};}
  bool IsParentFolder()const{return parent;}
};
struct CGUIControl {bool visible=true,disabled=false;const CGUIControl* parent=nullptr;
  bool IsVisible()const{return visible;}bool IsDisabled()const{return disabled;}
  const CGUIControl* GetParentControl()const{return parent;}};
struct Transform {float scale=2,origin=40;void InverseTransformPosition(float& x,float& y){x=(x-origin)/scale;y=y/scale;}};
struct CGUIMessage {int id;CGUIMessage(int,int,int c):id(c){}};
struct Directory {std::string path;std::string GetPath()const{return path;}};
struct Window {virtual ~Window()=default;int focused=0,view=55;Directory directory;std::map<std::string,std::string> props;
  void OnMessage(const CGUIMessage&m){focused=m.id;}int GetFocusedControlID(){return focused;}int GetViewContainerID(){return view;}
  const Directory& CurrentDirectory()const{return directory;}
  Property GetProperty(const std::string& n)const{auto i=props.find(n);return {i==props.end()?"":i->second};}};
using CGUIMediaWindow=Window;
struct Manager {int active=WINDOW_VIDEO_NAV,modal=WINDOW_INVALID;Window window,home;
  Window* GetWindow(int n){return n==WINDOW_HOME?&home:&window;}
  int GetActiveWindow(){return active;}int GetTopmostModalDialog(){return modal;}};
struct Gui{Manager manager;Manager& GetWindowManager(){return manager;}};
struct Settings {std::string skin="skin.infinity.diggz";std::string GetString(const std::string&){return skin;}};
struct SettingsComponent {Settings settings;Settings* GetSettings(){return &settings;}};
namespace ADDON {
  struct OnlyEnabled {enum class CHOICE_YES_t {YES};static constexpr auto CHOICE_YES=CHOICE_YES_t::YES;};
  struct Version {std::string text;std::string asString()const{return text;}};
  struct Addon {std::string version="0.3.5.34";ADDON::Version Version()const{return {version};}
    std::string ID()const{return "script.infinity.commandcenter";}std::string Path()const{return "/verified/cc";}};
  using AddonPtr=std::shared_ptr<Addon>;
}
struct AddonMgr {bool enabled=true;ADDON::AddonPtr addon=std::make_shared<ADDON::Addon>();
  bool GetAddon(const std::string&,ADDON::AddonPtr& result,ADDON::OnlyEnabled::CHOICE_YES_t){result=addon;return enabled;}};
struct CServiceBroker {static Gui gui;static SettingsComponent settings;static AddonMgr addons;
  static Gui* GetGUI(){return &gui;}static SettingsComponent* GetSettingsComponent(){return &settings;}
  static AddonMgr& GetAddonMgr(){return addons;}};
Gui CServiceBroker::gui;SettingsComponent CServiceBroker::settings;AddonMgr CServiceBroker::addons;
std::vector<std::shared_ptr<CFileItem>> popupCopies;
struct CContextMenuItem {
  static CContextMenuItem CreateItem(const std::string&,const std::string&,const std::string& path,
    const std::string&,const std::string&,std::initializer_list<std::string> args){
    assert(path=="/verified/cc/context.py");assert(args.size()==2);return {};}
  bool Execute(std::shared_ptr<CFileItem> item)const{popupCopies.push_back(item);return true;}
};
struct URIUtils{static std::string AddFileToFolder(const std::string& a,const std::string& b){return a+"/"+b;}};
auto testNow=std::chrono::steady_clock::time_point(std::chrono::seconds(100));
struct CGUIBaseContainer:CGUIControl {
  int parentID=WINDOW_VIDEO_NAV,id=55,selected=0,scroll=0,opens=0,contexts=0;
  bool processed=true,m_gestureActive=false,m_waitForScrollEnd=true;
  float m_posX=0,m_posY=0;Transform m_cachedTransform;
  std::vector<std::shared_ptr<CGUIListItem>> m_items;
  std::string m_infinityMediaTapKey;
  std::chrono::steady_clock::time_point m_infinityMediaTappedAt{},m_infinityMediaSuppressUntil{};
  CGUIBaseContainer(){for(int i=0;i<5;++i){auto item=std::make_shared<CFileItem>();
    item->path="plugin://plugin.video.umbrella/?action=play&id="+std::to_string(i+1);
    item->tag.ids["tmdb"]=std::to_string(i+1);item->props["Infinity.ResumeHub.Key"]=std::string(64,'a'+i);m_items.push_back(item);}}
  int GetParentID()const{return parentID;}int GetID()const{return id;}bool HasProcessed()const{return processed;}
  bool CanFocusFromPoint(CPoint p)const{return p.x>=0&&p.x<300&&p.y>=0&&p.y<100;}
  int GetSelectedItem()const{return selected;}void SelectItem(int n){selected=n;}
  bool SelectItemFromPoint(CPoint p){selected=int(p.x/100)+scroll;return true;}
  bool OnClick(int action){if(action==ACTION_CONTEXT_MENU)++contexts;if(action==ACTION_SELECT_ITEM)++opens;return true;}
  bool OnInfinityMediaTouch(float,float,bool);
  std::shared_ptr<CFileItem> item(int n){return std::static_pointer_cast<CFileItem>(m_items[n]);}
};
void advance(int milliseconds=250){testNow+=std::chrono::milliseconds(milliseconds);}
void reset(){CServiceBroker::gui=Gui();CServiceBroker::settings=SettingsComponent();
 CServiceBroker::addons=AddonMgr();popupCopies.clear();advance(10000);}
void ownedDirectory(){CServiceBroker::gui.manager.window.directory.path="plugin://script.infinity.commandcenter/?action=library";}
void capsule(CGUIBaseContainer& c){for(int i=0;i<5;++i){c.item(i)->props["Infinity.Selection.Contract"]="1";
 c.item(i)->props["Infinity.Selection.Snapshot"]="exact-typed-identity-and-source-"+std::to_string(i);}}
'''

CASES = r'''
int main(){
  // Default focus is not a tap. Recreated same-title rows preserve identity;
  // a new title at the same coordinates/route must not inherit an armed tap.
  {reset();ownedDirectory();CGUIBaseContainer c;
   assert(c.OnInfinityMediaTouch(60,50,false)&&c.opens==0);advance();
   c.m_items[0]=std::make_shared<CFileItem>(*c.item(0));
   assert(c.OnInfinityMediaTouch(60,50,false)&&c.opens==1);advance();
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.selected==1&&c.opens==1);advance();
   c.item(1)->tag.ids["tmdb"]="unrelated-identity";
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==1);advance();
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==2);}

  // Preserve the already established debounce and re-arm timing exactly.
  for(int milliseconds:{119,120,5000,5001}){
   reset();ownedDirectory();CGUIBaseContainer c;
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==0);advance(milliseconds);
   assert(c.OnInfinityMediaTouch(260,50,false));
   assert(c.opens==((milliseconds>=120&&milliseconds<=5000)?1:0));}

  // A scrolled/reordered neighbour cannot be activated by the prior tap.
  {reset();ownedDirectory();CGUIBaseContainer c;
   assert(c.OnInfinityMediaTouch(260,50,false));advance();c.scroll=1;
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.selected==2&&c.opens==0);advance();
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==1);}

  // Hold delivers a copy, retains selection/scroll, and suppresses release tap.
  {reset();ownedDirectory();CGUIBaseContainer c;c.scroll=1;
   assert(c.OnInfinityMediaTouch(260,50,true)&&c.selected==2&&c.scroll==1&&c.contexts==0&&c.opens==0);
   assert(popupCopies.size()==1&&popupCopies.back().get()!=c.item(2).get());
   auto original=popupCopies.back()->path;c.item(2)->path="changed-after-copy";
   assert(popupCopies.back()->path==original);
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==0);advance(601);
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==0);advance();
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==1);}

  // Each actual Infinity Movies/TV Home rail uses the same owned handler.
  for(int id:{8103,8104,8603,8604,8703,8704,8803,8804,8721,8722,8821,8822,9201,9202,8830,8831}){
   reset();CGUIBaseContainer c;c.parentID=WINDOW_HOME;c.id=id;CServiceBroker::gui.manager.active=WINDOW_HOME;capsule(c);
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==0);advance();
   assert(c.OnInfinityMediaTouch(260,50,false)&&c.opens==1);advance();
   assert(c.OnInfinityMediaTouch(460,50,true)&&popupCopies.size()==1&&c.selected==2&&c.contexts==0);}

  // Synthetic/unsupported rows without the capsule cannot create title actions.
  {reset();CGUIBaseContainer c;c.parentID=WINDOW_HOME;c.id=8103;CServiceBroker::gui.manager.active=WINDOW_HOME;
   assert(!c.OnInfinityMediaTouch(260,50,true)&&popupCopies.empty()&&c.selected==0);}

  // Search/CC result types retain their exact original provider paths.
  for(const auto& type:{"movie","tvshow","episode","season"}){
   reset();ownedDirectory();CGUIBaseContainer c;c.item(1)->tag.m_type=type;
   assert(c.OnInfinityMediaTouch(260,50,true)&&popupCopies.size()==1&&popupCopies.back()->path==c.item(1)->path);}

  // Dedicated Browse-all window uses only CC saved capsules or Latest proof.
  {reset();CGUIBaseContainer c;c.parentID=WINDOW_HOME+1193;c.id=50;capsule(c);
   CServiceBroker::gui.manager.active=c.parentID;
   CServiceBroker::gui.manager.home.props["Infinity.BrowsePath"]="plugin://script.infinity.commandcenter/?action=library";
   assert(c.OnInfinityMediaTouch(260,50,true)&&popupCopies.size()==1);
   CServiceBroker::gui.manager.home.props["Infinity.BrowsePath"]="addons://sources/video";
   assert(!c.OnInfinityMediaTouch(460,50,true)&&popupCopies.size()==1&&c.selected==1);}
  for(int id:{8101,8102,8601,8602,8701,8702,8801,8802,50}){
   reset();CGUIBaseContainer c;c.parentID=id==50?WINDOW_HOME+1193:WINDOW_HOME;c.id=id;
   CServiceBroker::gui.manager.active=c.parentID;
   CServiceBroker::gui.manager.home.props["Infinity.BrowsePath"]="plugin://plugin.infinity.latestreleases/?action=feed";
   auto i=c.item(1);i->path="plugin://plugin.infinity.latestreleases/?exact=wrapped";
   i->props["Infinity.LatestReleases.Identity"]="v1";i->props["Infinity.LatestReleases.Kind"]="movie";
   assert(c.OnInfinityMediaTouch(260,50,true)&&popupCopies.size()==1);}

  // Real ordinary Kodi library/provider context and CC33 fallback stay original.
  for(const auto& path:{"videodb://movies/titles/7", "plugin://plugin.video.cobra/?original=7", "plugin://plugin.video.umbrella/?original=7"}){
   reset();CGUIBaseContainer c;c.item(1)->path=path;CServiceBroker::gui.manager.window.directory.path=path;
   assert(c.OnInfinityMediaTouch(260,50,true)&&c.contexts==1&&popupCopies.empty());}
  {reset();ownedDirectory();CGUIBaseContainer c;CServiceBroker::addons.addon->version="0.3.5.33";
   assert(c.OnInfinityMediaTouch(260,50,true)&&c.contexts==1&&popupCopies.empty());}
  {reset();ownedDirectory();CGUIBaseContainer c;CServiceBroker::settings.settings.skin="skin.cobra";
   assert(!c.OnInfinityMediaTouch(260,50,true)&&c.contexts==0&&popupCopies.empty()&&c.selected==0);}
  for(int id:{8720,8820,9200,19600,19601}){
   reset();CGUIBaseContainer c;c.parentID=WINDOW_HOME;c.id=id;CServiceBroker::gui.manager.active=WINDOW_HOME;capsule(c);
   assert(!c.OnInfinityMediaTouch(260,50,true)&&popupCopies.empty());}

  // Modal, scrolling, non-title command, hidden parent and outside hits are inert.
  {reset();ownedDirectory();CGUIBaseContainer c;CServiceBroker::gui.manager.modal=10100;
   assert(!c.OnInfinityMediaTouch(260,50,true));CServiceBroker::gui.manager.modal=WINDOW_INVALID;
   c.m_gestureActive=true;assert(!c.OnInfinityMediaTouch(260,50,true));c.m_gestureActive=false;
   c.item(1)->tag.m_type="";assert(!c.OnInfinityMediaTouch(260,50,true)&&c.selected==0);c.item(1)->tag.m_type="movie";
   CGUIControl owner;owner.visible=false;c.parent=&owner;assert(!c.OnInfinityMediaTouch(260,50,true));c.parent=nullptr;
   assert(!c.OnInfinityMediaTouch(-10,50,true));c.item(1)->parent=true;
   assert(!c.OnInfinityMediaTouch(260,50,true)&&c.selected==0&&popupCopies.empty());}
  std::cout << "PASS: compiled actual method; 14 Home rails + Resume + Latest + Browse + Search types; selection/hold/copy/legacy isolation" << std::endl;
}
'''


def method(text):
    start = text.index('bool CGUIBaseContainer::OnInfinityMediaTouch(')
    end = text.index('\nbool CGUIBaseContainer::', start + 10)
    return text[start:end].strip()


class NativeSelection(unittest.TestCase):
    def test_compiled_actual_method_and_exact_preimages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'overlay'
            ledger = native.apply(SOURCE, out)
            EVIDENCE.update(patch_source_sha256=PATCH_SHA, test_source_sha256=TEST_SHA,
                            patched_source_sha256={name: value['final_sha256'] for name, value in ledger.items()})
            self.assertEqual(set(ledger), {native.PATH, native.INPUT_PATH})
            old = (SOURCE / native.PATH).read_text(); new = (out / native.PATH).read_text()
            # Every exact replacement reverses to the signed baseline, including
            # all unrelated and original legacy branches in both compiler files.
            for path, replacements in ((native.PATH, native.REPLACEMENTS), (native.INPUT_PATH, native.INPUT_REPLACEMENTS)):
                restored = (out / path).read_text()
                for before, after in reversed(replacements):
                    self.assertEqual(restored.count(after), 1)
                    restored = restored.replace(after, before)
                self.assertEqual(restored.encode(), (SOURCE / path).read_bytes())
            actual = method(new)
            original = method(old)
            self.assertIn(original[original.index('  if ((!provider && !library && !local)'):], actual)
            # Only the test clock is substituted; all production decisions,
            # identity building and exact-copy helper execute unchanged.
            body = actual.replace('std::chrono::steady_clock::now()', 'testNow')
            cpp = root / 'selection.cpp'
            cpp.write_text(SHIM + native.HELPER + body + '\n' + CASES)
            EVIDENCE.update(production_method_sha256=hashlib.sha256(actual.encode()).hexdigest(),
                            compiled_test_source_sha256=hashlib.sha256(cpp.read_bytes()).hexdigest())
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                            str(cpp), '-o', str(root / 'selection')], check=True, timeout=60)
            result = subprocess.run([str(root / 'selection')], check=True, capture_output=True, text=True, timeout=10)
            print(result.stdout.strip())
            altered = root / 'changed-source'
            for path in (native.PATH, native.INPUT_PATH):
                target = altered / path; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((SOURCE / path).read_bytes())
            path = altered / native.PATH; path.write_bytes(path.read_bytes() + b'\n// changed source\n')
            with self.assertRaises(RuntimeError): native.apply(altered, root / 'rejected-overlay')
            self.assertEqual(PATCH_SHA, hashlib.sha256((HERE.parent / 'final_eight_native.py').read_bytes()).hexdigest())
            self.assertEqual(TEST_SHA, hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--source', type=Path, required=True)
    SOURCE = parser.parse_args().source.resolve()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeSelection))
    (HERE / 'SELECTION-NATIVE-HOST.json').write_text(json.dumps(dict(
        host='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
        scope='Actual patched C++ selection method compiled against controlled GUI/API stubs; signed source preimages verified',
        source_sha256={p: hashlib.sha256((SOURCE / p).read_bytes()).hexdigest() for p in (native.PATH, native.INPUT_PATH)},
        **EVIDENCE,
        android17='NOT RUN', physical_fold='NOT RUN', shutdown='NOT RUN'), indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
