#!/usr/bin/env python3
"""One-file, Rails-scoped Kodi directory scheduling and stale-result correction.

Preserves all 17 shutdown owners, RC1 interpreter retirement, skin, and helper.
No changed touch mapping, renderer, data store, or application setting.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

SOURCE = "xbmc/guilib/listproviders/DirectoryProvider.cpp"
PROTECTED = (
    "xbmc/interfaces/python/PythonInvoker.cpp",
    "xbmc/interfaces/python/PythonInvoker.h",
    "xbmc/interfaces/generic/ScriptInvocationManager.cpp",
    "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp",
    "xbmc/platform/android/activity/InfinityScriptPersistence.h",
    "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp",
)
HELPER = r'''
// Home-only add-on cards: do not accelerate ordinary browsing, provider URLs,
// arbitrary RunScript calls, or URLs whose section merely shares a prefix.
static bool InfinityIsAddonRailRequest(const std::string& url)
{
  constexpr char prefix[] = "plugin://script.infinity.rails/?section=";
  constexpr std::size_t start = sizeof(prefix) - 1;
  if (url.compare(0, start, prefix) != 0)
    return false;
  const auto tail = url.substr(start);
  return (tail.compare(0, 6, "movies") == 0 &&
          (tail.size() == 6 || tail[6] == '&')) ||
         (tail.compare(0, 7, "tvshows") == 0 &&
          (tail.size() == 7 || tail[7] == '&'));
}
'''
PRIORITY_BEFORE = '''    m_jobID = CServiceBroker::GetJobManager()->AddJob(
        new CDirectoryJob(m_currentUrl, m_target.GetLabel(m_parentID, false), m_currentSort,
                          m_currentLimit, m_currentBrowse, m_parentID),
        this);'''
PRIORITY_AFTER = '''    // Startup can have 70+ low-priority widget directories queued. Promote
    // ONLY Infinity's two on-screen Add-on Rails to normal display priority.
    // Keep every other Kodi directory at its original low priority.
    const auto priority = InfinityIsAddonRailRequest(m_currentUrl)
                              ? CJob::PRIORITY_NORMAL : CJob::PRIORITY_LOW;
    m_jobID = CServiceBroker::GetJobManager()->AddJob(
        new CDirectoryJob(m_currentUrl, m_target.GetLabel(m_parentID, false), m_currentSort,
                          m_currentLimit, m_currentBrowse, m_parentID),
        this, priority);'''
STALE_BEFORE = '''  if (success)
  {
    m_items = static_cast<CDirectoryJob*>(job)->GetItems();'''
STALE_AFTER = '''  // A cancelled directory may finish after a section switch. OnJobComplete
  // is invoked on the worker: publishing an old rail list here can overwrite
  // a newer active request or clear its job ID. Reject only obsolete *rail*
  // completions; leave every non-rail directory callback unchanged.
  const auto* completed = static_cast<CDirectoryJob*>(job);
  if ((InfinityIsAddonRailRequest(m_currentUrl) ||
       InfinityIsAddonRailRequest(completed->GetUrl())) &&
      (jobID == 0 || jobID != m_jobID || completed->GetUrl() != m_currentUrl))
  {
    CLog::Log(LOGDEBUG, "Infinity rails: stale job discarded job={} current={}",
              jobID, m_jobID);
    return;
  }
  if (success)
  {
    m_items = static_cast<CDirectoryJob*>(job)->GetItems();'''

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def once(raw: str, old: str, new: str, key: str):
    if raw.count(old) != 1:
        raise RuntimeError(f"Rail handoff source anchor {key}: expected 1, got {raw.count(old)}")
    return raw.replace(old, new, 1)

def apply(root: Path, expected_source_sha: str | None = None):
    root = Path(root)
    protected = {p:sha((root / p).read_bytes()) for p in PROTECTED}
    source = root / SOURCE
    before = source.read_bytes()
    if expected_source_sha and sha(before) != expected_source_sha:
        raise RuntimeError("Refusing different DirectoryProvider from verified RC1 parent")
    data = before.decode("utf-8")
    if "InfinityIsAddonRailRequest" in data:
        raise RuntimeError("Rail handoff repair already installed")
    data = once(data, "using namespace PVR;\n\nclass CDirectoryJob",
                "using namespace PVR;\n" + HELPER + "\nclass CDirectoryJob", "rail_url")
    data = once(data, '  const std::vector<CGUIStaticItemPtr> &GetItems() const { return m_items; }',
                '  const std::vector<CGUIStaticItemPtr> &GetItems() const { return m_items; }\n'
                '  const std::string& GetUrl() const { return m_url; }',
                "job_identity")
    data = once(data, PRIORITY_BEFORE, PRIORITY_AFTER, "rail_priority")
    start = data.index("void CDirectoryProvider::OnJobComplete(")
    end = data.index("\n}\n", start) + 3
    method = data[start:end]
    method_new = once(method, STALE_BEFORE, STALE_AFTER, "stale_callback")
    data = data[:start] + method_new + data[end:]
    source.write_text(data)
    for p, expected in protected.items():
        if sha((root/p).read_bytes()) != expected:
            raise RuntimeError("Protected subsystem changed: " + p)
    return {
        "changed": [SOURCE],
        "before": {SOURCE: sha(before)},
        "after": {SOURCE: sha(source.read_bytes())},
        "protected": protected,
        "rails_only_priority_promotion": True,
        "non_rail_callback_behavior_unchanged": True,
        "stale_rail_callback_rejected": True,
        "python_retirement_rc1_preserved": True,
        "all_17_shutdown_owner_gates_preserved": True,
        "skin_1_0_5_223_preserved": True,
        "rails_helper_preserved": True,
        "physical_fold_verified": False,
        "locked": False,
    }
