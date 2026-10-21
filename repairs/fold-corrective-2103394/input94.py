"""Touch-only, typed Infinity Movie/TV interception; original actions retained."""
from native94 import once,require
CONTAINER='xbmc/guilib/GUIBaseContainer.cpp'
HEADER='xbmc/guilib/GUIBaseContainer.h'
INPUT='xbmc/input/InputManager.cpp'
GUIWINDOW='xbmc/guilib/GUIWindow.cpp'
LABEL='xbmc/guilib/GUIListLabel.cpp'
METHOD=r'''
bool CGUIBaseContainer::OnInfinityMediaTouch(float x, float y, bool hold)
{
#if defined(TARGET_ANDROID)
  auto& windows = CServiceBroker::GetGUI()->GetWindowManager();
  auto* window = windows.GetWindow(GetParentID());
  const bool video = GetParentID() == WINDOW_VIDEO_NAV && window &&
      GetID() == window->GetViewContainerID();
  const bool featured = GetParentID() == WINDOW_HOME &&
      (GetID() == 8101 || GetID() == 8102 || GetID() == 8601 || GetID() == 8602 ||
       GetID() == 8701 || GetID() == 8702 || GetID() == 8801 || GetID() == 8802);
  const bool resume = GetParentID() == WINDOW_HOME && (GetID() == 8830 || GetID() == 8831);
  if ((!video && !featured && !resume) || !window || !HasProcessed() || m_gestureActive ||
      windows.GetActiveWindow() != GetParentID() || windows.GetTopmostModalDialog() != WINDOW_INVALID ||
      CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") != "skin.infinity.diggz")
    return false;
  for (const CGUIControl* owner = this; owner; owner = owner->GetParentControl())
    if (!owner->IsVisible() || owner->IsDisabled()) return false;
  CPoint point(x,y);
  m_cachedTransform.InverseTransformPosition(point.x,point.y);
  if (!CanFocusFromPoint(point)) return false;
  const int previous = GetSelectedItem();
  if (!SelectItemFromPoint(point-CPoint(m_posX,m_posY))) return false;
  const int selected = GetSelectedItem();
  const auto reject = [this,previous]() { SelectItem(previous); return false; };
  if (selected < 0 || selected >= static_cast<int>(m_items.size()) ||
      !m_items[selected] || !m_items[selected]->IsFileItem()) return reject();
  const auto item = std::static_pointer_cast<CFileItem>(m_items[selected]);
  if (!item->HasVideoInfoTag()) return reject();
  const std::string type = item->GetVideoInfoTag()->m_type;
  if (type != "movie" && type != "tvshow" && type != "season" && type != "episode")
    return reject(); // search/history/command entries are not media records
  const std::string path = item->GetPath();
  const auto* mediaWindow = video ? dynamic_cast<const CGUIMediaWindow*>(window) : nullptr;
  const std::string directory = mediaWindow ? mediaWindow->CurrentDirectory().GetPath() : "";
  const bool provider = path.compare(0,22,"plugin://plugin.video.") == 0 ||
      directory.compare(0,22,"plugin://plugin.video.") == 0;
  const bool library = path.compare(0,10,"videodb://") == 0 || directory.compare(0,10,"videodb://") == 0;
  const std::string saved = item->GetProperty("Infinity.ResumeHub.Key").asString();
  const bool local = saved.size() == 64 && saved.find_first_not_of("0123456789abcdef") == std::string::npos &&
      (resume || directory.compare(0,39,"plugin://script.infinity.commandcenter/") == 0);
  if ((!provider && !library && !local) || path.size() > 8192 || item->IsParentFolder()) return reject();
  if (hold && (featured || resume)) return reject(); // existing Option B / Resume management owns holds
  const auto now = std::chrono::steady_clock::now();
  m_waitForScrollEnd = false;
  CGUIMessage focus(GUI_MSG_SETFOCUS,GetParentID(),GetID());
  window->OnMessage(focus);
  if (GetSelectedItem() != selected || window->GetFocusedControlID() != GetID()) return reject();
  const std::string key = type + "\n" + path + "\n" + std::to_string(selected) + "\n" +
      std::to_string(reinterpret_cast<std::uintptr_t>(item.get()));
  if (hold)
  {
    m_infinityMediaTapKey.clear();
    m_infinityMediaSuppressUntil = now + std::chrono::milliseconds(600);
    OnClick(ACTION_CONTEXT_MENU); // original exact-item provider/native context, no Select
    return true;
  }
  if (now < m_infinityMediaSuppressUntil) return true;
  const auto elapsed = now-m_infinityMediaTappedAt;
  const bool open = previous == selected && m_infinityMediaTapKey == key &&
      elapsed >= std::chrono::milliseconds(120) && elapsed <= std::chrono::seconds(5);
  m_infinityMediaTapKey = key;
  m_infinityMediaTappedAt = now;
  if (open)
  {
    m_infinityMediaTapKey.clear();
    OnClick(ACTION_SELECT_ITEM); // existing action once; no route construction
  }
  return true;
#else
  return false;
#endif
}
'''
DISPATCH=r'''
#if defined(TARGET_ANDROID)
      // INFINITY_2103394_MEDIA_TOUCH: before synthetic hover can change the
      // prior selection. Only the active media view or explicit Home posters.
      if ((newEvent.touch.action == ACTION_TOUCH_TAP || newEvent.touch.action == ACTION_TOUCH_LONGPRESS) &&
          newEvent.touch.pointers == 1 &&
          CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") == "skin.infinity.diggz")
      {
        auto& wm = CServiceBroker::GetGUI()->GetWindowManager();
        const auto power = CServiceBroker::GetAppComponents().GetComponent<CApplicationPowerHandling>();
        auto* owner = wm.GetWindow(wm.GetActiveWindow());
        if (owner && power && !power->IsInScreenSaver() && wm.GetTopmostModalDialog() == WINDOW_INVALID)
        {
          bool handled = false;
          std::vector<int> ids;
          if (wm.GetActiveWindow() == WINDOW_VIDEO_NAV) ids.push_back(owner->GetViewContainerID());
          else if (wm.GetActiveWindow() == WINDOW_HOME)
            ids = {8101,8102,8601,8602,8701,8702,8801,8802,8830,8831};
          for (const int id : ids)
          {
            auto* view = dynamic_cast<CGUIBaseContainer*>(owner->GetControl(id));
            if (view && view->OnInfinityMediaTouch(newEvent.touch.x,newEvent.touch.y,
                                                  newEvent.touch.action == ACTION_TOUCH_LONGPRESS))
            { handled = true; break; }
          }
          if (handled) break;
        }
      }
#endif
'''

LABEL_HELPER=r'''
#if defined(TARGET_ANDROID)
namespace
{
std::string InfinitySearchCommandLabel(const CGUIListItem* item, std::string label)
{
  if (!g_SkinInfo || g_SkinInfo->ID() != "skin.infinity.diggz" || !item || !item->IsFileItem()) return label;
  const auto* file = static_cast<const CFileItem*>(item);
  if (file->HasVideoInfoTag() && !file->GetVideoInfoTag()->m_type.empty()) return label;
  CURL url(file->GetPath());
  if (url.GetProtocol() != "plugin" || url.GetHostName() != "plugin.video.umbrella") return label;
  const auto action = url.GetOption("action");
  if (action != "movieSearchnew" && action != "tvSearchnew" &&
      action != "movieSearch" && action != "tvSearch" && action != "cache_clearSearch") return label;
  // Remove presentation tags only, on the actual Search command rows. The
  // original label, provider URL, history and context ownership stay intact.
  size_t at=0;
  while ((at=label.find('[',at)) != std::string::npos)
  {
    const auto end=label.find(']',at);
    if (end==std::string::npos) break;
    const auto tag=label.substr(at,end-at+1);
    if (StringUtils::StartsWithNoCase(tag,"[COLOR ") || StringUtils::EqualsNoCase(tag,"[/COLOR]"))
      label.erase(at,end-at+1);
    else at=end+1;
  }
  return label;
}
}
#endif
'''

def patches(before):
    markers={CONTAINER:b'OnInfinityMediaTouch',HEADER:b'OnInfinityMediaTouch',
             INPUT:b'INFINITY_2103394_MEDIA_TOUCH',GUIWINDOW:b'InfinitySubtitleSettings.xml',
             LABEL:b'InfinitySearchCommandLabel'}
    require(all(marker not in before[path] for path,marker in markers.items()),'touch overlay already applied')
    out=dict(before)
    raw=out[HEADER]
    raw=once(raw,b'#include <list>',b'#include <list>\n#include <chrono>\n#include <cstdint>')
    raw=once(raw,b'  std::string m_infinityUiTapKey;',b'''  std::string m_infinityUiTapKey;
  bool OnInfinityMediaTouch(float x,float y,bool hold);
  std::string m_infinityMediaTapKey;
  std::chrono::steady_clock::time_point m_infinityMediaTappedAt{};
  std::chrono::steady_clock::time_point m_infinityMediaSuppressUntil{};''')
    out[HEADER]=raw
    raw=out[CONTAINER]
    raw=once(raw,b'#include "FileItem.h"',b'#include "FileItem.h"\n#include "video/VideoInfoTag.h"\n#include "windows/GUIMediaWindow.h"')
    raw=once(raw,b'bool CGUIBaseContainer::OnInfinityUiTouch(',METHOD.encode()+b'\nbool CGUIBaseContainer::OnInfinityUiTouch(')
    start=raw.index(b'bool CGUIBaseContainer::OnInfinityOptionBLongPress(')
    end=raw.index(b'bool CGUIBaseContainer::OnInfinityRailLongPress(',start)
    body=raw[start:end]
    body=once(body,b'  const int selected = GetSelectedItem();',
        b'  const int selected = GetSelectedItem();\n  CLog::Log(LOGINFO, "[InfinityTouch] {{\\"event\\":\\"touch.option_b\\",\\"phase\\":\\"native.hit\\",\\"outcome\\":\\"accepted\\",\\"control\\":{},\\"index\\":{}}}", GetID(), selected);')
    body=once(body,b'  home->SetProperty("Infinity.HomeOptionB.PendingProof", proof);',
        b'  home->SetProperty("Infinity.HomeOptionB.PendingProof", proof);\n  CLog::Log(LOGINFO, "[InfinityTouch] {{\\"event\\":\\"touch.option_b\\",\\"phase\\":\\"native.proof\\",\\"outcome\\":\\"accepted\\",\\"control\\":{},\\"index\\":{}}}", GetID(), selected);')
    body=once(body,b'  return true;\n}',
        b'  CLog::Log(LOGINFO, "[InfinityTouch] {{\\"event\\":\\"touch.option_b\\",\\"phase\\":\\"native.posted\\",\\"outcome\\":\\"accepted\\",\\"control\\":{},\\"index\\":{}}}", GetID(), selected);\n  return true;\n}')
    raw=raw[:start]+body+raw[end:]
    raw=once(raw,b'  // stop the timer on any other action',b'''  if (action.GetID() == ACTION_GESTURE_BEGIN || action.GetID() == ACTION_GESTURE_PAN ||
      action.GetID() == ACTION_GESTURE_ABORT)
    m_infinityMediaTapKey.clear();
  // stop the timer on any other action''')
    out[CONTAINER]=raw
    raw=out[INPUT]
    dispatch=DISPATCH
    raw=once(raw,b'      if (newEvent.touch.action == ACTION_TOUCH_TAP)\n',dispatch.encode()+b'\n      if (newEvent.touch.action == ACTION_TOUCH_TAP)\n')
    out[INPUT]=raw
    raw=out[GUIWINDOW]
    raw=once(raw,b'    const std::string selectedFile = infinityPlayerSettings ? "InfinityPlayerSettings.xml" : strFileName;',b'''    const std::string selectedFile = !infinityPlayerSettings ? strFileName :
        GetID() == WINDOW_DIALOG_SUBTITLE_OSD_SETTINGS ? "InfinitySubtitleSettings.xml" :
        GetID() == WINDOW_DIALOG_VIDEO_OSD_SETTINGS ? "InfinityVideoSettings.xml" : "InfinityPlaybackSettings.xml";''')
    out[GUIWINDOW]=raw
    raw=out[LABEL]
    raw=once(raw,b'#include "addons/Skin.h"',b'''#include "addons/Skin.h"
#include "FileItem.h"
#include "video/VideoInfoTag.h"
#include "utils/StringUtils.h"
#include "URL.h"''')
    raw=once(raw,b'using namespace KODI::GUILIB;',b'using namespace KODI::GUILIB;\n'+LABEL_HELPER.encode())
    raw=once(raw,b'    SetLabel(m_info.GetItemLabel(item));',b'''#if defined(TARGET_ANDROID)
    SetLabel(InfinitySearchCommandLabel(item,m_info.GetItemLabel(item)));
#else
    SetLabel(m_info.GetItemLabel(item));
#endif''')
    out[LABEL]=raw
    return out
