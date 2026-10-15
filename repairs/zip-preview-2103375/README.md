# Native ZIP preview hook — isolated 2103375

Parent: locked Cobra 2103374, build `9c3af2e9271402486c4c998efc62b5d08b872f29`, lock `d95ca4956b79e7f87923c6644ff039d058c1ab45`.

The exact parent APK hash is `160adfccc775f83c640354778e54f6f33164084413401f9c348ebe9ea41fb3e4`; native `libkodi.so` hash is `5d42d0d8ef6a90a5678fd7a24cc4e3b01e2375c213c590a92c178d7a34cc1113`.

Kodi's shares-based Install from ZIP picker owns the actual selected file and returns its confirmation to `CAddonInstaller::InstallFromZip`. The upstream 21.3 picker has no file preview callback on list context actions. A skin script alone must not guess a pressed filename, replace the installer, or perform its own installation. The hook publishes the selected native item into transient window properties, launches one fixed trusted skin script, and accepts a generation ticket only for the same still-selected ZIP. Source-root actions and ordinary selection/OK behavior keep their original handling.

The bridge is opt-in via `Infinity.FilePreview.OptIn=v1` in the new skin File Browser. With older skins it remains dormant. It applies only to the native ZIP-install heading/mask, never generic browsing, provider source selection, normal playback, PVR, save-state or shutdown. Preview control 9410 opens metadata; virtual confirmation message 9411 returns through the original browse confirmation. No archive filename/metadata is interpolated into a command. No archive inspection happens on the native GUI thread.

Native delta: two existing files (`GUIDialogFileBrowser.cpp/.h`) and one small production contract header. `native-delta.json` fixes exact preimages and outputs. Every 9,390 parent input is reconstructed and checked by the unchanged original lineage recipe and tests before this delta is applied. The unchanged compiler recipe receives a strict extended manifest in scratch; original manifests, tests and package sources are not edited. The exact 119 previously unresolved source preimages are retained in build evidence.

The final APK must retain all Java/DEX, assets, resources and the other 46 native libraries byte-for-byte from 2103374. It requires a new version and the same permanent signer. Skin 209 is delivered separately. Physical Fold acceptance and production promotion remain pending; no lock is authorized by this implementation handoff.
