# Infinity / Infinity Preview label coverage

The Android application label remains `Infinity`. The original MAIN/LAUNCHER and
LEANBACK_LAUNCHER entry stays on the same Splash component with its original label
inheritance and icon. The existing video's VIEW filter is labeled `Infinity
Preview`; the single-video SEND filter on that same component has the same label.
The original audio/image filter retains its existing behavior. The internal
player has no exported filter, launcher entry or separate application identity.

Actual Android API37.1 PackageManager resolution returned exactly one matching
Infinity video handler. Its `ResolveInfo.loadLabel()` was `Infinity Preview`, and
its `ApplicationInfo.loadLabel()` was `Infinity`. The captured `handler-labels.png`
is the disposable source fixture displaying those real resolver values; it is
**not** a screenshot of MiXplorer or Samsung's chooser UI. File title, playback
pixels and current controls were also observed on the separate private player.

| Source or surface | Evidence and limit |
| --- | --- |
| Android package resolver | One video handler; exact filter and application labels verified on Android API37.1. |
| Synthetic Android source/provider | Actual granted content VIEW, video SEND, rapid replacements, HTTP and denied/invalid sources exercised. Uses the same exported Splash gateway. |
| MiXplorer | Source-specific chooser presentation and its MIME/grant behavior require physical app testing. No MiXplorer-specific code exists. |
| Samsung My Files | Samsung/One UI chooser presentation requires the user's physical Fold. |
| Android Files / Files by Google | Actual app UI was not exercised; central resolver and ContentResolver grant contracts were exercised. |
| Google Drive | Account-dependent external opening, temporary grants and the app's chooser UI were not exercised. A Drive webpage is not promised to be a direct stream. |
| Downloads / browsers | Direct HTTP media and Android intent handling were exercised through the fixture; each actual app's Open with UI remains unverified. |
| Other compatible applications | Same package metadata and gateway apply; app-specific UI is not claimed to have been tested. |

A selector may show the app label alone, use the intent-filter label as its main
row, omit a subtitle, or render the raw Activity class name. Infinity cannot force
its exact two-line presentation in a selector that ignores Android's handler
label. Changing Splash's global Activity label would also change label inheritance
for launchers that read ActivityInfo directly; it is therefore kept intact. No
Activity alias, second public video handler, raw `PreviewActivity` display label,
extra launcher icon or application-specific substitution is introduced.

Physical acceptance should confirm `Infinity` / `Infinity Preview` in each
available source that honors Android handler metadata, and record any selector
that chooses a different layout. Normal launcher / chooser operation and the
protected Cobra/Kodi components remain covered by exact preservation checks.
