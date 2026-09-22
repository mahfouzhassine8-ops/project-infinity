  private android.widget.TextView infinityHealthText(String value,int color,float size,int gravity)
  {
    android.widget.TextView view=new android.widget.TextView(this);
    view.setText(value);view.setTextColor(color);view.setTextSize(size);view.setGravity(gravity);
    view.setTypeface(vtheme().font("chooser.health.text",android.graphics.Typeface.create("sans-serif",android.graphics.Typeface.NORMAL)));
    view.setPadding(chooserDp(4),chooserDp(2),chooserDp(4),chooserDp(2));
    return view;
  }

  private android.view.View infinityHealthRow(String glyph,String title,String subtitle,int panel,int rim,int accent,int text,int muted,Runnable action)
  {
    android.widget.LinearLayout row=new android.widget.LinearLayout(this);
    row.setOrientation(android.widget.LinearLayout.HORIZONTAL);
    row.setGravity(android.view.Gravity.CENTER_VERTICAL);
    row.setFocusable(true);row.setClickable(true);
    row.setPadding(chooserDp(14),chooserDp(10),chooserDp(14),chooserDp(10));
    row.setBackground(chooserControlSurface(panel,rim,16,accent));

    android.widget.TextView icon=infinityHealthText(glyph,accent,22,android.view.Gravity.CENTER);
    android.widget.LinearLayout.LayoutParams iconLp=new android.widget.LinearLayout.LayoutParams(chooserDp(42),chooserDp(42));
    row.addView(icon,iconLp);

    android.widget.LinearLayout copy=new android.widget.LinearLayout(this);
    copy.setOrientation(android.widget.LinearLayout.VERTICAL);
    copy.setPadding(chooserDp(8),0,chooserDp(4),0);
    android.widget.TextView heading=infinityHealthText(title,text,15,android.view.Gravity.LEFT|android.view.Gravity.CENTER_VERTICAL);
    heading.setTypeface(vtheme().font("chooser.health.row.title",android.graphics.Typeface.create("sans-serif-medium",android.graphics.Typeface.NORMAL)));
    android.widget.TextView detail=infinityHealthText(subtitle,muted,11,android.view.Gravity.LEFT|android.view.Gravity.CENTER_VERTICAL);
    detail.setMaxLines(2);
    copy.addView(heading,new android.widget.LinearLayout.LayoutParams(-1,chooserDp(24)));
    copy.addView(detail,new android.widget.LinearLayout.LayoutParams(-1,chooserDp(34)));
    row.addView(copy,new android.widget.LinearLayout.LayoutParams(0,chooserDp(58),1));

    android.widget.TextView arrow=infinityHealthText("›",muted,24,android.view.Gravity.CENTER);
    row.addView(arrow,new android.widget.LinearLayout.LayoutParams(chooserDp(24),chooserDp(44)));

    row.setOnClickListener(v->action.run());
    return row;
  }

  private android.app.Dialog infinityHealthDialog(String title,String subtitle,boolean scrollBody)
  {
    final boolean light="light".equals(chooserAppearanceMode());
    final boolean oled="oled".equals(chooserAppearanceMode());
    final int background=chooserBuiltinColor("background",0xfff7f9fc,android.graphics.Color.BLACK);
    final int panel=chooserBuiltinColor("panel",0xffffffff,oled?0xff05080d:0xff0b0f16);
    final int rim=chooserBuiltinColor("rim",0xffcbd7e8,0xff293244);
    final int accent=chooserBuiltinColor("accent",0xff145fdf,0xff62aaff);
    final int text=chooserBuiltinColor("text",0xff101b2c,0xfff7faff);
    final int muted=chooserBuiltinColor("muted",0xff526176,0xffb1bfd2);

    android.app.Dialog dialog=new android.app.Dialog(this);
    dialog.requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
    android.widget.LinearLayout shell=new android.widget.LinearLayout(this);
    shell.setOrientation(android.widget.LinearLayout.VERTICAL);
    shell.setPadding(chooserDp(18),chooserDp(18),chooserDp(18),chooserDp(14));
    shell.setBackground(chooserSurface(panel,accent,24));

    android.widget.LinearLayout header=new android.widget.LinearLayout(this);
    header.setOrientation(android.widget.LinearLayout.HORIZONTAL);
    header.setGravity(android.view.Gravity.CENTER_VERTICAL);
    android.widget.TextView mark=infinityHealthText("∞",accent,31,android.view.Gravity.CENTER);
    header.addView(mark,new android.widget.LinearLayout.LayoutParams(chooserDp(54),chooserDp(54)));
    android.widget.LinearLayout copy=new android.widget.LinearLayout(this);
    copy.setOrientation(android.widget.LinearLayout.VERTICAL);
    android.widget.TextView heading=infinityHealthText(title,text,20,android.view.Gravity.LEFT|android.view.Gravity.CENTER_VERTICAL);
    heading.setTypeface(vtheme().font("chooser.health.header",android.graphics.Typeface.create("sans-serif-medium",android.graphics.Typeface.BOLD)));
    android.widget.TextView sub=infinityHealthText(subtitle,muted,11,android.view.Gravity.LEFT|android.view.Gravity.CENTER_VERTICAL);
    copy.addView(heading,new android.widget.LinearLayout.LayoutParams(-1,chooserDp(30)));
    copy.addView(sub,new android.widget.LinearLayout.LayoutParams(-1,chooserDp(24)));
    header.addView(copy,new android.widget.LinearLayout.LayoutParams(0,chooserDp(58),1));
    shell.addView(header,new android.widget.LinearLayout.LayoutParams(-1,chooserDp(64)));

    android.view.View divider=new android.view.View(this);
    divider.setBackgroundColor(rim);
    android.widget.LinearLayout.LayoutParams dividerLp=new android.widget.LinearLayout.LayoutParams(-1,Math.max(1,chooserDp(1)));
    dividerLp.setMargins(0,chooserDp(4),0,chooserDp(10));
    shell.addView(divider,dividerLp);

    dialog.setContentView(shell);
    android.view.Window window=dialog.getWindow();
    if(window!=null){
      window.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT));
      window.addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND);
      android.view.WindowManager.LayoutParams lp=window.getAttributes();
      lp.dimAmount=.56f;window.setAttributes(lp);
    }
    dialog.setOnShowListener(d->{
      android.view.Window w=dialog.getWindow();if(w==null)return;
      int available=getResources().getDisplayMetrics().widthPixels-chooserDp(28);
      int width=Math.min(chooserDp(500),available);
      w.setLayout(width,android.view.WindowManager.LayoutParams.WRAP_CONTENT);
      w.setGravity(android.view.Gravity.CENTER);
    });
    dialog.getWindow().getDecorView().setTag(new Object[]{shell,panel,rim,accent,text,muted,background});
    return dialog;
  }

  private android.widget.LinearLayout infinityHealthDialogShell(android.app.Dialog dialog)
  {
    Object tag=dialog.getWindow().getDecorView().getTag();
    return tag instanceof Object[]?(android.widget.LinearLayout)((Object[])tag)[0]:null;
  }

  private int infinityHealthDialogColor(android.app.Dialog dialog,int index)
  {
    Object tag=dialog.getWindow().getDecorView().getTag();
    return tag instanceof Object[]?(Integer)((Object[])tag)[index]:android.graphics.Color.WHITE;
  }

  private void showInfinityHealthCenter()
  {
    final android.app.Dialog dialog=infinityHealthDialog("Infinity Health Center","DIAGNOSTICS  •  RECOVERY",false);
    final android.widget.LinearLayout shell=infinityHealthDialogShell(dialog);
    final int panel=infinityHealthDialogColor(dialog,1);
    final int rim=infinityHealthDialogColor(dialog,2);
    final int accent=infinityHealthDialogColor(dialog,3);
    final int text=infinityHealthDialogColor(dialog,4);
    final int muted=infinityHealthDialogColor(dialog,5);

    String[][] rows={
      {"↺","Recent crashes & exits","See Android-reported Infinity crashes, ANRs and abnormal exits."},
      {"⇧","Export diagnostic report","Save a shareable Infinity diagnostic text report."},
      {"⧉","Copy diagnostic report","Copy the full report to your clipboard for quick sharing."},
      {"ⓘ","Build & device info","View Infinity version, Android build and device details."}
    };
    Runnable[] actions=new Runnable[]{
      ()->{dialog.dismiss();infinityShowHealthText("Recent crashes & exits",infinityHealthExitHistory(false));},
      ()->{dialog.dismiss();infinityExportHealthReport();},
      ()->{infinityCopyHealthReport();},
      ()->{dialog.dismiss();infinityShowHealthText("Build & device info",infinityHealthBuildInfo());}
    };
    for(int i=0;i<rows.length;i++){
      android.view.View row=infinityHealthRow(rows[i][0],rows[i][1],rows[i][2],panel,rim,accent,text,muted,actions[i]);
      android.widget.LinearLayout.LayoutParams lp=new android.widget.LinearLayout.LayoutParams(-1,chooserDp(78));
      lp.bottomMargin=chooserDp(9);shell.addView(row,lp);
    }

    android.widget.Button close=new android.widget.Button(this);
    close.setText("Close");close.setAllCaps(false);close.setTextSize(13);close.setTextColor(accent);
    close.setTypeface(vtheme().font("chooser.health.close",android.graphics.Typeface.create("sans-serif-medium",android.graphics.Typeface.NORMAL)));
    close.setBackground(chooserControlSurface(panel,rim,14,accent));
    close.setOnClickListener(v->dialog.dismiss());
    android.widget.LinearLayout.LayoutParams closeLp=new android.widget.LinearLayout.LayoutParams(-1,chooserDp(48));
    closeLp.topMargin=chooserDp(2);shell.addView(close,closeLp);
    dialog.show();
  }

  private void infinityShowHealthText(String title,String body)
  {
    final android.app.Dialog dialog=infinityHealthDialog(title,"INFINITY DIAGNOSTICS",true);
    final android.widget.LinearLayout shell=infinityHealthDialogShell(dialog);
    final int panel=infinityHealthDialogColor(dialog,1);
    final int rim=infinityHealthDialogColor(dialog,2);
    final int accent=infinityHealthDialogColor(dialog,3);
    final int text=infinityHealthDialogColor(dialog,4);

    android.widget.TextView output=infinityHealthText(
        body==null||body.trim().isEmpty()?"No diagnostic information available.":body,
        text,12,android.view.Gravity.LEFT|android.view.Gravity.TOP);
    output.setTextIsSelectable(true);output.setLineSpacing(chooserDp(2),1.0f);
    android.widget.ScrollView scroll=new android.widget.ScrollView(this);
    scroll.setFillViewport(false);scroll.setBackground(chooserSurface(panel,rim,14));
    output.setPadding(chooserDp(14),chooserDp(12),chooserDp(14),chooserDp(12));
    scroll.addView(output,new android.widget.ScrollView.LayoutParams(-1,-2));
    android.widget.LinearLayout.LayoutParams scrollLp=new android.widget.LinearLayout.LayoutParams(-1,0,1);
    scrollLp.bottomMargin=chooserDp(10);shell.addView(scroll,scrollLp);

    android.widget.Button close=new android.widget.Button(this);
    close.setText("Close");close.setAllCaps(false);close.setTextColor(accent);close.setTextSize(13);
    close.setBackground(chooserControlSurface(panel,rim,14,accent));close.setOnClickListener(v->dialog.dismiss());
    shell.addView(close,new android.widget.LinearLayout.LayoutParams(-1,chooserDp(48)));
    dialog.show();
    android.view.Window w=dialog.getWindow();
    if(w!=null){
      int available=getResources().getDisplayMetrics().widthPixels-chooserDp(28);
      int width=Math.min(chooserDp(520),available);
      int maxHeight=(int)(getResources().getDisplayMetrics().heightPixels*.78f);
      w.setLayout(width,maxHeight);
    }
  }

