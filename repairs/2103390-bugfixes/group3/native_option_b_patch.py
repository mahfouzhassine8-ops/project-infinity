#!/usr/bin/env python3
"""Group #3 ONLY: apply a guarded Movie/TV Home Option B native longpress.

REQUIRES the prior matched Infinity Rails Hold V2 native source already applied.
No global keymaps or app/Cobra code. This is a source overlay for rebuilding
native libkodi.so, NOT a binary patch, signed APK or an Android/Fold pass.

The original four add-on Rails IDs, fallback gesture translator and ordinary
taps are retained byte-for-byte. Fail closed on missing/duplicate anchors.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json

NATIVE_FILES = (
    "xbmc/input/InputManager.cpp",
    "xbmc/guilib/GUIBaseContainer.cpp",
    "xbmc/guilib/GUIBaseContainer.h",
)
GROUP3_ALLOWLIST = set(NATIVE_FILES)

# Guarded, separate member method. The existing OnInfinityRailLongPress method
# remains unchanged; media rails do not share helper keys or script destinations.
METHOD = r'''
bool CGUIBaseContainer::OnInfinityOptionBLongPress(float x, float y)
{
  // GROUP3_OPTION_B_V1: strict original Infinity Home media release panels.
  if (GetParentID() != WINDOW_HOME || (GetID() != 8101 && GetID() != 8102) ||
      !HasProcessed() || m_gestureActive || m_waitForScrollEnd)
    return false;
  for (const CGUIControl* owner = this; owner; owner = owner->GetParentControl())
    if (!owner->IsVisible() || owner->IsDisabled())
      return false;

  CPoint point(x, y);
  m_cachedTransform.InverseTransformPosition(point.x, point.y);
  if (!CanFocusFromPoint(point))
    return false;
  const int oldSelection = GetSelectedItem();
  if (!SelectItemFromPoint(point - CPoint(m_posX, m_posY)))
    return false;
  const int selected = GetSelectedItem();
  const auto restore = [this, oldSelection]() { SelectItem(oldSelection); return false; };
  if (selected < 0 || selected >= static_cast<int>(m_items.size()) ||
      !m_items[selected] || !m_items[selected]->IsFileItem())
    return restore();

  const auto item = std::static_pointer_cast<CFileItem>(m_items[selected]);
  const std::string path = item->GetPath();
  const std::string label = item->GetLabel();
  // Original 2103390 top release panels use Umbrella. Reject unrelated
  // dynamic media, short names, or giant data; never execute item-supplied text.
  if (path.compare(0, 31, "plugin://plugin.video.umbrella/") != 0 ||
      path.size() > 4096 || label.empty() || label.size() > 512)
    return restore();

  auto& windows = CServiceBroker::GetGUI()->GetWindowManager();
  if (windows.GetActiveWindow() != WINDOW_HOME ||
      windows.GetTopmostModalDialog() != WINDOW_INVALID)
    return restore();
  auto* home = windows.GetWindow(WINDOW_HOME);
  if (!home)
    return restore();

  // Focus the hit-tested actual poster so Kodi's normal provider Select/Info
  // will still use exactly this item after the dialog closes.
  CGUIMessage focus(GUI_MSG_SETFOCUS, WINDOW_HOME, GetID());
  home->OnMessage(focus);
  if (home->GetFocusedControlID() != GetID() || GetSelectedItem() != selected)
    return restore();

  // The sole command is literal. The untrusted title/URL never enter a
  // Kodi builtin command; place them in the already-existing Home property
  // table to be revalidated in Python before opening and after closing.
  const std::string input = std::to_string(GetID()) + "\n" +
      std::to_string(selected) + "\n" + path + "\n" + label;
  const std::string proof =
      UTILITY::CDigest::Calculate(UTILITY::CDigest::Type::SHA256, input);
  home->SetProperty("Infinity.HomeOptionB.PendingControl", std::to_string(GetID()));
  home->SetProperty("Infinity.HomeOptionB.PendingIndex", std::to_string(selected));
  home->SetProperty("Infinity.HomeOptionB.PendingPath", path);
  home->SetProperty("Infinity.HomeOptionB.PendingLabel", label);
  home->SetProperty("Infinity.HomeOptionB.PendingProof", proof);
  m_waitForScrollEnd = false;

  CServiceBroker::GetAppMessenger()->PostMsg(
      TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
      "RunScript(script.infinity.uirepair,option-b," + std::to_string(GetID()) +
          "," + std::to_string(selected) + "," + proof + ")");
  return true;
}
'''

DISPATCH = r'''            if (!handled)
            {
              // GROUP3_OPTION_B_V1: only the original Movie/TV release
              // containers, after the four existing add-on rail checks.
              // Other gesture and ordinary touch paths fall through unchanged.
              for (const int mediaID : {8101, 8102})
              {
                auto* rail = dynamic_cast<CGUIBaseContainer*>(home->GetControl(mediaID));
                if (rail && rail->OnInfinityOptionBLongPress(newEvent.touch.x, newEvent.touch.y))
                {
                  handled = true;
                  break;
                }
              }
            }
'''

CPP_METHOD_ANCHOR = "bool CGUIBaseContainer::OnInfinityRailLongPress(float x, float y)"
HEADER_ANCHOR = "  bool OnInfinityRailLongPress(float x, float y);"
RAILS_MARKER = "// INFINITY_RAIL_HOLD_V2"
RAILS_IDS = "for (const int railID : {9200, 8820, 8720, 19601})"
TAP_ANCHOR = "      if (newEvent.touch.action == ACTION_TOUCH_TAP)"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def replace_one(s: str, old: str, new: str, purpose: str) -> str:
    count = s.count(old)
    if count != 1:
        raise ValueError(f"{purpose}: expected one native preimage, found {count}")
    return s.replace(old, new, 1)


def patch_sources(originals: dict[str, bytes]) -> dict[str, bytes]:
    if set(originals) != GROUP3_ALLOWLIST:
        raise ValueError("Unexpected or missing Group #3 native file")
    raw = {p: b.decode("utf-8") for p, b in originals.items()}
    h = raw["xbmc/guilib/GUIBaseContainer.h"]
    c = raw["xbmc/guilib/GUIBaseContainer.cpp"]
    m = raw["xbmc/input/InputManager.cpp"]
    for marker in ("OnInfinityOptionBLongPress", "GROUP3_OPTION_B_V1"):
        if marker in h or marker in c or marker in m:
            raise ValueError("Option B native change already applied")
    if c.count(CPP_METHOD_ANCHOR) != 1 or h.count(HEADER_ANCHOR) != 1:
        raise ValueError("Original Rails native implementation is absent/ambiguous")
    if m.count(RAILS_MARKER) != 1 or m.count(RAILS_IDS) != 1 or m.count(TAP_ANCHOR) != 1:
        raise ValueError("Matched Infinity Rails Hold V2 native preimage required")
    h = replace_one(h, HEADER_ANCHOR,
                    HEADER_ANCHOR + "\n  bool OnInfinityOptionBLongPress(float x, float y);",
                    "new isolated method declaration")
    c = replace_one(c, CPP_METHOD_ANCHOR, METHOD + "\n" + CPP_METHOD_ANCHOR,
                    "new isolated top-release longpress")
    for include in ('#include "guilib/GUIWindow.h"', '#include "utils/Digest.h"'):
        if include not in c:
            c = replace_one(c, '#include "GUIMessage.h"',
                            '#include "GUIMessage.h"\n' + include,
                            "required verified native include")
    start = m.index(RAILS_MARKER)
    stop = m.index(TAP_ANCHOR, start)
    segment = m[start:stop]
    tail = "            if (handled)\n              break;"
    if segment.count(tail) != 1:
        raise ValueError("Existing Rails dispatch epilogue is not unique")
    segment = segment.replace(tail, DISPATCH + tail, 1)
    m = m[:start] + segment + m[stop:]
    for id in ("9200", "8820", "8720", "19601"):
        if id not in m:
            raise ValueError("Original add-on Rail ID disappeared")
    if m.count(RAILS_IDS) != 1 or m.count(TAP_ANCHOR) != 1:
        raise ValueError("Original native fallback input route was changed")
    return {p: text.encode("utf-8") for p, text in (
        ("xbmc/guilib/GUIBaseContainer.h", h),
        ("xbmc/guilib/GUIBaseContainer.cpp", c),
        ("xbmc/input/InputManager.cpp", m),
    )}


def apply(root: Path, *, expected_before: dict[str, str] | None = None) -> dict:
    root = Path(root)
    before = {p: (root / p).read_bytes() for p in NATIVE_FILES}
    if expected_before and {p: sha(b) for p, b in before.items()} != expected_before:
        raise ValueError("Refusing native source different from signed 2103390 reconstruction")
    after = patch_sources(before)  # refuse preimage mismatch BEFORE any writes
    for p, content in after.items():
        (root / p).write_bytes(content)
    return dict(
        changed=sorted(after),
        before={p: sha(b) for p, b in sorted(before.items())},
        after={p: sha(b) for p, b in sorted(after.items())},
        original_addon_rails_unchanged=True,
        original_other_input_fallback_unchanged=True,
        shared_native_cobra_paths_guarded=True,
        modified_cobra_files=[],
        rebuilt_libkodi=False,
        android_compiled=False,
        physical_fold_verified=False,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("reconstructed_native_source", type=Path)
    parser.add_argument("--expected-before-json", type=Path)
    args = parser.parse_args()
    expected = json.loads(args.expected_before_json.read_text()) if args.expected_before_json else None
    print(json.dumps(apply(args.reconstructed_native_source, expected_before=expected), indent=2))
