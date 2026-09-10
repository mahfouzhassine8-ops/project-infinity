#!/usr/bin/env python3
# Apply the cumulative Infinity Responsive Bridge v5 after audited bridge v4.
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "patches/infinity-responsive-v5/contract.json"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected 1 match, got {count}")
    return text.replace(old, new, 1)

def transform_bridge(text: str) -> str:
    text = replace_once(text, "static final int VERSION = 4;", "static final int VERSION = 5;", "bridge version")
    text = replace_once(
        text,
        "  private boolean supported;\n",
        '''  private boolean supported;

  // Packed v5 window-mode extension. Bits 0..3 retain v4 PiP/multi/managed/TV.
  private static final int DEVICE_SHIFT = 4;      // 3 bits
  private static final int LAYOUT_SHIFT = 7;      // 2 bits
  private static final int WIDTH_DP_SHIFT = 9;    // 11 bits
  private static final int HEIGHT_DP_SHIFT = 20;  // 11 bits
  private static final int FOLD_HINT = 0x80000000;
  private static final int DEVICE_UNKNOWN = 0;
  private static final int DEVICE_COVER = 1;
  private static final int DEVICE_INNER = 2;
  private static final int DEVICE_PHONE = 3;
  private static final int DEVICE_TABLET = 4;
  private static final int DEVICE_TV = 5;
  private static final int LAYOUT_UNKNOWN = 0;
  private static final int LAYOUT_COMPACT = 1;
  private static final int LAYOUT_MEDIUM = 2;
  private static final int LAYOUT_EXPANDED = 3;
''',
        "bridge constants",
    )
    old = '''    final boolean pip = Build.VERSION.SDK_INT >= 26 && activity.isInPictureInPictureMode();
    final boolean multi = Build.VERSION.SDK_INT >= 24 && activity.isInMultiWindowMode();
    final boolean television = activity.getPackageManager().hasSystemFeature(PackageManager.FEATURE_LEANBACK);
    final int mode = (pip ? 1 : 0) | (multi ? 2 : 0) | (television ? 8 : 0);
    // Preserve Kodi's TV resolution/GUI-limit policy outside PiP and multi-window.
    final boolean managed = pip || multi || !television;
    activity.infinityPublishWindowSnapshot(view.getWidth(), view.getHeight(), theme, mode, managed);
    activity._infinitySyncDisplayState();
    Log.d("InfinityController", "Published window/theme: " + java.util.Arrays.toString(activity._infinityGetState()));
'''
    new = '''    final boolean pip = Build.VERSION.SDK_INT >= 26 && activity.isInPictureInPictureMode();
    final boolean multi = Build.VERSION.SDK_INT >= 24 && activity.isInMultiWindowMode();
    final boolean television = activity.getPackageManager().hasSystemFeature(PackageManager.FEATURE_LEANBACK);
    final int width = Math.max(0, view.getWidth());
    final int height = Math.max(0, view.getHeight());
    final float density = Math.max(0.1f, view.getResources().getDisplayMetrics().density);
    final int widthDp = Math.min(2047, width > 0 ? Math.round(width / density) : 0);
    final int heightDp = Math.min(2047, height > 0 ? Math.round(height / density) : 0);
    boolean foldHint = false;
    try {
      foldHint = activity.getPackageManager().hasSystemFeature("android.hardware.sensor.hinge_angle");
    } catch (RuntimeException ignored) {
    }
    final float ratio = widthDp > 0 && heightDp > 0 ?
        Math.max(widthDp, heightDp) / (float)Math.min(widthDp, heightDp) : 99f;
    final int layout = widthDp <= 0 ? LAYOUT_UNKNOWN :
        widthDp < 600 ? LAYOUT_COMPACT : widthDp < 840 ? LAYOUT_MEDIUM : LAYOUT_EXPANDED;
    final int device;
    if (television) device = DEVICE_TV;
    else if ((foldHint || ratio <= 1.60f) && widthDp >= 600) device = DEVICE_INNER;
    else if (foldHint && widthDp > 0) device = DEVICE_COVER;
    else if (widthDp >= 600) device = DEVICE_TABLET;
    else if (widthDp > 0) device = DEVICE_PHONE;
    else device = DEVICE_UNKNOWN;
    final int mode = (pip ? 1 : 0) | (multi ? 2 : 0) | (television ? 8 : 0) |
        (device << DEVICE_SHIFT) | (layout << LAYOUT_SHIFT) |
        (widthDp << WIDTH_DP_SHIFT) | (heightDp << HEIGHT_DP_SHIFT) |
        (foldHint ? FOLD_HINT : 0);
    // Preserve Kodi's TV resolution/GUI-limit policy outside PiP and multi-window.
    final boolean managed = pip || multi || !television;
    activity.infinityPublishWindowSnapshot(width, height, theme, mode, managed);
    activity._infinitySyncDisplayState();
    Log.d("InfinityController", "Published responsive v5: " + widthDp + "x" + heightDp +
        "dp device=" + device + " layout=" + layout +
        " state=" + java.util.Arrays.toString(activity._infinityGetState()));
'''
    text = replace_once(text, old, new, "responsive Java publication")
    text = replace_once(text, "Source-built Infinity Controller v4 attached",
                        "Source-built Infinity Controller v5 attached", "bridge log")
    return text

def transform_state(text: str) -> str:
    text = replace_once(text, "static constexpr int VERSION = 4;",
                        "static constexpr int VERSION = 5;", "native version")
    return text.replace("// ABI v4:", "// ABI v5:")

def transform_window(text: str) -> str:
    old = '''      home->SetProperty("Infinity.SystemTheme", theme == 2 ? "dark" : theme == 1 ? "light" : "unknown");
      home->SetProperty("Infinity.DeviceMode", (mode & 8) ? "tv" : "mobile");
      home->SetProperty("Infinity.BridgeVersion", CInfinityBridgeState::VERSION);
      home->SetProperty("Infinity.ThemeRevision", static_cast<int64_t>(themeRevision));
'''
    new = '''      const uint32_t packed = static_cast<uint32_t>(mode);
      const int deviceCode = static_cast<int>((packed >> 4) & 0x7u);
      const int layoutCode = static_cast<int>((packed >> 7) & 0x3u);
      const int widthDp = static_cast<int>((packed >> 9) & 0x7ffu);
      const int heightDp = static_cast<int>((packed >> 20) & 0x7ffu);
      const char* device = deviceCode == 1 ? "cover/front" :
                           deviceCode == 2 ? "inner/large" :
                           deviceCode == 3 ? "phone" :
                           deviceCode == 4 ? "tablet" :
                           deviceCode == 5 ? "tv" : "unknown";
      const char* layout = layoutCode == 1 ? "compact" :
                           layoutCode == 2 ? "medium" :
                           layoutCode == 3 ? "expanded" : "unknown";
      const char* orientation = widthDp <= 0 || heightDp <= 0 ? "unknown" :
                                widthDp > heightDp ? "landscape" :
                                heightDp > widthDp ? "portrait" : "square";
      const char* touch = layoutCode == 1 ? "compact" :
                          layoutCode == 2 ? "normal" :
                          layoutCode == 3 ? "large-display" : "unknown";

      // Raw Android/native facts are separate from effective skin state.
      // NativeDisplayRevision is the commit marker and is written after the fact set.
      home->SetProperty("Infinity.NativeReady", "false");
      home->SetProperty("Infinity.NativeSystemTheme", theme == 2 ? "dark" : theme == 1 ? "light" : "unknown");
      home->SetProperty("Infinity.NativeDeviceMode", device);
      home->SetProperty("Infinity.NativeLayout", layout);
      home->SetProperty("Infinity.NativeOrientation", orientation);
      home->SetProperty("Infinity.NativeTouchClass", touch);
      home->SetProperty("Infinity.NativeWidthDp", static_cast<int64_t>(widthDp));
      home->SetProperty("Infinity.NativeHeightDp", static_cast<int64_t>(heightDp));
      home->SetProperty("Infinity.NativePiP", (packed & 1u) ? "true" : "false");
      home->SetProperty("Infinity.NativeMultiWindow", (packed & 2u) ? "true" : "false");
      home->SetProperty("Infinity.NativeManagedGeometry", (packed & 4u) ? "true" : "false");
      home->SetProperty("Infinity.NativeFoldHint", (packed & 0x80000000u) ? "true" : "false");
      home->SetProperty("Infinity.BridgeVersion", CInfinityBridgeState::VERSION);
      home->SetProperty("Infinity.NativeDisplayRevision", static_cast<int64_t>(themeRevision));
      home->SetProperty("Infinity.NativeReady", widthDp > 0 && heightDp > 0 ? "true" : "false");
'''
    text = replace_once(text, old, new, "native responsive properties")
    text = replace_once(text, "Infinity theme fact applied: mode={} revision={} (no geometry reset)",
                        "Infinity native fact applied: theme={} revision={} (responsive v5)",
                        "native log")
    return text

TRANSFORMS = {
    "tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in": transform_bridge,
    "xbmc/platform/android/activity/InfinityBridgeState.h": transform_state,
    "xbmc/windowing/android/WinSystemAndroid.cpp": transform_window,
}

def verify(source: Path) -> None:
    checks = {
        "tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in": [
            "static final int VERSION = 5;", "WIDTH_DP_SHIFT = 9",
            "android.hardware.sensor.hinge_angle", "Published responsive v5",
        ],
        "xbmc/platform/android/activity/InfinityBridgeState.h": [
            "static constexpr int VERSION = 5;",
        ],
        "xbmc/windowing/android/WinSystemAndroid.cpp": [
            "Infinity.NativeDeviceMode", "Infinity.NativeWidthDp",
            "Infinity.NativeDisplayRevision", "Infinity.NativeSystemTheme",
        ],
    }
    for rel, needles in checks.items():
        text = (source / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                raise ValueError(f"missing {needle!r} in {rel}")
    win = (source / "xbmc/windowing/android/WinSystemAndroid.cpp").read_text(encoding="utf-8")
    if '(mode & 8) ? "tv" : "mobile"' in win:
        raise ValueError("legacy generic mobile classifier survived")
    print("PASS: Infinity Responsive Bridge v5 source contract verified.")

def apply(source: Path) -> None:
    source = source.resolve()
    cfg = load_contract()
    if cfg["base_bridge_version"] != 4 or cfg["bridge_version"] != 5:
        raise ValueError("unexpected v5 contract version")
    current = {rel: digest(source / rel) for rel in TRANSFORMS}
    expected = cfg["preimage_files"]
    if all(current[rel] == expected.get(rel) for rel in TRANSFORMS):
        for rel, fn in TRANSFORMS.items():
            path = source / rel
            path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")
    else:
        verify(source)
        print("Source already appears to contain v5; exact v4 preimage check skipped.")
        return
    verify(source)
    print("Applied Infinity Responsive Bridge v5 cumulatively after audited v4.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["source", "verify"])
    p.add_argument("--source", type=Path, required=True)
    a = p.parse_args()
    (apply if a.command == "source" else verify)(a.source)

if __name__ == "__main__":
    main()
