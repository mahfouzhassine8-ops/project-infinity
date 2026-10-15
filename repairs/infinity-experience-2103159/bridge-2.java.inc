  private final class ExperienceBackdrop extends View
  {
    private final ExperienceTheme theme;
    private final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    ExperienceBackdrop(ExperienceTheme value) { super(Splash.this); theme = value; setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO); }
    @Override protected void onDraw(android.graphics.Canvas canvas)
    {
      int w = getWidth(), h = getHeight();
      canvas.drawColor(theme.background);
      paint.setShader(new android.graphics.RadialGradient(w * .5f, h * .35f,
          Math.max(w, h) * .68f, theme.backgroundGlow, theme.background,
          android.graphics.Shader.TileMode.CLAMP));
      canvas.drawRect(0, 0, w, h, paint); paint.setShader(null);
      paint.setStyle(android.graphics.Paint.Style.STROKE);
      paint.setStrokeWidth(Math.max(1, chooserDp(1)));
      paint.setColor((theme.horizon & 0x00ffffff) | 0x55000000);
      android.graphics.RectF horizon = new android.graphics.RectF(-w * .12f, h * .70f, w * 1.12f, h * 1.28f);
      canvas.drawArc(horizon, 196, 148, false, paint);
      paint.setColor((theme.horizon & 0x00ffffff) | 0x22000000);
      for (int i = 1; i <= 4; ++i)
      {
        float inset = i * chooserDp(12);
        android.graphics.RectF echo = new android.graphics.RectF(
            horizon.left + inset, horizon.top + inset * .45f,
            horizon.right - inset, horizon.bottom - inset * .45f);
        canvas.drawArc(echo, 198, 144, false, paint);
      }
      paint.setStyle(android.graphics.Paint.Style.FILL);
    }
  }

  private final class ExperienceMark extends View
  {
    private final boolean cobra;
    private final int color;
    private final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    ExperienceMark(boolean isCobra, int ink) { super(Splash.this); cobra = isCobra; color = ink; setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO); }
    @Override protected void onDraw(android.graphics.Canvas canvas)
    {
      int w = getWidth(), h = getHeight(); float cx = w / 2f, cy = h / 2f;
      paint.setStyle(android.graphics.Paint.Style.STROKE); paint.setStrokeCap(android.graphics.Paint.Cap.ROUND);
      paint.setStrokeJoin(android.graphics.Paint.Join.ROUND); paint.setStrokeWidth(Math.max(2, Math.min(w, h) * .065f)); paint.setColor(color);
      android.graphics.Path path = new android.graphics.Path();
      if (!cobra)
      {
        float rx = w * .33f, ry = h * .25f;
        path.moveTo(cx, cy);
        path.cubicTo(cx - rx * .45f, cy - ry, cx - rx, cy - ry, cx - rx, cy);
        path.cubicTo(cx - rx, cy + ry, cx - rx * .45f, cy + ry, cx, cy);
        path.cubicTo(cx + rx * .45f, cy - ry, cx + rx, cy - ry, cx + rx, cy);
        path.cubicTo(cx + rx, cy + ry, cx + rx * .45f, cy + ry, cx, cy);
      }
      else
      {
        path.moveTo(cx + w * .16f, cy - h * .30f);
        path.cubicTo(cx - w * .03f, cy - h * .38f, cx - w * .20f, cy - h * .18f, cx - w * .12f, cy - h * .02f);
        path.cubicTo(cx - w * .03f, cy + h * .15f, cx + w * .20f, cy + h * .04f, cx + w * .09f, cy - h * .06f);
        path.cubicTo(cx - w * .04f, cy - h * .15f, cx - w * .27f, cy + h * .06f, cx - w * .14f, cy + h * .24f);
        path.cubicTo(cx - w * .02f, cy + h * .40f, cx + w * .18f, cy + h * .30f, cx + w * .20f, cy + h * .16f);
        canvas.drawCircle(cx + w * .11f, cy - h * .21f, Math.max(1, w * .012f), paint);
      }
      canvas.drawPath(path, paint);
    }
  }
