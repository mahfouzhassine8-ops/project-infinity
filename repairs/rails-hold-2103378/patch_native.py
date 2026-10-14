#!/usr/bin/env python3
"""Opt-in, coordinate-preserving Home rail hold; no keymap or APK payload edits."""
import hashlib
import json
from pathlib import Path

METHOD = r'''
bool CGUIBaseContainer::OnInfinityRailLongPress(float x, float y)
{
  // Use the actual rendered transform (window scale, nested origins, animations).
  // A stale/hidden view must never win merely because it has the same row data.
  if (GetParentID() != WINDOW_HOME || !HasProcessed() || m_gestureActive ||
      (GetID() != 9200 && GetID() != 8820 && GetID() != 8720 && GetID() != 19601))
    return false;
  for (const CGUIControl* owner = this; owner; owner = owner->GetParentControl())
    if (!owner->IsVisible() || owner->IsDisabled())
      return false;
  CPoint point(x, y);
  m_cachedTransform.InverseTransformPosition(point.x, point.y);
  if (!CanFocusFromPoint(point))
    return false;
  const int previous = GetSelectedItem();
  if (!SelectItemFromPoint(point - CPoint(m_posX, m_posY)))
    return false;
  const int selected = GetSelectedItem();
  if (selected < 0 || selected >= static_cast<int>(m_items.size()))
    return false;
  const auto item = m_items[selected];
  const std::string section = item->GetProperty("Infinity.Rails.Section").asString();
  const std::string key = item->GetProperty("Infinity.Rails.Key").asString();
  const std::string addon = item->GetProperty("Addon.ID").asString();
  // Fixed command plus strict token grammar: never execute an arbitrary item property.
  const auto safe = [](const std::string& value) {
    return !value.empty() && value.size() <= 200 &&
      value.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-") == std::string::npos;
  };
  const bool builtin = key.size() == 18 && key.compare(0, 2, "b:") == 0 &&
      key.find_first_not_of("0123456789abcdef", 2) == std::string::npos;
  const bool custom = key.compare(0, 2, "c:") == 0 && safe(key.substr(2)) &&
      key.substr(2) == addon;
  if (item->GetProperty("Infinity.Rails.HoldVersion").asString() != "1" ||
      item->GetProperty("Infinity.Rails.Item").asString() != "true" ||
      (section != "movies" && section != "tvshows") ||
      !safe(addon) || (!builtin && !custom))
  {
    SelectItem(previous);
    return false;
  }
  m_waitForScrollEnd = false;
  CLog::Log(LOGINFO, "Infinity Rails hold: control={} section={} key={} addon={} previous={} selected={}",
            GetID(), section, key, addon, previous, selected);
  CServiceBroker::GetAppMessenger()->PostMsg(
      TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
      "RunScript(script.infinity.rails,options," + section + "," + key + "," + addon + ")");
  return true;
}

'''

DISPATCH = '''
      // INFINITY_RAIL_HOLD_V1: preserve raw coordinates before a global add-on
      // keymap can replace this hold with a coordinate-free RunScript action.
      if (newEvent.touch.action == ACTION_TOUCH_LONGPRESS && newEvent.touch.pointers == 1)
      {
        auto& windows = CServiceBroker::GetGUI()->GetWindowManager();
        if (windows.GetActiveWindow() == WINDOW_HOME &&
            windows.GetTopmostModalDialog() == WINDOW_INVALID &&
            CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") ==
                "skin.infinity.diggz")
        {
          auto* home = windows.GetWindow(WINDOW_HOME);
          auto* rail = home ? dynamic_cast<CGUIBaseContainer*>(home->GetFocusedControl()) : nullptr;
          if (rail && rail->OnInfinityRailLongPress(newEvent.touch.x, newEvent.touch.y))
            break;
        }
      }
'''

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError('Unexpected native source anchor: '+old[:100])
    return text.replace(old, new, 1)

def apply(root):
    root = Path(root)
    before, after = {}, {}
    paths = ['xbmc/input/InputManager.cpp', 'xbmc/guilib/GUIBaseContainer.cpp',
             'xbmc/guilib/GUIBaseContainer.h']
    for name in paths:
        path = root/name
        raw = path.read_bytes()
        before[name] = hashlib.sha256(raw).hexdigest()
        text = raw.decode()
        if name.endswith('InputManager.cpp'):
            text = replace_once(text, '#include "guilib/GUIControl.h"',
                                '#include "guilib/GUIControl.h"\n#include "guilib/GUIBaseContainer.h"')
            text = replace_once(text, '      if (newEvent.touch.action == ACTION_TOUCH_TAP)',
                                DISPATCH+'      if (newEvent.touch.action == ACTION_TOUCH_TAP)')
        elif name.endswith('.h'):
            text = replace_once(text, '  bool OnMouseOver(const CPoint &point) override;',
                                '  bool OnMouseOver(const CPoint &point) override;\n'
                                '  bool OnInfinityRailLongPress(float x, float y);')
        else:
            text = replace_once(text, '#include "GUIMessage.h"',
                                '#include "GUIMessage.h"\n#include "WindowIDs.h"\n'
                                '#include "messaging/ApplicationMessenger.h"')
            text = replace_once(text, 'bool CGUIBaseContainer::OnMouseOver(const CPoint &point)',
                                METHOD+'bool CGUIBaseContainer::OnMouseOver(const CPoint &point)')
        path.write_text(text)
        after[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(before=before, after=after, changed=paths,
                keymaps_changed=False, ordinary_click_branch_changed=False,
                protected_shutdown_code_changed=False, physical_fold_accepted=False)

if __name__ == '__main__':
    import sys
    print(json.dumps(apply(sys.argv[1]), indent=2))
