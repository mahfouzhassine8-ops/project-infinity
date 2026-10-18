"""Opt-in UI gestures only. No player, directory callback, or persistence edits."""
from pathlib import Path
import hashlib

FILES = ('xbmc/input/InputManager.cpp', 'xbmc/guilib/GUIBaseContainer.cpp',
         'xbmc/guilib/GUIBaseContainer.h')

METHOD = r'''
bool CGUIBaseContainer::OnInfinityUiTouch(float x, float y, bool hold)
{
  const bool resume = GetParentID() == WINDOW_HOME && (GetID() == 8830 || GetID() == 8831);
  const bool browse = GetParentID() == WINDOW_HOME + 1193 && GetID() == 50;
  auto* window = CServiceBroker::GetGUI()->GetWindowManager().GetWindow(GetParentID());
  const bool popup = window && window->GetProperty("Infinity.UI.Popup").asString() == "1" && GetID() == 50;
  if ((!resume && !browse && !popup) || (resume && !hold) || !HasProcessed() || m_gestureActive)
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
  {
    SelectItem(previous);
    return false;
  }
  const auto item = m_items[selected];
  const std::string kind = item->GetProperty("Infinity.UI.Kind").asString();
  const std::string token = item->GetProperty("Infinity.UI.Token").asString();
  const bool safe = !token.empty() && token.size() <= 200 &&
      token.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-") == std::string::npos;
  if (item->GetProperty("Infinity.UI.Version").asString() != "1" || !safe ||
      (resume && kind != "resume") || (browse && kind != "addon") || (popup && kind != "action"))
  {
    SelectItem(previous);
    return false;
  }
  m_waitForScrollEnd = false;
  CGUIControl::OnMouseOver(point); // focus the actual transformed container, without activation
  if (hold)
  {
    m_infinityUiTapKey = token;
    if (!popup)
    {
      // Coordinates are in the actual skin viewport after its cached inverse
      // transform, including the current Fold layout and container scroll.
      window->SetProperty("Infinity.UI.Anchor.X", std::to_string(point.x));
      window->SetProperty("Infinity.UI.Anchor.Y", std::to_string(point.y));
      window->SetProperty("Infinity.UI.Anchor.Token", token);
      OnInfinityUiContextMenu();
    }
    return true;
  }
  // ACTION_TOUCH_TAP is intercepted BEFORE Kodi synthesizes MouseMove. Merely
  // having default/hover focus is therefore never mistaken for the first tap.
  const bool activate = m_infinityUiTapKey == token && previous == selected;
  m_infinityUiTapKey = token;
  if (activate)
  {
    m_infinityUiTapKey.clear();
    OnClick(ACTION_SELECT_ITEM); // one original dispatch; D-pad remains unchanged
  }
  return true;
}

bool CGUIBaseContainer::OnInfinityUiContextMenu()
{
  const bool resume = GetParentID() == WINDOW_HOME && (GetID() == 8830 || GetID() == 8831);
  const bool browse = GetParentID() == WINDOW_HOME + 1193 && GetID() == 50;
  if (!resume && !browse)
    return false;
  const int selected = GetSelectedItem();
  if (selected < 0 || selected >= static_cast<int>(m_items.size()))
    return false;
  const auto item = m_items[selected];
  const std::string token = item->GetProperty("Infinity.UI.Token").asString();
  const std::string kind = item->GetProperty("Infinity.UI.Kind").asString();
  if (item->GetProperty("Infinity.UI.Version").asString() != "1" ||
      token.empty() || token.size() > 200 ||
      token.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-") != std::string::npos ||
      (resume && (kind != "resume" || token.size() != 64 ||
                  token.find_first_not_of("abcdef0123456789") != std::string::npos)) ||
      (browse && (kind != "addon" || token != item->GetProperty("Addon.ID").asString())))
    return false;
  CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
      "RunScript(script.infinity.uirepair," + kind + "," + token + ")");
  return true;
}

'''

DISPATCH = r'''
      // INFINITY_UI_TOUCH_V1: original content opts in explicitly. This owns
      // only actual one-finger taps/holds, never physical mouse or D-pad input.
      if ((newEvent.touch.action == ACTION_TOUCH_TAP || newEvent.touch.action == ACTION_TOUCH_LONGPRESS) &&
          newEvent.touch.pointers == 1 &&
          CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") == "skin.infinity.diggz")
      {
        auto& windows = CServiceBroker::GetGUI()->GetWindowManager();
        const auto power = CServiceBroker::GetAppComponents().GetComponent<CApplicationPowerHandling>();
        const int modal = windows.GetTopmostModalDialog();
        const int active = modal == WINDOW_INVALID ? windows.GetActiveWindow() : modal;
        auto* owner = windows.GetWindow(active);
        if (owner && power && !power->IsInScreenSaver() &&
            (modal == WINDOW_INVALID || owner->GetProperty("Infinity.UI.Popup").asString() == "1"))
        {
          bool handled = false;
          for (const int id : {8830, 8831, 50})
          {
            auto* control = dynamic_cast<CGUIBaseContainer*>(owner->GetControl(id));
            if (control && control->OnInfinityUiTouch(newEvent.touch.x, newEvent.touch.y,
                                                    newEvent.touch.action == ACTION_TOUCH_LONGPRESS))
            {
              handled = true;
              break;
            }
          }
          if (handled)
            break;
        }
      }
'''

INFO = r'''
    // Plugin-projected Video Sources keep their installed add-on identity.
    // Build Kodi's real add-on info item; never open an uninitialised dialog.
    if (GetParentID() == WINDOW_HOME + 1193 && GetID() == 50)
    {
      const int selected = GetSelectedItem();
      if (selected >= 0 && selected < static_cast<int>(m_items.size()))
      {
        const auto item = m_items[selected];
        const std::string id = item->GetProperty("Addon.ID").asString();
        if (item->GetProperty("Infinity.UI.Version").asString() == "1" &&
            item->GetProperty("Infinity.UI.Kind").asString() == "addon" &&
            item->GetProperty("Infinity.UI.Token").asString() == id)
        {
          ADDON::AddonPtr addon;
          if (CServiceBroker::GetAddonMgr().GetAddon(id, addon, ADDON::OnlyEnabled::CHOICE_YES))
            return CGUIDialogAddonInfo::ShowForItem(std::make_shared<CFileItem>(addon));
          return true;
        }
      }
    }
'''

def once(s, old, new):
    if s.count(old) != 1:
        raise ValueError('Unexpected protected source anchor: ' + old[:90])
    return s.replace(old, new, 1)

def apply(root):
    root = Path(root)
    before, after = {}, {}
    for name in FILES:
        path = root / name
        raw = path.read_bytes()
        before[name] = hashlib.sha256(raw).hexdigest()
        s = raw.decode()
        if name.endswith('InputManager.cpp'):
            assert 'INFINITY_BROWSE_HOLD_V1' in s and 'INFINITY_RAIL_HOLD_V2' in s
            s = once(s, '      if (newEvent.touch.action == ACTION_TOUCH_TAP)',
                     DISPATCH + '\n      if (newEvent.touch.action == ACTION_TOUCH_TAP)')
        elif name.endswith('.h'):
            s = once(s, '  bool PrepareInfinityBrowseLongPress(float x, float y);',
                     '  bool PrepareInfinityBrowseLongPress(float x, float y);\n'
                     '  bool OnInfinityUiTouch(float x, float y, bool hold);\n'
                     '  bool OnInfinityUiContextMenu();\n'
                     '  std::string m_infinityUiTapKey;')
        else:
            s = once(s, '#include "GUIBaseContainer.h"',
                     '#include "GUIBaseContainer.h"\n#include "addons/AddonManager.h"\n'
                     '#include "addons/gui/GUIDialogAddonInfo.h"\n'
                     '#include "guilib/GUIComponent.h"\n#include "guilib/GUIWindow.h"\n'
                     '#include "guilib/GUIWindowManager.h"')
            s = once(s, '  case ACTION_SHOW_INFO:\n', '  case ACTION_SHOW_INFO:\n' + INFO)
            s = once(s, 'bool CGUIBaseContainer::OnMouseOver(const CPoint &point)',
                     METHOD + 'bool CGUIBaseContainer::OnMouseOver(const CPoint &point)')
            s = once(s, 'bool CGUIBaseContainer::OnContextMenu()\n{',
                     'bool CGUIBaseContainer::OnContextMenu()\n{\n  if (OnInfinityUiContextMenu())\n    return true;')
            s = once(s, '  else if (event.m_id == ACTION_GESTURE_BEGIN)\n  {',
                     '  else if (event.m_id == ACTION_GESTURE_BEGIN)\n  {\n    m_infinityUiTapKey.clear();')
            # A focus change invalidates the control too. Do not erase the
            # first tap on that ordinary no-op layout update. Clear only once
            # CalculateLayout has established a genuine size/template change.
            s = once(s, '  // ensure that the scroll offset is a multiple of our size\n',
                     '  m_infinityUiTapKey.clear();\n'
                     '  // ensure that the scroll offset is a multiple of our size\n')
            s = once(s, 'void CGUIBaseContainer::Reset()\n{',
                     'void CGUIBaseContainer::Reset()\n{\n  m_infinityUiTapKey.clear();')
        path.write_text(s)
        after[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(changed=list(FILES), before=before, after=after,
                scope='opt-in Home Continue, Video Sources, and item popup touch/context dispatch',
                native_player_changed=False, shutdown_changed=False, crash_fix=False,
                physical_fold_verified=False)
