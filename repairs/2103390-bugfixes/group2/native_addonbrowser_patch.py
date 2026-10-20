#!/usr/bin/env python3
"""INFINITY Group #2 only: fail-closed Kodi native Add-on Browser patch.

The four source files are ONLY staged, not installed/built. Every original
source file SHA-256 is supplied by the checked-out, recorded native baseline.
The user-approved behavior change is bounded to window AddonBrowser under
skin.infinity.diggz. Every other path retains its original implementation.
Cobra, shutdown, services, providers, playback and user data untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PATCHES = json.loads(r'''{"xbmc/addons/gui/GUIWindowAddonBrowser.h":[["#include <string>\n#include <vector>","#include <set>\n#include <string>\n#include <vector>"],["  bool OnClick(int iItem, const std::string& player = \"\") override;\n  void UpdateButtons() override;","  bool OnClick(int iItem, const std::string& player = \"\") override;\n  void GetContextButtons(int itemNumber, CContextButtons& buttons) override;\n  bool OnContextButton(int itemNumber, CONTEXT_BUTTON button) override;\n  void UpdateButtons() override;"],["  CProgramThumbLoader m_thumbLoader;","  // Group2: temporary view-only filter; no add-on manager/database writes.\n  std::set<std::string> m_infinityHiddenFromBrowse;\n  std::string m_infinityArmedTouchItem;\n  CProgramThumbLoader m_thumbLoader;"]],"xbmc/addons/gui/GUIWindowAddonBrowser.cpp":[["CGUIWindowAddonBrowser::CGUIWindowAddonBrowser(void)","\nnamespace\n{\nconstexpr CONTEXT_BUTTON INFINITY_HIDE_FROM_BROWSER = static_cast<CONTEXT_BUTTON>(0x7901);\nbool InfinityAddonBrowserSkinActive()\n{\n  const auto settings = CServiceBroker::GetSettingsComponent()->GetSettings();\n  return settings && settings->GetString(\"lookandfeel.skin\") == \"skin.infinity.diggz\";\n}\nbool InfinityIsUserAddonSection(const std::string& path)\n{\n  return StringUtils::StartsWith(path, \"addons://user/\");\n}\n} // namespace\n\nCGUIWindowAddonBrowser::CGUIWindowAddonBrowser(void)"],["    case GUI_MSG_WINDOW_DEINIT:\n    {\n      CServiceBroker::GetRepositoryUpdater().Events().Unsubscribe(this);","    case GUI_MSG_WINDOW_DEINIT:\n    {\n      m_infinityHiddenFromBrowse.clear();\n      m_infinityArmedTouchItem.clear();\n      CServiceBroker::GetRepositoryUpdater().Events().Unsubscribe(this);"],["        // iItem is checked for validity inside these routines\n        if (iAction == ACTION_SHOW_INFO)","        // Group2: first touch selects; second deliberate touch activates.\n        // Keyboard/D-pad and every other Kodi window retain native behavior.\n        if (InfinityAddonBrowserSkinActive() && iAction == ACTION_MOUSE_LEFT_CLICK &&\n            iItem >= 0 && iItem < m_vecItems->Size())\n        {\n          const std::string fingerprint = m_vecItems->GetPath() + \"|\" +\n              std::to_string(iItem) + \"|\" + m_vecItems->Get(iItem)->GetPath();\n          if (m_infinityArmedTouchItem != fingerprint)\n          {\n            m_infinityArmedTouchItem = fingerprint;\n            return true;\n          }\n          m_infinityArmedTouchItem.clear();\n        }\n        // iItem is checked for validity inside these routines\n        if (iAction == ACTION_SHOW_INFO)"],["  CFileItemPtr item = m_vecItems->Get(iItem);\n  if (item->GetPath() == \"addons://install/\")","  if (iItem < 0 || iItem >= m_vecItems->Size())\n    return true;\n  CFileItemPtr item = m_vecItems->Get(iItem);\n  if (InfinityAddonBrowserSkinActive() && item->GetPath() == \"addons://infinity-show-hidden/\")\n  {\n    m_infinityHiddenFromBrowse.clear();\n    m_infinityArmedTouchItem.clear();\n    Refresh();\n    return true;\n  }\n  if (item->GetPath() == \"addons://install/\")"],["  for (int i = 0; i < items.Size(); ++i)\n    UpdateStatus(items[i]);","  // Preserve all six authentic Kodi Add-on Browser root routes even when\n  // Kodi's default root hides empty update categories.\n  if (result && InfinityAddonBrowserSkinActive() &&\n      (strDirectory == \"addons://\" || strDirectory == \"addons:///\"))\n  {\n    const auto ensureNativeRoute = [&items](const std::string& route, const std::string& label)\n    {\n      for (int i = 0; i < items.Size(); ++i)\n        if (items[i]->GetPath() == route)\n          return;\n      auto node = std::make_shared<CFileItem>(route, true);\n      node->SetLabel(label);\n      node->SetArt(\"icon\", \"DefaultAddonsUpdates.png\");\n      items.Add(node);\n    };\n    ensureNativeRoute(\"addons://outdated/\", \"Available updates\");\n    ensureNativeRoute(\"addons://recently_updated/\", \"Recently updated\");\n  }\n  // A reversible browser-only filter, never a Kodi AddonManager change.\n  if (result && InfinityAddonBrowserSkinActive() &&\n      InfinityIsUserAddonSection(strDirectory) && !m_infinityHiddenFromBrowse.empty())\n  {\n    for (int i = items.Size() - 1; i >= 0; --i)\n    {\n      const std::string id = items[i]->GetProperty(\"Addon.ID\").asString();\n      if (!id.empty() && m_infinityHiddenFromBrowse.count(id))\n        items.Remove(i);\n    }\n    // The user can recover hidden items even if every add-on is filtered.\n    auto restore = std::make_shared<CFileItem>(\"addons://infinity-show-hidden/\", false);\n    restore->SetLabel(\"Show hidden add-ons\");\n    restore->SetArt(\"icon\", \"DefaultAddonsInstalled.png\");\n    restore->SetSpecialSort(SortSpecialOnTop);\n    items.Add(restore);\n  }\n  for (int i = 0; i < items.Size(); ++i)\n    UpdateStatus(items[i]);"],["  if (m_thumbLoader.IsLoading())\n    m_thumbLoader.StopThread();\n\n  if (!CGUIMediaWindow::Update(strDirectory, updateFilterPath))","  if (m_thumbLoader.IsLoading())\n    m_thumbLoader.StopThread();\n  if (strDirectory != m_vecItems->GetPath())\n    m_infinityArmedTouchItem.clear();\n\n  if (!CGUIMediaWindow::Update(strDirectory, updateFilterPath))"],["void CGUIWindowAddonBrowser::UpdateButtons()\n{","\nvoid CGUIWindowAddonBrowser::GetContextButtons(int itemNumber, CContextButtons& buttons)\n{\n  if (!InfinityAddonBrowserSkinActive() || !InfinityIsUserAddonSection(m_vecItems->GetPath()) ||\n      itemNumber < 0 || itemNumber >= m_vecItems->Size())\n    return;\n  const auto& item = m_vecItems->Get(itemNumber);\n  if (item && item->HasAddonInfo() && !item->GetProperty(\"Addon.ID\").asString().empty())\n    buttons.Add(INFINITY_HIDE_FROM_BROWSER, \"Hide from this browser (not Disable)\");\n}\n\nbool CGUIWindowAddonBrowser::OnContextButton(int itemNumber, CONTEXT_BUTTON button)\n{\n  if (button != INFINITY_HIDE_FROM_BROWSER || !InfinityAddonBrowserSkinActive() ||\n      !InfinityIsUserAddonSection(m_vecItems->GetPath()) ||\n      itemNumber < 0 || itemNumber >= m_vecItems->Size())\n    return false;\n  const auto& item = m_vecItems->Get(itemNumber);\n  if (!item || !item->HasAddonInfo())\n    return false;\n  const std::string id = item->GetProperty(\"Addon.ID\").asString();\n  if (id.empty())\n    return false;\n  // This is never Kodi DisableAddon/UnInstall; hidden IDs are only in memory.\n  m_infinityHiddenFromBrowse.insert(id);\n  m_infinityArmedTouchItem.clear();\n  Refresh();\n  return true;\n}\n\nvoid CGUIWindowAddonBrowser::UpdateButtons()\n{"]],"xbmc/addons/gui/GUIDialogAddonInfo.cpp":[["    if (PromptIfDependency(24075, 24091))\n      return; //required. can't disable\n\n    CServiceBroker::GetAddonMgr().DisableAddon(m_localAddon->ID(), AddonDisabledReason::USER);","    if (PromptIfDependency(24075, 24091))\n      return; //required. can't disable\n\n    // Disable is NOT a reversible Hide; confirm only in Infinity Add-on Browser.\n    if (CServiceBroker::GetGUI()->GetWindowManager().GetActiveWindow() == WINDOW_ADDON_BROWSER &&\n        CServiceBroker::GetSettingsComponent()->GetSettings()->GetString(\"lookandfeel.skin\") ==\n            \"skin.infinity.diggz\" &&\n        !CGUIDialogYesNo::ShowAndGetInput(CVariant{\"Disable add-on?\"},\n                                         CVariant{m_localAddon->Name()},\n                                         CVariant{\"This stops the add-on. To only hide it, use the browser Hide action.\"}, CVariant{\"\"}))\n      return;\n\n    CServiceBroker::GetAddonMgr().DisableAddon(m_localAddon->ID(), AddonDisabledReason::USER);"]],"xbmc/addons/ContextMenus.cpp":[["#include \"addons/gui/GUIHelpers.h\"","#include \"addons/gui/GUIHelpers.h\"\n#include \"guilib/WindowIDs.h\"\n#include \"dialogs/GUIDialogYesNo.h\"\n#include \"guilib/GUIComponent.h\"\n#include \"guilib/GUIWindowManager.h\"\n#include \"settings/Settings.h\"\n#include \"settings/SettingsComponent.h\"\n#include \"utils/Variant.h\""],["  return CServiceBroker::GetAddonMgr().DisableAddon(item->GetAddonInfo()->ID(),\n                                                    AddonDisabledReason::USER);","  // Same browser-only confirmation for the direct native context-menu path.\n  if (CServiceBroker::GetGUI()->GetWindowManager().GetActiveWindow() == WINDOW_ADDON_BROWSER &&\n      CServiceBroker::GetSettingsComponent()->GetSettings()->GetString(\"lookandfeel.skin\") ==\n          \"skin.infinity.diggz\" &&\n      !CGUIDialogYesNo::ShowAndGetInput(CVariant{\"Disable add-on?\"},\n                                       CVariant{item->GetAddonInfo()->Name()},\n                                       CVariant{\"This stops the add-on. To only hide it, use the browser Hide action.\"}, CVariant{\"\"}))\n    return false;\n  return CServiceBroker::GetAddonMgr().DisableAddon(item->GetAddonInfo()->ID(),\n                                                    AddonDisabledReason::USER);"]]}''')
FILES = tuple(PATCHES)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch_member(filename: str, data: bytes) -> bytes:
    if filename not in PATCHES:
        raise ValueError("Unapproved Group 2 native source path")
    text=data.decode("utf-8")
    for old,new in PATCHES[filename]:
        if text.count(old) != 1 or new in text:
            raise ValueError("Unknown native source anchor or patch already applied: "+filename)
        text=text.replace(old,new,1)
    if text.encode("utf-8")==data:
        raise ValueError("No scoped native source change")
    return text.encode("utf-8")

def stage(original: Path, destination: Path, sha_manifest: dict[str,str]) -> dict:
    original,destination=Path(original).resolve(),Path(destination).resolve()
    if original==destination or destination.is_relative_to(original) or original.is_relative_to(destination):
        raise ValueError("Protected source tree and output must be separate")
    if set(sha_manifest)!=set(FILES):
        raise ValueError("Incomplete/unapproved original source SHA manifest")
    staged={}
    for filename in FILES:
        before=(original/filename).read_bytes()
        if sha256(before)!=sha_manifest[filename]:
            raise ValueError("Native 2103390 source no longer matches: "+filename)
        staged[filename]=patch_member(filename,before)
    # Verify the ENTIRE original allowlist before writing any output.
    for filename,after in staged.items():
        path=destination/filename
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(after)
    return {
        "type":"INFINITY_GROUP2_HOST_SOURCE_STAGE_ONLY",
        "original_native_files_modified":0,
        "native_source_files_staged":[
            {"path":p,"original_sha256":sha_manifest[p],"staged_sha256":sha256(staged[p])}
            for p in FILES
        ],
        "original_kodi_core_behavior":"Unchanged outside Add-on Browser + Infinity skin guards",
        "Cobra_code_modified":False, "shutdown_modified":False,
        "disabled_addons_or_deleted_user_data":False,
        "compiled_native_build":"NOT_RUN",
        "physical_fold_verification":"NOT_RUN",
        "applied_to_signed_apk":False
    }

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("source_tree",type=Path)
    cli.add_argument("staged_tree",type=Path)
    cli.add_argument("--original-hashes",type=Path,required=True)
    x=cli.parse_args()
    print(json.dumps(stage(x.source_tree,x.staged_tree,
          json.loads(x.original_hashes.read_text(encoding="utf-8"))),indent=2))
