# Physical testing and forward recovery — no automatic installation

This document does not execute or authorize an automatic installation. Delivery must include the signed higher-version recovery artifact and successful static/host preservation, signature and authentication gates before offering the testing APK. Physical installation and recovery remain pending user control.

Before any later physical test, confirm the installed package/version on the phone. Candidate456 is intended for the original-signer `com.projectinfinity.kodi` at451–455; if the phone has an unexpected certificate or version456 or higher, stop rather than uninstall, downgrade or clear data. Verify the delivered APK SHA256 and original certificate fingerprint. Keep the protected signed451 recovery baseline and both new artifact checksums available.

If the user chooses to test the candidate:

1. Use an ordinary Android install-over update only. Do not uninstall, clear data, reset settings or grant new storage/network permissions. Verify the chooser and existing Cobra/Preview presentation remain unchanged.
2. On the Fold cover display, test first-tap selection, second-tap original activation and hold/context/Back on existing movie, show, season, episode, folder and Favorites items. Check default focus, changed selection, scroll/rebind, parent `..`, direct Close/Back/Power controls, modal ownership and ordinary remote/mouse input. Power should only open its existing menu; no shutdown behavior suite is selected.
3. Repeat touch checks unfolded, portrait/landscape and Light/Dark. Check actual hit positions and selection after fold/rotation/background return. Preserve every existing context owner; dismiss menus without executing data-changing actions during the touch check.
4. Verify Movies→existing Umbrella Movies, TV Shows→Umbrella TV Shows, Sports→verified installed SportHD, Favorites→native Favorites. Verify distinct indexed Library entries, native Browse Files, authorized Downloads playback and return. Existing permissions/denied-access handling remain in force.
5. Select a supported global media view; traverse provider/page/category, Back, refresh and reopening. Check fallback does not overwrite the saved preference. Check available poster/title/details and View Options close behavior. The full browser mockup remains incomplete.
6. Observe Search All and direct provider headings. The two known settings-related failures remain expected unresolved defects, not PASS. Retain privacy-safe diagnostics when available; do not expose queries, account data or media paths publicly.

Forward recovery457 restores the exact451 functional code/native engine, with higher Android/module/skin versions and necessary authenticated metadata. It is an in-place forward update, not installation of a lower version. It preserves existing databases, provider configuration and persisted user files. Installer checks, signature verification and downgrade defenses remain enabled.

Only attempt a later recovery update at an existing safe persistence/close point. Do not force-kill Kodi, bypass a failed checkpoint or treat an unknown pending write as durable. A recovery APK cannot restore unsaved in-memory data. If Kodi cannot reach a safe point, preserve diagnostics and stop rather than forcing installation/termination. Recovery of a hung process with unresolved durability obligations is not a proven guarantee.

After a user-controlled recovery update, verify the original451 browsing/playback and existing user data. Candidate-only module helpers may remain on disk: the restored authenticated import contract refuses them, and restored routes do not invoke them. No arbitrary file deletion is performed. Host tests cover signature, interrupted module writes, retry, retained-helper refusal and a disposable userdata sentinel; actual Fold installer/skin-generation behavior is NOT RUN until physically tested.
