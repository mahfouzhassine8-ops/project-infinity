# Infinity 2103328 + skin 1.0.5.202 — Closing Infinity polish candidate

## Exact parents

- Android/APK parent: user-accepted Infinity **2103327 JobManager Close RC1**, GitHub run `37687616440`, source commit `2bb8f12f700ee69fe5d86629e6639bc0b1a0b79e`.
- Parent APK SHA-256: `02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5`.
- Parent packaged native SHA-256: `a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c`.
- Native source lineage remains `541fdbb25dae16d6e38d7814948a5a8ae54ad13e`; **no native rebuild or native byte change is authorized**.
- Skin parent: exact locked `skin.infinity.diggz 1.0.5.201`, artifact SHA-256 `c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5`.
- Skin rollback remains 1.0.5.201; APK rollback remains 2103327.

## Approved bite-for-bite behavior

On Android, tapping the existing **CLOSE KODI** row immediately changes only that row inside Infinity Power to:

- **CLOSING INFINITY…**
- **Please wait while your session is saved**
- **Saving → Services → Scripts → Cleanup**
- thin Infinity-cyan indeterminate/pulsing treatment that honors the existing reduced-motion policy.

At the same time the existing independent Android shutdown guard shows a quiet heads-up-capable notification:

- **Closing Infinity…**
- **Saving state and finishing cleanup**
- **Saving • Services • Scripts • Cleanup**
- indeterminate progress.

The in-skin state is the primary visual. The Android foreground notification is the independent safety net while Kodi's renderer may stop repainting during legitimate Python/native finalization.

## Android scope

Only `InfinityCloseGuardService.java.in` changes, plus ordinary version/BuildConfig compiler output. The existing guard lifetime, owner validation, `BIND_IMPORTANT` lease, 150-second safety ceiling, nonsticky behavior, cleanup evidence, and stop/unbind behavior are preserved exactly.

The channel uses a new ID because Android notification-channel importance is immutable after creation. It is HIGH importance to permit a heads-up presentation, but sound, vibration and lights are explicitly disabled. Samsung/Android remains authoritative for exact placement and whether a heads-up is displayed.

No force-stop, PID kill, `System.exit`, timeout shortening, native completion shortcut, new permission, database reset, provider change, Cobra change or playback change is introduced.

## Skin scope

Candidate skin **1.0.5.202** is built from the exact locked .201 ZIP. Only:
- `skin.infinity.diggz/unified/DialogButtonMenu.xml`
- `skin.infinity.diggz/addon.xml`

change. The normal pre-tap Close Kodi row retains its existing visual geometry. Force Close, every other power row, Home, drawer, player, providers, themes and all other skin files remain byte-identical to .201.

## Acceptance

This is not locked by CI. Install over the existing app without uninstalling or clearing data, install skin 1.0.5.202 over .201, then verify repeated normal closes on the Fold. Required behavior: immediate visual acknowledgment, legitimate save/cleanup still completes, real Kodi PID exits, notification clears automatically, reopen remains quick, and saved settings/resume/watch state survive.
