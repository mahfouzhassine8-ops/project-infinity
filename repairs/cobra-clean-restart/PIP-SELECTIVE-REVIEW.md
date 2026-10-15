# PiP corrective continuation — selective comparison

User authorization: COBRA — PiP CORRECTIVE REPAIR — PROCEED, continuing from `aca973f21642c30148367baaf7ed0e0f83f079f8`.

The user physically tested PiP in rejected 2103370 and reports it worked in the scenario tested. The precise entry surface, mute state and lifecycle sequence were not specified; no broader physical acceptance is inferred. 2103370 remains rejected as a complete build.

## Source comparison

Read-only reference: `47d9e563a6052e6ac5d90f784ad526346d93d9cf`, `repairs/cobra-six-2103370/changes.patch`, especially the PiP block at lines 249–305.

Existing clean implementation: last tested runtime at `daa8c1b19d02c84b86696fc82cb8cb0a0ac30563`, saved by checkpoint `aca973f21642c30148367baaf7ed0e0f83f079f8`.

Both paths use the preserved `enterCobraPictureInPicture()` implementation, `cobraPipParams()`, preview-to-fullscreen session transfer and return to the originating preview. The current implementation already passed its controlled mini/fullscreen round trips. Replacing that whole controller is unnecessary for the identified layout crash.

Selectively retained from 2103370 in the new mini-player entry only:

- Reject entry when the player is locked or already in PiP.
- Require the selected channel's exact session key to match the actual preview session before promoting it. This prevents the existing promotion fallback from opening a new player for a mismatched selection.

The retained guard calls existing owners and does not change fullscreen Channels audio, previous/next/direct tuning, audio focus, call handling, background policy, or the native PiP entry implementation.

Not copied:

- The Status/health fullscreen rail, navigation arrows, scroll instruction text, or its saved-preference-based Pro predicate.
- Global audio carry inserted by 2103370 into unrelated direct and ordinary tuning methods.
- Explicit paused/multi-entry policy and broad lifecycle/audio restoration changes. They are not required for this corrective step and are not established as the user's physically tested scenario.
- Any Sports/Stats/header/chooser code from 2103370.

## Unsupported-control crash

The clean controller keeps a ninth `Hero.player` action for PiP but does not attach it to the original strip when unsupported. The existing layout loop iterates all actions and requires LayoutParams even for an unattached action.

The correction initializes LayoutParams on **only `player[8]`**, using the same strip parameter class and existing default size. Original eight actions, strip order, original layout loop, unsupported strip membership, visibility decisions and callbacks remain unchanged. No null-pointer is caught or suppressed and no preservation assertion is disabled.

`pip_corrective.py` refuses to apply unless both generated runtime files match their exact saved preimage hashes. It produces a separate narrow delta and updates the full changed-method/source receipts. The approved 2103324 Cobra provenance and 2103369 transport stay fixed.

## Groups investigation

The first corrective rerun retains the existing failed Groups assertion. A read-only trace records adapter size, framework layout flags, child count, selected positions and attached ancestor geometry if the list is empty. It does not create rows, call hidden tuning callbacks, reset the adapter, force layout, or turn a failure into success.

Current comparison and source edits are not acceptance statements. All 185 cases must pass; no APK packaging or signing is part of these workflows. Native libraries and original signed APKs remain untouched.
