package qa.external;
import android.app.Activity;
import android.content.Intent;
import android.content.ClipData;
import android.net.Uri;
import android.os.Bundle;
import android.widget.*;
import java.io.*;

/** Disposable CI source application. Never included in Infinity or delivered. */
public final class SourceActivity extends Activity {
    LinearLayout list;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);list=new LinearLayout(this);list.setOrientation(1);
        ScrollView scroll=new ScrollView(this);scroll.addView(list);setContentView(scroll);
        TextView title=new TextView(this);title.setText("External video source fixture");list.addView(title);
        try { for (String name:getAssets().list("")) if(name.endsWith(".mp4")) {
            try(InputStream in=getAssets().open(name);FileOutputStream out=new FileOutputStream(new File(getFilesDir(),name))) {
                byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
            }
        }}catch(Exception e){throw new RuntimeException(e);}
        for(String s:new String[]{"A","B","C","END","BAD","AUDIO"}) add("Open "+s,()->open(s.toLowerCase()+".mp4",true,false,false));
        add("Rapid A B C",()->{for(String s:new String[]{"a.mp4","b.mp4","c.mp4"})open(s,true,false,false);});
        add("Share B",()->open("b.mp4",true,true,false));
        add("Denied A",()->open("denied.mp4",false,false,false));
        add("HTTP A",()->open("a.mp4",false,false,true));
        add("Handler labels",()->labels());
    }
    void add(String text,Runnable action){Button b=new Button(this);b.setText(text);b.setAllCaps(false);b.setOnClickListener(v->action.run());list.addView(b);}
    void open(String file,boolean grant,boolean send,boolean http){
        Uri uri=Uri.parse(http?"http://10.0.2.2:8765/"+file:"content://qa.external.source/"+file);
        Intent i=new Intent(send?Intent.ACTION_SEND:Intent.ACTION_VIEW).setType("video/mp4");
        if(send)i.putExtra(Intent.EXTRA_STREAM,uri);else i.setDataAndType(uri,"video/mp4");
        i.setClassName("com.projectinfinity.kodi","com.projectinfinity.kodi.Splash");
        if(grant){i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);i.setClipData(ClipData.newRawUri("video",uri));}
        startActivity(i);
    }
    void labels(){
        Intent i=new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.parse("content://qa.external.source/a.mp4"),"video/mp4");
        java.util.List<android.content.pm.ResolveInfo> found=getPackageManager().queryIntentActivities(i,0);
        StringBuilder out=new StringBuilder();int count=0;
        for(android.content.pm.ResolveInfo r:found)if(r.activityInfo.packageName.equals("com.projectinfinity.kodi")){
            count++;out.append(r.loadLabel(getPackageManager())).append(" | ").append(r.activityInfo.applicationInfo.loadLabel(getPackageManager())).append("\n");
        }
        new android.app.AlertDialog.Builder(this).setTitle("Handlers: "+count).setMessage(out.toString()).setPositiveButton("OK",null).show();
    }
}
