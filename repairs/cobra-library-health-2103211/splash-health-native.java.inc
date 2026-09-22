  private void showExperienceCardSettings(String experience)
  {
    final boolean cobra = "live".equals(experience);
    final String title = cobra ? "Cobra options" : "Infinity options";
    final String label = cobra ? "Cobra" : "Infinity";
    final String[] options = cobra ? new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Infinity Health Center",
        "Cobra Recovery"
    } : new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Infinity Health Center"
    };
    (cobra ? new android.app.AlertDialog.Builder(this,
        "light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:
        android.R.style.Theme_Material_Dialog_Alert)
        : new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings"))
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
          else if (which == 2)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .remove(INFINITY_EXPERIENCE_DEFAULT).apply();
            android.widget.Toast.makeText(this,
                "Infinity will ask which experience to open next time.",
                android.widget.Toast.LENGTH_SHORT).show();
          }
          else if (which == 3)
          {
            showInfinityHealthCenter();
          }
          else if (which == 4 && cobra)
          {
            showCobraRecovery();
          }
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  /** Crash-safe diagnostics owned by the Android/Infinity chooser, not Kodi or Cobra. */
  private void showInfinityHealthCenter()
  {
    final String[] options = new String[]{
        "Recent crashes & exits",
        "Export diagnostic report",
        "Copy diagnostic report",
        "Build & device info"
    };
    new android.app.AlertDialog.Builder(this,
        "light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:
        android.R.style.Theme_Material_Dialog_Alert)
        .setTitle("Infinity Health Center")
        .setItems(options,(dialog,which)->{
          if(which==0)infinityShowHealthText("Recent crashes & exits",infinityHealthExitHistory(false));
          else if(which==1)infinityExportHealthReport();
          else if(which==2)infinityCopyHealthReport();
          else if(which==3)infinityShowHealthText("Build & device info",infinityHealthBuildInfo());
        })
        .setNegativeButton("Close",null)
        .show();
  }

  private void infinityShowHealthText(String title,String body)
  {
    android.widget.TextView text = new android.widget.TextView(this);
    text.setText(body==null||body.trim().isEmpty()?"No diagnostic information available.":body);
    text.setTextSize(13);
    text.setTextColor("light".equals(chooserAppearanceMode())?0xff101b2c:0xffeef5ff);
    text.setTextIsSelectable(true);
    text.setPadding(chooserDp(18),chooserDp(14),chooserDp(18),chooserDp(14));
    android.widget.ScrollView scroll = new android.widget.ScrollView(this);
    scroll.addView(text,new android.widget.ScrollView.LayoutParams(-1,-2));
    new android.app.AlertDialog.Builder(this,
        "light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:
        android.R.style.Theme_Material_Dialog_Alert)
        .setTitle(title).setView(scroll).setPositiveButton("Close",null).show();
  }

  private String infinityHealthBuildInfo()
  {
    String versionName="unknown";long versionCode=0L;
    try{
      android.content.pm.PackageInfo info=getPackageManager().getPackageInfo(getPackageName(),0);
      versionName=info.versionName==null?"unknown":info.versionName;
      versionCode=Build.VERSION.SDK_INT>=28?info.getLongVersionCode():info.versionCode;
    }catch(Exception ignored){}
    StringBuilder out=new StringBuilder();
    out.append("Infinity diagnostic environment\n\n");
    out.append("Package: ").append(getPackageName()).append('\n');
    out.append("Version: ").append(versionName).append(" (").append(versionCode).append(")\n");
    out.append("Device: ").append(Build.MANUFACTURER).append(' ').append(Build.MODEL).append('\n');
    out.append("Android: ").append(Build.VERSION.RELEASE).append(" / API ").append(Build.VERSION.SDK_INT).append('\n');
    out.append("Build fingerprint: ").append(Build.FINGERPRINT).append('\n');
    out.append("Process uptime: ").append(android.os.SystemClock.elapsedRealtime()/1000L).append("s\n");
    out.append("Diagnostics owner: Infinity Android chooser (Kodi-independent)\n");
    return out.toString();
  }

  private String infinityExitReasonName(int reason)
  {
    switch(reason){
      case 1:return "self exit";
      case 2:return "signal";
      case 3:return "low memory";
      case 4:return "Java crash";
      case 5:return "native crash";
      case 6:return "ANR";
      case 7:return "initialization failure";
      case 8:return "permission change";
      case 9:return "excessive resource use";
      case 10:return "user requested";
      case 11:return "user stopped";
      case 12:return "dependency died";
      case 13:return "other";
      case 14:return "freezer";
      case 15:return "package state change";
      case 16:return "package updated";
      default:return "unknown ("+reason+")";
    }
  }

  private long infinityNewestAbnormalExit()
  {
    if(Build.VERSION.SDK_INT<30)return 0L;
    try{
      ActivityManager manager=(ActivityManager)getSystemService(Context.ACTIVITY_SERVICE);
      if(manager==null)return 0L;
      java.util.List<android.app.ApplicationExitInfo> rows=
          manager.getHistoricalProcessExitReasons(getPackageName(),0,12);
      for(android.app.ApplicationExitInfo row:rows){
        int reason=row.getReason();
        if(reason==4||reason==5||reason==6)return row.getTimestamp();
      }
    }catch(Exception ignored){}
    return 0L;
  }

  private boolean infinityShouldOfferCrashRecovery()
  {
    long timestamp=infinityNewestAbnormalExit();
    if(timestamp<=0L)return false;
    android.content.SharedPreferences prefs=getSharedPreferences(INFINITY_EXPERIENCE_PREFS,MODE_PRIVATE);
    long seen=prefs.getLong("health_last_acknowledged_exit",0L);
    if(timestamp<=seen)return false;
    prefs.edit().putLong("health_last_acknowledged_exit",timestamp).apply();
    return true;
  }

  private String infinityReadExitTrace(android.app.ApplicationExitInfo row)
  {
    if(Build.VERSION.SDK_INT<31||row==null)return "";
    java.io.InputStream input=null;
    try{
      input=row.getTraceInputStream();
      if(input==null)return "";
      java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
      byte[] buffer=new byte[4096];int total=0,read;
      while((read=input.read(buffer))>0&&total<65536){
        int keep=Math.min(read,65536-total);out.write(buffer,0,keep);total+=keep;
      }
      return out.toString("UTF-8");
    }catch(Exception ignored){return "";}
    finally{if(input!=null)try{input.close();}catch(Exception ignored){}}
  }

  private String infinityHealthExitHistory(boolean includeTrace)
  {
    StringBuilder out=new StringBuilder();
    if(Build.VERSION.SDK_INT<30){
      out.append("Android exit history requires Android 11 or newer.\n");
      return out.toString();
    }
    try{
      ActivityManager manager=(ActivityManager)getSystemService(Context.ACTIVITY_SERVICE);
      if(manager==null)return "Android ActivityManager is unavailable.\n";
      java.util.List<android.app.ApplicationExitInfo> rows=
          manager.getHistoricalProcessExitReasons(getPackageName(),0,12);
      if(rows==null||rows.isEmpty())return "No recent Infinity process exits were reported by Android.\n";
      java.text.SimpleDateFormat stamp=new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss",java.util.Locale.US);
      int index=0;
      for(android.app.ApplicationExitInfo row:rows){
        out.append("#").append(++index).append("  ")
            .append(stamp.format(new java.util.Date(row.getTimestamp()))).append('\n');
        out.append("Reason: ").append(infinityExitReasonName(row.getReason())).append('\n');
        out.append("Process: ").append(row.getProcessName()).append('\n');
        if(row.getDescription()!=null&&!row.getDescription().trim().isEmpty())
          out.append("Description: ").append(row.getDescription().trim()).append('\n');
        out.append("Status: ").append(row.getStatus()).append("  Importance: ").append(row.getImportance()).append('\n');
        out.append("PSS/RSS: ").append(row.getPss()).append('/').append(row.getRss()).append(" KB\n");
        if(includeTrace&&(row.getReason()==5||row.getReason()==6)){
          String trace=infinityReadExitTrace(row);
          if(!trace.isEmpty())out.append("--- Android exit trace ---\n").append(trace).append("\n--- end trace ---\n");
        }
        out.append('\n');
      }
    }catch(Exception e){
      out.append("Could not read Android exit history: ").append(e.getClass().getSimpleName()).append('\n');
    }
    return out.toString();
  }

  private String infinityHealthReport()
  {
    return infinityHealthBuildInfo()+"\nRecent process exits\n====================\n"+
        infinityHealthExitHistory(true);
  }

  private void infinityCopyHealthReport()
  {
    String report=infinityHealthReport();
    android.content.ClipboardManager clipboard=
        (android.content.ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
    if(clipboard!=null){
      clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Infinity diagnostics",report));
      android.widget.Toast.makeText(this,"Infinity diagnostic report copied.",android.widget.Toast.LENGTH_SHORT).show();
    }
  }

  private void infinityExportHealthReport()
  {
    mInfinityHealthExportText=infinityHealthReport();
    Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
    intent.addCategory(Intent.CATEGORY_OPENABLE);
    intent.setType("text/plain");
    String stamp=new java.text.SimpleDateFormat("yyyyMMdd-HHmmss",java.util.Locale.US).format(new java.util.Date());
    intent.putExtra(Intent.EXTRA_TITLE,"Infinity-Diagnostics-"+stamp+".txt");
    try{startActivityForResult(intent,INFINITY_HEALTH_EXPORT_RESULT_CODE);}
    catch(Exception e){
      mInfinityHealthExportText="";
      android.widget.Toast.makeText(this,"No compatible file saver is available.",android.widget.Toast.LENGTH_LONG).show();
    }
  }

