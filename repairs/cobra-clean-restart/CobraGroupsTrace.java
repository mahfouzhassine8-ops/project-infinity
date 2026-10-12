package com.projectinfinity.kodi;

import android.view.View;
import android.view.ViewParent;
import android.widget.ListView;
import java.io.File;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.JSONArray;
import org.json.JSONObject;

/** Read-only trace; no layout, adapter, field, visibility or assertion is changed. */
final class CobraGroupsTrace {
  private static Object field(Object object,String name) throws Exception {
    for(Class<?> type=object.getClass();type!=null;type=type.getSuperclass()) {
      try {Field f=type.getDeclaredField(name);f.setAccessible(true);return f.get(object);}
      catch(NoSuchFieldException missing) { /* search the next framework superclass */ }
    }
    return "FIELD_NOT_FOUND";
  }
  static void record(String context,ListView list) throws Exception {
    JSONObject result=new JSONObject().put("context",context).put("adapterCount",list.getCount())
        .put("childCount",list.getChildCount()).put("first",list.getFirstVisiblePosition())
        .put("last",list.getLastVisiblePosition()).put("mainThread",android.os.Looper.myLooper()==android.os.Looper.getMainLooper());
    for(String name:new String[]{"mBlockLayoutRequests","mInLayout","mDataChanged","mItemCount","mOldItemCount","mLayoutMode","mSelectedPosition","mNextSelectedPosition","mNeedSync","mAdapter","mAdapterDataSetObserver"})result.put(name,String.valueOf(field(list,name)));
    JSONArray parents=new JSONArray();
    for(View v=list;v!=null;) {
      parents.put(new JSONObject().put("class",v.getClass().getName()).put("width",v.getWidth()).put("height",v.getHeight())
          .put("visibility",v.getVisibility()).put("alpha",v.getAlpha()).put("attached",v.isAttachedToWindow())
          .put("layoutRequested",v.isLayoutRequested()).put("layoutSuppressed",String.valueOf(field(v,"mSuppressLayout")))
          .put("privateFlags",String.valueOf(field(v,"mPrivateFlags"))));
      ViewParent parent=v.getParent();v=parent instanceof View?(View)parent:null;
    }
    result.put("ancestors",parents);System.out.println("GROUPS_FRAMEWORK_TRACE "+result.toString());
    File dir=new File(System.getProperty("cobra.clean.evidence"));if(!dir.isDirectory()&&!dir.mkdirs())throw new java.io.IOException("Cannot create trace directory");
    Files.write(new File(dir,"GROUPS-FRAMEWORK-TRACE.json").toPath(),result.toString(2).getBytes(StandardCharsets.UTF_8));
  }
}
