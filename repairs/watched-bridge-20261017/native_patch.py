"""Add a read-only row-state bridge; preserve TEST1's native repair and writers."""
from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent
FILES = ("xbmc/GUIInfoManager.cpp", "xbmc/interfaces/builtins/GUIBuiltins.cpp", "xbmc/profiles/ProfileManager.cpp")
ADDED = ("xbmc/guilib/InfinityWatchedIndex.h", "xbmc/guilib/InfinityWatchedPresentation.h")

PUBLISH = r'''
// INFINITY_WATCHED_PRESENTATION_V1: command executes on the GUI dispatcher;
// poster lookups read an immutable index and never enter this window/JSON path.
static int InfinityResumeHubUpdate(const std::vector<std::string>& params)
{
  if (!params.empty())
    return -1;
  const auto fail = []() {
    InfinityWatched::Clear();
    CServiceBroker::GetGUI()->GetInfoManager().ResetCache();
    return -1;
  };
  auto* home = CServiceBroker::GetGUI()->GetWindowManager().GetWindow(WINDOW_HOME);
  if (!home)
    return fail();
  const std::string text = home->GetProperty("Infinity.ResumeHub.PresentationSnapshot").asString();
  if (text.size() > 262144)
    return fail();
  CVariant value;
  if (!CJSONVariantParser::Parse(text, value) || !value.isObject() ||
      !value["schema"].isInteger() || value["schema"].asInteger() != 1 ||
      !value["profile"].isString() || !value["revision"].isString() ||
      value["revision"].asString().size() != 64 || !value["records"].isArray() ||
      value["records"].size() > 1200 || !value["providers"].isObject() || value["providers"].size() > 32)
    return fail();
  std::string profile = CSpecialProtocol::TranslatePath("special://profile/");
  while (!profile.empty() && (profile.back() == '/' || profile.back() == '\\'))
    profile.pop_back();
  if (value["profile"].asString() != profile)
    return fail();
  std::vector<InfinityWatched::Record> records;
  records.reserve(value["records"].size());
  for (auto rowIt = value["records"].begin_array(); rowIt != value["records"].end_array(); ++rowIt)
  {
    const auto& row = *rowIt;
    const auto& identity = row["identity"];
    if (!row.isObject() || !row["watched"].isBoolean() || !identity.isObject() ||
        !identity["kind"].isString() || !identity["scope"].isString() || !identity["ids"].isObject())
      return fail();
    InfinityWatched::Record record;
    record.watched = row["watched"].asBoolean();
    record.identity.kind = identity["kind"].asString();
    record.identity.scope = identity["scope"].asString();
    for (auto idIt = identity["ids"].begin_map(); idIt != identity["ids"].end_map(); ++idIt)
    {
      const auto& name = idIt->first;
      const auto& id = idIt->second;
      if (!id.isString())
        return fail();
      record.identity.ids[name] = id.asString();
    }
    if (record.identity.kind == "episode")
    {
      if (!identity["season"].isInteger() || !identity["episode"].isInteger() ||
          identity["season"].asInteger() < 0 || identity["season"].asInteger() > 100000 ||
          identity["episode"].asInteger() < 0 || identity["episode"].asInteger() > 100000)
        return fail();
      record.identity.season = static_cast<int>(identity["season"].asInteger());
      record.identity.episode = static_cast<int>(identity["episode"].asInteger());
    }
    records.emplace_back(std::move(record));
  }
  std::map<std::string, std::string> providers;
  for (auto it = value["providers"].begin_map(); it != value["providers"].end_map(); ++it)
  {
    if (!it->second.isString())
      return fail();
    providers[it->first] = it->second.asString();
  }
  if (!InfinityWatched::Publish(std::move(records), std::move(providers)))
    return fail();
  CServiceBroker::GetGUI()->GetInfoManager().ResetCache();
  return 0;
}

'''


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unexpected watched native source anchor: " + old[:100])
    return text.replace(old, new, 1)


def apply(root):
    root = Path(root)
    before, after = {}, {}
    for name in FILES:
        path = root / name
        data = path.read_bytes()
        before[name] = hashlib.sha256(data).hexdigest()
        text = data.decode()
        if name.endswith("GUIInfoManager.cpp"):
            text = once(text, '#include "GUIInfoManager.h"', '#include "GUIInfoManager.h"\n#include "guilib/InfinityWatchedPresentation.h"\n#include "guilib/WindowIDs.h"')
            anchor = '  CGUIInfo info(constinfo);'
            text = once(text, anchor, anchor + '''
  // Capability is an info-label contract, not a mutable window property.
  if (info.m_info == WINDOW_PROPERTY && info.GetData1() == WINDOW_HOME &&
      StringUtils::EqualsNoCase(info.GetData3(), "Infinity.ResumeHub.BridgeVersion"))
    return "1";
''')
            signature = 'std::string CGUIInfoManager::GetMultiInfoItemLabel('
            start = text.index(signature)
            body = text[start:]
            anchor = '  std::string value;'
            body = once(body, anchor, '''  if (info.m_info == LISTITEM_PROPERTY &&
      StringUtils::EqualsNoCase(info.GetData3(), "Infinity.ResumeHub.Watched"))
  {
    const auto state = InfinityWatched::ItemState(*item);
    if (!state.empty())
      return state;
  }

''' + anchor)
            text = text[:start] + body
        elif name.endswith("GUIBuiltins.cpp"):
            text = once(text, '#include "GUIBuiltins.h"', '#include "GUIBuiltins.h"\n#include "GUIInfoManager.h"\n#include "guilib/InfinityWatchedIndex.h"\n#include "filesystem/SpecialProtocol.h"\n#include "utils/JSONVariantParser.h"\n#include "utils/Variant.h"')
            text = once(text, 'static int Action(const std::vector<std::string>& params)', PUBLISH + 'static int Action(const std::vector<std::string>& params)')
            text = once(text, '           {"action",', '           {"infinityresumehubupdate", {"Publish bounded local watched metadata", 0, InfinityResumeHubUpdate}},\n           {"action",')
        else:
            text = once(text, '#include "ProfileManager.h"', '#include "ProfileManager.h"\n#include "guilib/InfinityWatchedIndex.h"')
            text = once(text, 'void CProfileManager::SetCurrentProfileId(unsigned int profileId)\n{',
                        'void CProfileManager::SetCurrentProfileId(unsigned int profileId)\n{\n  InfinityWatched::Clear(); // Never carry derived title state into another profile.')
        path.write_text(text)
        after[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ADDED:
        path = root / name
        if path.exists():
            raise ValueError("Watched bridge header already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((HERE / "native" / path.name).read_bytes())
        after[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(before=before, after=after, changed=list(FILES), added=list(ADDED),
                gui_to_python_callbacks=False, per_item_disk_or_database_reads=False,
                provider_or_command_center_code_changed=False, shutdown_and_write_admission_changed=False,
                physical_fold_verified=False, locked=False)
