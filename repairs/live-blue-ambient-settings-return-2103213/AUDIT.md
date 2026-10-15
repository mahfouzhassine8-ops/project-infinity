# Infinity/Cobra 2103213 — Live TV blue Ambient + Settings return

Protected parent: locked successful 2103212 Health + Ambient Media Trim.

This is a tightly scoped presentation/navigation successor. The 2103209 Python 3.11 GIL-stability native engine remains byte-identical.

## Authorized corrections

### Live TV Ambient
- Live TV now owns a fixed Cobra blue ambient tint (#49A9FF), instead of inheriting provider/source colors.
- Subtle adds restrained blue edging/wash.
- Immersive adds a clearly visible stronger blue edge/atmospheric wash.
- Coverage reaches the TV Grid/guide shell, rail, toolbar, guide directory/details, visual/settings sheets, and Live TV player drawer.
- Movies/TV Shows keep their existing content-driven Ambient treatment from locked 2103212.
- Video/preview pixels are never recolored.

### Player / Night Cinema presentation
- Player header/footer chrome receives Ambient treatment.
- Live player chrome uses the fixed blue Live TV tint.
- Movie/TV Show player chrome retains content-driven tint.
- Night Cinema now visibly applies true-black player chrome plus restrained Cobra-blue edges, including player drawer/settings-sheet surfaces.
- Transport, playback ownership and video surfaces are untouched.

### Settings return
- Entering Cobra Settings captures the previous Cobra screen before Settings replaces the stage.
- A Back control returns to the preserved screen with the same view object/scroll state when possible.
- Pressing Settings again from the navigation drawer while already in Settings also returns.
- Guide state is restored when Settings was opened from Live TV.
- If a prior screen cannot be safely restored, fallback is Cobra's normal primary Live TV view.

## Preserved
- Locked 2103212 Movies/TV Shows implementation and ambient trim.
- Infinity-native Health Center and crash/export logic.
- Live playback, providers, channel loading, Quick Peek, timeshift/rewind, Multi-View, PiP/background, network policy.
- Native engine, assets/resources and permanent signer.
