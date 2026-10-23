#pragma once

#if defined(TARGET_ANDROID)
#include "InfinitySavedNavigationState.h"
#include "FileItem.h"
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
inline bool Begin(const CFileItem& item, const std::string& listing)
{
  try
  {
    const auto bucket = item.GetProperty("Infinity.ResumeHub.Bucket").asString();
    if (!Enabled() || !Bucket(bucket)) return false;
    // Home playback carries the exact first-party listing on its original item.
    const CURL parent(listing.empty() ? item.GetProperty("Infinity.SavedNavigation.Listing").asString() : listing);
    if (!parent.IsProtocol("plugin") || parent.GetHostName() != "script.infinity.commandcenter" ||
        parent.GetOption("action") != "library" || parent.GetOption("bucket") != bucket) return false;
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
inline void PrepareNext(const std::string& path)
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
    const auto current = State().Read();
    if (!current || !current->folder || current->path != path) return;
    const bool verified = success && (!current->recovering || FolderMatches(*current, items));
    const auto ticket = State().Finish(current->token, path, verified,
        success ? "provider_identity_unverified" : "provider_directory_failed");
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
    if (current && current->folder && current->path == path) State().Cancelled(current->token);
  }
  catch (...) { }
}
inline thread_local std::string movieToken;
class MovieAttempt
{
public:
  explicit MovieAttempt(const CFileItem& item) : m_previous(movieToken)
  {
    try
    {
      const std::string path = item.GetDynPath();
      if (!Enabled() || !ProviderPath(path)) return;
      PrepareNext(path);
      auto current = State().Read();
      if (!current || current->path != path || current->failed)
      {
        Begin(item, item.GetProperty("ParentPath").asString());
        current = State().Read();
      }
      if (current && !current->folder && !current->failed && current->path == path)
      {
        m_token = movieToken = current->token;
        m_path = path;
      }
    }
    catch (...) { }
  }
  ~MovieAttempt() { movieToken = m_previous; }
  void Finish(bool success, const CFileItem& result)
  {
    try
    {
      if (m_token.empty()) return;
      const auto current = State().Read();
      if (!current || current->token != m_token || current->path != m_path) return;
      const bool verified = success && (!current->recovering || MediaMatches(result, Pending(*current)["identity"], false));
      const auto ticket = State().Finish(m_token, m_path, verified,
          success ? "provider_identity_unverified" : "provider_resolution_failed");
      if (ticket) { if (ticket->succeeded) PublishSuccess(*ticket); else Publish(*ticket); }
    }
    catch (...) { }
  }
private:
  std::string m_previous, m_token, m_path;
};
inline void MovieCancelled(bool cancelled)
{
  if (cancelled && !movieToken.empty())
    try { State().Cancelled(movieToken); } catch (...) { }
}
} // namespace InfinitySavedNavigation
#endif
