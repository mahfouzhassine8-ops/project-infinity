  private void showStyledInfinityExperienceChooser(ExperienceTheme theme)
  {
    android.widget.FrameLayout root = new android.widget.FrameLayout(this);
    root.setTag("experience-themed-root");
    root.addView(new ExperienceBackdrop(theme), new android.widget.FrameLayout.LayoutParams(-1, -1));

    android.widget.ScrollView scroll = new android.widget.ScrollView(this);
    scroll.setFillViewport(true); scroll.setClipToPadding(false);
    android.widget.LinearLayout content = new android.widget.LinearLayout(this);
    content.setOrientation(android.widget.LinearLayout.VERTICAL); content.setGravity(android.view.Gravity.CENTER_HORIZONTAL);
    content.setPadding(chooserDp(theme.outerPadding), chooserDp(20), chooserDp(theme.outerPadding), chooserDp(18));
    scroll.addView(content, new android.widget.ScrollView.LayoutParams(-1, -2));
    root.addView(scroll, new android.widget.FrameLayout.LayoutParams(-1, -1));

    android.widget.FrameLayout identity = new android.widget.FrameLayout(this);
    android.widget.LinearLayout center = new android.widget.LinearLayout(this); center.setOrientation(android.widget.LinearLayout.VERTICAL); center.setGravity(android.view.Gravity.CENTER);
    ExperienceMark infinityMark = new ExperienceMark(false, theme.infinityBorder); center.addView(infinityMark, new android.widget.LinearLayout.LayoutParams(chooserDp(94), chooserDp(54)));
    android.widget.TextView brand = chooserStyledText(theme.brand, theme.text, 22, true, android.view.Gravity.CENTER); brand.setLetterSpacing(.28f); center.addView(brand);
    android.widget.TextView brandTag = chooserStyledText(theme.brandTagline, theme.muted, 10, false, android.view.Gravity.CENTER); brandTag.setLetterSpacing(.24f); center.addView(brandTag);
    identity.addView(center, new android.widget.FrameLayout.LayoutParams(-1, -2, android.view.Gravity.CENTER));

    android.widget.LinearLayout personalized = new android.widget.LinearLayout(this); personalized.setOrientation(android.widget.LinearLayout.VERTICAL); personalized.setGravity(android.view.Gravity.CENTER);
    android.widget.TextView initials = chooserStyledText(theme.initials, theme.text, 15, true, android.view.Gravity.CENTER); initials.setTag("experience-initials"); initials.setBackground(chooserSurface(theme.badgeFill, theme.badgeBorder, 24));
    personalized.addView(initials, new android.widget.LinearLayout.LayoutParams(chooserDp(48), chooserDp(48)));
    android.widget.TextView personal = chooserStyledText(theme.personalization, theme.muted, 8, false, android.view.Gravity.CENTER); personal.setLetterSpacing(.12f); personal.setMaxLines(1); personalized.addView(personal);
    android.widget.FrameLayout.LayoutParams personalizedParams = new android.widget.FrameLayout.LayoutParams(chooserDp(128), -2, android.view.Gravity.END | android.view.Gravity.TOP);
    identity.addView(personalized, personalizedParams);
    content.addView(identity, new android.widget.LinearLayout.LayoutParams(-1, chooserDp(98)));

    android.widget.TextView title = chooserStyledText(theme.title, theme.text, 30, true, android.view.Gravity.CENTER); title.setTag("experience-title");
    android.widget.LinearLayout.LayoutParams titleParams = new android.widget.LinearLayout.LayoutParams(-1, -2); titleParams.topMargin = chooserDp(18); content.addView(title, titleParams);

    android.widget.LinearLayout cards = new android.widget.LinearLayout(this);
    int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels / getResources().getDisplayMetrics().density);
    boolean stacked = widthDp < theme.stackBelowWidth;
    cards.setOrientation(stacked ? android.widget.LinearLayout.VERTICAL : android.widget.LinearLayout.HORIZONTAL); cards.setGravity(android.view.Gravity.CENTER);
    android.widget.LinearLayout.LayoutParams cardsParams = new android.widget.LinearLayout.LayoutParams(-1, -2); cardsParams.topMargin = chooserDp(26); content.addView(cards, cardsParams);

    android.widget.FrameLayout infinity = chooserExperienceCard(theme, true,
        () -> launchInfinityExperience("infinity"), () -> showExperienceCardSettings("infinity"));
    android.widget.FrameLayout cobra = chooserExperienceCard(theme, false,
        () -> launchInfinityExperience("live"), () -> showExperienceCardSettings("live"));
    if (stacked)
    {
      android.widget.LinearLayout.LayoutParams first = new android.widget.LinearLayout.LayoutParams(-1, chooserDp(theme.cardHeight)); first.bottomMargin = chooserDp(theme.cardGap); cards.addView(infinity, first);
      cards.addView(cobra, new android.widget.LinearLayout.LayoutParams(-1, chooserDp(theme.cardHeight)));
    }
    else
    {
      android.widget.LinearLayout.LayoutParams first = new android.widget.LinearLayout.LayoutParams(0, chooserDp(theme.cardHeight), 1); first.rightMargin = chooserDp(theme.cardGap / 2); cards.addView(infinity, first);
      android.widget.LinearLayout.LayoutParams second = new android.widget.LinearLayout.LayoutParams(0, chooserDp(theme.cardHeight), 1); second.leftMargin = chooserDp(theme.cardGap / 2); cards.addView(cobra, second);
    }

    android.widget.TextView footer = chooserStyledText(theme.footerBrand, theme.muted, 9, false, android.view.Gravity.CENTER); footer.setLetterSpacing(.10f);
    android.widget.LinearLayout.LayoutParams footerParams = new android.widget.LinearLayout.LayoutParams(-1, -2); footerParams.topMargin = chooserDp(34); content.addView(footer, footerParams);
    android.widget.TextView footerTag = chooserStyledText(theme.footerTagline, theme.muted, 8, false, android.view.Gravity.CENTER); footerTag.setLetterSpacing(.18f); content.addView(footerTag);

    setContentView(root);
    infinity.requestFocus();
    infinity.setBackground(chooserGradient(theme.infinityTop, theme.infinityBottom, theme.infinityGlow, theme.cardRadius, true));
    infinity.setElevation(chooserDp(9));
  }
