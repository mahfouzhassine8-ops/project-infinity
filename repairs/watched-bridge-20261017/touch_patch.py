"""Preselect the touched All Add-ons tile, then retain the one native right-click."""
from pathlib import Path
import hashlib

FILES = ("xbmc/input/InputManager.cpp", "xbmc/guilib/GUIBaseContainer.cpp", "xbmc/guilib/GUIBaseContainer.h")
METHOD = r'''
bool CGUIBaseContainer::PrepareInfinityBrowseLongPress(float x, float y)
{
  if (GetParentID() != WINDOW_HOME + 1193 || GetID() != 50 ||
      !HasProcessed() || m_gestureActive)
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
  m_waitForScrollEnd = false;
  // Do not click, launch, post a command or consume the input. The original
  // coordinate-bearing right-click now sees the same selected tile and opens
  // its native/provider-owned context menu exactly once.
  return true;
}

'''

DISPATCH = r'''
      #if defined(TARGET_ANDROID)
      // INFINITY_BROWSE_HOLD_V1: only an actual translated touch RightClick,
      // in the processed All Add-ons grid; never remap ordinary mouse input.
      if (newEvent.touch.action == ACTION_TOUCH_LONGPRESS && newEvent.touch.pointers == 1 &&
          actionId == ACTION_MOUSE_RIGHT_CLICK)
      {
        auto& windows = CServiceBroker::GetGUI()->GetWindowManager();
        const auto appPower = CServiceBroker::GetAppComponents().GetComponent<CApplicationPowerHandling>();
        if (appPower && !appPower->IsInScreenSaver() &&
            windows.GetActiveWindow() == WINDOW_HOME + 1193 &&
            windows.GetTopmostModalDialog() == WINDOW_INVALID &&
            CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") ==
                "skin.infinity.diggz")
        {
          auto* home = windows.GetWindow(WINDOW_HOME);
          const std::string path = home ? home->GetProperty("Infinity.BrowsePath").asString() : "";
          if (path == "addons://sources/video" || path == "addons://sources/video/")
          {
            auto* window = windows.GetWindow(WINDOW_HOME + 1193);
            auto* grid = window ? dynamic_cast<CGUIBaseContainer*>(window->GetControl(50)) : nullptr;
            if (grid)
              grid->PrepareInfinityBrowseLongPress(newEvent.touch.x, newEvent.touch.y);
          }
        }
      }
      #endif
'''


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unexpected All Add-ons input source: " + old[:90])
    return text.replace(old, new, 1)


def apply(root):
    root = Path(root)
    before, after = {}, {}
    for name in FILES:
        path = root / name
        data = path.read_bytes(); text = data.decode()
        before[name] = hashlib.sha256(data).hexdigest()
        if name.endswith("InputManager.cpp"):
            if "INFINITY_RAIL_HOLD_V2" not in text:
                raise ValueError("Approved Home rail hold is missing")
            text = once(text, '      if (actionId <= 0)\n        return false;',
                        '      if (actionId <= 0)\n        return false;\n' + DISPATCH)
        elif name.endswith(".h"):
            text = once(text, '  bool OnInfinityRailLongPress(float x, float y);',
                        '  bool OnInfinityRailLongPress(float x, float y);\n  bool PrepareInfinityBrowseLongPress(float x, float y);')
        else:
            text = once(text, 'bool CGUIBaseContainer::OnMouseOver(const CPoint &point)',
                        METHOD + 'bool CGUIBaseContainer::OnMouseOver(const CPoint &point)')
        path.write_text(text)
        after[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(before=before, after=after, changed=list(FILES),
                scope="Translated single-finger Android-style touch RightClick in Infinity custom 1193/50 with Video Sources content",
                original_context_dispatch_changed=False, provider_menus_changed=False, keymaps_changed=False,
                original_home_rail_method_changed=False, physical_fold_verified=False)
