  private android.widget.TextView chooserStyledText(String value, int color, float sp,
      boolean medium, int gravity)
  {
    android.widget.TextView text = chooserText(value, color, sp);
    text.setGravity(gravity);
    text.setTypeface(android.graphics.Typeface.create("sans-serif", medium ? android.graphics.Typeface.BOLD : android.graphics.Typeface.NORMAL));
    text.setIncludeFontPadding(false);
    return text;
  }

  private android.widget.FrameLayout chooserExperienceCard(ExperienceTheme theme,
      boolean infinity, Runnable launch, Runnable settings)
  {
    int border = infinity ? theme.infinityBorder : theme.cobraBorder;
    int top = infinity ? theme.infinityTop : theme.cobraTop;
    int bottom = infinity ? theme.infinityBottom : theme.cobraBottom;
    int glow = infinity ? theme.infinityGlow : theme.cobraGlow;
    String title = infinity ? theme.infinityTitle : theme.cobraTitle;
    String subtitle = infinity ? theme.infinitySubtitle : theme.cobraSubtitle;

    android.widget.FrameLayout card = new android.widget.FrameLayout(this);
    card.setFocusable(true); card.setClickable(true); card.setTag(infinity ? "experience-card-infinity" : "experience-card-cobra");
    card.setContentDescription(title + ", " + subtitle);
    card.setBackground(chooserGradient(top, bottom, border, theme.cardRadius, false));
    card.setPadding(chooserDp(18), chooserDp(16), chooserDp(18), chooserDp(14));

    android.widget.LinearLayout body = new android.widget.LinearLayout(this);
    body.setOrientation(android.widget.LinearLayout.VERTICAL); body.setGravity(android.view.Gravity.CENTER);
    ExperienceMark mark = new ExperienceMark(!infinity, border); mark.setTag(infinity ? "experience-mark-infinity" : "experience-mark-cobra");
    body.addView(mark, new android.widget.LinearLayout.LayoutParams(chooserDp(112), chooserDp(78)));
    android.widget.TextView heading = chooserStyledText(title, theme.text, 23, true, android.view.Gravity.CENTER); heading.setLetterSpacing(.12f); body.addView(heading);
    android.widget.TextView copy = chooserStyledText(subtitle, theme.text, 12, false, android.view.Gravity.CENTER); copy.setLetterSpacing(.06f); copy.setMaxLines(3);
    android.widget.LinearLayout.LayoutParams copyParams = new android.widget.LinearLayout.LayoutParams(-1, -2); copyParams.topMargin = chooserDp(10); body.addView(copy, copyParams);
    card.addView(body, new android.widget.FrameLayout.LayoutParams(-1, -1));

    android.widget.TextView gear = chooserStyledText("⚙", theme.text, 17, false, android.view.Gravity.CENTER);
    gear.setFocusable(true); gear.setClickable(true); gear.setTag(infinity ? "experience-settings-infinity" : "experience-settings-cobra"); gear.setContentDescription(title + " settings");
    gear.setBackground(chooserSurface((top & 0x00ffffff) | 0xdd000000, border, 16));
    gear.setOnClickListener(v -> {
      if (!infinity)
      {
        final String[] choices = new String[]{"Cobra settings", "Restore Built-in Theme", "Cancel"};
        new android.app.AlertDialog.Builder(this)
            .setTitle("Cobra recovery")
            .setItems(choices, (dialog, which) -> {
              if (which == 0) settings.run();
              else if (which == 1)
              {
                new android.app.AlertDialog.Builder(this)
                    .setTitle("Restore Built-in Theme?")
                    .setMessage("Disables the installed Cobra visual theme and returns Cobra to its built-in appearance. Playback, timeshift and app data are not cleared.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Restore", (confirm, button) -> restoreBuiltInVisualThemeFromChooser())
                    .show();
              }
            }).show();
      }
      else settings.run();
    });
    android.widget.FrameLayout.LayoutParams gearParams = new android.widget.FrameLayout.LayoutParams(chooserDp(44), chooserDp(44), android.view.Gravity.TOP | android.view.Gravity.END);
    card.addView(gear, gearParams);

    card.setOnClickListener(v -> launch.run());
    card.setOnFocusChangeListener((v, focused) -> {
      card.setBackground(chooserGradient(top, bottom, focused ? glow : border, theme.cardRadius, focused));
      card.animate().scaleX(focused ? 1.015f : 1f).scaleY(focused ? 1.015f : 1f).setDuration(theme.motionMs).start();
      card.setElevation(chooserDp(focused ? 9 : 3));
    });
    return card;
  }
