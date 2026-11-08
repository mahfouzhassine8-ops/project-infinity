#pragma once

#if defined(TARGET_ANDROID)
#include "InfinitySavedNavigationState.h"
#include "FileItem.h"
#include "filesystem/SpecialProtocol.h"
#include <climits>
#include <cstdlib>
#include <cmath>
#include "ServiceBroker.h"
#include "URL.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIWindow.h"
#include "guilib/GUIWindowManager.h"
#include "interfaces/generic/ScriptInvocationManager.h"
#include "interfaces/legacy/ModuleXbmc.h"
#include "messaging/ApplicationMessenger.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "utils/Digest.h"
#include "utils/JSONVariantParser.h"
#include "utils/JSONVariantWriter.h"
#include "utils/StringUtils.h"
#include "utils/Variant.h"
#include "utils/log.h"
#include "video/VideoInfoTag.h"
#include "windowing/WinSystem.h"

namespace InfinitySavedNavigation
{
inline Correlation& State()
{
  static Correlation state;
  return state;
}
inline bool Enabled()
{
  return XBMCAddon::xbmc::getSkinDir() == "skin.infinity.diggz" &&
      !InfinityAndroidCheckpoint::IsActive() &&
      !CScriptInvocationManager::GetInstance().IsShutdownRequested();
}
inline std::string Home(const std::string& key, const std::string* value = nullptr)
{
  auto* gui = CServiceBroker::GetGUI();
  auto* win = CServiceBroker::GetWinSystem();
  if (!gui || !win) return {};
  std::unique_lock<CCriticalSection> lock(win->GetGfxContext());
  auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME);
  if (!home) return {};
  if (value) home->SetProperty(key, *value);
  return home->GetProperty(key).asString();
}
inline std::string Hash(const std::string& value)
{
  return KODI::UTILITY::CDigest::Calculate(KODI::UTILITY::CDigest::Type::SHA256, value);
}
inline bool Key(const std::string& value)
{
  return value.size() == 64 && value.find_first_not_of("0123456789abcdef") == std::string::npos;
}
inline bool ProviderPath(const std::string& path)
{
  if (path.empty() || path.size() > 65536 || path.find('|') != std::string::npos) return false;
  const CURL url(path);
  return url.IsProtocol("plugin") && !url.GetHostName().empty() &&
      url.GetHostName() != "script.infinity.commandcenter";
}
inline bool Bucket(const std::string& value)
{
  return value == "later" || value == "watchlist" || value == "continue";
}
inline std::string WatchProfile()
{
  auto value = CSpecialProtocol::TranslatePath("special://profile");
  while (!value.empty() && (value.back() == '/' || value.back() == '\\')) value.pop_back();
  return value;
}
inline std::string WatchNonce()
{
  auto value = StringUtils::CreateUUID();
  StringUtils::Replace(value, "-", "");
  return value;
}
inline int64_t WatchEpoch()
{
  return std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count();
}
inline std::string WatchJSON(const CVariant& value)
{
  std::string raw; CJSONVariantWriter::Write(value, raw, true); return raw;
}
inline bool WatchParse(const std::string& raw, CVariant& value)
{
  return raw.size() <= 262144 && CJSONVariantParser::Parse(raw, value) && value.isObject();
}
inline bool WatchCapsule(const CVariant& value, const std::string& key)
{
  return WatchJSON(value).size() <= 16384 && value["schema"].asInteger() == 1 && value["owner"].asString() == "script.infinity.commandcenter" &&
      value["bucket"].asString() == "watchlist" && value["key"].asString() == key && Key(key) &&
      Key(value["token"].asString()) && value["identity"].isObject();
}
inline WatchIdentity WatchTyped(const CFileItem& item)
{
  WatchIdentity result;
  if (!item.HasVideoInfoTag()) return result;
  const auto* tag = item.GetVideoInfoTag();
  result.kind = tag->m_type;
  result.tmdb = tag->GetUniqueID("tmdb"); result.tvdb = tag->GetUniqueID("tvdb");
  result.imdb = tag->GetUniqueID("imdb");
  if (result.kind == "season" || result.kind == "episode") result.season = tag->m_iSeason;
  if (result.kind == "episode") result.episode = tag->m_iEpisode;
  return result;
}
inline WatchIdentity WatchTyped(const CVariant& value)
{
  WatchIdentity result;
  result.kind = value["kind"].asString();
  result.tmdb = value["ids"]["tmdb"].asString(); result.tvdb = value["ids"]["tvdb"].asString();
  result.imdb = value["ids"]["imdb"].asString();
  if (result.kind == "season" || result.kind == "episode") result.season = value["season"].asInteger();
  if (result.kind == "episode") result.episode = value["episode"].asInteger();
  return result;
}
inline bool WatchCoordinate(const std::string& raw, int& value)
{
  if (raw.empty() || raw.size() > 5 || raw.find_first_not_of("0123456789") != std::string::npos) return false;
  value = std::stoi(raw); return value >= 0;
}
// Reviewed provider route contracts only. Unknown producers remain ordinary playback.
inline bool WatchRoute(const std::string& path, WatchIdentity& identity)
{
  if (!ProviderPath(path)) return false;
  const CURL url(path);
  if (url.GetHostName() == "plugin.video.pov" && url.GetOption("mode") == "play_media")
  {
    identity.kind = url.GetOption("mediatype"); identity.tmdb = url.GetOption("tmdb_id");
    if (identity.tmdb.empty()) return false;
  }
  else if (url.GetHostName() == "plugin.video.umbrella" &&
      (url.GetOption("action") == "play_Item" || url.GetOption("action") == "play"))
  {
    identity.tmdb = url.GetOption("tmdb"); identity.tvdb = url.GetOption("tvdb");
    identity.imdb = url.GetOption("imdb");
    identity.kind = url.GetOption("season").empty() && url.GetOption("episode").empty() ? "movie" : "episode";
  }
  else return false;
  if (identity.kind == "episode")
    return WatchCoordinate(url.GetOption("season"), identity.season) &&
        WatchCoordinate(url.GetOption("episode"), identity.episode) &&
        (!identity.tmdb.empty() || !identity.tvdb.empty() || !identity.imdb.empty());
  return identity.kind == "movie" && url.GetOption("season").empty() && url.GetOption("episode").empty() &&
      (!identity.tmdb.empty() || !identity.tvdb.empty() || !identity.imdb.empty());
}
inline CVariant WatchValue(const WatchOrigin& origin)
{
  CVariant value(CVariant::VariantTypeObject), selection;
  if (!WatchParse(origin.selection, selection)) return value;
  value["schema"] = 1; value["token"] = origin.token; value["key"] = origin.key;
  value["profile"] = origin.profile; value["selection"] = selection;
  value["destination"] = origin.route; value["epoch_ms"] = origin.epoch;
  value["resume"] = origin.resume; value["resume_revision"] = origin.resumeRevision;
  return value;
}
inline bool WatchAnchorMatches(const CVariant& selection, const WatchIdentity& actual)
{
  auto expected = WatchTyped(selection["identity"]);
  if (expected.kind == "tvshow" || expected.kind == "season")
  {
    if (actual.kind != "season" && actual.kind != "episode") return false;
    if (expected.kind == "season" && expected.season != actual.season) return false;
    expected.kind = actual.kind; expected.season = actual.season; expected.episode = actual.episode;
  }
  return WatchMatches(expected, actual);
}
inline thread_local std::optional<WatchOrigin> watchDirectoryPermit;
// Returns true only when the actual selected wrapper is handled by fresh Python dispatch.
inline bool WatchBegin(const CFileItem& item, const std::string& listing)
{
  watchDirectoryPermit.reset();
  if (!Enabled()) { State().WatchInvalidate(); return false; }
  const auto profile = WatchProfile();
  const auto seal = item.GetProperty("Infinity.Watchlist.Child").asString();
  if (!seal.empty())
  {
    if (auto selected = State().WatchSelect(seal, item.GetPath(), profile))
    {
      if (item.m_bIsFolder) watchDirectoryPermit = std::move(selected);
      return false;
    }
  }
  State().WatchInvalidate();
  const CURL parent(listing.empty() ? item.GetProperty("Infinity.SavedNavigation.Listing").asString() : listing);
  const auto key = item.GetProperty("Infinity.ResumeHub.Key").asString();
  CVariant selection;
  if (!parent.IsProtocol("plugin") || parent.GetHostName() != "script.infinity.commandcenter" || parent.GetOption("action") != "library" ||
      parent.GetOption("bucket") != "watchlist" ||
      !WatchParse(item.GetProperty("Infinity.Selection.Snapshot").asString(), selection) ||
      !WatchCapsule(selection, key)) return false;
  const CURL target(item.GetPath());
  const bool wrapper = target.IsProtocol("plugin") && target.GetHostName() == "script.infinity.commandcenter" &&
      target.GetOption("action") == "watchlist-play" && target.GetOption("key") == key && !item.m_bIsFolder;
  const auto destination = wrapper ? item.GetProperty("Infinity.Watchlist.Destination").asString() : item.GetPath();
  if (!ProviderPath(destination)) return false;
  WatchOrigin origin;
  origin.token = WatchNonce(); origin.key = key; origin.profile = profile;
  origin.selection = WatchJSON(selection); origin.route = destination;
  origin.provider = CURL(destination).GetHostName(); origin.identity = WatchTyped(selection["identity"]);
  origin.epoch = WatchEpoch(); origin.selectedToken = wrapper ? origin.token : "";
  origin.generation = State().WatchBegin(origin);
  if (!wrapper)
  {
    if (item.m_bIsFolder) watchDirectoryPermit = origin;
    return false;
  }
  auto value = WatchValue(origin);
  const auto raw = WatchJSON(value);
  Home("Infinity.Watchlist.Selected", &raw);
  CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
      "RunPlugin(plugin://script.infinity.commandcenter/?action=watchlist-play&key=" + key +
      "&token=" + origin.token + ")");
  return true;
}
inline std::optional<WatchOrigin> WatchLaunch(const CFileItem& item)
{
  const auto raw = item.GetProperty("Infinity.Watchlist.Launch").asString();
  if (raw.empty()) return {};
  const auto pending = Home("Infinity.Watchlist.Launch");
  if (pending != raw) return {};
  const std::string empty;
  Home("Infinity.Watchlist.Launch", &empty); // consume before provider dispatch, including mismatches
  CVariant value;
  if (!Enabled() || !WatchParse(raw, value) || value["schema"].asInteger() != 1 ||
      value["token"].asString().size() != 32 ||
      value["token"].asString().find_first_not_of("0123456789abcdef") != std::string::npos ||
      !WatchCapsule(value["selection"], value["key"].asString()) ||
      value["profile"].asString() != WatchProfile() || value["destination"].asString() != item.GetDynPath() ||
      value["epoch_ms"].asInteger() < WatchEpoch() - 30000 ||
      value["epoch_ms"].asInteger() > WatchEpoch() + 30000) return {};
  WatchOrigin origin;
  origin.key = value["key"].asString(); origin.profile = value["profile"].asString();
  origin.selection = WatchJSON(value["selection"]); origin.route = value["destination"].asString();
  origin.token = WatchNonce(); origin.epoch = WatchEpoch(); origin.provider = CURL(origin.route).GetHostName();
  origin.launchToken = value["token"].asString();
  origin.resume = value["resume"].asDouble(); origin.resumeRevision = value["resume_revision"].asInteger();
  if (!std::isfinite(origin.resume) || origin.resume < 0 || origin.resume >= 1e12 || origin.resumeRevision < 0) return {};
  if (!WatchRoute(origin.route, origin.identity) || !WatchAnchorMatches(value["selection"], origin.identity)) return {};
  return State().WatchLaunch(value["selected_token"].asString(), std::move(origin));
}
struct WatchWindow { std::string path, profile; uint64_t generation{0}; };
inline thread_local std::vector<WatchWindow> watchWindows;
inline void WatchPrepare(const std::string& path)
{
  if (watchWindows.size() >= 16) { watchWindows.clear(); State().WatchInvalidate(); }
  const auto profile = WatchProfile();
  auto permit = std::move(watchDirectoryPermit);
  watchDirectoryPermit.reset();
  const auto current = Enabled() && permit && permit->route == path && permit->profile == profile ?
      State().WatchCurrent(path, profile) : std::optional<WatchOrigin>();
  const bool selected = current && current->generation == permit->generation && current->token == permit->token;
  if (!selected) State().WatchInvalidate();
  watchWindows.push_back({path, profile, selected ? current->generation : 0});
}
inline void WatchWindowResult(const std::string& path, bool success, const CFileItemList& items)
{
  if (watchWindows.empty()) { State().WatchInvalidate(); return; }
  const auto frame = watchWindows.back(); watchWindows.pop_back();
  if (frame.path != path) { watchWindows.clear(); State().WatchInvalidate(); return; }
  if (!frame.generation) return;
  const auto current = State().WatchCurrent(path, WatchProfile());
  if (!Enabled() || !success || !current || current->generation != frame.generation)
  { if (current) State().WatchInvalidate(); return; }
  CVariant selection;
  if (!WatchParse(current->selection, selection)) return;
  for (int i = 0; i < items.Size(); ++i)
  {
    const auto item = items.Get(i);
    if (!item || item->IsParentFolder() || !ProviderPath(item->GetPath()) ||
        CURL(item->GetPath()).GetHostName() != current->provider ||
        !WatchAnchorMatches(selection, WatchTyped(*item))) continue;
    auto child = *current;
    child.token = WatchNonce(); child.route = item->GetPath(); child.identity = WatchTyped(*item);
    if (!item->m_bIsFolder && (!WatchRoute(child.route, child.identity) ||
        !WatchAnchorMatches(selection, child.identity) || !WatchMatches(child.identity, WatchTyped(*item)))) continue;
    if (State().WatchSeal(frame.generation, child)) item->SetProperty("Infinity.Watchlist.Child", child.token);
  }
}
inline thread_local std::optional<WatchOrigin> watchMoviePermit;
struct WatchResultContext
{
  std::string path;
  std::optional<WatchOrigin> origin;
  int invoker{-1};
};
inline thread_local WatchResultContext* watchResult{nullptr};
class WatchResultScope
{
public:
  explicit WatchResultScope(const std::string& path) noexcept : m_previous(watchResult)
  {
    watchResult = nullptr;
    try { m_context.path = path; watchResult = &m_context; } catch (...) { }
  }
  ~WatchResultScope() { watchResult = m_previous; }
private:
  WatchResultContext m_context;
  WatchResultContext* m_previous;
};
struct WatchResolverContext
{
  WatchOrigin origin;
  std::string script;
  std::vector<std::string> arguments;
  bool observed{false};
  int invoker{-1};
};
inline thread_local WatchResolverContext* watchResolver{nullptr};
class WatchResolver
{
public:
  WatchResolver(const std::string& path, const std::string& addon, const std::string& script, bool resume)
    : m_previous(watchResolver), m_result(watchResult)
  {
    // A nested unrelated resolver must mask the outer context.
    watchResolver = nullptr;
    try
    {
      if (!Enabled() || !watchMoviePermit || watchMoviePermit->route != path ||
          watchMoviePermit->profile != WatchProfile() || watchMoviePermit->provider != addon) return;
      const auto origin = State().WatchClaimResolver(*watchMoviePermit, WatchNonce());
      if (!origin) return;
      WatchIdentity route;
      if (!WatchRoute(path, route)) return; // directory calls cannot authorize a player
      CVariant selection;
      if (!WatchParse(origin->selection, selection) || !WatchAnchorMatches(selection, route)) return;
      m_context.origin = *origin; m_context.origin.identity = route; m_context.script = script;
      CURL url(path); const auto options = url.GetOptions(); url.SetOptions("");
      m_context.arguments = {url.Get(), "", options, StringUtils::Format("resume:{}", resume)};
      watchResolver = &m_context;
    }
    catch (...) { }
  }
  ~WatchResolver()
  {
    // Only this exact StartScript call may publish its dispatched invoker to its result scope.
    if (m_result && m_result == watchResult && m_result->path == m_context.origin.route &&
        m_context.observed && m_context.invoker >= 0)
    {
      try { m_result->origin = m_context.origin; m_result->invoker = m_context.invoker; }
      catch (...) { m_result->origin.reset(); m_result->invoker = -1; }
    }
    watchResolver = m_previous;
  }
private:
  WatchResolverContext m_context;
  WatchResolverContext* m_previous;
  WatchResultContext* m_result;
};
inline void WatchDispatch(int id, const std::string& addon, const std::string& script,
                          const std::vector<std::string>& argv, int handle) noexcept
{
  try
  {
    std::optional<WatchOrigin> origin;
    auto* context = watchResolver;
    if (context && !context->observed && context->origin.provider == addon && context->script == script &&
        argv.size() == 4 && handle >= 0 && argv[0] == context->arguments[0] &&
        argv[1] == std::to_string(handle) && argv[2] == context->arguments[2] && argv[3] == context->arguments[3])
    { context->observed = true; context->invoker = id; origin = context->origin; }
    State().WatchDispatch(id, origin);
  }
  catch (...) { try { State().WatchDispatch(id, {}); } catch (...) { } }
}
inline void WatchPlaying(CFileItem& item, const std::string& addon, long invoker) noexcept
{
  try
  {
    item.ClearProperty("Infinity.Watchlist.Origin");
    if (!Enabled()) { State().WatchInvalidate(); return; }
    if (invoker < 0 || invoker > INT_MAX) return;
    const auto origin = State().WatchConsume(static_cast<int>(invoker), addon, WatchProfile(), WatchTyped(item), item.GetDynPath());
    if (origin) item.SetProperty("Infinity.Watchlist.Origin", origin->token);
  }
  catch (...) { }
}
inline void WatchResolved(const std::string& path, bool success, CFileItem& item)
{
  try
  {
    item.ClearProperty("Infinity.Watchlist.Origin");
    if (!Enabled()) return;
    if (!watchResult || watchResult->path != path || !watchResult->origin || watchResult->invoker < 0) return;
    if (!success) { State().WatchFail(path, watchResult->origin->resolverToken); return; }
    const auto origin = State().WatchConsume(watchResult->invoker, CURL(path).GetHostName(), WatchProfile(),
        WatchTyped(item), item.GetDynPath(), watchResult->origin->resolverToken);
    if (origin) item.SetProperty("Infinity.Watchlist.Origin", origin->token);
  }
  catch (...) { }
}
inline CVariant WatchActive(const CFileItem& item)
{
  try
  {
    if (!Enabled()) { State().WatchInvalidate(); return {}; }
    const auto origin = State().WatchReceipt(item.GetProperty("Infinity.Watchlist.Origin").asString(),
        WatchProfile(), WatchTyped(item), item.GetDynPath());
    if (origin) return WatchValue(*origin);
  }
  catch (...) { }
  return {};
}

inline bool Begin(const CFileItem& item, const std::string& listing, bool observeWatch = true)
{
  try
  {
    if (observeWatch && WatchBegin(item, listing)) return true;
    const auto bucket = item.GetProperty("Infinity.ResumeHub.Bucket").asString();
    if (!Enabled() || !Bucket(bucket)) return false;
    // Home playback carries the exact first-party listing on its original item.
    const CURL parent(listing.empty() ? item.GetProperty("Infinity.SavedNavigation.Listing").asString() : listing);
    const bool controllerLibrary = parent.GetHostName() == "script.infinity.commandcenter" &&
        parent.GetOption("action") == "library" && parent.GetOption("bucket") == bucket;
    const bool continueListing = bucket == "continue" && parent.GetOption("action") == "continue" &&
        (parent.GetHostName() == "script.infinity.commandcenter" || parent.GetHostName() == "script.infinity.uirepair");
    if (!parent.IsProtocol("plugin") || (!controllerLibrary && !continueListing)) return false;
    const auto key = item.GetProperty("Infinity.ResumeHub.Key").asString();
    const auto& path = item.GetPath();
    if (!Key(key)) return false;
    const CURL target(path);
    if (target.IsProtocol("plugin") && target.GetHostName() == "script.infinity.commandcenter" &&
        target.GetOption("action") == "saved-recovery" && target.GetOption("key") == key &&
        target.GetOption("bucket") == bucket)
    {
      // The component explicitly marked a missing/incompatible/known-failed
      // destination. Do not enter Kodi's directory/player resolver for this action.
      const auto offset = item.GetProperty("StartOffset").asDouble();
      const auto resume = offset >= 0 && offset < 1e12 ? offset : 0.0;
      CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
          "RunPlugin(plugin://script.infinity.commandcenter/?action=saved-recovery&key=" + key +
          "&bucket=" + bucket + "&resume=" + std::to_string(resume) + ")");
      return true;
    }
    if (!ProviderPath(path)) return false;
    Ticket ticket;
    ticket.token = StringUtils::CreateUUID();
    ticket.key = key;
    ticket.bucket = bucket;
    ticket.originalPath = ticket.path = path;
    ticket.folder = item.m_bIsFolder;
    const auto offset = item.GetProperty("StartOffset").asDouble();
    ticket.resume = offset >= 0 && offset < 1e12 ? offset : 0.0;
    ticket.attempted.push_back(CURL(path).GetHostName());
    State().Begin(std::move(ticket));
    const std::string empty;
    Home("Infinity.SavedNavigation.Failure", &empty);
    Home("Infinity.SavedNavigation.Next", &empty);
    Home("Infinity.SavedNavigation.Success", &empty);
    Home("Infinity.SavedNavigation.Pending", &empty);
    CLog::Log(LOGINFO, "INFINITY_SAVED_ROUTE_BEGIN key={} destination_sha256={}", key, Hash(path));
  }
  catch (...) { } // Observation must preserve the original user action.
  return false;
}
inline void PrepareRecoveryNext(const std::string& path)
{
  try
  {
    if (!Enabled() || !ProviderPath(path)) return;
    // Only a user-selected, verified component recovery may arm a missing route.
    const auto start = Home("Infinity.SavedNavigation.Start");
    CVariant selected;
    if (start.size() <= 70000 && CJSONVariantParser::Parse(start, selected) && selected.isObject() &&
        Key(selected["key"].asString()) && selected["token"].asString().size() == 32 &&
        selected["token"].asString().find_first_not_of("0123456789abcdef") == std::string::npos &&
        selected["path"].asString() == path && Bucket(selected["bucket"].asString()) &&
        selected["original"].asString().size() <= 65536 && selected["folder"].isBoolean())
    {
      Ticket ticket;
      ticket.key = selected["key"].asString(); ticket.token = selected["token"].asString();
      ticket.bucket = selected["bucket"].asString(); ticket.path = path;
      ticket.originalPath = selected["original"].asString();
      ticket.folder = selected["folder"].asBoolean(); ticket.recovering = true;
      const auto offset = selected["resume"].asDouble();
      ticket.resume = offset >= 0 && offset < 1e12 ? offset : 0.0;
      ticket.attempted.push_back(CURL(path).GetHostName());
      State().Begin(std::move(ticket));
      const std::string empty;
      Home("Infinity.SavedNavigation.Start", &empty);
      Home("Infinity.SavedNavigation.Failure", &empty);
      Home("Infinity.SavedNavigation.Success", &empty);
      return;
    }
    const auto current = State().Read();
    if (!current || !current->failed) return;
    const auto raw = Home("Infinity.SavedNavigation.Next");
    if (raw.size() > 70000) return;
    CVariant request;
    if (!CJSONVariantParser::Parse(raw, request) || !request.isObject() ||
        request["token"].asString() != current->token || request["path"].asString() != path) return;
    if (State().Next(current->token, path, CURL(path).GetHostName()))
    {
      const std::string empty;
      Home("Infinity.SavedNavigation.Next", &empty);
      Home("Infinity.SavedNavigation.Failure", &empty);
      CLog::Log(LOGINFO, "INFINITY_SAVED_ROUTE_ALTERNATIVE key={} destination_sha256={}", current->key, Hash(path));
    }
  }
  catch (...) { }
}
inline void PrepareNext(const std::string& path)
{
  try { WatchPrepare(path); } catch (...) { }
  PrepareRecoveryNext(path);
}
inline void Publish(const Ticket& ticket)
{
  if (!Enabled()) return;
  CVariant value(CVariant::VariantTypeObject);
  value["schema"] = 1;
  value["token"] = ticket.token;
  value["key"] = ticket.key;
  value["bucket"] = ticket.bucket;
  value["original_sha256"] = Hash(ticket.originalPath);
  value["failed_sha256"] = Hash(ticket.path);
  value["reason"] = ticket.reason;
  value["folder"] = ticket.folder;
  value["resume"] = ticket.resume;
  value["epoch_ms"] = static_cast<int64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count());
  value["attempted"] = CVariant(CVariant::VariantTypeArray);
  for (const auto& provider : ticket.attempted) value["attempted"].push_back(provider);
  std::string raw;
  CJSONVariantWriter::Write(value, raw, true);
  Home("Infinity.SavedNavigation.Failure", &raw);
  CLog::Log(LOGINFO, "INFINITY_SAVED_ROUTE_FAILED key={} destination_sha256={} reason={}",
      ticket.key, Hash(ticket.path), ticket.reason);
  // Existing main-thread message dispatch; no new wait, GUI join or provider kill.
  CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
      "RunPlugin(plugin://script.infinity.commandcenter/?action=saved-fallback&key=" + ticket.key +
      "&token=" + ticket.token + "&bucket=" + ticket.bucket + ")");
}
inline CVariant Pending(const Ticket& ticket)
{
  CVariant value;
  const auto raw = Home("Infinity.SavedNavigation.Pending");
  if (raw.size() > 70000 || !CJSONVariantParser::Parse(raw, value) || !value.isObject() ||
      value["token"].asString() != ticket.token || value["key"].asString() != ticket.key ||
      value["route"].asString() != ticket.path || value["bucket"].asString() != ticket.bucket)
    return {};
  return value;
}
inline bool MediaMatches(const CFileItem& item, const CVariant& identity, bool folder)
{
  if (!item.HasVideoInfoTag()) return false;
  const auto* tag = item.GetVideoInfoTag();
  const auto kind = identity["kind"].asString();
  if (folder ? (tag->m_type != "season" && tag->m_type != "episode") : tag->m_type != kind)
    return false;
  if (kind == "season" || kind == "episode")
    if (tag->m_iSeason != identity["season"].asInteger()) return false;
  if (kind == "episode" && tag->m_iEpisode != identity["episode"].asInteger()) return false;
  bool common = false;
  for (const auto* name : {"tmdb", "tvdb", "imdb"})
  {
    const auto expected = identity["ids"][name].asString();
    const auto actual = tag->GetUniqueID(name);
    if (expected.empty() || actual.empty()) continue;
    if (expected != actual) return false;
    common = true;
  }
  return common;
}
inline bool FolderMatches(const Ticket& ticket, const CFileItemList& items)
{
  const auto pending = Pending(ticket);
  if (!pending.isObject()) return false;
  for (int i = 0; i < items.Size(); ++i)
  {
    const auto item = items.Get(i);
    if (item && !item->IsParentFolder() && MediaMatches(*item, pending["identity"], true))
      return true;
  }
  return false;
}
inline void PublishSuccess(const Ticket& ticket)
{
  if (!Enabled() || !ticket.recovering || !ticket.succeeded || !Pending(ticket).isObject()) return;
  CVariant value(CVariant::VariantTypeObject);
  value["schema"] = 2; value["key"] = ticket.key; value["token"] = ticket.token;
  value["bucket"] = ticket.bucket; value["folder"] = ticket.folder;
  value["original_sha256"] = Hash(ticket.originalPath); value["destination_sha256"] = Hash(ticket.path);
  value["phase"] = ticket.folder ? "directory_opened" : "media_resolved";
  value["identity_verified"] = true;
  value["epoch_ms"] = static_cast<int64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count());
  std::string raw; CJSONVariantWriter::Write(value, raw, true);
  Home("Infinity.SavedNavigation.Success", &raw);
  // Resolved media is remembered only after the existing onAVStarted callback.
  if (ticket.folder)
    CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
        "RunPlugin(plugin://script.infinity.commandcenter/?action=saved-confirm&key=" + ticket.key +
        "&token=" + ticket.token + ")");
}
inline void WindowResult(const std::string& path, bool success, const CFileItemList& items)
{
  try
  {
    WatchWindowResult(path, success, items);
    const auto current = State().Read();
    if (!current || !current->folder || current->path != path) return;
    bool populated = false;
    for (int i = 0; i < items.Size(); ++i)
      if (items.Get(i) && !items.Get(i)->IsParentFolder()) { populated = true; break; }
    const bool verified = success && populated && (!current->recovering || FolderMatches(*current, items));
    const auto ticket = State().Finish(current->token, path, verified,
        success && populated ? "provider_identity_unverified" : "provider_directory_failed");
    if (ticket) { if (ticket->succeeded) PublishSuccess(*ticket); else Publish(*ticket); }
  }
  catch (...) { }
}
inline void DirectoryCancelled(const std::string& path, bool cancelled)
{
  if (!cancelled) return;
  try
  {
    const auto current = State().Read();
    const auto watchCurrent = State().WatchCurrent(path, WatchProfile());
    if (watchCurrent && !watchWindows.empty() && watchWindows.back().path == path &&
        watchWindows.back().generation == watchCurrent->generation) State().WatchInvalidate();
    if (current && current->folder && current->path == path) State().Cancelled(current->token);
  }
  catch (...) { }
}
inline thread_local std::string movieToken;
inline thread_local bool movieIdentityVerified{false};
// Inspect the fresh resolver result before Kodi merges the original saved tags.
// Only a currently selected recovery is affected; ordinary providers retain
// their exact success result and metadata path.
inline bool MovieResolved(const std::string& path, bool success, CFileItem& fresh)
{
  WatchResolved(path, success, fresh);
  const auto current = State().Read();
  if (!Enabled() || !current || !current->recovering || current->folder ||
      current->token != movieToken || current->path != path || !success) return success;
  movieIdentityVerified = MediaMatches(fresh, Pending(*current)["identity"], false);
  return movieIdentityVerified;
}
class MovieAttempt
{
public:
  explicit MovieAttempt(const CFileItem& item) : m_previous(movieToken), m_previousVerified(movieIdentityVerified),
      m_previousWatch(std::move(watchMoviePermit))
  {
    watchMoviePermit.reset(); // Ordinary nested/concurrent callers cannot borrow a route lookup.
    try
    {
      const std::string path = item.GetDynPath();
      if (!Enabled() || !ProviderPath(path)) return;
      PrepareRecoveryNext(path);
      if (auto launch = WatchLaunch(item)) watchMoviePermit = std::move(launch);
      else watchMoviePermit = State().WatchItemPermit(
          item.GetProperty("Infinity.Watchlist.Child").asString(), path, WatchProfile());
      auto current = State().Read();
      if (!current || current->path != path || current->failed)
      {
        Begin(item, item.GetProperty("ParentPath").asString(), false);
        current = State().Read();
      }
      if (current && !current->folder && !current->failed && current->path == path)
      {
        m_token = movieToken = current->token;
        movieIdentityVerified = false;
        m_path = path;
      }
    }
    catch (...) { }
  }
  ~MovieAttempt() { movieToken = m_previous; movieIdentityVerified = m_previousVerified; watchMoviePermit = std::move(m_previousWatch); }
  void Finish(bool success, const CFileItem& result)
  {
    try
    {
      if (m_token.empty()) return;
      const auto current = State().Read();
      if (!current || current->token != m_token || current->path != m_path) return;
      const bool verified = success && (!current->recovering || (movieIdentityVerified && MediaMatches(result, Pending(*current)["identity"], false)));
      const auto ticket = State().Finish(m_token, m_path, verified,
          success ? "provider_identity_unverified" : "provider_resolution_failed");
      if (ticket) { if (ticket->succeeded) PublishSuccess(*ticket); else Publish(*ticket); }
    }
    catch (...) { }
  }
private:
  std::string m_previous, m_token, m_path;
  bool m_previousVerified{false};
  std::optional<WatchOrigin> m_previousWatch;
};
inline void MovieCancelled(bool cancelled)
{
  if (cancelled && !movieToken.empty())
    try { State().Cancelled(movieToken); } catch (...) { }
}
} // namespace InfinitySavedNavigation
#endif
