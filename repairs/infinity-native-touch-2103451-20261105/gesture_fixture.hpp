// Host test boundaries only. These are not production headers or a Kodi runtime.
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cmath>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

constexpr int WINDOW_HOME=10000, WINDOW_VIDEO_NAV=10025, WINDOW_FAVOURITES=10060, WINDOW_INVALID=-1;
constexpr int GUI_MSG_SETFOCUS=1, GUI_MSG_LOSTFOCUS=2, ACTION_SELECT_ITEM=7, ACTION_CONTEXT_MENU=117;
constexpr int ACTION_TOUCH_TAP=401, ACTION_TOUCH_LONGPRESS=411;
struct Value { std::string value; std::string asString() const { return value; } };
struct CPoint { float x,y; CPoint(float a,float b):x(a),y(b){} CPoint operator-(CPoint p) const {return {x-p.x,y-p.y};} };
struct Transform {
  float scale=1,translation=0;
  void InverseTransformPosition(float& x,float& y) const { x=(x-translation)/scale;y=(y-translation)/scale; }
};
struct CGUIMessage {
  int kind,sender,target;
  CGUIMessage(int a,int b,int c):kind(a),sender(b),target(c){}
  int GetMessage() const {return kind;}
  int GetControlId() const {return sender;}
  int GetParam1() const {return target;}
};
struct CGUIControl {
  bool visible=true,disabled=false;
  CGUIControl* ancestor=nullptr;
  virtual ~CGUIControl()=default;
  bool IsVisible() const {return visible;}
  bool IsDisabled() const {return disabled;}
  const CGUIControl* GetParentControl() const {return ancestor;}
};
struct Tag {
  std::string m_type;
  int m_iSeason=0,m_iEpisode=0;
  std::string GetUniqueID(const std::string&) const {return "fixture-id";}
};
struct CGUIListItem {
  bool file=true;
  virtual ~CGUIListItem()=default;
  bool IsFileItem() const {return file;}
};
struct CFileItem : CGUIListItem {
  std::string path;
  Tag tag;
  bool tagged=false,parent=false,favourite=false,m_bIsFolder=false;
  std::map<std::string,std::string> properties;
  bool HasVideoInfoTag() const {return tagged;}
  const Tag* GetVideoInfoTag() const {return &tag;}
  bool IsParentFolder() const {return parent;}
  bool IsFavourite() const {return favourite;}
  const std::string& GetPath() const {return path;}
  Value GetProperty(const std::string& key) const {auto i=properties.find(key);return {i==properties.end()?"":i->second};}
};
struct CGUIBaseContainer : CGUIControl {
  int parentID=WINDOW_VIDEO_NAV,id=50,selected=0;
  bool processed=true,m_gestureActive=false,focused=true,m_waitForScrollEnd=true;
  float m_posX=0,m_posY=0;
  Transform m_cachedTransform;
  std::vector<std::shared_ptr<CGUIListItem>> m_items;
  std::vector<std::pair<int,std::string>> actions;
  std::string m_infinityMediaTapKey;
  std::chrono::steady_clock::time_point m_infinityMediaTappedAt{},m_infinityMediaSuppressUntil{};
  int GetParentID() const {return parentID;}
  int GetID() const {return id;}
  int GetSelectedItem() const {return selected;}
  bool HasProcessed() const {return processed;}
  bool HasFocus() const {return focused;}
  bool CanFocusFromPoint(CPoint p) const {return p.x>=m_posX && p.x<m_posX+300 && p.y>=m_posY && p.y<m_posY+100*m_items.size();}
  bool SelectItemFromPoint(CPoint p) {int i=static_cast<int>(std::floor(p.y/100));if(i<0 || i>=static_cast<int>(m_items.size()))return false;selected=i;return true;}
  void SelectItem(int value) {selected=value;}
  void OnClick(int action) {actions.emplace_back(action,std::static_pointer_cast<CFileItem>(m_items[selected])->path);}
  void LoseFocusTo(int target);
  bool OnInfinityMediaTouch(float x,float y,bool hold);
};
struct CGUIWindow {
  int view=50,focus=50;
  bool refuseFocus=false;
  std::map<int,CGUIControl*> controls;
  std::map<std::string,std::string> properties;
  virtual ~CGUIWindow()=default;
  int GetViewContainerID() const {return view;}
  int GetFocusedControlID() const {return focus;}
  CGUIControl* GetControl(int id) {auto i=controls.find(id);return i==controls.end()?nullptr:i->second;}
  Value GetProperty(const std::string& key) const {auto i=properties.find(key);return {i==properties.end()?"":i->second};}
  void OnMessage(CGUIMessage& message) {
    if(refuseFocus)return;
    auto* old=dynamic_cast<CGUIBaseContainer*>(GetControl(focus));
    if(old)old->LoseFocusTo(message.target);
    focus=message.target;
    auto* next=dynamic_cast<CGUIBaseContainer*>(GetControl(focus));
    if(next)next->focused=true;
  }
};
struct CGUIMediaWindow : CGUIWindow {
  CFileItem directory;
  const CFileItem& CurrentDirectory() const {return directory;}
};
struct WindowManager {
  int active=WINDOW_VIDEO_NAV,modal=WINDOW_INVALID;
  std::map<int,CGUIWindow*> windows;
  int GetActiveWindow() const {return active;}
  int GetTopmostModalDialog() const {return modal;}
  CGUIWindow* GetWindow(int id) {auto i=windows.find(id);return i==windows.end()?nullptr:i->second;}
};
struct Settings { std::string skin="skin.infinity.diggz";std::string GetString(const std::string&) const {return skin;} };
struct SettingsComponent { Settings settings; Settings* GetSettings(){return &settings;} };
struct GUI { WindowManager wm; WindowManager& GetWindowManager(){return wm;} };
struct CApplicationPowerHandling { bool screensaver=false;bool IsInScreenSaver() const {return screensaver;} };
struct AppComponents {
  std::shared_ptr<CApplicationPowerHandling> power=std::make_shared<CApplicationPowerHandling>();
  template<class T> std::shared_ptr<T> GetComponent(){return power;}
};
inline GUI fixtureGUI;
inline SettingsComponent fixtureSettings;
inline AppComponents fixtureComponents;
struct CServiceBroker {
  static GUI* GetGUI(){return &fixtureGUI;}
  static SettingsComponent* GetSettingsComponent(){return &fixtureSettings;}
  static AppComponents& GetAppComponents(){return fixtureComponents;}
};
inline bool titleOwnerReady=false;
inline std::vector<std::string> titlePopups;
static bool InfinityTitleOwnerReady(){return titleOwnerReady;}
static void InfinityOpenTitlePopup(const std::shared_ptr<CFileItem>& item){titlePopups.push_back(item->path);}
struct Event { struct Touch {int action=ACTION_TOUCH_TAP,pointers=1;float x=25,y=50;} touch; };
