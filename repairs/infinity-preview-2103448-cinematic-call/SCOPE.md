# Preview cinematic appearance and phone-call playback — authorized scope

Base: exact signed 2103448, source ecfbfdd00c443bad530d3ed429eb69755f46601f,
APK SHA256 2c20613f9056e84fea402cf67729939a205b7d9afb87ec1b6fab800a641efbd3.
User explicitly selected 448 as the base and requested the locked right-hand
cinematic mockup, with every unrelated component preserved, plus playback during
a phone call. The current attached reference is visually readable in the
conversation. No raw PNG file is exposed by the workspace or connected Pages;
no raw-image hash or automated pixel-diff claim is made from the inline image.
The design-only lock document remains unchanged as the visual/behavior contract.

Authorized production changes: Preview activity presentation and call-aware audio
focus handling; tightly scoped Preview-only drawing/theme helpers. Retain the
exact 448 decoder, resume database/helper, request state and Splash routing.
Cobra, Kodi, shared/native, launcher, chooser behavior, all other assets and
shutdown are frozen. Only necessary app/component version metadata and original
signature output may additionally change in the candidate APK. No native,
Media3, database migration, data reset, replacement keys or shutdown tests.

Selected checks recorded before implementation/execution:
- Actual Android rendering of dark/light chrome, native Resume choice, and the
  exact existing control actions, content descriptions, true horizontal control
  scrolling and independent timeline seeking. Cover, inner, landscape and short
  windows; compare measured geometry and manually inspect against the visible
  approved reference. Do not claim literal bitmap equality for dynamic media,
  filenames, time or differently shaped Android windows.
- Resume/Start Over regression reuses 448 storage evidence when byte-identical;
  real input checks verify the new presentation preserves these actions.
- Targeted focus-policy checks for granted/denied focus, active call and ordinary
  non-call focus losses; user Pause/Stop/Close remain authoritative. Preserve
  USAGE_MEDIA, device/call volume, audio route and Android's enforced muting.
- Focused real Android decoding and synthetic emulator call/communication
  observations where supported. Never place a real call. Distinguish simulated
  Android audio-policy evidence from actual Fold/carrier/VoIP acceptance.
- Original-key/signature, owner/class/member preservation versus actual signed
  448, package identity and higher install-over version; matching components.

The official Android audio-focus contract permits intentionally starting playback
during a call, while the OS may mute media that was already playing when a call
arrives. The correction must not spoof audio usage, take call ownership, alter
system volume or disable telephony protections. Physical Fold acceptance and a
new release lock remain the user's decision.
