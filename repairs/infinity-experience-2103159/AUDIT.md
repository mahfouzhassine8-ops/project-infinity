# Infinity 2103159 — Experience Chooser ZIP Bridge RC1

## Scope

This candidate branches from the user-locked Cobra 2103158 baseline at
`fd2af59bab2edcaea6be9e5046720715e25e64e0`. The lock is never moved or edited.
The Android delta is intentionally limited to the startup `Splash` chooser plus
version metadata. Cobra Health Center, per-channel playback, recovery, EPG, all
five view renderers, diagnostics, native engine/assets and signer remain the exact
2103158 sources/payload unless a gate proves otherwise.

The reason an APK bridge is required once: the locked 2103158 startup chooser is
constructed inside `Splash.java.in`; the existing Cobra UI ZIP loader only feeds
`InfinityLiveActivity`. A ZIP alone cannot reach that screen. Bridge 1 makes
Splash optionally read one bounded visual JSON file that the existing Cobra UI
installer already stages safely. Future chooser copy/color/spacing changes can
therefore be ZIP-only as long as they remain inside this contract.

## Approved visual target

The user-approved reference is the dark cinematic Infinity/Cobra mockup created
in the current design session. The implementation recreates it with native
Android text, gradients and Canvas-drawn marks rather than stretching the mockup
bitmap over controls. This preserves crisp rendering, actual focus/click targets,
large-screen scaling and a functional settings gear.

Required copy in UI 1.4.0:
- `INFINITY` / `BEYOND ENTERTAINMENT`
- `HM` with `PERSONALIZED FOR YOU`
- `Choose Your Experience`
- Infinity: `YOUR HOME FOR MOVIES, SHOWS AND MORE`
- Cobra: `FOCUSED. FAST. POWERFUL.`
- footer: `INFINITY BY HASSINE MAHFOUZ` and `ONE APP • YOUR WORLD`

The themed screen contains no `2-IN-1`, no explanatory subtitle under the title,
and no `Live TV` wording on the Infinity card. No separate user identity data is
read; `HM` is a visual token in the installed package.

## ZIP contract

`Infinity-Cobra-UI-1.4.0-Experience.zip` is built from the exact locked matching
UI 1.3.9 SHA-256
`88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a`.
The existing `cobra-theme.json` and module bytes are preserved exactly. The
existing `cobra-ui.json` remains schema 1 / `cobra-live-only` and retains every
protected contract as `native`; only its package version advances to 1.4.0.
The one additional staged resource is
`resources/experience-chooser.json` with explicit scope
`infinity-experience-chooser` and `minimum_bridge: 1`.

This design intentionally lets locked 2103158 accept/store the 1.4.0 ZIP through
its existing Cobra UI updater without changing 2103158 behavior. After the 2103159
bridge APK is installed, Splash reads the already-staged adjunct on the next
chooser display. The ZIP never owns launch routing, remembered defaults, playback,
EPG, native renderer, rotation, Fold or background/resume behavior.

## Runtime hardening

Splash accepts only its app-specific external-files location, canonicalizes the
resource path, caps the JSON file at 64 KiB, performs a complete bounded read,
requires schema/scope/bridge compatibility, bounds dimensions and validates
colors/copy. Invalid, missing, oversized or future-schema data logs a bounded
warning and falls back to the exact pre-2103159 chooser method.

The old chooser body is preserved byte-for-byte under a fallback method. The
existing `startXBMC`, card settings, `launchInfinityExperience` and `onCreate`
methods are byte-protected. The themed view calls the same launch/settings owners
instead of duplicating behavior.

The theme is presentation-only. No arbitrary class/action names, URLs, paths,
intents, Java snippets or provider credentials are accepted from JSON.

## Responsive presentation

The themed root is scrollable for short displays and large text. Native vector
marks, title/copy, settings controls and cards scale with Android density. Normal
phone/Fold layouts retain the approved side-by-side cards; very narrow displays
stack them. Focus changes use bounded scale/elevation and border emphasis. The
background recreates the approved metallic-night glow and curved horizon using
Canvas gradients/arcs, so no low-resolution screenshot is used as an interactive
surface.

## Automated gates

Before push, host tests require the exact locked Splash hash, reject modified
preimages, prove launch/settings/startup methods remain byte-identical, verify the
fallback chooser, validate approved copy, and build 1.4.0 from exact 1.3.9 while
preserving untouched UI files. The parent 2103158 reconstruction also reruns its
policy and integrity stack.

CI then rebuilds/signs the Android shell using the locked native payload. It reruns
all 11 Android cases from locked 2103158 (4 navigation + 7 health/playback) and 6
new Splash cases: approved copy/HM, card settings and launch destinations,
malformed fallback, 320dp stacked layout, 960dp landscape layout, and oversized
file fallback. The tests render actual production views under Robolectric native
graphics; they do not claim physical GPU/Fold-panel acceptance.

Signed delivery is blocked unless all 17 Android tests have zero failures/errors/
skips, required screenshots exist, APK/signature/native/assets checks pass, and
the staged ZIP hash remains unchanged after testing.

## Device acceptance still required

Install the 2103159 APK over 2103158 without uninstalling or clearing data. Install
UI 1.4.0 through the existing Cobra UI update picker. Set the startup choice to
Ask every time if necessary, relaunch, and compare the real screen to the approved
mockup on the Fold inner display, cover display and landscape. Verify D-pad/touch
focus, both gear menus and both destinations. Then test malformed/rollback ZIP
behavior and confirm the rest of Cobra remains identical.

This RC is not a new lock or an official release until those physical checks and
the requested final adversarial audit are accepted.
