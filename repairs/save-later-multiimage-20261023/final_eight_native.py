"""Exact Infinity-owned shared title selection; original nonowned handlers retained."""
import hashlib

PATH = 'xbmc/guilib/GUIBaseContainer.cpp'
BEFORE = '4a716be3ce8024e430fe17827437b83ba8ce5a438549958d9e57395e980d0082'
INPUT_PATH = 'xbmc/input/InputManager.cpp'
INPUT_BEFORE = '9f8a8b32257a69353edf93d18d5834a6d26145b50cb7c1c70e84fdd32a1988c1'
HOME_IDS = '8103,8104,8603,8604,8703,8704,8803,8804,8721,8722,8821,8822,9201,9202'

HELPER = r'''#if defined(TARGET_ANDROID)
static bool InfinityTitleOwnerReady()
{
  if (CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") != "skin.infinity.diggz")
    return false;
  ADDON::AddonPtr addon;
  return CServiceBroker::GetAddonMgr().GetAddon("script.infinity.commandcenter", addon,
      ADDON::OnlyEnabled::CHOICE_YES) && addon->Version().asString() == "0.3.5.34";
}
static bool InfinityOpenTitlePopup(const std::shared_ptr<CFileItem>& item)
{
  if (!item || !item->HasVideoInfoTag() || !InfinityTitleOwnerReady()) return false;
  const auto& type = item->GetVideoInfoTag()->m_type;
  if (type != "movie" && type != "tvshow" && type != "episode" && type != "season") return false;
  ADDON::AddonPtr addon;
  if (!CServiceBroker::GetAddonMgr().GetAddon("script.infinity.commandcenter", addon,
      ADDON::OnlyEnabled::CHOICE_YES)) return false;
  // Only the owned handler below calls this. Kodi's context invoker receives
  // the exact copy, including original provider route and saved-list capsule.
  const auto popup = CContextMenuItem::CreateItem("Title options", "",
      URIUtils::AddFileToFolder(addon->Path(), "context.py"), "", addon->ID(), {addon->ID(), "infinity-item-menu-v1"});
  return popup.Execute(std::make_shared<CFileItem>(*item));
}
static void InfinitySelectionField(std::string& key, const std::string& field)
{
  key += std::to_string(field.size()) + ":" + field;
}
#endif

'''

# All approved title surfaces enter this one branch. No database/provider scan
# or callback occurs while computing selection. Nonowned code remains below it.
OWNED = r'''  const bool controllerDirectory = directory.rfind("plugin://script.infinity.commandcenter/", 0) == 0;
  auto* home = windows.GetWindow(WINDOW_HOME);
  const std::string browsePath = sharedBrowse && home ? home->GetProperty("Infinity.BrowsePath").asString() : "";
  const bool controllerBrowse = sharedBrowse && browsePath.rfind("plugin://script.infinity.commandcenter/", 0) == 0;
  const bool capsule = item->GetProperty("Infinity.Selection.Contract").asString() == "1" &&
      !item->GetProperty("Infinity.Selection.Snapshot").asString().empty();
  const bool latest = (featured || (sharedBrowse && browsePath.rfind("plugin://plugin.infinity.latestreleases/", 0) == 0)) &&
      path.rfind("plugin://plugin.infinity.latestreleases/", 0) == 0 &&
      item->GetProperty("Infinity.LatestReleases.Identity").asString() == "v1" &&
      item->GetProperty("Infinity.LatestReleases.Kind").asString() == type;
  const bool owned = (controllerDirectory || latest ||
      (capsule && (resume || sharedHome || controllerBrowse))) && InfinityTitleOwnerReady();
  if (owned)
  {
    if (item->IsParentFolder() || path.empty() || path.size() > 32768U) return reject();
    m_waitForScrollEnd = false;
    CGUIMessage focus(GUI_MSG_SETFOCUS, GetParentID(), GetID());
    window->OnMessage(focus);
    if (GetSelectedItem() != selected || window->GetFocusedControlID() != GetID()) return reject();
    // Length framing prevents separator collisions. Position and pointer are
    // never identity: recycled/reordered rows cannot arm another title.
    std::string key = "infinity-title-selection-v1";
    for (const auto& field : {type, path, directory, browsePath,
         item->GetProperty("Infinity.Selection.Snapshot").asString(),
         item->GetProperty("Infinity.Search.Provider").asString(),
         item->GetVideoInfoTag()->GetUniqueID("tmdb"), item->GetVideoInfoTag()->GetUniqueID("imdb"),
         item->GetVideoInfoTag()->GetUniqueID("tvdb"),
         std::to_string(item->GetVideoInfoTag()->m_iSeason), std::to_string(item->GetVideoInfoTag()->m_iEpisode)})
      InfinitySelectionField(key, field);
    const auto now = std::chrono::steady_clock::now();
    if (hold)
    {
      m_infinityMediaTapKey.clear();
      m_infinityMediaSuppressUntil = now + std::chrono::milliseconds(600);
      InfinityOpenTitlePopup(item);
      return true;
    }
    if (now < m_infinityMediaSuppressUntil) return true;
    const auto elapsed = now - m_infinityMediaTappedAt;
    const bool open = previous == selected && m_infinityMediaTapKey == key &&
        elapsed >= std::chrono::milliseconds(120) && elapsed <= std::chrono::seconds(5);
    m_infinityMediaTapKey = key;
    m_infinityMediaTappedAt = now;
    if (open)
    {
      m_infinityMediaTapKey.clear();
      OnClick(ACTION_SELECT_ITEM); // exact original item route, once
    }
    return true;
  }
  if (sharedHome || sharedBrowse) return reject(); // no opt-in, no behavior change
'''

REPLACEMENTS = [
    ('#include "GUIBaseContainer.h"', '#include "GUIBaseContainer.h"\n#include "ContextMenuItem.h"\n#include "utils/URIUtils.h"'),
    ('bool CGUIBaseContainer::OnInfinityOptionBLongPress(float x, float y)\n{',
     HELPER + 'bool CGUIBaseContainer::OnInfinityOptionBLongPress(float x, float y)\n{\n#if defined(TARGET_ANDROID)\n  if (InfinityTitleOwnerReady()) return OnInfinityMediaTouch(x, y, true);\n#endif'),
    ('  if ((!video && !featured && !resume) || !window || !HasProcessed() || m_gestureActive ||',
     '  const bool sharedHome = GetParentID() == WINDOW_HOME && (GetID() == ' + ' || GetID() == '.join(HOME_IDS.split(',')) + ');\n'
     '  const bool sharedBrowse = GetParentID() == WINDOW_HOME + 1193 && GetID() == 50;\n'
     '  if ((!video && !featured && !resume && !sharedHome && !sharedBrowse) || !window || !HasProcessed() || m_gestureActive ||'),
    ('  if ((!provider && !library && !local) || path.size() > 8192 || item->IsParentFolder()) return reject();',
     OWNED + '  if ((!provider && !library && !local) || path.size() > 8192 || item->IsParentFolder()) return reject();'),
    ('bool CGUIBaseContainer::OnInfinityUiTouch(float x, float y, bool hold)\n{',
     'bool CGUIBaseContainer::OnInfinityUiTouch(float x, float y, bool hold)\n{\n#if defined(TARGET_ANDROID)\n'
     '  if (GetParentID() == WINDOW_HOME && (GetID() == 8830 || GetID() == 8831) && InfinityTitleOwnerReady())\n'
     '    return OnInfinityMediaTouch(x, y, hold);\n#endif'),
]
INPUT_REPLACEMENTS = [
    ('            ids = {8101,8102,8601,8602,8701,8702,8801,8802,8830,8831};',
     '            ids = {8101,8102,8601,8602,8701,8702,8801,8802,8830,8831,' + HOME_IDS + '};\n'
     '          else if (wm.GetActiveWindow() == WINDOW_HOME + 1193) ids = {50};'),
]


def apply(source, overlay):
    delta = {}
    for name, pin, replacements in ((PATH, BEFORE, REPLACEMENTS), (INPUT_PATH, INPUT_BEFORE, INPUT_REPLACEMENTS)):
        raw = (source / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin:
            raise RuntimeError('Infinity selection preimage differs: ' + name)
        text = raw.decode()
        for before, after in replacements:
            if text.count(before) != 1:
                raise RuntimeError('Infinity selection boundary changed: ' + before[:80])
            text = text.replace(before, after)
        path = overlay / name
        if path.exists(): raise RuntimeError('Overlapping native selection correction')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        delta[name] = dict(original_sha256=pin, final_sha256=hashlib.sha256(text.encode()).hexdigest(),
            defect='Unified exact-item Infinity selection and popup routing',
            justification='CC34 owned saved/Search/latest/browse projections share copied identity; original ordinary Kodi/provider/Cobra handlers remain outside this opt-in branch')
    return delta
