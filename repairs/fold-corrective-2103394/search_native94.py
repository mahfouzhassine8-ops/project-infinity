"""Bound only Infinity Universal Search directory-result consumers.

Provider URLs reach the original provider unchanged. Timed-out result handles
retire normally; script invokers, file descriptors, databases and protected
writers remain in the original checkpoint accounting. No StopScript/kill or
false persistence receipt is introduced. At most three such invocations can
remain alive, including timed-out requests, across all Search All sessions.
"""
from native94 import once

RUNNER='xbmc/interfaces/generic/ScriptRunner.cpp'
HEADER='xbmc/interfaces/generic/ScriptRunner.h'
PLUGIN='xbmc/filesystem/PluginDirectory.cpp'

HELPERS=r'''
#if defined(TARGET_ANDROID)
namespace
{
struct InfinitySearchLeases
{
  std::mutex mutex;
  std::map<std::string, int> scripts;
  bool Reserve(const std::string& token)
  {
    std::map<std::string, int> previous;
    { std::lock_guard<std::mutex> lock(mutex); previous = scripts; }
    for (const auto& entry : previous)
      if (entry.second >= 0 && !CScriptInvocationManager::GetInstance().IsRunning(entry.second))
      {
        std::lock_guard<std::mutex> lock(mutex);
        const auto current = scripts.find(entry.first);
        if (current != scripts.end() && current->second == entry.second)
          scripts.erase(current);
      }
    std::lock_guard<std::mutex> lock(mutex);
    if (scripts.size() >= 3 || scripts.count(token))
      return false;
    scripts.emplace(token, -1);
    return true;
  }
  void Started(const std::string& token, int id)
  {
    std::lock_guard<std::mutex> lock(mutex);
    if (id < 0) scripts.erase(token);
    else scripts[token] = id;
  }
};
InfinitySearchLeases& InfinitySearchJobs()
{
  static auto* jobs = new InfinitySearchLeases;
  return *jobs;
}
std::string InfinitySearchProperty(const std::string& key, const char* value = nullptr)
{
  auto* gui = CServiceBroker::GetGUI();
  auto* win = CServiceBroker::GetWinSystem();
  if (!gui || !win) return {};
  std::unique_lock<CCriticalSection> lock(win->GetGfxContext());
  auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME);
  if (!home) return {};
  if (value) home->SetProperty(key, value);
  return home->GetProperty(key).asString();
}
bool InfinitySearchOwnerVerified()
{
  for (const char* root : {"special://home/addons/", "special://xbmc/addons/"})
    if (InfinityAndroidCheckpoint::ClassifyScript(
            std::string(root) + "script.infinity.commandcenter/plugin.py",
            "script.infinity.commandcenter") == "command_center_client")
      return true;
  return false;
}
}
#endif
'''

PREPARE=r'''
#if defined(TARGET_ANDROID)
  // INFINITY_2103394_BOUNDED_SEARCH: explicit result-consumer lease only.
  // Protocol metadata is removed before provider invocation. Ordinary Kodi,
  // background playback, provider menus and Cobra keep their original path.
  m_infinitySearch = false;
  std::string infinityProviderPath = path;
  CURL infinityRequest(path);
  m_infinitySearchToken = infinityRequest.GetProtocolOption("infinity_search");
  if (!m_infinitySearchToken.empty())
  {
    const auto separator = path.find('|');
    const bool tokenValid = m_infinitySearchToken.size() == 32 &&
        m_infinitySearchToken.find_first_not_of("0123456789abcdef") == std::string::npos;
    const bool protocolValid = infinityRequest.GetProtocolOptions() ==
        "infinity_search=" + m_infinitySearchToken;
    if (!tokenValid || !protocolValid || separator == std::string::npos ||
        path.size() > 8192 || CServiceBroker::GetAppMessenger()->IsProcessThread() ||
        XBMCAddon::xbmc::getSkinDir() != "skin.infinity.diggz" ||
        InfinityAndroidCheckpoint::IsActive() ||
        CScriptInvocationManager::GetInstance().IsShutdownRequested() ||
        !InfinitySearchOwnerVerified())
      return false;
    infinityProviderPath = path.substr(0, separator);
    const std::string proof = KODI::UTILITY::CDigest::Calculate(
        KODI::UTILITY::CDigest::Type::SHA256, infinityProviderPath);
    const std::string leaseKey = "Infinity.Search.Request." + m_infinitySearchToken;
    if (InfinitySearchProperty(leaseKey) != proof)
      return false;
    InfinitySearchProperty(leaseKey, "");
    if (addon->ID() == "script.infinity.commandcenter" &&
        infinityProviderPath == "plugin://script.infinity.commandcenter/?action=search-probe")
    {
      InfinitySearchProperty("Infinity.Search.Protocol", "1");
      return true;
    }
    if (infinityRequest.GetProtocol() != "plugin" ||
        infinityRequest.GetHostName() != addon->ID() ||
        addon->ID().compare(0, 13, "plugin.video.") != 0 ||
        !InfinitySearchJobs().Reserve(m_infinitySearchToken))
    {
      InfinitySearchProperty("Infinity.Search.Result." + m_infinitySearchToken, "busy_or_unsupported");
      return false;
    }
    m_infinitySearch = true;
    m_infinitySearchDeadline = std::chrono::steady_clock::now() + std::chrono::seconds(20);
  }
#endif
'''

EXPIRY=r'''
#if defined(TARGET_ANDROID)
bool CScriptRunner::InfinitySearchExpired()
{
  if (!m_infinitySearch) return false;
  const bool cancelled = InfinitySearchProperty("Infinity.Search.Cancel." + m_infinitySearchToken) == "1";
  if (!cancelled && std::chrono::steady_clock::now() < m_infinitySearchDeadline)
    return false;
  InfinitySearchProperty("Infinity.Search.Result." + m_infinitySearchToken,
                         cancelled ? "cancelled" : "timeout");
  // Return the consumer, not a fake end-of-script or persistence completion.
  // The invocation stays registered and occupies its bounded slot until its
  // real thread finishes; all original Close admission barriers remain active.
  return true;
}
#endif
'''


def patches(before):
    out=dict(before)
    raw=out[HEADER]
    raw=once(raw,b'#include <string>',b'#include <string>\n#include <chrono>')
    raw=once(raw,b'  CEvent m_scriptDone;',b'''  CEvent m_scriptDone;
#if defined(TARGET_ANDROID)
  bool InfinitySearchExpired();
  bool m_infinitySearch{false};
  std::string m_infinitySearchToken;
  std::chrono::steady_clock::time_point m_infinitySearchDeadline;
#endif''')
    out[HEADER]=raw
    raw=out[RUNNER]
    raw=once(raw,b'#include "platform/android/activity/InfinityShutdownTrace.h"',
        b'''#include "platform/android/activity/InfinityShutdownTrace.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "interfaces/legacy/ModuleXbmc.h"
#include "guilib/GUIWindow.h"
#include "windowing/WinSystem.h"
#include "utils/Digest.h"
#include <map>
#include <mutex>''')
    raw=once(raw,b'using namespace std::chrono_literals;',HELPERS.encode()+b'\nusing namespace std::chrono_literals;')
    raw=once(raw,b'  int scriptId = ExecuteScript(addon, path, handle, resume);',
        PREPARE.encode()+b'''  int scriptId = ExecuteScript(addon,
#if defined(TARGET_ANDROID)
      infinityProviderPath,
#else
      path,
#endif
      handle, resume);
#if defined(TARGET_ANDROID)
  if (m_infinitySearch) InfinitySearchJobs().Started(m_infinitySearchToken, scriptId);
#endif''')
    marker=b'      if (shutdownResultCancelled())'
    # Both polling loops retain the original shutdown cancellation at every
    # point. Only a previously validated private search lease gets a deadline.
    assert raw.count(marker)==2
    raw=raw.replace(marker,b'      if (InfinitySearchExpired()) return false;\n'+marker)
    marker=b'    if (shutdownResultCancelled())'
    assert raw.count(marker)==4  # two indented loop calls plus two epilogues
    raw=raw.replace(b'\n    if (shutdownResultCancelled())',b'\n    if (InfinitySearchExpired()) return false;\n    if (shutdownResultCancelled())')
    raw=once(raw,b'  return !cancelled && !IsCancelled() && IsSuccessful();',b'''#if defined(TARGET_ANDROID)
  if (m_infinitySearch)
    InfinitySearchProperty("Infinity.Search.Result." + m_infinitySearchToken,
                           !cancelled && !IsCancelled() && IsSuccessful() ? "completed" : "failed");
#endif
  return !cancelled && !IsCancelled() && IsSuccessful();''')
    out[RUNNER]=raw+EXPIRY.encode()
    raw=out[PLUGIN]
    start=raw.index(b'bool CPluginDirectory::StartScript(')
    end=raw.index(b'bool CPluginDirectory::GetResolvedPluginResult(',start)
    body=raw[start:end]
    changed=once(body,b'!CAddonInstaller::GetInstance().InstallModal(url.GetHostName(), addon,',
        b'(!url.GetProtocolOption("infinity_search").empty() ||\n       !CAddonInstaller::GetInstance().InstallModal(url.GetHostName(), addon,')
    changed=once(changed,b'InstallModalPrompt::CHOICE_YES))',b'InstallModalPrompt::CHOICE_YES)))')
    raw=once(raw,body,changed)
    out[PLUGIN]=raw
    return out
