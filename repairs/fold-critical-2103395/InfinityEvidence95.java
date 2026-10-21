package com.projectinfinity.kodi;
import android.content.Context;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Explicit export only. Distinguishes disk candidates from Kodi-resolved paths. */
final class InfinityEvidence95 {
  @SuppressWarnings("deprecation") // Retain the package API available to the original app.
  static void append(Context context,JSONObject report) {
    try {
      JSONObject details=new JSONObject();report.put("corrective_2103395",details);
      details.put("pid",android.os.Process.myPid());details.put("captured_epoch_ms",System.currentTimeMillis());
      details.put("app_version_code",context.getPackageManager().getPackageInfo(context.getPackageName(),0).getLongVersionCode());
      details.put("read_only",true);details.put("disk_locations_are_not_runtime_resolution",true);
      JSONArray locations=new JSONArray();details.put("component_locations",locations);
      File external=context.getExternalFilesDir(null),internal=context.getFilesDir();
      List<File> roots=new ArrayList<>();if(external!=null)roots.add(new File(external.getCanonicalFile(),".kodi/addons"));roots.add(new File(internal.getCanonicalFile(),".kodi/addons"));
      JSONObject expected;
      try(InputStream in=context.getAssets().open("infinity-2103395-components.json")){expected=new JSONObject(new String(read(in,1048576),StandardCharsets.UTF_8));}
      try(ZipFile apk=new ZipFile(context.getApplicationInfo().sourceDir)) {
        ZipEntry engine=apk.getEntry("lib/arm64-v8a/libkodi.so");
        if(engine!=null)try(InputStream in=apk.getInputStream(engine)){details.put("apk_native_sha256",digest(in,400*1024*1024));}
        details.put("native_loaded_identity","APK member hash; loaded-process identity requires matching engine receipt");
        Iterator<String> ids=expected.keys();
        while(ids.hasNext()) {
          String id=ids.next();JSONObject pins=expected.getJSONObject(id);
          for(File root:roots) {
            File dir=new File(root,id).getAbsoluteFile();if(!dir.isDirectory())continue;
            JSONObject row=new JSONObject();locations.put(row);row.put("id",id);row.put("directory",dir.toString());row.put("runtime_active","UNKNOWN");
            if(!dir.equals(dir.getCanonicalFile())){row.put("state","LINK_REJECTED");continue;}
            JSONObject hashes=new JSONObject();row.put("files",hashes);boolean match=true;
            Iterator<String> names=pins.keys();
            while(names.hasNext()) {
              String name=names.next();File file=new File(dir,name).getAbsoluteFile();JSONObject observed=new JSONObject();hashes.put(name,observed);
              if(!file.equals(file.getCanonicalFile()) || !file.isFile()){observed.put("state","MISSING_OR_LINK");match=false;continue;}
              try(InputStream in=new FileInputStream(file)){String hash=digest(in,4*1024*1024);observed.put("sha256",hash);observed.put("state",hash.equals(pins.getString(name))?"MATCH":"DIFFERENT");match&=hash.equals(pins.getString(name));}
            }
            row.put("state",match?"MATCH":"DIFFERENT");
          }
        }
      }
      details.put("touch_current",touch(external,false));details.put("touch_previous",touch(external,true));
    }catch(Exception unavailable){try{report.put("critical95_evidence_error",unavailable.getClass().getSimpleName());}catch(JSONException ignored){}}
  }
  static JSONArray touch(File external,boolean previous) throws Exception {
    JSONArray output=new JSONArray();if(external==null)return output;
    File file=new File(external.getCanonicalFile(),".kodi/temp/"+(previous?"kodi.old.log":"kodi.log"));
    if(!file.isFile()||!file.equals(file.getCanonicalFile()))return output;
    byte[] bytes;try(RandomAccessFile in=new RandomAccessFile(file,"r")){long length=in.length(),start=Math.max(0,length-4*1024*1024);in.seek(start);bytes=new byte[(int)(length-start)];in.readFully(bytes);}
    ArrayList<JSONObject> rows=new ArrayList<>();
    for(String line:new String(bytes,StandardCharsets.UTF_8).split("\n")){
      int at=line.indexOf("[InfinityTouch] ");if(at<0||line.length()>4096)continue;
      try{JSONObject raw=new JSONObject(line.substring(at+16).trim());JSONObject row=new JSONObject();
        for(String k:new String[]{"event","phase","outcome"}){String v=raw.optString(k);if(v.matches("[A-Za-z0-9_.-]{1,100}"))row.put(k,v);}
        for(String k:new String[]{"control","index","pid","tid","epoch_ns","monotonic_ns","pointers","window","modal"})if(raw.has(k))row.put(k,raw.getLong(k));
        rows.add(row);
      }catch(Exception partial){/* Partial records never authorize a pass. */}
    }
    for(int i=Math.max(0,rows.size()-256);i<rows.size();i++)output.put(rows.get(i));return output;
  }
  static byte[] read(InputStream in,int maximum)throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] buf=new byte[8192];for(int n;(n=in.read(buf))!=-1;){if(b.size()+n>maximum)throw new IOException("limit");b.write(buf,0,n);}return b.toByteArray();}
  static String digest(InputStream in,int maximum)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");byte[] b=new byte[8192];int size=0;for(int n;(n=in.read(b))!=-1;){size+=n;if(size>maximum)throw new IOException("limit");d.update(b,0,n);}StringBuilder out=new StringBuilder();for(byte v:d.digest())out.append(String.format(Locale.ROOT,"%02x",v&255));return out.toString();}
}
