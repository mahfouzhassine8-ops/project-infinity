#!/usr/bin/env python3
"""Keep the startup chooser to two cards with per-card settings menus.

Android presentation-shell only. The two large experience cards launch immediately
without changing the remembered default. A small gear on each card exposes the
optional remember/default controls. Kodi native, Cobra playback/provider ownership,
rotation, Fold, background/resume, and explicit in-app handoff controls stay intact.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SPLASH = Path("tools/android/packaging/xbmc/src/Splash.java.in")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Chooser {label}: expected one exact match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"Chooser {label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"Chooser {label}: end marker missing")
    return text[:a] + replacement + text[b:]


def patch(java: str) -> str:
    settings_helper = r'''  private void showExperienceCardSettings(String experience)
  {
    final boolean cobra = "live".equals(experience);
    final String title = cobra ? "Cobra options" : "Infinity options";
    final String label = cobra ? "Cobra" : "Infinity";
    final String[] options = new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time"
    };
    new android.app.AlertDialog.Builder(this)
        .setTitle(title)
        .setItems(options, (dialog, which) -> {
          if (which == 0)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .putString(INFINITY_EXPERIENCE_DEFAULT, experience).apply();
            launchInfinityExperience(experience);
          }
          else if (which == 1)
          {
            launchInfinityExperience(experience);
          }
          else
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .remove(INFINITY_EXPERIENCE_DEFAULT).apply();
            android.widget.Toast.makeText(this,
                "Infinity will ask which experience to open next time.",
                android.widget.Toast.LENGTH_SHORT).show();
          }
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

'''
    java = once(
        java,
        "  private void showInfinityExperienceChooser()\n",
        settings_helper + "  private void showInfinityExperienceChooser()\n",
        "card settings helper",
    )

    old_cards = r'''    android.widget.LinearLayout.LayoutParams infinityParams =
        new android.widget.LinearLayout.LayoutParams(0, chooserDp(210), 1);
    infinityParams.rightMargin = chooserDp(10);
    cards.addView(infinity, infinityParams);
    android.widget.LinearLayout.LayoutParams cobraParams =
        new android.widget.LinearLayout.LayoutParams(0, chooserDp(210), 1);
    cobraParams.leftMargin = chooserDp(10);
    cards.addView(cobra, cobraParams);

'''
    new_cards = r'''    android.widget.FrameLayout infinityCard = new android.widget.FrameLayout(this);
    infinityCard.addView(infinity, new android.widget.FrameLayout.LayoutParams(
        android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
        android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
    android.widget.Button infinitySettings = new android.widget.Button(this);
    infinitySettings.setText("⚙");
    infinitySettings.setTextColor(white);
    infinitySettings.setTextSize(18);
    infinitySettings.setAllCaps(false);
    infinitySettings.setPadding(0, 0, 0, 0);
    infinitySettings.setMinHeight(0);
    infinitySettings.setMinWidth(0);
    infinitySettings.setContentDescription("Infinity settings");
    infinitySettings.setBackground(chooserSurface(
        android.graphics.Color.rgb(18, 62, 84), cyan, 18));
    android.widget.FrameLayout.LayoutParams infinityGearParams =
        new android.widget.FrameLayout.LayoutParams(
            chooserDp(48), chooserDp(48), android.view.Gravity.TOP | android.view.Gravity.END);
    infinityGearParams.setMargins(0, chooserDp(10), chooserDp(10), 0);
    infinityCard.addView(infinitySettings, infinityGearParams);

    android.widget.FrameLayout cobraCard = new android.widget.FrameLayout(this);
    cobraCard.addView(cobra, new android.widget.FrameLayout.LayoutParams(
        android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
        android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
    android.widget.Button cobraSettings = new android.widget.Button(this);
    cobraSettings.setText("⚙");
    cobraSettings.setTextColor(white);
    cobraSettings.setTextSize(18);
    cobraSettings.setAllCaps(false);
    cobraSettings.setPadding(0, 0, 0, 0);
    cobraSettings.setMinHeight(0);
    cobraSettings.setMinWidth(0);
    cobraSettings.setContentDescription("Cobra settings");
    cobraSettings.setBackground(chooserSurface(
        android.graphics.Color.rgb(66, 19, 32), cobraRed, 18));
    android.widget.FrameLayout.LayoutParams cobraGearParams =
        new android.widget.FrameLayout.LayoutParams(
            chooserDp(48), chooserDp(48), android.view.Gravity.TOP | android.view.Gravity.END);
    cobraGearParams.setMargins(0, chooserDp(10), chooserDp(10), 0);
    cobraCard.addView(cobraSettings, cobraGearParams);

    android.widget.LinearLayout.LayoutParams infinityParams =
        new android.widget.LinearLayout.LayoutParams(0, chooserDp(210), 1);
    infinityParams.rightMargin = chooserDp(10);
    cards.addView(infinityCard, infinityParams);
    android.widget.LinearLayout.LayoutParams cobraParams =
        new android.widget.LinearLayout.LayoutParams(0, chooserDp(210), 1);
    cobraParams.leftMargin = chooserDp(10);
    cards.addView(cobraCard, cobraParams);

'''
    java = once(java, old_cards, new_cards, "card gear overlays")

    # The main card is always a one-tap launch. Remembering is intentionally
    # optional and lives behind the small gear so the chooser itself stays clean.
    actions = r'''    infinity.setOnClickListener(v -> launchInfinityExperience("infinity"));
    cobra.setOnClickListener(v -> launchInfinityExperience("live"));
    infinitySettings.setOnClickListener(v -> showExperienceCardSettings("infinity"));
    cobraSettings.setOnClickListener(v -> showExperienceCardSettings("live"));

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
        actions + "    setContentView(root);\n",
        "two-card action block",
    )
    return java


def verify(java: str) -> None:
    required = (
        'launchInfinityExperience("infinity")',
        'launchInfinityExperience("live")',
        'showExperienceCardSettings("infinity")',
        'showExperienceCardSettings("live")',
        'setContentDescription("Infinity settings")',
        'setContentDescription("Cobra settings")',
        '"Remember & launch " + label',
        '"Launch " + label + " just this time"',
        '"Ask every time"',
        '.remove(INFINITY_EXPERIENCE_DEFAULT)',
        'putString(INFINITY_EXPERIENCE_DEFAULT, experience)',
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
    print("PASS: two-card chooser with per-card remember/settings menus applied")


if __name__ == "__main__":
    main()
