"""Exact seven-workstream native delta over the verified 2103397 engine inputs."""
from pathlib import Path
import json
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'fold-targeted-2103396'))
import native96 as previous
from native94 import require, once

VFS='xbmc/dbwrappers/InfinitySQLiteVFS.h'
CONTAINER=previous.CONTAINER
HEADER='xbmc/guilib/GUIBaseContainer.h'
INPUT='xbmc/input/InputManager.cpp'
BROWSER='xbmc/addons/gui/GUIWindowAddonBrowser.cpp'
CONTRACT=previous.CONTRACT
COORDINATOR=previous.COORDINATOR
BUTTON='xbmc/guilib/GUIButtonControl.cpp'
BUTTON_HEADER='xbmc/guilib/GUIButtonControl.h'
ADDON_INFO='xbmc/addons/gui/GUIDialogAddonInfo.cpp'
PATHS={VFS,CONTAINER,HEADER,INPUT,BROWSER,CONTRACT,COORDINATOR,BUTTON,BUTTON_HEADER,ADDON_INFO}


def patches(before, original, final):
    require(set(before)==PATHS,'native scope mismatch')
    out=dict(before)
    out[VFS]=once(before[VFS], b'  // Inquiry controls do not mutate bytes.', b'''  // INFINITY_2103398_SQLITE_INVENTORY: database_list is SQLite's own
  // connection inventory. Do not ask a VFS to execute/override this inspection:
  // SQLITE_NOTFOUND continues normal SQLite processing and enumerates actual
  // ATTACH filenames. No file is mutated and no write admission is granted.
  // Every other PRAGMA, xWrite, xTruncate, WAL and ATTACH write stays guarded.
  if (operation == SQLITE_FCNTL_PRAGMA && argument)
  {
    const auto args = static_cast<char**>(argument);
    if (args[1] && sqlite3_stricmp(args[1], "database_list") == 0 && !args[2])
      return SQLITE_NOTFOUND;
  }
  // Inquiry controls do not mutate bytes.''')
    raw=before[CONTAINER]
    raw=once(raw,b'#include "FileItem.h"',b'#include "FileItem.h"\n#include "FileItemList.h"\n#include "windows/GUIMediaWindow.h"\n#include "addons/IAddon.h"\n#include "Util.h"')
    raw=once(raw,b'''  if (path.compare(0, 31, "plugin://plugin.video.umbrella/") != 0)
    { trace("native.validate","provider_mismatch"); return restore(); }
  if (path.size() > 4096)''',b'''  const bool infinityLatest = path.rfind("plugin://plugin.infinity.latestreleases/", 0) == 0;
  if (!infinityLatest && path.compare(0, 31, "plugin://plugin.video.umbrella/") != 0)
    { trace("native.validate","provider_mismatch"); return restore(); }
  if (infinityLatest &&
      (item->GetProperty("Infinity.LatestReleases.Identity").asString() != "v1" ||
       item->GetProperty("Infinity.LatestReleases.Kind").asString() !=
           ((GetID() == 8101 || GetID() == 8801) ? "movie" : "tvshow") ||
       !item->HasVideoInfoTag() || item->GetVideoInfoTag()->m_type !=
           ((GetID() == 8101 || GetID() == 8801) ? "movie" : "tvshow")))
    { trace("native.validate","infinity_media_identity_mismatch"); return restore(); }
  if (path.size() > (infinityLatest ? 32768U : 4096U))''')
    method=(HERE/'browser_touch.cpp').read_bytes()
    raw=once(raw,b'bool CGUIBaseContainer::OnInfinityUiTouch(',method+b'\n\nbool CGUIBaseContainer::OnInfinityUiTouch(')
    import components98 as c
    checks=[]
    for leaf in ('default.py','identity.py','addon.xml'):
        checks.append('CUtil::GetFileDigest(latest->Path() + "/'+leaf+'", UTILITY::CDigest::Type::SHA256) != "'+c.sha(final[c.LATEST+'/'+leaf])+'"')
    source_guard = ('  if (infinityLatest)\n  {\n    ADDON::AddonPtr latest;\n'
      '    if (!CServiceBroker::GetAddonMgr().GetAddon("plugin.infinity.latestreleases", latest, ADDON::OnlyEnabled::CHOICE_YES) ||\n        '+
      ' ||\n        '.join(checks)+')\n    { trace("native.validate","infinity_source_identity_mismatch"); return restore(); }\n  }\n')
    anchor=b'  if (label.empty() || label.size() > 512)\n    { trace("native.validate","label_empty_or_exceeds_512"); return restore(); }'
    raw=once(raw,anchor,anchor+b'\n'+source_guard.encode())
    out[CONTAINER]=raw
    out[HEADER]=once(before[HEADER],b'  bool OnInfinityUiTouch(float x, float y, bool hold);',b'''  bool OnInfinityUiTouch(float x, float y, bool hold);
  bool OnInfinityAddonBrowserTouch(float x, float y, bool hold);
  std::string m_infinityAddonTapKey;
  std::chrono::steady_clock::time_point m_infinityAddonSuppressUntil{};''')
    out[BROWSER]=once(before[BROWSER],b'if (InfinityAddonBrowserSkinActive() && iAction == ACTION_MOUSE_LEFT_CLICK &&',b'''if (InfinityAddonBrowserSkinActive() &&
            !StringUtils::StartsWith(m_vecItems->GetPath(), "addons://search") &&
            iItem >= 0 && iItem < m_vecItems->Size() &&
            !StringUtils::StartsWith(m_vecItems->Get(iItem)->GetPath(), "addons://search") &&
            iAction == ACTION_MOUSE_LEFT_CLICK &&''')
    out[INPUT]=once(before[INPUT],b'      // INFINITY_UI_TOUCH_V1:',b'''#if defined(TARGET_ANDROID)
      // INFINITY_2103398_BROWSER_TOUCH: only actual one-pointer touch while
      // Infinity's Add-on Browser owns the active window. Search is excluded.
      if ((newEvent.touch.action == ACTION_TOUCH_TAP || newEvent.touch.action == ACTION_TOUCH_LONGPRESS) &&
          newEvent.touch.pointers == 1 &&
          CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") == "skin.infinity.diggz")
      {
        auto& wm = CServiceBroker::GetGUI()->GetWindowManager();
        const auto power = CServiceBroker::GetAppComponents().GetComponent<CApplicationPowerHandling>();
        const int modal = wm.GetTopmostModalDialog();
        if (wm.GetActiveWindow() == WINDOW_ADDON_BROWSER && power && !power->IsInScreenSaver() &&
            (modal == WINDOW_INVALID || modal == WINDOW_DIALOG_FILE_BROWSER))
        {
          auto* owner=wm.GetWindow(modal == WINDOW_INVALID ? WINDOW_ADDON_BROWSER : modal);
          bool handled=false;
          if (owner) for (const int id : {owner->GetViewContainerID(), 50, 450})
          {
            auto* view=dynamic_cast<CGUIBaseContainer*>(owner->GetControl(id));
            if (view && view->OnInfinityAddonBrowserTouch(newEvent.touch.x,newEvent.touch.y,
                                       newEvent.touch.action == ACTION_TOUCH_LONGPRESS))
            {handled=true;break;}
          }
          if (handled) break;
        }
      }
#endif
      // INFINITY_UI_TOUCH_V1:''')
    # Add a new exact controller revision; retain all previously valid variants.
    import components98 as c
    _,release,_=previous.old_adapters()
    oldpins=json.loads(original[c.UI+'/CONTROLLER-PREIMAGES.json'])
    newpins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
    require(len(oldpins)==len(newpins)==17,'controller coverage changed')
    raw=before[CONTRACT];blocks=[]
    for endpoint in (*release.coherence.ENDPOINTS,'default.py'):
        matches=[v for v in release.coherence.contracts(raw.decode()) if v['script']==c.CC+'/'+endpoint and v['pins']=={c.CC+'/'+n:h for n,h in oldpins.items()}]
        require(len(matches)==1,'exact CC26 variant missing '+endpoint)
        block=matches[0]['block'].encode()
        for n,pin in oldpins.items():
            if newpins[n]!=pin:block=once(block,pin.encode(),newpins[n].encode())
        blocks.append(block)
    out[CONTRACT]=once(raw,b'  };\n  return *contracts;',b'    // INFINITY_2103398_CC27_EXACT_SOURCES\n'+b'\n'.join(blocks)+b'\n  };\n  return *contracts;')
    out[COORDINATOR]=once(before[COORDINATOR],b'active["addon_version"].asString() != "0.3.5.26"',b'active["addon_version"].asString() != "0.3.5.26" && active["addon_version"].asString() != "0.3.5.27"')
    raw=out[COORDINATOR]
    raw=once(raw,b'  std::string safeStatus; // Immutable full receipt while SAFE remains valid.',
        b'  std::string archivedAttemptKey; // Diagnostic history never grants exit authority.\n  std::string safeStatus; // Immutable full receipt while SAFE remains valid.')
    a=raw.index(b'std::string Status(');b=raw.index(b'\nbool AuthorizeTermination(',a)
    status=raw[a:b]
    status=once(status,b'  std::lock_guard<std::mutex> lock(s.mutex);',b'  std::unique_lock<std::mutex> lock(s.mutex);')
    status=once(status,b'  return s.phase == "SAFE_TO_TERMINATE" ? s.safeStatus : EncodeStatusLocked(s);',b'''  const std::string encoded = s.phase == "SAFE_TO_TERMINATE" ? s.safeStatus : EncodeStatusLocked(s);
  const std::string key = s.session + "-" + s.phase;
  const std::string directory = s.directory;
  const bool archive = (s.phase == "CHECKPOINT_FAILED" || s.phase == "SAFE_TO_TERMINATE") &&
      Token(s.session) && !directory.empty() && key != s.archivedAttemptKey;
  lock.unlock();
  if (archive)
  {
    // Keep each actual terminal native receipt under its own attempt/phase.
    // Existing fsync+atomic rename helper, same coordinator protocol ownership.
    // No permission is added to any provider, and history is never read by exit
    // authorization. A later success cannot replace an earlier failed attempt.
    CoordinatorWriteScope permission;
    const auto saved = infinity::checkpoint::files::SaveProtocolRecord(
        directory + "/attempt-" + key + ".json", encoded);
    if (saved.ok)
    {
      std::lock_guard<std::mutex> historyLock(s.mutex);
      s.archivedAttemptKey = key;
    }
    else CLog::Log(LOGWARNING, "Infinity checkpoint attempt history could not be saved: errno={}", saved.error);
  }
  return encoded;''')
    out[COORDINATOR]=raw[:a]+status+raw[b:]
    out[BUTTON_HEADER]=once(before[BUTTON_HEADER],b'  bool OnAction(const CAction &action) override ;',b'''  bool OnAction(const CAction &action) override ;
  bool OnInfinityAddonActionTouch(float x,float y,bool hold);
  std::string m_infinityAddonActionKey;
  std::chrono::steady_clock::time_point m_infinityAddonActionSuppressUntil{};''')
    out[BUTTON_HEADER]=once(out[BUTTON_HEADER],b'#pragma once',b'#pragma once\n#include <chrono>')
    out[BUTTON]=once(before[BUTTON],b'#include "GUIButtonControl.h"',b'''#include "GUIButtonControl.h"
#include "ServiceBroker.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIWindow.h"
#include "guilib/GUIWindowManager.h"
#include "guilib/WindowIDs.h"''')
    out[BUTTON]=once(out[BUTTON],b'EVENT_RESULT CGUIButtonControl::OnMouseEvent(',
        (HERE/'addon_button_touch.cpp').read_bytes()+b'\n\nEVENT_RESULT CGUIButtonControl::OnMouseEvent(')
    out[ADDON_INFO]=once(before[ADDON_INFO],b'  CGUIDialog::OnInitWindow();\n  BuildDependencyList();',b'''  CGUIDialog::OnInitWindow();
  SetProperty("Infinity.AddonBrowser.ActionIdentity", m_item ? m_item->GetPath() + "\\n" +
      std::to_string(reinterpret_cast<std::uintptr_t>(m_item.get())) : "");
  BuildDependencyList();''')
    out[INPUT]=once(out[INPUT],b'#include "guilib/GUIBaseContainer.h"',b'#include "guilib/GUIBaseContainer.h"\n#include "guilib/GUIButtonControl.h"')
    marker=b'        const int modal = wm.GetTopmostModalDialog();\n        if (wm.GetActiveWindow() == WINDOW_ADDON_BROWSER'
    out[INPUT]=once(out[INPUT],marker,b'''        const int modal = wm.GetTopmostModalDialog();
        if (wm.GetActiveWindow() == WINDOW_ADDON_BROWSER && modal == WINDOW_DIALOG_ADDON_INFO && power && !power->IsInScreenSaver())
        {
          auto* dialog=wm.GetWindow(modal);bool handled=false;
          if(dialog) for(const int id : {6,7,8,9,10,12,13,14})
          {
            auto* button=dynamic_cast<CGUIButtonControl*>(dialog->GetControl(id));
            if(button && button->OnInfinityAddonActionTouch(newEvent.touch.x,newEvent.touch.y,newEvent.touch.action==ACTION_TOUCH_LONGPRESS))
            {handled=true;break;}
          }
          if(handled)break;
        }
        if (wm.GetActiveWindow() == WINDOW_ADDON_BROWSER''')
    return out

import components98 as c
import os,copy
old_adapters=previous.old_adapters
module=previous.module
SOURCE97_MAP_SHA='022033b457321593ce57037b56a0e669e3f07b3139495950ccd4d3318837aaa2'

def bind(producer, parent, stage, source_commit):
    d, _, _ = previous.old_adapters()
    native = producer / 'kodi'
    checkpoint = producer / 'checkpoint-build'
    expected = json.loads((checkpoint / 'FOLD96-NATIVE-SOURCE-MAP.json').read_text())
    require(len(expected)==9404 and c.sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()) == SOURCE97_MAP_SHA, 'exact 2103397 native map required')
    for name,pin in expected.items():require(c.digest(native/name)==pin,'native baseline drift '+name)
    links = d.native_build_inventory(native, expected, Path(os.environ['DEPENDS']))
    original = c.read_parent(parent)
    final = c.components(original)
    require(c.ledger(original, final) == json.loads((c.HERE / 'MEMBER-DELTA.json').read_text()),
            'unreviewed component delta')
    for name, body in final.items():
        require((stage / name).read_bytes() == body, 'component stage mismatch ' + name)
    after = patches({p: (native / p).read_bytes() for p in PATHS}, original, final)
    after_map = dict(expected, **{p: c.sha(b) for p, b in after.items()})
    driver = d.module('targeted96_immutable_driver', producer / 'repairs/four-repair-20261018/native_ci.py')
    ordering = driver.parent.parent.parent.parent.parent.parent.parent
    compiler = Path(ordering.native_manifest(ordering.stable())).resolve()
    paths = [checkpoint / 'FOUR-REPAIR-INPUT-DELTA.json', compiler,
             checkpoint / 'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json']
    locked = json.loads((checkpoint / 'LOCKED-2103384-SOURCE-MAP.json').read_text())
    records = [json.loads(p.read_text()) for p in paths]
    require(len({p.resolve() for p in paths}) == 3 and
        dict(locked, **records[0]['after']) == expected and
        all(v['after'] == expected for v in records[1:]), 'complete compiler ledgers required')
    replacements = {native / p: body for p, body in after.items()}
    for path, record in zip(paths, records):
        value = copy.deepcopy(record)
        value['after'].update({p: after_map[p] for p in PATHS})
        value['changed'] = sorted(set(value.get('changed', [])) | PATHS)
        value['source_commit'] = source_commit
        value['consolidated_2103398_delta'] = sorted(PATHS)
        replacements[path] = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    backups = {path: path.read_bytes() for path in replacements}
    try:
        for path, body in replacements.items():
            path.write_bytes(body)
        require(d.native_build_inventory(native, after_map, Path(os.environ['DEPENDS'])) == links,
                'unrelated source or build link drift')
        proof = dict(source_commit=source_commit, parent_source_commit=c.COMMIT,
            original_source_count=9404, final_source_count=9404,
            protected_source_count=9404-len(PATHS),
            before={p: expected[p] for p in sorted(PATHS)},
            after={p: after_map[p] for p in sorted(PATHS)},
            all_other_sources_byte_identical=True, unchanged_build_links=links,
            essential_first_guards_unchanged=True, cobra_changed=False,
            physical_fold_verified=False, final_lock=False,
            option_b_eligibility_changed=True)
        for name, value in [('FOLD98-NATIVE-BINDING.json', proof),
                            ('FOLD98-NATIVE-SOURCE-MAP.json', after_map)]:
            (checkpoint / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
        return proof
    except BaseException:
        for path, body in backups.items():
            path.write_bytes(body)
        raise
