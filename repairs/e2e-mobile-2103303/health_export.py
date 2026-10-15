"""Replace the UI-thread text-only collector with an explicit worker ZIP export."""

def replace_region(text, start, end, new):
    assert text.count(start) == 1 and text.count(end) == 1
    a, b = text.index(start), text.index(end)
    assert a < b
    return text[:a] + new + text[b:]


def repair_health_export(text):
    for old, new in (
        ('"Export diagnostic report","Save a shareable Infinity diagnostic text report."',
         '"Export diagnostics ZIP","Save the report and available Android crash or ANR traces."'),
        ('"Copy diagnostic report","Copy the full report to your clipboard for quick sharing."',
         '"Copy diagnostic summary","Copy a text summary for quick sharing."'),
    ):
        assert text.count(old) == 2
        text = text.replace(old, new)
    text = replace_region(text,
        '    if (requestCode == INFINITY_HEALTH_EXPORT_RESULT_CODE)',
        '    if (requestCode == PERMISSION_RESULT_CODE)',
        '''    if (requestCode == INFINITY_HEALTH_EXPORT_RESULT_CODE)
    {
      if (resultCode == RESULT_OK && data != null && data.getData() != null)
        infinitySaveHealthArchive(data.getData());
      return;
    }
''')
    old = '  private String mInfinityHealthExportText = "";'
    assert text.count(old) == 1
    text = text.replace(old, '  private final java.util.concurrent.atomic.AtomicBoolean mInfinityHealthBusy = new java.util.concurrent.atomic.AtomicBoolean();')
    text = replace_region(text,
        '  private String infinityReadExitTrace(android.app.ApplicationExitInfo row)',
        '  private String infinityHealthExitHistory(boolean includeTrace)', '')
    old = '''        if(includeTrace&&(row.getReason()==5||row.getReason()==6)){
          String trace=infinityReadExitTrace(row);
          if(!trace.isEmpty())out.append("--- Android exit trace ---\\n").append(trace).append("\\n--- end trace ---\\n");
        }
'''
    assert text.count(old) == 1
    text = text.replace(old, '')
    old = 'infinityHealthExitHistory(true);'
    assert text.count(old) == 1
    text = text.replace(old, 'infinityHealthExitHistory(false)+"\\nRaw Android crash/ANR traces are included separately in Export diagnostics ZIP when available.\\n";')
    text = replace_region(text,
        '  private void infinityCopyHealthReport()',
        '  private void showInfinityExperienceChooser()',
        '''  private void infinityHealthToast(String message)
  {
    runOnUiThread(() -> {
      if (!isFinishing() && !isDestroyed())
        android.widget.Toast.makeText(this,message,android.widget.Toast.LENGTH_LONG).show();
    });
  }

  private void infinityCopyHealthReport()
  {
    if (!mInfinityHealthBusy.compareAndSet(false,true)) return;
    Thread worker=new Thread(() -> {
      try {
        android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND);
        String report=infinityHealthReport();
        // Binder/clipboard stays bounded, even if a retained report grows.
        final String copy=report.length()>120000
            ?report.substring(0,120000)+"\\n[Clipboard summary truncated; export diagnostics ZIP for full evidence.]"
            :report;
        runOnUiThread(() -> {
          if (isFinishing() || isDestroyed()) return;
          try {
            android.content.ClipboardManager clipboard=(android.content.ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard!=null) {
              clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Infinity diagnostics",copy));
              infinityHealthToast("Infinity diagnostic summary copied.");
            }
          } catch (RuntimeException failure) { infinityHealthToast("Could not copy the diagnostic summary."); }
        });
      } catch (Exception failure) { infinityHealthToast("Could not collect the diagnostic summary."); }
      finally { mInfinityHealthBusy.set(false); }
    },"InfinityHealthCopy");
    worker.setDaemon(true);worker.start();
  }

  private void infinityExportHealthReport()
  {
    if (mInfinityHealthBusy.get()) return;
    Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
    intent.addCategory(Intent.CATEGORY_OPENABLE);
    intent.setType("application/zip");
    String stamp=new java.text.SimpleDateFormat("yyyyMMdd-HHmmss",java.util.Locale.US).format(new java.util.Date());
    intent.putExtra(Intent.EXTRA_TITLE,"Infinity-Diagnostics-"+stamp+".zip");
    try{startActivityForResult(intent,INFINITY_HEALTH_EXPORT_RESULT_CODE);}
    catch(Exception e){infinityHealthToast("No compatible file saver is available.");}
  }

  private void infinitySaveHealthArchive(android.net.Uri destination)
  {
    if (!mInfinityHealthBusy.compareAndSet(false,true)) return;
    final Context app=getApplicationContext();
    Thread worker=new Thread(() -> {
      try {
        android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND);
        String report=infinityHealthReport();
        try (java.io.OutputStream output=app.getContentResolver().openOutputStream(destination,"w")) {
          if(output==null)throw new java.io.IOException("No document output stream");
          InfinityHealthExport.write(app,output,report);
        }
        infinityHealthToast("Infinity diagnostic ZIP saved.");
      } catch (Exception failure) {
        android.util.Log.w("InfinityHealth","Diagnostic export failed: "+failure.getClass().getSimpleName());
        infinityHealthToast("Could not finish the diagnostic ZIP. The selected file may be incomplete.");
      } finally { mInfinityHealthBusy.set(false); }
    },"InfinityHealthExport");
    worker.setDaemon(true);worker.start();
  }

''')
    return text
