"""Exact Infinity-owned video-list hold dispatch; unrelated touch paths untouched."""
import hashlib
from pathlib import Path

PATH = 'xbmc/guilib/GUIBaseContainer.cpp'
BEFORE = '4a716be3ce8024e430fe17827437b83ba8ce5a438549958d9e57395e980d0082'
OLD = '    OnClick(ACTION_CONTEXT_MENU); // original exact-item provider/native context, no Select'
NEW = '    if (local && video)\n    {\n      std::string bucket = item->GetProperty("Infinity.ResumeHub.Bucket").asString();\n      if (bucket != "continue" && bucket != "watchlist" && bucket != "later" &&\n          bucket != "history" && bucket != "watched" && bucket != "collection" &&\n          bucket != "list" && bucket != "ratings" && bucket != "progress" && bucket != "next")\n        bucket.clear();\n      CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,\n          "RunPlugin(plugin://script.infinity.commandcenter/?action=item-menu&key=" + saved + "&bucket=" + bucket + ")");\n    }\n    else\n      OnClick(ACTION_CONTEXT_MENU); // original exact-item provider/native context, no Select'

HELPER = '''#if defined(TARGET_ANDROID)
static bool InfinityOpenTitlePopup(const std::shared_ptr<CFileItem>& item)
{
  if (!item || !item->HasVideoInfoTag() ||
      (item->GetVideoInfoTag()->m_type != "movie" && item->GetVideoInfoTag()->m_type != "tvshow") ||
      CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") != "skin.infinity.diggz")
    return false;
  ADDON::AddonPtr addon;
  if (!CServiceBroker::GetAddonMgr().GetAddon("script.infinity.commandcenter", addon,
                                            ADDON::OnlyEnabled::CHOICE_YES) ||
      addon->Version().asString() != "0.3.5.33")
    return false;
  // Kodi's context invoker owns this exact copy. No later focused-item lookup,
  // Python wrapper of a live GUI container, provider command, or synchronous wait.
  const auto popup = CContextMenuItem::CreateItem("Title options", "",
      addon->Path() + "/context.py", "", addon->ID(), {addon->ID(), "infinity-item-menu-v1"});
  return popup.Execute(std::make_shared<CFileItem>(*item));
}
#endif

'''

NEW = NEW.replace('    else\n      OnClick', '    else if (!InfinityOpenTitlePopup(item))\n      OnClick')
REPLACEMENTS = [
    ('#include "GUIBaseContainer.h"', '#include "GUIBaseContainer.h"\n#include "ContextMenuItem.h"'),
    ('bool CGUIBaseContainer::OnInfinityOptionBLongPress(float x, float y)', HELPER + 'bool CGUIBaseContainer::OnInfinityOptionBLongPress(float x, float y)'),
    ('  // The sole command is literal. The untrusted title/URL never enter a',
     '  #if defined(TARGET_ANDROID)\n  if (InfinityOpenTitlePopup(item))\n  {\n    m_waitForScrollEnd = false;\n    m_infinityMediaTapKey.clear();\n    m_infinityMediaSuppressUntil = std::chrono::steady_clock::now() + std::chrono::milliseconds(600);\n    return true;\n  }\n  #endif\n\n  // The sole command is literal. The untrusted title/URL never enter a'),
    ('  const bool provider = path.compare(0,22,"plugin://plugin.video.") == 0 ||',
     '  const bool latest = featured && path.rfind("plugin://plugin.infinity.latestreleases/", 0) == 0 &&\n      item->GetProperty("Infinity.LatestReleases.Identity").asString() == "v1" &&\n      item->GetProperty("Infinity.LatestReleases.Kind").asString() == type;\n  const bool provider = latest || path.compare(0,22,"plugin://plugin.video.") == 0 ||'),
    ('if ((!provider && !library && !local) || path.size() > 8192 || item->IsParentFolder())',
     'if ((!provider && !library && !local) || path.size() > (latest ? 32768U : 8192U) || item->IsParentFolder())'),
    ('  if (hold && (featured || resume)) return reject(); // existing Option B / Resume management owns holds',
     '  if (hold && resume) return reject(); // existing Resume management owns holds'),
    (OLD, NEW),
]

def apply(source, overlay):
    raw = (source / PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BEFORE:
        raise RuntimeError('Infinity touch preimage differs from signed baseline')
    text = raw.decode()
    for before, after in REPLACEMENTS:
        if text.count(before) != 1:
            raise RuntimeError('Infinity media hold boundary changed: ' + before[:80])
        text = text.replace(before, after)
    updated = text.encode()
    path = overlay / PATH
    if path.exists():
        raise RuntimeError('Overlapping native touch correction')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(updated)
    return {PATH: dict(original_sha256=BEFORE, final_sha256=hashlib.sha256(updated).hexdigest(),
                      defect='Infinity Movies/TV selected-title popup',
                      justification='Infinity-only hit-tested Movie/TV holds use exact context-item copies; saved lists retain key/bucket dispatch; original fallback and resume ownership retained')}
