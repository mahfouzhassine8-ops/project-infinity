#!/usr/bin/env python3
"""Make the startup experience chooser two-card, direct-launch, and remembered.

Android presentation-shell only. This patch changes Splash.java.in after the
existing one-app chooser has been reconstructed. It does not touch Kodi native,
Cobra playback/provider ownership, rotation, Fold, background/resume, or the
explicit Infinity/Cobra handoff controls inside the experiences.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SPLASH = Path("tools/android/packaging/xbmc/src/Splash.java.in")


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"Chooser {label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"Chooser {label}: end marker missing")
    return text[:a] + replacement + text[b:]


def patch(java: str) -> str:
    # Preserve the existing cards, title and subtitle. Replace the old two-step
    # selection + bottom action row with direct card actions. A card tap writes
    # the same preference already consumed by startXBMC(), then launches it.
    direct_actions = r'''    infinity.setOnClickListener(v -> {
      getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
          .putString(INFINITY_EXPERIENCE_DEFAULT, "infinity").apply();
      launchInfinityExperience("infinity");
    });
    cobra.setOnClickListener(v -> {
      getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
          .putString(INFINITY_EXPERIENCE_DEFAULT, "live").apply();
      launchInfinityExperience("live");
    });

    // D-pad/remote focus remains visual only; activation still happens on click.
    infinity.setOnFocusChangeListener((v, hasFocus) -> {
      if (hasFocus) {
        setChooserCardState(infinity, true, true);
        setChooserCardState(cobra, false, false);
      }
    });
    cobra.setOnFocusChangeListener((v, hasFocus) -> {
      if (hasFocus) {
        setChooserCardState(cobra, false, true);
        setChooserCardState(infinity, true, false);
      }
    });
    infinity.requestFocus();
    setChooserCardState(infinity, true, true);
    setChooserCardState(cobra, false, false);

'''
    java = replace_between(
        java,
        "    final Runnable refresh = () -> {\n",
        "    setContentView(root);\n",
        direct_actions + "    setContentView(root);\n",
        "direct-card action block",
    )
    return java


def verify(java: str) -> None:
    required = (
        'putString(INFINITY_EXPERIENCE_DEFAULT, "infinity")',
        'putString(INFINITY_EXPERIENCE_DEFAULT, "live")',
        'launchInfinityExperience("infinity")',
        'launchInfinityExperience("live")',
        'setChooserCardState(infinity, true, true)',
        'setChooserCardState(cobra, false, true)',
        'Choose Your Experience',
        '∞  INFINITY',
        '◈  COBRA',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Chooser contract missing: " + token)
    for forbidden in (
        "LAUNCH & REMEMBER",
        "JUST THIS TIME",
        "Remember my choice",
        'chooserCard(\n        "EXIT"',
        "switch experiences later from Settings.",
        "switch apps later from Settings.",
    ):
        if forbidden in java:
            raise RuntimeError("Old chooser control remains: " + forbidden)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    splash = args.source.resolve() / SPLASH
    java = splash.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    splash.write_text(java, encoding="utf-8")
    print("PASS: two-card remembered experience chooser applied")


if __name__ == "__main__":
    main()
