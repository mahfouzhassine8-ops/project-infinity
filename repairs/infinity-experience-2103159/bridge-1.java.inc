  private static final int INFINITY_EXPERIENCE_THEME_BRIDGE = 1;
  private static final String INFINITY_EXPERIENCE_THEME_FILE =
      ".kodi/addons/script.infinity.cobra.theme/resources/experience-chooser.json";

  private static final class ExperienceTheme
  {
    final String brand, brandTagline, title, initials, personalization;
    final String infinityTitle, infinitySubtitle, cobraTitle, cobraSubtitle;
    final String footerBrand, footerTagline;
    final int background, backgroundGlow, text, muted;
    final int infinityTop, infinityBottom, infinityBorder, infinityGlow;
    final int cobraTop, cobraBottom, cobraBorder, cobraGlow;
    final int badgeFill, badgeBorder, horizon;
    final int outerPadding, cardRadius, cardGap, cardHeight, stackBelowWidth, motionMs;

    ExperienceTheme(org.json.JSONObject root) throws org.json.JSONException
    {
      if (root.optInt("schema", 0) != 1 ||
          !"infinity-experience-chooser".equals(root.optString("scope")) ||
          root.optInt("minimum_bridge", Integer.MAX_VALUE) > INFINITY_EXPERIENCE_THEME_BRIDGE)
        throw new org.json.JSONException("Unsupported experience theme contract");
      org.json.JSONObject copy = root.getJSONObject("copy");
      org.json.JSONObject palette = root.getJSONObject("palette");
      org.json.JSONObject layout = root.optJSONObject("layout");
      brand = chooserThemeText(copy, "brand", "INFINITY", 28, false);
      brandTagline = chooserThemeText(copy, "brand_tagline", "BEYOND ENTERTAINMENT", 40, false);
      title = chooserThemeText(copy, "title", "Choose Your Experience", 48, false);
      initials = chooserInitials(copy.optString("initials", "HM"));
      personalization = chooserThemeText(copy, "personalization", "PERSONALIZED FOR YOU", 40, false);
      infinityTitle = chooserThemeText(copy, "infinity_title", "INFINITY", 24, false);
      infinitySubtitle = chooserThemeText(copy, "infinity_subtitle", "YOUR HOME FOR MOVIES, SHOWS AND MORE", 72, true);
      cobraTitle = chooserThemeText(copy, "cobra_title", "COBRA", 24, false);
      cobraSubtitle = chooserThemeText(copy, "cobra_subtitle", "FOCUSED. FAST. POWERFUL.", 72, true);
      footerBrand = chooserThemeText(copy, "footer_brand", "INFINITY BY HASSINE MAHFOUZ", 56, false);
      footerTagline = chooserThemeText(copy, "footer_tagline", "ONE APP • YOUR WORLD", 48, false);
      background = chooserThemeColor(palette, "background", "#030713");
      backgroundGlow = chooserThemeColor(palette, "background_glow", "#14253B");
      text = chooserThemeColor(palette, "text", "#F4F8FF");
      muted = chooserThemeColor(palette, "muted", "#91A4BB");
      infinityTop = chooserThemeColor(palette, "infinity_top", "#0B4771");
      infinityBottom = chooserThemeColor(palette, "infinity_bottom", "#082B4A");
      infinityBorder = chooserThemeColor(palette, "infinity_border", "#28D9FF");
      infinityGlow = chooserThemeColor(palette, "infinity_glow", "#1AB8F0");
      cobraTop = chooserThemeColor(palette, "cobra_top", "#66151D");
      cobraBottom = chooserThemeColor(palette, "cobra_bottom", "#351017");
      cobraBorder = chooserThemeColor(palette, "cobra_border", "#FF3B4F");
      cobraGlow = chooserThemeColor(palette, "cobra_glow", "#E21D35");
      badgeFill = chooserThemeColor(palette, "badge_fill", "#10213A");
      badgeBorder = chooserThemeColor(palette, "badge_border", "#4AA7FF");
      horizon = chooserThemeColor(palette, "horizon", "#17B6FF");
      outerPadding = chooserThemeBound(layout, "outer_padding_dp", 24, 12, 48);
      cardRadius = chooserThemeBound(layout, "card_radius_dp", 22, 10, 40);
      cardGap = chooserThemeBound(layout, "card_gap_dp", 14, 6, 30);
      cardHeight = chooserThemeBound(layout, "card_height_dp", 230, 180, 320);
      stackBelowWidth = chooserThemeBound(layout, "stack_below_width_dp", 330, 280, 480);
      motionMs = chooserThemeBound(layout, "motion_ms", 180, 0, 400);
    }
  }

  private static String chooserThemeText(org.json.JSONObject object, String key,
      String fallback, int max, boolean forbidLegacy) throws org.json.JSONException
  {
    String value = object.optString(key, fallback).trim();
    if (value.isEmpty() || value.length() > max || value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0)
      throw new org.json.JSONException("Invalid experience copy: " + key);
    String lower = value.toLowerCase(java.util.Locale.US);
    if (forbidLegacy && (lower.contains("live tv") || lower.contains("2-in-1") || lower.contains("2 in 1")))
      throw new org.json.JSONException("Legacy chooser copy rejected");
    return value;
  }

  private static String chooserInitials(String value) throws org.json.JSONException
  {
    String initials = value == null ? "" : value.trim().toUpperCase(java.util.Locale.US);
    if (!initials.matches("[A-Z]{1,3}"))
      throw new org.json.JSONException("Invalid chooser initials");
    return initials;
  }

  private static int chooserThemeColor(org.json.JSONObject object, String key, String fallback)
      throws org.json.JSONException
  {
    String value = object.optString(key, fallback).trim();
    if (!value.matches("#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{8}"))
      throw new org.json.JSONException("Invalid experience color: " + key);
    return android.graphics.Color.parseColor(value);
  }

  private static int chooserThemeBound(org.json.JSONObject object, String key,
      int fallback, int low, int high)
  {
    int value = object == null ? fallback : object.optInt(key, fallback);
    return Math.max(low, Math.min(high, value));
  }

  private void restoreBuiltInVisualThemeFromChooser()
  {
    File root = getExternalFilesDir(null);
    if (root == null)
    {
      android.widget.Toast.makeText(this, "Theme recovery unavailable", android.widget.Toast.LENGTH_LONG).show();
      return;
    }
    File visualRoot = new File(root, ".kodi/addons/script.infinity.cobra.theme/resources/visual");
    File pointer = new File(visualRoot, "active.json");
    boolean reset = false;
    try
    {
      if (pointer.isFile())
      {
        File backup = new File(visualRoot, "active.recovery-backup.json");
        try
        {
          java.nio.file.Files.copy(pointer.toPath(), backup.toPath(),
              java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
        catch (Exception ignored) {}
        if (!pointer.delete())
        {
          try (java.io.FileOutputStream out = new java.io.FileOutputStream(pointer, false))
          {
            out.write("{\"active\":\"\",\"previous\":\"\"}\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
          }
        }
        reset = true;
      }
      File legacy = new File(root, ".kodi/addons/script.infinity.cobra.theme/resources/visual-theme.json");
      if (legacy.isFile())
      {
        File disabled = new File(legacy.getParentFile(), "visual-theme.disabled-by-recovery.json");
        if (disabled.exists()) disabled.delete();
        if (!legacy.renameTo(disabled) && !legacy.delete())
          throw new java.io.IOException("Could not disable legacy visual theme");
        reset = true;
      }
      android.widget.Toast.makeText(this,
          reset ? "Built-in Cobra theme restored" : "Cobra is already using the built-in theme",
          android.widget.Toast.LENGTH_LONG).show();
    }
    catch (Exception failure)
    {
      android.util.Log.e(TAG, "Emergency theme recovery failed", failure);
      android.widget.Toast.makeText(this, "Theme recovery failed", android.widget.Toast.LENGTH_LONG).show();
    }
  }

  private ExperienceTheme loadExperienceTheme()
  {
    File root = getExternalFilesDir(null);
    if (root == null)
      return null;
    File file = new File(root, INFINITY_EXPERIENCE_THEME_FILE);
    try
    {
      if (!file.isFile() || file.length() <= 0 || file.length() > 65536)
        return null;
      File addon = new File(root, ".kodi/addons/script.infinity.cobra.theme/resources");
      String parent = addon.getCanonicalPath() + File.separator;
      if (!file.getCanonicalPath().startsWith(parent))
        return null;
      int size = (int) file.length();
      byte[] data = new byte[size]; int offset = 0;
      try (java.io.FileInputStream input = new java.io.FileInputStream(file))
      {
        while (offset < size)
        {
          int read = input.read(data, offset, size - offset);
          if (read < 0) break;
          if (read == 0) throw new java.io.IOException("Stalled experience theme read");
          offset += read;
        }
      }
      if (offset != size) return null;
      return new ExperienceTheme(new org.json.JSONObject(
          new String(data, java.nio.charset.StandardCharsets.UTF_8)));
    }
    catch (Exception failure)
    {
      Log.w(TAG, "Experience theme ignored: " + failure.getClass().getSimpleName());
      return null;
    }
  }

  private android.graphics.drawable.GradientDrawable chooserGradient(
      int top, int bottom, int stroke, int radius, boolean active)
  {
    android.graphics.drawable.GradientDrawable shape = new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
        new int[]{top, bottom});
    shape.setCornerRadius(chooserDp(radius));
    shape.setStroke(chooserDp(active ? 2 : 1), stroke);
    return shape;
  }
