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
inline void Begin(const CFileItem& item, const std::string& listing)
{
  try
  {
    if (!Enabled() || item.GetProperty("Infinity.ResumeHub.Bucket").asString() != "later") return;
    const CURL parent(listing);
    if (!parent.IsProtocol("plugin") || parent.GetHostName() != "script.infinity.commandcenter" ||
        parent.GetOption("action") != "library" || parent.GetOption("bucket") != "later") return;
    const auto key = item.GetProperty("Infinity.ResumeHub.Key").asString();
    const auto& path = item.GetPath();
    if (!Key(key) || !ProviderPath(path)) return;
    Ticket ticket;
    ticket.token = StringUtils::CreateUUID();
    ticket.key = key;
    ticket.originalPath = ticket.path = path;
    ticket.folder = item.m_bIsFolder;
    ticket.attempted.push_back(CURL(path).GetHostName());
    State().Begin(std::move(ticket));
    const std::string empty;
    Home("Infinity.SavedNavigation.Failure", &empty);
    Home("Infinity.SavedNavigation.Next", &empty);
    CLog::Log(LOGINFO, "INFINITY_SAVED_ROUTE_BEGIN key={} destination_sha256={}", key, Hash(path));
  }
  catch (...) { } // Observation must preserve the original user action.
}
inline void PrepareNext(const std::string& path)
{
  try
  {
    if (!Enabled() || !ProviderPath(path)) return;
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
  value["original_sha256"] = Hash(ticket.originalPath);
  value["failed_sha256"] = Hash(ticket.path);
  value["reason"] = ticket.reason;
  value["folder"] = ticket.folder;
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
      "&token=" + ticket.token + ")");
}
inline void WindowResult(const std::string& path, bool success)
{
  try
  {
    const auto current = State().Read();
    if (!current || !current->folder || current->path != path) return;
    const auto ticket = State().Finish(current->token, path, success, "provider_directory_failed");
    if (ticket) Publish(*ticket);
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
  void Finish(bool success)
  {
    try
    {
      if (m_token.empty()) return;
      const auto ticket = State().Finish(m_token, m_path, success, "provider_resolution_failed");
      if (ticket) Publish(*ticket);
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
